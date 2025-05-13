# dependencies.py
# import re, torch
import requests, json
# from transformers import NougatProcessor, VisionEncoderDecoderModel

from pymongo import MongoClient
from fastapi import Depends

PAGE_LIMIT=2000
GEN_STORE_THREASHOLD = 5000

client = MongoClient('mongodb://admin:123@192.168.5.120:17017/')

# 数据库
def get_db():
    return client.XRDF

def deprecated_info(old_name, new_name, deadline=''):
    print(f"[ Deprecated ] 函数{old_name}将在后期被删除，请使用新函数{new_name}替代! deadline:{deadline}")


# 加载向量模型
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