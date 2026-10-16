"""
文件名：app/schemas/chat.py
作用：问答接口的 Pydantic 数据模型（请求/响应格式约定）。
      统一放在 schemas/ 目录，与 api/ 路由层职责分离：
      api/ 只管路由逻辑，schemas/ 只管"数据长什么样"。
对应规范：SPEC.md §9.2 问答接口
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """
    请求体格式约定：
    前端发来的 JSON 必须长这样：{"question": "住宿费怎么报销"}
    FastAPI 会自动按这个格式校验——少了 question 字段会自动返回 422 错误
    """
    question: str
