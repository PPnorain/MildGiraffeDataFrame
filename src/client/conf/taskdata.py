'''
数据类的设计符合前端组件的路径结构，使得数据类的名字和前端路径名之间可以相互转换。
该文件中定义的数据结构的嵌入路径一定是和组件在组件树中的路径结构是一致的。
'''
from dataclasses import dataclass
from typing import List, Optional, Union
# 生成组件全配置
@dataclass
class GenConfigFSG:
    FSG_min: int=1
    FSG_max: int=2
    FSG_typ: str='prompt-response'
    FSG_template_map: str='prompt-response'
    FSG_sep_map: str=''
    FSG_prompt_map: str=''
    FSG_response_map: str=''

@dataclass
class GenConfigBA:
    BA_template_map: str=''
    BA_prompt_map: List[str]=None

@dataclass
class Extra:
    FSG: GenConfigFSG = None
    BA: GenConfigBA = None

@dataclass
class GenConfig:
    generate_method: str=''  
    template_name: str='' 
    seed_name: str=''
    models_config_list: str=''
    generate_number: int=0
    generate_fault_tolerance: int=0
    generate_filename: str=''
    generate_overwrite: bool=False
    extra: Extra=None

# pdf处理组件全配置
@dataclass
class PDF2MDConfig:
    PDF2MD_generate_num: int=1024
    # --- lmr start --- 
    PDF2MD_pages: int=1
    pdf_total_num: int=1
    # --- lmr end --- 

@dataclass
class PreProcessExtra:
    PDF2MD: PDF2MDConfig = None

@dataclass
class PreProcessConfig:
    preprocess_method: str=''
    preprocess_extra: PreProcessExtra=None

# 回归测试组件全配置
@dataclass
class RegressConfig:
    collection_name: str=''
    api_url: str=''
    fixed_params: str=''
    keys_list: str=''
    data_mapping: str=''
    label_index: str=''
    evaluation_methods: List[str] = None
    judge_method: str=''
    thread_nums: int=1
    interval_time: int=0
    model: str=''

# 单独向用户空间传递模型配置的数据结构
@dataclass
class NamedModelConfig:
    models_config_name: str=''
    models_config: 'ModelConfig'=None
    @dataclass
    class ModelConfig:
        api_type: Optional[str]=''
        api_base: Optional[str]=''
        api_key: Optional[str]=''
        deployment_name: Optional[str]=''
        temperature: float=0.8
        top_p: float=0.7
        thread_num: int=20
        sleep_time: int=0

@dataclass
class ClusterConfig:
    analysis_source: str=''
    analysis_collection_name: str=''
    cluster_type: str='text'  # 文本/语义
    cluster_label: str=''  # 列名称
    cluster_method: str='Kmeans'  # kmeans/dbscan/hiper...
    cluster_figure_class: str='柱状图'  # 图形类别
    n_clusters: int = 0  # kmeans/hiper 参数
    distance_threshold: float = 0.1  # hiper 参数
    eps: float = 0.1  # dbscan 参数
    min_samples: int = 1  # dbscan 参数

@dataclass
class LengthConfig:
    analysis_source: str=''
    analysis_collection_name: str=''
    analysis_len_label: str=''
    analysis_len_class: str='柱状图'  # 图


@dataclass
class ClassConfig:
    analysis_source: str=''
    analysis_collection_name: str=''
    analysis_label: str= ''
    analysis_class: str= '柱状图'  # 图
    analysis_label_type: str= "单标签"  # 单、多标签
    ngram_rate: float=0.5
    ngram_n: int=1

@dataclass
class AnalySearchsisConfig:
    analysis_source: str=''
    analysis_collection_name: str=''
    search_analysis_method: str=''
    search_analysis_column: str=''
    search_analysis_keyword: str=''
    search_analysis_regex: str=''
    cluster_search_config: 'ClusterSearchConfig'=None
    similar_search_config: 'SimilarSearchConfig'=None
    @dataclass
    class ClusterSearchConfig:
        search_cluster_type: str='text'  # 文本/语义
        search_cluster_method: str='Kmeans'  # kmeans/dbscan/hiper...
        search_n_clusters: int = 0  # kmeans/hiper 参数
        # search_distance_threshold: float = 0.1  # hiper 参数
        # search_eps: float = 0.1  # dbscan 参数
        # search_min_samples: int = 1  # dbscan 参数
    @dataclass
    class SimilarSearchConfig:
        search_similar_method: str='exact_match'
        search_similar_query: str=''
        search_similar_threshold: float = 0.1
        search_similar_ngram: int=1

datatype_map = {
    'generation_config':{'path':'generation', 'type':GenConfig},
    'NamedModelConfig':{'path':'generation', 'type':NamedModelConfig},
    'preprocess_config':{'path':'preprocess', 'type':PreProcessConfig},
    'regresstest_config':{'path':'regresstest', 'type':RegressConfig},
    'class_config': {'path': 'analysis', 'type': ClassConfig},
    'length_config': {'path': 'analysis', 'type': LengthConfig},
    'cluster_config': {'path': 'analysis', 'type': ClusterConfig},
    'cluster_search_config': {'path': 'analysis', 'type': AnalySearchsisConfig},
}