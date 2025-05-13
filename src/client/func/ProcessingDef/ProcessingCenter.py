from .utils import *
import gradio as gr
from apiweb import api_get_meta_std, api_get_meta_std,api_get_filed_list, api_delete,api_get_list, api_logs_write, api_read_page, api_check_repeat, api_read, api_write
from common import get_droplist_check, response_checker
from pprint import pprint
import tempfile, os, json, requests
# 功能组件显示控制
def show_mode(mode_name):
    if mode_name == '多列合并':
        return [gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*15
    elif mode_name == '长度统计':
        return [gr.update(visible=False,open=False)]*1+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*14
    elif mode_name == '分类统计(数量)':
        return [gr.update(visible=False,open=False)]*2+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*13
    elif mode_name == '多行混合':
        return [gr.update(visible=False,open=False)]*3+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*12
    elif mode_name == '条件删除':
        return[gr.update(visible=False,open=False)]*4+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*11
    elif mode_name == '条件删除-Bool':
        return [gr.update(visible=False,open=False)]*5+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*10
    elif mode_name == '分割数据为多列':
        return [gr.update(visible=False,open=False)]*6+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*9
    elif mode_name == '数据拆分':
        return [gr.update(visible=False,open=False)]*7+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*8
    elif mode_name == '数据去重':
        return [gr.update(visible=False,open=False)]*8+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*7
    elif mode_name == '指定字符替换':
        return [gr.update(visible=False,open=False)]*9+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*6
    elif mode_name == '字段抽取':
        return [gr.update(visible=False,open=False)]*10+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*5
    elif mode_name == '数据抽取':
        return [gr.update(visible=False,open=False)]*11+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*4
    elif mode_name == '概率插入字符':
        return [gr.update(visible=False,open=False)]*12+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*3
    elif mode_name == '交叉合并':
        return [gr.update(visible=False,open=False)]*13+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*2
    elif mode_name == '数据替换':
        return [gr.update(visible=False,open=False)]*14+[gr.update(visible=True,open=True)]+[gr.update(visible=False,open=False)]*1
    elif mode_name == '概率替换字符':
        return [gr.update(visible=False,open=False)]*15+[gr.update(visible=True,open=True)]
    return [gr.update(visible=False,open=False)]*16
# 数据删除
def delete_data(user_name, tab, file_name, filedname=None, filedvalue=None, sub_type=''):
    if file_name in ['', [], None]:
        gr.Warning('【删除失败】没有选择数据名')
        api_logs_write(user_name, f'[{__name__}] 【删除失败】没有选择数据名')
        return 
    if tab != 'processing':
        gr.Warning(f'【删除失败】{file_name} 不是processing数据集,如需删除其他数据集，请前往其他页面')
        return
    sub_type = filedvalue if filedvalue else ''
    response = api_delete(user_name, tab, file_name, filedname, filedvalue, sub_type)
    if "err_code" not in response:
        gr.Info(f'【删除成功】{file_name}数据集已删除')
        api_logs_write(user_name, f'[{__name__}] 【删除成功】{file_name}数据集已删除')
        return 
    gr.Info(f'【删除失败】{file_name} 响应错误{response["err_code"]}')
    api_logs_write(user_name, f'[{__name__}]【删除失败】{file_name} 响应错误{response["err_code"]}')

# 数据列表更新
def get_droplist_check(user_name, typ, dataset_name, fieldname=None, filedvalue=None):
    if not typ:
        gr.Info("请先选择数据源！")
        return gr.update()
    if user_name != '':
        if typ == "dataset_info"  or typ == 'processing':
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


# 控制数据列选择
def show_col(user_name,processing_source,processing_collection_name,*args):
    res = api_get_meta_std(user_name, processing_source, processing_collection_name)
    if res['code'] == 200:
        if 'columns' not in res['data']:
            return [gr.update(choices=['text'],value='text')]*len(args)
        elif res['data']['columns'] == []:
            return [gr.update(choices=['text'],value='text')]*len(args)
        else:
            columns = res['data']['columns']
            if len(columns) >= 1:
                return [gr.update(choices=columns,value=columns[0])]*len(args)
            else:
                return [gr.update(choices=columns,value=columns[0])]*len(args)
    # df = pd.read_excel(file)
    # df_col = df.columns.tolist()
    # updated_dropdown = gr.Dropdown(choices=df_col)
    # return [updated_dropdown]*len(args)
    return [gr.update(choices=[],value=None)]*len(args)
# 元数据展示
def show_meta(user_name, typ, dataset_name):
    if not check_input(typ, dataset_name):
        return gr.update(), gr.update()
    res = api_get_meta_std(user_name, typ, dataset_name)
    if res['code'] == 200:
        return gr.update(value=res['data'], visible=True), gr.update(visible=True, open=True)
    return [gr.update()] * 2
# 数据展示
def show_dataset(user_name, typ, dataset_name):
    if not check_input(typ, dataset_name): return [gr.update()] * 2
    if typ == 'generation':
        response = api_read(user_name, typ, dataset_name, 'type', 'generated_data')
    else:
        response = api_read(user_name, typ, dataset_name)
    if not response_checker(response): return [gr.update()] * 2

    df = get_response_content(response, typ)
    if df is not None:
        return gr.update(value=df, visible=True), gr.update(visible=True, open=True)
    gr.Warning("数据集为空")
    return [gr.update()] * 2

def get_page_content_tab(user_name, tab, filename, page, filedname=None, filedvalue=None):
    if tab == 'dataset_info':
        res = api_read_page(user_name, tab, filename, page, filedname, filedvalue)
    else:
        res = api_read_page(user_name, tab, filename, page, 'type', 'generated_data')
    if res['code'] == 200:
        # 对于生成数据和上传数据格式有所不同
        if len(res['data']) > 0 and isinstance(res['data'][0], dict):
            df = pd.DataFrame(res['data']).reset_index()
        else:
            df = pd.DataFrame(res['data'], columns=['text']).reset_index()

        return gr.update(value=df)
    gr.Warning(f'[ Code ] {res["code"]}:{res["message"]}')
    return gr.update()
# 数据下载
def processing_download_file(user_name, processing_source,processing_collection_name,download_type):
    if processing_collection_name in [None, '', []] or processing_source in [None, '', []]:
        gr.Warning('数据集未选择')
        api_logs_write(user_name, f"[{__name__}] [失败] 数据集未选择！")
        return gr.update()
    gr.Info("请求数据")
    response = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if response['code'] != 200:
        gr.Warning(response['message'])
        return gr.update()
    response = response['data']
    if response == []:
        gr.Warning(f'数据集【{__name__}】没有数据')
        return gr.update(visible=False)
    df = pd.DataFrame(response)
    temp = tempfile.NamedTemporaryFile(suffix='.'+download_type, delete=False)
    if download_type == 'csv':
        df.to_csv(temp, encoding='utf_8_sig', index=False)
    elif download_type == 'xlsx':
        df.to_excel(temp, index=False, engine='xlsxwriter')
    # 这个有问题 
    elif download_type == 'json':
        df.to_json(temp, orient='records', force_ascii=False, indent=4)
    else:
        df.to_json(temp, orient='records', lines=True, force_ascii=False)
    gr.Info(f"数据集{processing_collection_name}准备完成。")
    return gr.update(value=temp.name, visible=True)

# 数据写入
def processing_write(user_name,process_name,data,processing_overwrite):
    result_dict = data.to_dict(orient='records')
    # 判断文件是否存在
    repeat = api_check_repeat(user_name, 'processing', process_name)
    # print(repeat)
    if not response_checker(repeat):
        gr.Warning(f'重复文件检查API请求失败。\ncode:{repeat["code"]}: {repeat["message"]}')
        api_logs_write(user_name, f"重复文件检查API请求失败。\ncode:{repeat['code']}: {repeat['message']}")
        return gr.update(value = None,visible=True,interactive=False)
    name_checked = repeat['data']
    # print(repeat['data'],'processing_overwrite',processing_overwrite)
    if name_checked and not processing_overwrite:
        gr.Warning(f'文件【{process_name}】已存在，请选择覆盖或修改文件名')
        api_logs_write(user_name, f"文件【{process_name}】已存在，请选择覆盖或修改文件名")
        return gr.update(value = None,visible=True,interactive=False)
    if processing_overwrite or (not processing_overwrite and not name_checked):
        # 数据写入
        response = api_write(user_name,'processing',process_name,result_dict)
        if response['code'] == 200:
            gr.Info('数据写入成功')
            return gr.update(value = data.head(200),visible=True,interactive=False)
        # 写入失败
        # pprint(result_dict)
        gr.Warning(f'数据写入失败：[ Code ] {response["code"]}:{response["message"]}')
        api_logs_write(user_name, f"数据写入失败。\ncode:{response['code']}: {response['message']}")
        return gr.update(value = None,visible=True,interactive=False)
    return gr.update()
# 数据格式处理，字段处理
def contorl_field_andcolumnsdatas(user_name,processing_source,
                processing_collection_name,acd_data_col, acd_and_str,
                acd_result_type,acd_new_col,out_df,process_name,processing_overwrite):
    if not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not acd_result_type:
        gr.Warning('请选择结果类型')
        return gr.update()
    elif not acd_data_col or len(acd_data_col) < 2:
        gr.Warning('请选择列名')
        return gr.update()
    elif acd_result_type=='str' and not acd_and_str:
        gr.Warning('请选择分隔符')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    # 请求数据
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    # print(res)
    # print(len(res['data']))
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = and_columns_datas(df,and_str=acd_and_str,data_columns=acd_data_col,result_type=acd_result_type,new_column=acd_new_col)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_longcondatas(user_name,processing_source,
                processing_collection_name,lcd_longcondata_type,lcd_data_col, 
                lcd_lengthrange_min, lcd_lengthrange_max,
                out_df,process_name,processing_overwrite):
    if not lcd_data_col and (not lcd_lengthrange_min or not lcd_lengthrange_max):
        gr.Warning('请选择列名和长度范围')
        return gr.update()
    elif not lcd_data_col or (lcd_lengthrange_min == 'NULL' or not lcd_lengthrange_max):
        gr.Warning('请选择长度范围' if lcd_data_col else '请选择列名')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    elif not lcd_longcondata_type:
        gr.Warning('请选择数据统计类型')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        if lcd_longcondata_type == '超长统计':
            result = long_con_out(datas=df,columns_name=lcd_data_col,length_range=[lcd_lengthrange_min,lcd_lengthrange_max])
        elif lcd_longcondata_type == '长度统计':
            result = long_con_in(datas=df,columns_name=lcd_data_col,length_range=[lcd_lengthrange_min,lcd_lengthrange_max])
        else:
            gr.Warning('请选择正确数据统计类型')
            return gr.update()
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_categoriescondata(user_name,processing_source,
                processing_collection_name,ccd_data_col,ccd_data_count,process_name,processing_overwrite):
    if not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not ccd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif ccd_data_count < 0:
        gr.Warning('请选择筛选数量')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = Categories_Con(datas=df,data_columns=ccd_data_col,data_count=ccd_data_count)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)
    
def contorl_field_allcolmix(user_name,processing_source,
                processing_collection_name,ac_data_col, 
                ac_nums, ac_str_mix, ac_eve_num, 
                ac_pre_suffix, ac_and_mode,out_df,process_name,processing_overwrite):
    if not ac_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not ac_nums:
        gr.Warning('请选择合并后行数')
        return gr.update()
    elif not ac_and_mode:
        gr.Warning('请选择合并模式')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    elif not ac_str_mix or not isinstance(eval(ac_str_mix),dict):
        gr.Warning('请选择字符分隔字典')
        return gr.update()
    elif not ac_eve_num or not isinstance(eval(ac_eve_num),dict):
        gr.Warning('请选择合并数量字典')
        return gr.update()
    elif ac_pre_suffix and (not isinstance(eval(ac_pre_suffix),list) or len(ac_pre_suffix) != 2):
        gr.Warning('请选择前后缀列表')
        return gr.update()
    ac_and_mode = 0 if ac_and_mode == '不放回合并' else 1
    ac_pre_suffix = eval(ac_pre_suffix)
    ac_str_mix = eval(ac_str_mix)
    ac_eve_num = eval(ac_eve_num)
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = all_colmix(datas=df,columns_name=ac_data_col,nums=ac_nums,str_mix=ac_str_mix,eve_num=ac_eve_num,pre_suffix=ac_pre_suffix,and_mode=ac_and_mode)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_conditiondel(user_name,processing_source,
                processing_collection_name,cddd_data_col,cddd_conditionstr,out_df,process_name,processing_overwrite):
    if not cddd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not cddd_conditionstr or not isinstance(eval(cddd_conditionstr),list):
        gr.Warning('请填写正确删除条件')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    cddd_conditionstr = eval(cddd_conditionstr)
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = condition_del(datas=df,condition_str=cddd_conditionstr,data_columns=cddd_data_col)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_conditiondelbooldatas(user_name,processing_source,
                processing_collection_name,cddbd_data_col, cddbd_condition_str,cddbd_min_length,cddbd_max_length,cddbd_comditionsdeltype,ouput_df,process_name,processing_overwrite):
    if not cddbd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not cddbd_comditionsdeltype:
        gr.Warning('请选择删除条件类型')
        return gr.update()
    elif cddbd_comditionsdeltype == 'LongDel' and (not cddbd_min_length or not cddbd_max_length or cddbd_min_length >= cddbd_max_length or cddbd_min_length < 0):
        gr.Warning('请选择长度范围')
        return gr.update()
    elif cddbd_comditionsdeltype == 'StrDel' and (not cddbd_condition_str or isinstance(eval(cddbd_condition_str),list)):
        gr.Warning('请填写删除条件')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        if cddbd_comditionsdeltype == 'LongDel':
            result = condition_del_bool(datas=df,condition_str=[cddbd_min_length,cddbd_max_length],data_columns=cddbd_data_col,ConditionsDelType=cddbd_comditionsdeltype)
        elif cddbd_comditionsdeltype == 'StrDel':
            result = condition_del_bool(datas=df,condition_str=eval(cddbd_condition_str),data_columns=cddbd_data_col,ConditionsDelType=cddbd_comditionsdeltype)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_cutcolumnsonedelmanydatas(user_name,processing_source,
                processing_collection_name,cctmd_col, cctmd_cut_str, cctmd_cut_num,ouput_df,process_name,processing_overwrite):
    if not cctmd_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not cctmd_cut_str:
        gr.Warning('请填写切割字符串')
        return gr.update()
    elif not cctmd_cut_num or cctmd_cut_num < 2:
        gr.Warning('请填写切割后列数,至少2列')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = cut_columns_to(df,columns=cctmd_col,cut_str=cctmd_cut_str,cut_num=cctmd_cut_num)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_cutcolumnsonedatas(user_name,processing_source,
                processing_collection_name,ccsd_data_col, ccsd_cut_str, ccsd_cut_suffix_first, ccsd_cut_suffix_end, ccsd_hold_splitter,ouput_df,process_name,processing_overwrite):
    if not ccsd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not ccsd_cut_str:
        gr.Warning('请填写切割字符')
        return gr.update()
    elif not ccsd_hold_splitter:
        gr.Warning('请填写是否保留切割字符')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    ccsd_hold_splitter = 0 if ccsd_hold_splitter == '否' else 1
    ccsd_cut_suffix_first = '' if not ccsd_cut_suffix_first else ccsd_cut_suffix_first
    ccsd_cut_suffix_end = '' if not ccsd_cut_suffix_end else ccsd_cut_suffix_end
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = cut_columns_one(datas=df,data_col=ccsd_data_col,cut_str=ccsd_cut_str,cut_suffix=[ccsd_cut_suffix_first,ccsd_cut_suffix_end],hold_splitter=ccsd_hold_splitter)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_deletionconditionsdatas(user_name,processing_source,
                processing_collection_name,dcd_data_col,ouput_df,process_name,processing_overwrite):
    if not dcd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = Deletion_Conditions(datas=df,data_columns=dcd_data_col)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_redelstrdatas(user_name,processing_source,
                processing_collection_name,rdsd_data_col, rdsd_restr, rdsd_repstr,ouput_df,process_name,processing_overwrite):
    if not rdsd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not rdsd_restr:
        gr.Warning('请填写删除字符')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = re_del_str(datas=df,data_columns=rdsd_data_col,restr=rdsd_restr,repstr=rdsd_repstr)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_extractfieldsdatas(user_name,processing_source,
                processing_collection_name,efd_data_col, efd_fieldslist,efd_patterns_mode,output_df,process_name,processing_overwrite):
    if not efd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not efd_fieldslist or not isinstance(eval(efd_fieldslist), list):
        gr.Warning('请填写抽取字段')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    elif not efd_patterns_mode:
        gr.Warning('请选择抽取模式')
        return gr.update()
    efd_fieldslist = eval(efd_fieldslist) if efd_patterns_mode == '正常抽取' else efd_fieldslist
    efd_patterns_mode = 'normal' if efd_patterns_mode == '正常抽取' else 're'
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = Excerpt_Fields(datas=df,excerpt_columns=efd_data_col,fieldslist=efd_fieldslist,patterns_mode=efd_patterns_mode)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_extractdatas(user_name,processing_source,
                processing_collection_name,ed_data_col, ed_extract_mode, ed_re_data, ed_num, ed_index_start, ed_index_end, output_df,process_name,processing_overwrite):
    if not ed_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    elif not ed_extract_mode:
        gr.Warning('请选择抽取模式')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        if ed_extract_mode == '随机抽取':
            if not ed_num:
                gr.Warning('请填写抽取数量')
                return gr.update()
            elif ed_num < 0:
                gr.Warning('请填写正确抽取数量')
                return gr.update()
            result=extract_data(datas=df,extract_mode='Randomly',num=ed_num)
        elif ed_extract_mode == '正则抽取':
            if not ed_re_data:
                gr.Warning('请填写正则表达式')
                return gr.update()
            result=extract_data(datas=df,data_columns=ed_data_col,extract_mode='ReExtraction',re_data=ed_re_data,num=ed_num)
        elif ed_extract_mode == '索引抽取':
            if (not ed_index_end or not ed_index_start) and ed_index_start != 0 and ed_index_end != 0:
                gr.Warning('请填写索引')
                return gr.update()
            elif ed_index_start < 0 or ed_index_end <= ed_index_start:
                gr.Warning('请填写正确索引')
                return gr.update()
            result=extract_data(datas=df,extract_mode='IndexExtraction',IndexNum=[ed_index_start, ed_index_end])
        else:
            gr.Warning('请选择正确的抽取模式')
            return gr.update()
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

    
def contorl_field_insertion_location_str(user_name,processing_source,
                processing_collection_name,ilsd_data_col, ilsd_strdict, ilsd_frequencydict, ilsd_insert_mode, ilsd_str_location, ilsd_maxsub, output_df,process_name,processing_overwrite):
    if not ilsd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not ilsd_strdict or not isinstance(eval(ilsd_strdict), dict):
        gr.Warning('请填写插入字符概率字典')
        return gr.update()
    elif not ilsd_frequencydict or not isinstance(eval(ilsd_frequencydict), dict):
        gr.Warning('请填写插入字符次数概率字典')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    elif not ilsd_insert_mode:
        gr.Warning('请选择插入模式')
        return gr.update()
    elif ilsd_insert_mode == '指定位置插入' and (not ilsd_str_location or ilsd_maxsub < 1):
        gr.Warning('请填写插入位置')
        return gr.update()
    # ilsd_str_location = 0 if ilsd_insert_mode == '随机插入' else ilsd_str_location
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = Insertion_location_str(datas=df,data_columns=ilsd_data_col,strdict=eval(ilsd_strdict),frequencydict=eval(ilsd_frequencydict),str_location=ilsd_str_location,maxsub=ilsd_maxsub)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)
    
def contorl_field_overlapping_and(user_name,processing_source,
                processing_collection_name,oaad_data1,oaad_data2,ouput_df,process_name,processing_overwrite):
    if not oaad_data1 or not oaad_data2:
        gr.Warning('请选择列名')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        lst1 = [i for i in df[oaad_data1]]
        lst2 = [i for i in df[oaad_data2]]
        result = overlapping_and(lst1=lst1, lst2=lst2)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

    
def contorl_field_replace_data(user_name,processing_source,
                processing_collection_name,rdd_data_col,rdd_replace_data,rdd_replace_to,output_df,process_name,processing_overwrite):
    if not rdd_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not rdd_replace_data or not rdd_replace_to:
        gr.Warning('请填写替换字符')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = replace_data(df=df,column_name=rdd_data_col,replace_data=rdd_replace_data,replace_to=rdd_replace_to)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)

def contorl_field_replace_list_probability(user_name,processing_source,
                processing_collection_name,rsp_data_col, rsp_strdict, rsp_rep_probability,rsp_rep_str, output_df,process_name,processing_overwrite):
    if not rsp_data_col:
        gr.Warning('请选择列名')
        return gr.update()
    elif not rsp_strdict or not isinstance(eval(rsp_strdict),dict):
        gr.Warning('请填写替换字符概率字典')
        return gr.update()
    elif not processing_source or not processing_collection_name:
        gr.Warning('请选择文件')
        return gr.update()
    elif not process_name or process_name.strip() == '':
        gr.Warning('请填写文件保存名称')
        return gr.update()
    res = api_read(user_name, processing_source, processing_collection_name,limit=0)
    if res['code'] == 200:
        df = pd.DataFrame(res['data'])
        gr.Info('正在处理数据，请稍后')
        result = replace_list_probability(datas=df,data_columns=rsp_data_col,strdict=eval(rsp_strdict),rep_probability=rsp_rep_probability,rep_str=rsp_rep_str)
        gr.Info('数据处理完成,正在写入数据')
        return processing_write(user_name,process_name,result,processing_overwrite)
    gr.Warning(f'数据请求失败：[ Code ] {res["code"]}:{res["message"]}')
    api_logs_write(user_name, f"数据请求失败。\ncode:{res['code']}: {res['message']}")
    return gr.update(value = None,visible=True,interactive=False)