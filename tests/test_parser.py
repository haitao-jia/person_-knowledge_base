"""
文件名：tests/test_parser.py
作用：解析模块单元测试（不依赖外部 API 与数据库）。
对应规范：SPEC.md §10.2 用例清单、§10.3 验收标准
          - test_parse_markdown：MD 解析提取文本与文件名
          - test_parse_excel：XLSX 解析提取单元格与 sheet_name
待实现：
    - 使用 tmp_path 构造临时文件后调用 parse_file 断言
    - 运行：pytest -q
"""
