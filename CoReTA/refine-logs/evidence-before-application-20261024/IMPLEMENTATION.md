# 前置核对原型 v1 实现记录

2026-10-24。实现模块src/coreta/workboard/grounded.py；基线runtime.py仅新增默认返回空字典的before_application钩子。已有实验入口默认仍使用Runner，不会自动切换历史冻结实验。

## 实际路径

基线普通轮：2 OBSERVE → TRY → CHECK_USE + CHECK_EFFECT → CHOOSE。
候选普通轮：2 OBSERVE → GROUND → TRY → CHECK_USE → CHOOSE。
三人正常轮均6次调用。pass、unable可提前结束，实际调用量未必相同。终稿仍FINALIZE、双检查、FINAL_CHOOSE共4次。相同调用数不等于相同token或成本。

OBSERVE沿用原贡献字段，增加claims(statement/premises/source_refs)，由提供者生成，不增加抽取调用。GROUND由编辑者与提供者之外的成员执行；输出每项supported/conflict/unresolved、具体理由与可见来源以及limits。schema要求每项都有结果，但不能保证模型列全了语义内容或判断正确。TRY收到完整贡献与GROUND_REVIEW；核对没有强制否决权。CHECK_USE检查整个真实前后差异及超出建议的改动。CHOOSE仍选已有版本。GROUND输入输出由gateway日志保存，另记ground_review事件；结果文件带method_variant。

## 明确的设计取舍

第一版使用完整公开贡献和可见候选稿件，保留推荐意见，称ground_full_public_v1。此前隔离建议的构想暂未实现。这样避免再次用字段删除冒充信息保留，代价是不能检验隔离建议是否有用。检查者只取得自己的私有原件；其他成员资料仍通过公开转述获取。没有加入研究者选出的正确摘录或正确推理。

GROUND不接收FEEDBACK或其他检查者新裁决，但公开稿件本身仍可含旧结论，不能称独立认知或盲态。该原型同时改变贡献表示、检查顺序和事后检查职责；若改善，只能先归因于整体变体。后续机制归因需要另行控制。

## 启用方式

显式用GroundRunner/GroundContracts/GroundPrompts替代对应基线类；gateway设置max_output_tokens.ground（拟取原check_effect上限），保留总调用和总输出预算。漏配ground cap或混用基线contracts/prompts会拒绝构造。没有新增live批量入口，不复用旧批次授权或篡改冻结件。

## 本地完成范围

运行tools/preview_grounded.py生成interface-preview/中的004/034真实历史输入视图、GROUND提示和输出schema、OBSERVE输出schema。脚本不创建网络客户端，不读取凭据。历史knowledge整段复制为示例claim，标注为接口展示，绝不用于声称自主抽取成功；没有伪造模型输出。

此次未添加或运行测试。接口示例可生成不代表端到端路径已经通过验证。尚需在用户要求验证时检查调用顺序、异常停批、基线一致性、权限、完整链路及预算，再冻结新案例和实验批次。未产生新模型结果、未证明收益。

后续实验应同时记录有效帮助保留、错误帮助传播、TRY新增错误、终稿质量和成本；两个旧题用于接口展示，不作为新效果证据。
