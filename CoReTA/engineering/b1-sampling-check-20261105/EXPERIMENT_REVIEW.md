# T2 随机采样核验：24次固定技术生成

2026-11-05，助手自审none/provisional。目标是核查同底座普通成员高同答是否来自采样/seed/adapter隔离失效，不强迫答案不同，不估计任务成绩。用户已授权按下一步继续。

科学意义PASS：既有28完整题普通三人23题逐字同答，不能仅用不同seed声明证明后端有效。先重放原32记录、检查种子/路由和错误相关性，再在既有V前2题做B/E×3seed×2原样重复，恰好24次。seed固定20261102/20261103/20261104；每题每seed顺序B,E,B,E，检查E调用前后底座恢复。不按得分选题/seed；不读新C/H、不训练、不改温度/精度/提示。原V2短答256合同。B使用M2关闭adapter，E使用M1启用adapter。重复不是独立新任务。

执行准备：prepare必须完成32轨迹重放、原评分事件的相关性摘要、全部24实际载荷token长度、当前GPU空闲、现有本地权重/adapter身份元数据与旧配置一致。冻结script、review、requests、config、b1_runtime/b1_controls/b1_stop_status、旧manifest/scores/backend哈希；任何变化拒绝run。APPROVAL.json绑定FREEZE哈希且两项PASS后才执行，准备阶段未完成时DO_NOT_RUN。

只读hook原LocalBackend.respond的实际model.generate与torch.multinomial，记录生效解码配置、实际LoRA层disable标记、每次首4步过滤后概率top5/熵、RNG状态hash、全部采样token及输出token hash；不替换概率或采样结果。此hook有同步开销，本次耗时不是加速基准。stdout只打印进度/摘要，完整输出落盘。

预算/失败：包含加载600秒软预算，外部timeout900秒硬预算；最多24次，无重试。技术异常立即保存并停；累计2条非OK响应停止；任一依赖无效不作正常结果。每次先追加原响应，finally写汇总；硬终止时日志/响应仍保留，不能称完整。GPU资源被其他计算占用则不运行。

验收：24完整、真实multinomial实际调用、do_sample/.7/.95/top_k0生效、所有层B禁用/E启用、不同seed首步RNG状态不同、相同seed的RNG状态复现；输出完全重复是诊断字段而非强行通过门槛（CUDA数值非确定性可另解释）。相同答案可由集中分布产生；两题不能证明全部语义同质的唯一原因，也不倒推原32曾记录不存在的RNG证据。原32/28与分数不变。

预检修正：v1准备记录的max_input_tokens=2是当前分词器默认返回映射时len(mapping)而非token数，审核发现后未放行、零生成。v2显式return_dict=False，与真实后端一致，并断言整数token列表/非空长度；旧准备记录保留并标DO_NOT_RUN。

总体启动结论：条件门槛。prepare产物和GPU检查通过后写本批APPROVAL、RUN_ALLOWED；本文件本身不直接放行。无新付费API。
