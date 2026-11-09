## 2026-11-05 batch2完整协作D8对照已启动

见engineering/b1-batch2-fullflow-20261105/EXPERIMENT_REVIEW.md、runs/b1-batch2-fullflow-20261105-v1/STATUS.json。固定D前8题，serial/batch2各完整8×52，共832调用上限；两组4题交替执行顺序，原v2较长分析/256短答512工作不变，无新增Unknown或弃权规则。题内依赖/即时广播与四组保留，仅同路由跨题1/2合批。单题多分支失败隔离，单cell3道不同题失败只停该引擎，另一方式仍可继续；异常/全局预算停全部。软6000/硬6600秒+30s宽限，无重试/改cap/自动扩32。助手自审none/provisional，技术验证非独立质量等价；PID 1204037，启动不等于完成。

