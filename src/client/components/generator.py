import os, json
import gradio as gr
from typing import TYPE_CHECKING, Dict
from manager import manager

from .data import create_preview_box
from conf.userconf import GENERATE_METHOD
from apiweb import api_store, api_logs_write, api_get_filed_list, api_delete, api_get_userspace, api_get_userspace_item
from func.datamanager.datamanager import get_droplist
from common import get_logs, submit_file, download_file, show_pages, get_page_content, close_show, response_checker
if TYPE_CHECKING:
    from gradio.components import Component
from func.generator.generator import gr_generate_query, generate_data, list_files, upload_file, refresh, clear_file, store_data, gr_generate_ba_query, get_generation_config, template_input_save, fsg_typ_select, fsg_PR_flush, fsg_Temp_flush, delete_data, read_data,  generation_get_filed_list, show_meta, save_models_config, find_list_models_config, delete_models_config, find_item_models_config, gr_generate_continue, loda_template, make_interrupt, get_all_tasks, close_generation_window

def show_extra(op):
    if op == 'FewShotGenerator':
        return gr.update(visible=True), gr.update(visible=False)
    if op == 'BatchGenerator':
        return gr.update(visible=False), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=False)

def create_generator_tab() -> Dict[str, "Component"]:
    interactive_elems, user_elems, elem_dict = set(), set(), dict()
    session_flag = gr.State({'generation_window': True})

    user_name = manager.get_elem_by_name('top.user_name')
    gr.Markdown('''### 生成数据管理''')
    with gr.Row():
        dataset_generation_name = gr.Dropdown(choices=[], label="生成数据集", scale=7, interactive=False)

        with gr.Column():
            btn_generation_show = gr.Button(value='展示数据', interactive=False)
            btn_generation_closeshow = gr.Button(value='关闭展示', interactive=False)
        with gr.Column():
            btn_generation_showmeta = gr.Button(value='元信息', interactive=False)
            btn_generation_remove = gr.Button(value='删除数据', interactive=False)

    with gr.Row():
        download_type = gr.Dropdown(choices=['xlsx', 'csv', 'json', 'jsonl'], label="保存文件类型", value='xlsx', scale=8, interactive=False)
        btn_generation_download = gr.Button(value='下载数据', scale=1, interactive=False)
        file_downloaded = gr.File(scale=1, visible=False)

    collection_generation_meta = gr.Json(label='数据集元信息', visible=False)
    collection_generation_data = gr.Dataframe(label='数据集展示', height=500, wrap=True, visible=False)
    collection_generation_pages = gr.Slider(label='pages', visible=False, interactive=True)

    user_elems.update({session_flag})
    interactive_elems.update({dataset_generation_name, btn_generation_show, btn_generation_closeshow, btn_generation_showmeta, btn_generation_remove, download_type, btn_generation_download, file_downloaded, collection_generation_pages})

    elem_dict.update(dict(
        session_flag=session_flag,
        dataset_generation_name=dataset_generation_name,
        btn_generation_show=btn_generation_show,
        btn_generation_closeshow=btn_generation_closeshow,
        btn_generation_showmeta=btn_generation_showmeta,
        btn_generation_remove=btn_generation_remove,
        download_type=download_type,
        btn_generation_download=btn_generation_download,
        file_downloaded=file_downloaded,
        collection_generation_meta=collection_generation_meta,
        collection_generation_data=collection_generation_data,
        collection_generation_pages=collection_generation_pages
    ))

    gr.Markdown('''### 生成配置''')
    # 生成基础配置
    generate_method = gr.Dropdown(label='方法选择', choices=GENERATE_METHOD, value=GENERATE_METHOD[0], interactive=False)
    with gr.Row():
        template_name = gr.Dropdown(label='模板名', choices=[],  scale=8, interactive=False)
        with gr.Column():
            but_template_preview = create_preview_box(user_name, template_name, tab='generation', typ='template')
            but_template_delete = gr.Button(value='删除', scale=1, interactive=False)
        with gr.Column():
            btn_generation_load = gr.Button(value='加载', scale=1, interactive=False)
            btn_template_download = gr.Button(value='下载', scale=1, interactive=False)
            file_template = gr.File(visible=False)

    with gr.Row():
        seed_name = gr.Dropdown(label='种子文件名', scale=8, interactive=False, choices=[])
        with gr.Column():
            but_seed_preview = create_preview_box(user_name, seed_name, tab='generation', typ='seed')
            but_seed_delete = gr.Button(value='删除', scale=1, interactive=False)
        with gr.Column():
            btn_seed_download = gr.Button(value='下载', scale=1, interactive=False)
            file_seed = gr.File(visible=False)

    user_elems.update({generate_method, template_name, seed_name})
    interactive_elems.update({btn_generation_load, btn_template_download, but_template_delete, btn_seed_download, but_seed_delete, generate_method, template_name, seed_name, file_template, file_seed})
    elem_dict.update(dict(
        generate_method=generate_method, template_name=template_name, btn_generation_load=btn_generation_load, btn_template_download=btn_template_download, but_template_delete=but_template_delete, seed_name=seed_name, btn_seed_download=btn_seed_download, but_seed_delete=but_seed_delete, file_seed=file_seed, file_template=file_template, **but_template_preview, **but_seed_preview
    ))
    # 文件上传
    with gr.Accordion(label="模板与种子文件管理", open=False) as llm_tab:
        with gr.Row():
            with gr.Column():
                template_upload = gr.File(label='模板', height=80)
                with gr.Row():
                    template_overwrite = gr.Checkbox(label='覆盖同名文件', value=False, interactive=False, scale=1)
                    btn_template_submit = gr.Button(value='上传', interactive=False, scale=2)

                seed_upload = gr.File(label='种子文件', height=80)
                with gr.Row():
                    seed_overwrite = gr.Checkbox(label='覆盖同名文件', value=False, interactive=False, scale=1)
                    btn_seed_submit = gr.Button(value='上传', interactive=False, scale=2)

            with gr.Column():
                with gr.Column():
                    template_input = gr.Textbox(label='编辑模板', lines=8, max_lines=8, placeholder='输入内容以创建自定义模板;\n请添加{sample_str0}字段在模板里，以便样本可以被顺利替换。\n如果想添加多个占位符，请使用{sample_str1},{sample_str2}', interactive=False)
                    template_sep = gr.Textbox(label='自定义分隔符', lines=1, max_lines=1, placeholder='输入自定义分隔符', interactive=False)
                    with gr.Row():
                        template_save_name = gr.Textbox(label='存储路径', interactive=False)
                        with gr.Column():
                            template_input_overwrite = gr.Checkbox(label='覆盖同名文件', value=False, interactive=False)
                            template_save_bt = gr.Button(value='保存', interactive=False)

    user_elems.update({})
    interactive_elems.update({template_input, template_sep, template_save_name, template_save_bt, template_overwrite, seed_overwrite, template_input_overwrite})
    elem_dict.update(dict(
        template_upload=template_upload, btn_template_submit=btn_template_submit, template_overwrite=template_overwrite, seed_upload=seed_upload, btn_seed_submit=btn_seed_submit, seed_overwrite=seed_overwrite, template_input=template_input, template_sep=template_sep, template_save_name=template_save_name, template_input_overwrite=template_input_overwrite, template_save_bt=template_save_bt))    

    extra = {}
    # FewShot生成器配置参数
    with gr.Accordion(label="FewShotGenerator-额外参数", open=False, visible=False) as gen_extra_tab:
        with gr.Row():
            FSG_min = gr.Number(label='采样下限', value=2, interactive=False)
            FSG_max = gr.Number(label='采样上限', value=4, interactive=False)
            FSG_typ = gr.Dropdown(label='拼接类型', value="prompt-response", choices=["prompt-response", "prompt-only", "response-only"], interactive=False)
            FSG_bt_preview = gr.Button(value='预览', interactive=False)
        with gr.Row():
            FSG_template_map = gr.Dropdown(label='template字段选择', interactive=False)
            FSG_sep_map = gr.Dropdown(label='sep字段选择', interactive=False)
            FSG_prompt_map = gr.Dropdown(label='prompt字段选择', interactive=False)
            FSG_response_map = gr.Dropdown(label='response字段选择', interactive=False)
        FSG_prompt_preview = gr.Textbox(label='完全prompt预览', lines=10, max_lines=10, interactive=False)

    user_elems.update({FSG_min, FSG_max, FSG_typ, FSG_template_map, FSG_sep_map, FSG_prompt_map, FSG_response_map})
    interactive_elems.update({FSG_min, FSG_max, FSG_typ, FSG_template_map, FSG_prompt_map, FSG_sep_map, FSG_response_map, FSG_bt_preview})
    extra.update(dict(FSG=dict(FSG_min=FSG_min, FSG_max=FSG_max, FSG_typ=FSG_typ, FSG_template_map=FSG_template_map, FSG_sep_map=FSG_sep_map, FSG_prompt_map=FSG_prompt_map, FSG_response_map=FSG_response_map,FSG_prompt_preview=FSG_prompt_preview, FSG_bt_preview=FSG_bt_preview)))
    elem_dict.update(gen_extra_tab=gen_extra_tab)    

    # Batch生成器配置参数
    with gr.Accordion(label="BatchGenerator-额外参数", open=False, visible=False) as gen_extra_batch_tab:
            BA_prompt_preview = gr.Textbox(label='完全prompt预览', interactive=False)
            with gr.Row():
                BA_template_map = gr.Dropdown(label='选择模板字段', interactive=False)
                BA_prompt_map = gr.Dropdown(label='种子字段', multiselect=True, interactive=False)
                BA_bt_preview = gr.Button(value='预览', interactive=False)

    user_elems.update({BA_template_map, BA_prompt_map})
    interactive_elems.update({BA_bt_preview, BA_template_map, BA_prompt_map})
    extra.update(dict(BA=dict(BA_prompt_preview=BA_prompt_preview,  BA_bt_preview=BA_bt_preview, BA_template_map=BA_template_map, BA_prompt_map=BA_prompt_map)))
    elem_dict.update(gen_extra_batch_tab=gen_extra_batch_tab)    

    with gr.Row():
        models_config_list = gr.Dropdown(label='模型配置选择', scale=7, interactive=False)
        with gr.Column():
            models_config_update = gr.Button(value='更新配置', scale=1, interactive=False)
            models_config_delete = gr.Button(value='删除配置', scale=1, interactive=False)

    with gr.Accordion(label="LLM 配置上传", open=False) as llm_tab:
        with gr.Row():
            with gr.Column(scale=4):
                with gr.Row():
                    with gr.Column():
                        api_type = gr.Dropdown(label='API类型', choices=['azure', 'openai', 'request'], value="openai", interactive=False)
                        api_base = gr.Textbox(label='API地址', value="", interactive=False)
                    with gr.Column():
                        api_key = gr.Textbox(label='API密钥', value="", interactive=False)
                        deployment_name = gr.Textbox(label='服务名', interactive=False, value="chat")
            with gr.Column(scale=4):
                with gr.Row():
                    # 线程数
                    thread_num = gr.Number(label='线程数', value=20, scale=2, minimum=1, maximum=20, interactive=False)
                    sleep_time = gr.Number(label='间隔时间', value=0, scale=2, minimum=0, maximum=10, interactive=False)
                with gr.Row():
                    temperature = gr.Slider(0.01, 1.5, value=0.75, step=0.01, scale=2, label='temperature', interactive=False)
                    top_p = gr.Slider(0.01, 1, value=0.7, step=0.01, scale=2, label='top-p', interactive=False)
        with gr.Row():
            models_config_name = gr.Textbox(label='API配置名', placeholder="输入您想保存的模型配置参数名", scale=8, interactive=False)
            with gr.Column():
                models_config_button = gr.Button(value="保存配置", scale=3, interactive=False)
                # 暂时不适用
                models_config_overwrite = gr.Checkbox(label='覆盖同名配置', scale=2, value=False, visible=False)

    user_elems.update({models_config_list, models_config_name, api_type, api_base, api_key, deployment_name, temperature, top_p, thread_num, sleep_time,})
    interactive_elems.update({models_config_list, models_config_update, models_config_delete, api_type, api_base, api_key, deployment_name, temperature, top_p, thread_num, sleep_time, models_config_name, models_config_button, models_config_overwrite})
    elem_dict.update(dict(
        models_config_list=models_config_list, models_config_update=models_config_update, models_config_delete=models_config_delete, llm_tab=llm_tab, models_config=dict(api_type=api_type, api_base=api_base, api_key=api_key,
        deployment_name=deployment_name, temperature=temperature, top_p=top_p,
        thread_num=thread_num, sleep_time=sleep_time), models_config_name=models_config_name, models_config_button=models_config_button, models_config_overwrite=models_config_overwrite
    ))

    with gr.Row():
        generate_number = gr.Number(label='设置生成数', info='最大生成数为10w', value=10, maximum=100000, scale=1, interactive=False)
        generate_fault_tolerance = gr.Number(label='容错数', info='生成时最大容错次数', value=0, minimum=0, maximum=100000, scale=1, interactive=False)
        generate_filename = gr.Textbox(label='输出文件名', placeholder="设置输出文件名", scale=3, interactive=False)
        with gr.Column(scale=1):
            generate_overwrite = gr.Checkbox(label='覆盖同名文件', value=False, scale=1, interactive=False)
        
    with gr.Row():
        btn_checkconfig = gr.Button(value='检查配置', scale=1, interactive=False)
        btn_checktasks = gr.Button(value='获取全局任务列表', scale=1, interactive=False)
        btn_generate = gr.Button(value='生成',scale=2, interactive=False)
        btn_continue = gr.Button(value='断点续连',scale=2, interactive=False)
        btn_interrupt = gr.Button(value='中断',scale=1, interactive=False)
        check_online_show = gr.Button(value='关闭实时显示',scale=1, interactive=False)

    user_elems.update({generate_number, generate_fault_tolerance, generate_filename, generate_overwrite})
    interactive_elems.update({generate_number, generate_fault_tolerance, generate_filename, btn_checkconfig, btn_checktasks, btn_generate, btn_continue, btn_interrupt, check_online_show, generate_overwrite})
    elem_dict.update(dict(
        generate_number=generate_number, generate_fault_tolerance=generate_fault_tolerance, generate_filename=generate_filename, btn_generate=btn_generate, btn_checkconfig=btn_checkconfig, btn_checktasks=btn_checktasks, btn_continue=btn_continue, btn_interrupt=btn_interrupt, check_online_show=check_online_show, generate_overwrite=generate_overwrite
    ))

    with gr.Column():
        with gr.Accordion(label='任务管理器', open=False) as task_manager:
            all_tasks = gr.DataFrame(visible=False, interactive=False)
        with gr.Accordion(label='进度管理器', open=False) as process_manager:
            process_bar = gr.Slider(visible=False, interactive=False)
            show_window = gr.Json(visible=False, elem_classes='json-container')
    elem_dict.update(dict(all_tasks=all_tasks, show_window=show_window, process_bar=process_bar))
    elem_dict.update(extra=extra)
    return elem_dict, interactive_elems, user_elems

def callback_init_generator():
    user_input = manager.get_elem_by_name('top.user_input')
    user_name = manager.get_elem_by_name('top.user_name')
    sys_info = manager.get_elem_by_name('top.sys_info')
    # 生成数据管理
    session_flag = manager.get_elem_by_name('generation.session_flag')

    dataset_generation_name = manager.get_elem_by_name('generation.dataset_generation_name')
    btn_generation_show = manager.get_elem_by_name('generation.btn_generation_show')
    btn_generation_showmeta = manager.get_elem_by_name('generation.btn_generation_showmeta')
    btn_generation_remove = manager.get_elem_by_name('generation.btn_generation_remove')
    btn_generation_closeshow = manager.get_elem_by_name('generation.btn_generation_closeshow')
    download_type = manager.get_elem_by_name('generation.download_type')
    btn_generation_download = manager.get_elem_by_name('generation.btn_generation_download')
    file_downloaded = manager.get_elem_by_name('generation.file_downloaded')

    collection_generation_meta = manager.get_elem_by_name('generation.collection_generation_meta')
    collection_generation_data = manager.get_elem_by_name('generation.collection_generation_data')
    collection_generation_pages = manager.get_elem_by_name('generation.collection_generation_pages')

    # 模板和种子文件选择
    template_name = manager.get_elem_by_name('generation.template_name')
    but_template_delete = manager.get_elem_by_name('generation.but_template_delete')
    btn_generation_load = manager.get_elem_by_name('generation.btn_generation_load')
    btn_template_download = manager.get_elem_by_name('generation.btn_template_download')
    file_template = manager.get_elem_by_name('generation.file_template')

    seed_name = manager.get_elem_by_name('generation.seed_name')
    but_seed_delete = manager.get_elem_by_name('generation.but_seed_delete')
    btn_seed_download = manager.get_elem_by_name('generation.btn_seed_download')
    file_seed = manager.get_elem_by_name('generation.file_seed')

    template_overwrite = manager.get_elem_by_name('generation.template_overwrite')
    seed_overwrite = manager.get_elem_by_name('generation.seed_overwrite')
    template_input_overwrite = manager.get_elem_by_name('generation.template_input_overwrite')

    # 模板和种子文件管理
    template_upload = manager.get_elem_by_name('generation.template_upload')
    seed_upload = manager.get_elem_by_name('generation.seed_upload')
    btn_template_submit = manager.get_elem_by_name('generation.btn_template_submit')
    btn_seed_submit = manager.get_elem_by_name('generation.btn_seed_submit')
    generate_method = manager.get_elem_by_name('generation.generate_method')

    template_input = manager.get_elem_by_name('generation.template_input')
    template_sep = manager.get_elem_by_name('generation.template_sep')
    template_save_name = manager.get_elem_by_name('generation.template_save_name')
    template_save_bt = manager.get_elem_by_name('generation.template_save_bt')

    # 生成方法配置
    FSG_min = manager.get_elem_by_name('generation.extra.FSG.FSG_min')
    FSG_max = manager.get_elem_by_name('generation.extra.FSG.FSG_max')
    FSG_typ = manager.get_elem_by_name('generation.extra.FSG.FSG_typ')
    FSG_template_map = manager.get_elem_by_name('generation.extra.FSG.FSG_template_map')
    FSG_sep_map = manager.get_elem_by_name('generation.extra.FSG.FSG_sep_map')
    FSG_prompt_map = manager.get_elem_by_name('generation.extra.FSG.FSG_prompt_map')
    FSG_response_map = manager.get_elem_by_name('generation.extra.FSG.FSG_response_map')

    FSG_bt_preview = manager.get_elem_by_name('generation.extra.FSG.FSG_bt_preview')
    FSG_prompt_preview = manager.get_elem_by_name('generation.extra.FSG.FSG_prompt_preview')

    BA_template_map = manager.get_elem_by_name('generation.extra.BA.BA_template_map')
    BA_prompt_map = manager.get_elem_by_name('generation.extra.BA.BA_prompt_map')
    BA_bt_preview = manager.get_elem_by_name('generation.extra.BA.BA_bt_preview')
    BA_prompt_preview = manager.get_elem_by_name('generation.extra.BA.BA_prompt_preview')

    models_config_list = manager.get_elem_by_name('generation.models_config_list')
    models_config_update = manager.get_elem_by_name('generation.models_config_update')
    models_config_delete = manager.get_elem_by_name('generation.models_config_delete')
    models_config_button = manager.get_elem_by_name('generation.models_config_button')
    # LLM 配置
    api_type = manager.get_elem_by_name('generation.models_config.api_type')
    api_base = manager.get_elem_by_name('generation.models_config.api_base')
    api_key = manager.get_elem_by_name('generation.models_config.api_key')
    deployment_name = manager.get_elem_by_name('generation.models_config.deployment_name')
    thread_num = manager.get_elem_by_name('generation.models_config.thread_num')
    sleep_time = manager.get_elem_by_name('generation.models_config.sleep_time')
    temperature = manager.get_elem_by_name('generation.models_config.temperature')
    top_p = manager.get_elem_by_name('generation.models_config.top_p')
    models_config_name = manager.get_elem_by_name('generation.models_config_name')

    gen_extra_tab = manager.get_elem_by_name('generation.gen_extra_tab')
    gen_extra_batch_tab = manager.get_elem_by_name('generation.gen_extra_batch_tab')
    btn_checkconfig = manager.get_elem_by_name('generation.btn_checkconfig')
    btn_checktasks = manager.get_elem_by_name('generation.btn_checktasks')
    btn_generate = manager.get_elem_by_name('generation.btn_generate')
    btn_continue = manager.get_elem_by_name('generation.btn_continue')
    btn_interrupt = manager.get_elem_by_name('generation.btn_interrupt')
    check_online_show = manager.get_elem_by_name('generation.check_online_show')

    all_tasks = manager.get_elem_by_name('generation.all_tasks')
    process_bar = manager.get_elem_by_name('generation.process_bar')
    show_window = manager.get_elem_by_name('generation.show_window')

    analysis_collection_name = manager.get_elem_by_name('analysis.analysis_collection_name')
    processing_collection_name = manager.get_elem_by_name('processing.processing_collection_name')

    # 生成数据管理
    btn_generation_show.click(read_data, inputs=[user_name, gr.State('generation'), dataset_generation_name, gr.State('type'), gr.State('generated_data')], outputs=[collection_generation_data]).then(show_pages, inputs=[user_name, gr.State('generation'), dataset_generation_name], outputs=collection_generation_pages).then(get_logs, [user_name], [sys_info])
    ## 分页滑片滑动切换页数
    collection_generation_pages.change(get_page_content, inputs=[user_name, gr.State('generation'), dataset_generation_name, collection_generation_pages, gr.State('type'), gr.State('generated_data')], outputs=[collection_generation_data])

    btn_generation_showmeta.click(show_meta, inputs=[user_name, gr.State('generation'), dataset_generation_name, gr.State('type'), gr.State('generated_data')], outputs=[collection_generation_meta]).then(get_logs, [user_name], [sys_info])
    btn_generation_closeshow.click(close_show, inputs=[gr.State(3)], outputs=[collection_generation_meta, collection_generation_data, collection_generation_pages]).then(get_logs, [user_name], [sys_info])

    btn_generation_remove.click(delete_data, inputs=[user_name, gr.State('generation'), dataset_generation_name, gr.State('type'), gr.State('generated_data')]).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('generated_data')], outputs=[dataset_generation_name]).then(get_logs, [user_name], [sys_info])

    btn_generation_download.click(download_file, inputs=[user_name, gr.State('generation'), dataset_generation_name, gr.State('type'), gr.State('generated_data'), download_type], outputs=[file_downloaded])
    file_downloaded.clear(lambda : gr.update(visible=False), outputs=file_downloaded)

    # 模板种子文件选择
    template_name.select(fsg_Temp_flush, inputs=[user_name, template_name, gr.State('type'), gr.State('template')], outputs=[FSG_template_map, FSG_sep_map, BA_template_map])

    but_template_delete.click(delete_data, [user_name, gr.State('generation'), template_name, gr.State('type'), gr.State('template')]).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('template')], outputs=[template_name]).then(get_logs, [user_name], [sys_info])

    btn_generation_load.click(loda_template, inputs=[user_name, gr.State('generation'), template_name, gr.State('type'), gr.State('template')], outputs=[template_input, template_sep, template_save_name])
    btn_template_download.click(download_file, inputs=[user_name, gr.State('generation'), template_name, gr.State('type'), gr.State('template'), download_type], outputs=[file_template])
    file_template.clear(lambda: gr.update(visible=False), outputs=file_template)

    seed_name.select(fsg_PR_flush, inputs=[user_name, seed_name, gr.State('type'), gr.State('seed')], outputs=[FSG_prompt_map, FSG_response_map, BA_prompt_map])

    but_seed_delete.click(delete_data, [user_name, gr.State('generation'), seed_name, gr.State('type'), gr.State('seed')]).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('seed')], outputs=[seed_name]).then(get_logs, [user_name], [sys_info])

    btn_seed_download.click(download_file, inputs=[user_name, gr.State('generation'), seed_name, gr.State('type'), gr.State('seed'), download_type], outputs=[file_seed])
    file_seed.clear(lambda: gr.update(visible=False), outputs=file_seed)

    # 模板种子文件上传
    template_upload.upload(upload_file, [user_name], outputs=btn_template_submit, queue=False)
    template_upload.clear(clear_file, outputs=[btn_template_submit], queue=False)

    btn_template_submit.click(submit_file, [user_name, template_upload, gr.State('generation'), gr.State('template'), template_overwrite], [btn_template_submit]).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('template'),template_name], outputs=[template_name]).then(get_logs, [user_name], [sys_info])

    seed_upload.upload(upload_file, [user_name], outputs=btn_seed_submit, queue=False)
    seed_upload.clear(clear_file, outputs=btn_seed_submit, queue=False)

    btn_seed_submit.click(lambda: gr.update(interactive=False), outputs=[btn_seed_submit]).then(submit_file, [user_name, seed_upload, gr.State('generation'), gr.State('seed'), seed_overwrite], [btn_seed_submit]).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('seed'), seed_name], outputs=[seed_name]).then(get_logs, [user_name], [sys_info])

    generate_method.select(show_extra, inputs=[generate_method], outputs=[gen_extra_tab, gen_extra_batch_tab], queue=False)
    # 
    template_save_bt.click(template_input_save, inputs=[user_name, template_input, template_sep, template_save_name, template_input_overwrite], concurrency_limit=1000).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('template'), template_name], outputs=[template_name]).then(get_logs, [user_name], [sys_info])
    # 生成方法配置
    FSG_typ.select(fsg_typ_select, inputs=[FSG_typ], outputs=[FSG_prompt_map, FSG_response_map])
    FSG_bt_preview.click(gr_generate_query, inputs=[user_name, seed_name, template_name, FSG_min, FSG_max, FSG_typ, FSG_template_map, FSG_sep_map, FSG_prompt_map, FSG_response_map], outputs=[FSG_prompt_preview]).then(get_logs, [user_name], [sys_info])

    BA_bt_preview.click(gr_generate_ba_query, inputs=[user_name, template_name, seed_name, BA_template_map, BA_prompt_map], outputs=[BA_prompt_preview], queue=True, concurrency_limit=1000)
    # 大模型配置--更新配置
    models_config_update.click(find_item_models_config, inputs=[user_name, models_config_list], outputs=[api_type, api_base, api_key, deployment_name, thread_num, sleep_time, temperature, top_p, models_config_name])
    # 大模型配置--删除
    models_config_delete.click(delete_models_config, inputs=[user_name, models_config_list]).then(find_list_models_config, inputs=[user_name], outputs=[models_config_list])
    # 大模型配置--保存
    models_config_button.click(save_models_config, inputs=set(manager.get_list_elems(typ='user')+[gr.State('NamedModelConfig')])).then(find_list_models_config, inputs=[user_name], outputs=[models_config_list])

    btn_checkconfig.click(lambda x: gr.update(value=manager.get_current_conf(x), visible=True), inputs=set(manager.get_list_elems(typ='user')+[gr.State("generation_config")]), outputs=show_window, queue=False)

    btn_checktasks.click(get_all_tasks, outputs=[all_tasks])

    btn_generate.click(lambda: gr.update(interactive=False), outputs=[btn_generate]).then(generate_data, inputs=set(manager.get_list_elems(typ='user')+[gr.State('generation_config')]), outputs=[process_bar, show_window, sys_info], concurrency_limit=100).then(lambda: gr.update(interactive=True), outputs=[btn_generate]).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('generated_data'), dataset_generation_name], outputs=dataset_generation_name).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('generated_data'), analysis_collection_name], outputs=analysis_collection_name).then(generation_get_filed_list, inputs=[user_name, gr.State('generation'), gr.State('type'), gr.State('generated_data'), processing_collection_name], outputs=processing_collection_name).then(get_logs, [user_name], [sys_info])

    btn_continue.click(gr_generate_continue, inputs=[user_name, session_flag], outputs=[process_bar, show_window, sys_info], concurrency_limit=1000)
    btn_interrupt.click(make_interrupt, inputs=[user_name, gr.State('generation')], concurrency_limit=1000, queue=True).then(get_logs, [user_name], [sys_info])
    check_online_show.click(close_generation_window, inputs=[session_flag], concurrency_limit=1000, queue=True)

# 登录状态初始化
def generation_login_component():
    dataset_generation_name = manager.get_elem_by_name('generation.dataset_generation_name')
    template_name = manager.get_elem_by_name('generation.template_name')
    seed_name = manager.get_elem_by_name('generation.seed_name')
    models_config_list = manager.get_elem_by_name('generation.models_config_list')

    return [dataset_generation_name, template_name, seed_name, models_config_list]

def generation_login_status(user_name):
    # 1.获取生成的数据集，模板和种子文件
    generation_datasets = api_get_filed_list(user_name, 'generation', 'type', 'generated_data')
    template_list = api_get_filed_list(user_name, 'generation', 'type', 'template')
    seed_list = api_get_filed_list(user_name, 'generation', 'type', 'seed')
    response = api_get_userspace(user_name, 'models_config')
    if not response_checker(response): models_config_list=[]
    else: models_config_list = response['data']

    if isinstance(generation_datasets, dict) and generation_datasets.get('err_code', 0) != 0:
        api_logs_write(user_name, f'[{__name__}] '+generation_datasets['err_content'])
        return [gr.update()]*4
    if isinstance(template_list, dict) and template_list.get('err_code', 0) != 0:
        api_logs_write(user_name, f'[{__name__}] '+template_list['err_content'])
        return [gr.update()]*4
    if isinstance(seed_list, dict) and seed_list.get('err_code', 0) != 0:
        api_logs_write(user_name, f'[{__name__}] '+seed_list['err_content'])
        return [gr.update()]*4

    return gr.update(choices=generation_datasets), gr.update(choices=template_list), gr.update(choices=seed_list), gr.update(choices=list(reversed(models_config_list)), value=None)

# 登出状态初始化
def generation_logout_component():
    collection_generation_pages = manager.get_elem_by_name('generation.collection_generation_pages')
    process_bar = manager.get_elem_by_name('generation.process_bar')
    show_window = manager.get_elem_by_name('generation.show_window')

    return [collection_generation_pages, process_bar, show_window]

def generation_logout_status():
    # 1.获取生成的数据集，模板和种子文件
    return [gr.update(visible=False)]*3