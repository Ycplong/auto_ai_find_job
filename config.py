from openai import OpenAI

from dotenv import load_dotenv
import os
import logging
from logging.handlers import TimedRotatingFileHandler
load_dotenv()
# 初始化 DeepSeek 客户端
# DeepSeek 的 API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")  # 假设这是 DeepSeek 的 API 地址


client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_URL)




class Logger:
    """
    日志工具类（单例模式）
    功能：
    1. 自动创建日志目录
    2. 支持控制台和文件输出
    3. 日志文件按时间轮转
    4. 全局唯一实例
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name="app", log_dir="logs", log_file="app.log",
                 level=logging.INFO, when="midnight", backup_count=7):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(level)

            # 防止重复添加handler
            if not self.logger.handlers:
                os.makedirs(log_dir, exist_ok=True)

                # 日志格式
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )

                # 控制台输出
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)

                # 文件输出（按天轮转）
                file_handler = TimedRotatingFileHandler(
                    filename=os.path.join(log_dir, log_file),
                    when=when,
                    backupCount=backup_count,
                    encoding="utf-8"
                )
                file_handler.setFormatter(formatter)

                self.logger.addHandler(console_handler)
                self.logger.addHandler(file_handler)

            self._initialized = True

    def get_logger(self):
        """获取配置好的logger对象"""
        return self.logger


# 项目全局logger实例（推荐直接使用这个实例）
logger = Logger().get_logger()