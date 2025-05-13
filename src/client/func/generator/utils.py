import random, requests, time
import gradio as gr
from apiweb import api_logs_write, api_check_repeat
from conf.userconf import URL
from typing import List 

def replace_sample_str(goal_str, samples_str: List[str]):
    '''
    功能简介：将prompt与template进行结合
    更新：支持多列拼接prompt。update 2024-6-11
    '''
    # goal_str = re.sub(r'\{samples_str\}', sample_str, goal_str)
    for idx, sample_str in enumerate(samples_str):
        goal_str = goal_str.replace("{sample_str" + str(idx) + "}", sample_str)
    return goal_str


def generate_query(user_name, seed_samples, template, sample_nums:tuple, typ, FSG_template_map, FSG_sep_map, FSG_prompt_map, FSG_response_map):
    '''
    功能简介：对few-shot进行硬编码方式拼接。
    模板和样本进行拼接
    这里太过于硬编码了
    '''
    try:
        if sample_nums[0] > len(seed_samples) or sample_nums[0] > len(seed_samples):
            gr.Warning('样本【采样异常】！请确保采样参数在样本数量范围内')
            api_logs_write(user_name, f'[{__name__}] 样本【采样异常】！请确保采样参数在样本数量范围内')
            return
        # 1.随机采样
        n = random.randint(sample_nums[0], sample_nums[1])
        samples_tmp = random.sample(seed_samples, n)
    except:
        gr.Warning('样本【采样异常】！请检查采样参数和种子文件')
        api_logs_write(user_name, f'[{__name__}] 样本【采样异常】！请检查采样参数和种子文件')
        return 
    try:
        if FSG_sep_map in ['', [], None]:
            gr.Warning('请选择sep字段')
            api_logs_write(user_name, f'[{__name__}] 请选择sep字段')
            return  

        sep = f'\n{template[FSG_sep_map]}\n'
        if typ == 'prompt-response':
            if not FSG_prompt_map or not FSG_response_map:
                gr.Warning('请选择prompt和response字段')
                api_logs_write(user_name, f'[{__name__}] 请选择prompt和response字段')
                return
            samples_str = sep+sep.join([f"Prompt:\n{s[FSG_prompt_map]}\nResponse:\n{s[FSG_response_map]}" for s in samples_tmp])+sep
        elif typ == 'prompt-only':
            if not FSG_prompt_map:
                gr.Warning('请选择prompt字段')
                api_logs_write(user_name, f'[{__name__}] 请选择promp字段')
                return
            samples_str = sep+sep.join([f"Prompt:\n{s[FSG_prompt_map]}" for s in samples_tmp])+sep
        elif typ == 'response-only':
            if not FSG_response_map:
                gr.Warning('请选择response字段')
                api_logs_write(user_name, f'[{__name__}] 请选择response字段')
                return
            samples_str = sep+sep.join([f"Response:\n{s[FSG_response_map]}" for s in samples_tmp])+sep
        
        if not FSG_template_map:
            gr.Warning('请选择template字段')
            api_logs_write(user_name, f'[{__name__}] 请选择template字段')
            return
        # from ipdb import set_trace
        # set_trace()
        # query = template[FSG_template_map].format(samples_str=samples_str)
        query = replace_sample_str(template[FSG_template_map], [samples_str])
    except:
        api_logs_write(user_name, '样本【拼接异常】！请检查模板和种子样本格式符合要求')
        return
    return query

def gen_config_checker(user_name, generate_overwrite, generate_config):
    '''
    功能简介：检查生成参数的正确性
    '''
    if generate_config['generate_filename'] in ['', None, []]:
        gr.Warning("[ 失败 ] 请确认输出文件名不为空！")
        api_logs_write(user_name, f'[{__name__}] [ 失败 ] 请确认输出文件名不为空！')
        return False
    
    # 添加数据库中是否已有数据名称文档的判断
    check_result = api_check_repeat(user_name, "generation", generate_config['generate_filename'])
    if check_result['code'] != 200:
        gr.Warning(f"重复文件检查API请求失败。\ncode:{check_result['code']}: {check_result['message']}")
        api_logs_write(user_name, f"重复文件检查API请求失败。\ncode:{check_result['code']}: {check_result['message']}")
        return False
    
    name_checked = check_result['data']
    if name_checked and not generate_overwrite:
        gr.Warning(f"文件【{generate_config['generate_filename']}】已存在，请更改输出文件名称重新开始生成")
        api_logs_write(user_name, f"文件【{generate_config['generate_filename']}】已存在，请更改输出文件名称重新开始生成")
        return False
    
    check_result = api_check_repeat(user_name, "generation", generate_config['generate_filename'], 'type', 'generated_data')
    if check_result['code'] != 200:
        gr.Warning(f"重复文件检查API请求失败。\ncode:{check_result['code']}: {check_result['message']}")
        api_logs_write(user_name, f"重复文件检查API请求失败。\ncode:{check_result['code']}: {check_result['message']}")
        return False
    
    type_checked = check_result['data']
    if name_checked and generate_overwrite and not type_checked:
        gr.Warning(f"文件【{generate_config['generate_filename']}】在其他类型数据存在重复，无法覆盖，请重新命名文件")
        api_logs_write(user_name, f"文件【{generate_config['generate_filename']}】在其他类型数据存在重复，无法覆盖，请重新命名文件")
        return False

    return True

def get_gen_status(user_name):
    url_progress = URL + f"standard-api/monitor/progress/?user_name={user_name}&func_typ=generation"

    response = requests.get(url_progress).json()['data']
    gen_status = response['generation_status']['status']
    filename = response['generation_status'].get('generate_filename', 'None')
    generation_status = response['generation_status']
    return gen_status, filename, generation_status


def watchdogs(user_name):
    '''
    功能简介：看门狗程序，用于查看后端任务进程是否还活着。如果任务进程状态为'running'并且20s内有心跳。则表示任务进程活着。心跳用process表示。
    返回值：
        False：不存在任务进程。
        True：存在任务进程。
    '''
    gen_status, _, generation_status = get_gen_status(user_name)
    if gen_status != "running" and gen_status != 'abort': return False

    cache_process, remain_time = generation_status['heart'], 10
    while gen_status == "running" and remain_time > 0:
        time.sleep(1)
        gen_status, _, generation_status = get_gen_status(user_name)
        if cache_process != generation_status['heart'] and gen_status == "running": return True
        remain_time -= 1
    return False

# def timed_request(timeout, interval, call_back, call_back_args):
#     '''
#     功能简述：定期间隔请求
#     '''
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         try:
#             call_back(*call_back_args)
#             return True
#         except:
#             time.sleep(interval)
#     return False
def get_task_meta(task):
    task_meta = dict(用户名=task['name'])
    # from ipdb import set_trace
    # set_trace()
    if 'generation_status' in task and task['generation_status'] and 'status' in task['generation_status']:
        task_meta['任务状态'] = task['generation_status']['status']
    else:
        task_meta['任务状态'] = None

    if 'generation_status' in task and task['generation_status'] and 'process' in task['generation_status'] and 'total' in task['generation_status']:
        task_meta['进度'] = (task['generation_status']['process'])/(task['generation_status']['total'])
    else:
        task_meta['进度'] = None

    if 'generation_status' in task and task['generation_status'] and 'template_name' in task['generation_status']:
        task_meta['模板'] = task['generation_status']['template_name']
    else:
        task_meta['模板'] = None

    if 'generation_status' in task and task['generation_status'] and 'seed_name' in task['generation_status']:
        task_meta['种子'] = task['generation_status']['seed_name']
    else:
        task_meta['种子'] = None

    if 'generation_status' in task and task['generation_status'] and 'generate_filename' in task['generation_status']:
        task_meta['生成文件'] = task['generation_status']['generate_filename']
    else:
        task_meta['生成文件'] = None

    if 'generation_status' in task and task['generation_status'] and 'heart' in task['generation_status']:
        hours = task['generation_status']['heart']//3600
        minites = task['generation_status']['heart']%3600//60
        seconds = task['generation_status']['heart']%60

        task_meta['消耗时间'] = f'{hours} h {minites} min {seconds} s'
    else:
        task_meta['消耗时间'] = None

    if 'generation_status' in task and task['generation_status'] and 'err_code' in task['generation_status']:
        task_meta['错误码'] = task['generation_status']['err_code']
    else:
        task_meta['错误码'] = None
    return task_meta