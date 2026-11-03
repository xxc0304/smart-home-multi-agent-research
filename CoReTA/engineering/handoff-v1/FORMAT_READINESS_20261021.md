# 排序交付与接口补充验证

日期：2026-10-21。用户授权补充事项已完成；六个开发求解运行尚未启动。

## 结论与修改

已补齐上次审核要求的排序契约、回归测试、后段输入检查和小范围真实接口兼容检查。可以按固定六单元计划开始开发试跑。真实求解时的结构合规率、知识优势和CoReTA能力收益仍待测量。

- 月球APPLY.artifact为完整物品排列数组或null；独立和最终答案为ranking数组与explanation。定长15、名称枚举、唯一性均由动态schema与本地验证器检查。非法时沿用最多一次格式恢复。
- 程序保持模型原顺序，确定性生成MY RANKING评分文本；不读标准答案、不补项、不调整顺序。解释单独保存并在普通讨论中公开。
- 模型输入去掉重复的排名文本和应用历史副本；所有原始贡献及应用历史保留。schema只在API response format中发送一份。
- 新入口默认接回项目已有的固定revision DeepSeek本地tokenizer，保留32768输入预算和256余量；三个系统一致，manifest记录tokenizer哈希。这是本地估计，服务端用量另存；文件缺失时失败，不静默切换算法。
- 核心协调机制、资料分配、模型与采样配置未改动。

## 验证证据

统一目录：`CoReTA/runs/handoff-format-readiness-20261021/`。

### 74项聚焦离线测试

`offline-validation/validation.json`与`unittest.log`保存结果和代码/任务包哈希。新增覆盖字符串交付漏洞、缺项/重名/未知名称/错误类型、一次恢复、解释干扰、任意顺序原样渲染、避免重复输入和本地计数器。没有真实模型调用。

### 后段压力检查

字节保守计数下的失败保存在`payload-sizing-initial.json`，没有覆盖。它将字节预算当作token预算，提前拦截长流程。修正后的`payload-sizing-final.json`含8个脚本场景，两个资料条件均完成：

| 场景 | 每条件请求数 | 两条件中最高输入估计 |
|---|---:|---:|
| 3次干预、2次异议核查，常规长度 | 14 | 8281 |
| 同流程，每次6条较长应用记录 | 14 | 11047 |
| 同长流程，末次加入约5000词非法输出并恢复一次 | 15 | 21915 |
| 三初答、六次较长讨论、最终交付 | 10 | 5780 |

均低于32768；没有提高上限或丢弃历史。脚本故意持续提异议，CoReTA最终为`best_effort_unreviewed/review_limit`，这是预期状态，不称排名解对或核查认可。预设长度不代表真实模型输出分布，也不是所有合法最大长度的穷举证明。

### 真实DeepSeek兼容检查

`live-compatibility-network/compatibility.json`及原始requests/responses保存5次完成请求：CONTRIBUTE/REPLY共用结构、APPLY、REVIEW、独立/最终共用排名结构、DISCUSS。全部schema合法、复制目标一致；两种排名输出均经渲染和严格解析。无传输或格式重试。

仅复制公开展示顺序和预设字段，不求解月球任务、不评分，未使用完整求解阶段提示；不能据此声称真实解题永不格式失败。服务端合计输入2152、输出383 token。隔离环境首次连接失败另保存在`live-compatibility/`，随后具备网络访问的检查完成5次请求，所有记录均保留。

复现工具为`tools/check_handoff_payloads.py`、`tools/check_handoff_live_compatibility.py`、`tools/validate_handoff_offline.py`。

## 接下来跑什么

沿用`PILOT_PLAN_20261021.json`：集中concentrated_A1和分散distributed_r0，各跑独立完整作答、普通讨论、CoReTA一次，共6个开发run；task_ordinal=1，driver=A2。无额外干预/重试时36次首尝试，总硬上限120次。本轮未启动。

先看交付与实际知识使用，再比较L1误差及成员独立参考；配对恢复/退化率仍未接通，单情景一次结果不支持普遍增益或机制因果结论。共性API/schema/上下文故障按计划停止批次，不能混用修复前后版本。`freeze.json`固定当前版本文件哈希，真实运行manifest仍须保存当次哈希。
