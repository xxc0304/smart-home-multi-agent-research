## 2026-11-05 三条截断请求的长度/执行形状诊断已启动

见engineering/b1-length-diagnostic-20261105/EXPERIMENT_REVIEW.md、runs/b1-length-diagnostic-20261105-v1/STATUS.json。原3失败请求及各自同批9条共12固定真实载荷，保持提示/seed/模型，512/1024×serial/batch2/batch4，共72上限。仅显式诊断cap覆盖，不改原B1合同/停止分数。软1800/硬2100秒+30s宽限，token触顶记录继续独立请求、异常停止，无重试/新cap搜索/自动重跑8或32/训练/C-H。PID 1148442，助手自审none/provisional，启动不等于完成。

