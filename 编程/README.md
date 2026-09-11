# 编程分区

本分区保存可执行代码、参数配置、验证记录与人工运行说明；原始附件只读，任何候选输出必须写入全新目录。

## 当前阶段状态

- 当前阶段：5（问题1已通过；问题2因果基线代码生成）
- 当前状态：Q2待人工正式运行
- 人工授权：`HUMAN-OVERRIDE-CODE-001 = CONFIRMED`
- 时间门禁：`Q1-TIME-MAPPING-PASS = CONFIRMED`
- 模型版本：`M1-Q1-MILP-v1.3-instant-left-hold`
- 数据版本：`PREP-TIME-REV-20260911T170805+0800`
- 已实现：公共配置/数据契约、B0闭式基线、B1 MILP构造、惰性 Solver backend、断言、候选工作簿导出与回读验证。
- Q1状态：`Q1-STAGE5-GATE = PASSED`。
- Q2门禁：`Q2-CAUSALITY-GATE-PASS`、`Q2-COLDSTART-001 = CONFIRMED`、`Q2-SOC-BRIDGE-001 = CONFIRMED`。
- 未执行：Q2正式全年求解、真实 `result2_candidate.xlsx` 导出、调参、正式绘图、问题3及 Git 操作。

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

## 问题2因果基线（待人工运行）

- 入口：`python -m q2_baseline.cli`
- 配置：`config/q2_baseline.json`
- 依赖：`requirements-q2.txt`
- 人工操作：`Q2_人工运行说明.md`
- 状态：`Q2-CAUSALITY-GATE-PASS`、`Q2-COLDSTART-001 = CONFIRMED`、`Q2-SOC-BRIDGE-001 = CONFIRMED`；代码已生成，未执行正式求解。
- 边界：只实现 B0、B1 和 Candidate 接口；不含问题3，不读取附件3/4，不覆盖官方 `result2.xlsx`。
- 预运行返修：`Q2-PRE-RUN-PATCH-001` 已加入正式输入SHA-256硬门、事后预测评价、统一manifest、公共dispatch空值语义及失败证据落盘。

Q2 的无 Solver 检查及正式人工运行命令见 `Q2_人工运行说明.md`。运行目录若已存在会被拒绝。
