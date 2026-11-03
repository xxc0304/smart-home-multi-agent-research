# RTX3090实机预检审核（2026-11-03）

## 结论

技术预检PASS；正式B0启动准备REVISE/DO_NOT_RUN，先完成该批配置和预算。此次为主助手本地两轮自审，review_independence=none，acceptance_status=provisional；没有委托新的独立研究评审。此前fresh代理只复现GPU/template命令，不是科研或全训练审核。

## 审核证据

直接读取服务器原始配置、longest_step/ten_steps的training_status.json、adapter/b0_origin.json、RELOAD_CHECK.json、OOM日志和B0/B1测试日志；重新计算TECHNICAL_FREEZE列出的4项，配置/训练源码/入口/训练数据全部匹配。未重跑训练或访问C/H正文。

- 模型：固定Qwen3-4B revision，已有三分片官方大小/SHA256检查。审查未重新下载或重复哈希8GB权重。
- 全1796训练及200V模板检查：无截断、loss前缀对齐；最长7326/5012。31工程检查的原日志确为9+22、全部OK。
- 最长样本1步：COMPLETE，9.00秒总流程/5.86秒训练，peak_allocated19.05GiB；原始日志确有分配器OOM警告，但没有抛出Python OOM或退出失败，loss与梯度有限，adapter已保存。
- 10步：COMPLETE，37.91秒总流程/22.63秒训练，peak_allocated13.52GiB，数值有限；来源文件明确purpose=technical_preflight、technical_steps=10。
- 真实adapter重载：有限logits、合成提示生成10token成功，未测MuSiQue准确率。代码明确拒绝将technical adapter用于真实E资格生成。
- GPU现已空闲。没有把技术产物作为专家，没有C资格或团队真实成绩。

## 发现及最小处理

1. **正式启动前必须处理：正式配置/预算尚未冻结。** 当前reviewed_for_run=true只绑定technical_preflight和1800秒，不能直接去掉--technical-steps就当正式运行。另建purpose=expert_training的批次配置，登记1epoch、有效batch、wall预算、候选次序和V选模；原技术配置与输出保留。最多两次主要尝试，C不调参。
2. **显存余量限制：不能从单步成功宣布整轮稳定。** peak_allocated是PyTorch活跃分配峰值，不是总占用或reserved峰值。最长样本已发生分配器恢复警告，正式批次保留OOM即停并记录实际allocator状态；如调整allocator/attention/量化等实际执行设置，须做受影响的有限技术复验，不能暗改为原测试已覆盖。当前没有证据要求更换模型、截断长题或重开数据清洗。
3. **V生成验收尚缺，限评价准备。** 合成Say OK重载测试没有经过真实b0_training.generate的TASK_DATA输入、64token/EOS终止和OUTPUT_LIMIT路径，也没有V真实吞吐记录。正式V/C评价前，用V中事先固定的短前缀做有限技术测试，原输出保留、计入开发暴露，统一B/E模板和推理设置；不能从合成生成推断实际任务质量。训练若单独启动，应明确其后V评价仍有这一准备依赖。
4. **时间外推只作预算估计。** 68分钟来自10步训练循环速度线性外推1796步，并非整轮实测，未含完整V生成。不要承诺一小时完成专家或将10步不同样本的loss下降当效果。

## 两轮自审处置

第一轮核对报告与日志，聚焦OOM和实际训练终态。第二轮比对冻结内容及生成入口，确认未发生配置漂移，补明确技术配置不能直接复用为正式批次，合成生成不替代V路径。未发现需否定已有工程结果的实质错误；不新增理论、全库清洗或查新。

## 下一步与主张边界

允许推进：有限V技术验收、正式B0候选/预算登记及启动审核。当前研究仍是构造真实任务优势成员后研究团队利用/损害与有益纠错，环境搭建没有替代研究中心。

允许声称：这台3090能够执行该固定4B/NF4配置的已测训练步和adapter重载。不能声称：专家已建立、准确率提升、完整训练稳定、团队有效或论文假设获支持。

本轮无新增GPU训练/API费用。审核文件及现行交接已同步服务器。
