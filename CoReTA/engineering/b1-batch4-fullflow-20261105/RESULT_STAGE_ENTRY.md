## 2026-11-05 batch4完整D8试点停止：3次TOKEN_LIMIT，完整性REVISE

见engineering/b1-batch4-fullflow-20261105/RESULTS.md、STOP_AUDIT.json。第0cell约7分半、102实际尝试=102返回：99EOS/3OUTPUT_LIMIT，同题000普通M4在A/B与M3在C的第一轮分析均满512无EOS、重复/绑定混乱；触发冻结的同cell3失败停止。只访问前4题、0题四臂完整（另3题A/B两臂完成），serial及后4题未启动；这不是准确率0，不可报告完整质量或提速。无OOM/网络/输入超限/Unknown，GPU空闲。A/M4载荷与seed同于此前serial300token、batch2 412token EOS，本次batch4触顶；C/M3同载荷此前408/372 EOS。执行形状敏感性及冗长重复已观察，padding/数值/采样具体贡献未拆分。上一固定载荷仅M1/M2，M3/M4完整流程边界覆盖不足。原记录/失败和停止规则保留，未偷偷加cap重跑；助手自审none/provisional，记录完整性PASS/完整执行器REVISE。下一步只做这3条的有限同输入长度/执行路径诊断准备，再决定batch2回退或重新验证batch4；不自动全量重跑/扩32/训练/C-H。

