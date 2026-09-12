# 编程分区导航

更新时间：2026-09-12。当前阶段：Stage 5。本页只列当前源码、验证、运行证据与论文取数入口；历史目录保留在原处供复现，但不作主导航。

| 问题 | 当前入口 | 状态 | 权威证据 |
|---|---|---|---|
| Q1 | `q1_baseline/`、`config/q1_baseline.json` | `PASSED` | `runs/q1_human_run_20260911_204149/` |
| Q2 | `q2_baseline/`；复现主模型须显式 `--experiment weekday_buffer` | `ACCEPTED / FROZEN` | `runs/q2_low_complexity_20260912_002010/weekday_buffer/`、`交付候选/Q2_20260912_weekday_buffer/` |
| Q3 | `q3_baseline/`、`config/q3_baseline.json` | `ACCEPTED / FROZEN` | `runs/q3_revised_20260912_112347/` |
| Q4-2 | `q4_baseline/`、`config/q4_baseline.json` | `ACCEPTED / FROZEN` | `runs/q4_2_20260912_193813/` |
| Q4-3 | — | `NOT_STARTED` | — |

## 当前说明

- Q1：见[人工运行说明](Q1_人工运行说明.md)与运行包；既有通过结果无需重跑。
- Q2：主模型为 `M2-Q2-EXPERIMENT-weekday_buffer-v1.0`，说明见[定版建议](Q2_结果复核与定版建议_20260912.md)。
- Q3：主模型为 `M3-Q3-POINT-MODEL-B-v2.0` / `Q3_ROLLING_INTERP`；说明见[修订版实现报告](Q3_修订版实现报告_20260912.md)、[技术核查](Q3_修订版运行技术核查_20260912.md)和运行包人工验收。
- Q4-2：可见性规则为 `TIMESTAMP_LE_DECISION_VISIBLE`，继承冻结 Q2；当前权威重跑已完成身份、断言、Solver、Excel 回读和人工验收。主轨道冻结为 `Q4_2_PRICE_CANDIDATE_P2` / `P2_EWMA`，说明见[最终重跑技术核查](Q4-2_最终重跑技术核查报告_20260912.md)和[人工验收](runs/q4_2_20260912_193813/人工验收.md)。

## 目录

- `q1_baseline/`、`q2_baseline/`、`q3_baseline/`、`q4_baseline/`：当前源码。
- `config/`、`tests/`：当前配置与测试；不得修改冻结 Q1--Q3 后沿用旧证据。
- `预处理审计输出_时间口径修订版/`：Q1/Q2 当前输入；`预处理审计输出_Q3修订版_点值语义/`：Q3 当前输入。
- [runs/](runs/README.md)：不可变运行证据；[交付候选/](交付候选/README.md)：论文取数候选物及其审批边界；[审计/](审计/README.md)：只读审计；`归档/`：历史材料。

当前运行前，必须遵守[四问模型完整基线](../四问模型完整基线.md)和[人工运行与反馈统一规范](../项目管理/人工运行与反馈统一规范.md)。
