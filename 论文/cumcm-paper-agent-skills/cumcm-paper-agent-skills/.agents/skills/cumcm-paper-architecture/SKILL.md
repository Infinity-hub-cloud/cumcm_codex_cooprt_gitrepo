---
name: cumcm-paper-architecture
description: 根据已理解的数学建模项目生成高质量竞赛论文主线与目录。用于 CUMCM/MCM 类论文的章节规划、问题依赖组织、统一模型放置、符号/公式/图表布局；强调优秀论文的一条论证链与按问题新增量写作，避免机械模板目录。
---

# CUMCM Paper Architecture

先读 `.paper/paper_context.md`；仅为核验结构所需事实回源。若不存在 context，先调用 `cumcm-paper-intelligence`。

同时遵守已安装的 `math-modeling-paper-pro`，尤其是 paper spine、question dependency、writing principles。

## Architecture rules

1. 先构造一条 paper spine：central problem -> shared core -> question progression/branches -> synthesis。
2. 题号不等于数学依赖；但最终目录必须让评委能快速定位每问答案。
3. 被两问及以上复用的预处理、符号、评价指标、状态方程或基础模型，优先在共享章节定义一次。
4. 下游问题只写 delta：新增变量、目标、约束、数据、平台、场景或风险。
5. 简单问不要硬拆成“模型建立/模型求解/结果分析/模型检验”四段；复杂问按 reader job 拆分。
6. 数据预处理只有在影响模型或结果时进入正文；普通清洗细节压缩或放附录。
7. 总体技术路线图最多承担一次全局导航；每问流程图只有在算法/决策链确实复杂时才保留。
8. 图看趋势/结构，表给精确方案/数值；同一信息不重复占版面。
9. Validation 尽量贴着被验证的 claim，不把所有检验扔到一个空泛章节。
10. “模型评价与推广”只写证据支持的优缺点、适用边界和可迁移结构，不写通用套话。

## Excellent-paper patterns

加载 `references/excellent-paper-patterns.md`。吸收其结构亮点，不复制具体题目的模型名称或文本。

## Outputs

生成或更新：

- `.paper/paper_outline.md`：三级以内目录 + 每节 reader job + 输入证据 + 预期图表/公式；
- `.paper/visual_plan.md`：只保留必要图表；
- `.paper/notation_ledger.md`：正文统一符号；
- 若已有 LaTeX 工程，可同步创建/调整 `sections/` 骨架，但不要在此阶段填大量正文。

目录必须对当前项目定制。优先删掉“看起来像论文但不增加论证”的章节。
