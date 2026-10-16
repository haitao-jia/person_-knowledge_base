
"""
文件名：app/main.py
作用：FastAPI 应用入口。创建应用实例、启动时自动建表、
      提供健康检查接口。
对应规范：SPEC.md §2.1 系统架构图、§4 目录结构、
          §7.1 接口通用约定、§7.2 健康检查、§11.3 启动与验证
"""

from contextlib import asynccontextmanager  # 用来写"应用启动/关闭时做什么"

from fastapi import FastAPI

from app.db.database import Base, engine
from app.db import models  # 导入模型模块，让 create_all 能看到两张表的"图纸"
from app.api import documents, chat

# lifespan：FastAPI 新版推荐的"应用生命周期"写法
# （替代已经弃用的 @app.on_event("startup")，SPEC §4 说明）
# yield 之前 = 应用启动时执行；yield 之后 = 应用关闭时执行
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时自动建表：只创建"还不存在"的表，重复启动不会报错（幂等）
    Base.metadata.create_all(bind=engine)
    yield


# 创建应用实例，把上面定义的生命周期挂到应用上
app = FastAPI(title="Enterprise RAG API", lifespan=lifespan)

app.include_router(documents.router)
app.include_router(chat.router)
# @app.get("/health")：注册一个路由——浏览器 GET /health 就调用下面的函数
@app.get("/health")
def health_check():
    """健康检查：用来探测服务是否活着，返回固定 JSON"""
    return {"status": "ok"}


# ============================================================
# 后续第 7、8 步会在这里注册业务路由，例如：
#   from app.api.documents import router as documents_router
#   from app.api.chat import router as chat_router
#   app.include_router(documents_router)
#   app.include_router(chat_router)
# ============================================================
