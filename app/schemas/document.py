"""
文件名：app/schemas/document.py
作用：Pydantic 数据模型（预留）。定义文档上传、文档列表、
      问答请求等接口的请求/响应校验模型。
对应规范：SPEC.md §4 目录结构、§7 接口规范（7.3 上传、
          7.4 列表、7.5 问答）、§10 测试规范
待实现（按 SPEC §7 的 JSON 结构定义）：
    - 上传响应：document_id / filename / status
    - 文档列表项：id / filename / file_type / status
    - 问答请求：question（长度 1-2000，Field(min_length=1, max_length=2000)）
    - 问答响应：answer / sources
    - 来源项：document_id / chunk_id / page_number / content / distance
"""
