import random, copy, sys, json, re, os, logging
import pandas as pd
from dataclasses import dataclass, field
from typing import Literal, Optional

# from transformers import HfArgumentParser

from .strategy import *
from .utils import *
from .dbOperation import db_userspace_filedvalue

def check_params(gen_args, gendboperator):
    # from ipdb import set_trace
    # set_trace()
    # 1. 未选择生成方法
    if not gen_args.generate_method:
        gendboperator.db_logs_write(f'[{__name__}] 参数错误 {Generator.err_map["-9"]}')
        gendboperator.db_status_set('err_code', Generator.err_map["-9"])
        return Generator.err_map["-9"]
    # 2. 模板未设置
    elif not gen_args.template_name:
        gendboperator.db_logs_write(f'[{__name__}] 参数错误 {Generator.err_map["-8"]}')
        gendboperator.db_status_set('err_code', Generator.err_map["-8"])
        return Generator.err_map["-8"]
    # 3. 种子文件未设置
    elif not gen_args.template_name:
        gendboperator.db_logs_write(f'[{__name__}] 参数错误 {Generator.err_map["-8"]}')
        gendboperator.db_status_set('err_code', Generator.err_map["-1"])
        return Generator.err_map["-1"]
    return True

def run_datagen(args_user, background_tasks):
    """
    功能简介：数据生成函数。
    """
    # import ipdb; ipdb.set_trace()
    # 1. 准备数据和组件
    # 用户名和生成参数
    user_name, gen_args = args_user.user_name, args_user.generation
    # 模型配置
    models_config_item = db_userspace_filedvalue(user_name, 'models_config', gen_args.models_config_list)
    # 模型API
    client = load_openai_client(models_config_item)
    # 数据库
    gendboperator = GenDBOperator(user_name, gen_args.template_name, gen_args.seed_name, gen_args.generate_filename)

    # 2. 任务开启前准备
    # 参数检查与错误记录
    check_res = check_params(gen_args, gendboperator)
    if check_res != True:
        return {'code': 421, 'data':'', 'message':check_res}

    # 2. 开启任务
    if gen_args.generate_method == 'FewShotGenerator':
        generator = FewShotGenerator(user_name, gen_args, models_config_item, gendboperator, client)
        gen_status = generator.fewshot_gen_samples_multithread(gen_args.generate_number, gen_args.generate_fault_tolerance, models_config_item['thread_num'], models_config_item['sleep_time'], gen_args.extra.FSG, background_tasks)

    elif gen_args.generate_method == 'BatchGenerator':
        generator = BatchGenerator(user_name, gen_args, models_config_item, gendboperator, client)
        gen_status = generator.batch_gen_samples_multithread(gen_args.generate_number, gen_args.generate_fault_tolerance, models_config_item['thread_num'], models_config_item['sleep_time'], gen_args.extra.BA, background_tasks)

    return gen_status

if __name__=='__main__':
    config_args ={                 
        'user_name': 'pxh',
        'generate_method': 'FewShotGenerator',
        'template_name': 'generate_templates.json',
        'seed_name': 'generate_seed.jsonl',
        'api_type': 'azure', 
        'api_base': 'https://api.deepseek.com/v1',
        'api_key': 'xxx',
        'deployment_name': 'deepseek-chat',
        'temperature':0.8,
        'top_p':0.7,
        'generate_number': 10,
        'generate_filename':'tmp.txt',
    }
    run_datagen(config_args)