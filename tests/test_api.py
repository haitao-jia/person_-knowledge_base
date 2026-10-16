"""
文件名：tests/test_api.py
作用：接口集成测试（依赖真实数据库与模型 API，或使用 mock）。
      覆盖"上传 → 入库 → 检索 → 问答"全链路。
对应规范：SPEC.md §10.2 用例清单、§10.3 验收标准
          - 上传入库：上传后文档状态为 indexed，分块可检索
          - RAG 问答：回答含来源片段；无相关资料时合理拒答
待实现：
    - 使用 httpx / TestClient 调用 FastAPI 接口
    - 需要真实 PostgreSQL + pgvector（docker compose up -d）
    - 模型 API 调用建议以 mock 方式隔离（SPEC §10.1）
"""
