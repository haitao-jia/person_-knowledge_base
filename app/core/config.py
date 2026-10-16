"""
文件名：app/core/config.py
作用：全局配置管家。启动时自动读取 .env 文件，把每一项配置装进
      settings 对象。项目里任何地方要用配置，都从 settings 拿，
      不重复读文件。
对应规范：SPEC.md §5 配置规范（5.1 配置项定义、5.2 .env.example、
          5.3 配置加载）
说明：聊天模型与 Embedding 模型分属两家 OpenAI 兼容服务商
      （聊天用 DeepSeek，Embedding 用阿里云百炼），因此配置拆为
      CHAT_* 与 EMBEDDING_* 两组，互不影响，便于更换供应商。
"""

# 导入两个东西（依赖已装好）：
#   BaseSettings      —— "会自动读 .env 的基类"，我们的类继承它才有这个能力
#   SettingsConfigDict —— 用来配置"怎么读"（读哪个文件、什么编码）
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    配置类：把 .env 里的每一项配置声明成一个字段。

    两个关键规则：
      1. 字段名必须和 .env 里的大写变量名一一对应（自动匹配，不区分大小写），
         写错名字就永远读不到值；
      2. 没有默认值的字段，.env 里必须能读到，否则启动直接报错（强制检查），
         有默认值的字段，.env 没写就用默认值。
    """

    # ================= 数据库 =================
    database_url: str  # 数据库连接串（.env 的 DATABASE_URL）
    upload_dir: str = "storage/uploads"  # 上传文件保存目录（UPLOAD_DIR），带默认值

    # ================= 聊天模型：DeepSeek（OpenAI 兼容） =================
    chat_base_url: str  # 聊天模型服务地址（CHAT_BASE_URL）
    chat_api_key: str  # 聊天模型密钥（CHAT_API_KEY），在 platform.deepseek.com 申请
    chat_model: str  # 聊天模型名称（CHAT_MODEL），如 deepseek-v4-flash

    # ================= Embedding 模型：阿里云百炼（OpenAI 兼容） =================
    embedding_base_url: str  # Embedding 服务地址（EMBEDDING_BASE_URL）
    embedding_api_key: str  # Embedding 密钥（EMBEDDING_API_KEY），在百炼控制台申请
    embedding_model: str  # Embedding 模型名（EMBEDDING_MODEL），如 qwen3.7-text-embedding-flash
    embedding_dimension: int = 1024  # 向量维度（EMBEDDING_DIMENSION），
    # 必须等于模型实际输出维度，否则建表/入库会失败（SPEC §5.1）

    # 告诉基类"怎么读"：从项目根目录的 .env 文件读取，文件编码 utf-8
    # extra="ignore"：.env 里出现这里没声明的其他变量，直接忽略、不报错
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 全局唯一配置实例：这行代码真正执行"读取 .env"这一步。
# 其他文件使用方式：from app.core.config import settings
settings = Settings()
