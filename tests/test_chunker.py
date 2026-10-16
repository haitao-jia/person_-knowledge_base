"""
文件名：tests/test_chunker.py
作用：分块模块单元测试（不依赖外部 API 与数据库）。
对应规范：SPEC.md §10.2 用例清单、§10.3 验收标准
          - test_split_documents：长文本被拆为多个非空片段；
            chunk_index 存在；源元数据保留
待实现：
    - 构造超长 Document 后调用 split_documents 断言
    - 运行：pytest -q
"""
