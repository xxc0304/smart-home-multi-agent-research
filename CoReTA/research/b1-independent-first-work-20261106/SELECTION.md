# 本批题目及选取理由

2026-11-06；25道不同题，各2种子。24覆盖题与8机制题重合7道，不相加成32题。全部为已见开发数据；输入审阅为助手判读，非独立盲标。

覆盖题按固定SHA256顺序、材料链可判定标准选取，先审41条、排17条；不按旧终答成功筛选。机制题的旧现象只帮助诊断，新种子/执行形状可能不复现，不要求出现预定结果。

|原题号|题目|覆盖样本|定向机制理由／输入备注|
|---|---|---|---|
|78|When did the operator of SS Cufic wipe out?|是|wipe out按defunct理解。|
|71|When did Cameroon's main ally change to driving on the right?|是|题目目标与材料支持链可判定。|
|77|When did the performer of Felt Good on My Lips release his first album?|是|题目目标与材料支持链可判定。|
|69|What specialized agency at John Hendra's employer serves as its public health division?|是|UN Women为UN实体，机构层级是材料内局部推断。|
|18|What county is bordered by another county, where Murphy Lake can be found?|是|边界由Colgate跨县线推得；非穷尽所有邻县。|
|1|When was Wesley Alba Sturges's institutional employer created?|是|普通成员先形成正确机构年份，专家初答错误；检验有效纠正保留。|
|27|Worldwide record sales total how many for the band from "That One Night: Live in Buenos Aires"?|是|乐队总销量被误读为专辑销量，且有团队损失候选。|
|15|When was the first circulation of currency for the country where Balama is located?|是|按材料当前货币metical的引入理解；保留first currency轻度措辞边界。|
|64|When was the band that performed Carnival established?|是|Carnival专辑与嘉年华活动误读；旧团队仍对，检验工作改善是否必要。|
|56|How much glaciation has disappeared in the country where, along with Germany and Otto Furrer's birth country, Lake Constance can be found?|是|题目目标与材料支持链可判定。|
|31|Who played the fictional Lost character named after the individual who was an advocate of separation of powers?|是|题目目标与材料支持链可判定。|
|20|When was the spring training home of the team Lance Blankenship is a member of built?|是|题目目标与材料支持链可判定。|
|74|What was the record label of the artist who recorded Roses in the Snow?|是|按给定材料Harris早期唱片标签回答；非全职业生涯唯一唱片公司。|
|22|Who is the sister of the Powderfinger composer?|是|同父关系可推出姐妹，公开拒绝推断；目标关系绑定。|
|24|What did Goring believe the operator of German submarine U-608 would gain with further support?|是|题目目标与材料支持链可判定。|
|79|The country where Flora Steiger-Crawford was born has how many states?|是|按给定历史材料29州评分，不引入当前州数。|
|35|Who was the first Muslim elected president of Jai Kishan's political party?|是|第一/第二位主席，普通成员能纠正专家错误工作。|
|4|What is the capitol of the province where Artsvanik is located?|是|题目目标与材料支持链可判定。|
|63|Which year did the agency that designed USRA 0-8-0 end?|是|题目目标与材料支持链可判定。|
|28|Who is the mother of the artist who released Hello Broadway?|是|题目目标与材料支持链可判定。|
|19|Who was the first president of the publisher of Dreaming?|是|题目目标与材料支持链可判定。|
|53|What county is Six Flags Magic Mountain located in?|是|市与县，局部消息对照已改变E工作但未跑下游。|
|44|When was the country where Meteti is located colonized by the country where a terrorist bombing Gaddafi's Libya was supposedly involved in occurred?|是|题目目标与材料支持链可判定。|
|39|What is the administrative territorial entity of the birthplace of Ike Hampton?|是|私人工作正确而末答错；检验阶段问题是否误当讨论瓶颈。|
|32|How many people died as a result of the fighting betwen Armenia and the country Çobankənd is located?|否|村庄所属国家被误读成村庄是国家；同时旧讨论团队改善，防只挑损害。|

## 运行前跳过的输入问题

这些题保留原数据/原分数，未修改金标。跳过不等于旧模型错误被删除；本批估计限输入合格任务。

|原题号|理由|
|---|---|
|72|Garfield Peak同时属Collegiate Peaks/Sawatch/Rocky多层山系，目标粒度非唯一。|
|45|材料是政府合署办公楼，不明确支持城市为县首府；capital/seat桥接弱。|
|54|broadcaster与and the hound拼接题意不完整，依赖Fox标题词串桥接。|
|68|Orsini意大利/英国home country指代不明，目标1934来自英国材料。|
|10|谁in charge未定时间，材料只说上一任联盟首席部长，核心时间指代不足。|
|14|Alberto Lista支持段未给出生地，关联博物馆缺链。|
|36|制造公司DaimlerChrysler与Chrysler创办者不是同一组织，缺少公司归属桥接。|
|51|父子Dodgson同名且材料父子关系桥接不足。|
|55|Tehran市与Tehran省/Ray县范围不同，题目城市归属链不足。|
|62|出生地either Ghent or Kassel；湖横跨县不能唯一支持出生地边界关系。|
|67|first invaded by British与Norman首次登陆、王权介入不等价，历史事件界定歧义。|
|59|Marvin与Anna共同写歌不证明配偶关系。|
|49|Nile/continent/中间航程/加勒比的核心桥接在题面和资料中不完整。|
|8|Hong Kong制作电影不自动证明故事based in香港。|
|30|首任军官/Commandant不等同创办者；海军与海军陆战队双制作方未消歧。|
|13|同建筑有CSIC总部不等同博物馆所属，且已有缩写表述边界。|
|60|发现最高峰和发现尸体时间存在核心歧义。|
