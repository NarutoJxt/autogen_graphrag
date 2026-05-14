# GraphRAG + AutoGen (AgentChat) + Chainlit

Chainlit 界面里用 **DeepSeek**（OpenAI 兼容 API）驱动对话智能体，并通过 **GraphRAG** 的 `query_graphRAG` 工具做本地/全局知识检索。索引阶段可在 `settings.yaml` 中配置 **Ollama** 等本地模型。

![Graphical Abstract](https://github.com/karthik-codex/autogen_graphRAG/blob/main/images/1721017707759.jpg?raw=true)

## 环境要求

| 组件 | 说明 |
|------|------|
| **Python** | **3.11–3.13**（推荐 **3.12**）。PyPI 上的 `graphrag` 当前不支持 **3.14**。 |
| **DeepSeek** | 对话模型：`appUI.py` 通过 `config.py` 调用 `https://api.deepseek.com/v1`。需有效 API Key。 |
| **Ollama**（可选） | 若 `settings.yaml` 里 GraphRAG 的 `llm` / `embeddings` 指向本机 Ollama，则索引与嵌入需要本机已安装并 `ollama serve`。 |
| **磁盘** | 建索引后会产生 `output/`、`cache/` 等目录（体积随语料变化）。 |

## 部署步骤（Windows / Linux 通用）

以下命令在项目根目录执行（含 `appUI.py`、`settings.yaml` 的目录）。

### 1. 获取代码

```bash
git clone <本仓库地址>
cd Autogen_GraphRAG_Ollama
```

### 2. 创建虚拟环境（务必用 3.12 等受支持版本）

**Windows（PowerShell）：**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

**Linux / macOS：**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置对话模型（DeepSeek）

```bash
copy config.example.py config.py
```

（Linux / macOS：`cp config.example.py config.py`）

编辑 **`config.py`**，至少填写：

- `API_KEY_DEEPSEEK`：DeepSeek API Key  
- `BASE_URL_DEEPSEEK`：一般为 `https://api.deepseek.com/v1`  
- `CHAT_MODEL_DEEPSEEK`：一般为 `deepseek-chat`  

**不要将含真实密钥的 `config.py` 提交到 Git。**

### 5. GraphRAG 工程文件

- 若目录下**还没有** `settings.yaml` / `prompts/`，在项目根执行：

  ```bash
  python -m graphrag init --root .
  ```

  若提示已存在，可备份后使用 `python -m graphrag init --root . --force`（会覆盖配置，慎用）。

- 仓库内 **`utils/settings.yaml`** 可作为 Ollama 等场景的参考；需要时可复制为根目录的 `settings.yaml` 再按需修改。

- 在项目根创建 **`.env`**（或与 `settings.yaml` 中变量一致），例如：

  ```env
  GRAPHRAG_API_KEY=ollama
  ```

  `settings.yaml` 里 `${GRAPHRAG_API_KEY}` 会在加载配置时被替换。

### 6. 检查 `settings.yaml` 中与 GraphRAG 加载器相关的约定

GraphRAG 会用 **`string.Template`** 预处理整份 YAML：

- 正则里若需要字面量 **`$`**（如行尾 `$`），在 YAML 里需写成 **`$$`**，或避免在会被模板解析的字符串里单独使用 `$`。  
- **`${timestamp}`** 等占位符对应**环境变量**；若未设置会报错。本仓库示例已将 `storage` / `reporting` 的 `base_dir` 改为固定路径（如 `output/artifacts`），无需 `timestamp` 环境变量。

### 7. 准备语料并建立索引

```bash
mkdir -p input/markdown
# 将 .md 文件放入 input/markdown
python -m graphrag index --root .
```

说明：

- 正确 CLI 为 **`python -m graphrag index`**（`index` 是子命令），**不要**使用 `python -m graphrag.index`。  
- 初始化用 **`python -m graphrag init --root .`**，不是 `index --init`。

### 8. 启动 Web UI

```bash
chainlit run appUI.py
```

浏览器打开终端提示的地址（默认多为 `http://localhost:8000`）。首次使用需在界面里完成 GraphRAG 相关开关与参数设置。

---

## 不再需要的旧步骤（与当前 GraphRAG 版本不兼容）

以下内容来自早期教程，**当前仓库不必执行**：

- ~~把 `utils/embedding.py`、`openai_embeddings_llm.py` 复制进 `site-packages/graphrag/...`~~（新版包路径与加载方式已变，应通过 **`settings.yaml` 的 `embeddings.llm`** 指向 Ollama/OpenAI 兼容端点。）  
- ~~`python -m graphrag.index --init`~~（命令错误；应使用 **`python -m graphrag init`**。）  
- **LiteLLM 代理**：当前 `appUI.py` 直连 **DeepSeek**，不依赖本机 `litellm --model ...`，除非你自己改回代理架构。

---

## 可选：仅用 Ollama 做对话（需支持 tools 的模型）

若改回本地 Ollama，需使用 **支持 function calling** 的模型（如部分 `llama3.1` 标签）；`llama3:latest` 在 Ollama 侧可能报「does not support tools」。并需在 `appUI.py` 的 `get_model_client()` 中改为 `OpenAIChatCompletionClient(..., base_url=http://localhost:11434/v1, ...)` 及合适的 `model_info`。

---

## 参考链接

- 原 Medium 思路：[GraphRAG + AutoGen + Ollama + Chainlit](https://medium.com/@karthik.codex/microsofts-graphrag-autogen-ollama-chainlit-fully-local-free-multi-agent-rag-superbot-61ad3759f06f)  
- [GraphRAG](https://github.com/microsoft/graphrag)  
- [AutoGen](https://github.com/microsoft/autogen)  
- [Chainlit](https://github.com/Chainlit/chainlit)

![Main Interface](https://github.com/karthik-codex/autogen_graphRAG/blob/main/images/UI1.webp?raw=true)

![Widget Settings](https://github.com/karthik-codex/autogen_graphRAG/blob/main/images/U2.webp?raw=true)
