from openai import OpenAI, OpenAIError
from selenium.common import TimeoutException, NoSuchElementException
from sentence_transformers import SentenceTransformer
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import os
import time
import logging
from dotenv import load_dotenv


from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter






# Check OpenAI version compatibility
from packaging import version

from config import client  # 从配置文件导入 client
from langchain_functions import generate_letter, should_use_local_langchain, chat_local, should_use_langchain

# 加载环境变量
load_dotenv()
# 创建日志目录（如果不存在）
log_dir = os.path.join(os.getcwd(), "logs")  # 日志保存目录
os.makedirs(log_dir, exist_ok=True)  # 如果目录不存在则创建
# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日志格式
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "sc.log")),  # 保存到文件
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 创建 logger 实例
logger = logging.getLogger(__name__)



# 调用 DeepSeek API 关闭stream
def call_deepseek_api(prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Hello"},
        ],
        stream=False
    )
    if response.status_code == 200:
        logger.info(f"deepseek返回消息:{response.choices[0].message.content}")
        return response.choices[0].message.content
    else:
        raise Exception(f"DeepSeek API Error: {response.status_code}, {response.text}")

def send_response_to_chat_box(driver, response):
    # 定位聊天输入框
    chat_box = driver.find_element(By.XPATH, "//*[@id='chat-input']")

    # 清除输入框中可能存在的任何文本
    chat_box.clear()

    # 将响应粘贴到输入框
    chat_box.send_keys(response)
    time.sleep(3)

    # 模拟按下回车键来发送消息
    chat_box.send_keys(Keys.ENTER)
    time.sleep(1)

def send_response_and_go_back(driver, response):
    # 调用函数发送响应
    send_response_to_chat_box(driver, response)

    time.sleep(10)
    # 返回到上一个页面
    driver.back()
    time.sleep(3)

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

def create_thread(client):
    """
       创建一个新的线程并返回其 ID。

       参数:
           client (OpenAI): 初始化的 OpenAI 客户端对象。

       返回:
           str: 新创建的线程 ID。如果创建失败，返回 None。
       """

    try:
        response = client.beta.threads.create()  # No assistant_id needed
        thread_id = response.id
        return thread_id
    except OpenAIError as e:
        # 捕获 OpenAI 相关异常
        logger.error(f"创建线程时发生错误: {e}")
        return None
    except Exception as e:
        # 捕获其他异常
        logger.error(f"发生未知错误: {e}")
        return None

def chat(user_input, assistant_id=None, thread_id=None):
    if thread_id is None:
        # thread_id = create_thread(client)
        # if thread_id is None:
        #     return json.dumps({"error": "Failed to create a new thread"})
        pass

    logger.info(f"boss职位标准message: {user_input} ")


    return call_deepseek_api(user_input)
    # Run the Assistant
    # try:
    #     # Add the user's message to the thread
    #     client.beta.threads.messages.create(
    #         thread_id=thread_id,
    #         role="user",
    #         content=user_input
    #     )
    #
    #     # Start the Assistant Run
    #     run = client.beta.threads.runs.create(
    #         thread_id=thread_id,
    #         assistant_id=assistant_id
    #     )
    #
    #     # Check if the Run requires action (function call)
    #     while True:
    #         run_status = client.beta.threads.runs.retrieve(
    #             thread_id=thread_id,
    #             run_id=run.id,
    #             timeout=60  # 设置超时时间为60秒
    #         )
    #
    #         if run_status.status == 'completed':
    #             break
    #         elif run_status.status == 'requires_action':
    #             # Here you can handle specific actions if your assistant requires them
    #             # ...
    #             time.sleep(1)  # Wait for a second before checking again
    #
    #     # Retrieve and return the latest message from the assistant
    #     messages = client.beta.threads.messages.list(thread_id=thread_id)
    #     assistant_message = messages.data[0].content[0].text.value
    #     logger.info(f'deepseek返回的职业推荐消息: {assistant_message}')
    #
    #     time.sleep(2000)
    #     # 将换行符替换为一个空格
    #     formatted_message = assistant_message.replace("\n", " ").replace(" ", "").replace("真诚的，龙思卓", "")
    #     import re
    #     formatted_message = re.sub(r'【.*?】', '', formatted_message)
    #
    #
    #     # response_data = json.dumps({"response": assistant_message, "thread_id": thread_id})
    #     return formatted_message
    #
    # except Exception as e:
    #     logger.info(f"An error occurred: {e}")
    #     error_response = json.dumps({"error": str(e)})
    #

def send_job_descriptions_to_chat(url, browser_type, label, assistant_id=None, vectorstore=None,platform='boss',city=None):

    # 开始浏览并获取工作描述
    if platform == 'boss':
        import finding_jobs
        finding_jobs.open_browser_with_options(url, browser_type)
        finding_jobs.log_in()
        job_index = 1  # 开始的索引
        index_c = 1
        while True:
            try:
                # 获取 driver 实例
                driver = finding_jobs.get_driver()
                # 更改下拉列表选项
                finding_jobs.select_dropdown_option(driver, label)
                # 调用 finding_jobs.py 中的函数来获取描述
                job_description = finding_jobs.get_job_description_by_index(job_index)
                if job_description:
                    #立即沟通
                    element = driver.find_element(By.CSS_SELECTOR, '.op-btn.op-btn-chat').text
                    logger.info(element)

                    time.sleep(15)
                    if element == '立即沟通':
                        # 发送描述到聊天并打印响应
                        if should_use_langchain():
                            response = '你好'
                        if not should_use_local_langchain():
                            response = generate_letter(vectorstore, job_description)
                        else:
                            response = chat_local(vectorstore, job_description)
                        logger.info(f"返回的求职信息{response}")
                        time.sleep(1)
                        # 点击沟通按钮

                        contact_button = driver.find_element(By.XPATH,
                                                             "//*[@id='wrap']/div[2]/div[2]/div/div/div[2]/div/div[1]/div[2]/a[2]")

                        contact_button.click()
                        logger.info(f'点击沟通成功 职位需求为：{job_description}')
                        # 聊过得消息跳过 XPath
                        xpath_locator_wechat_history = "/html/body/div[8]/div[2]/div[3]/a[2]"
                        xpath_locator_wechat_continue = "/html/body/div[8]/div[2]/div[3]/a[1]"
                        try:
                            # 等待继续沟通出现，最多等待 10 秒
                            WebDriverWait(driver, 15).until(
                                EC.presence_of_element_located((By.XPATH, xpath_locator_wechat_history))
                            )
                            logger.info("已经发送默认消息/匹配到继续沟通按钮")



                            wechat_button = driver.find_element(By.XPATH, xpath_locator_wechat_history)
                            wechat_button.click()
                            logger.info('点击继续沟通success')

                        except TimeoutException:
                            logger.info("超时未找到")
                        except NoSuchElementException:
                            logger.info("异常错误")

                        # 等待回复框出现
                        xpath_locator_chat_box = "//*[@id='chat-input']"
                        chat_box = WebDriverWait(driver, 50).until(
                            EC.presence_of_element_located((By.XPATH, xpath_locator_chat_box))
                        )
                    #     # 调用函数发送响应
                        send_response_and_go_back(driver, response)
                    else:
                        #直接投递
                        pass

                # 等待一定时间后处理下一个工作描述
                time.sleep(3)
                # job_index += 1
                index_c+=1
                logger.info(f"已沟通简历{index_c}份")
            except Exception as e:
                logger.info(f"An error occurred: {e}")
                break
    elif platform == 'zl':
        import finding_jobs_zl
        finding_jobs_zl.open_browser_with_options(url, browser_type)
        finding_jobs_zl.log_in()
        try:
            # 获取 driver 实例
            driver = finding_jobs_zl.get_driver()
            # 更改下拉列表选项
            finding_jobs_zl.select_dropdown_option(driver,label,city)
            # 调用 finding_jobs.py 中的函数来投递
            finding_jobs_zl.one_click_delivery()
        except Exception as e:
            logger.info(f"An error occurred: {e}")
            pass
    elif platform == 'wy':
        pass
    else:
        pass






if __name__ == '__main__':
    # 读取简历
    resume_text = read_resumes()
    logger.info("Resume text loaded successfully.")

    # # 获取文本块
    # chunks = get_text_chunks(resume_text)
    # logger.info("Text chunks created successfully.")

    # # 获取向量存储
    # vectorstore = get_vectorstore(chunks)
    # logger.info("Vectorstore created successfully.")
    platform = 'zl'

    url = "https://www.zhipin.com/web/geek/job-recommend?ka=header-job-recommend"
    browser_type = "chrome"
    label = "Python（深圳）"  # 想要选择的下拉菜单项
    send_job_descriptions_to_chat(url, browser_type, label, vectorstore=resume_text,platform=platform)