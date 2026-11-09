// Assistant judgments from reading original material; no automatic gold matching.
// Each arm: final classes, process tags, reading note. Raw evidence is joined separately.
module.exports=[
{id:'2hop__123383_21417',context:'按题目分解的Yale Law School桥接，段落15明确1843；1810属于医学院。Sturges后来还在Miami工作，当前结论限定原桥接。',arms:{
A:[['CLEAR_ERROR'],[], 'M1两轮均误称法学院建于1810，终答保持；M4私人工作给1843但与M1不互见，团队选1810。'],
B:[['SUPPORTED'],['PUBLIC_CORRECT_CONTENT'], 'M1第一轮把医学院1810误配法学院；M3|18给1843，M2|19明确区分医/法学院，M4|20纠正；M1|21改1843，终答四人一致。是可见有效纠错的时序候选，不证明因果采用。'],
C:[['CLEAR_ERROR'],[], 'M1两轮/终答1810；普通两人终答1843使团队正确，专家错误与团队正确并存。'],
D:[['CLEAR_ERROR'],[], 'M1两轮1810；同伴摘录也主张1810，最终四人一致错误。公开身份包与此共现，但不能单例归因为权威。']}},
{id:'2hop__153074_79404',context:'题面is from与段落18迁居Singapore存在口径张力；段落16支持总统任命。原别名Republic of Singapore/Singapore可把未回答方式的地点判EM1。',arms:{
A:[['EQUIVALENCE_CANDIDATE','AMBIGUOUS'],[], 'M1两轮明确总统任命；终答仅总统实体，方式动词省略，不能直接定为知识丢失。普通答案有方式变体和Geneva；原EM均0。'],
B:[['AMBIGUOUS','UNRESOLVED'],['CORRECT_INITIAL_AVAILABLE'], 'M1两轮转Geneva口径且承认流程未给；终答Geneva local legal framework没有给具体方式。三名普通终答仍给Singapore任命方式，团队EM0。不能确认纯同伴误导。'],
C:[['EQUIVALENCE_CANDIDATE','AMBIGUOUS'],[], 'M1两轮任命关系正确于Singapore口径；终答只总统实体。M4终答Singapore因原别名EM1，未回答how；原期望团队0.25含此别名影响。'],
D:[['AMBIGUOUS','UNRESOLVED'],['CORRECT_INITIAL_AVAILABLE'], 'M1工作补出原段落未支持的DST/考试/培训，终答DST；这是材料外主张，不联网确认其真伪，不当明确事实金标。普通终答也变Geneva流程；原有Singapore初答可见。']}},
{id:'2hop__857136_78066',context:'段落4同时给1962概念车和1964上市/量产；first made口径未限定。保留gold1962和原评分，不把合理生产口径当无据妥协。',arms:{
A:[['AMBIGUOUS'],[], 'M1工作1962→1964，终答1964；没有同伴可见也变化。普通三人均生产口径1964。'],
B:[['AMBIGUOUS'],['CORRECT_INITIAL_AVAILABLE'], 'M1两轮明确生产而非Boss302年份，终答1964；同伴摘录论据一致。不能只用EM损失认定知识破坏。'],
C:[['SUPPORTED','AMBIGUOUS'],['READOUT_LOSS'], 'M1两轮与终答保持1962概念车口径；其余三人1964，3:1选生产口径，读出损失兼题意歧义。私人组没有接收专家信息的机会。'],
D:[['AMBIGUOUS'],['CORRECT_INITIAL_AVAILABLE'], 'M1两轮1964生产口径，终答同；保留有材料依据的替代解释，不计明确从众损害。']}},
{id:'2hop__178056_377891',context:'段落19为建筑容纳CSIC安达卢西亚总部，题问part of；总部与上级机构的粒度须区分。CSIC是原别名，但全称加缩写不是原EM可接受串。',arms:{
A:[['GRANULARITY'],[], 'M1两轮完整CSIC，终答Andalusian headquarters省略机构名，范围不足待判。普通两人全称加CSIC、另一人总部全称，原EM全0。'],
B:[['EQUIVALENCE_CANDIDATE','GRANULARITY'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT'], 'M1工作和四人终答均总部+CSIC，保留机构实体但具体范围更窄；原EM1→0不是清楚换成错误机构。'],
C:[['GRANULARITY'],[], 'M1两轮完整CSIC，终答省略机构名；普通三人含CSIC，但原EM均0。不是私人组受他人说服。'],
D:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT'], 'M1两轮完整CSIC，最终四人纯机构全称，EM均1；D优于B也包含输出规范化差异。']}},
{id:'2hop__446970_49333',context:'原桥接Balama→Mozambique→metical替换escudo，段落4给16 June1980；年份1980与完整日期是精度差异，不能自动等价合票。',arms:{
A:[['CLEAR_ERROR'],[], 'M1工作第一轮给16June1980，第二轮改16th century，终答同；错误早于终答，不能标最后一步才翻转。团队两票1980压过M2完整日期，粒度分裂。'],
B:[['SUPPORTED'],['PUBLIC_CORRECT_CONTENT'], 'M1两轮完整日期；M2|16先给完整日期，最终四人完整日期。专家初答16thcentury错误被纠正，但不能仅凭同答证明信息源。'],
C:[['SUPPORTED'],[], 'M1两轮完整日期，最终四人完整日期；私人自行复议也可修正，不能把B的纠正独占归于交流。'],
D:[['SUPPORTED'],['PUBLIC_CORRECT_CONTENT','READOUT_LOSS'], 'M1工作明确完整日期，终答同；普通三人终答1980，投票丢完整日期。其摘录也写完整日期却总结1980，涉及精度收缩。']}},
{id:'2hop__726238_705760',context:'段落14 Colgate跨Washington/Waukesha县界，段落15 MurphyLake在Washington；题要相邻县，按原桥接Waukesha而非湖所在县。多同名湖是干扰。',arms:{
A:[['SUPPORTED'],['LATE_CORRECT_FINAL','REASON_FINAL_MISMATCH','READOUT_LOSS'], 'M1两轮只Washington，终答才Waukesha；3票GrandCounty获选。私人组不涉及分享失败。'],
B:[['CLEAR_ERROR'],[], 'M1两轮列各湖后称缺县界，终答Washington只给湖所在县，未完成题目要求；普通三人GrandCounty，团队错。'],
C:[['SUPPORTED'],['LATE_CORRECT_FINAL','REASON_FINAL_MISMATCH','READOUT_LOSS'], 'M1两轮Washington，终答Waukesha；三名普通终答GrandCounty，私人多数读出丢失。'],
D:[['CLEAR_ERROR'],[], 'M1两轮称县界信息不足，终答GrandCounty；普通三人也GrandCounty。原材料存在Washington/Waukesha桥接，不能说材料真缺失。']}},
{id:'2hop__262172_14904',context:'段落19 Dreamingjournal→APA，段落18 Hall首任APA主席；Anuman来自游戏干扰。',arms:{
A:[['SUPPORTED'],['READOUT_LOSS'], 'M1两轮Hall及正确APA关系，终答Hall；普通终答APA/Anuman/Anuman，团队Anuman。私人条件仅是聚合丢失。'],
B:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT','REASON_FINAL_MISMATCH'], 'M1初答/首轮Hall；第二轮|22却否认APA关系且称不足，终答四人Hall。同伴|21/|23摘录也在否定中提Hall，不能称全队工作推理一致。'],
C:[['SUPPORTED'],['READOUT_LOSS'], 'M1两轮Hall，终答Hall；其他终答APA/Anuman/Anuman。公开身份未改变私人多数读出结果。'],
D:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT','REASON_FINAL_MISMATCH'], 'M1首轮Hall，第二轮|46称不足而终答Hall；同伴末轮摘录有条件给Hall，最终四人一致。答案可见不证明理由被一致理解。']}},
{id:'2hop__543705_18221',context:'段落0 OaklandAthletics；段落5 firstHoHoKam1976建、1979离开。当前题无额外时点限制，使用原桥接，不外查现代球场。',arms:{
A:[['SUPPORTED'],['REASON_FINAL_MISMATCH'], 'M1初答1976，工作两轮1979（离开年份），终答回1976；不是全程保持正确。普通四终答均1976。'],
B:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT'], 'M1两轮明确Oakland与1976并解释SloanPark混淆，终答四人1976；是正确关系公开与终答一致的候选。'],
C:[['SUPPORTED'],['REASON_FINAL_MISMATCH','READOUT_LOSS'], 'M1工作1976→1979，终答回1976；普通三人2014，3:1投票错。纠正发生在私有终答，初答已曾正确。'],
D:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','REASON_FINAL_MISMATCH'], 'M1两轮否认Oakland训练场信息，终答1976；普通终答均1976。正确初答已公开，不能说正确内容首次出现于终答。']}},
{id:'2hop__145663_123897',context:'段落1死亡地Legnica，段落6战役9April1241；KettleCreek/1815是干扰。战役位置nearLegnica按原任务桥接，不重新选题。',arms:{
A:[['CLEAR_ERROR'],[], 'M1两轮January8→January18,1815，终答后一日期；普通三人1779，投票错。'],
B:[['SUPPORTED'],['LATE_CORRECT_FINAL','REASON_FINAL_MISMATCH','READOUT_LOSS'], 'M1两轮均称缺死亡地，终答9April1241；同伴|16/|17/|18/|20/|22其实已公开列BattleofLegnica日期，但拒绝死亡地桥接。不能说正确日期第一次在终答出现，只能说M1正确完整作答晚于公开工作；3票1779获选。'],
C:[['CLEAR_ERROR'],[], 'M1两轮January8→January18,1815，终答后一日期；团队三票1779。'],
D:[['SUPPORTED'],['LATE_CORRECT_FINAL','REASON_FINAL_MISMATCH','READOUT_LOSS'], 'M1两轮称不足且说唯一日期1779，终答9April1241；六条同伴全文同样否认桥接，没有正确完整作答。3票1779获选；与B中已公开列正确日期的情况区分。']}},
{id:'2hop__722744_134827',context:'段落16艺术家MarvinGaye，段落7明确父MarvinGaySr/母AlbertaGay；问母亲关系明确。',arms:{
A:[['CLEAR_ERROR'],['FINALIZATION_REVERSAL'], 'M1初答和两轮均AlbertaGay，终答变MarvinPentzGaySr父亲；私有终答载荷仅自身正确历史，不存在同伴说服。普通三人终答母亲，团队仍正确。'],
B:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT'], 'M1初答/两轮/终答均母亲AlbertaGay，四人终答一致；相较A是配对观察，不证明交流保护机制。'],
C:[['CLEAR_ERROR'],['FINALIZATION_REVERSAL'], 'M1两轮均母亲AlbertaGay，终答父亲MarvinGaySr；私有历史隔离，身份提示存在；普通三人答对使团队正确。'],
D:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT'], 'M1工作给正确母亲，虽提校准提示仍终答母亲，四人一致正确。']}},
{id:'2hop__455004_523858',context:'材料给两个制作组织，段落10说Nicholas首任军官/传统首任司令，未直接等同founder；单数producer与双制作组织及founder推断均有歧义。原EM1不可当充分语义确认。',arms:{
A:[['AMBIGUOUS'],['READOUT_LOSS'], 'M1两轮给Nicholas首任身份，终答Nicholas；三名普通答制作组织，未回答创办人。原评分专家正确而投票错，但支持关系需谨慎。'],
B:[['AMBIGUOUS'],['CORRECT_INITIAL_AVAILABLE'], 'M1首轮答制作组织；末轮先答组织、再条件式声称Nicholas创办，终答四人Nicholas；不是一贯清晰的founder证据。'],
C:[['AMBIGUOUS'],['READOUT_LOSS'], 'M1两轮/终答Nicholas，三名普通答制作组织，原评分读出丢失；首任司令→founder仍待独立判断。'],
D:[['AMBIGUOUS'],['CORRECT_INITIAL_AVAILABLE','READOUT_LOSS','REASON_FINAL_MISMATCH'], 'M1两轮称资料没有创办人，终答Nicholas；普通三人制作组织，多数丢失原EM1候选。末轮与交付不一致，但初答已含Nicholas。']}},
{id:'2hop__468328_34197',context:'段落6村庄在Azerbaijan，段落17冲突估计死亡30,000；原题语法不佳但country[where]...关系可解，模型称村庄非国家不等于题真不可解。',arms:{
A:[['SUPPORTED'],['READOUT_LOSS'], 'M1两轮给Armenia/Azerbaijan冲突30,000，终答同；普通仅M2正确，2:2并列，期望0.5实际抽错0。'],
B:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT'], 'M1两轮虽错误批评题目将村当国家，仍明确给Azerbaijan冲突30,000；终答四人正确。答案正确不表示题意解释无误。'],
C:[['SUPPORTED'],['READOUT_LOSS'], 'M1两轮给估计30,000并说明非精确数，终答同；2:2并列抽错，不能把抽签损失称观点改变。'],
D:[['SUPPORTED'],['CORRECT_INITIAL_AVAILABLE','PUBLIC_CORRECT_CONTENT','REASON_FINAL_MISMATCH'], 'M1两轮写30,000但最后又称题不可解，终答四人30,000；自相冲突的工作表述与正确交付共存。']}}
];
