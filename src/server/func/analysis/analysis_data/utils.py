# from deprecated import deprecated
from dependencies import CustomEmbeddings
import pandas as pd
import numpy as np
from tqdm import tqdm
import jieba, re
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from multiprocessing import Pool, cpu_count
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

from common import UtilsDBOperator
from collections import defaultdict

embeddings = CustomEmbeddings("http://xx.xx.xx.xx:30316/embedding  ", 20)
from dependencies import deprecated_info
from .duplicated_analysis import get_duplicate_df

def contains_special_chars(cell):
    if not isinstance(cell, str):
        cell = str(cell)  # 将非字符串格式转为字符串
    return cell.startswith(' ') or cell.endswith(' ') or cell.startswith('\\') or cell.endswith('\\')

def get_condition_df(df, condition_type, column_name=None, dup_method=None, dup_threshold=None, ngram_dup=None):
    """
    功能简介：找出df中所有满足condition_type的数据以及占比。
    参数：
        df:待查找的数据。
        condition_type:可选的找出数据的条件。[duplicated_rows, duplicated_columns, null_rows, null_columns, length_rows, special_char_rows]
    返回值：
        符合条件的数据子表， 符合条件的数据占比
    """
    condition_map = {
        "duplicate_rows": lambda df, column_name: df.duplicated(keep=False), # 整行重复
        "duplicated_columns": lambda df, column_name: df[column_name].duplicated(keep=False), # 指定列中重复
        "null_rows": lambda df, column_name: df.apply(lambda row: row.isnull().any() or any(value in [None, '', 'None'] for value in row), axis=1), # 空行
        "null_columns": lambda df, column_name: df[column_name].isna() | df[column_name].apply(lambda x: x == 'None' or x is None or x == ''), # 指定列中查空
        "length_rows": lambda df, column_name: df.apply(lambda row: any(len(str(x)) > 1024 for x in row), axis=1), # 整行行长度查看
        "special_char_rows": lambda df, column_name: df.apply(lambda row: any(contains_special_chars(x) for x in row), axis=1), # 整行特殊符号查看
    }
    if condition_type == "duplicated_columns" and not column_name:
        return pd.DataFrame(), -1, 0

     # 重复分析
    print(f"开始执行{condition_type}分析")
    if dup_method == "MinHash" and "duplicate" in condition_type:
        return get_duplicate_df(df, column_name, dup_method, float(dup_threshold))
    elif dup_method == "Exact_Match" and "duplicate" in condition_type:
        condition_type = "duplicated_columns" if column_name != "整行" else "duplicate_rows"

    df = df.applymap(str)
    condition_df_bool = condition_map[condition_type](df, column_name)
    condition_count = int(condition_df_bool.sum())
    condition_rate = round(condition_count / len(df) if len(df) > 0 else 0, 5)
    condition_data = df[condition_df_bool].head(50)
    condition_result = f"数据量：{condition_count}; 占比：{condition_rate}"
    return condition_data, condition_result, condition_count

def check_column_redundancy(df):
    """
    功能简介：用于判断df中列是否存在全空列，返回数量，占比和空列名。
    """
    if df is not None:
        empty_values = ["", None, "None", np.nan]
        columns_empty = df.apply(lambda x: all(x.isin(empty_values)), axis=0)
        empty_column_names = df.columns[columns_empty].to_list()

        empty_count = int(columns_empty.sum())
        total_columns = len(df.columns)
        empty_ratio = empty_count / total_columns

        return empty_column_names, empty_ratio, empty_count
    return None, None, None

# ngrams重复分析
def find_common_phrases(texts, percentage, n):
    stop_words = []
    def generate_ngrams(text, n):
        words = list(jieba.cut(text))
        # cleaned = []
        # for word in words:
        #     if word not in stop_words:
        #         cleaned.append(word)
        # words = cleaned
        ngrams = zip(*[words[i:] for i in range(n)])
        return ["".join(ngram) for ngram in ngrams]

    phrase_counts = defaultdict(int)
    for text in texts:
        phrases = set(generate_ngrams(text, n))  # 生成n-gram
        for phrase in phrases:
            phrase_counts[phrase] += 1

    num_texts = len(texts)
    common_phrases = [phrase for phrase, count in phrase_counts.items() if count / num_texts > percentage]

    return common_phrases

def count_texts_with_common_phrases(df, texts_df, common_phrases):
    ngrams_count = 0
    ngrams_duplicate_data = []
    for i, text in tqdm(enumerate(texts_df)):
        for phrase in common_phrases:
            if phrase in text:
                ngrams_count += 1
                ngrams_duplicate_data.append(df.iloc[i])
                break  # No need to check further phrases once a match is found in a text
    return ngrams_count, ngrams_duplicate_data

def check_ngrams_row_duplicate(df):
    df = df.applymap(str)
    texts_df = df.apply('\t'.join, axis=1)
    common_phrases = find_common_phrases(texts_df, 0.1, 5)
    ngrams_count, ngrams_duplicate_data = count_texts_with_common_phrases(df, texts_df, common_phrases)
    ngrams_duplicate_rate = ngrams_count / len(df) if len(df) > 0 else 0
    return ngrams_duplicate_data, ngrams_duplicate_rate, ngrams_count

def check_full_row_duplicate(df):
    deprecated_info("check_full_row_duplicate", "check_duplicate_null", "5-23")
    full_row_duplicate = df.duplicated(keep=False)
    full_row_count = full_row_duplicate.sum()
    full_row_duplicate_rate = full_row_count / len(df) if len(df) > 0 else 0
    full_row_duplicate_data = df[full_row_duplicate]
    return full_row_duplicate_data, full_row_duplicate_rate

def check_column_duplicate(df, column_name):
    deprecated_info("check_column_duplicate", "check_duplicate_null", "5-23")
    column_duplicate = df.duplicated(subset=[column_name], keep=False)
    column_count = column_duplicate.sum()
    column_duplicate_rate = column_count / len(df) if len(df) > 0 else 0
    column_duplicate_data = df[column_duplicate]
    return column_duplicate_data, column_duplicate_rate

def check_full_row_null(df):
    deprecated_info("check_full_row_null", "check_duplicate_null", "5-23")
    full_row_null = df.apply(lambda row: row.isnull().any() or any(value in [None, '', 'None'] for value in row), axis=1)
    full_row_null_count = full_row_null.sum()
    full_row_null_rate = full_row_null_count / len(df) if len(df) > 0 else 0
    full_row_null_data = df[full_row_null]
    return full_row_null_data, full_row_null_rate

def check_column_null(df, column_name):
    deprecated_info("check_column_null", "check_duplicate_null", "5-23")
    # 检查列中是否包含空值、None或'None'
    # column_null = df[column_name].isnull()
    column_null = df[column_name].isna() | df[column_name].apply(lambda x: x == 'None' or x is None or x == '')
    # 计算空数据的比率
    column_null_count = column_null.sum()
    column_null_rate = column_null_count / len(df) if len(df) > 0 else 0
    # 选择出包含空值的行
    column_null_data = df[column_null]
    return column_null_data, column_null_rate

def remove_full_row_duplicate(df):
    df_no_duplicate = df.drop_duplicate()
    return df_no_duplicate

def remove_column_duplicate(df, column_name):
    df_no_duplicate = df.drop_duplicate(subset=[column_name])
    return df_no_duplicate

def is_list_string(s):
    try:
        obj = eval(s)
        return isinstance(obj, list)
    except Exception:
        return False

def split_labels(x):
    # 使用正则表达式匹配中文逗号、英文逗号和顿号作为分隔符来分割字符串
    # 并去除空格
    return [label.strip() for label in re.split(r'[，,、]\s*', x) if label.strip()]

def get_analysis_result_data(search_data_config, df):
    analysis_result_data = {}
    column = search_data_config['column']
    for label in search_data_config['class_count'].index:
        if search_data_config["type"] == "多标签" or search_data_config["type"] == "ngram":
            class_data = df[df[column].apply(lambda x: label in x)].head(50)
        else:
            class_data = df[df[column] == label].head(50)
        analysis_result_data[label] = class_data.to_dict(orient='records')
    return analysis_result_data

def count_fre_common_phrases(df, texts_df, common_phrases):
    df['ngrams_label'] = pd.Series([[] for _ in range(len(df))], index=df.index)
    for i, text in enumerate(texts_df):
        for phrase in common_phrases:
            if phrase in text:
                df.at[i, 'ngrams_label'].append(phrase)
    return df

# 频率分布分析
def analysis_frequency_distribution(df, column, config):
    '''
    功能简介：给定数据进行频率分布计算
    '''
    config = eval(config)
    if config["analysis_label_type"] == "多标签":
        df[column] = df[column].apply(lambda x: eval(x) if is_list_string(x) else x)
        # 将标签从字符串转换为列表
        df[column] = df[column].apply(lambda x: split_labels(x) if isinstance(x, str) else x)
        # 展开所有的标签并计数
        class_counts_all = df[column].explode().value_counts()
    elif config["analysis_label_type"] == "ngram":
        texts_df = df.applymap(str).apply('\t'.join, axis=1) if column == "整行" else df[column]
        common_phrases = find_common_phrases(texts_df, config['ngram_rate'], config['ngram_n'])
        # common_phrases = find_common_phrases(texts_df, 0.1, 1)
        if common_phrases == []:
            analysis_label_text, analysis_label_df = "无数据", pd.DataFrame()
            data_count = pd.DataFrame({'文本': [], '数量': []})
            return (analysis_label_text, analysis_label_df), data_count, pd.DataFrame()
        df = count_fre_common_phrases(df, texts_df, common_phrases)
        column = 'ngrams_label'
        class_counts_all = df[column].explode().value_counts()
    else:
        # 1. 特殊值处理
        df[column] = df[column].replace({None: ''}).astype(str)
        # 2. 标签统计
        class_counts_all = df[column].value_counts()

    # 3. 计算，获取前20类的分布情况
    class_counts = class_counts_all.nlargest(20)
    # 4. 对数据频率进行统计分析
    analysis_label_text, analysis_label_df = freq_len_statistics_info(class_counts_all)
    # # 5. 对前20类进行数据搜索，最多每类50条
    search_data_config = {'class_count': class_counts, 'column': column, 'type': config["analysis_label_type"]}
    analysis_class_data = get_analysis_result_data(search_data_config, df)

    data_count = pd.DataFrame({'文本': class_counts.index, '数量': class_counts.values})
    return (analysis_label_text, analysis_label_df), data_count, analysis_class_data
    
def freq_len_statistics_info(class_counts, cluster_info=""):
    '''
    功能简介：对频率分布进行统计分析
    '''
    # 最大类别和最小类别
    max_class, min_class = class_counts.idxmax(), class_counts.idxmin()
    max_count, min_count = class_counts.max(), class_counts.min()

    # 输出结果
    result = f"{cluster_info}" \
             f"最大类别：{max_class}; 数量：{max_count}\n" \
             f"最小类别：{min_class}; 数量：{min_count}" 
    
    # 创建DataFrame
    df_result = pd.DataFrame({
        '类别': class_counts.index,
        '数量': class_counts.values
    }).head(50)

    # 重置索引
    df_result.reset_index(drop=True, inplace=True)
    # # print(df_result)
    # for i, classes in enumerate(class_counts.index):
    #     if len(classes.strip()) > 4 and class_counts.values[i] >= 10 and len(classes) < 50:
    #         print(classes)
    # print(len(class_counts.index))

    return result, df_result

# 长度分布分析
def analysis_length_distribution(df, column):
    '''
    功能简介：对数据长度进行统计分析
    '''
    length_counts, df = get_column_length_distribution(df, column)
    analysis_label_text, analysis_label_df = freq_len_statistics_info(length_counts)
    search_data_config = {'class_count': length_counts, 'column': 'length_label', 'type': 'length'}
    analysis_result_data = get_analysis_result_data(search_data_config, df)
    data_count = pd.DataFrame({'长度': length_counts.index, '数量': length_counts.values})
    return (analysis_label_text, analysis_label_df), data_count, analysis_result_data

def get_column_length_distribution(df, column_name):
    # 找出该列的最长和最短字符长度
    max_length = df[column_name].astype(str).str.len().max()
    min_length = df[column_name].astype(str).str.len().min()

    # 如果最长和最短长度相同，说明所有数据长度一致，直接返回
    if max_length == min_length:
        df['length_label'] = str(max_length)
        label_counts = pd.DataFrame({
            'Length Range': [f'{min_length}'],
            'Count': [df[column_name].count()]
        }).set_index('Length Range')['Count']
        return label_counts, df
    
    # 将最短到最长分为 20 等分，四舍五入取整
    length_bins = np.unique(np.linspace(min_length, max_length, 21).astype(int))
    length_labels = [f'{l}-{u}' if u-l > 0 else f'{l}+' for l, u in zip(length_bins[:-1], length_bins[1:])]

    # 为每个字符长度分配到对应的标签区间
    df['length_label'] = pd.cut(df[column_name].astype(str).str.len(), bins=length_bins, labels=length_labels, include_lowest=True)

    # 展示在这二十个标签内的数据数量分布
    label_counts = df['length_label'].value_counts(normalize=False).reset_index()

    # 将标签名称设置为列名
    label_counts.columns = ['Length Range', 'Count']
    label_counts = label_counts.sort_values(by='Length Range')
    label_counts = label_counts.set_index('Length Range')['Count']

    return label_counts, df

# 文本聚类
def analysis_text_distribution(user_name, name, df, column, cluster_config):
    feature_matrix = get_text_feature(user_name, df, column)
    return get_cluster_distribution(user_name, name, df, feature_matrix, cluster_config)

def get_text_feature(user_name, df, column):
    texts = [' '.join(jieba.cut(str(text))) for text in tqdm(df[column])]
    vectorizer = CountVectorizer(ngram_range=(1, 1), token_pattern=r"(?u)\b\w+\b")
    feature_matrix = vectorizer.fit_transform(texts).toarray()
    return feature_matrix

def get_semantic_feature(user_name, df, column):
    texts = [str(text) for text in df[column]]
    try:
        with Pool(cpu_count() // 2) as p:
            query_embeddings = p.map(embeddings.embed_query, tqdm(texts))
        feature_matrix = np.array(query_embeddings)
    except Exception as e:
        print(f"Error occurred: {e}")
        UtilsDBOperator.db_logs_write_util(user_name, f'[ Error ] {e}')
    return feature_matrix

def analysis_semantic_distribution(user_name, name, df, column, cluster_config):
    # query_embeddings = [embeddings.embed_query(query) for query in tqdm(df[column])]
    feature_matrix = get_semantic_feature(user_name, df, column)
    return get_cluster_distribution(user_name, name, df, feature_matrix, cluster_config)

def get_cluster_distribution(user_name, name, df, feature_matrix, cluster_config):
    labels, cluster_result = get_cluster_labels(user_name, feature_matrix, cluster_config, df)
    cluster_result_info = cluster_result.replace("\n", "；")
    UtilsDBOperator.db_logs_write_util(user_name, f'[{name}] {cluster_result_info}')

    df['cluster_labels'] = labels
    class_counts = df['cluster_labels'].value_counts().nlargest(20)
    search_data_config = {'class_count': class_counts, 'column': 'cluster_labels', 'type': 'cluster'}
    analysis_result_data = get_analysis_result_data(search_data_config, df)
    data_count = pd.DataFrame({'类别': class_counts.index, '数量': class_counts.values})
    analysis_label_text, analysis_label_df = freq_len_statistics_info(class_counts, cluster_result)

    if feature_matrix.shape[1] == 1:
        scatter_matrix = feature_matrix
    else:
        pca = PCA(n_components=2)
        scatter_matrix = pca.fit_transform(feature_matrix)
    cluster_info = {'feature_matrix': scatter_matrix.tolist(), 'labels': labels.tolist()}
    return (analysis_label_text, analysis_label_df), data_count, cluster_info, analysis_result_data

def get_cluster_labels(user_name, feature_matrix, cluster_config, df=None):
    # 获取聚类参数
    cluster_config = eval(cluster_config) if isinstance(cluster_config, str) else cluster_config
    model = cluster_config["cluster_method"]
    cluster_result = ""
    try:
        if "search" in cluster_config:
            if cluster_config["n_clusters"] > len(feature_matrix):
                UtilsDBOperator.db_logs_write_util(user_name, f'[ Error ] 聚类数量不能大于样本数: {len(feature_matrix)}')
                return [], pd.DataFrame([])

        if model == "Kmeans":
            n_clusters = cluster_config["n_clusters"]
            if n_clusters == 0: # 未输入参数，自动选择n_clusters
                n_clusters, cluster_result = find_best_kmeans(model, feature_matrix)
            clustering_model = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)

        elif model == "Hierarchical":
            n_clusters, distance_threshold = cluster_config["n_clusters"], cluster_config["distance_threshold"]
            if distance_threshold != 0:
                n_clusters = None
            else:
                distance_threshold = None
                if n_clusters == 0:
                    n_clusters, cluster_result = find_best_kmeans(model, feature_matrix)
                else:
                    n_clusters, cluster_result = n_clusters, cluster_result
                # n_clusters, cluster_result = find_best_kmeans(model, feature_matrix) if n_clusters == 0 else n_clusters, cluster_result # 未输入参数，自动选择n_clusters
            clustering_model = AgglomerativeClustering(n_clusters=n_clusters, distance_threshold=distance_threshold)

        elif model == "DBSCAN":
            eps, min_samples = cluster_config["eps"], cluster_config["min_samples"]
            if 0 in [eps, min_samples]:
                best_params, cluster_result = find_best_dbscan(feature_matrix) # 未输入参数，自动选择eps, min_samples
                eps, min_samples = best_params[0], best_params[1]
            clustering_model = DBSCAN(eps=eps, min_samples=min_samples)

        labels = clustering_model.fit_predict(feature_matrix)

        # # 创建一个字典来存储每个聚类的样本索引
        # cluster_samples = {}
        # for label in np.unique(labels):
        #     cluster_samples[label] = np.where(labels == label)[0].tolist()  # 存储每个聚类的样本索引

        # if "search" in cluster_config:
        #     random_samples = []
        #     for cluster_index in cluster_samples:
        #         sample_index = np.random.choice(cluster_samples[cluster_index])  # 随机选择一个样本索引
        #         random_samples.append(df.iloc[sample_index])  # 抽取对应的样本
        #     return labels, random_samples

        if "search" in cluster_config:
            cluster_centers = clustering_model.cluster_centers_
            cluster_labels = labels
            return extract_cluster_data(cluster_labels, cluster_centers, df, feature_matrix)
        cluster_result = f"聚类方法: {model}, 聚类数量: n={len(set(labels))}\n{cluster_result}"
        return labels, cluster_result

    except Exception as e:
        UtilsDBOperator.db_logs_write_util(user_name, f'[ Error ] 聚类方法: {model}，出现错误：{e}')
        return [], cluster_result

def extract_cluster_data(cluster_labels, cluster_centers, df, weights):
    # 找到每个聚类中心点最近的样本
    random_samples_df = pd.DataFrame(columns=df.columns)
    for cluster_center in cluster_centers:
        # 计算每个样本与当前聚类中心点的距离；欧几里得距离；axis=1参数表示沿着每个样本点的维度计算范数
        distances = np.linalg.norm(weights - cluster_center, axis=1)
        # 找到最近的样本索引；返回给定数组中最小值的索引
        nearest_idx = np.argmin(distances)
        # 将最近的样本添加到结果DataFrame中
        random_samples_df = pd.concat([random_samples_df, df.iloc[nearest_idx:nearest_idx + 1]], ignore_index=True)
    # score = silhouette_score(weights, cluster_labels)
    return cluster_labels, random_samples_df


def find_best_kmeans(model, feature_matrix):
    n_clusters_range = range(1, 20) # 定义聚类数量范围
    best_score = -1
    best_n_clusters = 1
    max_len = len(feature_matrix)

    for k in n_clusters_range:
        if k > max_len:
            break
        if model == "Kmeans":
            clustering_model = KMeans(n_clusters=k, random_state=0, n_init=10)
        elif model == "Hierarchical":
            clustering_model = AgglomerativeClustering(n_clusters=k) # 凝聚的聚类算法
        clustering_model.fit(feature_matrix)
        if len(set(clustering_model.labels_)) > 1:
            score = silhouette_score(feature_matrix, clustering_model.labels_)
            if score > best_score:
                best_score = score
                best_n_clusters = k

    if best_score != -1:
        cluster_result = f"最佳聚类数: {best_n_clusters}, 最佳轮廓系数: {round(best_score, 2)}"
    else:
        cluster_result = "没有找到合适的聚类参数组合，默认聚为1类"
        best_n_clusters = 1
    return best_n_clusters, cluster_result


def find_best_dbscan(feature_matrix):
    # 确定eps和min_samples的范围
    eps_values = np.arange(0.1, 1.0, 0.1)
    min_samples_values = [1, 2, 5]  # 可以尝试不同的min_samples值
    best_score = -1
    best_params = None
    max_len = len(feature_matrix)
    label_count = len(feature_matrix)

    # 遍历所有参数组合
    for eps in eps_values:
        for min_samples in min_samples_values:
            if min_samples > max_len:
                break
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            dbscan.fit(feature_matrix)
            labels = dbscan.labels_
            if 1 < len(set(labels)) < len(feature_matrix):  # 确保至少有两个不同的标签
                score = silhouette_score(feature_matrix, labels)
                if score > best_score:
                    best_score = score
                    label_count = len(set(labels))
                    best_params = (eps, min_samples)

    if best_params is not None:
        cluster_result = f"最佳聚类数: {label_count}, 最佳轮廓系数: {round(best_score, 2)}\n最佳eps: {best_params[0]}, 最佳min_samples: {best_params[1]}"
    else:
        # print("没有找到合适的聚类参数组合。")
        cluster_result = f"没有找到合适的聚类参数组合，默认使用eps: 0.2, min_samples: 3进行聚类"
        best_params = (0.2, 3)
    return best_params, cluster_result

def analysis_text_search(user_name, name, df, column, cluster_config):
    if cluster_config["type"] == "text":
        feature_matrix = get_text_feature(user_name, df, column)
    else:
        feature_matrix = get_semantic_feature(user_name, df, column)
    labels, cluster_result = get_cluster_labels(user_name, feature_matrix, cluster_config, df)
    return labels, cluster_result