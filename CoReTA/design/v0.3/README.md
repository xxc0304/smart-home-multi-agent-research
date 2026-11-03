# CoReTA v0.3 设计入口

本版为三Agent设计规范。2026-10-19采用用户指定DeepSeek Flash；49项本地测试及7项Linux容器评分检查通过，开发数学50题gold预核查通过，尚无真实模型运行，详见 [评分就绪记录](../../engineering/LINUX_SCORING_READY_20261019.md)。

## 组件和职责

- 共享状态：版本候选、初稿、请求、贡献、检查与应用记录。
- 定向帮助：主解题者输出有限动作和明确交付；两名成员均可帮忙、检查或提出替代解。
- 检查与整合：非贡献成员审查，主解题者实际应用或拒绝，不把模型支持当真值。
- 应用反馈：记录变动与剩余问题，进入下一动作或结束。
- 程序调度：只管合法动作、版本引用、调用与停止，不新增第四个语义裁判。

## 阅读与附件

1. [完整组件规格](../../refine-logs/FINAL_PROPOSAL.md)
2. [来源与复用台账](../../refine-logs/SOURCE_LEDGER.md)
3. [固定提示词](PROMPTS.md)
4. [JSON Schema](coreta.schema.json)
5. [建议运行配置](run_config.proposed.json)
6. [实验协议](../../refine-logs/EXPERIMENT_PLAN.md)
7. [执行跟踪表](../../refine-logs/EXPERIMENT_TRACKER.md)
8. [审查与修订摘要](../../refine-logs/REVIEW_SUMMARY.md)
9. [人工构造协议示例](examples/README.md)
10. [附件检查记录](DESIGN_CHECKS.md)
11. [离线贡献标注规则与空表](CONTRIBUTION_ANNOTATION.md)

## 第一版任务与运行

开发题取 GSM8K train、MBPP sanitized train；正式评价采用 MATH-500 全500题及 HumanEval/Plus 全164题。先同模型三个独立实例、无在线工具；末端评分隔离。先 E0 实现核查，再按各10题的开发试点安排真实运行，之后进入正式评价。

模型/数据/运行数属于本轮建议配置，效果尚待测。服务端、revision、依赖锁和资源批次在实施前填写，不把空配置解释成已经接入。

## 复用与自设计

MetaGPT 消息字段、AutoGen 调度分离、Blackboard 请求响应及 Debate/MoA 候选交流提供实现参考。CoReTA 的候选机制为将具体请求、实际贡献、整合变化与下一动作关联起来；不以字段本身宣称新颖。

下一步是按这些契约实现，无需另做一轮泛化规划。

2026-10-19 已补齐审查提出的贡献类型、初审解释边界和无应用记录完整提示模板，见 [补齐记录](SUPPLEMENT_20261019.md)。本版仍为设计附件，尚无真实运行或标注结果。

