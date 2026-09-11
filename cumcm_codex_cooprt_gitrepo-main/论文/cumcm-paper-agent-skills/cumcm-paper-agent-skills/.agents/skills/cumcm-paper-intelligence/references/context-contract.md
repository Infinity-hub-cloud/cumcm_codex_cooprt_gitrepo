# Paper Context Contract

`paper_context.md` 保持短而可追溯：

## 1. Problem core
- central_problem
- requested_outputs
- core_reasoning

## 2. Question graph
每问：task / role / depends_on / reuses / adds / changes / answer_required。

关系优先使用：prerequisite / extension / generalization / specialization / validation / shared_core / independent_branch。

## 3. Shared mathematical structures
每项：name / definition / notation / first_home / used_by / source。

## 4. Per-question evidence
每问仅记录承重项：
- objective or estimand
- decision variables / key parameters
- constraints
- main model
- algorithm and why it fits
- decisive results + unit + precision
- interpretation allowed by model
- validation / sensitivity
- optimality & causal ceiling
- figures/tables + takeaway
- source pointers

## 5. Notation ledger
只收正文会使用的符号，统一单位、上下标和含义。

## 6. Conflicts / gaps
格式：`[BLOCKER|TODO] claim -> conflicting/missing sources -> affected section`。

## 7. Source map
只列被引用的高价值文件，不生成全仓库清单。
