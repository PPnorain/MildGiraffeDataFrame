import os, json
import gradio as gr
from typing import TYPE_CHECKING, Dict
from manager import manager
from func.user.user import log_in_step, log_out, resume
from components.datamanager import datamanager_logout_status, datamanager_logout_components, datamanager_login_components, datamanager_login_status
from components.analysis import analysis_login_status, analysis_login_components, analysis_logout_components, analysis_logout_status
from components.generator import generation_login_status, generation_login_component, generation_logout_component, generation_logout_status
# from components.regresstest import regresstest_logout_status, regresstest_logout_components, regresstest_login_components, regresstest_login_status
from common import get_logs
if TYPE_CHECKING:
    from gradio.components import Component

def create_top_tab() -> Dict[str, "Component"]:
    elem_dict, interactive_elems, user_elems = dict(), set(), set()

    with gr.Row():
        user_input = gr.Textbox(interactive=True, placeholder="输入用户名", scale=3, label='用户名')
        user_name = gr.Textbox(interactive=False, scale=3, label='登录用户')
        with gr.Column():
            btn_login = gr.Button(interactive=True, scale=1, value='登录')
            btn_logout = gr.Button(interactive=False, scale=1, value='登出')
    # sys_info = gr.HighlightedText(interactive=False, scale=3, label='系统信息')
    sys_info = gr.Textbox(scale=3, lines=7, max_lines=7, label='系统信息', elem_id="logtext", elem_classes="output-textarea", autoscroll=True, interactive=False)
    user_elems.update({user_input, user_name})
    elem_dict.update(dict(
        user_input=user_input, user_name=user_name, btn_login=btn_login, btn_logout=btn_logout, sys_info=sys_info
    ))

    return elem_dict, interactive_elems, user_elems

def callback_init_top():
    user_input = manager.get_elem_by_name('top.user_input')
    user_name = manager.get_elem_by_name('top.user_name')
    btn_login = manager.get_elem_by_name('top.btn_login')
    btn_logout = manager.get_elem_by_name('top.btn_logout')
    sys_info = manager.get_elem_by_name('top.sys_info')

    btn_login.click(log_in_step, inputs=set(manager.get_list_elems(typ='user')), outputs=[user_name, btn_login, btn_logout]).then(resume, [user_input, user_name, gr.State(True)], outputs=set(manager.get_list_elems(typ='interactive'))).success(datamanager_login_status, [user_name], outputs=datamanager_login_components()).success(analysis_login_status, [user_name], outputs=analysis_login_components()).success(generation_login_status, [user_name], outputs=generation_login_component()).then(get_logs, [user_name], [sys_info], scroll_to_output=True)
    # .success(regresstest_login_status, [user_name], outputs=regresstest_login_components())

    user_input.submit(log_in_step, inputs=set(manager.get_list_elems(typ='user')), outputs=[user_name, btn_login, btn_logout]).then(resume, [user_input, user_name, gr.State(True)], outputs=set(manager.get_list_elems(typ='interactive'))).success(datamanager_login_status, [user_name], outputs=datamanager_login_components()).success(analysis_login_status, [user_name], outputs=analysis_login_components()).success(generation_login_status, [user_name], outputs=generation_login_component()).then(get_logs, [user_name], [sys_info], scroll_to_output=True)
    # .success(regresstest_login_status, [user_name], outputs=regresstest_login_components())

    btn_logout.click(log_out, inputs=set(manager.get_list_elems(typ='user')), outputs=[user_name, btn_login, btn_logout]).then(resume, [user_input, user_name, gr.State(False)], outputs=set(manager.get_list_elems(typ='interactive'))).success(datamanager_logout_status, outputs=datamanager_logout_components()).success(analysis_logout_status, outputs=analysis_logout_components()).success(generation_logout_status, outputs=generation_logout_component()).then(get_logs, [user_name], [sys_info], scroll_to_output=True)
    # .success(regresstest_logout_status, outputs=regresstest_logout_components())