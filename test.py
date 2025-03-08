# # from selenium import webdriver
# # from selenium.webdriver.chrome.options import Options
# #
# # def open_browser_with_options(url, browser):
# #     options = Options()
# #     options.add_experimental_option("detach", True)
# #
# #     if browser == "chrome":
# #         driver = webdriver.Chrome(options=options)
# #         driver.maximize_window()
# #     else:
# #         raise ValueError("Browser type not supported")
# #
# #     driver.get(url)
# #
# # # Variables
# # url = "https://www.zhipin.com/web/geek/job-recommend?ka=header-job-recommend"
# # browser_type = "chrome"
# #
# # # Test case
# # open_browser_with_options(url, browser_type)
# #
# #
# # import os
# # from PyPDF2 import PdfReader
# # from langchain.text_splitter import CharacterTextSplitter
# # from langchain_community.embeddings import OpenAIEmbeddings
# # from langchain_community.vectorstores.faiss import FAISS
# #
# #
# # def read_resumes():
# #     resume_text = ""
# #     resume_folder = "./resume"
# #
# #     # 遍历 resume 文件夹中的所有 PDF 文件
# #     for filename in os.listdir(resume_folder):
# #         if filename.endswith(".pdf"):
# #             file_path = os.path.join(resume_folder, filename)
# #             # 打开 PDF 文件
# #             reader = PdfReader(file_path)
# #             # 提取每一页的文本
# #             for page in reader.pages:
# #                 resume_text += page.extract_text()
# #
# #     return resume_text
# #
# # def get_text_chunks(text):
# #     text_splitter = CharacterTextSplitter(
# #         separator="\n",
# #         chunk_size=2000,
# #         chunk_overlap=200,
# #         length_function=len
# #     )
# #     chunks = text_splitter.split_text(text)
# #     return chunks
# #
# # # 向量化，并且返回向量存储库
# # def get_vectorstore(text_chunks):
# #     embeddings = OpenAIEmbeddings()
# #     # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
# #     vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
# #     return vectorstore
# #
# # qz_text = get_text_chunks(read_resumes())
# # print(get_vectorstore(qz_text))
# import os
#
# import requests
# # sk-c87309f071ff4db5bf406e77c2f3950b
# #setx DEEPSEEK_API_KEY "sk-c87309f071ff4db5bf406e77c2f3950b"
# #
# # import faiss
# #
# # # 创建一个简单的索引
# # dimension = 64  # 向量维度
# # index = faiss.IndexFlatL2(dimension)  # 使用 L2 距离
# #
# # # 添加一些随机向量
# # import numpy as np
# # vectors = np.random.random((100, dimension)).astype('float32')
# # index.add(vectors)
# #
# # # 搜索最近的向量
# # query_vector = np.random.random((1, dimension)).astype('float32')
# # distances, indices = index.search(query_vector, 5)
# #
# # print("Distances:", distances)
# from dotenv import load_dotenv
# from langchain.text_splitter import CharacterTextSplitter
# from langchain_community.vectorstores.faiss import FAISS
# from sentence_transformers import SentenceTransformer
#
# import logging
# logger = logging.getLogger(__name__)
#
# def read_resumes():
#     resume_text = ""
#     resume_folder = "./resume"
#
#     # 遍历 resume 文件夹中的所有 PDF 文件
#     for filename in os.listdir(resume_folder):
#         if filename.endswith(".pdf"):
#             file_path = os.path.join(resume_folder, filename)
#             # 打开 PDF 文件
#             with open(file_path, "rb") as f:
#                 from PyPDF2 import PdfReader
#                 reader = PdfReader(f)
#                 # 提取每一页的文本
#                 for page in reader.pages:
#                     resume_text += page.extract_text()
#
#     return resume_text
# # 获取文本块
# def get_text_chunks(text):
#     text_splitter = CharacterTextSplitter(
#         separator="\n",
#         chunk_size=1000,
#         chunk_overlap=200,
#         length_function=len
#     )
#     chunks = text_splitter.split_text(text)
#     return chunks
# # 获取向量存储
# def get_vectorstore(text_chunks):
#     # 使用 Sentence Transformers 获取嵌入向量
#     model = SentenceTransformer('all-MiniLM-L6-v2')
#     embeddings = model.encode(text_chunks)  # 直接对整个文本块列表编码
#
#     # 将文本块和嵌入向量组合成 text_embeddings
#     text_embeddings = list(zip(text_chunks, embeddings))
#
#     # 创建 FAISS 向量存储
#     vectorstore = FAISS.from_embeddings(
#         text_embeddings=text_embeddings,
#         embedding=model  # 传递嵌入模型
#     )
#     return vectorstore
#
# # 读取简历
# resume_text = read_resumes()
# logger.info("Resume text loaded successfully.")
# print(resume_text)
# # 获取文本块
# # chunks = get_text_chunks(resume_text)
# # logger.info("Text chunks created successfully.")
# #
# # # 获取向量存储
# # vectorstore = get_vectorstore(chunks)
# # logger.info("Vectorstore created successfully.")
#
# # print(vectorstore)
import os

import requests



# from main_find import read_resumes


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
# def generate_letter(job_description, resume_text):
#     """
#     根据工作描述和简历内容生成求职信。
#
#     参数:
#         job_description (str): 工作描述。
#         resume_text (str): 简历内容。
#
#     返回:
#         str: 生成的求职信。
#     """
#     # 字数限制
#     character_limit = 20
#
#     # 提示词模板
#     prompt = f"""
#         你将扮演一位求职者的角色，根据简历内容以及应聘工作的描述，直接给 HR 写一封礼貌专业的求职消息。
#         要求：
#         1. 字数严格限制在 {character_limit} 以内。
#         2. 使用专业的语言结合简历中的经历和技能，并结合应聘工作的描述，阐述自己的优势。
#         3. 开头称呼招聘负责人。
#         4. 这是一份求职消息，不要包含求职内容以外的东西（例如“根据您上传的求职要求和个人简历，我来帮您起草一封求职邮件：”）。
#
#         工作描述：
#         {job_description}
#     """
#
#     try:
#         # 调用 DeepSeek API
#         response = client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {"role": "system", "content": f"你是一位专业的求职助手，能够根据简历和工作描述生成高质量的求职信。以下是简历内容：\n{resume_text}"},
#                 {"role": "user", "content": prompt},
#             ],
#             stream=False
#         )
#
#         # 提取生成的求职信
#         letter = response.choices[0].message.content
#
#         # 去掉所有换行符，防止分成多段消息
#         letter = letter.replace('\n', ' ')
#
#         return letter
#
#     except Exception as e:
#         print(f"生成求职信时发生错误: {e}")
#         return None
#
# from ollama import Client
#
#
# headers = {
#     "Content-Type": "application/json"
# }
#
# client = Client(
#   host='http://127.0.0.1:11434',
#   headers=headers
# )
# # 添加钩子
#
# response = client.generate(
#     model = "deepseek-r1:1.5b",
#     prompt= "为什么草是绿的？",
#     stream=False,
# )
# print(response)

# import requests
#

#
# data = {
#     "model": "deepseek-r1:1.5b",
#     "prompt": "为什么草是绿的？",
#     "stream": False
# }
#
# response = requests.post(
#     "http://127.0.0.1:11434/api/generate",
#     json=data,
#     headers=headers,
#     verify=False
# )
#
# print(response.json())






#
# import requests
#
# url = "http://127.0.0.1:11434/api/chat"
# headers = {
#     "Content-Type": "application/json"
# }
# data = {
#     "model": "deepseek-r1:1.5b",
#     "prompt": "为什么草是绿的？",
#     "stream": False
# }
#
# response = requests.post(url, headers=headers, json=data)
# print(response.json()['response'])

# import logging
# import httpx
# client = httpx.Client(verify=False)  #
# # 启用 httpx 的调试日志
# logging.basicConfig(level=logging.DEBUG)
#
#
# response = client.post(
#     "http://127.0.0.1:11434/api/generate",
#     json={"model": "deepseek-r1:1.5b", "prompt": "为什么草是绿的？", "stream": False},
#     headers={"Content-Type": "application/json"},
# )
# print(response)



def chat(job_description, resume_text):
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
        return None


job_description = """职位描述
岗位内容:
1. 设计和开发符合业务需求的爬虫系统，实现数据采集、处理和分析。
2. 优化爬虫程序，提升数据采集效率和准确性，保证数据的完整性和正确性。
3. 参与和配合团队进行数据分析和挖掘相关工作，为业务决策提供支持。
4. 关注技术前沿及发展趋势，不断优化爬虫系统并推进爬虫技术的发展。

任职要求:
1. 具备较强的编程能力，熟练掌握 Python 或其他主流编程语言。
2. 具备一定的计算机基础，熟悉网络协议和 Web 技术，能够解决常见问题。
3. 具备良好的团队合作和沟通能力，能够与团队成员紧密配合完成任务。
4. 有自我学习和探索的能力，关注行业动态和技术趋势，不断提升个人技能水平。"""
resume_text = read_resumes()
res = chat(job_description,resume_text)
print(res)