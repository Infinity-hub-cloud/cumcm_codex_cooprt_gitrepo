---
name: cumcm-paper-draft
description: 将已确认的数学建模模型、算法、结果和论文目录写成 CUMCM 风格正文初稿。适用于问题重述、问题分析、模型建立、求解、结果解释、验证、模型评价等章节，并优先直接更新现有 LaTeX/Markdown 工程。严格锁定科学事实，不编造结果。
---

# CUMCM Paper Draft

输入优先级：`.paper/paper_context.md` + `.paper/paper_outline.md` + 权威结果源。若缺前两项，先调用对应 skill。

使用 `math-modeling-paper-pro` 作为科学写作主规则；正文事实锁定后，再用 `sepia write/refactor` 处理中文自然度。Sepia 不得改变数字、单位、符号、条件、结论强度或 limitation。

## Core prose contract

写“数学推理”，不写团队工作流。

每问根据复杂度组合这些 reader jobs：

**继承关系/问题分析 -> 数学新增量 -> 模型/公式 -> 求解理由 -> 决定性结果 -> 结构解释 -> 贴附验证 -> 边界**。

不是每问都必须拥有所有小标题。

## Writing rules

- shared mathematics 只定义一次；后文引用式号并写 delta。
- 问题分析回答“为什么这样建模”，不提前堆结果与算法流程。
- 公式使用 `lead-in -> equation -> uptake`；公式前说用途，公式后说其对约束/目标/下一步的作用。
- 算法只写与题目结构有关的选择理由、关键改动和复核方式；标准伪代码/参数细节放附录或省略。
- 结果先直接回答赛题，再提炼 pattern；不逐行复述表格。
- 图表使用 `lead-in -> 图/表引用 -> takeaway`；图是论证，不是装饰。
- 相关性不写成因果；代理/近似不写成精确；启发式最好结果不写成全局最优。
- “准确、稳定、鲁棒、显著、高效”必须紧跟指标、比较或测试范围。
- 中文正式、克制、技术明确；让模型、变量和结果多做主语。
- 避免连续“针对问题X”“首先/其次/最后”“通过…可以…”和空洞收尾。

加载 `references/section-playbook.md` 处理不同章节。

## Missing evidence

这是“正文初稿”任务：不要因局部缺失停掉整个论文。无法确认处写：

`TODO[证据缺口: 需要 <文件/结果/单位/验证> 才能完成本句]`

禁止填猜测数值或伪造引用。其余可支持章节继续完成。

## File behavior

- 优先沿用现有 LaTeX/Overleaf 结构、命令、标签、bib 和文件名。
- 不因个人偏好重构整个工程。
- 没有既有工程时，再按 `.paper/paper_outline.md` 建立轻量 `sections/`。
- 一次可写全文初稿，但按 paper spine 顺序完成；复杂章节先写承重部分再补过渡。

## Completion

完成后：

1. 运行 Sepia `review`；
2. 只对成立的问题做 `refactor`；
3. 保留所有科学锁；
4. 列出仍存在的 `TODO[证据缺口]`，交给 `cumcm-paper-audit` 终审。
