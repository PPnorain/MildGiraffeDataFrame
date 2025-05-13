import time
from datetime import datetime
from abc import ABC, abstractmethod
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from dependencies import get_db, deprecated_info
import pandas as pd
from typing import Union
from func.utils import get_search_condition

router_common = APIRouter()

class DBOperator(ABC):
    db = get_db()
    def __init__(self, user_name):
        self.user_name = user_name
    # 状态记录系统
    @abstractmethod
    def db_status_init(self):
        pass
    @abstractmethod 
    def db_status_set(self, key, value):
        pass
    @abstractmethod
    def db_status_get(self, key):
        pass
    # 异常日志记录
    def db_logs_write(self, info):
        collection = self.db['init']
        doc = collection.find_one({'name': self.user_name})
        new_logs = doc.get('logs', '') + self.__format_logs__(info)
        collection.update_one({'name': self.user_name}, {"$set": {"logs": new_logs}})

    def db_get_dataset(self, dataset_name):
        collections = self.db[self.user_name]['dataset_info']
        dataset = collections.find_one({'name': dataset_name})
        if dataset:
            df = pd.DataFrame(dataset['content'])
        else:
            df = pd.DataFrame({})
        return df

    # 标准日志格式字符串
    @classmethod
    def __format_logs__(cls, info):
        # 获取时间戳
        timestamp = time.time()
        dt_object = datetime.fromtimestamp(timestamp)
        formatted_time = dt_object.strftime('%Y%m%d_%H:%M:%S')
        format_info = f'[ {formatted_time} ] {info}\n'
        return format_info

class UtilsDBOperator(DBOperator):
    @classmethod
    def db_logs_write_util(cls, user_name, info):
        collection = cls.db['init']
        doc = collection.find_one({'name': user_name})
        new_logs = doc.get('logs', '') + cls.__format_logs__(info)
        collection.update_one({'name': user_name}, {"$set": {"logs": new_logs}})

# 状态监控系统--进度监控
@router_common.get("/standard-api/monitor/progress/")
async def monitor_progress(user_name: str, func_typ: str, db=Depends(get_db)):
    '''进度监控：读取用户任务状态空间中的状态结构体'''
    try:
        collection = db['init']
        process = collection.find_one({'name': user_name}, {'_id':0, f'{func_typ}_status': 1})
        return {'code':200, 'data':process, 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库查询失败'}

# # 状态监控系统--增量数据读取
@router_common.get("/standard-api/monitor/argu-read/")
def monitor_read_argu(user_name: str, db_type: str, name: str, start: int = 0, filedname:Union[None, str] = None, filedvalue:Union[None, str] = None, db=Depends(get_db)):
    '''
    功能简述：大型数据读取接口：读取匹配的doc name的content域的内容。该API包括大数据读取，域匹配读取。 \n
    参数：
        user_name,db_type组成collections的名字 \n
        name：用于匹配doc中name域的值 \n
        start: 设置最大读取的数据数量；如果值为0，表示读取全部数据。
        filedname, filedvalue: 域和值匹配项，默认不进行限制。
    备注：1. 添加大数据读取子域。(24.6.3)
    '''

    try:
        search_condition = get_search_condition(name, filedname, filedvalue)

        user_collection = db[user_name][db_type]
        result = user_collection.find_one(search_condition, {'_id':0})

        if result:
            if result.get('is_large', False):  # 如果is_large字段为True
                if filedname == 'type' and filedvalue in ['seed', 'template', 'generated_data']:
                    large_collection = db[user_name]['large'][filedvalue][result['content']]  # 在大数据的集
                else:
                    large_collection = db[user_name]['large'][result['content']]  # 在大数据的集

                large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1}).skip(start)]  

                result['content'] = large_data  # 将查询到的大数据放回原位置

            elif isinstance(result['content'], list):
                result['content'] = result['content'][start:]
            return {'code':200, 'data':result['content'], 'message':'success'} 

        return {'code':500, 'data':'', 'message':'没有查找到对应数据'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_common.get("/standard-api/monitor/abort/")
def monitor_abort(user_name: str, func_typ: str, db=Depends(get_db)):
    '''中断置位：将用户任务状态空间中的中断标志置位'''
    try:
        collection = db['init']
        collection.update_one({'name': user_name}, {"$set": {f"{func_typ}_status.abort": 1}})
        return {'code': 200, 'data':'', 'message':'success'}
    except:
        return {'code': 500, 'data':'', 'message':'数据库更新失败'}

@router_common.get("/standard-api/monitor/status/")
def monitor_status(user_name: str, func_typ: str, status: str, db=Depends(get_db)):
    '''中断置位：将用户任务状态空间中的中断标志置位'''
    try:
        collection = db['init']
        collection.update_one({'name': user_name}, {"$set": {f"{func_typ}_status.status": status}})
        return {'code': 200, 'data':'', 'message':'success'}
    except:
        return {'code': 500, 'data':'', 'message':'数据库更新失败'}

# 日志系统
class LogInfo(BaseModel):
    user_name: str
    info: str

# TODO 待删除
@router_common.post("/logs/")
def logs_write(log_info: LogInfo, db=Depends(get_db)):
    '''Deprecated Mark'''
    try:
        deprecated_info('logs', 'standard-api/logs', '2024-5-10')
        collection = db['init']
        doc = collection.find_one({'name': log_info.user_name})
        new_logs = doc.get('logs', '') + log_info.info
        collection.update_one({'name': log_info.user_name}, {"$set": {"logs": new_logs}})
        return {'code': 200, 'data':'', 'message':'success'}
    except:
        return {'code': 500, 'data':'', 'message':'日志更新失败'}

@router_common.post("/standard-api/logs/")
def logs_write(log_info: LogInfo, db=Depends(get_db)):
    '''更新用户日志信息'''
    try:
        collection = db['init']
        doc = collection.find_one({'name': log_info.user_name})
        new_logs = doc.get('logs', '') + log_info.info
        collection.update_one({'name': log_info.user_name}, {"$set": {"logs": new_logs}})
        return {'code': 200, 'data':'', 'message':'success'}
    except:
        return {'code': 500, 'data':'', 'message':'日志更新失败'}

@router_common.get("/logs/")
def logs_read(user_name: str, db=Depends(get_db)):
    '''Deprecated Mark'''
    deprecated_info('/logs/', '/standard-api/logs', '2024-5-10')
    collection = db['init']
    logs = collection.find_one({'name': user_name}, {"logs": 1})
    if logs:
        return logs['logs']
    return '未查找到日志'

@router_common.get("/standard-api/logs/")
def logs_read(user_name: str, db=Depends(get_db)):
    '''读取用户日志信息'''
    try: 
        collection = db['init']
        logs = collection.find_one({'name': user_name}, {"logs": 1})
        if not logs: 
            return {'code': 500, 'data':'', 'message':'未查找到日志'}
        return {'code': 200, 'data':logs['logs'], 'message':'success'}
    except:
        return {'code': 500, 'data':'', 'message':'数据库查找失败'}

@router_common.get("/standard-api/logs/clear/")
def logs_clear(user_name: str, db=Depends(get_db)):
    '''清理用户日志'''
    try:
        collection = db['init']
        collection.update_one({'name': user_name}, {"$set": {"logs": ''}})
        return {'code': 200, 'data':'', 'message':'success'}
    except:
        return {'code': 500, 'data':'', 'message':'数据库操作失败'}
