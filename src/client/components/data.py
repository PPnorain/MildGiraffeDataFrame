import os, json
import gradio as gr
from typing import TYPE_CHECKING, Any, Dict, Tuple
from apiweb import api_read_page, api_get_meta_std
from common import response_checker
import math
if TYPE_CHECKING:
    from gradio.components import Component

def create_preview_box(user_name, dataset: "gr.Dropdown", tab='', typ=''):
    window = PreWindow(tab, typ)
    dataset.change(
        window.can_preview, [dataset], [window.btn_preview], queue=False
    ).then(
        lambda: 1, outputs=[window.page_index], queue=False
    )

    window.btn_preview.click(
            window.get_preview,
            [user_name, dataset, window.page_index],
            [window.preview_count, window.preview_samples, window.preview_box],
            queue=False
        )

    window.prev_btn.click(
            window.prev_page, [window.page_index], outputs=[window.page_index], queue=False
        ).then(
            window.get_preview,
            [user_name, dataset, window.page_index],
            [window.preview_count, window.preview_samples, window.preview_box],
            queue=False
        )

    window.next_btn.click(
            window.next_page, [window.page_index, window.preview_count], outputs=[window.page_index], queue=False
        ).then(
            window.get_preview,
            [user_name, dataset, window.page_index],
            [window.preview_count, window.preview_samples, window.preview_box],
            queue=False
        )

    window.page_index.submit( 
            window.get_preview,
            [user_name, dataset, window.page_index],
            [window.preview_count, window.preview_samples, window.preview_box],
            queue=False)
    window.close_btn.click(lambda: gr.update(visible=False), outputs=[window.preview_box], queue=False)

    return {
            "btn_preview_"+typ:window.btn_preview,
            'preview_count_'+typ:window.preview_count,
            'page_index_'+typ:window.page_index,
            'prev_btn_'+typ:window.prev_btn,
            'next_btn_'+typ:window.next_btn,
            'close_btn_'+typ:window.close_btn,
            'preview_samples_'+typ:window.preview_samples
    }

class PreWindow:
    PAGE_SIZE = 2
    def __init__(self, tab, typ) -> Dict[str, "Component"]:
        self.tab = tab
        self.btn_preview = gr.Button(value='预览', interactive=False, scale=1)
        self.typ = typ
        with gr.Column(visible=False, elem_classes="modal-box") as self.preview_box:
            with gr.Row():
                self.preview_count = gr.Number(value=0, interactive=False, precision=0, label='总数')
                self.page_index = gr.Number(value=0, interactive=True, precision=0, label='当前页')

            with gr.Row():
                self.prev_btn = gr.Button(value='上一页')
                self.next_btn = gr.Button(value='下一页')
                self.close_btn = gr.Button(value='关闭')

            with gr.Row():
                # if mode == 'json':
                    self.preview_samples = gr.JSON(label="详细数据展示")
                # elif mode == 'txt':
                    # self.preview_samples = gr.Textbox(interactive=False)
                
    def prev_page(self, page_index:int) -> int:
        page_index = page_index - 1 if page_index > 1 else page_index
        return page_index
        
    def next_page(self, page_index:int, total_num: int) -> int:
        page_index = page_index + 1 if (page_index + 1)  <= total_num else page_index
        return page_index

    def can_preview(self, dataset_name: list) -> Dict[str, Any]:
        if isinstance(dataset_name, str) and dataset_name != '':
            return gr.update(interactive=True)
        return gr.update(interactive=False)

    def get_preview(self, user_name: str, dataset_name: list, page_index:int) -> Tuple[int, list, Dict[str, Any]]:
        def gradio_bug_deal(data):
            '''
            功能简介：gradio.JSON有一个bug，如果字典中有path键，就会莫名奇妙去读取这个路径。所以不能有path键。这里将原始的path键全部暂时更名为path_gr_bug.
            '''
            def deal_path(data_dic):
                e = dict()
                for k, v in data_dic.items():
                    if k == 'path':
                        e['path_gr_bug'] = v
                    else:
                        e[k] = v 
                return e 
            if isinstance(data, list):
                new_data=[]
                for dic in data:
                    new_data.append(deal_path(dic))
            else:
                new_data = deal_path(data)
            return new_data
        response = api_read_page(user_name, self.tab, dataset_name, page_index, limit=self.PAGE_SIZE, filedname='type', filedvalue=self.typ)
        if not response_checker(response): return 0, [], gr.update()
        data = response['data']

        response = api_get_meta_std(user_name, self.tab, dataset_name)
        if not response_checker(response): return 0, [], gr.update()
        total_nums = response['data'].get('total_nums', 0)//self.PAGE_SIZE
        if isinstance(data, list):
            tmp_data = data
            tmp_data = gradio_bug_deal(tmp_data)
        else:
            tmp_data = gradio_bug_deal(data)
        return total_nums, gr.update(value=tmp_data), gr.update(visible=True)