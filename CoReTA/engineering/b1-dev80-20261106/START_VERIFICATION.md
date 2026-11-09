# 启动实测检查

2026-11-06；助手自审none/provisional。实际后台控制器PID1352874，首worker1352885。两项启动门槛PASS、51项CPU测试通过；旧8题416条真实历史完整回放/导出一致；D80原始输入最大含初答余量7971，极端合成历史仅index62达到17579超16384，风险已在冻结LENGTH_REVIEW/PREFLIGHT明示并由逐请求精确长度检查/单分支隔离处理，不承诺80题无缺失。

不设wall clock截止；BUDGET.wall_clock_cutoff与per_request_wall_cutoff均null，不用timeout。最多3744次新增调用，18个固定4题worker，旧8不重生；本机42个可用冻结文件与审批hash验证通过，启动审批/冻结/源码已下载本机归档。

首轮真实检查：24条新返回，23OK+1OUTPUT_LIMIT，0逐字Unknown；已进入work阶段、其他请求继续。后续核至34条（33OK+1OUTPUT_LIMIT），定位为index9/第10题、2hop__342640_126084|02、M3 initial256触顶，导致该题initial_failed并隔离四组依赖；不是工作1024触顶，已更正最初口头定位。没有为单条触顶停止全批或改变cap。本条不是全批结果，后续进度/完整性以服务器STATUS及各cell日志为准。截断原文保留，不将其标为EOS，不重试或向后续依赖补Unknown。

原始短答/工作提示、四组、两轮、投票、模型专家与采样不变。当前只扩大开发覆盖，不作为已验证机制/方法效果或独立确认。
