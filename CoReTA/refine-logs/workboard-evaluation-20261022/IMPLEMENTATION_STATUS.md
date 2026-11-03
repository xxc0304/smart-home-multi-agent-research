> 更新：2026-10-22 已完成冻结版本真实试跑，CoReTA 6/8、普通讨论 5/8，334 HTTP。详见 HIDDENBENCH_DEVELOPMENT_RESULTS_20261022.md。以下保留实验前实现记录。

# HiddenBench四题开发适配状态

日期：2026-10-22。本轮只实现和离线验证，没有调用解题模型。基准提交00338a49953246eaeff582e1a16f4c2959b77374，工作区已有未提交研究文件。决策先记入workboard-v3/implement-stage/ASSUMPTIONS.md A44–A49。

## 已落实

- 固定开发ID1/4/34/50，原生成员4/3/3/3；原description/shared_information和每成员hidden_information保留，选项按固定题ID打乱、映射独立保存。
- 模型输入匿名task ID、统一title，不含源name、correct_answer、rationale或源路径。原题语义中地名/选项保留，不删除任务事实。
- ChoiceAdapter使用单个option_N或null；完整合法选项才能交付。ChoicePackets严格检查原件范围及索引。
- 普通讨论支持3/4成员，5/6轮同步解题加最终提交；CoReTA后续16/25调用，两法总输出上限40448/61440。初稿真实共享，不按答案挑选。
- Board明确not_collected与collected；未采集仍用兼容空列表，并在可见输入解释其不是“没用资料”的证据。不填造来源，也不放宽引用权限。
- 新choice_experiment准备与显式运行入口，独立离线评分工具。运行路径不读取offline评价答案。单体参照独立一步INITIAL，提供全部资料或仅共享资料，不接收团队输出。

## 证据与边界

225项离线检查通过，0失败/错误/跳过；真实HTTP0。证据：runs/hiddenbench-development-offline-20261022-r1/summary.json及unittest.log。

其中10项新增检查包含完整334次脚本批次、三/四成员的完整周期、共享初稿、输入无原题名/答案字段、runtime禁止读取offline答案、首技术异常停批、准备输入篡改拒绝和独立评分。脚本产物明确不是模型能力结果。

最终准备包：runs/hiddenbench-development-prepared-20261022-r2/。共4题×2重复×2方法=16团队单元，26次共享初答、292次后续协作上限，另16次独立参照，合计最大334请求。r1为修改中准备包，保留但不执行；r2按最终代码重新冻结。

## 尚未通过的门槛

独立同家族代码/假设复核已恢复完成，未发现阻断项，结论为provisional；详见HIDDENBENCH_READINESS_REVIEW.md。尚未做真实服务兼容或自然端到端试跑，因此离线通过不保证无格式异常。Schedule、请求式黑板、全披露基线、53题正式评价均未实施/未启动。

下一步先完成独立复核、修复具体发现，再按冻结配置开展有界自然试跑。首技术异常停批，低分不重跑；不得用四题开发结果宣称一般优势。
