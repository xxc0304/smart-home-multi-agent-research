# 任务2：固定前四道D题核读

主助手核读，非独立人工标注。选择在看内容前固定为D原顺序前4题，已读全部80段。仅核对给定文本与数据集参考的关系，不验证百科事实的外部时效性。无agent作答，不能称发现模型失败原因。评分侧[原件包](ANALYSIS_ONLY_CASE_PACKET.json)含gold，禁止作为推理输入；[canonical核对](CANONICAL_CHECK.json)确认输入与本地官方train原件一致，并非本轮导出改写。

## D1：2hop__123383_21417

问题：When was Wesley Alba Sturges's institutional employer created? 官方答案1843；支持P17/P15。

- P17记录其1924–1961任Yale Law School教授，并任院长；也记录退休后赴University of Miami School of Law任院长。
- P15标题虽是Yale University，但正文明确列Yale Law School (1843)，区别于医学院1810、神学院1822、研究生院1847等日期。
- 参考链：Sturges→Yale Law School→1843，给定文本可支持该答案。
- 限制：题目未指定任职时期，P17有两个雇主。应标为“参考答案有文本支持，但雇主指代有歧义”，不能将模型询问雇主或另提Miami直接归成不听专家。也不能凭P15标题将机构偷换为Yale University。

记录：ANSWER_SUPPORTED_WITH_REFERENT_AMBIGUITY；其他可能雇主成立日期在本题资料未明示，本轮不补。

## D2：3hop1__478606_751065_78953

问题：Where is the country that the owner of Virgin Holiday Cruises is from located on the map? 官方答案Lying off the north-western coast of the European mainland；标注P6/P5/P10。

- P6明确Virgin Holidays Cruises owned by Virgin Group，另称总部Crawley。
- P10明确United Kingdom的地理位置，支持参考答案的地理部分。
- **标注为中间依据的P5是Virgin Games**，正文说其在线博彩服务主要在英国，并从Virgin Enterprises许可品牌；未明确写出Virgin Group的所属国家。另一家公司在英国经营，不足以单独完成owner-country的等价推断。利用Crawley在英国的背景知识属于题面外补桥接，不能假称这条关系已明确写在给定资料。
- P12美属维尔京群岛、P18瑞士注册邮轮公司等是可混淆对象；不是所有含Virgin/邮轮的段落都能接入正确关系。

记录：REFERENCE_BRIDGE_NOT_EXPLICIT_IN_CONTEXT。**不是断言英国/地理答案事实错误**，而是本题给定文本不足以直接支持标注的整条关系。保留该题原位置、gold及官方评分；未来若核读其轨迹，数据缺口与agent改答分别记录，不用此题独立证明H1或H2。

## D3：2hop__663664_46366

问题：Who sings with the performer of A Feelin' Like That on Every Storm? 官方答案Co-writer Hillary Lindsey，别名Hillary Lindsey；支持P0/P18。

- P0明确A Feelin' Like That由Gary Allan录制，而Ira Dean、David Lee Murphy、Kim Tribble是作者，不能混为演唱者。
- P18标题Every Storm (Runs Out of Rain)，明确Hillary Lindsey唱backing vocals，且标为co-writer。因此可支持问句所指歌曲的伴唱姓名。
- P18正文未再次明确该曲由Gary Allan演唱；从歌曲标题可直接读出唯一提及的伴唱姓名，未必需要模型使用第一个连接。这是可能的捷径/隐式桥接，不能据最终答对证明进行了完整多跳整合。
- 官方别名已包含姓名，不需本轮新增别名或改评分。

记录：ANSWER_SUPPORTED_WITH_SHORTCUT_OR_IMPLICIT_BRIDGE。若模型答“Hillary Lindsey”，可以评分正确；只有沿完整证据检查才讨论实际使用了哪段。

## D4：2hop__782778_777968

问题：What is the capitol of the province where Artsvanik is located? 官方答案Kapan；支持P5/P17。

- P5明确Artsvanik是Armenia的Syunik Province村庄；P17明确Kapan为Syunik Province的provincial capital。
- 参考链Artsvanik→Syunik Province→Kapan，实体与关系均明确；不是问Armenia国家首都，也不是只回答省名。
- 问句capitol用字不规范，但语义可读为capital；不据此改题或删题。其他国家/地区首府是干扰项。

记录：REFERENCE_CHAIN_EXPLICIT。可作为如何逐条记录证据关系的清晰例子；仍不是专家已答对的实测题。

## 这四题对主线的实际作用

获得了可核对的参考事实、指代/桥接限制和一个较清晰链例，说明过程分析不能只照gold答案判原因；也不能由答案正确证明多段信息被使用。本轮不估问题比例，不因发现问题改换数据集，不删除或重抽这四题、不触碰C/H。后续主结果保留全部预定分母，另单列已知数据限制的敏感性说明；不能只留下适合叙事的题。
