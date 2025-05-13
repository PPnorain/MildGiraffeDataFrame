import os, json
import gradio as gr
from typing import TYPE_CHECKING, Dict
from manager import manager
if TYPE_CHECKING:
    from gradio.components import Component
# from conf.userconf import SEARCH_METHOD_NEW
from common import get_logs, submit_file, download_file, show_pages, get_page_content, close_show
from func.datamanager.datamanager import change_status, get_droplist, show_subtab, submit_status, show_dataset, delete_dataset, show_meta, show_columns

from func.datamanager.search_algro import search_data

def create_datamanager_tab() -> Dict[str, "Component"]:
    interactive_elems, user_elems, elem_dict = set(), set(), dict()

    # 查看数据集
    gr.Markdown("### 查看/删除数据集")
    with gr.Row():
        dataset_datamanager_name = gr.Dropdown(choices=[], label="数据集", scale=7, interactive=False)

        with gr.Column(scale=3):
            with gr.Row():
                btn_datamanager_show = gr.Button(value='展示数据', interactive=False)
                btn_datamanager_closeshow = gr.Button(value='关闭展示', interactive=False)
            with gr.Row():
                btn_datamanager_showmeta = gr.Button(value='元信息', interactive=False)
                btn_datamanager_remove = gr.Button(value='删除数据', interactive=False)

    with gr.Accordion("数据内容", open=True, visible=False) as datamanager_show_data:
        collection_datamanager_meta = gr.Json(label='数据集元信息', visible=False)
        collection_datamanager_data = gr.Dataframe(label='数据集展示', height=500, wrap=True, visible=False)
        collection_datamanager_pages = gr.Slider(label='pages', visible=False, interactive=True)

    user_elems.update({})
    interactive_elems.update({dataset_datamanager_name, btn_datamanager_show, btn_datamanager_closeshow, btn_datamanager_showmeta, btn_datamanager_remove})
    elem_dict.update(dict(
        dataset_datamanager_name=dataset_datamanager_name, btn_datamanager_show=btn_datamanager_show, 
        btn_datamanager_showmeta=btn_datamanager_showmeta,btn_datamanager_remove=btn_datamanager_remove,
        collection_datamanager_meta=collection_datamanager_meta,
        datamanager_show_data=datamanager_show_data,
        collection_datamanager_pages=collection_datamanager_pages,btn_datamanager_closeshow=btn_datamanager_closeshow, 
        collection_datamanager_data=collection_datamanager_data, 
    ))

    gr.Markdown("### 上传数据集")
    with gr.Row():
        with gr.Column(scale=10):
            dataset_datamanager_upload = gr.File(label="数据集", height=80)

        with gr.Column(scale=5):
            overwrite_check = gr.Checkbox(label='覆盖已有重名文件', value=False)
            btn_datamanager_submit = gr.Button(value='上传', interactive=False)

    user_elems.update({})
    interactive_elems.update({})
    elem_dict.update(dict(
        dataset_datamanager_upload=dataset_datamanager_upload, 
        overwrite_check=overwrite_check,
        btn_datamanager_submit=btn_datamanager_submit
    ))

    gr.Markdown("### 下载数据集")
    with gr.Row():
        with gr.Column(scale=10):
            save_datamanager_typ = gr.Dropdown(choices=['xlsx', 'csv', 'json', 'jsonl'], label="保存文件类型", value='xlsx', interactive=False)
        with gr.Column(scale=5):
            download_datamanager_button = gr.Button(value='准备下载', scale=1, interactive=False)
    with gr.Row():
        collection_data_download = gr.File(label="Download 数据表", visible=False)

    user_elems.update({save_datamanager_typ})
    interactive_elems.update({download_datamanager_button, save_datamanager_typ})
    elem_dict.update(dict(
        save_datamanager_typ=save_datamanager_typ, download_datamanager_button=download_datamanager_button,
        collection_data_download=collection_data_download,
    ))

    return elem_dict, interactive_elems, user_elems

def callback_init_datamanager():
    user_name = manager.get_elem_by_name('top.user_name')
    sys_info = manager.get_elem_by_name('top.sys_info')
    # 数据展示
    dataset_datamanager_name = manager.get_elem_by_name('datamanager.dataset_datamanager_name')
    btn_datamanager_show = manager.get_elem_by_name('datamanager.btn_datamanager_show')
    btn_datamanager_closeshow = manager.get_elem_by_name('datamanager.btn_datamanager_closeshow')
    collection_datamanager_data = manager.get_elem_by_name('datamanager.collection_datamanager_data')
    collection_datamanager_meta = manager.get_elem_by_name('datamanager.collection_datamanager_meta')
    collection_datamanager_pages = manager.get_elem_by_name('datamanager.collection_datamanager_pages')
    datamanager_show_data = manager.get_elem_by_name('datamanager.datamanager_show_data')

    btn_datamanager_showmeta = manager.get_elem_by_name('datamanager.btn_datamanager_showmeta')
    btn_datamanager_remove = manager.get_elem_by_name('datamanager.btn_datamanager_remove')
    dataset_datamanager_upload = manager.get_elem_by_name('datamanager.dataset_datamanager_upload')
    overwrite_check = manager.get_elem_by_name('datamanager.overwrite_check')
    btn_datamanager_submit = manager.get_elem_by_name('datamanager.btn_datamanager_submit')
    download_datamanager_button = manager.get_elem_by_name('datamanager.download_datamanager_button')
    collection_data_download = manager.get_elem_by_name('datamanager.collection_data_download')
    save_datamanager_typ = manager.get_elem_by_name('datamanager.save_datamanager_typ')
    
    # 模块外部影响：回归组件
    # regresstest_collection_name = manager.get_elem_by_name('regresstest.collection_name')
    analysis_collection_name = manager.get_elem_by_name('analysis.analysis_collection_name')
    processing_collection_name = manager.get_elem_by_name('processing.processing_collection_name')

    # 数据上传
    dataset_datamanager_upload.upload(submit_status, inputs=[user_name, gr.State('load')], outputs=[btn_datamanager_submit], queue=False)
    dataset_datamanager_upload.clear(submit_status, inputs=[user_name, gr.State('unload')], outputs=[btn_datamanager_submit], queue=False)

    btn_datamanager_submit.click(lambda: gr.update(interactive=False), outputs=[btn_datamanager_submit]).then(submit_file, inputs=[user_name, dataset_datamanager_upload, gr.State('dataset_info'), gr.State(''), overwrite_check], outputs=[btn_datamanager_submit]).success(get_droplist, [user_name, gr.State('dataset_info'), dataset_datamanager_name], outputs=[dataset_datamanager_name]).success(get_droplist, [user_name, gr.State('dataset_info'), analysis_collection_name], outputs=[analysis_collection_name]).success(get_droplist, [user_name, gr.State('dataset_info'), processing_collection_name], outputs=[processing_collection_name]).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    # .success(get_droplist, [user_name, gr.State('dataset_info'), regresstest_collection_name], outputs=[regresstest_collection_name])

    btn_datamanager_show.click(show_dataset, inputs=[user_name, dataset_datamanager_name], outputs=[collection_datamanager_data, datamanager_show_data]).then(show_pages, inputs=[user_name, gr.State('dataset_info'), dataset_datamanager_name], outputs=collection_datamanager_pages)

    btn_datamanager_showmeta.click(show_meta, inputs=[user_name, dataset_datamanager_name], outputs=[collection_datamanager_meta, datamanager_show_data])

    collection_datamanager_pages.change(get_page_content, inputs=[user_name, gr.State('dataset_info'), dataset_datamanager_name, collection_datamanager_pages], outputs=[collection_datamanager_data])

    btn_datamanager_closeshow.click(close_show, inputs=[gr.State(4)], outputs=[collection_datamanager_data, collection_datamanager_meta, datamanager_show_data, collection_datamanager_pages])

    btn_datamanager_remove.click(delete_dataset, inputs=[user_name, dataset_datamanager_name], outputs=[dataset_datamanager_name, collection_datamanager_data, collection_datamanager_meta]).success(get_droplist, [user_name, gr.State('dataset_info'), dataset_datamanager_name], outputs=[dataset_datamanager_name]).success(get_logs, [user_name], outputs=[sys_info])
    # .success(get_droplist, [user_name, gr.State('dataset_info'), regresstest_collection_name], outputs=[regresstest_collection_name])

    download_datamanager_button.click(download_file, inputs=[user_name, gr.State("dataset_info"), dataset_datamanager_name, gr.State(None), gr.State(None), save_datamanager_typ], outputs=[collection_data_download])

# 登录时组件初始化
def datamanager_login_components():
    dataset_datamanager_name = manager.get_elem_by_name('datamanager.dataset_datamanager_name')

    return [dataset_datamanager_name]

def datamanager_login_status(user_name):
    dataset_datamanager_name = manager.get_elem_by_name('datamanager.dataset_datamanager_name')
    return get_droplist(user_name, 'dataset_info', dataset_datamanager_name)

# 登出时组件初始化
def datamanager_logout_components():
    dataset_datamanager_name = manager.get_elem_by_name('datamanager.dataset_datamanager_name')
    
    btn_datamanager_show = manager.get_elem_by_name('datamanager.btn_datamanager_show')
    btn_datamanager_closeshow = manager.get_elem_by_name('datamanager.btn_datamanager_closeshow')
    btn_datamanager_showmeta = manager.get_elem_by_name('datamanager.btn_datamanager_showmeta')
    collection_datamanager_data = manager.get_elem_by_name('datamanager.collection_datamanager_data')
    collection_datamanager_meta = manager.get_elem_by_name('datamanager.collection_datamanager_meta')
    btn_datamanager_remove = manager.get_elem_by_name('datamanager.btn_datamanager_remove')
    btn_datamanager_submit = manager.get_elem_by_name('datamanager.btn_datamanager_submit')

    collection_datamanager_pages = manager.get_elem_by_name('datamanager.collection_datamanager_pages')
    return [dataset_datamanager_name, btn_datamanager_show, btn_datamanager_closeshow, btn_datamanager_showmeta, collection_datamanager_data, collection_datamanager_meta, btn_datamanager_remove, btn_datamanager_submit, collection_datamanager_pages]

def datamanager_logout_status():
    return gr.update(choices=[], value=None), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=False), gr.update(visible=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=False)