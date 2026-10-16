
"""
文件名：app/services/rag_service.py
作用：问答编排（RAG 的"大脑"）。
      向量检索相关片段 → 拼成参考资料 → 调 DeepSeek 生成答案 → 返回答案+出处。
对应规范：SPEC.md §8.6 RAG 问答
"""

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import DocumentModel
from app.services.vector_store import search_chunks

# 创建 DeepSeek 客户端：
# DeepSeek 也兼容 OpenAI 接口，所以直接用 openai SDK，只改 base_url
chat_client = OpenAI(
    api_key=settings.chat_api_key,
    base_url=settings.chat_base_url,
)

# 系统提示词：告诉大模型"你是谁、按什么规则回答"
# 这是 RAG 防幻觉的关键条款：只许用参考资料，不许编造
SYSTEM_PROMPT = """你是企业知识库问答助手。
规则：
1. 只能根据下方【参考资料】回答用户问题。
2. 如果参考资料里没有答案，直接说"知识库中没有找到相关内容"，不要编造。
3. 回答要简洁准确。
"""


def ask_question(db: Session, question: str) -> dict:
    """输入：数据库会话 + 用户问题；输出：{answer, sources}"""

    # 第 1 步：向量检索——找最相关的 5 个块（vector_store 写的）
    chunks = search_chunks(db, question, top_k=5)

    # 兜底：一个相关块都没找到，直接返回提示，不调用大模型（省钱）
    if not chunks:
        return {
            "answer": "知识库中没有找到相关内容，请换个问法或联系管理员补充文档。",
            "sources": [],
        }

    # 第 2 步：每个块只知道 document_id，需要去 documents 表查出文件名
    # doc_ids 是"涉及到哪些文档"的集合（去重）
    doc_ids = {c["document_id"] for c in chunks}
    docs = db.execute(
        select(DocumentModel).where(DocumentModel.id.in_(doc_ids))
    ).scalars().all()
    # 做成 {文档id: 文件名} 的对照表，方便后面查
    filename_map = {d.id: d.filename for d in docs}

    # 第 3 步：把 5 个块拼成一大段"参考资料"文本
    context_text = ""
    for i, chunk in enumerate(chunks, start=1):
        filename = filename_map.get(chunk["document_id"], "未知文件")
        page = f" 第{chunk['page_number']}页" if chunk.get("page_number") else ""
        context_text += f"[资料{i}]（{filename}{page}）\n{chunk['content']}\n\n"

    # 第 4 步：调用 DeepSeek 生成答案
    response = chat_client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            # user 消息 = 参考资料 + 问题，打包发给大模型
            {"role": "user", "content": f"【参考资料】\n{context_text}\n\n【问题】{question}"},
        ],
        temperature=0.3,   # 低温度：回答稳定、不自由发挥（RAG 问答都用低温）
    )
    answer = response.choices[0].message.content

    # 第 5 步：整理引用来源——用到了哪些文件（按文件名去重）
    seen = set()
    sources = []
    for c in chunks:
        name = filename_map.get(c["document_id"], "未知文件")
        if name not in seen:
            seen.add(name)
            sources.append({"filename": name})

    return {"answer": answer, "sources": sources}
