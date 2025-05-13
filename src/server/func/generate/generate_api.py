from typing import Optional, Union

from fastapi import APIRouter, Depends, BackgroundTasks
from dependencies import get_db
from pydantic import BaseModel
from .data_gen.run_datagen import run_datagen
from dataclasses import dataclass, asdict

router_generate = APIRouter()

class GenConfigFSG(BaseModel):
    FSG_min: int=1
    FSG_max: int=2
    FSG_typ: Optional[str]='prompt-response'
    FSG_template_map: Union[str, list, None]=''
    FSG_sep_map: Union[str, list, None]=''
    FSG_prompt_map: Union[str, list, None]=''
    FSG_response_map: Union[str, list, None]=''

class GenConfigBA(BaseModel):
    BA_template_map: Union[str, list, None]=''
    BA_prompt_map: Union[str, list, None]=''


class ModelConfig(BaseModel):
    api_type: Optional[str]=''
    api_base: Optional[str]=''
    api_key: Optional[str]=''
    deployment_name: Optional[str]=''
    temperature: float=0.8
    top_p: float=0.7
    thread_num: int=20
    sleep_time: int=0
class NamedModelConfig(BaseModel):
    models_config_name: str=''
    models_config: ModelConfig=ModelConfig()

FiledConfig = Union[NamedModelConfig]

class Extra(BaseModel):
    FSG: GenConfigFSG = GenConfigFSG()
    BA: GenConfigBA = GenConfigBA()

class GenRequestData(BaseModel):
    generate_method: Optional[str]=''
    template_name: Optional[str]=''
    seed_name: Optional[str]=''
    models_config_list: Optional[str]=''
    generate_fault_tolerance: int=0
    generate_number: int=10
    generate_filename: Optional[str]=''
    extra: Extra=Extra()

class UserGenRequest(BaseModel):
    user_name: str
    generation: GenRequestData = GenRequestData()

@router_generate.post("/standard-api/generate/")
async def generate_data(gen_config:UserGenRequest, background_tasks: BackgroundTasks):
    '''
    功能简介：进行生成操作。生成数据再数据库中不在返回值中，需要另外请求。\n
    备注：message中存储了生成的日志状态，为空表示生成正常进行。非空表示出现错误，可以通过message字段知道部分错误原因。data域永远返回空字符串。
    '''
    try:
        gen_status = run_datagen(gen_config, background_tasks)
        return gen_status
    except:
        return {'code':500, 'data':'', 'message':'数据生成失败'}

# TODO 待删除
@router_generate.get("/monitor/generate/content/")
def monitor_regresstest_content(user_name: str, tab: str, filename: str, data_typ:str, db=Depends(get_db)):
    deprecated_info("/monitor/generate/content/", "/standard-api/monitor/generate/content/", '2024-6-17')
    collection = db[user_name][tab]
    content = collection.find_one({'name': filename}, {'_id':0, data_typ: 1})
    return content

# 生成任务管理--内容监控
@router_generate.get("/standard-api/monitor/generate/content/")
def monitor_regresstest_content(user_name: str, tab: str, filename: str, data_typ:str, db=Depends(get_db)):
    '''
    功能简述：获取指定collection中name域未filename中data_typ域中的内容
    '''
    try:
        collection = db[user_name][tab]
        content = collection.find_one({'name': filename}, {'_id':0, data_typ: 1})
        if content is None or not content:
            return {'code':200, 'data':'', 'message':'未找到数据'} 
        return {'code':200, 'data':content[data_typ], 'message':'success'} 
            
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# 生成任务管理--全局任务查询
@router_generate.get("/standard-api/monitor/get_all_generation_tasks/")
def monitor_regresstest_content(db=Depends(get_db)):
    '''
    功能简述：获取整个平台的所有用户的生成任务状态
    '''
    # from ipdb import set_trace
    # set_trace()
    try:
        collection = db['init']
        documents = collection.find({}, {'_id':0, 'name': 1, 'generation_status': 1})
        result = []
        for doc in documents:
            name, generation_status = doc.get('name', None), doc.get("generation_status", None)
            result.append(dict(name=name, generation_status=generation_status))
        return {'code':200, 'data':result, 'message':'success'} 
            
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

#TODO 待删除
@router_generate.get("/generate/get_config/")
def get_generation_config(user_name, db=Depends(get_db)):
    '''获取用户名的配置字段的值'''
    deprecated_info("/generate/get_config/", "/standard-api/generate/get_config/", '2024-6-17')
    collection = db['init']
    generation_config = collection.find_one({'name': user_name}, {'_id':0, 'generation': 1})
    if generation_config:
        return generation_config['generation']
    return {'err_code': -1, 'err_content':f'没有找到{user_name}的配置信息！'}

@router_generate.get("/standard-api/generate/get_config/")
def get_generation_config(user_name, db=Depends(get_db)):
    '''
    功能简介：获取用户名的生成模块的配置字段的值。
    '''
    try:
        collection = db['init']
        generation_config = collection.find_one({'name': user_name}, {'_id':0, 'generation': 1})
        if generation_config:
            return {'code':200, 'data': generation_config['generation'], 'message':'success'} 
        return {'code':200, 'data':'', 'message':'未找到数据'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

class TemplateSave(BaseModel):
    user_name: str
    template_content: str
    save_name: str

@router_generate.post("/generate/save_template/")
def save_generation_template(template_save: TemplateSave, db=Depends(get_db)):
    '''
    功能简介：存储用户的自定义模板。
    '''
    try:
        user_name = template_save.user_name
        collection = db[user_name]['generation']
        res = collection.update_one({'name': template_save.save_name}, {"$set":{"content":template_save.template_content, "type":"template"}}, upsert=True)
        return {'code':200, 'data':'', 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# TODO
@router_generate.post("/standard-api/generate/save_template/")
def save_generation_template(template_save: TemplateSave, db=Depends(get_db)):
    '''
    功能简介：存储用户的自定义模板。
    '''
    try:
        user_name = template_save.user_name
        collection = db[user_name]['generation']
        res = collection.update_one({'name': template_save.save_name}, {"$set":{"content":template_save.template_content, "type":"template"}}, upsert=True)
        return {'code':200, 'data':'', 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# 用户空间增删改查
# 查-列表
@router_generate.get("/standard-api/userspace/filedlist/")
def userspace_filedlist(user_name, filedname, db=Depends(get_db)):
    '''
    功能简介：获取用户空间中指定数据域的命名列表。
    '''

    # 聚合管道：将 models_config 转换为数组形式
    pipeline = [
        {"$match": {"name":user_name}},
        {"$project": {"model_fields": {"$objectToArray": "$models_config"}}},
        {"$unwind": "$model_fields"},
        {"$group": {"_id": None, "fields": {"$addToSet": "$model_fields.k"}}}
    ]
    collection = db['init']
    # 执行聚合查询
    try:
        result = list(collection.aggregate(pipeline))
        # 提取结果中的字段名
        if result:
            fields = result[0]['fields']
            return {'code':200, 'data':fields, 'message':'success'}
        return {'code':200, 'data':[], 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}
# 查-详细配置
@router_generate.get("/standard-api/userspace/filedvalue/")
def userspace_filedvalue(user_name, filedname, item_name, db=Depends(get_db)):
    '''
    功能简介：获取用户空间中指定数据域的命名列表。
    '''
    query = {'name':user_name}
    content = {f'{filedname}.{item_name}':1}
    collection = db['init']
    # 执行聚合查询
    try:
        res = collection.find_one(query, content)
        if res: return {'code':200, 'data':res[filedname][item_name], 'message':'success'}
        return {'code':200, 'data':'', 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# 增
@router_generate.post("/standard-api/userspace/add/")
def userspace_filedlist_add(user_name, filedname: str, item: FiledConfig, db=Depends(get_db)):
    '''
    功能简介：为用户空间指定域中添加一条信息。
    '''
    def update_config(collection, user_name, config_name, config_info):
        if not config_name: return False
        query = {"name": user_name}
        update = {"$set": {f"models_config.{config_name}":config_info}}
        # 执行查询
        result = collection.update_one(query, update)
        if result.modified_count > 0: return True
        return False

    try:
        user_collection = db['init']
        config_dict = item.models_config.dict()
        models_config_dict = {key: (value.strip() if isinstance(value, str) else value) for key, value in config_dict.items()} # 去除前尾空格
        res = update_config(user_collection, user_name, item.models_config_name.strip(), models_config_dict)
        if not res: return {'code':500, 'data':'', 'message':'数据库操作失败'}
        return {'code':200, 'data':'', 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}
# 删
@router_generate.get("/standard-api/userspace/delete/")
def userspace_filedlist_delete(user_name, filedname: str, item_name: str, db=Depends(get_db)):
    '''
    功能简介：为用户空间指定域中添加一条信息。
    '''
    try:
        user_collection = db['init']
        query = {"name":user_name}
        update = {"$unset": {f"models_config.{item_name}":""}}
        # 执行查询
        result = user_collection.update_one(query, update)
        if result.modified_count == 0: return {'code':500, 'data':'', 'message':'数据库操作失败'}
        return {'code':200, 'data':'', 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}