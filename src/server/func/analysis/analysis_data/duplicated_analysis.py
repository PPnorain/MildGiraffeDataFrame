import difflib
import json, jieba
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein, requests
from nltk import ngrams
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
smoothing_function = SmoothingFunction().method1
from rouge import Rouge
from multiprocessing import Pool, cpu_count
from functools import partial
from tqdm import tqdm
from common import UtilsDBOperator

class CustomEmbeddings:
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
    def embed_query(self, text, **kwargs):
        data = {
            "text": [text],
            **kwargs
        }
        response = json.loads(requests.post(self.url, json=data, timeout=self.timeout).text)
        return response['data']['embedding'][0]
# TODO 需要设置自己的嵌入模型
embeddings = CustomEmbeddings("http://xx.xx.xx.xx:30316/embedding  ", 20)

def cut_text(text):
    return set(list(jieba.cut(text)))

def ngram_text(text, ngram):
    return set(ngrams(list(jieba.cut(text)), ngram, pad_left=True, pad_right=True, left_pad_symbol='<s>', right_pad_symbol='</s>'))

def list_cut_text(text):
    return list(jieba.cut(text))

def join_cut_text(text):
    return ' '.join(jieba.cut(text))

def preprocess_texts(texts, method, ngram=None):
    # 根据方法预处理文本，返回一个列表，其中包含每个文本的特征
    if method == "embedding_cosine_similarity":
        try:
            with Pool(cpu_count() // 2) as p:
                query_embeddings = list(tqdm(p.imap(embeddings.embed_query, texts), total=len(texts)))
        except Exception as e:
            print(f"Analysis Error occurred: {e}")
        return query_embeddings
    elif method == "jaccard_distance":
        with Pool(cpu_count() // 2) as p:
            return list(tqdm(p.imap(cut_text, texts), total=len(texts)))
    elif method == "ngram_similarity":
        with Pool(cpu_count() // 2) as p:
            func = partial(ngram_text, ngram=ngram)
            return list(tqdm(p.imap(func, texts), total=len(texts)))
    elif method == "levenshtein_distance":
        return texts
    elif method == "bleu_similarity":
        with Pool(cpu_count() // 2) as p:
            return list(tqdm(p.imap(list_cut_text, texts), total=len(texts)))
    elif method == "rouge_similarity":
        with Pool(cpu_count() // 2) as p:
            return list(tqdm(p.imap(join_cut_text, texts), total=len(texts)))
    else:
        return texts

import jieba
from tqdm import tqdm
from datasketch import MinHash, MinHashLSH
def get_hash_dupublicate(texts):
    # 初始化jieba分词器
    jieba.initialize()

    # 创建MinHash和LSH对象
    lsh = MinHashLSH(threshold=0.9, num_perm=128)
    minhashes = {}

    # 处理文本，计算MinHash
    for i, doc in enumerate(tqdm(texts)):
        words = jieba.cut(doc)
        m = MinHash(num_perm=128)
        for word in words:
            m.update(word.encode('utf8'))
        minhashes[i] = m
        lsh.insert(f"doc_{i}", m)

    # 查找重复文档
    duplicates_index = []
    for i, minhash in minhashes.items():
        result = lsh.query(minhash)
        if len(result) > 1:
            duplicates_index.append(i)
    return duplicates_index

def calculate_similarity_batch(feature1, feature2, method):
    # 根据方法批量计算相似度
    if method == "difflib_distance":
        return difflib.SequenceMatcher(None, feature1, feature2).ratio()
    elif method == "levenshtein_distance":
        Levenshtein_distance = Levenshtein.distance(feature1, feature2)
        return 1 - (Levenshtein_distance / (len(feature1) + len(feature2) - 1))
    if method == "embedding_cosine_similarity":
        vectors = np.array([feature1, feature2])
        return cosine_similarity(vectors)[0][1]
    elif method == "jaccard_distance":
        intersection = feature1.intersection(feature2)
        union = feature1.union(feature2)
        return len(intersection) / len(union)
    elif method == "ngram_similarity":
        common_ngrams = feature1.intersection(feature2)
        return len(common_ngrams) / max(len(feature1), len(feature2))
    elif method == "bleu_similarity":
        return sentence_bleu([feature1], feature2, weights=(0.5, 0.5, 0, 0), smoothing_function=smoothing_function)
    elif method == "rouge_similarity":
        rouge = Rouge()
        scores = rouge.get_scores(feature2, feature1)
        return scores[0]['rouge-l']['f']
    else:
        return 0

def get_duplicate_df(df, target_field, method, thresh=None):
    # 修改为exact_match/minhash去重
    if method == "MinHash":
        field_data = df.applymap(str).apply('\t'.join, axis=1) if target_field == "整行" else df.applymap(str)[target_field].tolist()
        jieba.initialize() # 初始化jieba分词器
        try:
            lsh = MinHashLSH(threshold=thresh, num_perm=128) # 创建MinHash和LSH对象
            minhashes = {}
            for i, doc in enumerate(tqdm(field_data)): # 处理文本，计算MinHash
                words = jieba.cut(doc)
                m = MinHash(num_perm=128)
                for word in words:
                    m.update(word.encode('utf8'))
                minhashes[i] = m
                lsh.insert(f"doc_{i}", m)
        except Exception as e:
            UtilsDBOperator.db_logs_write_util(f'[ Error ] 哈希去重出错：{e}，请调整阈值后重试')
            return None, None, None

        # 查找重复文档
        duplicates_index = []
        for i, minhash in minhashes.items():
            result = lsh.query(minhash)
            if len(result) > 1:
                duplicates_index.append(i)
        
        duplicate_df = df.iloc[duplicates_index]
        duplicated_rate = round(len(duplicate_df) / len(field_data), 5)
        duplicated_result = f"数据量：{len(duplicate_df)}; 占比：{duplicated_rate}"
        return duplicate_df.head(50), duplicated_result, len(duplicate_df)
    return None, None, None

def get_query_duplicate_df(df, target_field, similar_config):
    query, method, thresh, ngram = similar_config['search_similar_query'], similar_config['search_similar_method'], similar_config['search_similar_threshold'], similar_config['search_similar_ngram']

    field_data = df.applymap(str).apply('\t'.join, axis=1) if target_field == "整行" else df.applymap(str)[target_field].tolist()
    duplicate_indices = []
    text_features = preprocess_texts(field_data, method, ngram)
    query_feature = preprocess_texts([query], method, ngram)[0]
    for i, text in enumerate(tqdm(text_features)):
        sim = calculate_similarity_batch(query_feature, text, method)
        if sim > thresh:  # 相似度阈值根据需要调整
            duplicate_indices.append(i)

    duplicate_df = df.iloc[duplicate_indices]
    return duplicate_df