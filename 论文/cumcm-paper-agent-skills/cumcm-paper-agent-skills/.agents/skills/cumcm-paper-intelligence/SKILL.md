---
name: cumcm-paper-intelligence
description: 理解数学建模竞赛项目并建立论文写作上下文缓存。用于论文手接手建模手/编程手成果时，扫描题目、代码、模型说明、求解结果、表格、图和现有正文，生成可追溯的 paper_context，避免后续写作反复读取整个仓库。不得重新选择模型或擅改科学结果。
---

# CUMCM Paper Intelligence

目标：把“整个项目”压缩成论文手可用、后续 agent 可复用的 `.paper/paper_context.md`。这是理解层，不是正文写作层。

## Boundary

- Solver/程序输出拥有模型、算法、目标、约束、数值、验证、因果与最优性状态。
- 本 skill 只负责发现、对齐、压缩和标注来源；不补算、不猜、不替换模型。
- 同一事实冲突时保留冲突及来源，不自行择一个“看起来合理”的值。

## Read order

1. 赛题/题目说明；
2. 建模说明、推导、README、笔记；
3. 主程序与关键函数，只读到足以理解数学含义；
4. 最终结果文件、CSV/XLSX/JSON/log；
5. 图表源数据与图；
6. 现有论文/LaTeX，作为展示层而非最高事实源。

忽略环境、依赖缓存、构建产物和无关代码。不要逐文件复述。

## Build `.paper/paper_context.md`

按 `references/context-contract.md` 建立紧凑缓存。每个关键事实都写短 source pointer（文件路径 + 表/变量/函数/行号或结果键）。

必须识别：

- 题目要回答什么；
- 各问的数学角色与依赖；
- shared core；
- 每问新增变量/目标/约束；
- 真正决定论文叙述的模型与算法理由；
- 决定性结果及单位/精度；
- validation / sensitivity / baseline；
- heuristic / approximate / exact / proven 的边界；
- 可用于正文的图表及其 takeaway；
- 公式和符号的权威位置；
- 冲突、缺口和未验证项。

## Token discipline

输出压缩后的知识，不复制大段源文、代码或日志。后续只在需要核验具体事实时回源。

如果 `.paper/paper_context.md` 已存在，先判断用户是否要求刷新；没有明显新科学结果时更新受影响部分，不做全量重写。

## Completion

交付：

- `.paper/paper_context.md`
- 如有问题，`.paper/open_issues.md`

结束时用 5–10 行概括：全题主线、每问角色、最关键结果、最大证据缺口。不要开始写完整论文，除非当前任务同时调用后续 skill。
