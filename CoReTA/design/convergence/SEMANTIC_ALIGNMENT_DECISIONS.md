# 最小协议语义一致性修订（离线）

- 不改已冻结minimal_review.py等代码；新增平面适配器版本，不增加Agent、阶段或字段。
- original_assessment只判断原observed_value这条观察：复算一致=supported，不一致且有依据=refuted；它不判断旧候选命题。旧多项式失败、原反例正确时应supported。
- exact_equality的expected/observed仅为规范整数/约分有理数。schema约束纯标量形状，程序继续检查规范形式；计算过程放reason。不解析或eval表达式。非零/非整数/有序对用model_judged。
- current_checks只核查当前候选需要成立的命题。否定已弃用答案放历史重查或reason，不把针对旧答案的counterexample转成当前缺陷。
- 有原case时保留其确切约束覆盖；无原case时不假装已知完整受影响条件，显式reviewer_selected，不强制引用T1全题句柄。公开全文始终提供，完成条件仍需实际核查，程序不证明语义穷尽。
- rebuttal可以质疑原数值，也可质疑原预期/适用性；观察supported不自动意味着异议正确。后者需独立理由和当前核查，标为模型判断，不机械证明。
- 旧真实输出原样验证，不能自动剥表达式、改枚举或重贴成功标签。人工修正版只用于接口fixture，数学错误必须保留为错误证据。
