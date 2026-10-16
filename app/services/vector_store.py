
"""
文件名：app/services/vector_store.py
作用：向量检索。把问题变成向量后，在 document_chunks 表里
      按余弦距离找最近的 Top-K 个片段返回。
对应规范：SPEC.md §8.4 向量检索
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunkModel
from app.services.embedding import embed_query


def search_chunks(db: Session, question: str, top_k: int = 5) -> list[dict]:
    """
    输入：数据库会话 db、用户问题、取前 top_k 个（默认 5）
    输出：最相关的片段列表，每段含内容、出处、距离
    """
    # 第 1 步：把用户问题变成向量（调上一步写好的 embed_query）
    query_vector = embed_query(question)

    # 第 2 步：构造 SQL——
    #   取出 DocumentChunkModel 的全部字段，
    #   额外计算一列"余弦距离"（query_vector 和这行的 embedding 有多近），
    #   按距离从小到大排序，只取前 top_k 条
    statement = (
        select(
            DocumentChunkModel,
            DocumentChunkModel.embedding.cosine_distance(query_vector).label("distance"),
        )
        .order_by(
            DocumentChunkModel.embedding.cosine_distance(query_vector)
        )
        .limit(top_k)
    )

    # 执行 SQL，拿到"（一行数据, 距离值）"的结果
    results = db.execute(statement).all()

    # 第 3 步：把结果整理成字典列表返回
    return [
        {
            "chunk_id": chunk.id,          # 片段 ID
            "document_id": chunk.document_id,  # 来自哪个文档
            "content": chunk.content,      # 片段正文
            "page_number": chunk.page_number,  # 页码（可能为 None）
            "chunk_index": chunk.chunk_index,  # 块序号
            "distance": float(distance),   # 余弦距离（越小越相关）
        }
        for chunk, distance in results
    ]
