import os
import time
import logging
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import tkinter as tk
from tkinter import filedialog, messagebox

from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import client
from langchain_functions import generate_cover_letter, JobApplicationHelper
# from config import logger

# 初始化配置
class AppConfig:
    def __init__(self):
        self.city = "深圳"
        self.platform = "boss"
        self.google_path = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Bin\chrome.exe"
        self.urls = {
            "boss": "https://www.zhipin.com/web/geek/job-recommend?ka=header-job-recommend",
            "zl": "https://www.zhaopin.com/"
        }
        self.chrome_driver_path = "chromedriver.exe"
        self.browser_type = "chrome"
        self.default_job = "Python后端"


# 核心功能类
class CoreFunctions:
    @staticmethod
    def read_resumes():
        resume_text = ""
        resume_folder = "./resume"

        if not os.path.exists(resume_folder):
            return None, "简历文件夹不存在！"

        pdf_files = [f for f in os.listdir(resume_folder) if f.endswith(".pdf")]
        if not pdf_files:
            return None, "简历文件不存在！"

        for filename in pdf_files:
            file_path = os.path.join(resume_folder, filename)
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    resume_text += page.extract_text() or ""

        return resume_text, "简历符合要求！"

    @staticmethod
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
            logging.info(f"deepseek返回消息:{response.choices[0].message.content}")
            return response.choices[0].message.content
        else:
            raise Exception(f"DeepSeek API Error: {response.status_code}, {response.text}")


# GUI主界面
class JobHunterApp:
    def __init__(self, root):
        self.root = root
        self.config = AppConfig()
        self.helper = JobApplicationHelper()
        self.setup_logging()
        self.setup_ui()

    def setup_logging(self):
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "sc.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_ui(self):
        self.root.title("DEEPSEEK自动求职工具")
        self.root.geometry("500x450")

        # 主容器
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建各个UI模块
        self.create_platform_selection()
        self.create_job_input()
        self.create_city_input()
        self.create_chrome_path()
        self.create_api_mode()
        self.create_action_buttons()
        self.create_status_bar()

        # 扩展面板
        self.extension_panel = ExtensionPanel(self.main_frame)

    def create_platform_selection(self):
        frame = tk.LabelFrame(self.main_frame, text="平台选择", padx=5, pady=5)
        frame.pack(fill=tk.X, pady=5)

        self.platform_var = tk.StringVar(value=self.config.platform)

        for text, value in [("BOSS直聘", "boss"), ("智联招聘", "zl")]:
            tk.Radiobutton(
                frame, text=text, variable=self.platform_var,
                value=value
            ).pack(side=tk.LEFT, padx=5)

    def create_job_input(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(frame, text="职位:", width=8).pack(side=tk.LEFT)
        self.job_entry = tk.Entry(frame)
        self.job_entry.insert(0, self.config.default_job)
        self.job_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_city_input(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(frame, text="城市:", width=8).pack(side=tk.LEFT)
        self.city_entry = tk.Entry(frame)
        self.city_entry.insert(0, self.config.city)
        self.city_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_chrome_path(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=5)

        tk.Button(
            frame, text="Chrome路径", command=self.select_chrome_path, width=8
        ).pack(side=tk.LEFT)

        self.chrome_path_label = tk.Label(frame, text=self.config.google_path, anchor="w")
        self.chrome_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_api_mode(self):
        frame = tk.LabelFrame(self.main_frame, text="API模式", padx=5, pady=5)
        frame.pack(fill=tk.X, pady=5)

        self.api_mode_var = tk.BooleanVar(value=self.helper.use_local)

        for text, value in [("本地API", True), ("远程API", False)]:
            tk.Radiobutton(
                frame, text=text, variable=self.api_mode_var,
                value=value, command=self.toggle_api_mode
            ).pack(side=tk.LEFT, padx=5)

    def create_action_buttons(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=10)

        tk.Button(
            frame, text="占位", command=self.check_resume, width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            frame, text="开始任务", command=self.start_task, width=15
        ).pack(side=tk.LEFT, padx=5)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")

        tk.Label(
            self.main_frame, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W
        ).pack(fill=tk.X, pady=(5, 0))

    def select_chrome_path(self):
        path = filedialog.askopenfilename(
            title="选择 Chrome 可执行文件",
            filetypes=[("Chrome", "chrome.exe")]
        )
        if path:
            self.config.google_path = path
            self.chrome_path_label.config(text=path)

    def toggle_api_mode(self):
        self.helper.use_local = self.api_mode_var.get()
        mode = '本地' if self.helper.use_local else '远程'
        self.logger.info(f"已切换到{mode}API模式")
        self.status_var.set(f"当前模式: {mode}API")
        messagebox.showinfo("模式切换", f"已切换到{mode}模式", parent=self.root)

    def check_resume(self):
        _, message = CoreFunctions.read_resumes()
        messagebox.showinfo("检查简历", message)
        self.status_var.set(message)

    def check_pdf(self):
        """
        检查resume文件夹中是否存在PDF文件
        返回:
            - True: 如果存在至少一个PDF文件
            - False: 如果文件夹不存在或没有PDF文件
        """
        resume_folder = "./resume"

        # 检查文件夹是否存在
        if not os.path.exists(resume_folder):
            return False

        try:
            # 列出目录下所有文件
            files = os.listdir(resume_folder)

            # 检查是否有PDF文件
            for file in files:
                if file.lower().endswith('.pdf'):
                    return True

            # 没有找到PDF文件
            return False

        except Exception as e:
            # 处理可能的权限错误等异常情况
            print(f"检查PDF时出错: {e}")
            return False


    def start_task(self):
        job = self.job_entry.get()
        city = self.city_entry.get()
        platform = self.platform_var.get()
        flag = self.check_pdf()
        message = "简历不存在或不唯一"
        if flag is False:
            self.status_var.set(message)
            return

        self.logger.info(f"开始任务 - 职位:{job} 城市:{city} 平台:{platform}")
        self.status_var.set(f"正在处理{job}职位...")

        try:
            self.execute_job_search(job, city, platform)
            self.status_var.set(f"{job}职位处理完成")
        except Exception as e:
            self.handle_task_error(e)

    def execute_job_search(self, job, city, platform):
        url = self.config.urls[platform]

        if platform == "boss":
            self.run_boss_job_search(url, job, city)
        elif platform == "zl":
            self.run_zl_job_search(url, job, city)

    def run_boss_job_search(self, url, job, city):
        import finding_jobs
        finding_jobs.open_browser_with_options(
            url, self.config.browser_type,
            self.config.google_path, self.config.chrome_driver_path
        )
        finding_jobs.log_in("boss")

        job_index = 1
        index_c = 1

        while True:
            try:
                driver = finding_jobs.get_driver()
                finding_jobs.select_dropdown_option(driver, job)

                job_description = finding_jobs.get_job_description_by_index(job_index)
                if job_description:
                    self.process_boss_job(driver, job_description)

                time.sleep(3)
                index_c += 1
                self.logger.info(f"已沟通简历{index_c}份")
            except Exception as e:
                self.logger.info(f"An error occurred: {e}")
                break

    def process_boss_job(self, driver, job_description):
        element = driver.find_element(By.CSS_SELECTOR, '.op-btn.op-btn-chat').text
        self.logger.info(element)
        time.sleep(15)

        if element == '立即沟通':
            response = generate_cover_letter(job_description)
            self.logger.info(f"返回的求职信息{response}")
            time.sleep(1)

            contact_button = driver.find_element(
                By.XPATH, "//*[@id='wrap']/div[2]/div[2]/div/div/div[2]/div/div[1]/div[2]/a[2]"
            )
            contact_button.click()
            self.logger.info(f'点击沟通成功 职位需求为：{job_description}')

            self.handle_boss_chat(driver, response)

    def handle_boss_chat(self, driver, response):
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[8]/div[2]/div[3]/a[2]"))
            )
            self.logger.info("已经发送默认消息/匹配到继续沟通按钮")

            wechat_button = driver.find_element(By.XPATH, "/html/body/div[8]/div[2]/div[3]/a[2]")
            wechat_button.click()
            self.logger.info('点击继续沟通success')

            chat_box = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='chat-input']"))
            )
            self.send_chat_response(driver, response)
        except (TimeoutException, NoSuchElementException) as e:
            self.logger.info(f"聊天处理异常: {e}")

    def send_chat_response(self, driver, response):
        chat_box = driver.find_element(By.XPATH, "//*[@id='chat-input']")
        chat_box.clear()
        chat_box.send_keys(response)
        time.sleep(3)
        chat_box.send_keys(Keys.ENTER)
        time.sleep(10)
        driver.back()
        time.sleep(3)

    def run_zl_job_search(self, url, job, city):
        import finding_jobs_zl
        finding_jobs_zl.open_browser_with_options(
            url, self.config.browser_type,
            self.config.google_path, self.config.chrome_driver_path
        )
        finding_jobs_zl.log_in("zl")

        try:
            driver = finding_jobs_zl.get_driver()
            finding_jobs_zl.select_dropdown_option(driver, job, city)
            finding_jobs_zl.one_click_delivery()
        except Exception as e:
            self.logger.info(f"An error occurred: {e}")

    def handle_task_error(self, error):
        self.logger.error(f"任务执行出错: {str(error)}")
        self.status_var.set(f"错误: {str(error)}")
        messagebox.showerror("错误", str(error))


# 扩展面板类
class ExtensionPanel:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.X, pady=10)
        self.buttons = []

    def add_button(self, text, command):
        btn = tk.Button(self.frame, text=text, command=command)
        btn.pack(side=tk.LEFT, padx=5)
        self.buttons.append(btn)
        return btn


# 主程序入口
if __name__ == '__main__':
    # 初始化应用
    load_dotenv()

    root = tk.Tk()
    app = JobHunterApp(root)

    # 这里可以添加扩展按钮示例
    # app.extension_panel.add_button("测试功能", lambda: print("测试"))

    root.mainloop()