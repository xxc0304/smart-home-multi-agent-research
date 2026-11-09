## 2026-11-05 T4一次加速对照结束，D32选择串行V5

见engineering/b1-batch-speed-20261105/RESULTS.md。16/16正常；串行8份48.56s/828token，batch2八份38.20s/830token，小样本时间比1.271。各自重复稳定，但1/4载荷跨执行文本/token改变（M2私人：LawSchool/1810→University/1881），不满足冻结采用门槛；测量PASS/替换REVISE，结束加速探索，按用户授权进入原串行V5完整D32分阶段批。新16生成、无训练/新C-H/付费API，非质量提升证据。助手自审none/provisional。

