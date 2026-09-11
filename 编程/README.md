# 编程分区

本分区保存可执行代码、参数配置、验证记录与人工运行说明；原始附件只读，任何候选输出必须写入全新目录。

## 当前阶段状态

- 当前阶段：5（公共编程底座 + 问题1确定性基线）
- 当前状态：待人工运行
- 人工授权：`HUMAN-OVERRIDE-CODE-001 = CONFIRMED`
- 时间门禁：`Q1-TIME-MAPPING-PASS = CONFIRMED`
- 模型版本：`M1-Q1-MILP-v1.3-instant-left-hold`
- 数据版本：`PREP-TIME-REV-20260911T170805+0800`
- 已实现：公共配置/数据契约、B0闭式基线、B1 MILP构造、惰性 Solver backend、断言、候选工作簿导出与回读验证。
- 未执行：正式附件求解、真实候选结果导出、调参、正式绘图、问题2及 Git 操作。

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

实际 B1 求解与 `result1_candidate.xlsx` 生成只能由人工按 `Q1_人工运行说明.md` 显式执行。运行目录若已存在会被拒绝，官方 `result1.xlsx` 永不作为输出目标。
