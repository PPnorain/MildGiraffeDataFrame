import random, threading, multiprocessing, time#, re, json
import regex as re
from typing import List
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from tqdm import tqdm
from .utils import get_gpt4_response, clean_patterns, heart_beat
from dataclasses import dataclass
from dependencies import GEN_STORE_THREASHOLD
from .dbOperation import GenDBOperator

@dataclass
class GenerateStatus:
    err_code = ""

def clean(response):
    ques = response.split('\n\n')
    # 去掉序号：如1.
    ques = [re.sub(r'\d+\.\s+', '', i) for i in ques]
    ques = [re.sub(r'\d+\.', '', i) for i in ques]
    # 
    ques = [i.replace('\\', '') for i in ques]
    ques = [i.strip('\n') for i in ques]
    # 去掉过短问题
    ques = [i for i in ques if len(i) > 5]
    return ques

def get_template(response, sep='\n\n'):
    ques = response.split(sep)
    return ques

def replace_sample_str(goal_str, samples_str: List[str]):
    '''
    功能简介：将prompt与template进行结合
    更新：支持多列拼接prompt。update 2024-6-11
    '''
    # goal_str = re.sub(r'\{samples_str\}', sample_str, goal_str)
    for idx, sample_str in enumerate(samples_str):
        goal_str = goal_str.replace("{sample_str" + str(idx) + "}", sample_str)
    return goal_str

class Generator:
    err_map = {
                "-1":"缺少种子文件；", 
                "-2":'模板字段不匹配字段；', 
                "-3":"样本【采样异常】！请检查采样参数和种子文件；", 
                "-4":"样本【拼接异常】！请检查模板和种子样本格式符合要求；", 
                "-6":"模板处理异常；", 
                "-7":"API请求异常，请检查API配置；", 
                "-8":"缺少模板文件；" ,
                "-9":"未选择生成方法；",
                "-10":"后处理异常，请检查分隔符以及分割情况；",
            }
    def __init__(self, user_name, gen_args, models_config_item, gendboperator, client):
        self.gendboperator = gendboperator
        self.template = self.gendboperator.db_get_template()
        self.seed_samples = self.gendboperator.db_get_seed()
        self.client = client
        self.chat_config = {'model':models_config_item['deployment_name'], 'temperature':models_config_item['temperature'], 'top_p':models_config_item['top_p']}
        # add lmr
        self.status = GenerateStatus()
        self.stop_heartbeat_event = threading.Event()  # 创建停止心跳的事件

    def heart_beat(self, interval, dbobj):
        heart = 0
        while not self.stop_heartbeat_event.is_set():  # 如果 self.stop_heartbeat_event.set() 被调用，循环将终止
            dbobj.db_add_heart(heart)
            time.sleep(interval)
            heart += 1
        # self.gendboperator.db_logs_write('心跳线程已停止')


class FewShotGenerator(Generator):

    def __preprocess__(self, num_samples, template, extra_FSG):
        queries = []
        for i in tqdm(range(num_samples), desc='[ 问题预处理 ]'):
            try:
                n = random.randint(extra_FSG.FSG_min, extra_FSG.FSG_max)
                samples_tmp = random.sample(self.seed_samples, n)
            except:
                self.gendboperator.db_logs_write('样本【采样异常】！请检查采样参数和种子文件')
                return []
            try:
                sep = f'\{self.template[extra_FSG.FSG_sep_map]}\n'
                if extra_FSG.FSG_typ == 'prompt-response':
                    samples_str = sep + sep.join([f"Prompt:\n{s[extra_FSG.FSG_prompt_map]}\nResponse:{s[extra_FSG.FSG_response_map]}" for s in samples_tmp]) + sep
                elif extra_FSG.FSG_typ == 'prompt-only':
                    samples_str = sep + sep.join([f"Prompt:\n{s[extra_FSG.FSG_prompt_map]}" for s in samples_tmp]) + sep
                elif extra_FSG.FSG_typ == 'response-only':
                    samples_str = sep + sep.join([f"Response:\n{s[extra_FSG.FSG_response_map]}" for s in samples_tmp])+ sep

                query = replace_sample_str(template, [samples_str])
                queries.append(query)
            except:
                self.gendboperator.db_logs_write('样本【拼接异常】！请检查模板和种子样本格式符合要求')
                self.status.err_code += self.err_map['-4']
                return []
        return queries

    def __postprocess__(self, response, extra, is_large, idx):
        try:
            if response == '[API异常]':
                ques = ['[API异常]']
            else:
                ques = response
                # ques = get_template(response, extra.FSG_sep_map)
        except:
            self.gendboperator.db_logs_write('后处理异常，请检查分隔符以及分割情况；')
            self.status.err_code += self.err_map['-10']
            return 
        self.gendboperator.db_append_sample({'prompt':str(idx), 'response':ques}, 'type', 'generated_data', is_large, idx)
        # self.gendboperator.db_append_sample({'prompt':str(idx), 'response':ques[0]}, 'type', 'generated_data', is_large, idx)

    def fewshot_gen_samples_multithread(self, num_samples, generate_fault_tolerance, thread_num, sleep_time, extra_FSG, background_tasks):
        self.gendboperator.db_logs_write(f'[{__name__}]启动【FewShotGenerator】开始生成')

        try:
            template = self.template[extra_FSG.FSG_template_map]
        except:
            self.gendboperator.db_logs_write(f'[ Warning ] 模板不存在{extra_FSG.FSG_template_map}字段')
            self.status.err_code += self.err_map['-2']
            return []
        self.gendboperator.db_status_set('total', num_samples)

        is_large = num_samples > GEN_STORE_THREASHOLD
        self.gendboperator.db_set_generated(is_large)
        # 1. 前处理
        queries = self.__preprocess__(num_samples, template, extra_FSG)
        # 2. 大模型并发响应
        self.gendboperator.db_status_set('status', 'running')

        error_container = generate_fault_tolerance
        heart_thread = threading.Thread(target=self.heart_beat, args=(1, self.gendboperator))
        heart_thread.daemon = True
        heart_thread.start()
        # 后台任务
        background_tasks.add_task(self.process_task, thread_num, sleep_time, queries, error_container, extra_FSG, is_large)
        # 多进程
        # process = multiprocessing.Process(target=self.process_task, args=(thread_num, sleep_time, queries, error_container, extra_FSG, is_large))
        # process.start()
        # 不返回
        # try:
        #     with ThreadPoolExecutor(max_workers=thread_num) as executor:
        #         chat_api_request_partial = partial(get_gpt4_response, client=self.client, chat_config=self.chat_config, sleep_time=sleep_time)
        #         for idx, response in enumerate(executor.map(chat_api_request_partial, [query for query in queries])):
        #             if isinstance(response, dict):
        #                 error_container -= 1
        #                 response = '[API异常]'
        #                 if error_container < 0:
        #                     raise Exception("API异常")
        #             self.__postprocess__(response, extra_FSG, is_large, idx)
        #             if self.status.err_code != '':
        #                 executor.shutdown(wait=False)
        #                 break
        #             self.gendboperator.db_status_set('process', idx+1)
        #             if self.gendboperator.db_status_get('abort'):  
        #                 self.gendboperator.db_logs_write('中断生成')
        #                 executor.shutdown(wait=False)
        #                 break
        # except:
        #     self.gendboperator.db_logs_write(f'[ Error ] API请求异常，请检查API配置；')
        #     self.status.err_code += self.err_map['-7']
        # self.gendboperator.db_set_meta('type', 'generated_data')
        # self.gendboperator.db_status_set('status', 'finish')
        # self.gendboperator.db_status_set('err_code', self.status.err_code)
        # # 查看错误状态
        # self.gendboperator.db_logs_write(f'[{__name__}]结束【FewShotGenerator】')
        # self.gendboperator.db_status_set('err_code', self.status.err_code)
        return {'code':200, 'data':'', 'message':'生成任务开启成功'}

    def process_task(self, thread_num, sleep_time, queries, error_container, extra_FSG, is_large):
        try:
            with ThreadPoolExecutor(max_workers=thread_num) as executor:
                chat_api_request_partial = partial(get_gpt4_response, client=self.client, chat_config=self.chat_config, sleep_time=sleep_time)
                for idx, response in enumerate(executor.map(chat_api_request_partial, [query for query in queries])):
                    if isinstance(response, dict):
                        error_container -= 1
                        response = '[API异常]'
                        if error_container < 0:
                            raise Exception("API异常")
                    self.__postprocess__(response, extra_FSG, is_large, idx)
                    if self.status.err_code != '':
                        executor.shutdown(wait=False)
                        break
                    self.gendboperator.db_status_set('process', idx+1)
                    if self.gendboperator.db_status_get('abort'):  
                        self.gendboperator.db_status_set('status', 'abort')
                        self.stop_heartbeat_event.set()
                        executor.shutdown(wait=False)
                        self.gendboperator.db_logs_write('中断生成')
                        break
        except:
            self.gendboperator.db_logs_write(f'[ Error ] API请求异常，请检查API配置；')
            self.status.err_code += self.err_map['-7']
        finally:
            self.stop_heartbeat_event.set()
        self.gendboperator.db_set_meta('type', 'generated_data')
        self.gendboperator.db_status_set('status', 'finish')
        self.gendboperator.db_status_set('err_code', self.status.err_code)
        # 查看错误状态
        self.gendboperator.db_logs_write(f'[{__name__}]结束【FewShotGenerator】')
        self.gendboperator.db_status_set('err_code', self.status.err_code)

    # def batch_pool(self, thread_num, sleep_time, queries, error_container, extra_FSG, is_large):
    #     process = multiprocessing.Process(target=self.process_task, args=(thread_num, sleep_time, queries, error_container, extra_FSG, is_large))
    #     process.start()


class BatchGenerator(Generator):
    def __preprocess__(self, template, extra_BA, seed_len):
        queries = []
        for i in range(seed_len):
            try:
                seed_samples = [self.seed_samples[i][x] for x in extra_BA.BA_prompt_map]
                query = replace_sample_str(template, seed_samples)

            except Exception as e:
                print(str(e))
                self.gendboperator.db_logs_write('模板处理异常')
                self.status.err_code += self.err_map['-6']
                return 
            queries.append(query)
        return queries

    def batch_gen_samples_multithread(self, num_samples, generate_fault_tolerance, thread_num, sleep_time, extra_BA, background_tasks):
        self.gendboperator.db_logs_write(f'[{__name__}]启动【BatchGenerator】开始生成')
        # import ipdb; ipdb.set_trace()
        try:
            template = self.template[extra_BA.BA_template_map]
        except:
            self.gendboperator.db_logs_write(f'[ Warning ] [{__name__}]模板缺少{extra_BA.BA_template_map}字段')
            return {'code': 421, 'data':'', 'message':f'模板缺少{extra_BA.BA_template_map}字段'}

        seed_len = min(len(self.seed_samples), num_samples)
        self.gendboperator.db_status_set('total', seed_len)

        is_large = seed_len > GEN_STORE_THREASHOLD
        self.gendboperator.db_set_generated(is_large)
        # 1. 前处理
        queries = self.__preprocess__(template, extra_BA, seed_len)
        self.gendboperator.db_status_set('status', 'running')

        error_container = generate_fault_tolerance
        heart_thread = threading.Thread(target=self.heart_beat, args=(1, self.gendboperator))
        heart_thread.daemon = True
        heart_thread.start()
    
        background_tasks.add_task(self.batch_pool, thread_num, sleep_time, queries, error_container, extra_BA, is_large)
        return {'code':200, 'data':'', 'message':'生成任务开启成功'}

    def batch_pool(self, thread_num, sleep_time, queries, error_container, extra_BA, is_large):
        # 2. 大模型并发响应
        try:
            with ThreadPoolExecutor(max_workers=thread_num) as executor:
                chat_api_request_partial = partial(get_gpt4_response, client=self.client, chat_config=self.chat_config, sleep_time=sleep_time)
                for idx, response in enumerate(executor.map(chat_api_request_partial, [query for query in queries])):
                    if isinstance(response, dict):
                        error_container -= 1
                        response = '[API异常]'
                        if error_container < 0:
                            raise Exception("API异常")
                    self.gendboperator.db_append_sample({'prompt':[self.seed_samples[idx][x] for x in extra_BA.BA_prompt_map], 'response':response}, 'type', 'generated_data', is_large, idx=idx)
                    
                    self.gendboperator.db_status_set('process', idx+1)
                    if self.gendboperator.db_status_get('abort'):  
                        self.gendboperator.db_status_set('status', 'abort')
                        self.stop_heartbeat_event.set() # 触发 Event 对象(用于触发心跳线程的停止。)
                        executor.shutdown(wait=False)
                        self.gendboperator.db_logs_write('中断生成')
                        break    

        except Exception as e:
            self.gendboperator.db_logs_write(f'[ Error ] API请求异常，请检查API配置；{e}')
            self.status.err_code += self.err_map['-7']
        finally:
            self.stop_heartbeat_event.set()
        self.gendboperator.db_set_meta('type', 'generated_data')
        self.gendboperator.db_status_set('status', 'finish')
        self.gendboperator.db_status_set('err_code', self.status.err_code)
        self.gendboperator.db_logs_write(f'[{__name__}]结束【BatchGenerator】')
        self.gendboperator.db_status_set('err_code', self.status.err_code)
            # 查看错误状态

        # if self.gendboperator.db_status_get('err_code') != '':
        #     self.gendboperator.db_status_set('status', 'aborted')
        #     self.gendboperator.db_status_set('abort', 1)

        # return self.gendboperator.db_status_get('err_code')