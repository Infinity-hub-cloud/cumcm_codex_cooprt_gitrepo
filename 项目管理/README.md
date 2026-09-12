# 项目管理与全量索引

本目录负责文件资产盘点，不保存模型结果。更新时间：2026-09-12。

## 文件

- `文件资产清单_20260912.csv`：除 `.git/` 内部对象外的全量项目文件索引；包含相对路径、类别、生命周期状态、字节数、修改时间和 SHA-256。清单自身及摘要自身使用 `SELF_NOT_HASHED`，避免自引用哈希。
- `资产状态摘要_20260912.json`：按类别和状态统计文件数、总字节数，并记录排除规则。
- `迁移记录_20260912.md`：本轮唯一实体移动的来源、目标和哈希。
- `工作区整理核验报告_20260912.md`：整理范围、状态校正、覆盖率和验证结论。
- `生成文件资产清单.py`：只读扫描共享区并机械重建前两项，不读取 `.git/`，不移动、删除或改写其他文件。
- `检查README链接.py`：检查项目自有 README 的相对链接；自动跳过第三方工具包，不修改任何文件。

## 使用方法

论文手先看共享区根 `README.md`，需要精确定位文件时再筛选 CSV 的 `asset_class`、`lifecycle_status` 或 `paper_use` 列。常用状态：

- `CURRENT`、`ACCEPTED_FROZEN`、`PASSED_EVIDENCE`：当前可追溯入口；仍需遵守每项证据边界。
- `PENDING_HUMAN_RUN`：实现已就绪但没有新的正式数值。
- `HISTORICAL`、`OBSOLETE_Q3_SEMANTICS`：只作审计和复现，不得形成当前结论。
- `OFFICIAL_READ_ONLY`、`VENDOR_READ_ONLY`：只读材料。
- `GENERATED_CACHE`：非交付缓存。

新增、移动或验收文件后，在共享区根目录执行：

```powershell
python 项目管理/生成文件资产清单.py
python 项目管理/检查README链接.py
```

生成后必须重新运行 README 相对链接检查。清单用于导航，不替代运行 manifest、人工验收或官方题面。
