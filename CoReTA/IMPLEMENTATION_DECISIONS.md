# 实现决策（先于对应代码）

日期：2026-10-19。依据v0.3及用户指定DeepSeek Flash。

| 决策 | 默认实现与理由 |
|---|---|
| 代码位置 | CoReTA/src/coreta，独立Python包，不绑定旧HomeCoord业务代码 |
| 契约 | 设计JSON Schema为唯一字段来源，使用jsonschema Draft202012Validator；避免另写一套Pydantic字段造成漂移 |
| 模型 | 三成员及Finalizer统一deepseek-flash，复用已有官方Responses端点和DEEPSEEK_API_KEY环境变量方式；旧业务schema不复用 |
| 推理与采样 | 第一版reasoning.effort=none、temperature=0.7；不发送Qwen的top_k/min_p/enable_thinking。官方说明Flash非思考top_p固定1，因此不发送旧top_p=0.8。记录logical seed但不发送未经支持的seed参数 |
| 请求 | 显式、无历史Responses调用；json_schema输出；网络仅重试超时/连接错误/429/5xx，不把400/鉴权失败当可重试 |
| 输入计数 | 接口允许注入token计数器；未配置实际tokenizer时采用UTF-8字节数加固定封装余量的保守长度估计，记录模式，不冒充真实token。可能过早溢出，正式运行前必须接入实际tokenizer并冻结 |
| 原子更新 | 整个LeadUpdate校验后才提交；模型引用只允许本次可见索引。构造视图不递归加载引用所指的历史内容 |
| 无应用消融 | 专用schema及模板；只传candidate的投影而非整个历史LeadUpdate；不提供Application历史 |
| 执行范围 | 本轮完成单任务协议、七条件、公开任务入口、运行记录和评分导出；不自动安装依赖、调用模型或执行生成代码。完整下载/评分与批量机制干预另行接入 |
| 恢复 | 单任务目录独占创建，失败不覆盖；本轮不支持半途中断的模型轨迹续跑。批量恢复按完整任务重新安排并保留旧尝试，不静默覆盖 |
| 初稿配对 | 提供可选共享draft-bank目录；按公开题面、重复、成员、配置及提示/契约指纹分键，复用仅限合法独立初稿。复用仍计部署正常调用，物理请求单独记录；不复用后续阶段 |
| 运行预算 | 正常调用和修复分别计数；最后Finalizer预留1次正常调用。整题deadline与请求deadline均生效，deadline已耗尽则直接返回最后合法artifact并标降级 |

API依据（2026-10-19检索）：https://api-docs.deepseek.com/guides/responses_api/ 与 https://api-docs.deepseek.com/api/create-response/ 。旧deepseek-v4-flash别名可能映射升级模型，实际response.model和调用日期逐次记录。

## E0与评分接入补充（2026-10-19，先于对应代码）

- 本轮用户已要求开始工程核查，使用unittest及模拟响应，不调用付费模型。依赖安装到项目.venv，记录精确安装版本。
- Math-Verify固定0.9.0，正式评分仅Linux独立进程主线程、parse/verify超时5秒。Windows仅提供明确标记的诊断模式，内部signal计时关闭、外层进程限时；不与正式分数混用。
- 金标准先独立预核查，再评分预测；预核查记录绑定原gold文件，预测不可解析记0，评分异常固定重试一次后保持score=null。
- 代码只由Docker隔离评分入口执行，固定EvalPlus0.3.1与HumanEval+ v0.1.10原数据；全量/子集均从给定本地母数据抽取，不联网下载，不修改测试。无Docker/WSL时只做命令与适配测试，不退化为宿主执行。
- Docker默认禁网、非root、只读根目录、只读输入、独立输出与临时缓存、资源限制；镜像须使用本地不可变image id或registry digest。超时停止本次创建的容器。
- MBPP开发评分单独按训练test_imports/test_list逐题容器执行，不冒充MBPP+。评分异常和断言失败分开记录。

## 环境及开发批次接入（2026-10-19）

- 用户已授权安装Docker，使用官方签名Windows包与WSL2，不自动重启。WSL自动下载失败时使用微软官方发行包；系统变更和安装结果保留单独日志。
- 开发数据下载固定已查询的HF提交，parquet用pyarrow读取，参考解/测试存evaluation，公开题面另存public；正式题面仅用于去重，不生成模型输出。50题中前3题为工程样本、前10题为E1候选，均先于结果固定。
- 批量入口默认只生成计划，不调用模型。真实批次必须指定--live及--max-jobs，按计划顺序启动有限任务；每次任务使用独立进程/目录，恢复仅跳过已有完整result.json且匹配本次输入的任务。失败记录保留，不根据得分补跑。

## Linux评分联调落实（2026-10-19）

- Docker Hub连接重置，构建改用AWS托管的Docker官方Python镜像，固定基础digest及最终镜像ID；未更换不明镜像或降低隔离参数。
- Windows正式数学入口支持--image，将题目送入独立Linux评分容器的主线程；无挂载额外工作区，仅stdin输入。开发gold可批量预核查，各题保留解析超时与错误状态。
- 验证中确认Math-Verify的TimeoutException继承BaseException，显式捕获并统一重试一次；容器总超时也重试一次，不静默记成零分。
- 49项本地测试、7项真实容器集成检查通过。构造/官方参考答案检查与模型实验结果分开，真实模型调用仍为0。


## 2026-10-19 真实联调更新

最新状态以 [准备修复与真实联调](engineering/PREPARATION_FIXES_20261019.md) 为准：52项本地检查通过；停批和tokenizer批量接入已修复；数学、代码各1题完成13次真实生成请求及Docker评分，结果分别1/0。未开展效果对照，帮助请求分支尚无真实验证。


## 2026-10-19 E1开发试点已完成

详见 [完整试点报告](engineering/DEVELOPMENT_PILOT_REPORT_20261019.md)。20题×三条件共60条轨迹、120条前后评分记录齐全。三条件逐题得分相同：数学9/10、代码8/10。59条正常完成，1条引用绑定错误降级；CoReTA实际帮助请求0。三道共同失败题存在评价一致性疑点，保留原分。先诊断任务适配与未求助原因，再决定是否修订并冻结新配置；未启动正式主实验。
