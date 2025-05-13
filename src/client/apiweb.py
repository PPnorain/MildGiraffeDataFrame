import requests, time, os, json, time
import gradio as gr
from conf.userconf import URL, PAGE_LIMIT
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def deprecated_info(old_name, new_name, deadline=''):
    print(f"[ Deprecated ] 函数{old_name}将在后期被删除，请使用新函数{new_name}替代! 最后期限：{deadline}")

def api_reformat(response, message):
    if response.status_code != 200:
        return {'code':response.status_code, 'data':'', 'message':message}
    return response.json()

def api_login(user_name):
    url = URL+f'standard-api/login/?user_name={user_name}'
    response = requests.get(url)
    return api_reformat(response, '登录请求[standard-api/login]失败')

def api_logout(user_config):
    url = URL+f'standard-api/logout/'
    response = requests.post(url, json=user_config)
    return api_reformat(response, '登出请求[standard-api/logout]失败')

def api_write(user_name, typ, file_name, content, sub_type=''):
    '''
    指定collection存储数据，字段固定
    只能在doc中的content字段中存储数据，并且content需要是字典或列表。
    '''
    if not sub_type:
        url = URL+"standard-api/write/"
    else:
        url = URL+f"standard-api/write/?sub_type={sub_type}"
    data={'db_name':user_name, 'db_type':typ, 'db_doc_name':file_name, 'db_doc_content':content}
    response = requests.post(url, json=data)
    return api_reformat(response, '写数据请求[standard-api/write]失败')

# 标准版读取API
def api_read(user_name, tab, file_name, filedname=None, filedvalue=None, limit=PAGE_LIMIT):
    '''用于读取doc中content字段的内容'''
    url = URL + f"standard-api/read/?user_name={user_name}&db_type={tab}&name={file_name}&limit={limit}&filedname={filedname}&filedvalue={filedvalue}"
    response = requests.get(url)
    return api_reformat(response, '数据读取请求[standard-api/read]失败')


def api_read_page(user_name, tab, file_name, page=1, filedname=None, filedvalue=None, limit=PAGE_LIMIT):
    '''用于读取doc中content字段的内容'''
    sub_type = filedvalue if filedname == 'type' else ''
    url = URL + f"standard-api/read/page/?user_name={user_name}&db_type={tab}&name={file_name}&page={page}&filedname={filedname}&filedvalue={filedvalue}&limit={limit}&sub_type={sub_type}"
    response = requests.get(url)
    return api_reformat(response, '数据页读取请求[standard-api/read/page]失败')

# 升级版删除API
def api_delete(user_name, tab, file_name, filedname=None, filedvalue=None, sub_type=''):
    url = URL + f"standard-api/delete/?user_name={user_name}&db_type={tab}&name={file_name}&filedname={filedname}&filedvalue={filedvalue}&sub_type={sub_type}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {'err_code':-1, 'err_content': f'删除失败:{response.status_code}'}

# TODO：即将被抛弃
def api_remove(user_name, typ, file_name):
    deprecated_info('api_remove', 'api_delete')
    url = URL + f"remove/?user_name={user_name}&db_type={typ}&name={file_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {'err_code': response.status_code, 'err_content':"响应失败"}

def api_refresh(user_name, typ):
    '''获取collections中所有文件的文件名'''
    url = URL + f'read/type_list/?user_name={user_name}&db_type={typ}'
    response = requests.get(url)
    return response.json()

def api_refresh_field(user_name, typ, fieldname, filedvalue):
    '''获取collections中符合指定域名的文档名'''
    url = URL + f'read/type_list/field/?user_name={user_name}&db_type={typ}&fieldname={fieldname}&filedvalue={filedvalue}'
    response = requests.get(url)
    return response.json()

def api_status_abort(user_name: str, func_typ: str):
    '''
    功能简介：发送中断请求
    '''
    url = URL + f'standard-api/monitor/abort/?user_name={user_name}&func_typ={func_typ}'
    response = requests.get(url)
    return api_reformat(response, '中断请求[standard-api/monitor/abort]失败')

def api_status_status(user_name: str, func_typ: str, status):
    '''
    功能简介：发送中断请求
    '''
    url = URL + f'standard-api/monitor/status/?user_name={user_name}&func_typ={func_typ}&status={status}'
    response = requests.get(url)
    return api_reformat(response, '中断请求[standard-api/monitor/abort]失败')

# 文件重复检查
def api_check_repeat(user_name, tab, file_name, filedname=None, filedvalue=None):
    '''
    功能简介：重复文件检查请求。
    返回：标准请求结果。
    '''
    url = URL+f"standarad-api/check/?user_name={user_name}&db_type={tab}&name={file_name}&filedname={filedname}&filedvalue={filedvalue}"
    response = requests.get(url)

    return api_reformat(response, '重复数据检查请求[standard-api/check]失败')

# 存储文件内容
def api_store(user_name, typ, file):
    '''读取文件内容，在指定collection中存储'''
    file_name = os.path.basename(file.name)
    with open(file.name, 'r', encoding='utf-8') as f:
        if file.name.endswith('.json'):
            content = json.load(f)
        elif file.name.endswith('.jsonl'):
            content = [json.loads(line) for line in f]
    response = api_write(user_name, typ, file_name, content)
    return response

# TODO 请求待更新
def api_store_filed(user_name, tab, name, typ, typ_value):
    '''在指定collection中添加(修改)指定字段'''
    url = URL + f'write/field/'
    data = {'user_name':user_name, 'tab':tab, 'name':name, 'typ':typ, 'typ_value':typ_value}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    return {'err_code':response.status_code}

# TODO 请求待更新
def api_get_list(user_name: str, typ: str):
    url = URL + f'getlist/?user_name={user_name}&typ={typ}'
    response = requests.get(url).json()
    return response

# TODO 请求待更新
def api_get_filed_list(user_name: str, typ: str, filedname: str, filedvalue: str):
    deprecated_info("api_get_filed_list", "not implement", "24-5-15")
    url = URL + f'read/type_list/field/?user_name={user_name}&db_type={typ}&fieldname={filedname}&filedvalue={filedvalue}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {'err_code':-1, "err_content":f"响应失败{response.status_code}"}

# 用户名空间的增删改查
## 查--列表
def api_get_userspace(user_name: str, filedname: str):
    '''
    功能简介：获取init中用户空间中用户存储的模型配置列表。
    备注：init中数据存储和其他用户空间的配置有所不同，需要专门实现API请求。
    '''
    url = URL + f'standard-api/userspace/filedlist/?user_name={user_name}&filedname={filedname}'
    response = requests.get(url)
    return api_reformat(response, '用户空间信息请求[standard-api/userspace/filedlist]失败')
## 查--内容
def api_get_userspace_item(user_name: str, filedname: str, item_name):
    '''
    功能简介：获取init中用户空间中用户存储的模型配置列表。
    备注：init中数据存储和其他用户空间的配置有所不同，需要专门实现API请求。
    '''
    url = URL + f'standard-api/userspace/filedvalue/?user_name={user_name}&filedname={filedname}&item_name={item_name}'
    response = requests.get(url)
    return api_reformat(response, '用户空间信息请求[standard-api/userspace/filedlist]失败')
# 增
def api_additem_userspace(user_name: str, filedname: str, filedvalue):
    '''
    功能简介：为init中用户空间中用户存储的模型配置列表增加一条数据。
    备注：init中数据存储和其他用户空间的配置有所不同，需要专门实现API请求。
    '''
    url = URL + f'standard-api/userspace/add/?user_name={user_name}&filedname={filedname}'
    response = requests.post(url, json=filedvalue)
    return api_reformat(response, '用户空间信息请求[standard-api/userspace/filedlist]失败')
# 删
def api_deleteitem_userspace(user_name: str, filedname: str, item_name: str):
    '''
    功能简介：为init中用户空间中用户存储的模型配置列表增加一条数据。
    备注：init中数据存储和其他用户空间的配置有所不同，需要专门实现API请求。
    '''
    url = URL + f'standard-api/userspace/delete/?user_name={user_name}&filedname={filedname}&item_name={item_name}'
    response = requests.get(url)
    return api_reformat(response, '用户空间信息请求[standard-api/userspace/filedlist]失败')

def api_get_meta_std(user_name: str, typ: str, file_name: str, filedname: str=None, filedvalue: str=None):
    '''
    功能简介：调用标准元信息获取API，获取指定数据集的元信息.
    返回：标准API请求结果。
    '''
    url = URL + f'standard-api/read/meta/?user_name={user_name}&db_type={typ}&name={file_name}&filedname={filedname}&filedvalue={filedvalue}'
    response = requests.get(url)
    return api_reformat(response, "数据元信息请求[standard-api/read/meta]失败")

# TODO 请求待更新
def api_read_doc_filed(user_name: str, typ: str, file_name: str, filedname: str):
    '''读取doc指定filed的值'''
    url = URL + f'read/filed/?user_name={user_name}&db_type={typ}&name={file_name}&filedname={filedname}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {'err': response.status_code}

# 回归
# TODO 请求待更新
def api_search(user_name, typ, file_name, s_key, s_col):
    url = URL + f"search/type_list/content/?user_name={user_name}&db_type={typ}&name={file_name}&s_key={s_key}&s_col={s_col}"
    response = requests.get(url).json()
    return response

# 标准日志格式字符串
def format_logs(info):
    # 获取时间戳
    timestamp = time.time()
    dt_object = datetime.fromtimestamp(timestamp)
    formatted_time = dt_object.strftime('%Y%m%d_%H:%M:%S')
    format_info = f'[ {formatted_time} ] {info}\n'
    return format_info

# 日志接口
def api_logs_write(user_name: str, info: str):
    url = URL+f'standard-api/logs/'
    data = {'user_name':user_name, 'info':format_logs(info)}
    response = requests.post(url, json=data)
    return api_reformat(response, '日志写请求[standard-api/logs/]失败')

def api_logs_read(user_name: str):
    url = URL+f'standard-api/logs/?user_name={user_name}'
    response = requests.get(url)
    return api_reformat(response, '日志读请求[standard-api/logs/]失败')

def api_logs_clear(user_name: str):
    url = URL+f'standard-api/logs/clear/?user_name={user_name}'
    response = requests.get(url)
    return api_reformat(response, '日志清除请求[standard-api/logs/clear]失败') 

# 搜索
def api_search_content(user_name, typ, file_name, search_config):
    # url = URL + f"standard-api/analysis_search/content/?user_name={user_name}&db_type={typ}&name={file_name}&search_config={search_config}"
    # response = requests.get(url)

    # 构造POST请求的URL
    url = URL + "standard-api/analysis_search/content/"
    headers = {"Content-Type": "application/json"}
    data = {
        "user_name": user_name,
        "db_type": typ,
        "name": file_name,
        "search_config": search_config
    }
    response = requests.post(url, headers=headers, json=data)
    return api_reformat(response, "搜索请求[standard-api/search/content]失败")


# ------------------- 数据分析功能请求 -------------------------
# 分布分析请求
def api_get_data_distribution(user_name, tab, file_name, method, column, config=None):
    url = URL + f"standard-api/get_data_distribution/?user_name={user_name}&tab={tab}&name={file_name}&method={method}&column={column}&config={config}"
    response = requests.get(url)
    return api_reformat(response, "搜索请求[standard-api/search/content]失败")

# 重复与判空分析请求
def api_get_condition_df(user_name, tab, file_name, condition_type, column, dup_method, dup_threshold, ngram_dup):
    url = URL + f"standard-api/get_condition_df/?user_name={user_name}&tab={tab}&name={file_name}&condition_type={condition_type}&column={column}&dup_method={dup_method}&dup_threshold={dup_threshold}&ngram_dup={ngram_dup}"
    response = requests.get(url)
    return api_reformat(response, "搜索请求[standard-api/search/content]失败")

# -------------------- 进度监控 ---------------------
# 进度监控---增量数据获取
def api_get_argu_data(user_name, db_type, name, start, filedname, filedvalue):
    # 增量数据请求
    url_get_argu_data = URL + f'standard-api/monitor/argu-read/?user_name={user_name}&db_type={db_type}&name={name}&start={start}&filedname={filedname}&filedvalue={filedvalue}'
    response = requests.get(url_get_argu_data)
    return api_reformat(response, "增量数据请求[standard-api/monitor/argu-read]失败")

# 进度监控---全局进度查询
def api_get_all_generation_tasks():
    # 增量数据请求
    url_get_all_generation_tasks = URL + f'standard-api/monitor/get_all_generation_tasks/'
    response = requests.get(url_get_all_generation_tasks)
    return api_reformat(response, "全局生成请求[standard-api/monitor/get_all_generation_tasks/]失败")