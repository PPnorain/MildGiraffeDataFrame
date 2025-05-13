def get_search_condition(name, filedname, filedvalue):
    # 兼容filedname和filedvalue参数
    filedname = None if filedname == "None" else filedname 
    filedvalue = None if filedvalue == "None" else filedvalue 
    if not filedname or not filedvalue:
        search_condition = {'name': name}
    else:
        search_condition = {'name': name, filedname:filedvalue}
    return search_condition

def get_content(user_name, tab, filename, db, filedname=None, filedvalue=None, limit=0):
    collections = db[user_name][tab]
    search_condition = get_search_condition(filename, filedname, filedvalue)
    result = collections.find_one(search_condition, {'_id':0})
    sub_type = '' if filedname != 'type' else filedvalue
    if result:
        if result.get('is_large', False):  # 如果is_large字段为True
            if not sub_type:
                large_collection = db[user_name]['large'][result['content']]  # 在大数据的集
            else:
                large_collection = db[user_name]['large'][sub_type][result['content']]  # 在大数据的集
            if limit:
                large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1}).limit(limit)]  
            else:
                large_data = [doc['content'] for doc in large_collection.find({}, {'_id':0, 'content':1})]  

            if large_data:
                result['content'] = large_data  # 将查询到的大数据放回原位置
    return result['content']