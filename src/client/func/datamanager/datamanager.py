import os, json, requests, tempfile
import pandas as pd
import gradio as gr
from apiweb import api_get_list, api_write, api_read, api_read_page, api_delete, api_get_meta_std, api_get_meta_std, api_logs_write, api_logs_read, api_read_doc_filed
from conf.userconf import URL

def change_status(choose):
    if choose:
        return gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
    return gr.update(), gr.update(), gr.update()

def get_droplist(user_name, typ, dataset_name):
    """
    功能简介：用户获取用户空间中所有数据集名字。
    """
    if user_name != '':
        choices = api_get_list(user_name, typ)
        api_logs_write(user_name, f"[ 数据集列表更新 ][{__name__}] {user_name} 数据集列表更新【成功】！")
        # 如果选中数据集在更新后列表中，则不改变选中的值，否则将值设置为空字符串
        if len(choices) > 0:
            if dataset_name in choices:
                return gr.update(choices=choices)
            else:
                return gr.update(choices=choices, value=None)
        else:
            return gr.update(choices=[])

    api_logs_write(user_name, f"[ 数据集列表更新 ][{__name__}] {user_name} 数据集列表更新【失败】！")
    return gr.update(choices=[])

def show_subtab(choose, user_name, filename):
    '''
    功能简介：选中具体的搜索算法则展示响应的配置面板和一些对应的功能。
    '''
    if not filename:
        gr.Warning('请先选择数据集！')
        return gr.update(), gr.update()
    if choose == 'keysearch':
        choices = api_read_doc_filed(user_name, 'dataset_info', filename, 'columns')
        return gr.update(visible=True), gr.update(choices=choices['columns'], value=None, interactive=True)
    return gr.update(visible=False), gr.update(value=None)


def show_search_conf(choose):
    '''
    功能简介：选中具体的搜索算法则展示响应的配置面板和一些对应的功能。
    '''
    if choose == 'key_search':
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    if choose == 'regex_search':
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
    if choose == 'cluster_search':
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
    if choose == 'similar_search':
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
    return [gr.update(visible=False)]*4

def submit_status(user_name, status):
    if status == 'load' and user_name not in ['', None]:
        return gr.update(interactive=True)
    return gr.update(interactive=False)

def show_dataset(user_name, dataset_name):
    if not dataset_name: 
        gr.Warning('请先选择数据集！')
        return gr.update(), gr.update()
    response = api_read(user_name, 'dataset_info', dataset_name)
    if response['code'] != 200:
        gr.Warning(response['message'])
        return [gr.update()]*2
    response = response['data']
    df = pd.DataFrame(response).reset_index()
    return gr.update(value=df, visible=True), gr.update(visible=True)

def show_meta(user_name, dataset_name):
    if not dataset_name:
        gr.Warning('请先选择数据集！')
        return gr.update(), gr.update()
    response = api_get_meta_std(user_name, 'dataset_info', dataset_name)
    if response['code'] != 200:
        gr.Warning(f"数据元信息请求失败\ncode:[{response['code']}]\nmessage:[{response['message']}]")
        return [gr.update()]*2
    return gr.update(value=response['data'], visible=True), gr.update(visible=True)

def close_show():
    return [gr.update(visible=False)]*4

def delete_dataset(user_name, dataset_name):
    if not dataset_name:
        gr.Warning("没有选择数据集！")
        return [gr.update()]*3
    response = api_delete(user_name, 'dataset_info', dataset_name)
    gr.Info(f"成功删除数据库集{dataset_name}！")
    return get_droplist(user_name, 'dataset_info', dataset_name), gr.update(visible=False), gr.update(visible=False)

# 搜索功能
def show_columns(user_name, dataset_name):
    # response = api_get_dataset
    return gr.update(choices=response, value=None if len(response) == 0 else response[0])