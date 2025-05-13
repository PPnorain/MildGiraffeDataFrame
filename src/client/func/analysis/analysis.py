import os, json, requests, tempfile, threading, time
import pandas as pd
import gradio as gr
from apiweb import api_get_meta_std, api_read, api_logs_write, api_logs_read, api_get_data_distribution, \
    api_get_condition_df, api_read_page
from conf.userconf import URL
from common import get_logs, response_checker
from .utils import check_input, get_dataset_picture, get_response_content, create_chart, get_distribution_figure, get_cluster_config, get_distribution_data

import numpy as np
import matplotlib.pyplot as plt
from sseclient import SSEClient
from manager import manager

plt.rcParams['font.sans-serif'] = ["SimHei"]  # 用来正常显示中文标签，微软雅黑
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def plot_data(component_data):
    '''
    功能简介：计算数据的数据分布，长度分布并显示。
    '''

    user_name = component_data[manager.get_elem_by_name('top.user_name')]
    typ, file_name, chart_type, label, disrti_typ, config_dict = parse_distri_components(component_data)
    api_logs_write(user_name, f"[ Analysis ] 开始{disrti_typ}数据分布分析")
    gr.Info(f'[ Analysis ] 开始{disrti_typ}数据分布分析')
    # 1. 参数检查
    if not file_name:
        gr.Warning('请先选择【数据集】！')
        return [gr.update(value=None, visible=False)] * 8
    if not chart_type:
        gr.Warning('请选择【图表类型】！')
        return [gr.update(value=None, visible=False)] * 8
    if not label:
        gr.Warning('请选择【数据列】！')
        return [gr.update(value=None, visible=False)] * 8

    # 2. 请求处理
    response = api_get_data_distribution(user_name, typ, file_name, disrti_typ, label, config_dict)
    if not response_checker(response): return [gr.update()] * 8

    text_info = response['data']['stati_info']['text_info']
    data_info = pd.DataFrame(response['data']['stati_info']['data_info'])
    data_count = pd.DataFrame(response['data']['data_count'])
    class_data_result = response['data']['data_content']
    class_index, data_content = get_distribution_data(class_data_result, disrti_typ)

    # 3. 画图准备
    title = 'Frequency of Classes in the Dataset'
    xlabel, ylabel = 'Class Labels', 'Frequency'

    # 获取数据分布
    if disrti_typ == "freq":
        x, y = data_count['文本'], data_count['数量']
        plt_figure = create_chart(x, y, chart_type, title, xlabel, ylabel)
    # 获取长度分布
    elif disrti_typ == "length":
        x, y = data_count["长度"], data_count["数量"]
        plt_figure = create_chart(x, y, chart_type, title, xlabel, ylabel)
    # 获取聚类分布
    elif disrti_typ == "text_cluster" or disrti_typ == 'semantic_cluster':
        if chart_type == "聚类散点图":
            cluster_info = response['data']['cluster_info']
            plt_figure = get_distribution_figure(cluster_info)
        else:
            x, y = data_count['类别'], data_count['数量']
            plt_figure = create_chart(x, y, chart_type, title, xlabel, ylabel)

    api_logs_write(user_name, f"[ Analysis ] 完成{disrti_typ}数据分布分析")
    gr.Info(f'[ Analysis ] 完成{disrti_typ}数据分布分析')
    return gr.update(value=plt_figure, visible=True), gr.update(value=text_info, visible=True), gr.update(value=data_info, visible=True), gr.update(visible=True), gr.update(choices=class_index, visible=True), gr.update(value=data_content, visible=True), gr.update( value=class_data_result, visible=False), gr.update(value=data_content, visible=False)

def search_result_data(origin_data_json, origin_data, search_class):
    if not search_class:
        gr.Warning("请选择数据类别")
        return gr.update()
    if search_class == 'all_class':
        return gr.update(value=origin_data, visible=True)
    selected_data = origin_data_json[search_class]
    selected_data_df = pd.DataFrame(selected_data)
    return gr.update(value=selected_data_df, visible=True)


def check_duplicate_null(user_name, typ, name, column_name, method='duplicate', dup_method=None, dup_threshold=None, ngram_dup=None):
    """
    功能简介：检查是否有空。
    参数：
        check_typ: 用于标记是调用处理重复还是处理空行。
    """
    # 1. 参数检查
    api_logs_write(user_name, f"[ Analysis ] 开始数据重复值/缺失值分析")
    gr.Info(f"[ Analysis ] 开始数据重复值/缺失值分析")

    method = 'duplicate' if method == '重复值' else 'null'
    if not name:
        gr.Warning('请先选择【数据集】！')
        return gr.update(visible=False), gr.update(value=""), gr.update(visible=False), gr.update(value=""), gr.update(visible=True)
    if not column_name:
        gr.Warning('请选择【数据列】！')
        return gr.update(visible=False), gr.update(value=""), gr.update(visible=False), gr.update(value=""), gr.update(visible=True)
    if column_name == '整行':
        check_typ = 'duplicate_rows' if method == 'duplicate' else 'null_rows'
    else:
        check_typ = "duplicated_columns" if method == 'duplicate' else "null_columns"

    response = api_get_condition_df(user_name, typ, name, check_typ, column_name, dup_method,dup_threshold, ngram_dup)
    if not response_checker(response): return [gr.update()] * 5

    data, ratio = pd.DataFrame(response['data']['condition_data']), response['data']['condition_rate']
    api_logs_write(user_name, f"[ Analysis ] 完成数据重复值/缺失值分析")
    gr.Info(f"[ Analysis ] 完成数据重复值/缺失值分析")

    return gr.update(value=data, visible=True), gr.update(value=ratio, visible=True), gr.update(value=data, visible=True), gr.update(value=ratio, visible=True), gr.update(visible=True)

def get_column_name(user_name, typ, file_name):
    res = api_get_meta_std(user_name, typ, file_name)
    if res['code'] == 200:
        if 'columns' not in res['data']:
            return [gr.update(choices=["text"], value="text")] * 5
        elif res['data']['columns'] == []:
            return [gr.update(choices=["text"], value="text")] * 5
        else:
            columns = res['data']['columns']
            columns_new = ["整行"] + columns
            if len(columns) >= 1:
                return gr.update(choices=columns, value=columns[0]), gr.update(choices=columns, value=columns[0]), gr.update(choices=columns_new, value=columns_new[1]), gr.update(choices=columns, value=columns[0]), gr.update(choices=columns, value=columns[0])
            else:
                return gr.update(choices=columns, value=columns[0]), gr.update(choices=columns, value=columns[0]), gr.update(choices=columns_new, value=columns_new[1]), gr.update(choices=columns, value=columns[0]), gr.update(choices=columns, value=columns[0])
    return [gr.update(choices=[], value=None)] * 5

def show_meta(user_name, typ, dataset_name):
    if not check_input(typ, dataset_name):
        return gr.update(), gr.update()
    res = api_get_meta_std(user_name, typ, dataset_name)
    if res['code'] == 200:
        return gr.update(value=res['data'], visible=True), gr.update(visible=True, open=True)
    return [gr.update()] * 2

def show_dataset(user_name, typ, dataset_name):
    if not check_input(typ, dataset_name): return [gr.update()] * 2
    if typ == 'generation':
        response = api_read(user_name, typ, dataset_name, 'type', 'generated_data')
    else:
        response = api_read(user_name, typ, dataset_name)
    if not response_checker(response): return [gr.update()] * 2

    df = get_response_content(response, typ)
    if df is not None:
        return gr.update(value=df, visible=True), gr.update(visible=True, open=True)
    gr.Warning("数据集为空")
    return [gr.update()] * 2


def get_page_content_tab(user_name, tab, filename, page, filedname=None, filedvalue=None):
    if tab == 'dataset_info':
        res = api_read_page(user_name, tab, filename, page, filedname, filedvalue)
    else:
        res = api_read_page(user_name, tab, filename, page, 'type', 'generated_data')
    if res['code'] == 200:
        # 对于生成数据和上传数据格式有所不同
        if len(res['data']) > 0 and isinstance(res['data'][0], dict):
            df = pd.DataFrame(res['data']).reset_index()
        else:
            df = pd.DataFrame(res['data'], columns=['text']).reset_index()

        return gr.update(value=df)
    gr.Warning(f'[ Code ] {res["code"]}:{res["message"]}')
    return gr.update()


def check_len(user_name, typ, dataset_name):
    if not check_input(typ, dataset_name):
        return None, None

    # TODO 修改为后端实现，返回length_rate, length_num
    response = api_read(user_name, typ, dataset_name)
    df = get_response_content(response, typ)

    if df is not None:
        # 对df的每一行中每一个单元格进行长度遍历，如果含有字符长度小于5或大于1024的单元格，则标记该行
        # df['short_cell'] = df.apply(lambda row: any(len(str(x)) < 5 or len(str(x)) > 1024 for x in row), axis=1)
        df['short_cell'] = df.apply(lambda row: any(len(str(x)) > 1024 for x in row), axis=1)
        short_rows = df[df['short_cell']]
        length_num = len(short_rows)
        total_count = len(df)
        length_rate = length_num / total_count if total_count > 0 else 0

        return length_rate, length_num
    return None, None


def check_column(user_name, typ, dataset_name):
    if not check_input(typ, dataset_name):
        return None, None, None

    # TODO 修改为后端实现，返回empty_count, empty_ratio, columns_empty
    response = api_read(user_name, typ, dataset_name)
    df = get_response_content(response, typ)
    if df is not None:
        empty_values = ["", None, "None", np.nan]
        columns_empty = df.apply(lambda x: all(x.isin(empty_values)), axis=0)

        empty_count = columns_empty.sum()
        total_columns = len(df.columns)
        empty_ratio = empty_count / total_columns

        return empty_count, empty_ratio, columns_empty
    return None, None, None


def get_process_bar(processed_value, unprocessed_value):
    # 定义饼图的总和
    total_value = processed_value + unprocessed_value

    # 计算每个部分的百分比
    processed_percentage = (processed_value / total_value) * 100
    unprocessed_percentage = (unprocessed_value / total_value) * 100

    # 绘制饼图
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.pie([unprocessed_percentage, processed_percentage],
           autopct=None,
           startangle=90,
           wedgeprops=dict(width=0.1, edgecolor='w', linewidth=0),
           counterclock=True,
           colors=['#A9A9A9', '#00FF00'])

    # 绘制一个白色的圆作为背景，以增强百分比标签的可读性
    circle = plt.Circle((0, 0), radius=0.8, color='white', fc='none', linewidth=0)
    ax.add_patch(circle)

    # 在饼图中心添加百分比标签
    ax.text(0, 0, f'{processed_percentage:.1f}%',
            ha='center', va='center', color='black', fontsize=12, fontweight='bold')

    # 使x轴和y轴的刻度相同，使得饼图显示为圆形
    ax.axis('equal')
    plt.tight_layout(pad=0)
    return plt


def analysis_dataset(user_name, typ, name):
    """
    功能简介：一键数据质量检测逻辑代码。
    """
    api_logs_write(user_name, f"[ Analysis ] 开始一键健康分析")
    gr.Info(f"[ Analysis ] 开始一键健康分析")

    info_map = {
        "row_duplicate_rate": {"process_info": "\n正在进行重复率得分计算，请稍后...", "score_weight": 0.2,"zh": "重复率得分", "problem_text": "- 重复的数据有{nums}条。"},
        "row_null_rate": {"process_info": "\n正在进行缺失率得分计算，请稍后...", "score_weight": 0.2, "zh": "缺失率得分", "problem_text": "- 存在某字段的值在[None, 'None', '', Nan]中的数据有{nums}条。"},
        "row_length_rate": {"process_info": "\n正在进行长度率正确得分计算，请稍后...", "score_weight": 0.2, "zh": "长度正确率得分", "problem_text": "- 存在某字段的长度在小于5或大于1024的数据有{nums}条。"},
        "row_special_char_rate": {"process_info": "\n正在进行特殊字符率得分计算，请稍后...", "score_weight": 0.2, "zh": "行特殊字符分数", "problem_text": "- 存在某字段前尾含有特殊字符[' ', '\\']的数据有{nums}条。"},
        "columns_null_rate": {"process_info": "\n正在进行字段冗余率得分计算，请稍后...", "score_weight": 0.1, "zh": "列冗余率得分", "problem_text": "- 内容全部为空的字段有{nums}个"},
        "row_ngrams_rate": {"process_info": "\n正在进行N-gram得分计算，请稍后...", "score_weight": 0.1, "zh": "N-gram重复得分", "problem_text": "- 存在5-grams存在在10%以上的数据有{nums}条。"},
    }
    # 检查输入
    if not check_input(typ, name): return [gr.update()] * 6
    # import ipdb; ipdb.set_trace()
    # 获取分数
    url = URL + f"standard-api/data_health_checker/?user_name={user_name}&typ={typ}&name={name}"
    response = requests.get(url, headers={'Accept': 'text/event-stream'}, stream=True)
    res = SSEClient(response)

    result_score_map, process_info = dict(), "开始统计数据健康得分..."
    yield gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(value=get_process_bar(0, len(info_map)), visible=True), gr.update(value=process_info, visible=True)

    for index, event in enumerate(res.events(), start=1):
        data = json.loads(event.data)['data']
        result_score_map.update(data)
        process_info += info_map[next(iter(data))]["process_info"]
        yield gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(value=get_process_bar(index, len(info_map) - index), visible=True), gr.update(value=process_info, visible=True)

    # 判断错误
    if any(val is None for val in list(result_score_map.values())):
        process_info = process_info + "\n" + "存在计算错误，请检查日志和数据..."
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update(value=process_info, visible=True)

    # 获取数据集画像
    process_info = process_info + "\n" + "正在进行综合得分计算，请稍后..."
    yield gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update(value=process_info, visible=True)

    plt_dataset_picture, analysis_score_detail, problems = get_dataset_picture(result_score_map, info_map)
    api_logs_write(user_name, f"[ Analysis ] 完成一键健康分析")
    gr.Info("[ Analysis ] 完成一键健康分析")

    yield gr.update(value=plt_dataset_picture, visible=True), gr.update(value=analysis_score_detail, visible=True), gr.update(value=problems, visible=True), gr.update(visible=False), gr.update(value="", visible=False)

def show_extra(user_name, typ, file_name, show_type, op):
    if show_type == 'class':
        if op == 'ngram':
            return gr.update(visible=True), gr.update(visible=True)
        if op == '单标签' or op == '多标签':
            return gr.update(visible=False), gr.update(visible=False)
    if show_type == 'cluster':
        if op == 'Kmeans':
            max_len = api_get_meta_std(user_name, typ, file_name)['data']['total_nums']
            return gr.update(visible=True, maximum=max_len), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        if op == 'Hierarchical':
            max_len = api_get_meta_std(user_name, typ, file_name)['data']['total_nums']
            return gr.update(visible=True, maximum=max_len), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
        if op == 'DBSCAN':
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
    if show_type == 'duplicate':
        if op == '重复值':
            return gr.update(value="Exact_Match", visible=True), gr.update(visible=False), gr.update(visible=False)
        if op == '缺失值':
            return [gr.update(visible=False)] * 3
    if show_type == 'duplicate_method':
        if op == 'Exact_Match':
            return gr.update(visible=False)
        else:
            return gr.update(visible=True)
    if show_type == 'duplicate_method_search':
        if op == 'ngram_similarity':
            return gr.update(visible=True)
        else:
            return gr.update(visible=False)
    return [gr.update(visible=False)] * 4

def parse_distri_components(component_data):
    analysis_config = manager.get_current_conf(component_data)
    typ = analysis_config['analysis_source']
    file_name = analysis_config['analysis_collection_name']
    config_dict = analysis_config
    if 'analysis_label' in analysis_config:
        disrti_typ = "freq"
        label = config_dict['analysis_label']
        chart_type = config_dict['analysis_class']
        config_dict["config_type"] = "class"
    elif 'analysis_len_label' in analysis_config:
        disrti_typ = "length"
        label = config_dict['analysis_len_label']
        chart_type = config_dict['analysis_len_class']
    elif 'cluster_type' in analysis_config:
        disrti_typ = config_dict['cluster_type'] + "_cluster"
        label = config_dict['cluster_label']
        chart_type = config_dict['cluster_figure_class']
        config_dict["config_type"] = "cluster"
    else:
        disrti_typ, label, chart_type = None, None, None
    return typ, file_name, chart_type, label, disrti_typ, config_dict