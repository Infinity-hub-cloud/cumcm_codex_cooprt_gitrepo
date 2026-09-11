---
name: cumcm-paper-audit
description: 审核数学建模竞赛论文初稿的科学一致性、结构完整性、结果可追溯性、符号公式、图表承接、结论强度、重复和 AI 模板痕迹。适用于 Codex 完成正文初稿后的终审与安全修复，不得借审稿之名重算或改变模型。
---

# CUMCM Paper Audit

以 `.paper/paper_context.md` 为索引，以原始结果/程序输出为最终事实源。结合 `math-modeling-paper-pro` 的 reviewer 规则。

## Audit order

1. **Task coverage**：每问是否在正文得到明确答案；目录与题目可追踪。
2. **Evidence**：所有关键数字、单位、比较、图表、验证能否回源；正文与表图是否一致。
3. **Claim ceiling**：heuristic ≠ global optimum；association ≠ causality；有限扰动 ≠ 普遍鲁棒；surrogate ≠ exact。
4. **Mathematics**：变量先定义后使用；符号/上下标/单位统一；objective sense、constraints、approximation status 不漂移。
5. **Structure**：shared core 是否重复；后问是否真正写 delta；validation 是否贴着 claim；是否按 solver 日志叙述。
6. **Figures/tables**：每个图表有必要性、正文引入和 takeaway；不存在图表与正文互相重复或像素读数造结论。
7. **Writing**：删除空评价、连接词堆积、机械题号开头、重复结尾与算法名堆砌。
8. **Compression**：保留任务答案、承重数学、结果、验证和限制；压缩教程式算法、逐表复述和常识背景。

加载 `references/audit-checklist.md`。

## Repair policy

可直接修：措辞、重复、结构位置、交叉引用、明显符号一致性、已经有证据支持的结果表达。

不可自行修：缺失数字、科学冲突、模型/目标/约束改变、未验证的最优性/因果性。此类写入 `.paper/paper_audit.md` 的 BLOCKER/TODO。

若使用 Sepia，顺序为：`review` 诊断 -> `refactor` 最小修改；之后必须重新核对 locked tokens。

## Output

- 直接修复安全问题（用户要求只审不改时除外）；
- 生成 `.paper/paper_audit.md`，按 BLOCKER / MAJOR / MINOR 排序；
- 最后给一个简短 verdict：`READY / READY WITH TODO / BLOCKED`，并说明最重要的 3–8 项。
