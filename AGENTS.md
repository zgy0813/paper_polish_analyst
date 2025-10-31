# Repository Guidelines

## 项目结构与模块组织
- `src/analysis` 集成增量分析、分层分析、质量评分与风格指南生成逻辑；`src/polishing` 负责多轮润色与风格选择；`src/utils` 和 `config.py` 统一日志、配置与模型调度。
- `data/` 保存期刊语料、分析缓存与生成的指南；避免将新的 `.json` 或大文件提交，必要时更新 `.gitignore`。
- `tests/` 提供 `unittest` 风格用例，可通过 `pytest` 运行；`docs/` 汇总架构与参数说明，`logs/` 存储调试与错误日志，便于回溯问题。

## 构建、测试与开发命令
- `python -m venv venv && source venv/bin/activate` 创建隔离环境。
- `pip install -r requirements.txt` 安装依赖后记得执行 `python -m spacy download en_core_web_md`。
- `python main.py analyze -i data/journals -o data/hybrid_style_guide.json` 批量生成混合风格指南，`-b/-m` 控制批次与上限。
- `python main.py polish -t "Abstract..." --no-interactive` 基于现有指南润色文本，或改用 `-f` 指定稿件。
- `python main.py status` 检查配置与缓存是否齐全；`streamlit run app.py` 在本地调试可视化界面。
- `pytest` 或 `pytest tests/test_style_selector.py` 运行全部或指定测试，提交前确保通过。

## 代码风格与命名约定
- 采用 Python 3.9+ 与四空格缩进，函数和变量沿用 `snake_case`，类名使用 `PascalCase`，模块命名与目录保持语义一致。
- 新增模块需补充 docstring，复杂流程在关键分支添加简洁注释。保持输入输出可序列化，便于 CLI 与 Web 共用。
- 统一使用 `black src tests` 与 `flake8 src tests` 格式化和静态检查，提交前确保无未修复告警。

## 测试规范
- 优先基于现有 `unittest` 模式扩展；若新增 PyTest 功能，请提供兼容的断言与 fixtures。
- 涉及外部 API 时以本地样例或假数据替代，避免在 CI 环境泄露密钥。
- 新增分析或润色策略需包含边界与错误路径测试，并更新相关样例数据。

## 提交与 PR 指南
- 遵循现有提交历史，使用英文祈使句概述变更，例如 `Update logging pipeline`；主题行尽量控制在 72 字符内。
- PR 描述需包含问题背景、核心改动、手动验证步骤及相关 `issue` 链接；界面或交互调整请附截图或终端输出。
- 推送前执行主要命令（分析、润色、测试）验证，确保日志无未捕获错误。

## 配置与安全提示
- 将 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY` 等敏感信息保存在 `.env` 或环境变量中，不要记录在提交或日志内。
- 默认配置写入 `config.py`，个性化调优建议放入 `docs/` 或自定义配置文件，避免直接改动常量导致冲突。
