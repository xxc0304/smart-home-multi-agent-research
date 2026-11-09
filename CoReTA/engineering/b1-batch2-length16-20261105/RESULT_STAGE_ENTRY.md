## 2026-11-05 batch2新两条截断16次诊断完成：1024可自然收尾

见engineering/b1-batch2-length16-20261105/RESULTS.md、POST_RUN_AUDIT.json。16尝试=16返回，4分16秒，14EOS+2个512TOKEN_LIMIT，无异常；原第6题A/M4、C/M3在batch2的1024下分别528/586 EOS，只多16/74token，串行380/406不变，另外两条同批请求均EOS。原512 batch2四条token完全复现，增cap8/8前缀一致，输入/seed/路由/采样/审批及12源码hash通过。重复比例约0.8%/5.3%，不同于旧batch4循环至1024；原文仍有Geneva/France/Singapore制度混接，不等于答对。助手自审none/provisional，PASS限定点技术诊断，旧8题未拼接/补跑，下一候选为保留长提示/256短答、四组统一1024工作余量的serial/batch2新合同，另需注册/回归/有限完整验证；未自动新8/32/训练/C-H。

