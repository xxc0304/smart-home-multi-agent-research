# 2026-11-05 三条截断请求诊断：COMPLETE

最终核验：72次尝试/返回、12分57秒，67自然EOS/5TOKEN_LIMIT，无运行异常。原batch4三失败在512复现，1024后两条结束、一条仍触顶且重复增加；batch2两种上限全部12/12 EOS，但不等于内容正确。36对增cap前缀一致、全部12条原batch4输出token复现。详细结论见RESULTS.md、POST_RUN_AUDIT.json，原始完整记录已留存，未自动重跑8/32。下文保留启动时说明。

服务器目录`/data2/xiaoxinchen/agent-research/CoReTA/runs/b1-length-diagnostic-20261105-v1`，后台PID1148442。

目标为前批题000的A/M4、B/M4、C/M3三条512 token截断请求，保留各自原四条batch的另外9条，共12固定完整输入。serial/batch2/batch4×512/1024上限，共最多72生成。提示、seed、模型/量化/采样不变；只在明示的诊断request覆盖输出上限，不改变生产B1规则、原停止批次或既有分数。

预检PASS：前批4条partial trace重放、原102条日志/attempt与三个原4请求组准确重建、12请求唯一且均普通成员工作、各计划同输入/seed、只改cap、上下文长度（最长输入+1024=4218<16384）、混合cap拒绝与空结果分析边界通过。实际RNG/路由/token对应仍在每次真实生成验证，预检不冒充本批生成结果。

预计约10–20分钟，软1800秒、硬2100秒加30秒强杀宽限，每cell软600秒，最多72。TOKEN_LIMIT是待测独立结果，记录后继续；空白/nontext/OOM/运行异常停止并保存，无重试、无新cap搜索、不自动重跑8/32或训练/新C-H。

完成后读`RESULTS.json`/`RESULTS.md`：三条在各组合下是否EOS、输出token、是否复现原batch4失败、512→1024前缀一致性、重复比例、原文及真实成本。EOS不等于语义正确，重复词面比例也不等于已证明推理循环；这不是新的团队准确率。助手自审none/provisional。

`STATUS.json`、`responses.jsonl`、`ATTEMPTS.jsonl`、`TIMINGS.json`按运行更新，服务端自动保存结果与阶段摘要。笔记本断网不影响已启动的后台进程；未设置自动聊天通知。
