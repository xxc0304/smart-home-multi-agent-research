# 三 Agent 原型实现交付

日期：2026-10-19。版本0.3.1；设计以v0.3及补充规范为依据。49项本地测试与7项Linux容器集成检查通过，Docker评分链路就绪；50题数学开发gold已通过预核查。未调用真实模型，实际API联调待完成。详见 [最新环境与核查记录](engineering/LINUX_SCORING_READY_20261019.md)。

## 本轮代码

| 文件 | 已写入职责 |
|---|---|
| src/coreta/schemas.py | Draft2020-12结构校验、引用/动作/应用关联校验、变体输出schema |
| src/coreta/state.py | 追加事件、候选版本提交、只读投影、可见引用索引 |
| src/coreta/prompts.py | 直接加载规范中的完整阶段模板；基线阶段提示 |
| src/coreta/model_client.py | DeepSeek无历史Responses请求、JSON输出、重试、deadline、原文/用量日志 |
| src/coreta/protocol.py | 三初稿、固定初审、两轮协作、检查/应用/停止、统一Finalizer及七条件 |
| src/coreta/tasks.py | 四类公开任务适配、MBPP签名提取、确定性选题及EvalPlus样本导出 |
| src/coreta/run.py | 单公开任务CLI、运行清单、独立输出目录、可选配对初稿银行 |
| src/coreta/analyze.py | 外部二元评分的题目级配对差及bootstrap区间 |
| config/deepseek_flash.json | 用户指定DeepSeek Flash的独立实际接入配置 |

三Agent均使用deepseek-flash，非思考模式；初稿各自独立，A0维护候选，A1/A2切换帮助与检查。程序没有在线代码执行或参考答案入口。DeepSeek客户端通信形态借鉴旧HomeCoord适配器，业务契约独立实现。

## 安装及入口

已在项目.venv安装可编辑包、jsonschema与Math-Verify。下列live入口尚未执行；安装复现命令保留供其他环境使用。

在CoReTA目录以Python3.11以上安装：

```powershell
python -m pip install -e .
```

入口为 `python -m coreta.run`，关键参数为 `--task <PublicTask.json> --output <新的单次运行目录> --system coreta --seed 17`。调用真实模型需要再显式传 `--live`，并沿用环境变量DEEPSEEK_API_KEY；不要把密钥写入配置、题面或日志。不要用人工示例输出作为真实模型结果。

支持条件：single_finalized、solo_refine、independent_aggregate、static_debate、coreta、generic_help、no_application_record。配对比较传入同一个 `--draft-bank <目录>`；该目录的首次请求生成初稿，后续相同题目/重复/成员/配置复用，仍按部署口径计初稿调用。共享银行按顺序使用；本轮没有跨进程并行缓存协议。

默认输入预算采用UTF-8字节数加封装余量的保守计数，可能过早触发溢出。正式冻结前应装可选依赖 `pip install -e ".[tokenizer]"`，用 `--tokenizer <本地tokenizer.json>` 指向经过确认与实际服务匹配的文件；记录路径及指纹。没有该文件时不得将保守计数描述成DeepSeek精确token计数。

每次运行写public_task.json、manifest.json、events.jsonl、requests.jsonl、responses.jsonl、parsed.jsonl及result.json；有修剪/缓存时另记context/cache日志。输入/响应日志不写Authorization头。实际response.model与usage保留；逻辑种子仅作运行关联，供应商没有在此接口接收seed，因此不宣称确定性。

## 运行与研究阶段的区别

核心代码已完成本地构造核查，含新增批量入口共47项测试；离线评分入口见 [评分说明](scoring/README.md)。无论JSON Schema合法或协议走完，都不能当作答案正确；构造测试响应不是DeepSeek真实轨迹。

后续仍需：

更新：开发数据已冻结在data/development-20261019，新增src/coreta/batch.py及tools/prepare_development.py。工程/试点两份计划仅列待运行任务，命令 `python -m coreta.batch run --plan <计划.json> --output <运行目录> --live --max-jobs 1` 才实际启动最多一个任务。当前不自动执行该命令。

1. 本地依赖、49项协议/适配/批量测试和7项Linux容器评分检查已完成；实际DeepSeek API输出兼容性待联调。
2. 开发数据和公开题面已冻结，开发50题数学gold已在Linux中预核查；正式评价数据的全量预核查仍需在正式生成前完成。
3. 接入批量任务清单、重试恢复、B3前缀分支重放、冗余贡献构造、人工标注整理及多指标统计；当前单任务Runner不会自动执行整套正式研究矩阵。
4. 上述工程就绪后，按既定E1开发批次观察真实行为，再冻结正式评价。不能把本轮实现交付等同于可以直接启动几万次正式调用。

新决策见IMPLEMENTATION_DECISIONS.md。服务端模型别名升级、保守输入计数和未执行的工程核查是当前结果解释的重要限制。


## 2026-10-19 真实联调更新

最新状态以 [准备修复与真实联调](engineering/PREPARATION_FIXES_20261019.md) 为准：52项本地检查通过；停批和tokenizer批量接入已修复；数学、代码各1题完成13次真实生成请求及Docker评分，结果分别1/0。未开展效果对照，帮助请求分支尚无真实验证。


## 2026-10-19 E1开发试点已完成

详见 [完整试点报告](engineering/DEVELOPMENT_PILOT_REPORT_20261019.md)。20题×三条件共60条轨迹、120条前后评分记录齐全。三条件逐题得分相同：数学9/10、代码8/10。59条正常完成，1条引用绑定错误降级；CoReTA实际帮助请求0。三道共同失败题存在评价一致性疑点，保留原分。先诊断任务适配与未求助原因，再决定是否修订并冻结新配置；未启动正式主实验。
