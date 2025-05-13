import json
from fastapi import APIRouter, Depends
from dependencies import get_db
from bson import json_util
from pydantic import BaseModel
import pandas as pd

router_datamanager = APIRouter()

@router_datamanager.get("/getlist/")
def datamanager_getlist(user_name: str, typ:str, db=Depends(get_db)):
    '''获取指定集合下所有文件名'''
    user_collection = db[user_name][typ]
    names = []
    for doc in user_collection.find({}, {"name": 1, "_id": 0}): # we only want the "name" field
        names.append(doc["name"])
    names = list(reversed(names))
    return names

@router_datamanager.get("/standard-api/getlist/")
def datamanager_getlist(user_name: str, typ:str, db=Depends(get_db)):
    '''
    功能简述：获取指定集合下doc name域的值。
    '''
    try:
        user_collection = db[user_name][typ]
        names = []
        for doc in user_collection.find({}, {"name": 1, "_id": 0}): # we only want the "name" field
            names.append(doc["name"])
        names = list(reversed(names))
        return {'code':200, 'data':names, 'message':'success'}

    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_datamanager.get("/getlist/columns/")
def datamanager_getlist(user_name: str, typ:str, filename:str, db=Depends(get_db)):
    '''获取指定集合下所有文件名'''
    user_collection = db[user_name][typ][filename]
    columns = user_collection.find_one({'name':filename}, {"columns":1})
    if not columns: return []
    return columns

@router_datamanager.get("/standard-api/getlist/columns/")
def datamanager_getlist(user_name: str, typ:str, filename:str, db=Depends(get_db)):
    '''
    功能简述：获取指定集合中name域为filename的doc的columns域的值。\n
    备注：columns域中存储的表的列名，一般情况下是一个列表
    '''
    try:
        user_collection = db[user_name][typ]
        columns = user_collection.find_one({'name':filename}, {"columns":1})
        if columns is None: 
            return {'code':200, 'data':[], 'message':'未找到数据'} 
        return {'code':200, 'data':columns['columns'], 'message':'success'} 
            
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_datamanager.get("/standard-api/search/content/")
async def data_search(user_name: str, db_type: str, name: str, s_key: str, s_col: str, db=Depends(get_db)):
    '''
    功能简述：提供content域中的数据搜索功能。返回搜索到的数据列表。\n
    参数:
        user_name, db_type: 定位collection \n
        name: 定位doc name \n
        s_key: 定义搜索的关键词 \n
        s_col: 定义要搜索的列名 \n
    '''
    try:
        user_collection = db[user_name][db_type]
        is_large = user_collection.find_one({"name": name})["is_large"]
        if not is_large:
            pipeline = [
                {'$match': {'name': name}},  # 匹配doc的name字段
                {'$unwind': '$content'},  # 将content字段展开，每个元素都展开是一个doc
                {'$match': {f'content.{s_col}': {'$regex': s_key}}},  # 再展开后的doc进行二次匹配
                {'$project': {"_id": 0, "content": 1}}
            ]
            results = user_collection.aggregate(pipeline)
        else:
            large_content = user_collection.find_one({"name": name}, {"content": 1})["content"]
            large_collection = db[user_name]["large"][large_content]
            results = large_collection.find({f"content.{s_col}": {"$regex": s_key}})

        contents = []

        for x in results:
            contents.append(x['content'])
        return {'code': 200, 'data': contents, 'message': 'success'}
    except:
        return {'code': 500, 'data': '', 'message': '数据库操作失败'}