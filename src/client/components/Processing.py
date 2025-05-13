import pandas as pd
import gradio as gr
from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from gradio.components import Component
from manager import manager
from common import close_show, show_pages,get_logs, get_droplist_check
from func.ProcessingDef import *

def create_processing_tab() -> Dict[str, "Component"]:
    interactive_elems, user_elems, elem_dict = set(), set(), dict()
    # 数据选择
    with gr.Row():
        processing_source = gr.Dropdown(choices=["dataset_info", "generation", "processing"], scale=1, value=None, label="下拉选择数据源", interactive=False)
        processing_collection_name = gr.Dropdown(choices=[], scale=2, value=None, label="下拉选择任务数据集", interactive=False)
        with gr.Column():
            with gr.Row():
                processing_meta_button = gr.Button(value='元信息', scale=1, interactive=False)
                processing_data_button = gr.Button(value='数据', scale=1, interactive=False)
            with gr.Row():
                processing_data_close_button = gr.Button(value='关闭显示', scale=1, interactive=False)
                processing_del_button = gr.Button(value='删除数据', scale=1, interactive=False)
    with gr.Row():
        download_type = gr.Dropdown(choices=['xlsx', 'csv', 'json', 'jsonl'], label="保存文件类型", value='xlsx', scale=8, interactive=False)
        btn_processing_download = gr.Button(value='下载数据', scale=1, interactive=False)
        file_downloaded = gr.File(scale=1, visible=False)

    # 数据展示
    with gr.Accordion("数据内容", open=True, visible=False) as processing_show_data:
        processing_collection_meta = gr.Json(label='数据元信息', visible=False)
        processing_collection_data = gr.Dataframe(type="pandas", height=500, wrap=True, visible=False, interactive=False)
        processing_collection_pages = gr.Slider(label='pages', visible=False, interactive=True)

    user_elems.update({processing_source, processing_collection_name,download_type})
    interactive_elems.update({processing_source,download_type,processing_del_button,file_downloaded,btn_processing_download, processing_collection_name, processing_meta_button, processing_data_button, processing_data_close_button, processing_collection_pages})
    elem_dict.update(dict(
        processing_source=processing_source,
        processing_collection_name=processing_collection_name, processing_meta_button=processing_meta_button,
        processing_data_button=processing_data_button, processing_data_close_button=processing_data_close_button,
        processing_show_data=processing_show_data,
        processing_collection_meta=processing_collection_meta, processing_collection_data=processing_collection_data,
        processing_collection_pages=processing_collection_pages,
        btn_processing_download = btn_processing_download,
        download_type = download_type,
        file_downloaded = file_downloaded,
        processing_del_button = processing_del_button
    ))
    with gr.Row():
        with gr.Column():
            processing_mode = gr.Dropdown(
                choices=[
                    '请选择',
                    '多列合并',
                    '长度统计',
                    '分类统计(数量)',
                    '多行混合',
                    '条件删除',
                    '条件删除-Bool',
                    '分割数据为多列',
                    '数据拆分',
                    '数据去重',
                    '指定字符替换',
                    '字段抽取',
                    '数据抽取',
                    '概率插入字符',
                    '交叉合并',
                    '数据替换',
                    '概率替换字符'
                ],
                label="选择处理方式", interactive=False,value='请选择')
    
    user_elems.update({
        processing_mode
    })
    interactive_elems.update({
        processing_mode
    })
    elem_dict.update(dict(
        processing_mode=processing_mode
    ))

    extra = {}
    def result_type_show_and_str(result_type):
        if result_type == 'str':
            return gr.update(visible=True)
        return gr.update(visible=False)
    # 多列合并字段选择
    with gr.Accordion(label='多列合并字段选择',visible=False,open=False) as andcolumnsdatas:
        gr.Markdown("""将指定的列按照指定分隔符进行合并""")
        with gr.Row():
            acd_data_col = gr.Dropdown(label="列名",multiselect=True)
            acd_and_str = gr.Textbox(label="合并分隔符",visible=False)
            acd_result_type = gr.Dropdown(label="结果类型",choices=['str','list','tuple'])
            acd_new_col = gr.Textbox(label="合并后列名")
            acd_btn = gr.Button(value="开始处理")
    acd_result_type.select(
        result_type_show_and_str,
        inputs=acd_result_type,
        outputs=acd_and_str
    )
    user_elems.update({acd_data_col, acd_and_str,acd_result_type,acd_new_col})
    interactive_elems.update({acd_data_col, acd_and_str,acd_btn,acd_result_type,acd_new_col})
    extra.update(dict(ACD=dict(
        acd_data_col=acd_data_col, 
        acd_and_str=acd_and_str, 
        acd_btn=acd_btn,
        acd_result_type=acd_result_type,
        acd_new_col=acd_new_col)))
    elem_dict.update(andcolumnsdatas=andcolumnsdatas)

    # 超长统计字段选择
    with gr.Accordion(label='长度统计',visible=False,open=False) as longcondatas:
        gr.Markdown('''统计选中列中数据指定长度的数据：超长统计、长度统计''')
        with gr.Row():
            lcd_longcondata_type = gr.Dropdown(label="统计类型",choices=['超长统计','长度统计'])
            lcd_data_col = gr.Dropdown(label="列名")
            lcd_lengthrange_min = gr.Number(label="最小长度")
            lcd_lengthrange_max = gr.Number(label="最大长度")
            lcd_btn = gr.Button(value="开始处理")
    user_elems.update({
        lcd_data_col,lcd_lengthrange_min,lcd_lengthrange_max,lcd_longcondata_type
    })
    interactive_elems.update({
        lcd_data_col,lcd_lengthrange_min,lcd_lengthrange_max,lcd_btn,lcd_longcondata_type
    })
    extra.update(dict(LCD=dict(
        lcd_data_col=lcd_data_col,
        lcd_lengthrange_min=lcd_lengthrange_min,
        lcd_lengthrange_max=lcd_lengthrange_max,
        lcd_btn=lcd_btn,
        lcd_longcondata_type=lcd_longcondata_type
    )))
    elem_dict.update(dict(
        longcondatas=longcondatas,
    ))

    # 分类统计字段选择
    with gr.Accordion(label='分类统计(数量)',visible=False,open=False) as categoriescondata:
        gr.Markdown('''统计选中列中数据分类情况,并筛选数量，筛选数量为0时不筛选''')
        with gr.Row():
            ccd_data_col = gr.Dropdown(label="列名",multiselect=True)
            ccd_data_count = gr.Number(label="统计数量筛选")
            ccd_btn = gr.Button(value="开始处理")
    user_elems.update({
        ccd_data_col,ccd_data_count
    })
    interactive_elems.update({
        ccd_data_col,ccd_btn,ccd_data_count
    })
    extra.update(dict(CC=dict(
        ccd_data_col=ccd_data_col,
        ccd_btn=ccd_btn,
        ccd_data_count=ccd_data_count
    )))
    elem_dict.update(dict(
        categoriescondata=categoriescondata,
    ))

    with gr.Accordion(label='多行混合',visible=False,open=False) as allcolmixdatas:
        gr.Markdown("""将指定列按照指定分隔符进行混合""")
        with gr.Row():
            ac_data_col = gr.Dropdown(label="列名")
            ac_nums = gr.Number(label="合并后数据行数")
            ac_str_mix = gr.Text(label="分隔符字典",placeholder='{分隔符：概率}')
            ac_eve_num = gr.Text(label='给定合并条数',placeholder='{条数：概率}')
        with gr.Row():
            ac_pre_suffix = gr.Text(label='合并后前后符号',placeholder='默认为空,输入格式为:['"前字符串"','"后字符串"']')
            ac_and_mode = gr.Dropdown(label='混合模式',choices=['不放回合并','放回合并'])
            ac_btn = gr.Button(value="开始处理")
    user_elems.update({
        ac_data_col,ac_nums,ac_str_mix,ac_eve_num,ac_pre_suffix,ac_and_mode
    })
    interactive_elems.update({
        ac_data_col,ac_nums,ac_str_mix,ac_eve_num,ac_pre_suffix,ac_and_mode,ac_btn
    })
    extra.update(dict(AC=dict(
        ac_data_col=ac_data_col,
        ac_nums=ac_nums,
        ac_str_mix=ac_str_mix,
        ac_eve_num=ac_eve_num,
        ac_pre_suffix=ac_pre_suffix,
        ac_and_mode=ac_and_mode,
        ac_btn=ac_btn
    )))
    elem_dict.update(dict(
        allcolmixdatas=allcolmixdatas,
    ))
    with gr.Accordion(label='条件删除',visible=False,open=False) as conditiondeldatas:
        gr.Markdown("""把含有某字段的行删除""")
        with gr.Row():
            cddd_data_col = gr.Dropdown(label="列名",multiselect=True)
            cddd_condition_str = gr.Text(label="删除条件",placeholder='要删除包含的字符串列表(可以使用正则)')
            cddd_btn = gr.Button(value="开始处理")
    user_elems.update({
        cddd_data_col, cddd_condition_str
    })
    interactive_elems.update({
        cddd_data_col, cddd_condition_str,cddd_btn
    })
    extra.update(dict(
        CDDD=dict(
            cddd_data_col=cddd_data_col,
            cddd_condition_str=cddd_condition_str,
            cddd_btn=cddd_btn
        )
    ))
    elem_dict.update(dict(
        conditiondeldatas=conditiondeldatas,
    ))
    def show_conditiondelbooldatas_typecontorl(mode_type):
        if mode_type == 'LongDel':
            return [
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=True),
            ]
        elif mode_type == 'StrDel':
            return [
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
            ]
    with gr.Accordion(label='条件删除-Bool',visible=False,open=False) as conditiondelbooldatas:
        gr.Markdown("""把含有某字段的行标注为False,其余为True,返回原数据+BOOL列
                    超出长度的标注为True,其余为False
                    """)
        with gr.Row():
            cddbd_data_col = gr.Dropdown(label="列名",multiselect=True)
            cddbd_condition_str = gr.Text(label="删除条件",placeholder='要删除包含的字符串列表(可以使用正则)',visible=False)
            cddbd_min_length = gr.Number(label="最小长度",visible=False)
            cddbd_max_length = gr.Number(label="最大长度",visible=False)
            cddbd_comditionsdeltype = gr.Dropdown(label='删除模式',choices=['LongDel','StrDel'])
            cddbd_btn = gr.Button(value="开始处理")
    cddbd_comditionsdeltype.select(
        show_conditiondelbooldatas_typecontorl,
        inputs=[cddbd_comditionsdeltype],
        outputs=[cddbd_condition_str,cddbd_min_length,cddbd_max_length]
    )
    user_elems.update({
        cddbd_data_col, cddbd_condition_str,cddbd_min_length,cddbd_max_length,cddbd_comditionsdeltype
    })
    interactive_elems.update({
        cddbd_data_col, cddbd_condition_str,cddbd_min_length,cddbd_max_length,cddbd_comditionsdeltype,cddbd_btn})
    extra.update(dict(
        CDDBD=dict(
            cddbd_data_col=cddbd_data_col,
            cddbd_condition_str=cddbd_condition_str,
            cddbd_min_length=cddbd_min_length,
            cddbd_max_length=cddbd_max_length,
            cddbd_comditionsdeltype=cddbd_comditionsdeltype,
            cddbd_btn=cddbd_btn
        )
    ))
    elem_dict.update(dict(
        conditiondelbooldatas=conditiondelbooldatas,
    ))
    with gr.Accordion(label='分割数据为多列',visible=False,open=False) as cutcolumntomanydatas:
        gr.Markdown("""将指定的DataFrame列按照指定的分隔符进行切割并将切割后的结果存储在新的DataFrame中。""")
        with gr.Row():
            cctmd_col = gr.Dropdown(label="列名")
            cctmd_cut_str = gr.Text(label="分隔符")
            cctmd_cut_num = gr.Number(label="最大切割列数")
            cctmd_btn = gr.Button(value="开始处理")
    user_elems.update({
        cctmd_col, cctmd_cut_str,cctmd_cut_num
    })
    interactive_elems.update({
        cctmd_col, cctmd_cut_str,cctmd_cut_num,cctmd_btn
    })
    extra.update(dict(
        CCTMD=dict(
            cctmd_col=cctmd_col,
            cctmd_cut_str=cctmd_cut_str,
            cctmd_cut_num=cctmd_cut_num,
            cctmd_btn=cctmd_btn
        )
    ))
    elem_dict.update(dict(
        cutcolumntomanydatas=cutcolumntomanydatas
    ))
    with gr.Accordion(label='数据拆分',visible=False,open=True) as cutcolumnsonedatas:
        gr.Markdown('''拆分数据去除前后缀,将拆分后的数据放在一列中''')
        with gr.Row():
            ccsd_data_col = gr.Dropdown(label="列名")
            ccsd_cut_str = gr.Text(label="切分字符")
            ccsd_cut_suffix_first = gr.Text(label="前缀",placeholder='前缀')
            ccsd_cut_suffix_end = gr.Text(label="后缀",placeholder='后缀')
            ccsd_hold_splitter = gr.Dropdown(label="是否保留分隔符",choices=['是','否'])
            ccsd_btn = gr.Button(value="开始处理")
    user_elems.update({
        ccsd_data_col, ccsd_cut_str,ccsd_cut_suffix_first,ccsd_cut_suffix_end,ccsd_hold_splitter
    })
    interactive_elems.update({
        ccsd_data_col, ccsd_cut_str,ccsd_cut_suffix_first,ccsd_cut_suffix_end,ccsd_hold_splitter,ccsd_btn})
    extra.update(dict(
        CCSD=dict(
            ccsd_data_col=ccsd_data_col,
            ccsd_cut_str=ccsd_cut_str,
            ccsd_cut_suffix_first=ccsd_cut_suffix_first,
            ccsd_cut_suffix_end=ccsd_cut_suffix_end,
            ccsd_hold_splitter=ccsd_hold_splitter,
            ccsd_btn=ccsd_btn
        )
    ))
    elem_dict.update(dict(
        cutcolumnsonedatas=cutcolumnsonedatas,
    ))
    with gr.Accordion(label='数据去重',open=False,visible=False) as deletionconditionsdatas:
        gr.Markdown("""将重复的数据去除，只保留第一次出现的数据。""")
        with gr.Row():
            dcd_data_col = gr.Dropdown(label="列名",multiselect=True)
            dcd_btn = gr.Button(value="开始处理")
    user_elems.update({
        dcd_data_col})
    interactive_elems.update({
        dcd_data_col, dcd_btn})
    extra.update(dict(
        DCD=dict(
            dcd_data_col=dcd_data_col,
            dcd_btn=dcd_btn
        )
    ))
    elem_dict.update(dict(
        deletionconditionsdatas=deletionconditionsdatas,
    ))
    with gr.Accordion(label='指定字符替换',visible=False,open=False) as redelstrdatas:
        gr.Markdown("""将指定列中的数据按照指定的字符串进行替换。""")
        with gr.Row():
            rdsd_data_col = gr.Dropdown(label="列名")
            rdsd_restr = gr.Text(label="要替换的字符")
            rdsd_repstr = gr.Text(label="替换后字符",placeholder='如要删除此处可以不填')
            rdsd_btn = gr.Button(value="开始处理")
    user_elems.update({
        rdsd_data_col, rdsd_restr,rdsd_repstr})
    interactive_elems.update({
        rdsd_data_col, rdsd_restr,rdsd_repstr,rdsd_btn})
    extra.update(dict(
        RDSD=dict(
            rdsd_data_col=rdsd_data_col,
            rdsd_restr=rdsd_restr,
            rdsd_repstr=rdsd_repstr,
            rdsd_btn=rdsd_btn
        )
    ))
    elem_dict.update(dict(
        redelstrdatas=redelstrdatas,
    ))
    with gr.Accordion(label='字段抽取',visible=False,open=True) as extractfieldsdatas:
        gr.Markdown("""抽取指定列中指定字段，返回原数据+抽取字段。""")
        with gr.Row():
            efd_data_col = gr.Dropdown(label="列名")
            efd_fieldslist = gr.Text(label="抽取字段",placeholder='正常模式下输入列表，如[1,2,3],正则模式下输入正则表达式')
            efd_patterns_mode = gr.Dropdown(label="抽取模式",choices=['正则抽取','正常抽取'])
            efd_btn = gr.Button(value="开始处理")
    user_elems.update({
        efd_data_col, efd_fieldslist,efd_patterns_mode})
    interactive_elems.update({
        efd_data_col, efd_fieldslist,efd_patterns_mode,efd_btn})
    extra.update(dict(
        EFD=dict(
            efd_data_col=efd_data_col,
            efd_fieldslist=efd_fieldslist,
            efd_patterns_mode=efd_patterns_mode,
            efd_btn=efd_btn
        )
    ))
    elem_dict.update(dict(
        extractfieldsdatas=extractfieldsdatas,
    ))
    def show_ed_mode(ed_extract_mode, ed_data_col, ed_re_data, ed_index_start, ed_index_end, ed_num):
        if ed_extract_mode == '随机抽取':
            return [gr.update(visible=False)]*4+[gr.update(visible=True)]
        elif ed_extract_mode == '索引抽取':
            return [gr.update(visible=False)]*2+[gr.update(visible=True)]*2+[gr.update(visible=False)]
        elif ed_extract_mode == '正则抽取':
            return [gr.update(visible=True)]*2+[gr.update(visible=False)]*2+[gr.update(visible=True)]
        else:
            return [gr.update(visible=False)]*5
    with gr.Accordion(label='数据抽取',visible=False,open=False) as extractdatas:
        gr.Markdown("""抽取方式为三种，正则抽取，索引抽取，随机抽取。
                    正则抽取：根据选择的列按照正则表达式抽取数据，
                    索引抽取：根据索引号抽取数据，随机抽取：抽取指定数量数据。""")
        with gr.Row():
            ed_data_col = gr.Dropdown(label="列名",multiselect=True,visible=False)
            ed_extract_mode = gr.Dropdown(label='抽取模式',choices=['请选择','正则抽取','索引抽取','随机抽取'],value='请选择')
            ed_re_data = gr.Text(label='正则表达式',placeholder='正则表达式',visible=False)
            ed_index_start = gr.Number(label='开始索引',visible=False)
            ed_index_end = gr.Number(label='结束索引',visible=False)
            ed_num = gr.Number(label='抽取数量',visible=False)
            ed_btn = gr.Button(value="开始处理")
            ed_extract_mode.select(
                show_ed_mode,
                inputs=[ed_extract_mode, ed_data_col, ed_re_data, ed_index_start, ed_index_end, ed_num],
                outputs=[ed_data_col, ed_re_data, ed_index_start, ed_index_end, ed_num]
            )
    user_elems.update({
        ed_data_col, ed_extract_mode,ed_re_data,ed_index_start, ed_index_end,ed_num})
    interactive_elems.update({
        ed_data_col, ed_extract_mode,ed_re_data,ed_index_start, ed_index_end,ed_num,ed_btn})
    extra.update(dict(
        ED=dict(
            ed_data_col=ed_data_col,
            ed_extract_mode=ed_extract_mode,
            ed_re_data=ed_re_data,
            ed_index_start = ed_index_start, 
            ed_index_end = ed_index_end,
            ed_num=ed_num,
            ed_btn=ed_btn
        )
    ))
    elem_dict.update(dict(
        extractdatas=extractdatas,
    ))
    def ilsd_show_mode(ilsd_insert_mdoe,ilsd_str_location,ilsd_maxsub):
        if ilsd_insert_mdoe == '随机插入':
            return [gr.update(visible=False)]*2
        elif ilsd_insert_mdoe == '指定位置插入':
            return [gr.update(visible=True)]*2
        else:
            return [gr.update(visible=False)]*2
    with gr.Accordion(label='混合概率插入字符',visible=False,open=False) as insertionlocationstrdatas:
        gr.Markdown("""混合用法
                    按照概率插入字符，插入位置为提供的字符
                    插入方式：1、随机插入；2、指定位置插入""")
        with gr.Row():
            ilsd_data_col = gr.Dropdown(label="列名")
            ilsd_strdict = gr.Text(label="字符概率字典",placeholder='如{"a":0.5,"c":0.5}')
            ilsd_frequencydict = gr.Text(label="字符个数概率字典",placeholder='如{"1":0.5,"2":0.5}')
            ilsd_insert_mode = gr.Dropdown(label="插入方式",choices=['随机插入','指定位置插入'])
            ilsd_str_location = gr.Text(label="插入位置",visible=False)
            ilsd_maxsub = gr.Number(label="最大插入次数",visible=False)
            ilsd_btn = gr.Button(value="开始处理")
    ilsd_insert_mode.select(
        ilsd_show_mode,
        inputs=[ilsd_insert_mode, ilsd_str_location,ilsd_maxsub],
        outputs=[ilsd_str_location,ilsd_maxsub]
    )
    user_elems.update({
        ilsd_data_col, ilsd_strdict, ilsd_frequencydict, ilsd_insert_mode, ilsd_str_location, ilsd_maxsub})
    interactive_elems.update({
        ilsd_data_col, ilsd_strdict, ilsd_frequencydict, ilsd_insert_mode, ilsd_str_location, ilsd_maxsub, ilsd_btn})
    extra.update(dict(
        ILSD = dict(
            ilsd_data_col=ilsd_data_col,
            ilsd_strdict = ilsd_strdict,
            ilsd_frequencydict = ilsd_frequencydict,
            ilsd_insert_mode = ilsd_insert_mode,
            ilsd_str_location = ilsd_str_location,
            ilsd_maxsub = ilsd_maxsub,
            ilsd_btn = ilsd_btn
        )
    ))
    elem_dict.update(dict(insertionlocationstrdatas=insertionlocationstrdatas))
    with gr.Accordion(label='交叉合并',visible=False,open=False) as overlappinganddatas:
        gr.Markdown('将两列数据交叉合并')
        with gr.Row():
            oaad_data1 = gr.Dropdown(label="列名1")
            oaad_data2 = gr.Dropdown(label="列名2")
            oaad_btn = gr.Button(value="开始处理")
    user_elems.update({
        oaad_data1, oaad_data2})
    interactive_elems.update({
        oaad_data1, oaad_data2, oaad_btn})
    extra.update(dict(
        OAAD = dict(
            oaad_data1=oaad_data1,
            oaad_data2=oaad_data2,
            oaad_btn=oaad_btn
        )
    ))
    elem_dict.update(dict(overlappinganddatas=overlappinganddatas))
    with gr.Accordion(label='数据替换',visible=False,open=False) as replacedatadatas:
        gr.Markdown('将含有某字段的数据全部替换')
        with gr.Row():
            rdd_data_col = gr.Dropdown(label="列名")
            rdd_replace_data = gr.Text(label='旧字符',placeholder='支持正则表达式')
            rdd_replace_to = gr.Text(label='新字符')
            rdd_btn = gr.Button(value="开始处理")
    user_elems.update({
        rdd_data_col, rdd_replace_data, rdd_replace_to})
    interactive_elems.update({
        rdd_data_col, rdd_replace_data, rdd_replace_to, rdd_btn})
    extra.update(dict(
        RDD = dict(
            rdd_data_col = rdd_data_col,
            rdd_replace_data = rdd_replace_data,
            rdd_replace_to = rdd_replace_to,
            rdd_btn = rdd_btn
        )
    ))
    elem_dict.update(dict(replacedatadatas=replacedatadatas))
    with gr.Accordion(label='概率替换字符',visible=False,open=False) as replacestrprobability:
        gr.Markdown('按照概率替换字符或删除字符')
        with gr.Row():
            rsp_data_col = gr.Dropdown(label='列名')
            rsp_strdict = gr.Text(label='替换字符的映射表',placeholder='{"字符":"概率"}')
            rsp_rep_str = gr.Text(label='替换字符',placeholder='不填为删除')
            rsp_rep_probability = gr.Slider(maximum=1,minimum=0,label= '概率',step=0.1, value=0.1, scale=1,interactive=True)
            rsp_btn = gr.Button(value='开始处理')
    user_elems.update({
        rsp_data_col, rsp_strdict, rsp_rep_probability,rsp_rep_str})
    interactive_elems.update({
        rsp_data_col, rsp_strdict, rsp_rep_probability,rsp_rep_str, rsp_btn})
    extra.update(dict(
        RSP = dict(
            rsp_data_col=rsp_data_col,
            rsp_strdict=rsp_strdict,
            rsp_rep_probability=rsp_rep_probability,
            rsp_rep_str=rsp_rep_str,
            rsp_btn=rsp_btn
        )
    ))
    elem_dict.update(dict(replacestrprobability=replacestrprobability))
    with gr.Row():
        process_name = gr.Text(label="处理名称",placeholder='请输入处理名称',interactive=False)
        with gr.Column(scale=1):
            processing_overwrite = gr.Checkbox(label='覆盖同名文件', value=False, scale=1, interactive=False)
    # 输出
    ouput_df = gr.Dataframe(label="处理结果",visible=False,interactive=False,type='pandas')
    user_elems.update({process_name,processing_overwrite})
    interactive_elems.update({ouput_df,process_name,processing_overwrite})
    elem_dict.update(dict(
        ouput_df=ouput_df,
        process_name = process_name,
        processing_overwrite = processing_overwrite
    ))
    elem_dict.update(extra=extra)
    return elem_dict, interactive_elems, user_elems


def callback_init_processing():
    user_name = manager.get_elem_by_name('top.user_name')
    sys_info = manager.get_elem_by_name('top.sys_info')
    # 文件选择
    processing_mode = manager.get_elem_by_name('processing.processing_mode')
    processing_source = manager.get_elem_by_name('processing.processing_source')
    processing_collection_name = manager.get_elem_by_name('processing.processing_collection_name')
    
    # 数据显示组件
    processing_meta_button = manager.get_elem_by_name('processing.processing_meta_button')
    processing_data_button = manager.get_elem_by_name('processing.processing_data_button')
    processing_data_close_button = manager.get_elem_by_name('processing.processing_data_close_button')

    processing_show_data = manager.get_elem_by_name('processing.processing_show_data')
    processing_collection_meta = manager.get_elem_by_name('processing.processing_collection_meta')
    processing_collection_data = manager.get_elem_by_name('processing.processing_collection_data')
    processing_collection_pages = manager.get_elem_by_name('processing.processing_collection_pages')
    # 多列合并组件
    andcolumnsdatas = manager.get_elem_by_name('processing.andcolumnsdatas')
    acd_data_col = manager.get_elem_by_name('processing.extra.ACD.acd_data_col')
    acd_and_str = manager.get_elem_by_name('processing.extra.ACD.acd_and_str')
    acd_result_type = manager.get_elem_by_name('processing.extra.ACD.acd_result_type')
    acd_new_col = manager.get_elem_by_name('processing.extra.ACD.acd_new_col')
    acd_btn = manager.get_elem_by_name('processing.extra.ACD.acd_btn')
    # 超长统计组件
    longcondatas = manager.get_elem_by_name('processing.longcondatas')
    lcd_longcondata_type = manager.get_elem_by_name('processing.extra.LCD.lcd_longcondata_type')
    lcd_data_col = manager.get_elem_by_name('processing.extra.LCD.lcd_data_col')
    lcd_lengthrange_min = manager.get_elem_by_name('processing.extra.LCD.lcd_lengthrange_min')
    lcd_lengthrange_max = manager.get_elem_by_name('processing.extra.LCD.lcd_lengthrange_max')
    lcd_btn = manager.get_elem_by_name('processing.extra.LCD.lcd_btn')

    # 分类统计组件
    categoriescondata = manager.get_elem_by_name('processing.categoriescondata')
    ccd_data_col = manager.get_elem_by_name('processing.extra.CC.ccd_data_col')
    ccd_data_count = manager.get_elem_by_name('processing.extra.CC.ccd_data_count')
    ccd_btn = manager.get_elem_by_name('processing.extra.CC.ccd_btn')
    # 多行混合组件
    allcolmixdatas = manager.get_elem_by_name('processing.allcolmixdatas')
    ac_data_col = manager.get_elem_by_name('processing.extra.AC.ac_data_col')
    ac_nums = manager.get_elem_by_name('processing.extra.AC.ac_nums')
    ac_str_mix = manager.get_elem_by_name('processing.extra.AC.ac_str_mix')
    ac_eve_num = manager.get_elem_by_name('processing.extra.AC.ac_eve_num')
    ac_pre_suffix = manager.get_elem_by_name('processing.extra.AC.ac_pre_suffix')
    ac_and_mode = manager.get_elem_by_name('processing.extra.AC.ac_and_mode')
    ac_btn = manager.get_elem_by_name('processing.extra.AC.ac_btn')
    # 条件删除组件
    conditiondeldatas = manager.get_elem_by_name('processing.conditiondeldatas')
    cddd_data_col = manager.get_elem_by_name('processing.extra.CDDD.cddd_data_col')
    cddd_condition_str = manager.get_elem_by_name('processing.extra.CDDD.cddd_condition_str')
    cddd_btn = manager.get_elem_by_name('processing.extra.CDDD.cddd_btn')
    ouput_df = manager.get_elem_by_name('processing.ouput_df')
    # 条件删除-Bool组件
    conditiondelbooldatas = manager.get_elem_by_name('processing.conditiondelbooldatas')
    cddbd_data_col = manager.get_elem_by_name('processing.extra.CDDBD.cddbd_data_col')
    cddbd_condition_str = manager.get_elem_by_name('processing.extra.CDDBD.cddbd_condition_str')
    cddbd_min_length = manager.get_elem_by_name('processing.extra.CDDBD.cddbd_min_length')
    cddbd_max_length = manager.get_elem_by_name('processing.extra.CDDBD.cddbd_max_length')
    cddbd_comditionsdeltype = manager.get_elem_by_name('processing.extra.CDDBD.cddbd_comditionsdeltype')
    cddbd_btn = manager.get_elem_by_name('processing.extra.CDDBD.cddbd_btn')
    # 分割数据为多列
    cutcolumntomanydatas = manager.get_elem_by_name('processing.cutcolumntomanydatas')
    cctmd_col = manager.get_elem_by_name('processing.extra.CCTMD.cctmd_col')
    cctmd_cut_str = manager.get_elem_by_name('processing.extra.CCTMD.cctmd_cut_str')
    cctmd_cut_num = manager.get_elem_by_name('processing.extra.CCTMD.cctmd_cut_num')
    cctmd_btn = manager.get_elem_by_name('processing.extra.CCTMD.cctmd_btn')
    # 数据拆分组件
    cutcolumnsonedatas = manager.get_elem_by_name('processing.cutcolumnsonedatas')
    ccsd_data_col = manager.get_elem_by_name('processing.extra.CCSD.ccsd_data_col')
    ccsd_cut_str = manager.get_elem_by_name('processing.extra.CCSD.ccsd_cut_str')
    ccsd_cut_suffix_first = manager.get_elem_by_name('processing.extra.CCSD.ccsd_cut_suffix_first')
    ccsd_cut_suffix_end = manager.get_elem_by_name('processing.extra.CCSD.ccsd_cut_suffix_end')
    ccsd_hold_splitter = manager.get_elem_by_name('processing.extra.CCSD.ccsd_hold_splitter')
    ccsd_btn = manager.get_elem_by_name('processing.extra.CCSD.ccsd_btn')
    # 去重组件
    deletionconditionsdatas = manager.get_elem_by_name('processing.deletionconditionsdatas')
    dcd_data_col = manager.get_elem_by_name('processing.extra.DCD.dcd_data_col')
    dcd_btn = manager.get_elem_by_name('processing.extra.DCD.dcd_btn')
    # 指定字符替换组件
    redelstrdatas = manager.get_elem_by_name('processing.redelstrdatas')
    rdsd_data_col = manager.get_elem_by_name('processing.extra.RDSD.rdsd_data_col')
    rdsd_restr = manager.get_elem_by_name('processing.extra.RDSD.rdsd_restr')
    rdsd_repstr = manager.get_elem_by_name('processing.extra.RDSD.rdsd_repstr')
    rdsd_btn = manager.get_elem_by_name('processing.extra.RDSD.rdsd_btn')
    # 字段抽取组件
    extractfieldsdatas = manager.get_elem_by_name('processing.extractfieldsdatas')
    efd_data_col = manager.get_elem_by_name('processing.extra.EFD.efd_data_col')
    efd_fieldslist = manager.get_elem_by_name('processing.extra.EFD.efd_fieldslist')
    efd_patterns_mode = manager.get_elem_by_name('processing.extra.EFD.efd_patterns_mode')
    efd_btn = manager.get_elem_by_name('processing.extra.EFD.efd_btn')
    # 数据抽取组件
    extractdatas = manager.get_elem_by_name('processing.extractdatas')
    ed_data_col = manager.get_elem_by_name('processing.extra.ED.ed_data_col')
    ed_extract_mode = manager.get_elem_by_name('processing.extra.ED.ed_extract_mode')
    ed_re_data = manager.get_elem_by_name('processing.extra.ED.ed_re_data')
    ed_index_start = manager.get_elem_by_name('processing.extra.ED.ed_index_start')
    ed_index_end = manager.get_elem_by_name('processing.extra.ED.ed_index_end')
    ed_num = manager.get_elem_by_name('processing.extra.ED.ed_num')
    ed_btn = manager.get_elem_by_name('processing.extra.ED.ed_btn')
    # 概率插入字符
    insertionlocationstrdatas = manager.get_elem_by_name('processing.insertionlocationstrdatas')
    ilsd_data_col= manager.get_elem_by_name('processing.extra.ILSD.ilsd_data_col')
    ilsd_strdict = manager.get_elem_by_name('processing.extra.ILSD.ilsd_strdict')
    ilsd_frequencydict = manager.get_elem_by_name('processing.extra.ILSD.ilsd_frequencydict')
    ilsd_insert_mode = manager.get_elem_by_name('processing.extra.ILSD.ilsd_insert_mode')
    ilsd_str_location = manager.get_elem_by_name('processing.extra.ILSD.ilsd_str_location')
    ilsd_maxsub = manager.get_elem_by_name('processing.extra.ILSD.ilsd_maxsub')
    ilsd_btn = manager.get_elem_by_name('processing.extra.ILSD.ilsd_btn')
    # 交叉合并组件
    overlappinganddatas = manager.get_elem_by_name('processing.overlappinganddatas')
    oaad_data1 = manager.get_elem_by_name('processing.extra.OAAD.oaad_data1')
    oaad_data2 = manager.get_elem_by_name('processing.extra.OAAD.oaad_data2')
    oaad_btn = manager.get_elem_by_name('processing.extra.OAAD.oaad_btn')
    # 数据替换组件
    replacedatadatas = manager.get_elem_by_name('processing.replacedatadatas')
    rdd_data_col = manager.get_elem_by_name('processing.extra.RDD.rdd_data_col')
    rdd_replace_data = manager.get_elem_by_name('processing.extra.RDD.rdd_replace_data')
    rdd_replace_to = manager.get_elem_by_name('processing.extra.RDD.rdd_replace_to')
    rdd_btn = manager.get_elem_by_name('processing.extra.RDD.rdd_btn')
    # 概率替换字符
    replacestrprobability = manager.get_elem_by_name('processing.replacestrprobability')
    rsp_data_col = manager.get_elem_by_name('processing.extra.RSP.rsp_data_col')
    rsp_strdict = manager.get_elem_by_name('processing.extra.RSP.rsp_strdict')
    rsp_rep_probability = manager.get_elem_by_name('processing.extra.RSP.rsp_rep_probability')
    rsp_rep_str = manager.get_elem_by_name('processing.extra.RSP.rsp_rep_str')
    rsp_btn = manager.get_elem_by_name('processing.extra.RSP.rsp_btn')

    process_name = manager.get_elem_by_name('processing.process_name')
    processing_overwrite = manager.get_elem_by_name('processing.processing_overwrite')
    # 文件下载
    file_downloaded = manager.get_elem_by_name('processing.file_downloaded')
    download_type = manager.get_elem_by_name('processing.download_type')
    btn_processing_download = manager.get_elem_by_name('processing.btn_processing_download')
    # 文件删除
    processing_del_button = manager.get_elem_by_name('processing.processing_del_button')

    # 外部组件
    analysis_collection_name = manager.get_elem_by_name('analysis.analysis_collection_name')
    analysis_source = manager.get_elem_by_name('analysis.analysis_source')

    processing_del_button.click(
        delete_data, 
        inputs=[user_name,processing_source,processing_collection_name],
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        )

    # 数据源下拉加载数据
    processing_source.select(
        get_droplist_check,
        inputs=[user_name,processing_source,processing_collection_name,gr.State('type'),gr.State('generated_data')],
        outputs=[processing_collection_name])
    # 元信息展示
    processing_meta_button.click(
        show_meta,
        inputs=[user_name,processing_source,processing_collection_name],
        outputs=[processing_collection_meta,processing_show_data]
    )
    # 显示数据集以及分页
    processing_data_button.click(
        show_dataset,
        inputs=[user_name,processing_source,processing_collection_name],
        outputs=[processing_collection_data,processing_show_data]
    ).then(
        show_pages,
        inputs=[user_name,processing_source,processing_collection_name],
        outputs=[processing_collection_pages]
    )
    # 分页
    processing_collection_pages.change(
        get_page_content_tab,
        inputs=[user_name,processing_source,processing_collection_name,processing_collection_pages],
        outputs=[processing_collection_data]
    )
    # 关闭显示
    processing_data_close_button.click(
        close_show,
        inputs=[gr.State(4)],
        outputs=[processing_collection_meta,processing_collection_data,processing_collection_pages,processing_show_data]
    )
    # 下载
    btn_processing_download.click(
        processing_download_file,
        inputs=[user_name, processing_source,processing_collection_name,download_type],
        outputs=[file_downloaded]
    )
    file_downloaded.clear(
        lambda : gr.update(visible=False),outputs=file_downloaded
    )
    # 功能组件显示控制
    processing_mode.select(
        show_mode,
        inputs=[processing_mode],
        outputs=[andcolumnsdatas,longcondatas,
                categoriescondata,allcolmixdatas,conditiondeldatas,
                conditiondelbooldatas,cutcolumntomanydatas,cutcolumnsonedatas,
                deletionconditionsdatas,redelstrdatas,extractfieldsdatas,
                extractdatas,insertionlocationstrdatas,overlappinganddatas,
                replacedatadatas,replacestrprobability]
    )
    # 下拉改变列名
    processing_collection_name.select(
        show_col,
        inputs=[user_name,processing_source,processing_collection_name,
                acd_data_col,ccd_data_col,lcd_data_col,
                ac_data_col,cddd_data_col,
                cddbd_data_col,cctmd_col,ccsd_data_col,
                dcd_data_col,rdsd_data_col,efd_data_col,
                ed_data_col,ilsd_data_col,oaad_data1,oaad_data2,
                rdd_data_col,rsp_data_col],
        outputs=[acd_data_col,ccd_data_col,lcd_data_col,
                ccsd_data_col,ac_data_col,
                cddd_data_col,cddbd_data_col,cctmd_col,
                dcd_data_col,rdsd_data_col,efd_data_col,
                ed_data_col,ilsd_data_col,oaad_data1,oaad_data2,
                rdd_data_col,rsp_data_col]
    )
    acd_btn.click(
        contorl_field_andcolumnsdatas,
        inputs=[user_name,processing_source,processing_collection_name,acd_data_col, acd_and_str,acd_result_type,acd_new_col,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    lcd_btn.click(
        contorl_field_longcondatas,
        inputs=[user_name,processing_source,processing_collection_name,lcd_longcondata_type,lcd_data_col, lcd_lengthrange_min, lcd_lengthrange_max,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    ccd_btn.click(
        contorl_field_categoriescondata,
        inputs=[user_name,processing_source,processing_collection_name,ccd_data_col,ccd_data_count,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    ac_btn.click(
        contorl_field_allcolmix,
        inputs=[user_name,processing_source,processing_collection_name,ac_data_col,ac_nums,ac_str_mix,ac_eve_num,ac_pre_suffix,ac_and_mode,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    cddd_btn.click(
        contorl_field_conditiondel,
        inputs=[user_name,processing_source,processing_collection_name,cddd_data_col, cddd_condition_str,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    cddbd_btn.click(
        contorl_field_conditiondelbooldatas,
        inputs=[user_name,processing_source,processing_collection_name,cddbd_data_col, cddbd_condition_str,cddbd_min_length,cddbd_max_length,cddbd_comditionsdeltype,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    cctmd_btn.click(
        contorl_field_cutcolumnsonedelmanydatas,
        inputs=[user_name,processing_source,processing_collection_name,cctmd_col, cctmd_cut_str, cctmd_cut_num,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    ccsd_btn.click(
        contorl_field_cutcolumnsonedatas,
        inputs=[user_name,processing_source,processing_collection_name,ccsd_data_col, ccsd_cut_str, ccsd_cut_suffix_first, ccsd_cut_suffix_end, ccsd_hold_splitter,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    dcd_btn.click(
        contorl_field_deletionconditionsdatas,
        inputs=[user_name,processing_source,processing_collection_name,dcd_data_col,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    rdsd_btn.click(
        contorl_field_redelstrdatas,
        inputs=[user_name,processing_source,processing_collection_name,rdsd_data_col, rdsd_restr, rdsd_repstr,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    efd_btn.click(
        contorl_field_extractfieldsdatas,
        inputs=[user_name,processing_source,processing_collection_name,efd_data_col, efd_fieldslist,efd_patterns_mode,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    ed_btn.click(
        contorl_field_extractdatas,
        inputs=[user_name,processing_source,processing_collection_name,ed_data_col, ed_extract_mode, ed_re_data, ed_num, ed_index_start, ed_index_end, ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    ilsd_btn.click(
        contorl_field_insertion_location_str,
        inputs=[user_name,processing_source,processing_collection_name,ilsd_data_col, ilsd_strdict, ilsd_frequencydict,
                ilsd_insert_mode, ilsd_str_location, ilsd_maxsub,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    oaad_btn.click(
        contorl_field_overlapping_and,
        inputs=[user_name,processing_source,processing_collection_name,oaad_data1,oaad_data2,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    rdd_btn.click(
        contorl_field_replace_data,
        inputs=[user_name,processing_source,processing_collection_name,rdd_data_col,rdd_replace_data,rdd_replace_to,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)
    rsp_btn.click(
        contorl_field_replace_list_probability,
        inputs=[user_name,processing_source,processing_collection_name,rsp_data_col, rsp_strdict, rsp_rep_probability, rsp_rep_str,ouput_df,process_name,processing_overwrite],
        outputs=[ouput_df]
    ).then(
        get_droplist_check, 
        inputs=[user_name,processing_source,processing_collection_name, gr.State('type'), gr.State('generated_data')],
        outputs=[processing_collection_name]
    ).then(get_logs, [user_name], [sys_info]
        ).success(
            get_droplist_check, 
            [user_name, analysis_source, analysis_collection_name, gr.State('type'), gr.State('generated_data')], 
            outputs=[analysis_collection_name]
            ).success(get_logs, [user_name], outputs=[sys_info], scroll_to_output=True)