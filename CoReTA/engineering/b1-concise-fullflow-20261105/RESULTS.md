# T2/T3 实际执行结果

2026-11-05，助手自审none/provisional。已按NEXT_TASKS顺序执行采样核验、V独答迁移、历史失败完整团队技术验证。

| 批次 | 实际/计划请求 | 正常响应 | 耗时（含加载） | 判定 |
|---|---:|---:|---:|---|
| T2随机后端 | 24/24 | 24 | 24.65s | PASS_TECHNICAL_ONLY |
| T3 V前8题双路 | 16/16 | 16 | 17.55s | PASS_TECHNICAL_ONLY |
| T3六题完整四组 | 2/312 | 1 | 10.37s | REVISE |

T2：真实multinomial与生成token逐项一致，252个LoRA层开关正确；不同seed随机状态不同，12对原样重复逐token相同。两题底座跨seed仍同答，专家一题有措辞变体，不能将同答判为实现故障。旧28题普通三人对错向量相同（3对25错，phi=1），是高度相关的同底座弱成员，不是独立证据，也不能外推一般异构团队。

新合同：所有成员/四臂，初/终答单行≤12词cap128，工作≤120词cap768，两轮不变；EOS和格式分开，超限保留全文并失败，不截取答案。Unknown合法但按未答对报告。V16中Unknown 4份；M1答对6/8，M2答对3/8，只是同合同下8题开发观察，不是新独立资格或与旧V20的配对效果。未以分数选提示。

32项B1回归通过，原32真实轨迹重放和评分复算完全一致。旧源码与已完成T2的冻结源码在更新前存档（T2/SOURCE_ARCHIVE.json），旧准备失败v1保留REJECTED（0生成）。

六题固定原索引9/13/16/22四个历史失败+0/1正常对照，按该顺序，原题/seed/说话顺序保留。完整流程尚未通过；末条请求{'request_id': '2hop__342640_126084|01', 'actor': 'M2', 'stage': 'initial', 'arm': None, 'status': 'FORMAT_VIOLATION', 'usage': {'input_tokens': 4111, 'output_tokens': 41, 'elapsed_seconds': 2.461280470000929, 'adapter_enabled': False, 'finish_reason': 'EOS', 'output_cap': 128, 'ended_with_eos': True, 'peak_allocated_bytes': 3968050176, 'peak_reserved_bytes': 4383047680, 'format_violation': 'WORD_LIMIT'}}。已按冻结规则停止，未自动换提示/补跑。已完整0/6题；本批Unknown 0份；实际最大词数{'initial': 28, 'work': 0, 'final': 0}。这是历史失败选择的技术样本，不能用于估计总体准确率或证明新提示更优；自动评分primary_enabled=false，所有单题报告也false。

原32仍28完整，旧分数SHA256未变；没有将新6题拼回旧28，也没有重跑/读取新C-H或训练、付费API。新生成总计42。新合同提示与cap同时变化，耗时变化不能叫引擎加速或科学条件严格等价。

阶段判定：REVISE_FULLFLOW。本轮意义是消除采样失效疑点并检验完整合同，不是机制确认。下一动作：先分析具体失败约束，不直接扩大样本或把部分成功记作修复完成；任何修改另存版本、重新审核，不自动搜索提示。
