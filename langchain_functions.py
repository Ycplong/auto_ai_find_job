from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import os
from config import client  # 从配置文件导入 client
import requests

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


