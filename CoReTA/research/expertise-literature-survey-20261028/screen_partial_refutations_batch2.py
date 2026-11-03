"""Offline, purposive screen: all hidden statements for source IDs 16–22, 24–25.

Rule defined before this batch: select these IDs in order, excluding ID 23 because
it was already examined. Classifications are a single non-blind reader's judgments.
"""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = root / 'data/task-source-audit-20261021/hiddenbench.json'
raw = source.read_bytes()
tasks = {x['id']: x for x in json.loads(raw.decode('utf-8'))}

# Each item: zero-based candidate, interpretation category, reason / limits.
assessments = {
    16: [(1, 'soft_or_ambiguous', '可能冻结和服务中断，不是已发生中断。'),
         (0, 'soft_or_ambiguous', '预计维修带来停电风险，未宣布停电。'),
         (2, 'supports_candidate', '线缆已修复并通过额外安全审计，不能证明没有其他风险。'),
         (1, 'soft_or_ambiguous', '管理者不熟悉预案是风险，不证明站点失效。')],
    17: [(2, 'requires_extra_assumption', '唯一道路受阻、车辆无法抵达；未排除其他方式，需额外前提。'),
         (0, 'requires_extra_assumption', '水流使涉水及乘船不安全，仍需确认其他通路和到达时效。'),
         (3, 'supports_candidate', '高原少蚊虫支持候选，其他地点严重虫害不自动等同不可行。'),
         (1, 'soft_or_ambiguous', '夜间掠食者风险高，任务未明确只能夜间暴露及风险阈值。')],
    18: [(2, 'soft_or_ambiguous', '预测大风下帐篷可能不稳，不是确定倒塌。'),
         (1, 'supports_candidate', '当前只有Pinecone有应急口粮，但补给延迟及任务持续时间的条件仍需判断。'),
         (0, 'soft_or_ambiguous', '升温可能引发雪崩，是条件性风险不是确定结果。'),
         (1, 'supports_candidate', '近期未见熊削弱风险，但不证明无熊。')],
    19: [(1, 'soft_or_ambiguous', '发电机被淹失效，不必然说明当前避难条件全部不可用。'),
         (2, 'supports_candidate', '屋顶通过紧急检查，直接支持建筑安全但不验证所有条件。'),
         (0, 'soft_or_ambiguous', '主路阻断，但另一道路仍可供车辆通行。'),
         (0, 'requires_extra_assumption', '唯一替代道路被树堵；仅此条不确定主路是否仍可通行，需结合第三条。')],
    20: [(0, 'supports_candidate', '日志称漏气修补后压力测试优秀，支持Alpha但不自动验证其他事项。'),
         (1, 'soft_or_ambiguous', '微震可能意味着地下不稳，报告明确需进一步调查。'),
         (1, 'soft_or_ambiguous', '氧气使用上升和警报维护逾期，不确定氧气已不足。'),
         (2, 'soft_or_ambiguous', '应急通风备用系统召回且未更换，不自动证明主要空气系统失效。')],
    21: [(0, 'requires_extra_assumption', '所有至Aurora列车停运；若该候选只能乘火车到达且停运持续，才可排除。'),
         (0, 'requires_extra_assumption', '主要公路禁止车辆通行，不证明列车或其他路径不可用。'),
         (1, 'soft_or_ambiguous', '巴士延至次日，需要明确任务最晚到达时限才可判不满足。'),
         (2, 'supports_candidate', '机场升级和设施补给支持候选，但不独立证明其他选项皆不可行。')],
    22: [(1, 'soft_or_ambiguous', '补给延误说明食水可能缺失，不是确定缺失。'),
         (0, 'supports_candidate', '风暴前无线电报告供电与储备良好，不保证风暴期间持续。'),
         (2, 'requires_extra_assumption', '通往救援站的雪路无法以车辆通过；仍需确认无其他可及时使用路径。'),
         (1, 'soft_or_ambiguous', '冰桥坍塌使通行危险，但未说该桥是唯一通道或完全不可通过。')],
    24: [(0, 'soft_or_ambiguous', '备用电源不可用，不等于市电已断或无法完成离线备份。'),
         (0, 'soft_or_ambiguous', '隔离网络故障；任务为实体离线交付，未证明依赖该网络。'),
         (1, 'soft_or_ambiguous', '主交换机有恶意软件，不自动证明空气隔离系统已失守。'),
         (2, 'supports_candidate', '新线路安全审计与建筑完好是支持信号，不自动确定离线备份安全。')],
    25: [(0, 'soft_or_ambiguous', '室内毒素上升是风险，未给暴露阈值或用途条件。'),
         (1, 'soft_or_ambiguous', '低但异常的传感器读数提示可能污染，非确认。'),
         (2, 'requires_extra_assumption', '太阳能及电池均失效且目前无电；只有供电是必要条件才可排除。'),
         (3, 'supports_candidate', '维护检查水、灯及污染信号，支持Delta但并未核实全部必要条件。')],
}

rows = []
for task_id in sorted(assessments):
    item = tasks[task_id]
    assert len(item['hidden_information']) == len(assessments[task_id]) == 4
    for index, (candidate_i, category, reason) in enumerate(assessments[task_id], 1):
        rows.append({'task_id': task_id, 'task_name': item['name'], 'evidence_index': index,
                     'evidence_quote': item['hidden_information'][index-1],
                     'candidate': item['possible_answers'][candidate_i], 'category': category,
                     'rationale': reason, 'holder_and_receiver': '未核定具体分发及接收者',
                     'development_history': '未核完整使用历史，不能作为未见样本'})
payload = {'source': str(source.relative_to(root)).replace('\\', '/'),
           'sha256': hashlib.sha256(raw).hexdigest(), 'all_source_count': len(tasks),
           'selection_rule': '固定选择原题16–22、24–25；23上一批已筛；逐条检查每题四条隐藏信息',
           'task_ids': sorted(assessments), 'scope': '单人知晓参考结果的初审，非独立复核或留出数据',
           'rows': rows}
out = Path(__file__).with_name('PARTIAL_REFUTATION_SCREEN_BATCH2_20261028.json')
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('wrote', out.name, len(assessments), 'tasks,', len(rows), 'statements')
