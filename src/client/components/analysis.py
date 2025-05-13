import os, json
import gradio as gr
from typing import TYPE_CHECKING, Dict
from manager import manager
from conf.userconf import SEARCH_METHOD_NEW, DUMPLICATE_METHOD, SIMILAR_METHOD
from apiweb import api_store, api_status_abort
from common import get_logs, get_droplist_typ, get_droplist_check, close_show, show_pages, get_page_content
from func.analysis.analysis import plot_data, check_duplicate_null, show_dataset, show_meta, get_column_name, analysis_dataset, show_extra, search_result_data, get_page_content_tab
from func.datamanager.datamanager import change_status, show_subtab, show_search_conf
from func.generator.generator import generation_get_filed_list
from func.datamanager.search_algro import search_data
if TYPE_CHECKING:
    from gradio.components import Component

def create_analysis_tab() -> Dict[str, "Component"]:
    interactive_elems, user_elems, elem_dict = set(), set(), dict()
    user_name = manager.get_elem_by_name('top.user_name')

    gr.Markdown("### 数据集查看")
    with gr.Row():
        analysis_source = gr.Dropdown(choices=["dataset_info", "generation", "processing"], scale=1, value=None, label="下拉选择数据源", interactive=False)
        analysis_collection_name = gr.Dropdown(choices=[], scale=2, value=None, label="下拉选择任务数据集", interactive=False)
        with gr.Column():
            with gr.Row():
                analysis_meta_button = gr.Button(value='元信息', scale=1, interactive=False)
                analysis_data_button = gr.Button(value='数据', scale=1, interactive=False)
            analysis_data_close_button = gr.Button(value='关闭显示', scale=3, interactive=False)

    with gr.Accordion("数据内容", open=True, visible=False) as analysis_show_data:
        analysis_collection_meta = gr.Json(label='数据元信息', visible=False)
        analysis_collection_data = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False, interactive=False)
        analysis_collection_pages = gr.Slider(label='pages', visible=False, interactive=True)

    user_elems.update({analysis_source, analysis_collection_name})
    interactive_elems.update({analysis_source, analysis_collection_name, analysis_meta_button, analysis_data_button, analysis_data_close_button, analysis_collection_pages})
    elem_dict.update(dict(
        analysis_source=analysis_source,
        analysis_collection_name=analysis_collection_name, analysis_meta_button=analysis_meta_button,
        analysis_data_button=analysis_data_button, analysis_data_close_button=analysis_data_close_button,
        analysis_show_data=analysis_show_data,
        analysis_collection_meta=analysis_collection_meta, analysis_collection_data=analysis_collection_data,
        analysis_collection_pages=analysis_collection_pages,
    ))

    with gr.Tab("数据统计信息分析", elem_classes=["tabselect"]):
        with gr.Row():
            analysis_process_bar_plt = gr.Plot(scale=1, visible=False)
            analysis_process_bar_text = gr.Textbox(scale=2, visible=False)
        with gr.Row():
            analysis_score = gr.Plot(scale=1, visible=False)
            analysis_score_detail = gr.Textbox(label="各维度得分", scale=1, lines=7, max_lines=8, interactive=False, visible=False, show_copy_button=True)
            analysis_desc_detail = gr.Textbox(label="问题描述", scale=2, lines=6, max_lines=7, interactive=False, visible=False, show_copy_button=True)
        with gr.Row():
            with gr.Column(scale=3):
                analysis_check_btn1 = gr.Button(visible=False)
            with gr.Column(scale=1):
                analysis_check_btn = gr.Button(value="开始健康分析", scale=1, interactive=False)

    user_elems.update({})
    interactive_elems.update({analysis_check_btn})
    elem_dict.update(dict(
        analysis_score=analysis_score,
        analysis_score_detail=analysis_score_detail, analysis_desc_detail=analysis_desc_detail, analysis_check_btn=analysis_check_btn,
        analysis_process_bar_plt=analysis_process_bar_plt, analysis_process_bar_text=analysis_process_bar_text
    ))
        
    with gr.Tab("数据细节信息分析", elem_classes=["tabselect"]):
        with gr.Tab("查看数据分布"):
            with gr.Accordion(open=True):
                with gr.Row():
                    analysis_label = gr.Dropdown(choices=[], label="选择数据列", scale=1)
                    analysis_class = gr.Dropdown(choices=["柱状图", "饼状图", "折线图"], value="柱状图", label="选择图表类型", scale=1)
                    analysis_label_type = gr.Dropdown(choices=["单标签", "多标签", "ngram"], value="单标签", label="选择标签类型", scale=1)
                    with gr.Column(scale=1):
                        plot_generate_btn = gr.Button(value="生成")
                        plot_retract_btn = gr.Button(value="收起")
                with gr.Row():
                    ngram_rate = gr.Number(label="百分比", minimum=0, maximum=1, step=0.1, value=0.1, visible=False, scale=1)
                    ngram_n = gr.Number(label="ngram", minimum=0, maximum=10, step=1, value=5, visible=False, scale=1)

            with gr.Accordion(label="查看统计结果", open=True, visible=True):
                with gr.Row():
                    with gr.Column(scale=5):
                        analysis_label_text = gr.Textbox(label="最大/最小类别", interactive=False, visible=True, max_lines=2, show_copy_button=True)
                        analysis_label_df = gr.DataFrame(height=220, interactive=False, visible=False, wrap=True)
                    with gr.Column(scale=5):
                        analysis_plt = gr.Plot(visible=False)

            with gr.Accordion(label="查看统计数据", open=True, visible=False) as accordion_class:
                with gr.Row():
                    with gr.Column(scale=3):
                        search_class = gr.Dropdown(choices=[], label="选择数据类别", scale=3)
                    with gr.Column(scale=1):
                        btn_search_class = gr.Button(value="确认")
                        btn_search_class_retract = gr.Button(value="收起")
                with gr.Row():
                    search_class_data = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False)
                    search_class_data_origin = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False)
                    search_class_data_json = gr.Json(label="结果数据（json）", visible=False)

            user_elems.update({analysis_label, analysis_class, analysis_label_type, ngram_rate, ngram_n})
            interactive_elems.update({analysis_label, analysis_class, analysis_label_type, plot_generate_btn, plot_retract_btn, ngram_rate, ngram_n})
            elem_dict.update(dict(
                analysis_label=analysis_label, analysis_class=analysis_class, analysis_label_type=analysis_label_type,
                plot_generate_btn=plot_generate_btn, plot_retract_btn=plot_retract_btn, analysis_label_text=analysis_label_text, analysis_label_df=analysis_label_df,
                analysis_plt=analysis_plt, ngram_rate=ngram_rate, ngram_n=ngram_n
            ))

        with gr.Tab("查看长度分布"):
            with gr.Row():
                analysis_len_label = gr.Dropdown(choices=[], label="选择数据列", scale=1)
                analysis_len_class = gr.Dropdown(choices=["柱状图", "饼状图", "折线图"], value="柱状图", label="选择图表类型", scale=2)
                with gr.Column(scale=1):
                    plot_generate_len_btn = gr.Button(value="生成")
                    plot_retract_len_btn = gr.Button(value="收起")

            with gr.Accordion(label="查看统计结果", open=True, visible=True):
                with gr.Row():
                    with gr.Column(scale=5):
                        analysis_label_len_text = gr.Textbox(label="最大/最小类别", interactive=False, max_lines=2, visible=True, show_copy_button=True)
                        analysis_label_len_df = gr.DataFrame(height=220, interactive=False, visible=False, wrap=True)
                    with gr.Column(scale=5):
                        analysis_len_plt = gr.Plot(visible=False)

            with gr.Accordion(label="查看统计数据", open=True, visible=False) as accordion_length:
                with gr.Row():
                    with gr.Column(scale=3):
                        search_length = gr.Dropdown(choices=[], label="选择数据长度")
                    with gr.Column(scale=1):
                        btn_search_length = gr.Button(value="确认")
                        btn_search_length_retract = gr.Button(value="收起")
                with gr.Row():
                    search_length_data_origin = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False)
                    search_length_data_json = gr.Json(label="结果数据（json）", visible=False)
                    search_length_data = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False)

            user_elems.update({analysis_len_label, analysis_len_class})
            interactive_elems.update(
                {analysis_len_label, analysis_len_class, plot_generate_len_btn, plot_retract_len_btn})
            elem_dict.update(dict(
                analysis_len_label=analysis_len_label, analysis_len_class=analysis_len_class,
                plot_generate_len_btn=plot_generate_len_btn, plot_retract_len_btn=plot_retract_len_btn,
                analysis_label_len_text=analysis_label_len_text, analysis_label_len_df=analysis_label_len_df,
                analysis_len_plt=analysis_len_plt
            ))

        with gr.Tab("查看聚类分布"):
            with gr.Accordion(open=True):
                with gr.Row():
                    cluster_type = gr.Dropdown(choices=["text", "semantic"], value="text", label="选择聚类特征", scale=1)
                    cluster_label = gr.Dropdown(choices=[], label="选择数据列", scale=2)
                    cluster_figure_class = gr.Dropdown(choices=["柱状图", "饼状图", "聚类散点图"], value="柱状图", label="选择图表类型", scale=1)
                with gr.Row():
                    cluster_method = gr.Dropdown(choices=["Kmeans", "DBSCAN", "Hierarchical"], label="选择聚类方法", value="Kmeans", scale=1)
                    n_clusters = gr.Number(label="聚类个数", minimum=0, maximum=10, value=5, visible=True, scale=1)
                    distance_threshold = gr.Number(label="距离阈值(优先)", minimum=0, maximum=20, step=0.1, visible=False, scale=1)
                    eps = gr.Slider(label="距离阈值", minimum=0, maximum=1, step=0.1, value=0.1, visible=False, scale=1)
                    min_samples = gr.Number(label="最小样本数", minimum=1, maximum=20, value=1, visible=False, scale=1)
                    with gr.Column(scale=1):
                        plot_cluster_btn = gr.Button(value="生成")
                        plot_retract_cluster_btn = gr.Button(value="收起")

            with gr.Accordion(label="查看统计结果", open=True, visible=True):
                with gr.Row():
                    with gr.Column(scale=5):
                        analysis_cluster_text = gr.Textbox(label="聚类结果", interactive=False, lines=4, visible=True, show_copy_button=True)
                        analysis_cluster_df = gr.DataFrame(label="各类别统计", height=180, interactive=False, visible=False, wrap=True, show_label=False)

                    with gr.Column(scale=5):
                        analysis_cluster_plt = gr.Plot(visible=False)

            with gr.Accordion(label="查看统计数据", open=True, visible=False) as accordion_cluster:
                with gr.Row():
                    with gr.Column(scale=3):
                        search_cluster = gr.Dropdown(choices=[], label="选择数据类别", scale=3)
                    with gr.Column(scale=1):
                        btn_search_cluster = gr.Button(value="确认")
                        btn_search_cluster_retract = gr.Button(value="收起")
                with gr.Row():
                    search_cluster_data_origin = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False)
                    search_cluster_data_json = gr.Json(label="结果数据（json）", visible=False)
                    search_cluster_data = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False)

            user_elems.update({cluster_type, cluster_method, cluster_label, cluster_figure_class, n_clusters, distance_threshold, eps, min_samples})
            interactive_elems.update(
                {cluster_type, cluster_method, cluster_label, cluster_figure_class, plot_cluster_btn, plot_retract_cluster_btn,
                 n_clusters, distance_threshold, eps, min_samples})
            elem_dict.update(dict(
                cluster_type=cluster_type, cluster_method=cluster_method,
                cluster_label=cluster_label, cluster_figure_class=cluster_figure_class,
                plot_cluster_btn=plot_cluster_btn, plot_retract_cluster_btn=plot_retract_cluster_btn, analysis_cluster_text=analysis_cluster_text, analysis_cluster_df=analysis_cluster_df, analysis_cluster_plt=analysis_cluster_plt,
                n_clusters=n_clusters, distance_threshold=distance_threshold, eps=eps, min_samples=min_samples
            ))
        
        with gr.Tab("缺失与重复"):
            with gr.Accordion(open=True):
                with gr.Row():
                    analysis_label_new = gr.Dropdown(choices=["整行"], scale=1, label="选择数据列")
                    analysis_null_dup = gr.Dropdown(choices=["缺失值", "重复值"], value="缺失值", scale=2, label="查看类型")
                    with gr.Column(scale=1):
                        rate_show_btn = gr.Button(value="查看统计", interactive=False)
                        rate_retract_btn = gr.Button(value="收起统计", interactive=False)
                with gr.Row():
                    analysis_dup_method = gr.Dropdown(choices=DUMPLICATE_METHOD, value="Exact_Match", scale=1, label="选择方法", visible=False)
                    analysis_dup_threshold = gr.Slider(label="阈值", minimum=0, maximum=1, step=0.01, visible=False)
                    ngram_dup = gr.Number(label="ngram", minimum=1, maximum=10, value=1, step=1, visible=False)
            with gr.Accordion(label="查看结果", open=True, visible=True) as show_null_dup:
                with gr.Column(scale=5):
                    # 缺失值
                    missing_dum_rate = gr.Textbox(label="统计结果", interactive=False, visible=True)
                    missing_dum_df = gr.DataFrame(label="查看数据", height=300, interactive=False, visible=False, wrap=True)

            user_elems.update({})
            interactive_elems.update({analysis_label_new, analysis_null_dup, rate_show_btn, rate_retract_btn, analysis_dup_method, analysis_dup_threshold, ngram_dup})
            elem_dict.update(dict(
                analysis_label_new=analysis_label_new,
                missing_dum_df=missing_dum_df, missing_dum_rate=missing_dum_rate, analysis_null_dup=analysis_null_dup,
                rate_show_btn=rate_show_btn, rate_retract_btn=rate_retract_btn, show_null_dup=show_null_dup,
                analysis_dup_method=analysis_dup_method, analysis_dup_threshold=analysis_dup_threshold, ngram_dup=ngram_dup
            ))

        # 2024.5.28 新增数据展示
        user_elems.update({search_class, search_length, search_cluster})
        interactive_elems.update(
            {search_class, btn_search_class, btn_search_class_retract,
                search_length, btn_search_length, btn_search_length_retract,
                search_cluster, btn_search_cluster, btn_search_cluster_retract})

        elem_dict.update(dict(
            search_class=search_class, btn_search_class=btn_search_class, btn_search_class_retract=btn_search_class_retract,
            search_length=search_length, btn_search_length=btn_search_length, btn_search_length_retract=btn_search_length_retract,
            search_cluster=search_cluster, btn_search_cluster=btn_search_cluster, btn_search_cluster_retract=btn_search_cluster_retract,
            search_class_data_origin=search_class_data_origin, search_length_data_origin=search_length_data_origin, search_cluster_data_origin=search_cluster_data_origin,
            search_class_data=search_class_data, search_length_data=search_length_data, search_cluster_data=search_cluster_data,
            search_class_data_json=search_class_data_json, search_length_data_json=search_length_data_json, search_cluster_data_json=search_cluster_data_json,
            accordion_class=accordion_class, accordion_length=accordion_length, accordion_cluster=accordion_cluster
        ))

    with gr.Tab("数据搜索", elem_classes=["tabselect"]):
        with gr.Row():
            search_analysis_column = gr.Dropdown(choices=[], label="搜索字段", scale=3)
            with gr.Column(scale=1):
                search_analysis_btn = gr.Button(value='搜索', interactive=False)
                search_analysis_retract = gr.Button(value='收起', interactive=True)
        with gr.Accordion(label="搜索配置", open=True, visible=True) as analysis_search_config:
            with gr.Row():
                search_analysis_method = gr.Dropdown(choices=SEARCH_METHOD_NEW, label='搜索算法', interactive=False, scale=1)
                search_analysis_keyword = gr.Textbox(label="关键字搜索", scale=1, visible=False)
                search_analysis_regex = gr.Textbox(label="正则匹配搜索", scale=1, visible=False)
            with gr.Accordion(label="聚类搜索配置", open=True, visible=False) as search_cluster_config:
                with gr.Row():
                    search_cluster_type = gr.Dropdown(choices=["text", "semantic"], value="text", label="选择聚类特征", scale=1)
                    search_cluster_method = gr.Dropdown(choices=["Kmeans", "Hierarchical"], label="选择聚类方法", value="Kmeans", scale=1)
                    search_n_clusters = gr.Number(label="聚类个数", minimum=1, step=1, value=2, visible=True, scale=1)
            with gr.Accordion(label="相似搜索配置", open=True, visible=False) as search_similar_config:
                with gr.Row():
                    search_similar_method = gr.Dropdown(choices=SIMILAR_METHOD, value="difflib_distance", scale=1, label="选择方法")
                    search_similar_query = gr.Textbox(label="查询语句", scale=3, visible=True)
                    search_similar_threshold = gr.Slider(label="阈值", minimum=0, maximum=1, step=0.1)
                    search_similar_ngram = gr.Number(label="ngram", minimum=1, maximum=10, value=1, step=1, visible=False)

        with gr.Accordion(label="数据搜索结果", open=True, visible=False) as analysis_search_result:
            search_analysis_metainfo = gr.Json(label='搜索结果统计信息')
            search_analysis_resultinfo = gr.Dataframe(label='搜索结果详细信息', type="pandas", height=500, wrap=True, visible=False)

        user_elems.update({search_analysis_column, search_analysis_method, search_analysis_keyword, search_analysis_regex,
                           search_cluster_type, search_cluster_method, search_n_clusters,
                           search_similar_method, search_similar_threshold, search_similar_query, search_similar_ngram})
        interactive_elems.update({search_analysis_method, search_analysis_btn, search_analysis_retract})
        elem_dict.update(dict(
            search_analysis_column=search_analysis_column, search_analysis_method=search_analysis_method, search_analysis_btn=search_analysis_btn,
            search_analysis_retract=search_analysis_retract, search_analysis_keyword=search_analysis_keyword, search_analysis_regex=search_analysis_regex,
            cluster_search_config=dict(search_cluster_type=search_cluster_type, search_cluster_method=search_cluster_method, search_n_clusters=search_n_clusters),
            similar_search_config=dict(search_similar_method=search_similar_method, search_similar_query=search_similar_query, search_similar_threshold=search_similar_threshold, search_similar_ngram=search_similar_ngram),
            search_analysis_metainfo=search_analysis_metainfo, search_analysis_resultinfo=search_analysis_resultinfo,
            analysis_search_config=analysis_search_config, search_cluster_config=search_cluster_config, search_similar_config=search_similar_config, analysis_search_result=analysis_search_result
        ))
    return elem_dict, interactive_elems, user_elems

def callback_init_analysis():
    user_name = manager.get_elem_by_name('top.user_name')
    sys_info = manager.get_elem_by_name('top.sys_info')
    analysis_source = manager.get_elem_by_name('analysis.analysis_source')
    analysis_collection_name = manager.get_elem_by_name('analysis.analysis_collection_name')

    # 数据显示组件
    analysis_meta_button = manager.get_elem_by_name('analysis.analysis_meta_button')
    analysis_data_button = manager.get_elem_by_name('analysis.analysis_data_button')
    analysis_data_close_button = manager.get_elem_by_name('analysis.analysis_data_close_button')

    analysis_show_data = manager.get_elem_by_name('analysis.analysis_show_data')
    analysis_collection_meta = manager.get_elem_by_name('analysis.analysis_collection_meta')
    analysis_collection_data = manager.get_elem_by_name('analysis.analysis_collection_data')
    analysis_collection_pages = manager.get_elem_by_name('analysis.analysis_collection_pages')

    # 数据统计分析组件
    ## 数据分布组件
    analysis_label = manager.get_elem_by_name('analysis.analysis_label')
    analysis_class = manager.get_elem_by_name('analysis.analysis_class')
    analysis_label_type = manager.get_elem_by_name('analysis.analysis_label_type')
    analysis_label_text = manager.get_elem_by_name('analysis.analysis_label_text')
    analysis_label_df = manager.get_elem_by_name('analysis.analysis_label_df')

    plot_generate_btn = manager.get_elem_by_name('analysis.plot_generate_btn')
    plot_retract_btn = manager.get_elem_by_name('analysis.plot_retract_btn')
    analysis_plt = manager.get_elem_by_name('analysis.analysis_plt')

    ## 2024.4.25 长度分析组件
    analysis_len_label = manager.get_elem_by_name('analysis.analysis_len_label')
    analysis_len_class = manager.get_elem_by_name('analysis.analysis_len_class')
    analysis_label_len_text = manager.get_elem_by_name('analysis.analysis_label_len_text')
    analysis_label_len_df = manager.get_elem_by_name('analysis.analysis_label_len_df')

    plot_generate_len_btn = manager.get_elem_by_name('analysis.plot_generate_len_btn')
    plot_retract_len_btn = manager.get_elem_by_name('analysis.plot_retract_len_btn')
    analysis_len_plt = manager.get_elem_by_name('analysis.analysis_len_plt')

    analysis_process_bar_plt = manager.get_elem_by_name('analysis.analysis_process_bar_plt')
    analysis_process_bar_text = manager.get_elem_by_name('analysis.analysis_process_bar_text')

    ## 2024.5.22 聚类分布组件
    cluster_type = manager.get_elem_by_name('analysis.cluster_type')
    cluster_method = manager.get_elem_by_name('analysis.cluster_method')
    cluster_label = manager.get_elem_by_name('analysis.cluster_label')
    cluster_figure_class = manager.get_elem_by_name('analysis.cluster_figure_class')
    plot_cluster_btn = manager.get_elem_by_name('analysis.plot_cluster_btn')
    plot_retract_cluster_btn = manager.get_elem_by_name('analysis.plot_retract_cluster_btn')
    analysis_cluster_text = manager.get_elem_by_name('analysis.analysis_cluster_text')
    analysis_cluster_df = manager.get_elem_by_name('analysis.analysis_cluster_df')
    analysis_cluster_plt = manager.get_elem_by_name('analysis.analysis_cluster_plt')

    ### 参数配置组件
    ngram_rate = manager.get_elem_by_name('analysis.ngram_rate')
    ngram_n = manager.get_elem_by_name('analysis.ngram_n')
    n_clusters = manager.get_elem_by_name('analysis.n_clusters')
    distance_threshold = manager.get_elem_by_name('analysis.distance_threshold')
    eps = manager.get_elem_by_name('analysis.eps')
    min_samples = manager.get_elem_by_name('analysis.min_samples')

    ## 2024.5.28 分布/细节数据展示
    search_class = manager.get_elem_by_name('analysis.search_class')
    btn_search_class = manager.get_elem_by_name('analysis.btn_search_class')
    btn_search_class_retract = manager.get_elem_by_name('analysis.btn_search_class_retract')
    search_length = manager.get_elem_by_name('analysis.search_length')
    btn_search_length = manager.get_elem_by_name('analysis.btn_search_length')
    btn_search_length_retract = manager.get_elem_by_name('analysis.btn_search_length_retract')
    search_cluster = manager.get_elem_by_name('analysis.search_cluster')
    btn_search_cluster = manager.get_elem_by_name('analysis.btn_search_cluster')
    btn_search_cluster_retract = manager.get_elem_by_name('analysis.btn_search_cluster_retract')
    search_class_data = manager.get_elem_by_name('analysis.search_class_data')
    search_length_data = manager.get_elem_by_name('analysis.search_length_data')
    search_cluster_data = manager.get_elem_by_name('analysis.search_cluster_data')
    search_class_data_origin = manager.get_elem_by_name('analysis.search_class_data_origin')
    search_class_data_json = manager.get_elem_by_name('analysis.search_class_data_json')
    search_length_data_origin = manager.get_elem_by_name('analysis.search_length_data_origin')
    search_length_data_json = manager.get_elem_by_name('analysis.search_length_data_json')
    search_cluster_data_origin = manager.get_elem_by_name('analysis.search_cluster_data_origin')
    search_cluster_data_json = manager.get_elem_by_name('analysis.search_cluster_data_json')
    accordion_class = manager.get_elem_by_name('analysis.accordion_class')
    accordion_length = manager.get_elem_by_name('analysis.accordion_length')
    accordion_cluster = manager.get_elem_by_name('analysis.accordion_cluster')

    ## 缺失重复组件
    analysis_label_new = manager.get_elem_by_name('analysis.analysis_label_new')
    missing_dum_df = manager.get_elem_by_name('analysis.missing_dum_df')
    missing_dum_rate = manager.get_elem_by_name('analysis.missing_dum_rate')
    analysis_null_dup = manager.get_elem_by_name('analysis.analysis_null_dup')
    rate_show_btn = manager.get_elem_by_name('analysis.rate_show_btn')
    rate_retract_btn = manager.get_elem_by_name('analysis.rate_retract_btn')
    show_null_dup = manager.get_elem_by_name('analysis.show_null_dup')
    analysis_dup_method = manager.get_elem_by_name('analysis.analysis_dup_method')
    analysis_dup_threshold = manager.get_elem_by_name('analysis.analysis_dup_threshold')
    ngram_dup = manager.get_elem_by_name('analysis.ngram_dup')

    # 健康分析组件
    analysis_check_btn = manager.get_elem_by_name('analysis.analysis_check_btn')
    analysis_score = manager.get_elem_by_name('analysis.analysis_score')
    analysis_score_detail = manager.get_elem_by_name('analysis.analysis_score_detail')
    analysis_desc_detail = manager.get_elem_by_name('analysis.analysis_desc_detail')

    # 搜索组件
    search_analysis_column = manager.get_elem_by_name('analysis.search_analysis_column')
    search_analysis_method = manager.get_elem_by_name('analysis.search_analysis_method')
    search_analysis_btn = manager.get_elem_by_name('analysis.search_analysis_btn')
    search_analysis_retract = manager.get_elem_by_name('analysis.search_analysis_retract')
    search_analysis_keyword = manager.get_elem_by_name('analysis.search_analysis_keyword')
    search_analysis_regex = manager.get_elem_by_name('analysis.search_analysis_regex')
    search_analysis_metainfo = manager.get_elem_by_name('analysis.search_analysis_metainfo')
    search_analysis_resultinfo = manager.get_elem_by_name('analysis.search_analysis_resultinfo')
    analysis_search_result = manager.get_elem_by_name('analysis.analysis_search_result')

    search_cluster_method = manager.get_elem_by_name('analysis.cluster_search_config.search_cluster_method')
    search_n_clusters = manager.get_elem_by_name('analysis.cluster_search_config.search_n_clusters')
    search_cluster_config = manager.get_elem_by_name('analysis.search_cluster_config')
    search_similar_config = manager.get_elem_by_name('analysis.search_similar_config')
    search_similar_query = manager.get_elem_by_name('analysis.similar_search_config.search_similar_query')
    search_similar_method = manager.get_elem_by_name('analysis.similar_search_config.search_similar_method')
    search_similar_ngram = manager.get_elem_by_name('analysis.similar_search_config.search_similar_ngram')

    # 2024.4.23 增加数据源切换
    analysis_source.select(get_droplist_check, inputs=[user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], outputs=[analysis_collection_name])

    # 2024.4.24 数据统计信息分析
    analysis_check_btn.click(analysis_dataset, inputs=[user_name, analysis_source, analysis_collection_name], outputs=[analysis_score, analysis_score_detail, analysis_desc_detail, analysis_process_bar_plt, analysis_process_bar_text], concurrency_limit=100).then(get_logs, [user_name], [sys_info])

    # 查看数据集信息
    ## 显示元信息
    analysis_meta_button.click(show_meta, inputs=[user_name, analysis_source, analysis_collection_name], outputs=[analysis_collection_meta, analysis_show_data])

    ## 显示数据集及分页
    analysis_data_button.click(show_dataset, inputs=[user_name, analysis_source, analysis_collection_name], outputs=[analysis_collection_data, analysis_show_data]).then(show_pages, inputs=[user_name, analysis_source, analysis_collection_name], outputs=[analysis_collection_pages])
    analysis_collection_pages.change(get_page_content_tab, inputs=[user_name, analysis_source, analysis_collection_name, analysis_collection_pages], outputs=[analysis_collection_data])
    analysis_data_close_button.click(close_show, inputs=[gr.State(4)], outputs=[analysis_collection_meta, analysis_collection_data, analysis_collection_pages, analysis_show_data])

    ## 更新columns
    analysis_collection_name.select(get_column_name, inputs=[user_name, analysis_source, analysis_collection_name], outputs=[analysis_label, analysis_len_label, analysis_label_new, cluster_label, search_analysis_column])

    # 数据细节信息分析
    ## 细节信息分析--频率分布
    analysis_label_type.select(show_extra, inputs=[user_name, analysis_source, analysis_collection_name, gr.State('class'), analysis_label_type], outputs=[ngram_rate, ngram_n])
    plot_generate_btn.click(plot_data, inputs=set(manager.get_list_elems(typ='user')+[gr.State('class_config')]), outputs=[analysis_plt, analysis_label_text, analysis_label_df, accordion_class, search_class, search_class_data, search_class_data_json, search_class_data_origin], concurrency_limit=100).then(get_logs, [user_name], [sys_info])
    ## 细节信息分析--长度分布
    plot_generate_len_btn.click(plot_data, inputs=set(manager.get_list_elems(typ='user')+[gr.State('length_config')]), outputs=[analysis_len_plt, analysis_label_len_text, analysis_label_len_df, accordion_length, search_length, search_length_data, search_length_data_json, search_length_data_origin], concurrency_limit=100).then(get_logs, [user_name], [sys_info])
    ## 细节信息分析--聚类分布
    cluster_method.select(show_extra, inputs=[user_name, analysis_source, analysis_collection_name, gr.State('cluster'), cluster_method], outputs=[n_clusters, distance_threshold, eps, min_samples]).then(get_logs, [user_name], [sys_info])
    plot_cluster_btn.click(plot_data, inputs=set(manager.get_list_elems(typ='user')+[gr.State('cluster_config')]), outputs=[analysis_cluster_plt, analysis_cluster_text, analysis_cluster_df, accordion_cluster, search_cluster, search_cluster_data, search_cluster_data_json, search_cluster_data_origin], concurrency_limit=100).then(get_logs, [user_name], [sys_info])

    ## 细节信息分析--缺失值/重复值查看
    rate_show_btn.click(check_duplicate_null, inputs=[user_name, analysis_source, analysis_collection_name, analysis_label_new, analysis_null_dup, analysis_dup_method, analysis_dup_threshold, ngram_dup], outputs=[missing_dum_df, missing_dum_rate, missing_dum_df, missing_dum_rate, show_null_dup], concurrency_limit=100).then(get_logs, [user_name], [sys_info])
    analysis_null_dup.select(show_extra, inputs=[user_name, analysis_source, analysis_collection_name, gr.State('duplicate'), analysis_null_dup], outputs=[analysis_dup_method, analysis_dup_threshold, ngram_dup])
    analysis_dup_method.select(show_extra, inputs=[user_name, analysis_source, analysis_collection_name, gr.State('duplicate_method'), analysis_dup_method], outputs=[analysis_dup_threshold])

    ## 数据查看
    btn_search_class.click(search_result_data, inputs=[search_class_data_json, search_class_data_origin, search_class], outputs=[search_class_data])
    btn_search_length.click(search_result_data, inputs=[search_length_data_json, search_length_data_origin, search_length], outputs=[search_length_data])
    btn_search_cluster.click(search_result_data, inputs=[search_cluster_data_json, search_cluster_data_origin, search_cluster], outputs=[search_cluster_data])

    ## 收起结果
    btn_search_class_retract.click(close_show, inputs=[gr.State(1)], outputs=[search_class_data])
    btn_search_length_retract.click(close_show, inputs=[gr.State(1)], outputs=[search_length_data])
    btn_search_cluster_retract.click(close_show, inputs=[gr.State(1)], outputs=[search_cluster_data])

    plot_retract_btn.click(close_show, inputs=[gr.State(4)], outputs=[analysis_plt, analysis_label_text, analysis_label_df, accordion_class], queue=False)  # 隐藏
    plot_retract_len_btn.click(close_show, inputs=[gr.State(4)], outputs=[analysis_len_plt, analysis_label_len_text, analysis_label_len_df, accordion_length], queue=False)  # 隐藏
    plot_retract_cluster_btn.click(close_show, inputs=[gr.State(4)], outputs=[analysis_cluster_plt, analysis_cluster_text, analysis_cluster_df, accordion_cluster], queue=False)
    rate_retract_btn.click(close_show, inputs=[gr.State(1)], outputs=[show_null_dup])

    # 数据搜索
    analysis_collection_name.select(change_status, inputs=[analysis_collection_name], outputs=[analysis_meta_button, analysis_data_button, analysis_data_close_button], queue=False)
    search_analysis_method.select(show_search_conf, inputs=[search_analysis_method], outputs=[search_analysis_keyword, search_analysis_regex, search_cluster_config, search_similar_config]).then(get_logs, [user_name], [sys_info]) # 选择方法
    search_similar_method.select(show_extra, inputs=[user_name, analysis_source, analysis_collection_name, gr.State('duplicate_method_search'), search_similar_method], outputs=[search_similar_ngram])

    search_analysis_btn.click(search_data, inputs=set(manager.get_list_elems(typ='user')+[gr.State('cluster_search_config')]), outputs=[search_analysis_metainfo, search_analysis_resultinfo, analysis_search_result], concurrency_limit=100).then(get_logs, [user_name], [sys_info])
    search_analysis_retract.click(close_show, inputs=[gr.State(1)], outputs=[analysis_search_result])  # 收起结果

# 用户登录状态初始化
def analysis_login_components():
    analysis_collection_name = manager.get_elem_by_name('analysis.analysis_collection_name')
    return [analysis_collection_name]

def analysis_login_status(user_name):
    dataset_name = manager.get_elem_by_name('analysis.analysis_label')
    return gr.update(value=None)

# # 登出时状态复原
def analysis_logout_components():
    analysis_source = manager.get_elem_by_name('analysis.analysis_source')
    analysis_collection_name = manager.get_elem_by_name('analysis.analysis_collection_name')
    analysis_collection_pages = manager.get_elem_by_name('analysis.analysis_collection_pages')
    return [analysis_source, analysis_collection_name, analysis_collection_pages]

def analysis_logout_status():
    return [gr.update(value=None)]*2 + [gr.update(visible=False)]