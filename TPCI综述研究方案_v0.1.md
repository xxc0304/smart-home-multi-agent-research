# 面向 CCF TPCI 的智慧家庭智能体综述研究方案

> 版本：v0.2（根据文献可得性进行选题修订）

## 1. 暂定题目

智慧家庭智能体系统中的任务执行与人机协同：从单智能体到多智能体的方法、基准与开放问题综述

英文暂定题目：

Intelligent Agent Systems for Task Execution and Human-Agent Collaboration in Smart Homes: From Single Agents to Multi-Agent Systems

## 2. 研究定位

本文以智慧家庭作为普适计算和人机交互场景，系统总结智能体系统在家庭任务理解、任务规划、资源调度、设备执行、状态验证和故障恢复等方面的研究，并重点比较单智能体与多智能体方案在任务复杂度、协同能力、实时性和可部署性方面的差异。

文章重点不是罗列 Agent 或多 Agent 算法，而是分析智能体系统如何适应智慧家庭中的动态环境、异构设备、用户干预、资源限制和长期运行需求。多智能体是重点方向，但不预设智慧家庭文献必须全部属于多智能体。

## 3. 研究范围

### 纳入内容

- 智慧家庭、家庭物联网、环境智能和相关室内普适计算场景；
- 多智能体系统、设备智能体、机器人智能体、软件智能体和 LLM Agent；
- 家庭任务规划、任务分解、任务分配、协同执行和资源调度；
- 动态环境、设备故障、用户临时干预、任务截止时间和计划修复；
- HomeBench、SimuHome 及其他相关数据集、仿真平台和评价指标。

### 暂不作为重点

- 与智慧家庭场景联系很弱的通用多智能体理论；
- 只讨论单智能体、且没有协同过程的家庭自动化工作；
- 只介绍硬件结构而不涉及智能任务执行的论文；
- 暂不开展新的完整系统开发和大规模算法复现实验。

## 4. 核心研究问题

### RQ1：系统与任务

智慧家庭中的多智能体系统有哪些典型角色、系统架构和任务类型？

### RQ2：规划与协同

现有研究如何完成家庭任务的理解、分解、规划、分配、通信和协同？

### RQ3：动态执行

现有方法如何处理家庭环境变化、设备状态变化、资源冲突、用户干预和任务截止时间？

### RQ4：验证与恢复

现有研究是否关注任务执行结果验证、执行不一致、失败检测、计划修复和任务恢复？

### RQ5：基准与评测

现有数据集、仿真环境和评价指标能否充分反映真实智慧家庭中的复杂性？

## 5. 预期综述贡献

1. 建立“情境感知—任务理解—任务规划—多智能体协同—设备执行—状态验证—故障恢复”的统一分析框架。
2. 按任务执行闭环和系统功能对相关研究进行分类，而不是按照论文逐篇罗列。
3. 横向比较不同方法在动态环境、异构设备、用户交互、实时性和故障恢复方面的能力。
4. 整理智慧家庭多智能体研究中的数据集、仿真环境和评价指标。
5. 总结现有研究距离真实家庭部署的主要差距，并提出有证据支撑的开放问题。

## 6. 初始检索词

### 场景词

smart home; intelligent home; home automation; ambient intelligence; pervasive computing; home IoT; residential environment

### 方法词

multi-agent system; multi-agent collaboration; agent coordination; task planning; task allocation; task scheduling; resource allocation; plan repair; execution monitoring; failure recovery

### 智能体词

LLM agent; language agent; embodied agent; robotic agent; device agent; autonomous agent; human-agent interaction

建议使用“场景词 AND 方法词”的组合进行初检，再根据高频关键词扩展。

## 7. 第一阶段交付物

- 确认后的题目和研究范围；
- 4—5 个最终研究问题；
- 文献检索和筛选标准；
- 文献矩阵表；
- 现有 19 篇种子文献的重新分类结果。

## 8. 选题可行性验证

### 8.1 概念边界

近两年快速发展的主要是基于大语言模型的 LLM Agent；Agent、软件 Agent、智能环境中的自主 Agent 和多智能体系统已有较长研究历史。因此，早期文献不能只使用“LLM Agent”检索，而应同时使用以下术语：

- intelligent agent；software agent；autonomous agent；personal assistant；service agent；device agent；
- context-aware agent；ambient intelligence；intelligent environment；smart environment；home automation；
- multi-agent system；cooperative agents；agent coordination；service composition。

### 8.2 一轮小规模试检索

在正式大规模检索前，先用三组查询比较文献规模：

1. 窄范围：`smart home AND (multi-agent OR multi-agent system)`；
2. 中范围：`(smart home OR home automation OR ambient intelligence) AND (agent OR software agent OR autonomous agent)`；
3. 任务范围：`(smart home OR intelligent environment) AND (task planning OR service composition OR human-agent interaction)`。

记录初始结果、去重结果、标题摘要筛选结果和最终纳入结果，并统计单智能体、多智能体和无法判断的论文数量。

### 8.3 主线选择规则

- 如果窄范围能够筛选出足够的高相关文献，则保留“多智能体”作为主线；
- 如果多智能体文献数量有限，则采用“从单智能体到多智能体”的主线，单智能体作为基础和对照，多智能体作为重点章节；
- 如果严格的智慧家庭文献过少，则扩展到 ambient intelligence、smart environment 和家庭物联网，但必须在文章中明确扩展理由；
- 不应把普通家庭自动化论文强行改称为 Agent 论文，也不应为了凑数量纳入与家庭场景关系很弱的通用多智能体论文。
