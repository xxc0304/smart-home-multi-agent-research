## 2026-11-05 三条截断诊断完成：batch4加至1024仍1条失败，优先batch2

见engineering/b1-length-diagnostic-20261105/RESULTS.md、POST_RUN_AUDIT.json。72尝试=72返回，12分57秒，67EOS/5TOKEN_LIMIT，无异常；12固定载荷=3失败目标+9原同批请求，非新独立题或团队分。batch4 512三目标全截断，1024仅B/C在772/550 EOS、A仍1024截断且8gram重复升至56.8%；serial B512截断、1024在531结束，说明部分只是余量不足，不能全归罪batch4。batch2三目标在两上限均412/363/372 EOS，但原文仍有错误/不确定，不等于语义正确。原batch4 12/12逐token复现，增cap36/36前缀一致；payload/seed/路由/采样/审批/12源码hash核验PASS。助手自审none/provisional，PASS限诊断，batch4完整执行器仍REVISE；不无限加cap，下一优先batch2有限完整验证并检查质量，未自动新8/32/训练/C-H。原停止和旧分数保留。

