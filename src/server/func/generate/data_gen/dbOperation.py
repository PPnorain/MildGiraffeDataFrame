import copy
from pymongo import MongoClient
from fastapi import Depends
from common import DBOperator
from dependencies import get_db
from func.utils import get_content
from func.file.store import data_delete_std
from taskdata import GENERATION_STATUS

db = get_db()

class GenDBOperator(DBOperator):
    def __init__(self, user_name, template_name, seed_name, generate_filename):
        super().__init__(user_name)
        self.template_name = template_name 
        self.seed_name = seed_name
        self.generate_filename = generate_filename
        self.db_status_init()

    def db_get_template(self):
        if self.template_name:
            collections = self.db[self.user_name]['generation']
            template = collections.find_one({'name':self.template_name})
            return template['content']
        else:
            self.db_status_set('abort', '1')
            return None

    def db_get_seed(self, limit=0):
        '''
        version: 24.5.13
        功能简介：读取种子文件中的内容，添加大数据读取。
        '''
        if self.seed_name:
            return get_content(self.user_name, 'generation', self.seed_name, self.db, 'type', 'seed', limit)
        else:
            self.db_status_set('abort', '1')
            return None

    def db_set_generated(self, is_large=False):
        '''
        version: 24.6.3
        功能简介：删除旧生成数据，创建空的生成数据空间。支持大数据
        '''
        collections = self.db[self.user_name]['generation']
        # 删除生成的旧数据
        data_delete_std(self.user_name, 'generation', self.generate_filename, 'type', 'generated_data', 'generated_data', db=self.db)
        # 创建生成存储空间
        content = [] if not is_large else self.generate_filename
        collections.update_one(
            {'name':self.generate_filename, "type":"generated_data"}, 
            {"$set":{"content":content, 'is_large':is_large, "total_nums":0, "columns":[]}}, upsert=True)

        collection = self.db[self.user_name]['large']['generated_data'][self.generate_filename]


    def db_append_sample(self, sample, filedname=None, filedvalue=None, is_large=False, idx=0):
        if not is_large:
            collections = self.db[self.user_name]['generation']

            if not filedname or not filedvalue:
                collections.update_one(
                    {'name': self.generate_filename}, 
                    {"$push": {"content": sample}}, 
                    upsert=True
                )
            else:
                collections.update_one(
                    {'name': self.generate_filename, filedname: filedvalue}, 
                    {"$push": {"content": sample}}, 
                    upsert=True
                )
        else:
            collections = self.db[self.user_name]['large']['generated_data'][self.generate_filename]
            data = {'name':self.generate_filename, 'line_number':idx, 'content':sample}
            collections.insert_one(data)

    def db_set_meta(self, filedname=None, filedvalue=None):
        '''
        功能简介：实现数据的元信息添加。使得生成和数据上传的数据结构一致。
        元信息包括：数据名(name),大数据存储标志(is_large),数据总数(total_nums),数据列名列表(columns)共4个元信息。
        备注： 1.添加大数据元信息的计算。(v24.6.4)
        '''
        # 1. 准备数据
        collections = self.db[self.user_name]['generation']

        # 2. 元信息计算
        if not filedname or not filedvalue:
            search_condition = {'name': self.generate_filename}
        else:
            search_condition = {'name': self.generate_filename, filedname: filedvalue}

        data = collections.find_one(search_condition, {'_id':0})
        is_large = data['is_large']
 
        if not is_large:
            total_nums = len(data['content'])
        else:
            collections_large = self.db[self.user_name]['large']['generated_data'][self.generate_filename]
            total_nums = collections_large.count_documents({})

        meta_info = {
            "total_nums": total_nums,
            "columns":['prompt', 'response'],
        }
        # 3. 插入元信息
        collections.update_one(
            search_condition,
            {"$set": meta_info}, 
            upsert=True
        )
    # 状态记录系统
    def db_status_init(self):
        collections = self.db['init']
        status = copy.deepcopy(GENERATION_STATUS)
        status['template_name'], status['seed_name'], status['generate_filename'] = self.template_name, self.seed_name, self.generate_filename
        collections.update_one({'name':self.user_name}, {"$set":{'generation_status':status}})
        
    def db_status_set(self, key, value):
        collections = self.db['init']
        collections.update_one({'name':self.user_name}, {"$set":{f'generation_status.{key}':value}})

    def db_status_get(self, key):
        collections = self.db['init']
        status = collections.find_one({"name":self.user_name})
        return status['generation_status'][key]
    
    def db_add_heart(self, heart):
        '''
        功能简介：数据生成状态空间心跳。
        '''
        collections = self.db['init']
        # heart = collections.find_one({"name":self.user_name})['generation_status']['heart']
        collections.update_one({'name':self.user_name}, {"$set":{f'generation_status.heart':heart}})

def db_userspace_filedvalue(user_name, filedname, item_name):
    '''
    功能简介：获取用户空间中指定数据域的命名列表。
    '''
    query = {'name':user_name}
    content = {f'{filedname}.{item_name}':1}
    collection = db['init']
    res = collection.find_one(query, content)
    return res[filedname][item_name]