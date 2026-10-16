
"""
文件名：app/db/database.py
作用：数据库连接管理。创建数据库引擎、会话工厂、ORM 基类，
      并提供 get_db 依赖，供 FastAPI 接口使用。
对应规范：SPEC.md §6.1 通用约定、§4 目录结构
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

##settings是config配置的env读取文件
from app.core.config import settings

# ============ 1. 数据库引擎：真正和 PostgreSQL 建立连接的"管道" ============
# pool_pre_ping=True：每次取连接前先测试连接是否还活着，
#                     避免用到已经断开的连接（比如数据库重启后）
engine = create_engine(
    settings.database_url,  # 连接地址，来自上一步的 settings（.env 的 DATABASE_URL）
    pool_pre_ping=True,
)

# ============ 2. 会话工厂：操作数据库的"入口" ============
# 注意：SessionLocal 本身不是会话，调用 SessionLocal() 才得到一个会话
# autoflush=False：查询前不自动把未提交的修改刷进数据库（行为更可控）
# expire_on_commit=False：commit 之后对象属性不失效，提交完还能继续读
SessionLocal = sessionmaker(
    bind=engine,  # 把引擎绑进来，会话才知道连哪个数据库
    autoflush=False,
    expire_on_commit=False,
)

# ============ 3. ORM 基类：所有表模型都继承它 ============
# 下一步 models.py 里的 documents、document_chunks 两个模型会继承 Base，
# SQLAlchemy 才能根据模型自动建表
class Base(DeclarativeBase):
    pass


# ============ 4. get_db：FastAPI 的依赖函数 ============
# FastAPI 接口里写 db: Session = Depends(get_db) 就能拿到一个会话
# yield 前面 = 请求开始时的准备（创建会话）
# yield 后面 = 请求结束时的清理（关闭会话）——无论接口成功失败都会执行
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
