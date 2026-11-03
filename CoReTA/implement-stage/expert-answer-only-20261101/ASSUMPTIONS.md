# 假设与选择（编码前）

ASK=never；用户已授权补齐离线流程，真实模型/硬件选择待预检。

| ID | 未定项 | 选择 | Class | Source |
|---|---|---|---|---|
| A01 | 执行库 | HF Transformers+PEFT，单设备LoRA/可选4bit；隔离.venv-expert，不改旧环境 | interface | default |
| A02 | 答案提取 | 去首尾空白及一个固定Answer:或答案:前缀，其余全文视为短答案；不按gold择片段；EM/F1用官方metric/别名 | semantic | default |
| A03 | loss边界 | tokenizer完整模板与生成前缀须token精确对齐，只有assistant答案及结束token受监督；右padding=-100；不截断 | semantic | default |
| A04 | 推理 | 首轮V/C固定greedy、max_new_tokens=64、每题重设seed20261102；thinking由实际模板显式配置，对B/E相同 | semantic | default |
| A05 | 统计 | C按既有子问题/支持/上下文关联元数据固定组，10000次组配对bootstrap、seed20261102、95%百分位；附逐题区间，少组警示不作强资格 | semantic | default |
| A06 | 失败 | 无静默重试；独立题允许记录失败继续；预算耗尽保留不完整，不宣布资格；不把技术缺失记语义错 | semantic | default |
| A07 | 停止预算 | 每次真实训练/生成必须填有限walltime；OOM/非有限loss停止保存；配置未齐拒运行 | interface | default |
| A08 | 模型和数据 | 本地显式模型路径、revision、精度/量化/长度/target_modules待填；禁隐式下载/remote code；新答案数据固定1796/200，C160一次不自动扩样 | semantic | user |
| A09 | CPU核验 | 本地随机tiny模型/tokenizer训练fixture检查adapter更新/保存加载；全部标FIXTURE，无Qwen兼容或任务能力主张 | semantic | default |
| A10 | V选模 | 预登记候选按EM→F1→较早登记顺序，只从完整、同条件V报告选；不以C选模 | semantic | user |

## 实现时识别的补充选择（首次编码后记录，保留时点）

| ID | 未定项 | 选择 | Class | Source |
|---|---|---|---|---|
| A11 | 最小训练附属超参 | microbatch1、AdamW训练库默认、constant LR、warmup0、weight_decay0、dropout0、clip1；只保留终态adapter，不用训练loss挑候选 | semantic | default |
| A12 | 关联精度提示 | 少于10组或最大组超过半数时不自动宣布资格，报告区间并要求精度复核；当前C139组/最大4，不触发 | semantic | default |
| A13 | 短步adapter | technical-steps或fixture产物不可作为真实专家C候选，训练purpose写入来源 | semantic | default |
| A14 | 生成结束 | 无结束符达到长度/时间限制标OUTPUT_LIMIT；不完整无主比较；OOM停止受影响批，其他独立错误记录后继续，无重试 | semantic | default |
| A15 | 软件验证边界 | CPU实测版本记录单独lock；GPU的CUDA/4bit依实机，不安装CPU lock到GPU机 | interface | default |

| A16 | 统计组权重 | 抽关联组、带入组内全部题，bootstrap每次按抽中题数加权；非每组等权平均 | semantic | sweep |
| A17 | 候选顺序契约 | select仅1–2个终态候选，调用者按训练前登记顺序传入reports；无全局作业平台，顺序是操作合同而非文件时间推断 | interface | sweep |
| A18 | wall边界 | step开始与最后step结束均验训练预算，计算步可能越界但不宣称完成候选；adapter保存时间另计。生成max_time为软截止，没结束符记OUTPUT_LIMIT | interface | sweep |

| A19 | 机器资格标志 | 只在真实完整C且EM差>0、组95%区间下界>0、无精度警示时标SUPPORTED_TASK_ADVANTAGE；F1辅助；5–10pp非代码硬线，实用价值仍人工解释 | semantic | sweep |
