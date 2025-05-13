import tempfile, os, json, requests
import gradio as gr
import pandas as pd
from conf.userconf import URL, PAGE_LIMIT, GENERATION_SEED_LIMIT
from apiweb import api_logs_read, api_logs_write, api_write, api_store_filed, api_read, api_get_list, api_get_meta_std, api_get_filed_list, api_read_page, api_check_repeat, api_delete
import xlsxwriter

# 进度条组件更新
# 状态空间需要固定4具有四个字段：total, process, abort, status
def update_process_bar(slide_status, visible=True):
    '''
    功能简介：进度条格式化显示组件。
    进度显示：process / total
    状态显示：status/abort
    时间显示：heart
    '''
    if not slide_status['total']:
        return gr.update(visible=False)

    percentage = round(100 * slide_status['process'] / slide_status['total'], 0) if slide_status['total'] != 0 else 100.0
    if slide_status['abort']: status = 'abort'
    else: status = slide_status['status']
    cost = slide_status['heart']
    label = "Running {:d}/{:d} status:{} time: {:d}h {:d}min {:d}s".format(
        slide_status['process'],
        slide_status['total'],
        status,
        cost // 3600,
        (cost % 3600) // 60,
        cost % 60
    )
    return gr.update(label=label, value=percentage, visible=visible)

def data_download(content, save_type):
    '''
    上传数据到文件组件，等待用户下载
    '''
    df = pd.DataFrame(content)
    temp = tempfile.NamedTemporaryFile(suffix='.'+save_type, delete=False)
    if save_type == 'csv':
        # df.to_csv(temp)
        df.to_csv(temp, encoding="utf_8_sig", index=False)
    elif save_type == 'xlsx':
        df.to_excel(temp, index=False)
    # 这个有问题 
    elif save_type == 'json':
        df.to_json(temp, orient='records', force_ascii=False)
    else:
        df.to_json(temp, orient='records', lines=True, force_ascii=False)
    return temp.name

# 读取日志并展示
def get_logs(user_name):
    logs = '【 INFO 】 请先【登录】！'
    if user_name != '':
        response = api_logs_read(user_name)
        if response['code'] != 200:
            gr.Warning(f"文件上传请求失败。\ncode:[{response['code']}\nmessage:[{response['message']}]")
            return gr.update()
        logs = response['data']
    return gr.update(value=logs)

def get_logs_continue(user_name):
    logs = '【 INFO 】 请先【登录】！'
    if user_name != '':
        response = api_logs_read(user_name)
        if response['code'] != 200:
            gr.Warning(f"文件上传请求失败。\ncode:[{response['code']}\nmessage:[{response['message']}]")
            return gr.update()
        logs = response['data']
    return gr.update(value=logs)


## 4 文件管理组件
def is_valid_typepath(s):
    parts = s.split("-")
    # 判断是否每个部分的字符串长度不大于10
    if all(len(part) <= 5 for part in parts):
        return True
    else:
        return False

# 4.1 多格式文件上传
def submit_file(user_name, file, tab, typ=None, overwrite=False, type_path=""):
    """
    功能简介：用户从前端界面上传文件后，通过该功能将数据集存储到数据库中。
    user_name，tab: 共同组成用户数据存储空间。
    file: 前端File组件存储的文件路径
    typ: 它可以定义不同的形式存储数据。例如template。通过该参数可以实现同一个接口实现不同的数据类型存储
    type_path: 可以设置数据集的type_path域的值，用来表示数据集的存储逻辑路径
    """
    file_name = os.path.basename(file.name)
    # 1. 公共数据集使用部分代码
    if typ == "common_dataset" and not type_path:
        gr.Warning("请填写数据集存储的逻辑路径")
        return gr.update(interactive=True)
    if type_path and not is_valid_typepath(type_path):
        gr.Warning("数据逻辑路径格式不正确，请保证每个路径字符小于5")
        return gr.update(interactive=True)

    # 2. 检查是否覆盖
    check_result = api_check_repeat(user_name, tab, file_name)
    if not response_checker(check_result): return gr.update(interactive=True)
    res_name = check_result["data"]

    if not overwrite and res_name:
        gr.Warning(f"文件【{file_name}】已存在，请确认覆盖原文件或更改文件名称重新上传")
        api_logs_write(user_name, f"文件【{file_name}】已存在，请确认覆盖原文件或更改文件名称重新上传")
        return gr.update(interactive=True)

    elif overwrite and res_name:
        if tab == 'dataset_info':
            api_delete(user_name, tab, file_name)
        elif tab == 'generation':
            check_result = api_check_repeat(user_name, tab, file_name, 'type', typ)
            if not response_checker(check_result): return gr.update(interactive=True)
            res_type = check_result['data']
            if not res_type: 
                gr.Warning(f"文件【{file_name}】在其他类型数据存在重复，无法覆盖，请重新命名文件")
                api_logs_write(user_name, f"文件【{file_name}】在其他类型数据存在重复，无法覆盖，请重新命名文件")
                return gr.update(interactive=True)
            api_delete(user_name, tab, file_name, 'type', typ, typ)
        gr.Warning(f"同名文件【{file_name}】已删除，请等待上传")
        api_logs_write(user_name, f"同名文件【{file_name}】已删除，请等待上传")

    # 2. 文件类型转换:转换为dataframe
    # 1. 文件类型转换提示
    gr.Info(f"文件【{file_name}】开始转换，请耐心等待!")
    api_logs_write(user_name, f"文件【{file_name}】开始转换，请耐心等待")

    if file_name.endswith('.xlsx'):
        df = pd.read_excel(file.name, date_format='iso', dtype=str)
        # df = pd.read_excel(file.name, date_format='iso')
    elif file_name.endswith('.csv'):
        df = pd.read_csv(file.name, dtype=str)
        # df = pd.read_csv(file.name)
    elif file_name.endswith('.json'):
        try:
            with open(file.name, encoding='utf-8') as f:
                data = json.load(f)
        except:
            gr.Warning('json文件存在问题，请注意区分json与jsonl！')
            api_logs_write(user_name, f"[ Warning ] json文件存在问题，请注意区分json与jsonl！")
            return gr.update(interactive=True)
            
        # 如果你的JSON文件是一个字典列表：
        if isinstance(data, list):
            df = pd.DataFrame(data)
        # 如果你的JSON文件是一个嵌套字典：
        elif isinstance(data, dict):
            df = pd.json_normalize(data)
        else:
            # pass
            df = pd.DataFrame().fillna('')
            # df = pd.DataFrame().fillna('None')
    elif file_name.endswith('.jsonl'):
        df = pd.read_json(file.name, lines=True, dtype=str)
    else:
        gr.Warning('上传文件只支持：json, jsonl, xlsx, csv格式！')
        api_logs_write(user_name, f"[ Warning ] 上传文件只支持：json, jsonl, xlsx, csv格式！")
        return gr.update(interactive=True)

    if typ=='seed' and len(df) > GENERATION_SEED_LIMIT:
        gr.Warning(f'种子文件数据量最多接收：{GENERATION_SEED_LIMIT}!')
        api_logs_write(user_name, f'[ 失败 ] 种子文件数据量最多接收：{GENERATION_SEED_LIMIT}!')
        return gr.update(interactive=True)

    # 3. 上传到数据库
    api_logs_write(user_name, f"文件【{file_name}】转换完成\n开始上传数据")
    gr.Info(f'文件【{file_name}】转换完成\n开始上传数据')

    # df = df.fillna('None')
    df = df.fillna('') # 取消空值填补
    # 4. 统一将dataframe转换为json
    # 消除数据中可能存在的时间戳数据结构
    content = json.loads(df.to_json(orient="records"))

    if typ == 'template' and len(content) != 1:
        gr.Warning('模板文件错误，模板只能有一行数据！')
        api_logs_write(user_name, f"模板【{file_name}】文件错误，它只能有一行数据！")
        return gr.update(interactive=True)

    if typ:
        api_store_filed(user_name, tab, file_name, 'type', typ)
        if typ == 'template':
            response = api_write(user_name, tab, file_name, content[0], typ)
        else:
            if typ == 'common_dataset':
                api_store_filed(user_name, tab, file_name, 'type_path', type_path)
            response = api_write(user_name, tab, file_name, content, typ)

    else:
        response = api_write(user_name, tab, file_name, content)
    # 4. 转换结束提示
    if response['code'] == 200:
        gr.Info(f"文件【{file_name}】上传成功")
        api_logs_write(user_name, f"文件【{file_name}】上传成功")
    else:
        gr.Warning(f"文件上传请求失败。\ncode:[{response['code']}\nmessage:[{response['message']}]")
        api_logs_write(user_name, f"文件上传请求失败。\ncode:[{response['code']}\nmessage:[{response['message']}]")
    return gr.update(interactive=True)

# 4.2 多格式文件下载
def download_file(user_name, tab, dataset_name, filedname=None, filedvalue=None, save_type='csv', limit=0):
    if dataset_name in [None, '', []]:
        gr.Warning('数据集未选择')
        api_logs_write(user_name, f"[{__name__}] [失败] 数据集未选择！")
        return gr.update()
    gr.Info("请求数据")
    response = api_read(user_name, tab, dataset_name, filedname, filedvalue, limit)
    if response['code'] != 200:
        gr.Warning(response['message'])
        return gr.update()
    response = response['data']
    if response == []:
        gr.Warning(f'数据集【{__name__}】没有数据')
        return gr.update(visible=False)
    if filedname == 'type' and filedvalue == 'template':
        df = pd.DataFrame(response, index=[0])
    else:
        df = pd.DataFrame(response)
    temp = tempfile.NamedTemporaryFile(suffix='.'+save_type, delete=False)
    # df.replace('', None)
    if save_type == 'csv':
        df.to_csv(temp, encoding='utf_8_sig', index=False)
    elif save_type == 'xlsx':
        # df.replace('', None)
        df.to_excel(temp, index=False, engine='xlsxwriter')
    # 这个有问题 
    elif save_type == 'json':
        df.to_json(temp, orient='records', force_ascii=False, indent=4)
    else:
        df.to_json(temp, orient='records', lines=True, force_ascii=False)
    gr.Info(f"数据集{dataset_name}准备完成。")
    return gr.update(value=temp.name, visible=True)

## 4.4 分页显示
def show_pages(user_name, tab, filename, limit=PAGE_LIMIT):
    if not filename: 
        return gr.update()
    res = api_get_meta_std(user_name, tab, filename)
    if not response_checker(res): return gr.update()

    total_nums = res['data'].get('total_nums', 1)
    value_max = total_nums // limit
    if total_nums % limit: value_max += 1
    if value_max <= 1: return gr.update(visible=False)
    return gr.update(visible=True, value=1, minimum=1, maximum=value_max)

# 获取指定页数的内容
def get_page_content(user_name, tab, filename, page, filedname=None, filedvalue=None):
    '''
    功能简介：获取指定页数的数据内容，并将其返回到DataFrame窗口。支持List[str]和List[dict]两种数据形式的显示。
    更新：1.添加生成数据的大数据读取。(v24.6.6)
    '''
    res = api_read_page(user_name, tab, filename, page, filedname, filedvalue)
  
    if not response_checker(res): return gr.update()
    # 对于生成数据和上传数据格式有所不同
    if len(res['data']) > 0 and isinstance(res['data'][0], dict):
        df = pd.DataFrame(res['data']).reset_index()
    else:
        df = pd.DataFrame(res['data'], columns=['text']).reset_index()

    return gr.update(value=df)
    

# 4.5 关闭展示窗口
def close_show(nums):
    if nums == 1:
        return gr.update(visible=False)
    return [gr.update(visible=False)]*nums

def get_droplist_typ(user_name, typ):
    if user_name != '':
        choices = api_get_list(user_name, typ)
        api_logs_write(user_name, f"[ 数据集列表更新 ][{__name__}] {user_name} 数据集列表更新【成功】！")
        return gr.update(choices=choices)

    api_logs_write(user_name, f"[ 数据集列表更新 ][{__name__}] {user_name} 数据集列表更新【失败】！")
    return gr.update(choices=[])

def get_droplist_check(user_name, typ, dataset_name, fieldname=None, filedvalue=None):
    if not typ:
        gr.Info("请先选择数据源！")
        return gr.update()
    if user_name != '':
        if typ == "dataset_info" or typ == "processing":
            choices = api_get_list(user_name, typ)
        else:
            choices = api_get_filed_list(user_name, typ, fieldname, filedvalue)
        api_logs_write(user_name, f"[ 数据集列表更新 ][{__name__}] {user_name} 数据集列表更新【成功】！")
        if len(choices) > 0:
            if dataset_name in choices:
                return gr.update(choices=choices)
            else:
                return gr.update(choices=choices, value=None)
        else:
            return gr.update(choices=[])
        
    api_logs_write(user_name, f"[ 数据集列表更新 ][{__name__}] {user_name} 数据集列表更新【失败】！")
    return gr.update(choices=[])

# 请求校验
def response_checker(response):
    if response["code"] != 200:
        gr.Warning(f"code:[{response['code']}]\nmessage:[{response['message']}]")
        return False
    return True