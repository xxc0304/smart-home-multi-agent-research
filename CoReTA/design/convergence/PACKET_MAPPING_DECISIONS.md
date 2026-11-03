# 真实状态映射决策（实现前）

- 唯一开发输入为先前A2复核使用的公开组件上下文；不加载gold、评分结果、诊断或后续检查输出。
- 完整当前artifact作为C1，candidate hash由程序重算，与原artifact/steps保持一致。
- 必需历史案例直接来自原evidence_records；每个H句柄映射原record_id+case位置，并保留原量/输入/观测，禁止推测表达式。
- 相同历史候选只存一份historical_objects；历史case的definition可引用该对象，预检必须核对对象内容和版本。无匹配原版本/hash则停止，不能用当前候选冒充旧对象。
- 当前packet保留全部活动异议、关闭理由、可见历史步骤。TaskFacts解释继续标model_asserted；case受影响约束按已有fact/item关联映射，不自动语义分析。
- 修复额度采用可共享Budget实例；组件回放是独立工程任务，可初始化0，完整流程必须注入原任务已消耗额度，不能重置。
- 本轮离线构造、结构/来源/预算验收；不生成任何模型观察，不把映射成功记为复核成功。
