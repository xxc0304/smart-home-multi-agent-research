## 2026-11-05 T3 V5完整可读流程：PASS_READABLE_FLOW_WITH_WARNINGS

见engineering/b1-concise-readable-20261105/RESULTS.md、SUMMARY.json与FORMAT_WARNINGS.json。严格V4首题M2自然EOS/41token/28词，仅因12词硬门槛在2条后停止，保留REVISE。另冻结V5：提示/精度/采样/seed/cap不变，可读超词/多行只记警告并按完整原文评分/入历史；空白/截断/异常仍停，不抽取答案。V16请求逐项相同，复用16既有迁移结果（E6/8、B3/8，Unknown4），非新增独立资格。新6题生成312/312，正常312、完整6/6，耗时1045.54s、格式警告3、Unknown5；不能声称严格格式全通过。原32仍28完整，旧分数SHA未变，原版本/失败与源冻结存档；助手自审none/provisional，技术样本primary=false，不外推总体或机制。T2仍24/24通过，本轮总生成354，无训练/新C-H/付费API。下一步先评估格式与语义/同条件加速候选，不自动扩大批次。

