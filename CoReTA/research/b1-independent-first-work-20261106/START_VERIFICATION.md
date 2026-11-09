# 实际启动核验

2026-11-06 18:22+08:00，助手自审none/provisional。

已实际启动远端runs/b1-independent-first-work-20261106-v1，PID1768230存活。START_SNAPSHOT记录运行162.08秒、24尝试/23实际返回，23全部OK、3025输出token，当时第78题/index77第一个seed的B分支。尝试比返回多1是正在生成中的请求，不当作缺失或失败。

真实工作返回已核M1 adapter启用/disabled_layers0，普通成员adapter关闭/disabled_layers252；全部batch1。不是只保存计划或启动命令。全批和B_delay完整闭环尚未结束，无成绩解释。首次状态仅用于记录/路由核验，不据阶段正确率停止或改样本。

准备证据：13CPU检查；1490真实响应回放；真实最大输入+cap10257、长实际历史压力15395<16384；冻结SHA与READY_REVIEW一致。配置、输入、离线标签、长度/预算、PREFLIGHT/FREEZE/APPROVAL及PID已下载至本目录prepared/。旧原始实验/评分未变，模型训练和C/H新评估为0。

运行不依赖笔记本或SSH窗口保持打开。无时间硬截止；有限题/seed/输出额度及失败规则仍生效。耗时粗估5–8小时，按后续完整题实测更新，非硬性结束时间。状态入口：远端项目根运行/data2/xiaoxinchen/venvs/coreta/bin/python research/b1-independent-first-work-20261106/status.py。

补充真实闭环核验：首题index77/r0五分支已COMPLETE；约447秒完成63次物理生成（64逻辑调用减1共同B上游），随后已进入r1。最新journal68实际返回全部OK。FIRST_BRANCH_INTEGRITY.json确认冻结未变、E第一次只有自身initial、第二轮恢复四名initial、后续普通工作包含新E工作；并非只通过模拟测试。早期STATUS字段在共同初答/上游阶段可能暂滞后于journal，status.py同时导出实际终态trial计数；不将一次完整题外推为全批成功或质量收益。
