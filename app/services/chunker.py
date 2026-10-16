
"""
文件名：app/services/chunker.py
作用：文本分块。把 parser 解析出的长文档，切成适合检索的小片段（chunk）。
对应规范：SPEC.md §8.2 文本分块
          chunk_size=800、chunk_overlap=120、保留元数据并补 chunk_index
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents: list[Document]) -> list[Document]:
    """
    输入：parser 解析出的 Document 列表
    输出：切好的小片段列表（每个片段也是一个 Document，带原元数据 + chunk_index）
    """
    # RecursiveCharacterTextSplitter：递归字符切分器
    # 它会按优先级尝试各种边界，尽量在"自然位置"切分
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,        # 每块目标长度：约 800 个字符
        chunk_overlap=120,     # 相邻两块重叠 120 个字符，避免一句话正好被从中间切断
        add_start_index=True,  # 在元数据里记录这块在原文的起始位置
        separators=[           # 切分边界的优先级（排在前面的先试）：
            "\n\n",            #   ① 段落之间空行——最理想
            "\n",              #   ② 换行
            "。", "！", "？", "；",  # ③ 中文句子标点——按句号切
            " ",               #   ④ 空格
            "",                #   ⑤ 实在不行就按单个字符硬切（最后手段）
        ],
    )

    # 执行切分：传入文档列表，返回切好的片段列表
    chunks = splitter.split_documents(documents)

    # 给每个片段补一个全局序号 chunk_index（第 0 块、第 1 块……）
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    return chunks
