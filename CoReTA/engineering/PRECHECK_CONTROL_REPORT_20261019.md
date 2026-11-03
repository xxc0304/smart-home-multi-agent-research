# 603同配置旧式B/C/U控制

## 实现与验收

新增`src/coreta/precheck.py`和独立入口`coreta.run_precheck`，使用同一v0.5 Candidate、模型配置、4096输出上限、初稿提示词与直接导出规则。检查阶段置于应用前，检查贡献与当前候选；A0应用时可直接提交关闭，之后没有候选复核。

只有inspect/apply阶段提示词因检查对象和关闭权限变化而对应调整，完整保存于`design/precheck_prompts.json`；这比较的是B/C/U及单方关闭与B/U/C及复核关闭的整体协议，不是只交换调用次序的纯消融。

新增3项检查：B/C/U顺序与直接导出、A0可在检查提出异议后提交关闭、初稿生成提示词/配置与后置复核一致。完整110项检查通过，见`PRECHECK_ENGINEERING_TESTS_20261019.txt`。

## 冻结运行与结果

计划`PRECHECK_CALIBRATION_PLAN_20261019.json`先于调用冻结，复用v0.5校准三份全错初稿，逐份payload哈希一致；无重跑或限额修改。

|条件|最终分数|正常调用|新增HTTP|修复|截断|
|---|---:|---:|---:|---:|---:|
|原v0.5 B/U/C，已见校准|1|10|11|1|0|
|本次同配置B/C/U控制|0|7|4|0|0|

控制run为`coreta-precheck-2e9561ba6ac8`，正常complete，离线Docker评分AssertionError。其交付从[1..n]开始，k=1的整表筛除立即清空列表，不能产生期望序列；并非运行故障。

预检查者也给出多处错误手工推演，A0关闭两个问题后交付。不能概括为“所有正确修复已经存在、只因关闭权限而失败”。后置复核版本实际多用一轮工作，正常调用10而非7；提前结束差异可能属于协议效应，但该单次轨迹不能将额外推理与检查顺序的作用完全分开。

## 证据力度

新控制减少了旧版2048截断、自由final、初稿变化等混杂项；本例仍观察到新协议成功、控制失败。它是已见任务上的一次机制诊断，模型生成仍随机、角色知识和后续贡献不同、未同时预先冻结原成功轨迹，因此不是一般性因果结论或成本优势。

两入口的result.system都沿用coreta_revision，聚合必须以计划条件/入口来源区分precheck和postcheck，不能按该字段混为同一条件。当前文件/目录和计划已明确分开，后续批次汇总须显式带condition字段。

原始轨迹`runs/precheck-calibration-20261019/coreta_revision/`，评分与汇总`PRECHECK_CALIBRATION_SUMMARY_20261019.json`。来源分析见`603_CONTRIBUTION_PROVENANCE_20261019.md`。
