

"""
文件名：app/db/models.py
作用：ORM 数据模型。定义第一版两张核心表：
      documents（文档主表）与 document_chunks（分块表）。
对应规范：SPEC.md §6 数据模型规范
          - 6.2 documents 表字段定义
          - 6.3 document_chunks 表字段定义
          - 6.4 关系与索引约束（外键级联、向量维度）
          - 6.5 文档处理状态机
"""

import uuid  # 生成 UUID 字符串，用作每行记录的主键

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import VECTOR  # pgvector 提供的"向量"字段类型

from app.core.config import settings  # 取向量维度配置（1024）
from app.db.database import Base  # 继承上一步的 ORM 基类


class DocumentModel(Base):
    """文档主表：记录"上传了哪个文件、处理到什么状态"。"""

    __tablename__ = "documents"  # 数据库里的表名

    id: Mapped[str] = mapped_column(
        String(36),  # 主键：36 位字符串
        primary_key=True,  # 主键（唯一标识一行）
        default=lambda: str(uuid.uuid4()),  # 没传值时就自动生成一个 UUID
    )
    filename: Mapped[str] = mapped_column(String(255))  # 原始文件名
    file_type: Mapped[str] = mapped_column(String(20))  # 文件类型：pdf/docx/md/txt/xlsx
    status: Mapped[str] = mapped_column(
        String(30), default="uploaded"
    )  # 处理状态，默认 uploaded


class DocumentChunkModel(Base):
    """分块表：一个文档被切成很多块，每块一行，存文本 + 向量。"""

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    document_id: Mapped[str] = mapped_column(
        #`CASCADE` = 删掉文档时，它的所有分块**自动跟着删**
        ForeignKey("documents.id", ondelete="CASCADE"),  # 外键：指向 documents.id
        index=True,  # 建索引，按文档过滤时检索更快
    )
    content: Mapped[str] = mapped_column(Text)  # 分块文本内容
    page_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 页码（PDF 有，其他可空）
    chunk_index: Mapped[int] = mapped_column(Integer)  # 块在文档内的顺序号（从 0 开始）
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(settings.embedding_dimension)  # 向量列，维度取配置的 1024
    )

