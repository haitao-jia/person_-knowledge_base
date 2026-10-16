
"""
文件名：app/api/documents.py
作用：文档相关的 HTTP 接口：上传文档、列出所有文档、查看单个文档。
对应规范：SPEC.md §9.1 文档管理接口
"""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import DocumentModel
from app.services.ingestion import ingest_file

# 路由分组：这个文件负责所有 /api/documents 开头的接口
router = APIRouter(prefix="/api/documents", tags=["documents"])

# 上传文件的保存目录
UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)   # 目录不存在就自动创建


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),          # 接收上传的文件
    db: Session = Depends(get_db),           # 自动注入数据库会话
):
    # 第 1 步：把上传的文件先存到 storage/uploads 目录
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())          # await：异步读取上传内容

    # 第 2 步：调入库流水线（解析→切块→向量化→写库）
    try:
        doc_id = ingest_file(file_path, db)
    except Exception as e:
        # 解析失败/格式不支持：返回 400 错误
        raise HTTPException(status_code=400, detail=str(e))

    return {"document_id": doc_id, "filename": file.filename, "status": "completed"}


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    # 查出所有文档，按 id 倒序（新上传的排前面）
    docs = db.query(DocumentModel).order_by(DocumentModel.id.desc()).all()
    return [
        {"id": d.id, "filename": d.filename, "file_type": d.file_type, "status": d.status}
        for d in docs
    ]


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    # 按 id 查单个文档；查不到返回 404
    doc = db.get(DocumentModel, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "status": doc.status,
    }
