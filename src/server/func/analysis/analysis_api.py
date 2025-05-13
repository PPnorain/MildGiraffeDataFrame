import json, time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from dependencies import get_db
import pandas as pd
from .analysis_data.utils import get_condition_df, check_column_redundancy, analysis_frequency_distribution, analysis_length_distribution, analysis_text_distribution, analysis_semantic_distribution, check_ngrams_row_duplicate, analysis_text_search
from .analysis_data.duplicated_analysis import get_query_duplicate_df
from ..file.store import data_read_standard
from common import UtilsDBOperator

router_analysis = APIRouter()

class AnalysisRequestData(BaseModel):
    user_name: str
    typ: str
    name: str
    column_name: str

def read_data_multisource(user_name, typ, name, db):
    if typ == 'generation':
        response = data_read_standard(user_name, typ, name, filedname='type', filedvalue='generated_data', limit=0, db=db)
    else:
        response = data_read_standard(user_name, typ, name, limit=0, db=db)
    return response

@router_analysis.get("/standard-api/get_data_distribution/")
def get_data_distribution(user_name, tab, name, method, column, config=None, db=Depends(get_db)):
    '''
    功能简介：数据分析接口，可以实现频率分布和长度分布的计算。
    '''
    # 1.读取数据集
    response = read_data_multisource(user_name, tab, name, db)

    if response['code'] != 200:
        return json.dumps(response)
        
    if tab == 'generation' and len(response['data']) > 0 and len(response['data'][0]) == 0:
        df = pd.DataFrame(response['data'], columns=['text']).reset_index()
    else:
        df = pd.DataFrame(response['data'])
    cluster_info = ''
    analysis_result_data = {}
    # 2. 分析计算
    if method == 'freq':
        stati_info, data_count, analysis_result_data = analysis_frequency_distribution(df, column, config)
    elif method == 'length':
        stati_info, data_count, analysis_result_data = analysis_length_distribution(df, column)
    elif method == 'text_cluster':
        stati_info, data_count, cluster_info, analysis_result_data = analysis_text_distribution(user_name, name, df, column, config)
    elif method == 'semantic_cluster':
        stati_info, data_count, cluster_info, analysis_result_data = analysis_semantic_distribution(user_name, name, df, column, config)
    
    return {'code': 200, 'data':{'stati_info': {'text_info':stati_info[0], 'data_info':stati_info[1].to_dict()}, 'data_count': data_count.to_dict(), 'cluster_info': cluster_info, 'data_content': analysis_result_data}, 'message':'success'}

@router_analysis.get("/standard-api/get_condition_df/")
def get_condition_df_service(user_name: str, tab: str, name: str, condition_type: str, column: str=None, dup_method=None, dup_threshold=None, ngram_dup=None, db=Depends(get_db)):
    """
    功能简介：根据不同的条件找出满足条件的对应行的数据。
    参数：
        user:待查找的数据。
    """

    # 1. 数据加载
    response = read_data_multisource(user_name, tab, name, db)

    if response['code'] != 200:
        return json.dumps(response)
        
    # df = pd.DataFrame(response['data'])
    # df = pd.DataFrame(response['data'], columns=['text']).reset_index() if tab != "dataset_info" else pd.DataFrame(response['data'])
    if tab == 'generation' and len(response['data']) > 0 and len(response['data'][0]) == 0:
        df = pd.DataFrame(response['data'], columns=['text']).reset_index()
    else:
        df = pd.DataFrame(response['data'])
    # 2 分析计算
    condition_data, condition_rate, count = get_condition_df(df, condition_type, column, dup_method, dup_threshold, ngram_dup)
    return {'code': 200, 'data':{'condition_data':condition_data.to_dict(), 'condition_rate':condition_rate}, 'message':'success'}

@router_analysis.get("/standard-api/data_health_checker/")
def sse_data_health_checker(user_name: str, typ: str, name: str, db=Depends(get_db)):
    def data_health_checker(user_name: str, typ: str, name: str, db):
        '''
        功能简介：数据集健康检查API。检查包括：1.行重复率；2.行缺失率；3.长度得分；4.冗余字段计算；5.特殊字符计算；
        参数：
            user_name, typ, name: 决定数据集。

        '''

        try:
            # 1.读取数据集
            response = read_data_multisource(user_name, typ, name, db)

            if response['code'] != 200:
                yield json.dumps(response)
                return
            # df = pd.DataFrame(response['data'])
            # df = pd.DataFrame(response['data'], columns=['text']).reset_index() if typ != "dataset_info" else pd.DataFrame(response['data'])
            if typ == 'generation' and len(response['data']) > 0 and len(response['data'][0]) == 0:
                df = pd.DataFrame(response['data'], columns=['text']).reset_index()
            else:
                df = pd.DataFrame(response['data'])
            # 2. 进行健康分析
            ## 2.1 行重复率
            row_duplicate_data, row_duplicate_rate, count = get_condition_df(df, 'duplicate_rows')
            yield f"data: {json.dumps({'code':200, 'data':{'row_duplicate_rate':{'ratio': row_duplicate_rate, 'nums':count}}, 'message':'success'})}\n\n"

            ## 2.2 行空率
            row_null_data, row_null_rate, count = get_condition_df(df, 'null_rows')
            yield f"data: {json.dumps({'code':200, 'data':{'row_null_rate': {'ratio': row_null_rate, 'nums':count}}, 'message':'success'})}\n\n"

            ## 2.3 长度正常分数
            row_length_data, row_length_rate, count = get_condition_df(df, 'length_rows')
            yield f"data: {json.dumps({'code':200, 'data':{'row_length_rate': {'ratio':row_length_rate, 'nums':count}}, 'message':'success'})}\n\n"

            ## 2.4 特殊符号分数
            row_special_char_data, row_special_char_rate, count = get_condition_df(df, 'special_char_rows')
            yield f"data: {json.dumps({'code':200, 'data':{'row_special_char_rate': {'ratio':row_special_char_rate, 'nums':count}}, 'message':'success'})}\n\n"

            ## 2.5 全空列占比
            columns_null_data, columns_null_rate, count = check_column_redundancy(df)
            yield f"data:{json.dumps({'code':200, 'data':{'columns_null_rate': {'ratio':columns_null_rate, 'nums':count}}, 'message':'success'})}\n\n"

            ## 2.6 ngrams 重复率
            row_ngrams_data, row_ngrams_rate, count = check_ngrams_row_duplicate(df)
            yield f"data: {json.dumps({'code':200, 'data':{'row_ngrams_rate': {'ratio':row_ngrams_rate, 'nums':count}}, 'message':'success'})}\n\n"
        except Exception as e:
            print(e)
            yield f"data: {json.dumps({'code':500, 'data':'', 'message':'数据健康检查失败'})}\n\n"
    return StreamingResponse(data_health_checker(user_name, typ, name, db=db), media_type="text/event-stream")

class SearchData(BaseModel):
    user_name: str
    db_type: str
    name: str
    search_config: dict
@router_analysis.post("/standard-api/analysis_search/content/")
async def data_search(search_data:SearchData, db=Depends(get_db)):
    '''
    功能简述：提供content域中的数据搜索功能。返回搜索到的数据列表。\n
    参数:
        user_name, db_type: 定位collection \n
        name: 定位doc name \n
        s_key: 定义搜索的关键词 \n
        s_col: 定义要搜索的列名 \n
    '''
    try:
        # search_config = eval(search_config)
        user_name, db_type, name = search_data.user_name, search_data.db_type, search_data.name
        search_config = search_data.search_config
        user_collection = db[user_name][db_type]
        target_field = search_config['search_analysis_column']
        method = search_config['search_analysis_method']

        is_large = user_collection.find_one({"name":name})["is_large"]
        if method == 'key_search' or method == 'regex_search':
            s_type_map = {
                'key_search': search_config['search_analysis_keyword'],
                'regex_search': {'$regex': search_config['search_analysis_regex']}}
            s_col = search_config['search_analysis_column']
            if not is_large:
                pipeline = [
                    {'$match': {'name': name}},  # 匹配doc的name字段
                    {'$unwind': '$content'},  # 将content字段展开，每个元素都展开是一个doc
                    {'$match': {f'content.{s_col}': s_type_map[search_config['search_analysis_method']]}},  # 再展开后的doc进行二次匹配
                    {'$project': {"_id": 0, "content": 1}}
                ]
                results = user_collection.aggregate(pipeline)
            else:
                large_content = user_collection.find_one({"name": name}, {"content": 1})["content"]
                large_collection = db[user_name]["large"][large_content]
                results = large_collection.find({f"content.{s_col}": s_type_map[search_config['search_analysis_method']]})

            contents = []
            for x in results:
                # print(x['content'])
                contents.append(x['content'])

        elif method == 'cluster_search' or method == 'similar_search':
            response = data_read_standard(user_name, db_type, name, limit=0, db=db)
            if response['code'] != 200:
                return json.dumps(response)
            if db_type == 'generation' and len(response['data']) > 0 and len(response['data'][0]) == 0:
                df = pd.DataFrame(response['data'], columns=['text']).reset_index()
            else:
                df = pd.DataFrame(response['data'])

            if method == 'cluster_search':
                cluster_config = search_config['cluster_search_config']
                config = {"cluster_method": cluster_config["search_cluster_method"], "n_clusters": cluster_config["search_n_clusters"], "distance_threshold": 0, "search": True, "type": cluster_config["search_cluster_type"]}
                labels, cluster_data = analysis_text_search(user_name, name, df, target_field, config)
                contents = cluster_data.to_dict(orient='records')

            elif method == 'similar_search':
                if db_type == 'generation' and len(response['data']) > 0 and len(response['data'][0]) == 0:
                    df = pd.DataFrame(response['data'], columns=['text']).reset_index()
                else:
                    df = pd.DataFrame(response['data'])
                similar_config = search_config['similar_search_config']
                contents = get_query_duplicate_df(df, target_field, similar_config)
                contents = contents.to_dict(orient='records')

        return {'code':200, 'data':contents, 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}