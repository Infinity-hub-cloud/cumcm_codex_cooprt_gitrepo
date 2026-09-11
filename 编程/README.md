# 编程分区

本分区保存可执行代码、参数配置、验证记录与人工运行说明；原始附件只读，任何候选输出必须写入全新目录。

## 当前阶段状态

2026-09-12更新：问题二主模型已由人工冻结为`M2-Q2-EXPERIMENT-weekday_buffer-v1.0`。`BLOCKER-Q3-TIME-001`已关闭；问题三四条轨道已完成人工运行，数值断言、候选Excel回读和价值分解已由人工验证通过。Q3滚动相对00:00-only改善，但相对冻结Q2费用更高，主模型是否冻结仍待人工明确决策。

先读[Q2结果复核与定版建议](Q2_结果复核与定版建议_20260912.md)，再看[交付候选包](交付候选/Q2_20260912_weekday_buffer/README.md)。包中已有`result2.xlsx`、四日论文表1—3、指标/指纹和人工验收表；无需为补齐结果重跑四组。

- 当前阶段：5（问题1已通过；问题2主模型已冻结；问题3四轨道已人工验证）
- 当前状态：Q3运行与证据验收通过，主模型冻结决策待人工确认；未进入问题4
- 人工授权：`HUMAN-OVERRIDE-CODE-001 = CONFIRMED`
- 时间门禁：`Q1-TIME-MAPPING-PASS = CONFIRMED`
- Q1模型版本：`M1-Q1-MILP-v1.3-instant-left-hold`
- Q2推荐模型版本：`M2-Q2-EXPERIMENT-weekday_buffer-v1.0`
- Q3模型版本：`M3-Q3-ROLLING-4ISSUE-v1.0`
- Q3时间门禁：`Q3-TIME-ALIGNMENT-GATE-PASS`；`BLOCKER-Q3-TIME-001 = CLOSED`
- 数据版本：`PREP-TIME-REV-20260911T170805+0800`
- 已实现：公共配置/数据契约、B0闭式基线、B1 MILP构造、惰性 Solver backend、断言、候选工作簿导出与回读验证。
- Q1状态：`Q1-STAGE5-GATE = PASSED`。
- Q2门禁：`Q2-CAUSALITY-GATE-PASS`、`Q2-COLDSTART-001 = CONFIRMED`、`Q2-SOC-BRIDGE-001 = CONFIRMED`。
- 已有人工证据：原Q2基线及四组365模板日连续求解、334正式模板日候选Excel和汇总。
- 本轮未执行：重新求解、调参、正式绘图、论文Word编辑、问题3及Git提交/推送；没有代替人工批准Q2。

## 目录入口

- `q1_baseline/`：问题1实现包；导入包不会调用 Solver。
- `config/q1_baseline.json`：唯一参数入口，内部充放电上限由 `功率 × delta_t` 精确计算。
- `tests/`：默认不调用 Solver 的单元测试；Solver 集成测试标记为 `REQUIRES_HUMAN_RUN`。
- `requirements-q1.txt`：人工运行环境依赖。
- `Q1_人工运行说明.md`：准确命令、核验步骤、完整反馈文件清单及后续阶段共通规则。

## 安全入口

在本目录执行以下命令只检查环境、输入或非求解测试：

```powershell
python -m q1_baseline.cli --config config/q1_baseline.json doctor
python -m q1_baseline.cli --config config/q1_baseline.json validate-input
python -m unittest discover -s tests -v
```

Q1 已经由人工运行并通过门禁；既有 Q1 包与证据保持不变。

## 问题2因果基线及推荐模型（已运行，待验收）

- 入口：`python -m q2_baseline.cli`
- 配置：`config/q2_baseline.json`
- 依赖：`requirements-q2.txt`
- 人工操作：`Q2_人工运行说明.md`
- 状态：`Q2-CAUSALITY-GATE-PASS`、`Q2-COLDSTART-001 = CONFIRMED`、`Q2-SOC-BRIDGE-001 = CONFIRMED`；人工求解完成，新的主模型接受门禁见候选包`人工验收.md`。
- 注意：CLI默认仍是`baseline`。复现推荐模型必须显式使用`--experiment weekday_buffer`，不能只看配置文件旧模型名。
- 边界：只实现 B0、B1 和 Candidate 接口；不含问题3，不读取附件3/4，不覆盖官方 `result2.xlsx`。
- 预运行返修：`Q2-PRE-RUN-PATCH-001` 已加入正式输入SHA-256硬门、事后预测评价、统一manifest、公共dispatch空值语义及失败证据落盘。

Q2 的无 Solver 检查及正式人工运行命令见 `Q2_人工运行说明.md`。运行目录若已存在会被拒绝。

## 问题3滚动光伏与购电调整（代码已生成，待人工运行）

- 入口：`python -m q3_baseline.cli`
- 配置：`config/q3_baseline.json`
- 依赖：`requirements-q3.txt`
- 人工操作与反馈文件：`Q3_人工运行说明.md`
- 四轨道：`REF_Q2_FROZEN`、`Q3_ATTACHMENT3_0ONLY`、`Q3_ROLLING_4ISSUE`、`Q3_NOSTORAGE_REFERENCE`
- 午夜顺序：先用当日00:00新issue最终确定前日slot144，再计算00:10 SOC，随后生成当日新模板G。
- 时间匹配：只按`(interval_start, interval_end)`；初始slot144为`fallback_q2_pv`；不允许裸`interval_index == template_slot`。
- 边界：本轮未运行全年Q3、未调用正式Solver、未生成真实`result3_candidate.xlsx`、未进入问题4。

## 文件分层

- 正式输入：仅`预处理审计输出_时间口径修订版/`；旧`预处理审计输出/`保留历史用途，不作为模型输入。不要无参数重跑旧预处理入口。
- 运行证据：`runs/`原路径全部保留；001710为失败suite，002010为本次成功suite。
- 交付候选：`交付候选/Q2_20260912_weekday_buffer/`，先人工接受再提交。
- 旧临时目录：三个`_smoke_audit_time_revision_20260911_*`已移至`归档/20260912_旧冒烟审计/`，未删除内容，可按原名恢复。
- `__pycache__`不是成果；根目录`编程.zip`是历史快照，不是当前可执行代码来源。
