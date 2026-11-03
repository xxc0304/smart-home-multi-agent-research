# 实验二两轮四分支离线实现

ASK=never，EFFORT=balanced，assurance=draft。基线commit00338a49953246eaeff582e1a16f4c2959b77374；旧未提交文件保留，本次不提交无关内容。

目标：整体审核并落实A私人隐藏/B讨论隐藏/C私人公开/D讨论公开，4共用初答+4×12=52，公开/隐藏顺序配对、私人历史隔离、私有短终答、均匀随机平票。输入D既定前缀及显式真实/fixture输出；输出可追溯请求/原始响应、答案与转移/配对描述统计、待填运行配置。复用B0的模型加载/答案metric/bootstrap，旧四轮程序不改。无真实训练、付费调用、C/H题/标签读取、新数据语义抽查。

验收：.venv-expert/Scripts/python.exe -m unittest discover -s tests -p test_b1_controls.py -v；工具smoke写fixture产物，D元数据/接口预检。真实Qwen/GPU/长上下文/专家资格待实机。
