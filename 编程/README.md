# 编程分区导航

更新时间：2026-09-12。当前阶段：Stage 5；Q2/Q3 已人工验收并冻结。Q4-2 价格可见性已人工批准，生产代码、测试和运行说明已生成；正式全年 Solver、真实候选导出和 Q4-3 仍未授权。

## 状态总表

| 问题 | 当前入口 | 状态 | 主要证据 |
|---|---|---|---|
| Q1 | `q1_baseline/`，`config/q1_baseline.json` | `PASSED` | `runs/q1_human_run_20260911_204149/` |
| Q2 | `q2_baseline/`，显式 `--experiment weekday_buffer` | `ACCEPTED / FROZEN` | `runs/q2_low_complexity_20260912_002010/weekday_buffer/`、`交付候选/Q2_20260912_weekday_buffer/` |
| Q3 | `q3_baseline/`，`config/q3_baseline.json` | `ACCEPTED / FROZEN` | `runs/q3_revised_20260912_112347/`、技术核查和统一人工验收 |
| Q4-2 | `q4_baseline/`，`config/q4_baseline.json` | `CODE_READY / HUMAN_REVIEW_REQUIRED` | `Q4-2_人工运行说明.md`、`q4_baseline/README.md` |

人工现仅授权 Q4 的 `PRICE AUDIT + MODEL SPEC`。Q4 正式全年调度 Solver、Q4-3 生产实现/求解及 result4 导出仍未授权；Q2/Q3 冻结代码和证据不得修改。

## 当前生产入口

### Q1

- 模型：`M1-Q1-MILP-v1.3-instant-left-hold`。
- 说明：[Q1 人工运行说明](Q1_人工运行说明.md)。
- 状态：`Q1-STAGE5-GATE = PASSED`；既有结果和证据不需重跑。

### Q2

- 冻结主模型：`M2-Q2-EXPERIMENT-weekday_buffer-v1.0`。
- 预测：最近已完成同星期同自然时刻，不足时回退最近同刻。
- 缓冲：28 天同刻净负载残差、至少 7 样本、正部 0.8 分位数。
- 说明：[Q2 定版建议](Q2_结果复核与定版建议_20260912.md)、[Q2 人工运行说明](Q2_人工运行说明.md)、[交付候选导航](交付候选/Q2_20260912_weekday_buffer/README.md)。
- 注意：普通 CLI 默认值仍可能是历史 baseline；复现冻结主模型必须显式传 `--experiment weekday_buffer`。

### Q3

- 当前生产版本：`M3-Q3-POINT-MODEL-B-v2.0`。
- 说明：[Q3 修订版实现报告](Q3_修订版实现报告_20260912.md)和[Q3 人工运行说明](Q3_人工运行说明.md)。
- 正式映射：`预处理审计输出_Q3修订版_点值语义/`，支持 ZOH 与同 issue INTERP。
- 主费用语义：MODEL-B；MODEL-A 只作为敏感性轨道。
- 当前已验证：75 个非 Solver 测试通过、4 个标记 `REQUIRES_HUMAN_RUN` 跳过；2 个极小 toy Solver 测试通过；输入映射门禁通过。
- 已完成：冻结 Q2 参考、七条数值轨道、频率消融、修订版候选 Excel、逐值回读和身份门禁价值分解；技术核查见[Q3 修订版运行技术核查](Q3_修订版运行技术核查_20260912.md)。
- 已完成人工验收：8份`human_feedback.md`已签认；主轨道候选Excel、MODEL-B分账和已登记WARNING已接受；`Q3_ROLLING_INTERP`正式冻结为问题三主轨道。
- 旧 `runs/q3_20260912_*` 全部采用已废止的旧时间/费用语义，只能用于审计问题复现。

### Q4

- 正式规则：`Q4_PRICE_VISIBILITY_RULE=TIMESTAMP_LE_DECISION_VISIBLE`，`BLOCKER-Q4-PRICE-TIME-001=CLOSED`。
- Q4-2 代码、P0/P1/P2/P3、冻结 Q2 桥接、真实 Attachment4 结算、导出器、身份门禁和测试已生成；详见[Q4-2代码说明](q4_baseline/README.md)、[代码生成报告](Q4-2_代码生成报告_20260912.md)。
- 当前仅可运行非Solver/unit测试和极小toy Solver；正式全年 Solver及真实 `result4-2_candidate.xlsx` 仍需人工单独授权。
- Q4-3 生产实现、正式求解和问题4最终提交仍未开始。

## 目录索引

| 目录/文件 | 用途 | 当前性 |
|---|---|---|
| `q1_baseline/` | Q1 公共底座与模型 | 已通过，保留 |
| `q2_baseline/` | Q2 因果预测、MILP、回放与导出 | Q2 冻结实现 |
| `q3_baseline/` | Q3 点值语义、滚动优化、MODEL-B、因果守卫与导出 | 当前生产代码 |
| `config/` | 三问参数入口 | 当前；运行前不得临时改参数后沿用旧证据 |
| `tests/` | 单元、因果、导出回读及 toy Solver 测试 | 当前 |
| `预处理审计输出_时间口径修订版/` | Q1/Q2 正式规范化数据 | 当前输入 |
| `预处理审计输出_Q3修订版_点值语义/` | Q3 point/ZOH/INTERP 映射 | 当前 Q3 输入 |
| `预处理审计输出/` | 首版预处理 | 历史，不作当前输入 |
| `runs/` | 完整运行证据 | 详见 [runs 导航](runs/README.md) |
| `human_run_logs/` | 人工控制台日志 | 详见 [日志导航](human_run_logs/README.md) |
| `交付候选/` | 候选 Excel、论文表及验收记录 | 详见 [候选导航](交付候选/README.md) |
| `审计/` | 独立只读审计输出 | 详见 [审计导航](审计/README.md) |
| `归档/` | 历史快照、旧临时审计 | 详见 [归档导航](归档/README.md) |

根目录中的 `preprocess_audit.py` 是原预处理入口；`build_q3_revised_mapping.py` 是修订映射生成器；`audit_q3_*.py` 与 `test_q3_audit_contracts.py` 是独立审计工具。它们保留原路径以维持已有报告和命令可复现。

## 运行边界

Q3当前无需重跑。若后续确需复现，仍须使用全新`runs/q3_revised_<timestamp>/`；MODEL-A结果不得与MODEL-B主结果混用。Q4 必须先由人工选择并锁定价格可见性规则、关闭 `BLOCKER-Q4-PRICE-TIME-001`，再另行授权生产代码。

既有正式 Solver 和候选 Excel 均由人工运行产生；本轮仅生成 Q4-2 代码和测试，未执行 Q4-2 正式全年 Solver、未生成真实候选、未修改 Q1/Q2/Q3 冻结结果，也未执行 Git 写操作。
