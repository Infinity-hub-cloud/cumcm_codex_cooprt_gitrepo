# 推荐提示词

请使用 `cumcm-paper-intelligence -> cumcm-paper-architecture -> cumcm-paper-draft`，并结合 `math-modeling-paper-pro`。先扫描项目一次并建立 `.paper/paper_context.md`；再按真实问题依赖生成论文主线、目录和正文初稿。共享数学只定义一次，各问按“继承关系/新增量 -> 模型 -> 求解理由 -> 决定性结果 -> 解释 -> 验证/边界”展开。只使用可追溯的模型、公式、数字和图表，不编造、不夸大最优性或因果性；证据缺失处标 `TODO[证据缺口]`，其余继续完成。优先直接更新现有 LaTeX/Markdown 工程。完成后用 `sepia review -> refactor`，再运行 `cumcm-paper-audit` 修复可安全修复的问题并给出剩余阻塞项。
