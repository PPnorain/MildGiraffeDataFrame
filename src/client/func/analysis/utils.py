import gradio as gr
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
import regex as re

# -------------- 参数检查 ------------------
def check_input(typ, dataset_name):
    """
    功能简介：检查是否选择数据源和数据集。
    """
    if not typ:
        gr.Warning('请先选择数据源！')
        return False
    elif not dataset_name:
        gr.Warning('请先选择数据集！')
        return False
    return True

def replace_latex_display_mode(text):
    # if isinstance
    # 替换连续的多个 $ 为一个 $
    text = str(text)
    return re.sub(r'\$', '\\$', text)

# -------------- 画图 ------------------
def create_chart(x, y, chart_type, title, xlabel, ylabel, data=None):
    """
    根据指定的图表类型创建图表。

    参数:
    - x: 横坐标的数据，可以是列表或pandas Index对象。
    - y: 纵坐标的数据，可以是列表或pandas Series对象。
    - chart_type: 字符串，指定要创建的图表类型，可以是 "柱状图"、"折线图" 或 "饼状图"。
    - title: 字符串，图表的标题。
    - xlabel: 字符串，图表的横坐标标签。
    - ylabel: 字符串，图表的纵坐标标签。
    """
    try:
        x = [replace_latex_display_mode(item) for item in x]
        plt.figure(figsize=(10, 5))
        if isinstance(y, list) is False:
            y = y.to_list()

        if chart_type == "柱状图":
            # 检查 x 和 y 是否为列表或元组
            if not isinstance(x, (list, tuple)) or not isinstance(y, (list, tuple)):
                raise ValueError("x 和 y 必须是列表或元组")
            
            # 检查 x 和 y 的长度是否相等
            if len(x) != len(y):
                raise ValueError("x 和 y 的长度必须相同")
            
            # 检查 title, xlabel, ylabel 是否为字符串
            if not isinstance(title, str) or not isinstance(xlabel, str) or not isinstance(ylabel, str):
                raise ValueError("title, xlabel, ylabel 必须是字符串")
            
            x_values = range(len(x))
            plt.barh(x_values, y, color='skyblue')
            plt.title(title)
            plt.xlabel(ylabel)
            plt.ylabel(xlabel)
            
            # 设置 y 轴的标签
            plt.yticks(x_values, x)
            
            # 显示数值标签，并检查每个 y 值是否可以转换为字符串
            for i, value in enumerate(y):
                try:
                    plt.text(value + 0.1, i, str(value), va='center', usetex=False)  # 调整数值标签的位置
                except (TypeError, ValueError) as e:
                    print(f"Error displaying value {value} at position {i}: {e}")
            
            plt.tight_layout()

        elif chart_type == "折线图":
            plt.plot(x, y, color='skyblue', marker='o')
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.grid(True)
            plt.tight_layout()

        elif chart_type == "饼状图":
            if len(x) != len(y):
                raise ValueError("饼状图的x和y数据长度必须相同")
            plt.figure(figsize=(10, 5))
            plt.pie(y, labels=x, autopct='%1.1f%%', startangle=140)
            # plt.title('Class Distribution as Percentage')
            plt.axis('equal')
            plt.margins(0)
            plt.tight_layout()

        elif chart_type == "雷达图":
            # plt.figure(figsize=(3, 3))
            if len(x) != len(y):
                raise ValueError("雷达图的x和y数据长度必须相同")
            categories = x
            num_vars = len(categories)
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            y.append(y[0])  # 将第一个分数添加到最后，形成封闭的形状
            angles.append(angles[0])  # 添加重复的角度值，形成封闭的形状
            fig, ax = plt.subplots(figsize=(4, 3), subplot_kw=dict(polar=True))

            ax.fill(angles, y, color='skyblue', alpha=0.25)  # 使用fill绘制雷达图的填充部分
            # ax.plot(angles, y, color='skyblue', linewidth=2) # 使用plot绘制雷达图的边框线条

            # 设置雷达图的标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 100)

            ax.spines['polar'].set_visible(False)
            # ax.grid(False)
            # ax.set_theta_zero_location('N')
            # plt.margins(0)
            plt.title(title) if title != "" else None

        elif chart_type == "散点图":
            plt.scatter(x, y, color='skyblue')
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            return plt

        elif chart_type == "聚类散点图":
            # 画出聚类结果
            scatter = plt.scatter(x, y, c=data, cmap='viridis')
            plt.title(title)
            plt.xlabel('PCA 1')
            plt.ylabel('PCA 2')
            plt.colorbar(scatter)
            return plt

        elif chart_type == "直方图":
            plt.hist(y, color='skyblue', edgecolor='black')
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)

        elif chart_type == "箱型图":
            plt.boxplot(y, vert=False)
            plt.title(title)
            plt.xticks(x, rotation=90)

        elif chart_type == "热力图":
            if len(x) != len(y) or len(x) != len(y[0]):
                raise ValueError("热力图的x, y数据需要构成矩阵")
            ax = plt.axes()
            cax = ax.matshow(np.array(y), cmap='viridis')
            plt.colorbar(cax)
            plt.xticks(rotation=90)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.title(title)

        else:
            # raise ValueError("Unsupported chart type")
            gr.Info(f"不支持的图表类型：{chart_type}")
            return None
        # 显示图表
        # plt.tight_layout()  # 调整布局以适应标签和标题
        return plt
    except Exception as e:
        gr.Warning(f"图表创建失败：{e}")
        print(e)
        return None


# ----------------- 分数计算 --------------
def rate_to_score(rate):
    """
    将比率转换为得分。

    :param rate: 比率，范围为0.0到1.0。
    :return: 相应的得分，范围为0到100。
    """
    # 将比率转换为得分，假设满分是100分
    if isinstance(rate, str):
        match = re.search(r'占比：([0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)', rate)
        if match:
            rate = float(match.group(1))
    score = round((1 - rate) * 100, 5)
    return score


def get_dataset_picture(result_score_map, info_map):
    result_score = {info_map[k]["zh"]: {"score": rate_to_score(v['ratio']), "weight": info_map[k]["score_weight"], "nums": v["nums"], "problem_text": info_map[k]["problem_text"]} for k, v in result_score_map.items()}
    # 计算总分，加权平均
    total_score = sum([v["score"] * v["weight"] for k, v in result_score.items()])
    total_score = round(total_score, 2)

    # 1. 雷达图
    x = list(result_score.keys())
    y = [result_score[i]["score"] for i in x]
    title = f'综合得分：{total_score}'
    xlabel = ylabel = "得分"
    plt = create_chart(x, y, "雷达图", '', xlabel, ylabel)
    # 2. 详细分数列表
    analysis_score_detail = f"- 综合得分：{total_score}"
    for k, v in result_score.items():
        analysis_score_detail += f"\n- {k}:{v['score']}"

    # 3. 详细问题信息
    problems = []
    for k, v in result_score.items():
        if v['nums'] > 0:
            problems.append(v["problem_text"].format(nums=v['nums']))

    problems = "\n".join(problems) if problems != [] else "该数据没有问题"
    return plt, analysis_score_detail, problems


# ---------------- 数据预处理 ---------------
def get_response_content(response, typ):
    if response['code'] == 200:
        content = response['data']
        if content == []:
            return None
        df = pd.DataFrame(content)
        if isinstance(df.columns, pd.RangeIndex) and len(df.columns) == 1:
            df = pd.DataFrame(content, columns=['text']).reset_index()
        else:
            df = df.reset_index()
        return df
    gr.Warning(f"{response['code']}:{response['messages']}")
    return None


def get_distribution_figure(cluster_info):
    feature_matrix = np.array(cluster_info['feature_matrix'])
    labels = np.array(cluster_info['labels'])

    # 画出聚类结果
    plt.figure(figsize=(10, 5))

    if feature_matrix.shape[1] == 1:
        scatter = plt.scatter(feature_matrix[:, 0], feature_matrix[:, 0], c=labels, cmap='viridis')
    else:
        # # 使用PCA将高维嵌入向量降维到2D
        # pca = PCA(n_components=2)
        # feature_matrix = pca.fit_transform(feature_matrix)
        scatter = plt.scatter(feature_matrix[:, 0], feature_matrix[:, 1], c=labels, cmap='viridis')

    plt.title('Text Clustering Results')
    plt.xlabel('PCA 1')
    plt.ylabel('PCA 2')
    plt.colorbar(scatter)
    return plt


def get_cluster_config(cluster_typ, cluster_method, n_clusters=None, distance_threshold=None, eps=None,
                       min_samples=None):
    cluster_config_dict = {
        "config_type": "cluster",
        "cluster_typ": cluster_typ,
        "cluster_model": cluster_method,
        "n_clusters": n_clusters,
        "distance_threshold": distance_threshold,
        "eps": eps,
        "min_samples": min_samples
    }
    return cluster_config_dict


def get_distribution_data(class_data_result, disrti_typ):
    analysis_df = []
    class_index = []

    # 自定义排序键函数
    def sort_length(tag):
        # 将标签拆分为两个部分，并转换为整数
        if "-" not in tag:
            return (tag, tag)
        start, end = map(int, tag.split('-'))
        # 返回一个元组，用于排序
        return (start, end)

    # 然后，将字典列表添加为新的行
    for label, data_dicts in class_data_result.items():
        for data_dict in data_dicts:
            analysis_df.append(data_dict)
            class_index = class_index + [label]
    if disrti_typ == "length":
        class_index = ["all_class"] + sorted(list(set(class_index)), key=sort_length)
    else:
        class_index = ["all_class"] + list(set(class_index))
    # class_index = "all_class" + class_index
    data_content = analysis_df
    data_content = pd.DataFrame(data_content)
    return class_index, data_content