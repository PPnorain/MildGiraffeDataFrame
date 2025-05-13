CSS = r"""
.duplicate-button {
  margin: auto !important;
  color: white !important;
  background: black !important;
  border-radius: 100vh !important;
}

.modal-box {
  position: fixed !important;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%); /* center horizontally */
  max-width: 1000px;
  max-height: 750px;
  overflow-y: auto;
  background-color: var(--input-background-fill);
  flex-wrap: nowrap !important;
  border: 2px solid black !important;
  z-index: 1000;
  padding: 10px;
}

.dark .modal-box {
  border: 2px solid white !important;
}

#logtext.textarea {
    color: red !important
}

.output-textarea textarea {
    class: scroll !important;
    font-size: 20px !important;

}

textarea.scroll-hide {
    overflow: scroll !important;
}

.tabselect button.selected{
    font-size: 16px !important;
    color:red !important
    
}

.json-container {
    height: 400px;
    overflow: auto !important
}

.custom-md p {
    line-height: 0.4;
    color: blue;
}

footer {visibility: hidden}

"""

JS = """document.getElementById('logtext').disabled=true"""

LOCALES = {
    "lang": {
        "en": {
            "label": "Lang"
        },
        "zh": {
            "label": "语言"
        }
    },
    "generate_method": {
        "en": {
            "label": "Generate Method"
        },
        "zh": {
            "label": "生成方法"
        }
    },
    "template_path": {
        "en": {
            "label": "Template path"
        },
        "zh": {
            "label": "自定义模板路径"
        }
    },
    "template_name": {
        "en": {
            "label": "Template name"
        },
        "zh": {
            "label": "模板名"
        }
    },
    "but_preview_template": {
        "en": {
            "value": "Preview template"
        },
        "zh": {
            "value": "预览模板"
        }
    },
    "but_close_template": {
        "en": {
            "value": "Close Preview",
        },
        "zh": {
            "value": "关闭模板预览",
        }
    },
    "seed_path": {
        "en": {
            "label": "Seed Path"
        },
        "zh": {
            "label": "种子文件路径"
        }
    },
    "seed_name": {
        "en": {
            "label": "Seed Name"
        },
        "zh": {
            "label": "种子文件名"
        }
    },
    "template": {
        "en": {
            "label": "Prompt template",
            "info": "The template used in constructing prompts."
        },
        "zh": {
            "label": "提示模板",
            "info": "构建提示词时使用的模板"
        }
    },
    "booster": {
        "en": {
            "label": "Booster"
        },
        "zh": {
            "label": "加速方式"
        }
    },
    "training_stage": {
        "en": {
            "label": "Stage",
            "info": "The stage to perform in training."
        },
        "zh": {
            "label": "训练阶段",
            "info": "目前采用的训练方式。"
        }
    },
    "deepspeed_config_path": {
        "en": {
            "label": "deepspeed_config_path",
            "info": "The path to deepspeed config."
        },
        "zh": {
            "label": "deepspeed配置文件路径",
            "info": "deepspeed配置文件路径。"
        }
    },
    "dataset_dir": {
        "en": {
            "label": "Data dir",
            "info": "Path to the data directory."
        },
        "zh": {
            "label": "数据路径",
            "info": "数据文件夹的路径。"
        }
    },
    "dataset": {
        "en": {
            "label": "Dataset"
        },
        "zh": {
            "label": "数据集"
        }
    },
    "btn_preview_seed": {
        "en": {
            "value": "Preview seed"
        },
        "zh": {
            "value": "预览种子数据"
        }
    },
    "preview_count_seed": {
        "en": {
            "label": "Count"
        },
        "zh": {
            "label": "数量"
        }
    },
    "page_index_seed": {
        "en": {
            "label": "Page"
        },
        "zh": {
            "label": "页数"
        }
    },
    "prev_btn_seed": {
        "en": {
            "value": "Prev"
        },
        "zh": {
            "value": "上一页"
        }
    },
    "next_btn_seed": {
        "en": {
            "value": "Next"
        },
        "zh": {
            "value": "下一页"
        }
    },
    "close_btn_seed": {
        "en": {
            "value": "Close"
        },
        "zh": {
            "value": "关闭"
        }
    },
    "preview_samples_seed": {
        "en": {
            "label": "Samples"
        },
        "zh": {
            "label": "样例"
        }
    },
    "btn_preview_template": {
        "en": {
            "value": "Preview Template"
        },
        "zh": {
            "value": "预览模板"
        }
    },
    "preview_count_template": {
        "en": {
            "label": "Count"
        },
        "zh": {
            "label": "数量"
        }
    },
    "page_index_template": {
        "en": {
            "label": "Page"
        },
        "zh": {
            "label": "页数"
        }
    },
    "prev_btn_template": {
        "en": {
            "value": "Prev"
        },
        "zh": {
            "value": "上一页"
        }
    },
    "next_btn_template": {
        "en": {
            "value": "Next"
        },
        "zh": {
            "value": "下一页"
        }
    },
    "close_btn_template": {
        "en": {
            "value": "Close"
        },
        "zh": {
            "value": "关闭"
        }
    },
    "preview_samples_template": {
        "en": {
            "label": "Samples"
        },
        "zh": {
            "label": "样例"
        }
    },
    "btn_login": {
        "en": {
            "value": "Log In",
        },
        "zh": {
            "value": "登录",
        }
    },
    "btn_logout": {
        "en": {
            "value": "Log Out",
        },
        "zh": {
            "value": "登出",
        }
    },
    "user_name": {
        "en": {
            "label": "User Name",
        },
        "zh": {
            "label": "用户名",
        }
    },
    "evaluation_steps": {
        "en": {
            "label": "Evaluation steps",
            "info": "Evaluate steps."
        },
        "zh": {
            "label": "测试间隔",
            "info": "每两次测试之间的间隔步数。"
        }
    },
    "eval_method": {
        "en": {
            "label": "Evaluation Method",
            "info": "Method used to evaluate."
        },
        "zh": {
            "label": "评测方法",
            "info": "用于测试模型的评测标准。"
        }
    },
    "num_train_epochs": {
        "en": {
            "label": "Epochs",
            "info": "Total number of training epochs to perform."
        },
        "zh": {
            "label": "训练轮数",
            "info": "需要执行的训练总轮数。"
        }
    },
    "max_samples": {
        "en": {
            "label": "Max samples",
            "info": "Maximum samples per dataset."
        },
        "zh": {
            "label": "最大样本数",
            "info": "每个数据集最多使用的样本数。"
        }
    },
    "compute_type": {
        "en": {
            "label": "Compute type",
            "info": "Whether to use fp16 or bf16 mixed precision training."
        },
        "zh": {
            "label": "计算类型",
            "info": "是否启用 FP16 或 BF16 混合精度训练。"
        }
    },
    "batch_size": {
        "en": {
            "label": "Batch size",
            "info": "Number of samples to process per GPU."
        },
        "zh":{
            "label": "批处理大小",
            "info": "每块 GPU 上处理的样本数量。"
        }
    },
    "gradient_accumulation_steps": {
        "en": {
            "label": "Gradient accumulation",
            "info": "Number of gradient accumulation steps."
        },
        "zh": {
            "label": "梯度累积",
            "info": "梯度累积的步数。"
        }
    },
    "lr_scheduler_type": {
        "en": {
            "label": "LR Scheduler",
            "info": "Name of learning rate scheduler.",
        },
        "zh": {
            "label": "学习率调节器",
            "info": "采用的学习率调节器名称。"
        }
    },
    "max_grad_norm": {
        "en": {
            "label": "Maximum gradient norm",
            "info": "Norm for gradient clipping.."
        },
        "zh": {
            "label": "最大梯度范数",
            "info": "用于梯度裁剪的范数。"
        }
    },
    "val_size": {
        "en": {
            "label": "Val size",
            "info": "Proportion of data in the dev set."
        },
        "zh": {
            "label": "验证集比例",
            "info": "验证集占全部样本的百分比。"
        }
    },
    "extra_tab": {
        "en": {
            "label": "Extra configurations"
        },
        "zh": {
            "label": "其它参数设置"
        }
    },
    "logging_steps": {
        "en": {
            "label": "Logging steps",
            "info": "Number of steps between two logs."
        },
        "zh": {
            "label": "日志间隔",
            "info": "每两次日志输出间的更新步数。"
        }
    },
    "save_steps": {
        "en": {
            "label": "Save steps",
            "info": "Number of steps between two checkpoints."
        },
        "zh": {
            "label": "保存间隔",
            "info": "每两次断点保存间的更新步数。"
        }
    },
    "warmup_steps": {
        "en": {
            "label": "Warmup steps",
            "info": "Number of steps used for warmup."
        },
        "zh": {
            "label": "预热步数",
            "info": "学习率预热采用的步数。"
        }
    },
    "neftune_alpha": {
        "en": {
            "label": "NEFTune Alpha",
            "info": "Magnitude of noise adding to embedding vectors."
        },
        "zh": {
            "label": "NEFTune 噪声参数",
            "info": "嵌入向量所添加的噪声大小。"
        }
    },
    "train_on_prompt": {
        "en": {
            "label": "Train on prompt",
            "info": "Compute loss on the prompt tokens in supervised fine-tuning."
        },
        "zh": {
            "label": "计算输入损失",
            "info": "在监督微调时候计算输入序列的损失。"
        }
    },
    "upcast_layernorm": {
        "en": {
            "label": "Upcast LayerNorm",
            "info": "Upcast weights of layernorm in float32."
        },
        "zh": {
            "label": "缩放归一化层",
            "info": "将归一化层权重缩放至 32 位浮点数。"
        }
    },
    "lora_tab": {
        "en": {
            "label": "LoRA configurations"
        },
        "zh": {
            "label": "LoRA 参数设置"
        }
    },
    "lora_rank": {
        "en": {
            "label": "LoRA rank",
            "info": "The rank of LoRA matrices."
        },
        "zh": {
            "label": "LoRA 秩",
            "info": "LoRA 矩阵的秩。"
        }
    },
    "lora_dropout": {
        "en": {
            "label": "LoRA Dropout",
            "info": "Dropout ratio of LoRA weights."
        },
        "zh": {
            "label": "LoRA 随机丢弃",
            "info": "LoRA 权重随机丢弃的概率。"
        }
    },
    "lora_target": {
        "en": {
            "label": "LoRA modules (optional)",
            "info": "Name(s) of target modules to apply LoRA. Use commas to separate multiple modules."
        },
        "zh": {
            "label": "LoRA 作用模块（非必填）",
            "info": "应用 LoRA 的目标模块名称。使用英文逗号分隔多个名称。"
        }
    },
    "additional_target": {
        "en": {
            "label": "Additional modules (optional)",
            "info": "Name(s) of modules apart from LoRA layers to be set as trainable. Use commas to separate multiple modules."
        },
        "zh": {
            "label": "附加模块（非必填）",
            "info": "除 LoRA 层以外的可训练模块名称。使用英文逗号分隔多个名称。"
        }
    },
    "create_new_adapter": {
        "en": {
            "label": "Create new adapter",
            "info": "Whether to create a new adapter with randomly initialized weight or not."
        },
        "zh": {
            "label": "新建适配器",
            "info": "是否创建一个经过随机初始化的新适配器。"
        }
    },
    "rlhf_tab": {
        "en": {
            "label": "RLHF configurations"
        },
        "zh": {
            "label": "RLHF 参数设置"
        }
    },
    "dpo_beta": {
        "en": {
            "label": "DPO beta",
            "info": "Value of the beta parameter in the DPO loss."
        },
        "zh": {
            "label": "DPO beta 参数",
            "info": "DPO 损失函数中 beta 超参数大小。"
        }
    },
    "reward_model": {
        "en": {
            "label": "Reward model",
            "info": "Adapter of the reward model for PPO training. (Needs to refresh adapters)"
        },
        "zh": {
            "label": "奖励模型",
            "info": "PPO 训练中奖励模型的适配器路径。（需要刷新适配器）"
        }
    },
    "cmd_preview_btn": {
        "en": {
            "value": "Preview command"
        },
        "zh": {
            "value": "预览命令"
        }
    },
    "start_btn": {
        "en": {
            "value": "Start"
        },
        "zh": {
            "value": "开始"
        }
    },
    "stop_btn": {
        "en": {
            "value": "Abort"
        },
        "zh": {
            "value": "中断"
        }
    },
    "output_dir": {
        "en": {
            "label": "Output dir",
            "info": "Directory for saving results."
        },
        "zh": {
            "label": "输出目录",
            "info": "保存结果的路径。"
        }
    },
    "overwrite_output_dir": {
        "en": {
            "label": "overwrite output_dir",
            "info": "Chose weather overwrite output dir."
        },
        "zh": {
            "label": "是否重写输出目录",
            "info": "勾选则覆写输出目录。"
        }
    },
    "output_box": {
        "en": {
            "value": "Ready."
        },
        "zh": {
            "value": "准备就绪。"
        }
    },
    "loss_viewer": {
        "en": {
            "label": "Loss"
        },
        "zh": {
            "label": "损失"
        }
    },
    "predict": {
        "en": {
            "label": "Save predictions"
        },
        "zh": {
            "label": "保存预测结果"
        }
    },
    "load_btn": {
        "en": {
            "value": "Load model"
        },
        "zh": {
            "value": "加载模型"
        }
    },
    "unload_btn": {
        "en": {
            "value": "Unload model"
        },
        "zh": {
            "value": "卸载模型"
        }
    },
    "info_box": {
        "en": {
            "value": "Model unloaded, please load a model first."
        },
        "zh": {
            "value": "模型未加载，请先加载模型。"
        }
    },
    "system": {
        "en": {
            "placeholder": "System prompt (optional)"
        },
        "zh": {
            "placeholder": "系统提示词（非必填）"
        }
    },
    "query": {
        "en": {
            "placeholder": "Input..."
        },
        "zh": {
            "placeholder": "输入..."
        }
    },
    "generate_output": {
        "en": {
            "label": "output file name"
        },
        "zh": {
            "label": "存储文件名"
        }
    },
    "generate_number": {
        "en": {
            "label": "generate number"
        },
        "zh": {
            "label": "数量"
        }
    },
    "btn_checkconfig": {
        "en": {
            "value": "Check Config"
        },
        "zh": {
            "value": "检查配置"
        }
    },
    "btn_generate": {
        "en": {
            "value": "Generate"
        },
        "zh": {
            "value": "生成"
        }
    },
    "btn_interrupt": {
        "en": {
            "value": "interrupt"
        },
        "zh": {
            "value": "中断"
        }
    },
    "top_p": {
        "en": {
            "label": "Top-p"
        },
        "zh": {
            "label": "Top-p 采样值"
        }
    },
    "temperature": {
        "en": {
            "label": "Temperature"
        },
        "zh": {
            "label": "温度系数"
        }
    },
    "api_type": {
        "en": {
            "label": "API Type"
        },
        "zh": {
            "label": "API类型"
        }
    },
    "api_base": {
        "en": {
            "label": "API Base"
        },
        "zh": {
            "label": "API地址"
        }
    },
    "api_key": {
        "en": {
            "label": "API Key"
        },
        "zh": {
            "label": "API密钥"
        }
    },
    "deployment_name": {
        "en": {
            "label": "depolyment name"
        },
        "zh": {
            "label": "部署名"
        }
    }
}

ALERTS = {
    "err_conflict": {
        "en": "A process is in running, please abort it firstly.",
        "zh": "任务已存在，请先中断训练。"
    },
    "err_exists": {
        "en": "You have loaded a model, please unload it first.",
        "zh": "模型已存在，请先卸载模型。"
    },
    "err_no_template": {
        "en": "Please select a template.",
        "zh": "请选择模板。"
    },
    "err_no_seed": {
        "en": "Please select a seed file.",
        "zh": "请选择种子模板"
    },
    "err_no_dataset": {
        "en": "Please choose a dataset.",
        "zh": "请选择数据集。"
    },
    "err_no_adapter": {
        "en": "Please select an adapter.",
        "zh": "请选择一个适配器。"
    },
    "err_no_export_dir": {
        "en": "Please provide export dir.",
        "zh": "请填写导出目录"
    },
    "err_failed": {
        "en": "Failed.",
        "zh": "训练出错。"
    },
    "err_demo": {
        "en": "Training is unavailable in demo mode, duplicate the space to a private one first.",
        "zh": "展示模式不支持训练，请先复制到私人空间。"
    },
    "info_aborting": {
        "en": "Aborted, wait for terminating...",
        "zh": "训练中断，正在等待线程结束……"
    },
    "info_aborted": {
        "en": "Ready.",
        "zh": "准备就绪。"
    },
    "info_finished": {
        "en": "Finished.",
        "zh": "生成完毕。"
    },
    "info_loading": {
        "en": "Loading model...",
        "zh": "加载中……"
    },
    "info_unloading": {
        "en": "Unloading model...",
        "zh": "卸载中……"
    },
    "info_loaded": {
        "en": "Model loaded, now you can chat with your model!",
        "zh": "模型已加载，可以开始聊天了！"
    },
    "info_unloaded": {
        "en": "Model unloaded.",
        "zh": "模型已卸载。"
    },
    "info_exporting": {
        "en": "Exporting model...",
        "zh": "正在导出模型……"
    },
    "info_exported": {
        "en": "Model exported.",
        "zh": "模型导出完成。"
    }
}