# 企业智能知识库问答系统（Enterprise RAG）

基于 **FastAPI + PostgreSQL/pgvector + 国产大模型** 的 RAG（检索增强生成）后端。
用户上传企业文档（PDF / Word / Markdown / TXT / Excel），系统自动完成解析、分块、向量化与入库；
用户提问后，系统基于向量相似度召回相关片段，调用大模型生成**可追溯引用来源**的回答。

---

## 核心功能

- 📄 **多格式文档解析**：PDF（PyMuPDF 逐页）/ Word（python-docx）/ Markdown / TXT / Excel（openpyxl）
- ✂️ **语义分块**：递归字符切分（chunk_size=800，overlap=120），优先按段落、句子边界切分
- 🔢 **向量化入库**：调用阿里云百炼 Embedding 模型（1024 维），写入 pgvector 向量列
- 🔍 **语义检索**：余弦距离 Top-K（默认 5），按语义而非关键词匹配
- 💬 **RAG 问答**：召回片段作为参考资料注入 Prompt，约束大模型"无依据不回答"，并返回引用来源
- 📚 **自动接口文档**：FastAPI 自带 Swagger UI（`/docs`），可直接在浏览器里上传文档、提问

---

## 技术栈

| 层级 | 选型 | 说明 |
| --- | --- | --- |
| Web 框架 | FastAPI + Uvicorn | 异步接口、自动校验、自带 Swagger 文档 |
| ORM | SQLAlchemy 2.x | 表模型 + 原生 SQL 构造向量检索 |
| 数据库 | PostgreSQL 16 + pgvector | Docker 部署，向量列 `vector(1024)` |
| Embedding | 阿里云百炼 `qwen3.7-text-embedding-flash` | OpenAI 兼容接口，1024 维 |
| LLM | DeepSeek `deepseek-v4-flash` | OpenAI 兼容接口，temperature=0.3 |
| 文档解析 | PyMuPDF / python-docx / openpyxl | 多格式统一解析为 Document |
| 配置管理 | pydantic-settings + .env | 配置与代码分离 |

---

## 系统架构

```
                        ┌─────────────────────────────────────┐
浏览器 / 前端            │                                     │
   │  HTTP              │                                     │
   ▼                    ▼                                     │
┌──────────────────────────────┐                              │
│  app/api/                   │                              │
│  ├─ documents.py 上传/列表  │                              │
│  └─ chat.py       问答      │                              │
└──────────────┬───────────────┘                              │
               │ 调用                                         │
               ▼                                              │
┌──────────────────────────────┐                              │
│  app/services/               │                              │
│  ingestion.py   入库编排     │                              │
│    ├─ parser.py     解析     │                              │
│    ├─ chunker.py    分块     │                              │
│    └─ embedding.py 向量化 ──┼──► 百炼 Embedding API        │
│  rag_service.py  问答编排    │                              │
│    ├─ vector_store.py 检索 ──┼──► PostgreSQL + pgvector    │
│    └─ 调用 DeepSeek    ──────┼──► DeepSeek Chat API         │
└──────────────────────────────┘                              │
               │                                              │
               ▼                                              │
        app/db/models.py ─────────────────────────────────────┘
        documents / document_chunks 两张表
```

**问答流程**：问题 → Embedding 向量化 → pgvector 余弦距离 Top-K → 拼参考资料 → DeepSeek 生成 → 返回答案 + 引用来源。

---

## 项目结构

```text
企业知识库RAG/
├── app/
│   ├── main.py                # FastAPI 入口：注册路由、启动时自动建表
│   ├── core/config.py         # 配置读取（.env）
│   ├── db/
│   │   ├── database.py        # 数据库连接、Session、依赖注入
│   │   └── models.py          # ORM 表模型（documents / document_chunks）
│   ├── schemas/
│   │   └── chat.py            # Pydantic 请求模型（ChatRequest）
│   ├── api/
│   │   ├── documents.py       # 上传文档 / 文档列表 / 文档详情
│   │   └── chat.py            # 问答接口
│   └── services/
│       ├── parser.py          # 多格式文档解析
│       ├── chunker.py         # 文本分块
│       ├── embedding.py       # 调用 Embedding API（含分批、维度校验）
│       ├── vector_store.py    # pgvector 向量检索
│       ├── ingestion.py       # 入库编排（解析→分块→向量化→写库）
│       └── rag_service.py     # 问答编排（检索→拼 Prompt→调 LLM）
├── storage/uploads/           # 上传文件落盘目录
├── docker-compose.yml         # pgvector 数据库编排
├── requirements.txt
├── .env.example               # 配置模板
├── SPEC.md                    # 完整技术规范
└── README.md
```

---

## 快速启动

### 前置要求

- Python 3.11+
- Docker Desktop（用于跑 pgvector 数据库）
- 阿里云百炼 API Key（Embedding）+ DeepSeek API Key（Chat）

### 步骤

**1. 启动数据库**

```powershell
docker compose up -d
```

数据库容器启动后，启用 vector 扩展：

```powershell
docker exec -it enterprise-rag-db psql -U raguser -d enterprise_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

> 注意：主机映射端口为 **5433**（非默认 5432）。

**2. 安装依赖**

```powershell
pip install -r requirements.txt
```

**3. 配置环境变量**

复制 `.env.example` 为 `.env`，填入：

```env
DATABASE_URL=postgresql+psycopg://raguser:change_this_password@localhost:5433/enterprise_rag
EMBEDDING_API_KEY=你的百炼key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=qwen3.7-text-embedding-flash
EMBEDDING_DIMENSION=1024
CHAT_API_KEY=你的DeepSeek key
CHAT_BASE_URL=https://api.deepseek.com
CHAT_MODEL=deepseek-v4-flash
```

**4. 启动服务**

```powershell
uvicorn app.main:app --reload
```

浏览器打开 Swagger UI：**http://127.0.0.1:8000/docs**

- `POST /api/documents/upload`：上传文档（自动解析、分块、向量化、入库）
- `POST /api/chat`：提问，返回答案和引用来源

---

## 主要接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| POST | `/api/documents/upload` | 上传文档并入库（multipart/form-data） |
| GET | `/api/documents` | 文档列表 |
| GET | `/api/documents/{id}` | 文档详情 |
| POST | `/api/chat` | 问答，请求体 `{"question": "..."}` |

---

## 已实现 / 后续优化

**已实现（M1+M2）**：多格式解析、递归分块、百炼向量化、pgvector 检索、RAG 问答、引用来源、Swagger 接口联调。

**已知限制 & 可优化方向**：

- 扫描版 PDF 无法提取文本（需接入 OCR）
- 检索无距离阈值兜底：当问题与知识库完全无关时，仍会召回距离较远的片段（后续可加距离阈值直接返回"未找到"）
- 单用户、无权限管理、无删除/重入库接口
- 前端界面、流式输出、问答日志、效果评估均未实现

---

## 技术要点（开发中解决的问题）

- **百炼 Embedding 批量上限 20 条**：入库时按 20 条分批调用 API
- **OpenAI 兼容服务需关闭 LangChain 预分词**：`check_embedding_ctx_length=False`，否则百炼报 `contents is neither str nor list of str`
- **维度强校验**：入库前校验每个向量维度 = 1024，防止错误向量写入 `vector(1024)` 列
