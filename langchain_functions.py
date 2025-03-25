import io
import json
import os
import sys

import numpy as np
import requests
from dotenv import load_dotenv

from PyPDF2 import PdfReader
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from selenium.webdriver.support import expected_conditions as EC
from config import client  # 从配置文件导入 client

load_dotenv()
# 修复Windows系统的编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class RGAnalyzer:
    """
    改进版RGA（Relevance Gap Analysis）分析器
    主要优化点：
    1. 智能Top-K选择算法
    2. 阈值过滤低质量匹配
    3. 结果加权排序
    """

    def __init__(self, embedding_model='all-MiniLM-L6-v2'):
        """初始化嵌入模型和文本分割器"""
        self.embedding_model = SentenceTransformer(embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", "。", " ", ""],
            chunk_size=1000,
            chunk_overlap=200
        )

    # ----------------------
    # 阶段1：数据准备
    # ----------------------
    def load_resumes(self, folder_path="./resume"):
        """处理中文PDF读取"""
        resume_text = ""
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                filepath = os.path.join(folder_path, filename)
                try:
                    with open(filepath, "rb") as f:
                        reader = PdfReader(f)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                resume_text += text + "\n"
                except Exception as e:
                    print(f"读取文件 {filename} 出错: {str(e)}")
        return self._clean_text(resume_text)

    def _clean_text(self, text):
        """文本清洗"""
        return ' '.join(text.split()).strip()

    def chunk_text(self, text):
        """将文本分块"""
        return self.text_splitter.split_text(text)

    # ----------------------
    # 阶段2：嵌入计算
    # ----------------------
    def encode_texts(self, texts):
        """将文本列表转化为嵌入向量"""
        return self.embedding_model.encode(texts)

    # ----------------------
    # 阶段3：核心分析（改进版）
    # ----------------------
    def calculate_similarity(self, resume_embeddings, job_embeddings):
        """改进的相似度计算（包含标准化）"""
        sim_matrix = cosine_similarity(resume_embeddings, job_embeddings)
        # 标准化到0-1范围
        sim_matrix = (sim_matrix - sim_matrix.min()) / (sim_matrix.max() - sim_matrix.min())
        return sim_matrix

    def smart_top_k(self, sim_matrix, threshold=0.5, max_k=3):
        """
        智能Top-K选择算法
        参数:
            threshold: 相似度阈值，默认0.5
            max_k: 每个要求最多匹配的简历块数
        """
        results = []
        for j in range(sim_matrix.shape[1]):
            # 获取超过阈值的所有片段索引
            qualified = np.where(sim_matrix[:, j] > threshold)[0]

            if len(qualified) == 0:
                # 如果没有达到阈值的，取最相关的一个
                top_idx = np.argmax(sim_matrix[:, j])
                results.append({
                    "requirement_idx": j,
                    "matched_indices": [int(top_idx)],
                    "similarities": [float(sim_matrix[top_idx, j])]
                })
            else:
                # 按相似度降序排列
                sorted_indices = qualified[np.argsort(-sim_matrix[qualified, j])]
                # 限制最大数量
                selected_indices = sorted_indices[:max_k]
                results.append({
                    "requirement_idx": j,
                    "matched_indices": [int(i) for i in selected_indices],
                    "similarities": [float(sim_matrix[i, j]) for i in selected_indices]
                })
        return results

    # ----------------------
    # 阶段4：结果生成（改进版）
    # ----------------------
    def generate_analysis_report(self, sim_matrix, resume_chunks, job_requirements):
        """生成带智能排序的分析报告"""
        top_k_results = self.smart_top_k(sim_matrix)

        requirement_results = []
        for result in top_k_results:
            j = result["requirement_idx"]
            requirement_results.append({
                "requirement": job_requirements[j],
                "matches": [
                    {
                        "chunk": resume_chunks[i],
                        "similarity": result["similarities"][idx]
                    }
                    for idx, i in enumerate(result["matched_indices"])
                ],
                "avg_similarity": np.mean(result["similarities"])
            })

        # 按平均相似度降序排列
        requirement_results.sort(key=lambda x: -x["avg_similarity"])

        # 加权计算整体匹配度
        max_similarities = np.max(sim_matrix, axis=0)
        gap_score = float(1 - np.average(max_similarities))

        return {
            "requirements_analysis": requirement_results,
            "gap_score": gap_score,
            "match_percentage": (1 - gap_score) * 100
        }

    def format_report(self, analysis_result, job_title):
        """生成可读性报告"""
        report = [
            f"=== {job_title} RGA分析报告 ===",
            f"整体匹配度: {analysis_result['match_percentage']:.1f}%",
            "\n【最相关岗位要求】"
        ]

        for req in analysis_result['requirements_analysis'][:5]:  # 只展示前5个最相关要求
            report.append(f"\n► {req['requirement']} (平均匹配度: {req['avg_similarity']:.0%})")
            for match in req["matches"]:
                excerpt = match['chunk'][:100] + '...' if len(match['chunk']) > 100 else match['chunk']
                report.append(f"  ✓ {excerpt} ({match['similarity']:.0%})")

        return '\n'.join(report)


class JobApplicationHelper:
    """改进版求职助手（解决编码问题）"""

    def __init__(self, use_local=True, local_url="http://127.0.0.1:11434/api/generate", model="deepseek-r1:1.5b"):
        self._use_local = use_local  # 改为私有变量
        self.local_url = local_url
        self.model = model

    @property
    def use_local(self):
        """获取当前模式"""
        return self._use_local

    @use_local.setter
    def use_local(self, value):
        """设置本地/远程模式"""
        if not isinstance(value, bool):
            raise ValueError("必须传入布尔值")
        self._use_local = value
        print(f"已切换至{'本地' if value else '远程'}模式")

    def generate_letter(self, prompt, temperature=0.7):
        try:
            if self.use_local:
                return self._generate_local(prompt, temperature)
            return self._generate_remote(prompt, temperature)
        except Exception as e:
            print(f"生成失败: {str(e)}")
            return "求职信生成失败，请稍后重试"

    def _generate_local(self, prompt, temperature):
        """专用适配版本（当API响应格式固定时）"""
        try:
            response = requests.post(
                self.local_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "options": {"temperature": temperature},
                    "stream": False
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            response.raise_for_status()
            return self._clean_response(response.json()["response"])  # 直接取response字段

        except KeyError:
            raise RuntimeError("API响应格式异常，缺少'response'字段")
        except requests.exceptions.Timeout:
            raise RuntimeError("请求超时，请检查API服务是否正常运行")
        except Exception as e:
            raise RuntimeError(f"生成失败: {str(e)}")

    def _generate_remote(self, prompt, temperature):
        response = client.chat.completions.create(
            model="deepseek-chat",
            prompt=prompt,
            temperature=temperature,
            stream=False
        )
        return self._clean_response(response.choices[0].message.content)

    def _clean_response(self, text):
        """处理特殊字符编码"""
        return text.encode('utf-8', errors='ignore').decode('utf-8')


def generate_prompt_from_rga(job_description, top_k=3):
    """改进版Prompt生成（处理特殊字符）"""
    rga = RGAnalyzer()
    try:
        resume_text = rga.load_resumes()
        if not resume_text:
            raise ValueError("简历内容为空，请检查PDF文件")

        resume_chunks = rga.chunk_text(resume_text)
        job_requirements = [req.strip() for req in job_description.split("\n") if req.strip()]

        if not job_requirements:
            raise ValueError("无效的岗位描述")

        resume_emb = rga.encode_texts(resume_chunks)
        job_emb = rga.encode_texts(job_requirements)
        sim_matrix = rga.calculate_similarity(resume_emb, job_emb)

        analysis_result = rga.generate_analysis_report(sim_matrix, resume_chunks, job_requirements)

        # 使用ASCII字符替代Unicode符号
        prompt = [
            "请根据以下匹配分析生成求职内容，要求：",
            "1. 专业简洁，不超过400字",
            "2. 突出显示最相关的3项能力",
            "3. 包含具体成就或经验",
            "4. 直接使用第一人称我"
            "\n[岗位要求]",
            job_description,
            "\n[简历匹配分析]"
        ]

        for req in analysis_result["requirements_analysis"][:top_k]:
            prompt.append(f"\n- 要求: {req['requirement']} (匹配度: {req['avg_similarity']:.0%})")
            for match in req["matches"]:
                excerpt = match["chunk"][:150] + "..." if len(match["chunk"]) > 150 else match["chunk"]
                prompt.append(f"  * 相关经历: {excerpt}")

        prompt.append("\n请生成具有专业性的话，直接输出内容不要额外说明。")
        return "\n".join(prompt)

    except Exception as e:
        print(f"生成Prompt出错: {str(e)}")
        raise


def generate_cover_letter(job_description, resume_folder="./resume", save_report=False):
    """
    封装完整的求职信生成流程

    参数:
        job_description (str): 岗位描述文本
        resume_folder (str): 简历PDF所在目录路径
        save_report (bool): 是否保存分析报告

    返回:
        tuple: (求职信内容, 分析报告内容) 或 (None, None)（失败时）
    """
    # 使用全局helper实例
    global helper
    print("[1/4] 初始化组件...")
    rga = RGAnalyzer()


    try:
        # 阶段1：准备数据
        print("[2/4] 分析简历和岗位要求...")
        resume_text = rga.load_resumes(resume_folder)
        if not resume_text:
            raise ValueError("未读取到有效的简历内容，请检查PDF文件")

        resume_chunks = rga.chunk_text(resume_text)
        job_requirements = [req.strip() for req in job_description.split("\n") if req.strip()]

        # 阶段2：计算匹配度
        print("[3/4] 计算岗位匹配度...")
        resume_emb = rga.encode_texts(resume_chunks)
        job_emb = rga.encode_texts(job_requirements)
        sim_matrix = rga.calculate_similarity(resume_emb, job_emb)

        # 阶段3：生成报告
        analysis_result = rga.generate_analysis_report(sim_matrix, resume_chunks, job_requirements)
        report_content = rga.format_report(analysis_result, "目标岗位")

        # 阶段4：生成求职信
        print("[4/4] 生成求职信...")
        print(f"当前生成模式: {'本地' if helper.use_local else '远程'}")
        prompt = generate_prompt_from_rga(job_description)
        cover_letter = helper.generate_letter(prompt)

        # 保存报告（可选）
        if save_report:
            with open("analysis_report.txt", "w", encoding="utf-8") as f:
                f.write(report_content)
            print("分析报告已保存到 analysis_report.txt")

        return cover_letter, report_content

    except Exception as e:
        print(f"\n[ERROR] 生成过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

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




if __name__ == "__main__":
    pass

    # print(2)
    # # 示例用法
    # job_desc = """
    # 我们正在寻找一名Python开发工程师，要求：
    # - 3年以上Python开发经验
    # - 熟悉Django/Flask框架
    # - 有云计算(AWS/Azure)经验者优先
    # - 良好的算法和数据结构基础
    # """
    # print(1)
    # try:
    #
    #     prompt = generate_prompt_from_rga(job_desc)
    #     print("正在生成生成prompt成功...")
    #     # print(prompt)
    #     helper = JobApplicationHelper()
    #     cover_letter = helper.generate_letter(prompt)
    #
    #     print("\n生成的求职信：")
    #     print(cover_letter)

        # 可选：保存分析报告
        # rga = RGAnalyzer()
        # resume_text = rga.load_resumes()
        # resume_chunks = rga.chunk_text(resume_text)
        # job_reqs = [req.strip() for req in job_desc.split("\n") if req.strip()]
        # emb_resume = rga.encode_texts(resume_chunks)
        # emb_job = rga.encode_texts(job_reqs)
        # sim_matrix = rga.calculate_similarity(emb_resume, emb_job)
        # report = rga.generate_analysis_report(sim_matrix, resume_chunks, job_reqs)
        #
        # with open("analysis_report.txt", "w") as f:
        #     f.write(rga.format_report(report, "Python开发工程师"))
