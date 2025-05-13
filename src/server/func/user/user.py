import json, copy
from typing import Union
from fastapi import APIRouter, Depends
from dependencies import get_db
from bson import json_util
from pydantic import BaseModel

router_user = APIRouter()
from func.generate.generate_api import GenRequestData
from taskdata import GENERATION_STATUS

class UserConfig(BaseModel):
    user_name: str
    generation: GenRequestData

@router_user.get("/standard-api/login/")
async def user_login(user_name:str, db=Depends(get_db)):
    '''用户登录：更新已有用户状态，新用户创建新账户(重名用户暂时无判断)'''
    try:
        user_collection = db['init']
        query = {"name":user_name}
        if len(list(user_collection.find(query))) > 0:
            user_collection.update_one(query, {'$set': {'status': 'login'}})
            items = user_collection.find_one(query)
            return {'code':200, 'data':json.loads(json_util.dumps(items)), 'message':'success'}
        # 创建用户空间
        user_doc = {
            "name": user_name,
            "status": "login",
            "logs": "",
            "model_config": dict(),
            "generation_status": copy.deepcopy(GENERATION_STATUS)
        }
        user_collection.insert_one(user_doc)
        return {'code':200, 'data':json_util.dumps(user_doc), 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}


@router_user.post("/standard-api/logout/")
async def user_logout(user_config: UserConfig, db=Depends(get_db)):
    '''用户登出操作，存储用户状态和部分配置'''
    try:
        user_collection = db['init']
        user_collection.update_one({'name': user_config.user_name}, {'$set': user_config.dict()})
        return {'code':200, 'data':'', 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}