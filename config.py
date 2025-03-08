from openai import OpenAI
import os
# 初始化 DeepSeek 客户端
# DeepSeek 的 API 配置

from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")  # 假设这是 DeepSeek 的 API 地址

print(DEEPSEEK_API_KEY)
print(DEEPSEEK_API_URL)
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_URL)


