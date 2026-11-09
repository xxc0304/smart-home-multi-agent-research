const fs=require('fs'),path=require('path'),crypto=require('crypto');const root=path.resolve(__dirname,'../..'),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const block=`## 2026-11-07 研究目标复审：提高有专家团队表现，现象证据服务设计

见research/expert-team-performance-direction-audit-20261107/AUDIT.md。用户提出以提高有专家multi-agent团队表现为目标，用既有讨论的正反过程启发架构。PASS该方向，延续优势利用与有益纠错主线，不预设净拖累；取消先证明一个高频且独立成文现象才许方法探索的过强门槛。现有证据可支撑可证伪设计假设，不等于已确定方法或创新性。

REVISE上一原则方案：原基线已有独立初答→讨论→私答，首次E独立工作也试过且收益依赖设置；不能以重组/命名作新架构。私人提升不证明先独立工作必优，关系提醒无收益不证明结构化决策无效，终答核对也可能是本地接口控制。下一离线交付至多两张具体假设卡（损失/机会、唯一组织操作、区分预测、简单对照、预算）并优先选择，不自动堆组件/扩GPU。专家资格须说明适用阶段，但不要求每阶段必显著领先才设计。

评价按主张安排：原普通讨论、E私人/简单选E或加权、私人聚合为相关强简单比较；同总预算胜单体需另匹配预算，加入专家因果价值需无专家对照，均不要求无差别全跑。正式团队质量/辅助语义、两侧纠错和实际资源分开，允许明确质量—成本取舍。现有五篇近邻笔记不是最新穷尽查新，不声称独立机制或方法增量已成立。

现有56新seed run按原冻结继续，本次未检查即时进度、未新增模型调用，不变训练/协议/评分/现有run；方向审核不是新架构实验启动授权或独立人工验证。助手自审none/provisional，PASS限方向/证据约束，具体方法及论文贡献仍待建立。

`;
const files=['CORE_RESEARCH_BRIEF.md','CURRENT_STATE.md','handoff.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'];
const changes=[];for(const f of files){const p=path.join(root,f),t=fs.readFileSync(p,'utf8'),before=hash(p);if(!t.includes(block.split('\n')[0]))fs.writeFileSync(p,block+t);changes.push({path:f,before,after:hash(p)});}
fs.writeFileSync(path.join(__dirname,'RECORD_UPDATE.json'),JSON.stringify({scope:'DIRECTION_AUDIT_NOT_NEW_RUN',changes,auditSHA256:hash(path.join(__dirname,'AUDIT.md')),new_model_calls:0},null,2)+'\n');console.log(JSON.stringify({records:changes.length,new_model_calls:0,recordsMatch:changes.every(z=>hash(path.join(root,z.path))===z.after)}));
