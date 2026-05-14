# Chainlit 界面说明

本项目的 Web UI 由 **Chainlit** 启动（`chainlit run appUI.py`）。会话侧使用 **AutoGen AgentChat** 与 **DeepSeek**（见根目录 `config.py`）；检索侧通过工具调用 **GraphRAG** 的本地/全局查询（需已在本目录完成 `python -m graphrag index --root .`）。

## 部署与排错

完整环境要求、虚拟环境、GraphRAG 初始化与索引、配置注意事项等，见仓库根目录 **[README.md](README.md)**。
