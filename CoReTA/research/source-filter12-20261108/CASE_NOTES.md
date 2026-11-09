# 全12题双seed的R过程核读

助手全文句子去重/完整时序核读480响应槽位（含120旧S复用），非仅读答案字段；process.cjs的字典与时序可重建全部原句。call均R responses.jsonl零起算。seed0=2026110910、seed1=2126110910。两seed非独立题，正确答案不认证整链。对照旧B/E/S主要差异沿用sources-expansion32的1596槽位过程审核；新增核读E46/1全20响应和49/1、56/1、60/1关键路径，不宣称重读所有旧批3648条。

|题|seed0|seed1|
|---|---|---|
|16|c0–19：M1一直Bravo，M4/M2首工作Charlie，M3次轮Charlie，末答普通3Charlie带团队对；引用将Charlie审计归Bravo等错误仍有。|c20–39：M1首工作Charlie保持；普通M2先Charlie，M3次轮/M4三轮Charlie，最终全对。M1自行写队友观点不是真实收到推理。|
|17|c40–59：全末答Plateau。M2 c51/54将Plateau距动物远挂Riverbank，最终正确并不消除事实绑定问题。|c60–79：全首轮到末答Plateau，正确排其他点；无差异成功对照。|
|24|c80–99：M1/M3/M4末答City，M2反复承认Valley恶意软件仍Valley；3:1正确。|c100–119：M1一直City；M2/M4Valley，M3前三轮Mountain、第四及末答Valley，3:1错。物理离线备份与网络中断题义边界保留。|
|39|c120–139：M1/M2Bravo、M4Charlie；M3第四轮Alpha后末答保持；虽有正确候选，2:1:1最高票Bravo错。|c140–159：M2第一轮即Alpha全保持；其余M1Bravo、M3/M4Charlie，最高票Charlie错。多次承认洪水不安全却选Bravo、承认横风超限却选Charlie，过滤未解决。|
|45|c160–179：全首工作Beta；M3/M4/M2次轮Gamma，M1三轮Gamma，末答全Gamma，普通仍错称Gamma缺试剂。|c180–199：M3首轮Gamma、M4次轮Gamma、M2四轮Gamma；M1前三轮Beta、第四Gamma、私答Beta（旧S复用），普通3Gamma团队正确；不是M1从未答对。|
|46|c200–219：M1/M3/M4最后工作Riverside，M2Hillside；M4私答Downtown，末答Riverside2/Hillside1/Downtown1最高票对。|c220–239：M1一直Riverside；M2把封路挂Riverside仍Hillside，M4将空气差挂Hillside并Downtown；M3时而Riverside但最后Hillside、私答Downtown，最高票Downtown错。旧E1801/1802正确、1803/1805跟进，全末答Riverside。|
|49|c240–259：M1首轮Hilltop→Riverside→第四Hilltop→私答Riverside；M2Valley→第三四轮Hilltop→私答Valley；M4始终Hilltop，M3始终Riverside。最后工作3Hilltop，末答仅1Hilltop。|c260–279：M2初答及全工作/私答Hilltop；M3第一、三、四工作Hilltop但末答Riverside；M1/M4Riverside。正确依据未传播，兼有提交改错。E最终全Hilltop。|
|52|c280–299：M1/M2/M4Green保持，M3虽复述Red直接极端风仍Red，3:1对。M1/4少量把将来坝放水说成已发生为额外错误。|c300–319：同样三Green一Red；M3承认Green耐极端风仍Red，过滤不保证约束应用。|
|56|c320–339：无Vault候选，M1/M3/M4主要Museum、M2University；M3末答少The为唯一unknown。任意合法补票都无法让Vault最高。|c340–359：M1/M3Museum、M2/M4University，末答2:2错；M1将污染到来反转为不会到来。E普通M4/M2先Vault，M1跟进并全员保持。Vault钥匙/温控原题边界保留。|
|60|c360–379：M2/M4首工作A保持；M1首C次轮A保持；M3持续C，3:1A。|c380–399：M2首轮A持续但被隔离；M1/M3C，M4B，最高票C错。旧E由M4首轮A、M3/M1次轮接上，末答3:1A；E中M2最后工作A→末答B为反向提交。|
|63|c400–419：普通始终River，虚构“staff已解决地板/厨房问题”或仍不信Garden确认；M1第三工作Garden保持，末答1:3错。|c420–439：所有人一直River，把霉菌/地板/短路叫minor/manageable，Garden已确认主厅干燥未真正改变选择，全错。|
|64|c440–459：M3首轮HVAC保持，M2次轮HVAC保持；M1/M4食物，最终2:2期望0.5。|c460–479：M1HVAC持续（旧S）；M2次轮HVAC保持；M3/M4食物，最终2:2期望0.5。M3 c471虚构M1/M2强调快发病及HVAC应慢发病；输入无队友推理，不能当真实交流或泄漏。|

覆盖与统计详SUMMARY、ROUTING_CHECK和RESULTS_ANALYSIS。没有将重复句、旧复用、同题双seed当独立机制证据。
