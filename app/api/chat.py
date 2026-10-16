
"""
文件名：app/api/chat.py
作用：问答 HTTP 接口。接收用户问题，调 rag_service 生成答案，返回答案和引用来源。
对应规范：SPEC.md §9.2 问答接口
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.services.rag_service import ask_question

# 路由分组：这个文件负责所有 /api/chat 开头的接口
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    # 调用 RAG 问答编排（rag_service 写的：检索→拼资料→调DeepSeek）
    result = ask_question(db, req.question)
    # ask_question 返回 {"answer": ..., "sources": ...}，直接原样返回给前端
    return result
