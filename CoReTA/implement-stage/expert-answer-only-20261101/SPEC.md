# 仅答案专家最小执行路径

ASK=never；EFFORT=balanced；assurance=draft。基线commit：00338a49953246eaeff582e1a16f4c2959b77374；既有脏文件保留，不提交无关内容。

目标：接通答案SFT、V/C生成评分、配对统计与GPU到位配置。输入为既有1796/V200，C仅在后续真实运行显式选择；本轮仅准备C元数据。输出为adapter/原始响应/评分报告、待实机配置及本地fixture检查。训练只监督答案与结束符，不含资料/padding；不静默截断。无付费API、模型权重下载、真实专家训练、数据重审或H访问。CPU自建微型模型只验证工程，不当任务证据。

验收：.venv-expert/Scripts/python.exe -m unittest discover -s tests -p test_b0_expert.py -v；无torch的基础检查可用.venv。具体Qwen/GPU兼容和吞吐留实机预检。
