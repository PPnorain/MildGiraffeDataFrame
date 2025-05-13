import os, requests, time, random, threading
import regex as re
import gradio as gr
import pandas as pd
from dataclasses import asdict
from manager import manager
from conf.userconf import URL, PAGE_LIMIT
from typing import Optional, Dict, Any, Generator
from concurrent.futures import ThreadPoolExecutor
from apiweb import api_read, api_read_page, api_refresh_field, api_store, api_store_filed, api_login, api_logout, api_logs_write, api_logs_read, api_write, api_delete, api_get_filed_list, deprecated_info, api_get_meta_std, api_check_repeat, api_additem_userspace, api_deleteitem_userspace, api_get_userspace, api_get_userspace_item, api_get_argu_data, api_status_abort, api_status_status, api_get_all_generation_tasks

from common import update_process_bar, get_logs, response_checker
from .utils import gen_config_checker, replace_sample_str, generate_query, get_gen_status, watchdogs, get_task_meta
from func.utils import WindowData

# ---------------- 生成过程控制 ----------------
# 生成控制---创建生成任务---主函数
def generate_data(component_data):
    '''
    功能简介：生成功能逻辑可控制函数，最终根据配置调用gr_generate来真正请求数据生成API。
    '''
    # 1. 生成参数获取
    generate_config = manager.get_current_conf(component_data)
    user_name = component_data[manager.get_elem_by_name('top.user_name')]
    session_flag = component_data[manager.get_elem_by_name('generation.session_flag')]
    generate_overwrite = generate_config['generate_overwrite']
    generate_config['generate_filename'] = generate_config['generate_filename'].strip()
    # 2. 生成状态确认
    if watchdogs(user_name):
        gr.Warning("有未完成任务，正在结束")
        if not make_interrupt(user_name, 'generation'):
            return []

    # 2. 生成参数检查
    if not gen_config_checker(user_name, generate_overwrite, generate_config): return []
    if not check_template_glue(user_name, generate_config): return []
    # 3. 生成请求与监控
    response = gr_generate({'user_name':user_name, 'generation':generate_config, 'session_flag':session_flag})

    yield from response

# 生成控制---创建生成任务和监控窗口---核心函数
def gr_generate(request_config):
    """
    功能简介：实现生成功能API的调用。
    1. 实现增量数据请求，增加数据性能(v24.6.4)
    """
    user_name, filename, session_flag = request_config['user_name'], request_config['generation']['generate_filename'], request_config['session_flag']
    gr.Info('[ Status ] 准备开启生成任务... ')
    yield gr.update(visible=False), gr.update(visible=False), get_logs(user_name)

    # 开启生成任务
    # import ipdb; ipdb.set_trace()
    url_generate = URL + f'standard-api/generate/'
    response = requests.post(url_generate, json=request_config)
    if response.json()['code'] != 200: return 

    # def post_request(url, data):
    #     return requests.post(url, json=data)
    # generate_threading = threading.Thread(target=post_request, args=(url_generate, request_config))
    # generate_threading.start()
    # time.sleep(10)

    # gr.Info('[ Status ] 开启生成任务... ')
    _, _, generation_status = get_gen_status(user_name)
    # 数据缓存
    session_flag['generation_window'] = True
    cache_response_content = WindowData(200)
    while watchdogs(user_name) and session_flag['generation_window']:
        _, _, generation_status = get_gen_status(user_name)
        # 状态保险丝：防止后端死掉后状态未改变(10s数据状态未改变，强制反转abort和status)
        # 增量数据请求
        response_content = api_get_argu_data(user_name, 'generation', filename, cache_response_content.total, 'type', 'generated_data')
        if response_content['code'] != 200: break
        # 数据累积
        cache_response_content.add_data(response_content['data'])
        yield update_process_bar(generation_status), gr.update(value=cache_response_content.data, visible=True), get_logs(user_name)
        time.sleep(2)
        if generation_status['status'] == 'finish':break
    if generation_status['err_code'] != '':
        gr.Warning('[ 失败 ] '+ generation_status['err_code'])

    _, _, generation_status = get_gen_status(user_name)
    response_content = api_get_argu_data(user_name, 'generation', filename, cache_response_content.total, 'type', 'generated_data')
    if response_content['code'] != 200: response_content['data'] = []
    cache_response_content.add_data(response_content['data'])
    yield update_process_bar(generation_status, visible=session_flag['generation_window']), gr.update(value=cache_response_content.data, visible=session_flag['generation_window']), get_logs(user_name)

# 生成控制---断点续连
def gr_generate_continue(user_name, session_flag):
    """
    功能简介：实现生成功能的断点续连。
    1. 实现增量数据请求，增加数据性能(v24.6.4)
    """

    gen_status, filename, generation_status = get_gen_status(user_name)
    session_flag['generation_window'] = True

    if not watchdogs(user_name):
        gr.Info('所有任务已完成')
        yield update_process_bar(generation_status), gr.update(value=[], visible=True), get_logs(user_name)
        return

    cache_response_content = WindowData(500)
    while watchdogs(user_name) and session_flag['generation_window']:
        _, _, generation_status = get_gen_status(user_name)
        # 状态保险丝：防止后端死掉后状态未改变(10s数据状态未改变，强制反转abort和status)
        # 增量数据请求
        response_content = api_get_argu_data(user_name, 'generation', filename, cache_response_content.total, 'type', 'generated_data')
        if response_content['code'] != 200: break
        # 数据累积
        cache_response_content.add_data(response_content['data'])
        yield update_process_bar(generation_status), gr.update(value=cache_response_content.data, visible=True), get_logs(user_name)
        time.sleep(2)
        if generation_status['status'] == 'finish': break
    
    if generation_status['err_code'] != '':
        gr.Warning('[ 失败 ] '+ generation_status['err_code'])

    _, _, generation_status = get_gen_status(user_name)
    response_content = api_get_argu_data(user_name, 'generation', filename, cache_response_content.total, 'type', 'generated_data')
    if response_content['code'] != 200: response_content['data'] = []
    cache_response_content.add_data(response_content['data'])
    yield update_process_bar(generation_status, visible=session_flag['generation_window']), gr.update(value=cache_response_content.data, visible=session_flag['generation_window']), get_logs(user_name)

# 生成控制---中断
def make_interrupt(user_name, func_typ):
    gr.Info("发出中断信号")
    response = api_status_abort(user_name, func_typ) # abort：1
    if not response_checker(response): 
        gr.Warning("发送中断请求信号失败")
        return 
    start_time = time.time()
    while True:
        time.sleep(5)  # 每5秒检查一次
        if watchdogs(user_name):  # 如果任务进程仍然存在
            if (time.time() - start_time) >= 60:  # 超过1分钟
                gr.Warning("任务无法在1分钟内终止，请再次中断或联系管理员")
                return False
            else:
                gr.Info("任务正在中断，请耐心等待")
        else:
            gr.Info("未完成任务已经终止")
            return True

# 生成控制----全局任务查看
def get_all_tasks():
    response = api_get_all_generation_tasks()
    if not response_checker(response): return 
    tasks_meta = []
    for task in response['data']:
        task_meta = get_task_meta(task)
        tasks_meta.append(task_meta)
    # from ipdb import set_trace
    # set_trace()
    df = pd.DataFrame(tasks_meta)
    return gr.update(value=df, visible=True) 

# 生成控制----关闭实时进度显示窗口
def close_generation_window(session_flag):
    session_flag["generation_window"] = False
## ------------ 模板预览 -----------------
# 模板预览----fewshot
def gr_generate_query(user_name, seed_name, template_name, FSG_min, FSG_max, FSG_typ, FSG_template_map, FSG_sep_map, FSG_prompt_map, FSG_response_map):
    '''
    功能简介：生成few-shot的query预览。
    '''
    if not seed_name or not template_name:
        api_logs_write(user_name, f'[{__name__}] 模板或种子文件未选择')
        gr.Warning("模板或种子文件未选择")
        return gr.update()
    response = api_read(user_name, 'generation', template_name, 'type', 'template')
    if not response_checker(response): return ''
    template_content = response['data']

    response = api_read(user_name, 'generation', seed_name, 'type', 'seed')
    if not response_checker(response): return ''
    seed_content = response['data']

    query = generate_query(user_name, seed_content, template_content, (FSG_min, FSG_max), FSG_typ, FSG_template_map, FSG_sep_map, FSG_prompt_map, FSG_response_map)
    return query
# 模板预览----batch
def gr_generate_ba_query(user_name, template_name, seed_name, BA_template_map, BA_prompt_map):
    '''
    功能简介：生成batch-generation的query预览。
    '''
    if not seed_name or not template_name:
        api_logs_write(user_name, f'[{__name__}] 模板或种子文件未选择')
        gr.Warning("模板或种子文件未选择")
        return None
    if not BA_template_map or not BA_prompt_map:
        api_logs_write(user_name, f'[{__name__}] 模板字段或种子字段未选择')
        gr.Warning("模板字段或种子字段未选择")
        return None

    response = api_read(user_name, 'generation', template_name, 'type', 'template')
    if not response_checker(response): return None
    template_content = response['data']
    # 默认只读取2000条
    response = api_read(user_name, 'generation', seed_name, 'type', 'seed')
    if not response_checker(response): return None

    seed_content = response['data']
    samples_str = [seed_content[0][x] for x in BA_prompt_map]
    query = replace_sample_str(template_content[BA_template_map], samples_str)
    # query = template_content[BA_template_map].format(samples_str=seed_content[0][BA_prompt_map])
    return query

# 模板预览 ------- 检测模板拼接是否正常
def check_template_glue(user_name, generate_config):
    query = None
    if generate_config['generate_method'] == 'FewShotGenerator':
        query = gr_generate_query(user_name, generate_config['seed_name'], generate_config['template_name'], generate_config['extra']['FSG']['FSG_min'], generate_config['extra']['FSG']['FSG_max'], generate_config['extra']['FSG']['FSG_typ'], generate_config['extra']['FSG']['FSG_template_map'], generate_config['extra']['FSG']['FSG_sep_map'], generate_config['extra']['FSG']['FSG_prompt_map'], generate_config['extra']['FSG']['FSG_response_map'])

    elif generate_config['generate_method'] == 'BatchGenerator':
        query = gr_generate_ba_query(user_name, generate_config['template_name'], generate_config['seed_name'], generate_config['extra']['BA']['BA_template_map'], generate_config['extra']['BA']['BA_prompt_map'])
    else:
        gr.Warning('[ 失败 ] 请选择生成方法！')
        api_logs_write(user_name, f'[{__name__}] [ 失败 ] 请选择生成方法！')
        return False
    if query == None: 
        gr.Warning('[ 失败 ] 配置错误')
        api_logs_write(user_name, f'[{__name__}] [失败] 配置错误')
        return False
    return True

# ------------- LLM 配置空间增删改查 ----------------
# 查：配置列表
def find_list_models_config(user_name):
    response = api_get_userspace(user_name, 'models_config')
    if not response_checker(response): models_config_list=[]
    else: models_config_list = response['data']
    return gr.update(choices=list(reversed(models_config_list)), value=None)

# 查：查具体的配置
def find_item_models_config(user_name, config_name):
    if not config_name:
        gr.Warning("请选择LLM配置")
        return [gr.update()]*9
    response = api_get_userspace_item(user_name, 'models_config', config_name)
    if not response_checker(response): return [gr.update()]*9
    else: models_config = response['data']
    gr.Info(f"配置[{config_name}]更新成功")

    return gr.update(value=models_config['api_type']), gr.update(value=models_config['api_base']), gr.update(value=models_config['api_key']), gr.update(value=models_config['deployment_name']), gr.update(value=models_config['thread_num']), gr.update(value=models_config['sleep_time']), gr.update(value=models_config['temperature']), gr.update(value=models_config['top_p']), gr.update(value=config_name)

# 增
def save_models_config(component_data):
    namedModelConfig = manager.get_current_conf(component_data)
    if not namedModelConfig['models_config_name']: 
        gr.Warning('请输入API配置的存储名')
        return gr.update()
    # 在MongoDB查询中"."符号有特殊作用
    elif '.' in namedModelConfig['models_config_name']: 
        gr.Warning('存储名中不能存在“.”')
        return gr.update()
    user_name = component_data[manager.get_elem_by_name('top.user_name')]
    result = api_additem_userspace(user_name, 'models_config', namedModelConfig)

    gr.Info(f"配置[{namedModelConfig['models_config_name']}存储成功]")
    return gr.update()

# 删
def delete_models_config(user_name, config_name):
    if not config_name:
        gr.Warning('请选择LLM配置')
        return gr.update()
    result = api_deleteitem_userspace(user_name, 'models_config', config_name)
    gr.Info(f"配置[{config_name}]删除成功")
    return gr.update()

def list_files(dir_path: Optional[str] = None, file_type=['json', 'jsonl', 'txt']) -> Dict[str, Any]:
    try:
        file_list = [file_name for file_name in os.listdir(dir_path) if file_name.endswith(tuple(file_type))]
    except:
        file_list = []
    return gr.update(value=[], choices=file_list)

def upload_file(user_name):
    if isinstance(user_name, str) and user_name != '':
        return gr.update(interactive=True)
    return gr.update(interactive=False)
def clear_file():
    return gr.update(interactive=False)

def refresh(user_name, typ, fieldname, filedvalue):
    options = api_refresh_field(user_name, typ, fieldname, filedvalue)
    return gr.update(choices=options)

def store_data(file, user_name, tab, typ):
    '''
    存储模板和种子文件
    tab:指界面上的tab，不同tab理论上存储域不同；
    typ:指存储doc的type字段的值；
    '''
    api_logs_write(user_name, f'开始上传【{file.name}】数据。')
    yield gr.update(interactive=False)
    if file.name.rpartition('.')[-1] in ['jsonl', 'json']:
        api_store(user_name, tab, file)
        filename = os.path.basename(file.name)
        api_store_filed(user_name, tab, filename, 'type', typ)
        api_logs_write(user_name, f'数据【{file.name}】上传成功!')
        yield gr.update(interactive=True)
    else:
        api_logs_write(user_name, '请上传【json】或【jsonl】类型的文件')
        yield gr.update(interactive=False)

def read_data(user_name, tab, file_name, filedname, filedvalue, pages=1):
    '''
    功能简介：读取生成数据并显示。支持分页读取。
    '''
    if file_name in ['', None, []]:
        gr.Warning('请选择数据集！')
        api_logs_write(user_name, f'[{__name__}] 请选择数据集！')
        return gr.update()

    response = api_read_page(user_name, tab, file_name, pages, filedname, filedvalue, limit=PAGE_LIMIT)

    if response['code'] != 200:
        gr.Warning(response['message'])
        api_logs_write(user_name, f'[{__name__}] 生成数据【{file_name}】读取失败!\n{response["message"]}')
        return gr.update()
    if response['data'] == []:
        gr.Warning(f'数据集【{file_name}】没有数据')
        api_logs_write(user_name, f'[{__name__}] 生成数据【{file_name}】读取失败!\n没有数据')
        return gr.update()
    try:
        df = pd.DataFrame(response['data'], columns=['prompt', 'response']).reset_index()
    except:
        df = pd.DataFrame(response['data'], columns=['text']).reset_index()
    api_logs_write(user_name, f'[{__name__}] 生成数据【{file_name}】读取成功!')
    return gr.update(value=df, visible=True)

def show_meta(user_name, tab, dataset_name, filedname, filedvalue):
    if not dataset_name:
        gr.Warning('请先选择数据集！')
        return gr.update()
    response = api_get_meta_std(user_name, tab, dataset_name, filedname, filedvalue)
    if response['code'] != 200:
        gr.Warning(f"元信息数据请求失败。\ncode:{response['code']}: {response['message']}")
    return gr.update(value=response['data'], visible=True)

def clouseshow(num):
    return [gr.update(visible=False)]*num

def get_generation_config(user_name):
    deprecated_info('get_generation_config', 'Not implement', '24-5-15')
    url = URL + f'generate/get_config/?user_name={user_name}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {'err_code': -2, 'err_content': f'请求用户{user_name}配置信息失败！'}

def template_input_save(user_name, template_input, template_sep, template_save_name, template_input_overwrite=False):
    '''
    功能简介：模板存储功能实现
    '''
    template_save_name = template_save_name.strip()
    if template_input.strip() == '' or template_save_name.strip() == '':
        gr.Warning(f'请输入模板和模板存储名！')
        api_logs_write(user_name, f'[{__name__}] 请输入模板和模板存储名！')
        return 
        
    check_result = api_check_repeat(user_name, "generation", template_save_name)
    if not response_checker(check_result):
        api_logs_write(user_name, f"重复文件检查API请求失败。\ncode:{check_result['code']}: {check_result['message']}")
        return 
    name_checked = check_result['data']
    if name_checked and not template_input_overwrite:
        gr.Warning(f"文件【{template_save_name}】已存在，请更改输出文件名称重新保存")
        api_logs_write(user_name, f"文件【{template_save_name}】已存在，请更改输出文件名称重新保存")
        return 
    
    check_result = api_check_repeat(user_name, "generation", template_save_name, 'type', 'template')
    if not response_checker(check_result):
        api_logs_write(user_name, f"重复文件检查API请求失败。\ncode:{check_result['code']}: {check_result['message']}")
        return 
    typ_checked = check_result['data']
    if template_input_overwrite and name_checked and not typ_checked:
        gr.Warning(f"文件【{template_save_name}】在其他类型数据存在重复，无法覆盖，请重新命名文件")
        api_logs_write(user_name, f"文件【{template_save_name}】在其他类型数据存在重复，无法覆盖，请重新命名文件")
        return 

    template = {'text': template_input, 'sep': template_sep}
    api_write(user_name, 'generation', template_save_name, template)
    api_store_filed(user_name, 'generation', template_save_name, 'type', 'template')
    gr.Info(f'用户{user_name}存储模板{template_save_name}成功！')
    api_logs_write(user_name, f"[{__name__}] 用户{user_name}存储模板{template_save_name}成功！")


def fsg_typ_select(fsg_typ):
    if fsg_typ == 'prompt-response':
        return gr.update(visible=True), gr.update(visible=True)
    elif fsg_typ == 'prompt-only':
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)

def fsg_PR_flush(user_name, seed_name, filename, filevalue):
    '''
    功能简介：刷新生成时，额外参数的种子字段的值。包括fewshot和batch。
    '''
    response = api_read(user_name, 'generation', seed_name, filename, filevalue)
    if not response_checker(response): return [gr.update()]*3
    # from ipdb import set_trace
    # set_trace()
    seed_content = response['data']
    if len(seed_content) > 0:
        return gr.update(choices=list(seed_content[0].keys()), value=None), gr.update(choices=list(seed_content[0].keys()), value=None), gr.update(choices=list(seed_content[0].keys()), value=[])

    gr.Warning('种子文件内容为空！请检查种子文件。')
    api_logs_write(user_name, f'[{__name__}] 种子文件内容为空！请检查种子文件。')
    return [gr.update()]*3

def fsg_Temp_flush(user_name, template_name, filename, filevalue):
    '''
    功能简介：获取fewshot中模板的可映射列名列表。
    '''
    response = api_read(user_name, 'generation', template_name, filename, filevalue)
    if not response_checker(response): return [gr.update()]*3

    template_content = response['data']
    return [gr.update(choices=list(template_content.keys() if template_content else []), value=None)]*3

# ---数据管理---
# def generation_get_filed_list(user_name, tab, filedname, filedvalue):
#     content_list = api_get_filed_list(user_name, tab, filedname, filedvalue)
#     if isinstance(content_list, dict) and content_list.get('err_code', 0) != 0:
#         api_logs_write(user_name, f'[{__name__}] '+content_list['err_content'])
#         return gr.update()
#     return gr.update(choices=content_list, value=None)

def generation_get_filed_list(user_name, tab, filedname, filedvalue, origin_file=None):
    content_list = api_get_filed_list(user_name, tab, filedname, filedvalue)
    if isinstance(content_list, dict) and content_list.get('err_code', 0) != 0:
        api_logs_write(user_name, f'[{__name__}] '+content_list['err_content'])
        return gr.update()
    if origin_file:
        if origin_file in content_list:
            return gr.update(choices=content_list)
        else:
            return gr.update(choices=content_list, value=None)
    return gr.update(choices=content_list, value=None)

# 删除
def delete_data(user_name, tab, file_name, filedname, filedvalue, sub_type=''):

    if file_name in ['', [], None]:
        gr.Warning('【删除失败】没有选择数据名')
        api_logs_write(user_name, f'[{__name__}] 【删除失败】没有选择数据名')
        return 

    sub_type = filedvalue if filedvalue else ''
    response = api_delete(user_name, tab, file_name, filedname, filedvalue, sub_type)
    if "err_code" not in response:
        gr.Info(f'【删除成功】{file_name}数据集已删除')
        api_logs_write(user_name, f'[{__name__}] 【删除成功】{file_name}数据集已删除')
        return 
    gr.Info(f'【删除失败】{file_name} 响应错误{response["err_code"]}')
    api_logs_write(user_name, f'[{__name__}]【删除失败】{file_name} 响应错误{response["err_code"]}')

# 加载temlate
def loda_template(user_name, tab, file_name, filedname=None, filedvalue=None):
    if not file_name:
        gr.Warning('请选择模板名')
        # api_logs_write(user_name, f'[{__name__}] 请选择模板名')
        return [gr.update()]*2
    response = api_read_page(user_name, tab, file_name, page=1, filedname=None, filedvalue=None, limit=PAGE_LIMIT)
    if not response_checker(response): return 0, [], gr.update()
    data = response['data']
    template = data['text']
    sep = data['sep']
    return template, sep, file_name