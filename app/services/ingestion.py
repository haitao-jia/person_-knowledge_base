
"""
文件名：app/services/ingestion.py
作用：入库编排（数据流水线的传送带）。
      把"解析 → 切块 → 向量化 → 写数据库"串成一条龙。
      整个项目里，第一次真正往数据库写数据的地方。
对应规范：SPEC.md §8.5 数据入库
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import DocumentModel, DocumentChunkModel
from app.services.parser import parse_file
from app.services.chunker import split_documents
from app.services.embedding import embed_documents


def ingest_file(file_path: str | Path, db: Session) -> int:
    """
    输入：要入库的文件路径 + 数据库会话
    输出：新文档在 documents 表里的 id
    """
    path = Path(file_path)

    # 第 1 步：解析文件 → Document 列表（parser 写的）
    parsed = parse_file(path)

    # 第 2 步：切块 → 小 Document 列表（chunker 写的）
    chunks = split_documents(parsed)

    # 第 3 步：批量向量化——把所有块的正文一次性发给百炼
    texts = [c.page_content for c in chunks]   # 取出所有块的正文，拼成一个列表
    vectors = embed_documents(texts)            # 每个文本对应一个 1024 维向量

    # 第 4 步：往 documents 表插一行（一篇文档 = 一条记录）
    document = DocumentModel(
        filename=path.name,                    # 文件名
        file_type=path.suffix.lstrip("."),     # 后缀去掉点，如 ".md" → "md"
        status="completed",                    # 入库完成标记
    )
    db.add(document)
    # flush：把这条 INSERT 先发给数据库（但还没正式提交），
    # 目的是拿到数据库自动生成的 document.id，给下面的 chunk 表用
    db.flush()

    # 第 5 步：往 document_chunks 表插多行（一个块 = 一条记录）
    chunk_rows = []
    # zip(chunks, vectors)：把"块"和它对应的"向量"一一配对
    for chunk, vector in zip(chunks, vectors):
        chunk_rows.append(DocumentChunkModel(
            document_id=document.id,            # 指向所属文档（外键）
            content=chunk.page_content,         # 这块的正文
            embedding=vector,                   # 这块的向量（1024维）
            # metadata.get(...)：Word/MD 可能没有页码，取不到就存 None（表里允许空）
            page_number=chunk.metadata.get("page_number"),
            chunk_index=chunk.metadata.get("chunk_index"),
        ))
    db.add_all(chunk_rows)   # 一次把所有块都加进会话

    # 第 6 步：commit——到这一步，数据才真正落盘写进数据库
    db.commit()

    return document.id
