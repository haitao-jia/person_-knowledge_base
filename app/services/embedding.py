
"""
文件名：app/services/embedding.py
作用：向量化服务。调用阿里云百炼的 OpenAI 兼容 Embedding 接口，
      把文本转成数字向量，并执行输出维度强校验。
对应规范：SPEC.md §8.3 Embedding
"""

from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

# 创建 Embedding 客户端：
# OpenAIEmbeddings 本来是给 OpenAI 用的，但只要改 base_url/key/model，
# 就能直接接任何"OpenAI 兼容"的服务（这里是阿里云百炼）
embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,      # 模型名：qwen3.7-text-embedding-flash
    api_key=settings.embedding_api_key,  # 百炼 API Key
    base_url=settings.embedding_base_url,  # https://dashscope.aliyuncs.com/compatible-mode/v1
    check_embedding_ctx_length=False,   # 关键修复：
)

def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    批量向量化（入库时用）：输入一堆文本，输出一堆向量。
    注意：百炼接口一次最多收 20 条文本，所以我们自己分批发。
    """
    if not texts:
        return []

    all_vectors = []          # 所有批次的结果先攒这里
    batch_size = 20           # 百炼限制：每批最多 20 条

    # range(0, 总数, 20) 生成切片起点：0, 20, 40, 60...
    for i in range(0, len(texts), batch_size):
        # texts[i : i+20] 切出当前这一批（最后一批可能不足20条，没关系）
        batch = texts[i:i + batch_size]
        # 一批一批发给百炼
        vectors = embeddings.embed_documents(batch)

        # 每批都做维度校验
        for vector in vectors:
            if len(vector) != settings.embedding_dimension:
                raise ValueError("Embedding 输出维度与数据库配置不一致")

        # extend：把这一批的结果追加到大列表后面
        all_vectors.extend(vectors)

    return all_vectors




def embed_query(text: str) -> list[float]:
    """
    单条向量化（用户提问时用）：输入一句问题，输出一个向量。
    这个向量拿去数据库里找"余弦距离最近"的块。
    """
    vector = embeddings.embed_query(text)
    if len(vector) != settings.embedding_dimension:
        raise ValueError("Query Embedding 输出维度与数据库配置不一致")
    return vector
