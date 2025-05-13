import gradio as gr
from dataclasses import is_dataclass
from manager import manager
from conf.taskdata import GenConfig, datatype_map
from apiweb import api_login, api_logout, api_logs_write, api_logs_clear
from conf.userconf import GENERATE_METHOD

def resume(user_input, user_name, op):
    if (user_input == '' and op) or (user_name != user_input and op): 
        return {elem: gr.update() for elem in manager.get_list_elems(typ='interactive')}
    if op:
        gr.Info("登录成功")
    else:
        gr.Info("登出成功")

    flatten_dict = manager.flatten_dict(manager.tree_elems)
    update_status = {}
    for name, component in flatten_dict.items():
        if component in manager.interactive_elems:
            tmp_status = dict(interactive=op)
            
            # 生成功能的控件控制
            if name in ['generation.generate_method'] and op:
                tmp_status = dict(choices=GENERATE_METHOD, interactive=op, value=GENERATE_METHOD[0])
            elif name in ['generation.template_name', 'generation.seed_name', 'generation.generate_method']:
                tmp_status = dict(choices=[], value=None, interactive=op)

            # 数据集管理的控件控制
            if name in ['datamanager.dataset_datamanager_name'] and not op:
                tmp_status = dict(choices=[], value=None, interactive=op)

                
            update_status[component] = gr.update(**tmp_status)
    return update_status

    
def log_in_step(component_data):
    user_input = manager.get_componet_value('top.user_input', component_data)
    user_name = manager.get_componet_value('top.user_name', component_data)
    # from ipdb import set_trace
    # set_trace()
    if user_input != '' and not user_name:
        response = api_login(user_input)
        api_logs_write(user_input, f'[{__file__}] 用户【{user_input}】登录成功')

        api_logs_clear(user_input)
        return gr.update(value=user_input, interactive=False), gr.update(interactive=False), gr.update(interactive=True)
    if user_name:
        gr.Warning('请先登出再重新登录！')
    if not user_input:
        gr.Warning('用户名输入为空！')
    return [gr.update()]*3


def log_out(component_data):
    '''
    登出状态存储
    TODO 后期如果存在更多组件，需要更新 
    '''
    user_name = component_data[manager.get_elem_by_name('top.user_name')]
    generation_config = manager.get_componet_value_dict('generation', component_data)

    response = api_logout({'user_name':user_name, 'generation':generation_config})
    api_logs_write(user_name, f'用户【{user_name}】退出系统')
    return gr.update(value=''), gr.update(interactive=True), gr.update(interactive=False)