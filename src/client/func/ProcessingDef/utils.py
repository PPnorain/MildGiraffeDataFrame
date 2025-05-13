import random
import pandas as pd
import numpy as np
import re
import gradio as gr


# 检查数据源和数据集
def check_input(typ, dataset_name):
    """
    功能简介：检查是否选择数据源和数据集。
    """
    if not typ:
        gr.Warning('请先选择数据源！')
        return False
    elif not dataset_name:
        gr.Warning('请先选择数据集！')
        return False
    return True

def get_response_content(response, typ):
    if response['code'] == 200:
        content = response['data']
        if content == []:
            return None
        df = pd.DataFrame(content)
        if isinstance(df.columns, pd.RangeIndex) and len(df.columns) == 1:
            df = pd.DataFrame(content, columns=['text']).reset_index()
        else:
            df = df.reset_index()
        return df
    gr.Warning(f"{response['code']}:{response['messages']}")
    return None


'''
    混合用法
    多行混合，抽取行，按照概率取分隔符，进行混合
        模式：1、放回；2、不放回
'''
def all_colmix(datas,columns_name, nums: int, 
            str_mix: dict, eve_num: dict, 
            pre_suffix:list=[], and_mode:int = 0):
    '''
    datas:传入要合并的数据
    columns_name:传入要合并的列名
    nums:合并后数据行数
    str_mix:分隔符字典，分隔符：概率
    eve_num:给定合并条目，条数：概率
    pre_suffix:合并后前后符号
    and_mode:两种模式，0：不放回合并，1：放回合并
    '''
    result = []
    datas = datas[columns_name]
    # 放回合并
    if and_mode:
        # 合并nums条
        for _ in range(0,nums):
            # 按照概率生成字符和条数
            strmix = random.choices(list(str_mix.keys()),weights=list(str_mix.values()))[0]
            evenum = random.choices(list(eve_num.keys()),weights=list(eve_num.values()))[0]
            
            # 生成合并索引
            try:
                random_numbers = random.sample(range(0,len(datas)), int(evenum))
            except:
                random_numbers = list(datas.index)
            and_str = f'{strmix}'.join([str(i) for i in datas.loc[random_numbers]])
            
            if len(pre_suffix) == 1:
                result.append(and_str + pre_suffix)
            elif len(pre_suffix) == 2:
                result.append(pre_suffix[0]+and_str+pre_suffix[1])
            else:
                result.append(and_str)
        return pd.DataFrame(result,columns=[str(columns_name)])

    # 不放回合并
    for _ in range(0,nums):
        # 如果datas中数据已经全部合并，则返回合并结果
        if len(datas) == 0:
            return pd.DataFrame(result,columns=[str(columns_name)])
            
        # 按照概率生成字符和条数
        strmix = random.choices(list(str_mix.keys()),weights=list(str_mix.values()))[0]
        evenum = random.choices(list(eve_num.keys()),weights=list(eve_num.values()))[0]
        
        # 生成合并索引,如果要取的行数大于实际行数，则取出所有行
        try:
            random_numbers = random.sample(range(0,len(datas)), int(evenum))
        except:
            random_numbers = list(datas.index)
        and_str = f'{strmix}'.join([str(i) for i in datas.loc[random_numbers]])
        
        # 根据传入前后符号的长度进行拼接
        if len(pre_suffix) == 1:
                result.append(and_str + pre_suffix)
        elif len(pre_suffix) == 2:
            result.append(pre_suffix[0]+and_str+pre_suffix[1])
        else:
            result.append(and_str)
        # result.append(f'{strmix}'.join([datas.iloc[x,0] for x in random_numbers]))
        
        # 删除已经合并过的行，并重置索引
        datas = datas.drop(random_numbers).reset_index(drop=True)
    return pd.DataFrame(result,columns=[str(columns_name)])

'''
    多列合并
    将指定的列按照指定分割符进行合并，输出列
'''
def and_columns_merging(data,data_columns,and_str,result_type):
    if result_type == 'str':
        return f'{and_str}'.join([str(data[i]) for i in data_columns])
    elif result_type == 'list':
        return [str(data[i]) for i in data_columns]
    elif result_type == 'tuple':
        return tuple([str(data[i]) for i in data_columns])
    # result = [str(i) + ':' + str(data[i]) for i in data_columns]
    raise Exception('result_type error')
def and_columns_datas(datas,and_str='',data_columns=[],result_type:str = 'str',new_column:str='output')->pd.DataFrame:
    '''
    datas:要合并的数据表
    and_str:合并分隔符
    data_columns:需要合并的列，默认合并全部列,list
    result_type:合并后的类型，str,list,tuple
    new_column:合并后列名
    '''
    # result = pd.DataFrame()
    if data_columns == []:
        data_columns = datas.columns

    data_columns = data_columns
    datas[new_column] = datas.apply(lambda x:and_columns_merging(x,data_columns,and_str,result_type), axis=1)
    return datas


'''
分类统计(数量)
'''

def Categories_Con(datas,data_columns:list,data_count:int)->pd.DataFrame:
    '''
    datas:传入数据(pandas.DataFrame)
    data_columns:列名(list(str))
    '''
    group_data = datas.groupby(data_columns)[data_columns].size().reset_index(name = 'count')
    group_data = group_data[group_data['count'] > data_count]
    return group_data


'''
    条件删除：
        把含有某字段的数据清空,然后删除其所在行
        返回DataFrame
'''
def condition_del(datas,condition_str:list,data_columns=['All']) -> pd.DataFrame:
    """
    根据条件删除数据中的行

    Args:
        datas (pd.DataFrame): 传入数据
        condition_str (list): 要删除包含的字符串列表(可以使用正则)
        data_columns (list, optional): 要删除的列，默认全部. Defaults to ['All'].

    Returns:
        pd.DataFrame: 处理后的DataFrame
    """
    if data_columns[0] == 'All':
        data_columns = datas.columns

    # 复制数据，避免直接修改原始DataFrame
    result = datas.copy().astype(str)
    condition_str = [str(i) for i in condition_str]
    for col in data_columns:
        result[col] = result[col].apply(lambda x: np.nan if any(re.search(re.compile(patterns),str(x)) for patterns in condition_str) else x)

    result = result.dropna()
    return result


'''
    条件删除：
        把含有某字段的数据行标False
        返回原数据+bool列表
'''
# 把含有指定字段的数据清空
def filter_data(data,condition_str,ConditionsDelType):
    
    if ConditionsDelType == 'LongDel':
        if len(condition_str) != 2 or condition_str[0] > condition_str[1]:
            raise ValueError(f"长度删除需要传入两个参数，第一个为小值，第二个为大值")
        if len(str(data)) < condition_str[0] or len(str(data)) > condition_str[1]:
            return True
        return False
        
    if ConditionsDelType == 'StrDel':
        for i in condition_str:
            pattern = re.compile(i)
            if pattern.search(data):
                return False
        return True
    raise Exception('{ConditionsDelType} Error')


def condition_del_bool(datas,condition_str:list,data_columns:list,ConditionsDelType='StrDel'):
    '''
    datas:传入数据
    condition_str:要删除包含的字符串列表，或者长度
    data_columns:要删除的列
    ConditionsDelType:删除选项
        --LongDel   按照长度删除
        --StrDel    按照关键字删除
    '''
    result_data = datas.copy()
    result_list = [True for i in range(len(datas))]
    for i in data_columns:
        databool = datas[i].apply(lambda x: filter_data(str(x),condition_str,ConditionsDelType)).to_list()
        result_list = [i and j for i,j in zip(result_list,databool)]
    result_data['BOOL'] = result_list
    return result_data


'''
将指定的DataFrame列按照指定的分隔符进行切割
并将切割后的结果存储在新的DataFrame中。
'''
def cut_list(list1,cut_colname):
    '''
    list1: 列表
    cut_colname: 切割列名和值的分隔符
    '''
    result = []
    for i in list1:
        # 使用cut_colname作为分隔符对i进行切割，最多切割一次，返回切割后的列表
        cut_list1 = i.split(cut_colname,1)
        # 如果切割后的列表长度为2，则将其添加到结果列表中
        if len(cut_list1) %2 == 0:
            # print(cut_list1)
            result.extend(cut_list1)
    # 创建一个DataFrame，其中行数为1，列名为结果列表中偶数索引的元素（即列名），数据为结果列表中奇数索引的元素（即列值）
    result_data = pd.DataFrame([[result[i] for i in range(1,len(result),2)]],
                columns=[result[i] for i in range(0,len(result),2)])
    return result_data
def cut_columns_to_many(df,columns_name:str,cut_str:str,cut_colname:str):
    '''
    df: DataFrame
    columns_name: 列名
    cut_str: 分隔符
    cut_colname: 切割列名和值的分隔符
    '''
    result = pd.DataFrame()
    # 对指定的列使用分隔符进行切割，并赋值给原列
    df[columns_name] = df[columns_name].apply(lambda x: x.split(cut_str))
    # 对切割后的列表使用cut_colname进行再次切割，并将结果赋值给result
    result = df[columns_name].apply(lambda x: cut_list(x,cut_colname))
    # 初始化一个空的DataFrame，用于存储最终结果
    result_all = pd.DataFrame()
    # 遍历result中的每个元素，将其拼接到result_all中
    for i in result:
        result_all = pd.concat([result_all,i])
    return result_all

# 拆分数据，拆分为多列，不切分列名
def cut_columns_to(df, columns:str, cut_str, cut_num:int=2):
    """
    df: pd.DataFrame
    columns: str列名
    cut_str: str切分字符串
    cut_num: 1,2,3...切分后列数
    """
    # 确保columns列是字符串类型，如果不是则转换为字符串
    if not pd.api.types.is_string_dtype(df[columns]):
        df[columns] = df[columns].astype(str)
    df['result'] = df[columns].str.split(cut_str,n=cut_num-1)
    # result = pd.DataFrame(df['result'].tolist(), columns=[columns+'_'+str(i) for i in range(cut_num)])
    result = pd.DataFrame(df['result'].tolist())
    result = result.rename(columns=lambda x: str(x))
    result = pd.concat([df,result],axis=1)
    return result

'''
    拆分数据，去除前后缀
'''
def cut_columns_one(datas,data_col:str,cut_str,cut_suffix=['',''],hold_splitter=0):
    '''
    datas: 传入要拆分的数据
    data_col: 传入要拆分的列
    cut_str: 切分字符。
    cut_suffix: 去除前后缀的字符列表[前缀, 后缀]。
    hold_splitter: 是否保留切分字符，0不保留，1保留。
    '''
    result = []
    datas = datas[data_col]
    for data in datas:
        data_list = [i.lstrip(cut_suffix[0]).rstrip(cut_suffix[1]) for i in str(data).split(cut_str)]
        if hold_splitter:
            data_list = [str(i)+cut_str if i != data_list[-1] else i for i in data_list]
        result.extend(data_list)
    result = [line.strip() for line in result if line.strip()]
    return pd.DataFrame(result,columns=[data_col])



'''
    数据去重,保留第一项
'''
def Deletion_Conditions(datas,data_columns:list):
    '''
    datas:传入要去重的数据
    data_columns:要去重的列
    '''
    for i in data_columns:
        datas= datas.drop_duplicates(subset=i,keep='first')

    return datas



'''
    删除指定字符
'''
# 删除前后指定字符
def del_left_right(datas:pd.DataFrame,data_columns:str,delstr:str)->pd.DataFrame:
    '''
    datas:传入数据
    data_columns:列名
    delstr:去除前后字符
    '''
    datas[data_columns] = datas[data_columns].apply(lambda x: x.lstrip(delstr).rstrip(delstr))
    return datas
# 删除、替换指定字符
def re_del_str(datas:pd.DataFrame,data_columns,restr:str,repstr:str='')->pd.DataFrame:
    '''
    datas:传入数据
    data_columns:列名
    restr:去除的字符，可以是正则表达式
    repstr:修改后的字符，默认为空
    '''
    datas[data_columns] = datas[data_columns].apply(lambda x: re.sub(re.compile(restr),repstr,str(x)))
    return datas




'''
    字段抽取
'''
def Excerpt_Everyone(data,pattern):
    data = [i for i in set(re.findall(pattern,data))]
    if len(data) >= 2:
        return ' '.join(data)
    try:
        return data[0]
    except:
        return 'NULL'
def Excerpt_Fields(datas,fieldslist:list|str,excerpt_columns:str,patterns_mode='normal'):
    '''
    datas:传入要抽取字段的数据
    fields:要抽取的字段列表，正常模式输入列表，正则模式输入正则表达式
    excerpt_columns:列名
    patterns:模式，默认正常模式
        normal:正常模式，将字段列表的数据抽取出来
        re:正则表达式的方式抽取
    '''
    if patterns_mode == 'normal':
        fields = '|'.join(fieldslist)
        pattern = re.compile(fields)
        datas['Excerpt'] = datas[excerpt_columns].apply(lambda x: Excerpt_Everyone(x,pattern))
        return datas
    
    if patterns_mode == 're':
        pattern = re.compile(fieldslist,re.S)
        datas['Excerpt'] = datas[excerpt_columns].apply(lambda x: Excerpt_Everyone(x,pattern))
        return datas
    return pd.DataFrame()




'''抽取数据
        抽取方式： 1、正则；2、索引；3、随机
'''
def filter_re(pattern,x,data_columns):
    for i in data_columns:
        if pattern.search(str(x[i])):
            return x
    return np.nan
        
def extract_data(datas,extract_mode='Randomly',re_data='',data_columns:list=['All'],num=-1,IndexNum=[0,-1]) -> pd.DataFrame:
    '''
        datas:数据
        extract_mode:抽取方式，默认随机
            --Randomly  随机抽取
            --ReExtraction  正则抽取
            --IndexExtraction   索引抽取
        re_data:正则表达式
        data_columns:按照某列进行匹配,默认全部列
        num:抽取数量,默认抽取全部
        IndexNum:索引[起始位置,结束位置]
    '''
    # 随机抽取
    if extract_mode=='Randomly':
        # 在数据长度内随机生成指定数量的随机数
        result = pd.DataFrame()
        if num > len(datas):
            num = len(datas)
        random_numbers = random.sample(range(0,len(datas)), num)
        result = datas.iloc[random_numbers]
        # 索引重置
        result = result.reset_index(drop=True)
        return result
    # 正则抽取
    if extract_mode=='ReExtraction':
        pattern = re.compile(re_data)
        if data_columns[0] == 'All':
            data_columns = datas.columns
        result = pd.DataFrame(columns=datas.columns)

        result = datas.apply(lambda x:filter_re(pattern,x,data_columns),axis=1,result_type='broadcast')
        result = result.dropna(how='all')

        if num != -1:
            try:
                return result[:num:1]
            except:
                return result
        return result
    # 索引抽取
    if extract_mode=='IndexExtraction':
        return datas.iloc[IndexNum[0]:IndexNum[1]]
    return pd.DataFrame()


'''
    混合用法
    按照概率插入字符，插入位置为提供的字符
        插入方式：1、随机插入；2、指定位置插入
'''
# 选择符号，按概率选择符号出现次数
def randomstr_for_probability(strlist: list, str_probability: list, frequency: list, probability: list):
    '''
    strlist:用户自定义字符列表
    str_probability:用户自定义字符概率
    frequency:用户自定义出现次数列表
    probability:用户自定义次数概率列表
    '''
    # 按照概率随机选择符号
    str_chosen = random.choices(strlist, weights = str_probability)[0]
    # 按照概率随机生成符号出现次数
    str_probability = random.choices(frequency, weights = probability)[0]
    return str_chosen*str_probability

# 字符插入位置
# 按照概率选择插入字符以及插入字符个数，在指定符号后插入字符，可以选择最大插入次数
def Insertion_location_str(datas,data_columns:str,strdict: dict, frequencydict: dict, str_location = 0, maxsub = 1):
    '''
    datas:要插入符号的数据
    data_columns:数据列名
    strdict:插入字符：频率
    frequencydict:字符个数：频率
    str_location:提供符号位置，默认随机
    maxsub:表示最大插入次数，默认插入一次
    '''
    datas = datas[data_columns]
    result = []
    if str_location != 0:
        for data in datas:
            random_char = randomstr_for_probability(list(strdict.keys()),list(strdict.values()),list(frequencydict.keys()),list(frequencydict.values()))
            data_list = data.split(str_location,maxsplit = maxsub)
            result.append(f'{str_location+random_char}'.join(data_list))
        return pd.DataFrame(result,columns=[data_columns])
    
    for data in datas:
        random_char = randomstr_for_probability(list(strdict.keys()),list(strdict.values()),list(frequencydict.keys()),list(frequencydict.values()))
        # 随机生成位置
        random_position = random.randint(0, len(data)-1)
        result.append(data[:random_position] + random_char + data[random_position:])
    return pd.DataFrame(result,columns=[data_columns])



# 超长统计
def long_con_out(datas,columns_name,length_range:list) -> pd.DataFrame:
    '''
    datas:传入数据
    columns_name:列名
    length_range:长度区间,格式为 [min_length, max_length]
    '''
    # longer = pd.DataFrame()
    # for index,row in datas.iterrows():
    #     if len(row[columns_name])<length_range[0] or len(row[columns_name])>length_range[1]:
    #         longer = pd.concat([longer,pd.DataFrame([row])])
    # return longer
    datas[columns_name] = datas[columns_name].astype(str)
    mask = (datas[columns_name].str.len() <= length_range[0]) | (datas[columns_name].str.len() >= length_range[1])
    return datas[mask]
def long_con_in(datas,columns_name,length_range:list) -> pd.DataFrame:
    '''
    datas:传入数据
    columns_name:列名
    length_range:长度区间,格式为 [min_length, max_length]
    '''
    # longer = pd.DataFrame()
    # for index,row in datas.iterrows():
    #     if len(row[columns_name])<length_range[0] or len(row[columns_name])>length_range[1]:
    #         longer = pd.concat([longer,pd.DataFrame([row])])
    # return longer
    datas[columns_name] = datas[columns_name].astype(str)
    if len(length_range) != 2 or length_range[0] > length_range[1]:
            raise ValueError(f"长度删除需要传入两个参数，第一个为小值，第二个为大值")
    mask = (datas[columns_name].str.len() >= length_range[0]) & (datas[columns_name].str.len() <= length_range[1])
    return datas[mask]



# 交叉合并
def overlapping_and(lst1,lst2):
    '''
    交叉合并
    '''
    result = [item for pair in zip(lst1, lst2) for item in pair]
    return pd.DataFrame(result,columns=['and_result'])



def replace_data(df:pd.DataFrame,column_name:str,replace_data:str,replace_to:str):
    """
    在DataFrame的指定列中替换整个数据。

    Args:
        df (pd.DataFrame): 要处理的DataFrame对象。
        column_name (str): 要替换数据的列名。
        replace_data (str): 要被替换的数据，支持正则表达式。
        replace_to (str): 替换后的数据。

    Returns:
        pd.DataFrame: 替换后的DataFrame对象。

    """
    df = df.copy()
    df[column_name] = df[column_name].astype(str)
    df[column_name] = df[column_name].apply(
        lambda x: replace_to if re.search(re.compile(replace_data),x) else x
    )
    return df


'''
    混合用法
    按照概率替换字符或者删除字符
'''
# 按照概率判断指定字符是否要替换
def replace_str_probability(str_rep, strdict: dict, rep_probability=1, rep_str = ''):
    '''
    str_rep:要执行替换的字符串
    strdict:替换字符的映射表,字符:概率
    rep_probability:替换概率，默认为全部替换
    rep_str:要替换成的字符，默认为空
    '''
    # 输出的字符串
    result = ''
    # 按照概率判断本行需要替换的字符
    repstr = random.choices(list(strdict.keys()), weights = list(strdict.values()))[0]
    # 正则按照要替换的字符切分字符串，如果不存在，切分后的列表只有一个元素
    pattern = re.compile(repstr)
    resplit = re.split(pattern,str_rep)

    print(repstr,resplit)
    # 判断切分后的长度是否为1
    if len(resplit) == 1:
        return str_rep
    
    # 由result先承接切分后列表的第一个元素
    result = resplit[0]
    # 循环，在每一个位置，判断一次是否需要替换
    for i in range(0,len(resplit)-1):
        # print(resplit)
        if random.random() <= rep_probability:
            # 对于需要替换的字符进行替换，rep_str为替换后的元素
            result += rep_str + resplit[i+1]
            continue
        result += repstr + resplit[i+1]
    # print(result)
    return result
# 概率替换指定符号
def replace_list_probability(datas,data_columns:str, strdict: dict, rep_probability=1, rep_str = ''):
    '''
    datas:传入数据
    data_columns:要替换的列名
    strdict:替换字符的映射表,字符:概率
    rep_probability:替换概率，默认为全部替换
    rep_str:要替换成的字符，默认为空
    '''
    result = []
    
    # 遍历字符串，根据概率判断是否要替换对应字符
    for data in datas[data_columns]:
        # print(data)
        result.append(replace_str_probability(data, strdict, rep_probability, rep_str))
    datas[data_columns] = result
    return datas