import pickle, sys, json
from fastapi import APIRouter, Depends
from dependencies import get_db, deprecated_info, PAGE_LIMIT
from pydantic import BaseModel
from typing import Union, Optional
# from pympler import asizeof
from func.utils import get_search_condition

router_store = APIRouter()

class DBData(BaseModel):
    db_name: str
    db_type: str
    db_doc_name: str
    db_doc_content: Union[list, dict]

def islarge(value):
    if isinstance(value, list):
        total_size = 0
        for chunk in value:  # 假设value是一个可迭代对象，如列表或生成器
            total_size += sys.getsizeof(chunk)
            if total_size > 4 * 1024 * 1024:  # 16MB
                return True
        # return False
    serialized_value = pickle.dumps(value)  # 序列化value
    size = sys.getsizeof(serialized_value)  # 计算序列化后的大小
    if size > 4 * 1024 * 1024:  # 16MB
        return True
    return False

# 大数据，写
@router_store.post("/standard-api/write/")
def data_store(dbdata:DBData, sub_type: str='', db=Depends(get_db)):
    '''
    功能简述：大型数据存储接口：该接口会读取并分析数据，记录数据的元信息。\n
    备注：
    1. db_doc_content的内容必须是list[dict]的形式。这里数据元信息包括：数据名(name),大数据存储标志(is_large),数据总数(total_nums),数据列名列表(columns)共5个元信息。
    2. 添加大数据存储：子域sub_type(24.6.3)
    '''
    try: 
        is_large, total_nums = islarge(dbdata.db_doc_content), len(dbdata.db_doc_content)
        columns = []
        if isinstance(dbdata.db_doc_content, list) and len(dbdata.db_doc_content) > 0:
            columns = list(dbdata.db_doc_content[0].keys())

        if is_large and isinstance(dbdata.db_doc_content, list):
            if not sub_type:
                large_collection = db[dbdata.db_name]['large'][dbdata.db_doc_name]  # 创建一个新的集合用于存储大于16M的数据
            else:
                large_collection = db[dbdata.db_name]['large'][sub_type][dbdata.db_doc_name]  # 创建一个新的集合用于存储大于16M的数据
            docs = [{'name':dbdata.db_doc_name, 'line_number': i+1, 'content': row} for i, row in enumerate(dbdata.db_doc_content)]
            large_collection.insert_many(docs)

            dbdata.db_doc_content = dbdata.db_doc_name  # 将用户数据空间中的内容替换为大数据在数据库中的集合名
        user_collection = db[dbdata.db_name][dbdata.db_type]
        user_collection.update_one({f'name':dbdata.db_doc_name}, {'$set': {'is_large': is_large, 'total_nums': total_nums, 'columns': columns, 'content': dbdata.db_doc_content}}, upsert=True)  # 更新数据时，同时更新is_large字段
        return {'code':200, 'data':'', 'message':'success'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# TODO 待删除
# 读取指定数据库的content内容
@router_store.get("/read/")
def data_read(user_name: str, db_type: str, name: str, db=Depends(get_db)):
    '''大型数据读取接口'''
    deprecated_info('/read/', '/standard-api/read/')
    user_collection = db[user_name][db_type]
    result = user_collection.find_one({'name': name}, {'_id':0})
    if result:
        if result.get('is_large', False):  # 如果is_large字段为True
            large_collection = db[user_name]['large'][result['content']]  # 在大数据的集合中查询大数据
            # TODO 这里大数据的查询需要优化，不能将全部数据都读取出来
            large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1}).limit(PAGE_LIMIT)]  # 查询大数据
            if large_data:
                result['content'] = large_data  # 将查询到的大数据放回原位置
        return result['content']
    return {'err_code':-2, 'err_content': 'No Data Found'}

# 大数据：读。读取指定数据库的content内容
@router_store.get("/standard-api/read/")
def data_read_standard(user_name: str, db_type: str, name: str, limit: int = PAGE_LIMIT, filedname:Union[None, str] = None, filedvalue:Union[None, str] = None, db=Depends(get_db)):
    '''
    功能简述：大型数据读取接口：读取匹配的doc name的content域的内容。该API包括大数据读取，域匹配读取。 \n
    参数：
        user_name,db_type组成collections的名字 \n
        name：用于匹配doc中name域的值 \n
        limit: 设置最大读取的数据数量；如果值为0，表示读取全部数据。
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
                large_data = []
                if limit:
                    large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1}).limit(limit)]  
                else:
                    large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1})]  
                # if large_data:
                result['content'] = large_data  # 将查询到的大数据放回原位置

            elif limit and isinstance(result['content'], list):
                result['content'] = result['content'][:limit]
            return {'code':200, 'data':result['content'], 'message':'success'} 

        return {'code':500, 'data':'', 'message':'没有查找到对应数据'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}
# 大数据-删
@router_store.get("/standard-api/delete/")
def data_delete_std(user_name: str, db_type: str, name: str, filedname:Union[None, str] = None, filedvalue:Union[None, str] = None, sub_type: str='', db=Depends(get_db)):
    '''
    功能简述：删除指定文件名的doc,包括大数据删除
    备注：1. 添加大数据子域sub_type的删除(24.6.3)
    '''

    try:
        user_collection = db[user_name][db_type]
        search_condition = get_search_condition(name, filedname, filedvalue)

        dataset = user_collection.find_one(search_condition, {'_id':0})
        if not dataset:
            return {'code':500, 'data':'', 'message':'没有对应数据'}

        if dataset.get('is_large', False):
            if not sub_type:
                db[user_name]['large'][dataset['content']].drop()
            else:
                db[user_name]['large'][sub_type][dataset['content']].drop()

        user_collection.delete_one({'name': name})
        return {'code':200, 'data':'', 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# 大数据-读：分页。读取指定数据库的content内容
@router_store.get("/standard-api/read/page/")
def data_read_page(user_name: str, db_type: str, name: str, page: int, limit: int = PAGE_LIMIT, filedname:Union[None, str] = None, filedvalue:Union[None, str] = None,sub_type: str='', db=Depends(get_db)):
    '''
    功能简述：大型数据读取接口：读取匹配的doc name的content域的内容 \n
    参数：
        user_name,db_type组成collections的名字 \n
        name：用于匹配doc中name域的值 \n
    备注：
        1. 目前最多读取5000条数据, page从1开始计数
        2. 添加大数据子域sub_type的删除(24.6.3)
    '''
    try:
        skip_nums = (page - 1) * limit
        user_collection = db[user_name][db_type]
        result = user_collection.find_one({'name': name}, {'_id':0})
        if result:
            if result.get('is_large', False):  # 如果is_large字段为True
                if not sub_type and filedname == 'type':
                    sub_type = filedvalue
                if not sub_type:
                    large_collection = db[user_name]['large'][result['content']]  # 在大数据的集合中查询大数据
                else:
                    large_collection = db[user_name]['large'][sub_type][result['content']]  # 在大数据的集合中查询大数据
                
                large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1}).skip(skip_nums).limit(limit)]  # 查询大数据
                result['content'] = large_data  # 将查询到的大数据放回原位置
            elif limit and isinstance(result['content'], list):
                result['content'] = result['content'][skip_nums:page*limit]
            return {'code':200, 'data':result['content'], 'message':'success'} 
        return {'code':500, 'data':'', 'message':'没有查找到对应数据'}
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# TODO 待删除
# 读取指定数据库的content内容
@router_store.get("/restrict-read/")
def restric_read(user_name: str, db_type: str, name: str, filedname:str, filedvalue:str, db=Depends(get_db)):
    '''
    功能简述：条件限制的大型数据读取接口：读取匹配doc name 以及filedname域为filedvalue的doc content域的内容
    备注：只能查找匹配filedname对应值域为字符串类型的对象
    '''
    deprecated_info('/restrict-read', '/standard-api/read/')
    user_collection = db[user_name][db_type]
    result = user_collection.find_one({'name': name, filedname:filedvalue}, {'_id':0})
    if result:
        if result.get('is_large', False):  # 如果is_large字段为True
            large_collection = db[user_name]['large'][result['content']]  # 在大数据的集合中查询大数据
            # TODO 这里大数据的查询需要优化，不能将全部数据都读取出来
            large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1}).limit(10000)]  # 查询大数据
            if large_data:
                result['content'] = large_data  # 将查询到的大数据放回原位置
        return result['content']

    return {'err_code':-2, 'err_content': 'No Data Found'}

class FieldWrite(BaseModel):
    user_name: str
    tab: str
    name: str
    typ: str
    typ_value: str

@router_store.post("/write/field/")
def data_store(dbdata:FieldWrite, db=Depends(get_db)):
    '''
    指定doc文档添加字段和对应的值 \n
    注意：对于没有对应collections或doc时，会创建新的collections或doc，再添加对应的key-value
    '''
    try:
        collection = db[dbdata.user_name][dbdata.tab]  # 创建一个新的集合用于存储大于16M的数据
        collection.update_one({f'name':dbdata.name}, {'$set': {dbdata.typ: dbdata.typ_value}}, upsert=True)  # 更新数据时
        return {'code':200, 'data':'', 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_store.post("/standard-api/write/field/")
def data_store(dbdata:FieldWrite, db=Depends(get_db)):
    '''
    功能简述：指定doc文档添加字段和对应的值 \n
    备注：对于没有对应collections或doc时，会创建新的collections或doc，再添加对应的key-value
    '''
    try:
        collection = db[dbdata.user_name][dbdata.tab]  # 创建一个新的集合用于存储大于16M的数据
        collection.update_one({f'name':dbdata.name}, {'$set': {dbdata.typ: dbdata.typ_value}}, upsert=True)  # 更新数据时
        return {'code':200, 'data':'', 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# TODO 待删除
@router_store.get("/delete/")
def data_delete(user_name: str, db_type: str, name: str, db=Depends(get_db)):
    '''
    功能简述：删除指定文件名的doc，包括大数据删除。
    '''
    deprecated_info('/delete/', '/standard-api/delete/')
    try:
        user_collection = db[user_name][db_type]
        dataset = user_collection.find_one({'name':name})
        if dataset.get('is_large', False):
            db[user_name]['large'][dataset['content']].drop()
        user_collection.delete_one({'name': name})
        return {'code':200, 'data':'', 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# TODO 待删除
@router_store.get("/restrict-delete/")
def data_restrict_delete(user_name: str, db_type: str, name: str, filedname: str, filedvalue: str, db=Depends(get_db)):
    deprecated_info('/restrict-delete/', '/standard-api/delete/')
    user_collection = db[user_name][db_type]
    dataset = user_collection.find_one({'name':name, filedname:filedvalue})
    if dataset.get('is_large', False):
         db[user_name]['large'][dataset['content']].drop()
    user_collection.delete_one({'name': name})
    return {'success':1, 'success_content':'删除数据成功'}

# TODO 待删除
@router_store.get("/standard-api/restrict-delete/")
def data_restrict_delete(user_name: str, db_type: str, name: str, filedname: str, filedvalue: str, db=Depends(get_db)):
    '''
    功能简述：限制条件删除doc：删除名字和指定域值匹配的doc
    '''
    deprecated_info('/standard-api/restrict-delete/', '/standard-api/delete/')
    try:
        user_collection = db[user_name][db_type]
        dataset = user_collection.find_one({'name':name, filedname:filedvalue})
        if not dataset:
            return {'code':500, 'data':'', 'message':'没有对应数据'}

        if dataset.get('is_large', False):
            db[user_name]['large'][dataset['content']].drop()
        user_collection.delete_one({'name': name})
        return {'code':200, 'data':'', 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_store.get("/remove/")
async def data_remove(user_name: str, db_type: str, name: str, db=Depends(get_db)):
    user_collection = db[user_name][db_type]
    if len(list(user_collection.find({f'name': name}))) > 0:
        user_collection.delete_one({"name": name})
        return {'err': 0}
    else:
        return {'err': 1}

@router_store.get("/standard-api/remove/")
async def data_remove(user_name: str, db_type: str, name: str, db=Depends(get_db)):
    '''
    功能简述：删除doc：删除指定名字的doc\n
    备注：它与/standard-api/delete/的功能相同，不同的是该API是直接删除对应doc，没有考虑大数据存储关联的数据库，而前者考虑了大数据关联数据库的操作。建议使用前者，后期该API可能会考虑进行删除
    '''
    try:
        user_collection = db[user_name][db_type]
        if len(list(user_collection.find({f'name': name}))) > 0:
            user_collection.delete_one({"name": name})
            return {'code':200, 'data':'', 'message':'success'} 
        else:
            return {'code':500, 'data':'', 'message':'没有找到对应数据'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_store.get("/read/type_list/")
def read_type_list(user_name: str, db_type: str, db=Depends(get_db)):
    user_collection = db[user_name][db_type]
    collection_names = [doc['name'] for doc in user_collection.find() if 'name' in doc]
    return collection_names

@router_store.get("/standard-api/read/type_list/")
def read_type_list_std(user_name: str, db_type: str, db=Depends(get_db)):
    '''
    功能简述：获取doc名字列表：读取指定集合中所有doc name域的值，返回列表\n
    备注:如果数据库不存在它也不会报错，而是返回空。
    '''
    try:
        user_collection = db[user_name][db_type]
        collection_names = [doc['name'] for doc in user_collection.find() if 'name' in doc]
        return {'code':200, 'data':collection_names, 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_store.get("/read/type_list/field/")
def data_read_field(user_name: str, db_type: str, fieldname: str, filedvalue: str, db=Depends(get_db)):
    '''读取指定collections中满足filedname值为filedvalue的所有doc的name'''
    user_collection = db[user_name][db_type]
    doc_names = [doc['name'] for doc in user_collection.find({fieldname: filedvalue}, {'name': 1, '_id': 0})]
    doc_names = list(reversed(doc_names))
    return doc_names

@router_store.get("/standard-api/read/type_list/field/")
def data_read_field(user_name: str, db_type: str, fieldname: str, filedvalue: str, db=Depends(get_db)):
    '''
    功能简述：获取限制条件的doc名字列表：读取指定collections中满足filedname值为filedvalue的所有doc的name\n
    备注：如果数据库不存在它也不会报错，而是返回空。
    '''
    try:
        user_collection = db[user_name][db_type]
        doc_names = [doc['name'] for doc in user_collection.find({fieldname: filedvalue}, {'name': 1, '_id': 0})]
        doc_names = list(reversed(doc_names))
        return {'code':200, 'data':doc_names, 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_store.get("/read/filed/")
def doc_read_field(user_name: str, db_type: str, name: str, filedname, db=Depends(get_db)):
    '''读取指定doc中filedname域的值'''
    user_collection = db[user_name][db_type]
    filedvalue = user_collection.find_one({'name':name}, {'_id':0, filedname:1})
    return filedvalue

@router_store.get("/standard-api/read/filed/")
def doc_read_field(user_name: str, db_type: str, name: str, filedname, db=Depends(get_db)):
    '''
    功能简述：读取指定doc中filedname域的值
    '''
    try:
        user_collection = db[user_name][db_type]
        filedvalue = user_collection.find_one({'name':name}, {'_id':0, filedname:1})
        if filedvalue is None:
            return {'code':200, 'data':filedvalue, 'message':'没有找到对应数据'} 
        return {'code':200, 'data':filedvalue, 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

@router_store.get("/read/meta/")
def read_meta(user_name: str, db_type: str, name: str, db=Depends(get_db)):
    '''读取数据的所有元信息'''
    user_collection = db[user_name][db_type]
    meta_info = user_collection.find_one({'name':name}, {'_id':0, 'content':0, "result":0, "badcase":0, "evaluation":0})
    return meta_info

@router_store.get("/standard-api/read/meta/")
def read_meta_std(user_name: str, db_type: str, name: str, filedname:Union[None, str] = None, filedvalue:Union[None, str] = None, db=Depends(get_db)):
    '''
    功能简述：读取指定doc数据的所有元信息\n
    备注：元信息是指，除了_id,content,result,badcase,evaluation域之外的所有键值对。
    '''
    try:
        search_condition = get_search_condition(name, filedname, filedvalue)
        # 条件搜索
        user_collection = db[user_name][db_type]
        result = user_collection.find_one(search_condition, {'_id':0})

        meta_info = user_collection.find_one({'name':name}, {'_id':0, 'content':0, "result":0, "badcase":0, "evaluation":0})
        if meta_info is None:
            return {'code':200, 'data':meta_info, 'message':'没有找到对应数据'} 
        return {'code':200, 'data':meta_info, 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# 回归
@router_store.get("/read/type_list/content/")
async def read_precontent(user_name: str, db_type: str, name: str, db=Depends(get_db)):
    user_collection = db[user_name][db_type]
    content = user_collection.find_one({'name': name})['content']
    return content

@router_store.get("/standard-api/read/type_list/content/")
async def read_precontent(user_name: str, db_type: str, name: str, db=Depends(get_db)):
    '''
    功能简述：读取指定doc中数据域内容\n
    备注：数据域是指content字段,并且不支持大文件读取
    '''
    try:
        user_collection = db[user_name][db_type]
        content = user_collection.find_one({'name': name})
        if content is None or 'content' not in content:
            return {'code':200, 'data':'', 'message':'没有找到对应数据'} 

        return {'code':200, 'data':content, 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}

# 检查是否存在重名文件
@router_store.get("/standarad-api/check/")
async def data_check(user_name: str, db_type: str, name: str, filedname:Union[None, str] = None, filedvalue:Union[None, str] = None, db=Depends(get_db)):
    '''
    功能简述：检查指定collection是否存在name域为name的doc
    '''
    try:
        search_condition = get_search_condition(name, filedname, filedvalue)

        user_collection = db[user_name][db_type]
        if len(list(user_collection.find(search_condition))) > 0:
            return {'code':200, 'data':True, 'message':'success'} 
        return {'code':200, 'data':False, 'message':'success'} 
    except:
        return {'code':500, 'data':'', 'message':'数据库操作失败'}