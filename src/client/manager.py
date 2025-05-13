import copy
from typing import TYPE_CHECKING, Dict, List, Set, Generator, Any
import gradio as gr
from gradio.components import Component

from conf.taskdata import datatype_map
from dataclasses import asdict, fields, is_dataclass

# 在树种存储前端所有组件，根到节点的路径是该节点名
class ComponentTree:
    '''
    组件名定义：'top.user_name'

    组件名-组件对象(组件命名字典)：tree_elems
    组件名-组件值(组件值字典):get_componet_value_dict
    组件-组件值(组件状态字典):
    组件-组件更新函数(组件更新字典):
    '''
    def __init__(self, tree_dict):
        self.tree_elems = tree_dict
        self.user_elems = set()
        self.interactive_elems = set()

    def get_elem_by_name(self, elem_name):
        '''根据元素名(路径)找到对应路径的元素component，规定一定只有一个元素'''
        component = self.get_subtree_nodes(elem_name)
        assert len(component) == 1, f'error name：{elem_name}'
        return component[0]
       

    def get_list_elems(self, current_node=None, typ='all'):
        '''根据字典节点域获取其中所有叶节点元素，返回一个列表'''
        if current_node is None:
            current_node = self.tree_elems
        leaf_nodes = []
        for key, value in current_node.items():
            if isinstance(value, dict):
                leaf_nodes.extend(self.get_list_elems(current_node=value, typ=typ))
            else:
                if typ == 'all' or (typ == 'user' and value in self.user_elems) or (typ == 'interactive' and value in self.interactive_elems):
                    leaf_nodes.append(value)

        return leaf_nodes

    def get_subtree_nodes(self, path, typ='list'):
        '''根据路径找到其子树种所有的节点'''
        paths = path.split('.')
        current_node = self.tree_elems
        for p in paths:
            if p in current_node:
                current_node = current_node[p]
            else:
                return [] if typ == 'list' else dict()

        if isinstance(current_node, dict):
            return self.get_list_elems(current_node) if typ == 'list' else current_node
        # TODO 如果路径只有一个节点，字典类型返回有问题
        return [current_node] if typ=='list' else {}

    def add_node(self, path, node_name, node_value={}):
        '''根据路径给其添加一个节点域'''
        paths = path.split('.')
        current_node = self.tree_elems
        for p in paths:
            if p in current_node:
                current_node = current_node[p]
            else:
                return False  # 路径不存在
        current_node[node_name] = node_value
        return True  # 添加成功

    def get_componet_value_dict(self, path, component_data):
        '''获取组件值字典'''
        '''这个函数有问题，它会在原字典上进行替换'''
        def replace_leaf_values(nested_dict, component_data):
            new_dict = {}  # 创建一个新的字典
            for key, value in nested_dict.items():
                if isinstance(value, dict):  # 如果值是字典，递归处理
                    new_dict[key] = replace_leaf_values(value, component_data)
                else:  # 否则，替换叶节点值
                    if value in component_data:
                        new_dict[key] = component_data[value]
                    # else:
                    #     new_dict[key] = value
            return new_dict
        # 这个赋值很费事
        sub_tree = self.get_subtree_nodes(path, typ='dict')
        tree_value_dict = replace_leaf_values(sub_tree, component_data)
        return tree_value_dict

    def get_componet_value(self, name, component_data):
        '''获取某个组件对应的值'''
        return component_data[self.get_elem_by_name(name)]

    def get_update_status(self, status_dict):
        update_status = {}
        def recursive_update(path, status):
            if isinstance(status, dict):
                for k, v in status.items():
                    recursive_update(f'{path}.{k}', v)
            else:
                update_status[self.get_elem_by_name(path)] = gr.update(**{'value':status})

        for path, status in status_dict.items():
            recursive_update(path, status)
        return update_status

    def dataclass_to_dict(self, obj, path=None):
        '''数据对象转化为一维字典'''
        if path is None:
            path = []
        if is_dataclass(obj):
            result = {}
            for field in obj.__dataclass_fields__:
                new_path = path + [field]
                value = getattr(obj, field)
                result.update(self.dataclass_to_dict(value, new_path))
            return result
        else:
            return {'.'.join(path): obj}

    def flatten_dict(self, d, parent_key='', sep='.'):
        '''嵌套字典一维化'''
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def get_current_conf(self, component_data):
        '''从前端获取对应数据类成员的值，并对其进行赋值'''
        for k in component_data:
            if isinstance(k, gr.State):
                if isinstance(component_data[k], str) and component_data[k] in datatype_map:
                    typ = component_data[k]
                    break
        path, datatyp = datatype_map[typ]['path'], datatype_map[typ]['type']
        value_dict = self.get_componet_value_dict(path, component_data)
        user_config = Cls_from_dict(datatyp, value_dict)
        return asdict(user_config)  

def Cls_from_dict(data_class_type, data: dict):
    '''字典转换为数据类'''
    if is_dataclass(data_class_type):
        field_types = {f.name: f.type for f in data_class_type.__dataclass_fields__.values()}
        return data_class_type(**{f: Cls_from_dict(field_types[f], data[f]) if f in data else None for f in field_types})
    elif isinstance(data_class_type, type) and issubclass(data_class_type, list):
        element_type = data_class_type.__args__[0]
        return [Cls_from_dict(element_type, elem) for elem in data]
    else:
        return data
    
manager = ComponentTree({})