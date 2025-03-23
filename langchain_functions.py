import json
import os
from selenium.webdriver.support import expected_conditions as EC

import requests
from dotenv import load_dotenv
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from sentence_transformers import SentenceTransformer


from langchain.text_splitter import CharacterTextSplitter
from config import client  # 从配置文件导入 client
from langchain.vectorstores import FAISS

load_dotenv()


# 读取简历数据
def read_resumes():
    resume_text = ""
    resume_folder = "./resume"

    # 遍历 resume 文件夹中的所有 PDF 文件
    for filename in os.listdir(resume_folder):
        if filename.endswith(".pdf"):
            file_path = os.path.join(resume_folder, filename)
            # 打开 PDF 文件
            with open(file_path, "rb") as f:
                from PyPDF2 import PdfReader
                reader = PdfReader(f)
                # 提取每一页的文本
                for page in reader.pages:
                    resume_text += page.extract_text()

    return resume_text


# 获取文本块
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# 获取向量存储
def get_vectorstore(text_chunks):
    # 使用 Sentence Transformers 获取嵌入向量
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(text_chunks)  # 直接对整个文本块列表编码

    # 将文本块和嵌入向量组合成 text_embeddings
    text_embeddings = list(zip(text_chunks, embeddings))

    # 创建 FAISS 向量存储
    vectorstore = FAISS.from_embeddings(
        text_embeddings=text_embeddings,
        embedding=model  # 传递嵌入模型
    )
    return vectorstore


def should_use_local_langchain():
    return True

def should_use_langchain():
    return False

def generate_letter(resume_text,job_description):
    """
    根据工作描述和简历内容生成求职信。

    参数:
        job_description (str): 工作描述。
        resume_text (str): 简历内容。

    返回:
        str: 生成的求职信。
    """
    # 字数限制
    character_limit = 20

    # 提示词模板
    prompt = f"""
        你将扮演一位求职者的角色，根据简历内容以及应聘工作的描述，直接给 HR 写一封礼貌专业的求职消息。
        要求：
        1. 字数严格限制在 {character_limit} 以内。
        2. 使用专业的语言结合简历中的经历和技能，并结合应聘工作的描述，阐述自己的优势。
        3. 开头称呼招聘负责人，结尾附上求职者联系方式。
        4. 这是一份求职消息，不要包含求职内容以外的东西（例如“根据您上传的求职要求和个人简历，我来帮您起草一封求职邮件：”）。

        工作描述：
        {job_description}
    """

    try:
        # 调用 DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"你是一位专业的求职助手，能够根据简历和工作描述生成高质量的求职信。以下是简历内容：\n{resume_text}"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        # 提取生成的求职信
        letter = response.choices[0].message.content

        # 去掉所有换行符，防止分成多段消息
        letter = letter.replace('\n', ' ')

        return letter

    except Exception as e:
        print(f"生成求职信时发生错误: {e}")
        return "你好"


def chat_local(resume_text,job_description):
    """
        根据工作描述和简历内容生成求职信。

        参数:
            job_description (str): 工作描述。
            resume_text (str): 简历内容。

        返回:
            str: 生成的求职信。
        """
    # 字数限制
    character_limit = 100

    # 提示词模板
    prompt = f"""
            你将扮演一位求职者的角色，根据简历内容以及应聘工作的描述，直接给 HR 写一封礼貌专业的求职消息。
            要求：
            1. 字数严格限制在 {character_limit} 以内。
            2. 使用专业的语言结合简历中的经历和技能，并结合应聘工作的描述，阐述自己的优势。
            3. 开头称呼招聘负责人。
            4. 这是一份求职消息，不要包含求职内容以外的东西（例如“根据您上传的求职要求和个人简历，我来帮您起草一封求职邮件：”）。

            工作描述：
            {job_description}
        """

    try:
        url = "http://127.0.0.1:11434/api/chat"
        headers = {
            "Content-Type": "application/json"}

        data = {
            "model":"deepseek-r1:1.5b",
            "messages":[
                {"role": "system", "content": f"你是一位专业的求职助手，能够根据简历和工作描述生成高质量的求职信。以下是简历内容：\n{resume_text}"},
                {"role": "user", "content": prompt}],
        "stream": False }
        # 调用 DeepSeek API
        response = requests.post(url, headers=headers, json=data)

        response_json = response.json()
        # 提取生成的求职信内容
        content = response_json.get("message", {}).get("content", "")
        # print(content)
        # 去掉多余的思考部分（<think>...</think>）
        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()
        # 去掉多余的换行符和空格
        content = " ".join(content.split())
        return content
    except Exception as e:
        print(f"生成求职信时发生错误: {e}")
        return "你好"

def get_cookie_filename(driver,platform):
    """根据platform生成的 Cookie 文件名"""
    return f"{platform}_cookies.json"

def save_cookies(driver,platform):
    """保存 Cookies 到文件"""
    file_path = get_cookie_filename(driver,platform)
    cookies = driver.get_cookies()
    with open(file_path, "w") as file:
        json.dump(cookies, file)
    print(f"Cookies 已保存到 {file_path}")

def load_cookies(driver,platform):
    """从文件加载 Cookies"""
    file_path = get_cookie_filename(driver,platform)
    if not os.path.exists(file_path):
        print("没有找到 Cookies 文件，需重新登录")
        return False
    try:
        with open(file_path, "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print(f"Cookies 已加载自 {file_path}")
        return True
    except Exception as e:
        print(f"加载 Cookies 失败: {e}")
        return False

def is_logged_in(driver, platform):
    """检查是否已登录"""
    # 根据不同平台设置登录检查的 XPath
    login_check_xpaths = {
        "boss": "//*[@id='header']/div[1]/div[4]/div/a",  # BOSS 平台
        "zl": "//*[@id='right_nav_header']/div/div[2]/a[2]"  # 智联招聘平台
    }

    if platform not in login_check_xpaths:
        print(f"未知平台: {platform}")
        return False
    login_check_xpath = login_check_xpaths[platform]
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,login_check_xpath))
        )
        print(f"{platform}：检测到未登录，需要扫码")
        return False  # 发现登录按钮，说明未登录
    except TimeoutException:
        print(f"{platform}：未发现登录按钮，已登录")
        return True  # 未发现登录按钮，说明已登录

