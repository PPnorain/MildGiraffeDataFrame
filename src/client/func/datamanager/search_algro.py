import os, json, requests, tempfile
import pandas as pd
import gradio as gr
from apiweb import api_search_content, api_logs_write
from manager import manager
from conf.userconf import URL

# def search_data(user_name, filename, key_words, search_filed):
#     '''
#     功能简述：在dataset_info中的filename content中的search_filed域中搜索所有包含key_words条目的数据。
#     '''
#     if not user_name or not filename or not key_words or not search_filed:
#         gr.Warning(' 数据集，搜索关键词或搜索字段未选择！')
#         return [gr.update()]*2
#     res = api_search_content(user_name, 'dataset_info', filename, key_words, search_filed)
#
#     if res['code'] == 200:
#         df = pd.DataFrame(res['data']).reset_index()
#         df_meta = {'total':len(df)}
#         return df_meta, df
#     else:
#         gr.Warning(res['message'])
#     return [gr.update()]*2

# def search_data(user_name, typ, filename, search_method, key_words, search_filed, regex_patten, search_filed_regex):

def search_data(component_data):
    '''
    功能简述：在dataset_info中的filename content中的search_filed域中搜索所有包含key_words条目的数据。
    '''
    user_name = component_data[manager.get_elem_by_name('top.user_name')]
    search_config = manager.get_current_conf(component_data)
    typ, filename, search_method = search_config["analysis_source"], search_config["analysis_collection_name"], search_config["search_analysis_method"]

    api_logs_write(user_name, f"[ Analysis ] 开始【{search_method}】相似数据搜素")
    gr.Info(f"[ Analysis ] 开始【{search_method}】相似数据搜素")
    
    if not user_name or not filename or not search_method:
        gr.Warning(' 数据集、搜索字段或搜索算法未选择！')
        return [gr.update()]*3
    res = api_search_content(user_name, typ, filename, search_config)

    if res['code'] == 200:
        df = pd.DataFrame(res['data']).reset_index()
        df_meta = {'total':len(df)}
        # return df_meta, df
        api_logs_write(user_name, f"[ Analysis ] 结束【{search_method}】相似数据搜素")
        gr.Info(f"[ Analysis ] 结束【{search_method}】相似数据搜素")
        return gr.update(value=df_meta, visible=True), gr.update(value=df, visible=True), gr.update(visible=True)
    else:
        api_logs_write(user_name, f"[ Warning ] 【{search_method}】相似数据搜素出错")
        gr.Warning(res['message'])
    return [gr.update()]*3