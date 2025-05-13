import gradio as gr
from typing import Optional
from manager import manager

from components import (
    create_top_tab,
    callback_init_top,
    create_datamanager_tab,
    callback_init_datamanager,
    create_analysis_tab,
    callback_init_analysis,
    create_generator_tab,
    callback_init_generator,
    # create_pdf2markdown_tab,
    # callback_init_preprocess,
    # create_regresstest_tab,
    # callback_init_regresstest,
    create_processing_tab,
    callback_init_processing,
)
from conf.sysconf import CSS, JS

def create_ui() -> gr.Blocks:
    with gr.Blocks(title="MildGiraffe Data Platform", css=CSS) as demo:
        gr.Markdown(
            """
            # MildGiraffe Data Platform
            小鹿数据管理平台

            项目源码地址：https://github.com/PPnorain/MildGiraffeDataFrame.git
            
            微信：play-277

            """
        , elem_classes=["custom-md"])
        with gr.Row("Top"):
            top_elems, top_interactive_elems, top_user_elems = create_top_tab()
            manager.tree_elems["top"] = top_elems
            manager.user_elems |= top_user_elems

        with gr.Tab("Data Manager", elem_classes=["tabselect"]):
            datamanager_elems, datamanager_interactive_elems, datamanager_user_elems = create_datamanager_tab()
            manager.tree_elems["datamanager"] = datamanager_elems
            manager.interactive_elems |= datamanager_interactive_elems
            manager.user_elems |= datamanager_user_elems 

        with gr.Tab("Data Analysis", elem_classes=["tabselect"]):
            analysis_elems, analysis_interactive_elems, analysis_user_elems = create_analysis_tab()
            manager.tree_elems["analysis"] = analysis_elems
            manager.interactive_elems |= analysis_interactive_elems
            manager.user_elems |= analysis_user_elems

        with gr.Tab("Data Generation", elem_classes=["tabselect"]):
            generate_elems, generate_interactive_elems, generate_user_elems = create_generator_tab()
            manager.tree_elems["generation"] = generate_elems
            manager.interactive_elems |= generate_interactive_elems
            manager.user_elems |= generate_user_elems

        with gr.Tab("Data Preprocessing", elem_classes=["tabselect"]):
            generate_elems, generate_interactive_elems, generate_user_elems = create_processing_tab()
            manager.tree_elems["processing"] = generate_elems
            manager.interactive_elems |= generate_interactive_elems
            manager.user_elems |= generate_user_elems

        # with gr.Tab("Data Preprocess", elem_classes=["tabselect"]):
        #     preprocess_elems, preprocess_interactive_elems, preprocess_user_elems = create_pdf2markdown_tab()
        #     manager.tree_elems["preprocess"] = preprocess_elems
        #     manager.interactive_elems |= preprocess_interactive_elems
        #     manager.user_elems |= preprocess_user_elems

        # with gr.Tab("Regress Test", elem_classes=["tabselect"]):
        #     preprocess_elems, preprocess_interactive_elems, preprocess_user_elems = create_regresstest_tab()
        #     manager.tree_elems["regresstest"] = preprocess_elems
        #     manager.interactive_elems |= preprocess_interactive_elems
        #     manager.user_elems |= preprocess_user_elems

        callback_init_top()
        callback_init_datamanager()
        callback_init_analysis()
        callback_init_generator()
        callback_init_processing()
        # callback_init_preprocess()
        # callback_init_regresstest()
    
    demo.load(js=JS)
    return demo

if __name__ == "__main__":
    demo = create_ui()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=8000, share=False, inbrowser=True, show_error=True, max_threads=100, favicon_path='../../reference/images/giraffe.svg')