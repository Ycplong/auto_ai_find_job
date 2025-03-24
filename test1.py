import os
import numpy as np
import requests

from PyPDF2 import PdfReader
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import client


class RGAnalyzer:
    """
    RGA（Relevance Gap Analysis）全流程分析器
    包含：数据准备 -> 嵌入计算 -> 匹配分析 -> 报告生成
    """

    def __init__(self, embedding_model='all-MiniLM-L6-v2'):
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
        """加载并合并简历文本（RGA预处理阶段）"""
        resume_text = ""
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                with open(os.path.join(folder_path, filename), "rb") as f:
                    reader = PdfReader(f)
                    resume_text += "\n".join(page.extract_text() for page in reader.pages)
        return self._clean_text(resume_text)

    def _clean_text(self, text):
        """文本清洗（私有方法）"""
        return ' '.join(text.split()).strip()

    def chunk_text(self, text):
        """文本分块（RGA预处理阶段）"""
        return self.text_splitter.split_text(text)

    # ----------------------
    # 阶段2：嵌入计算
    # ----------------------
    def encode_texts(self, texts):
        """生成文本嵌入向量（RGA嵌入阶段）"""
        return self.embedding_model.encode(texts)

    # ----------------------
    # 阶段3：核心分析
    # ----------------------
    def calculate_similarity(self, resume_embeddings, job_embeddings):
        """计算相似度矩阵（RGA匹配阶段）"""
        return cosine_similarity(resume_embeddings, job_embeddings)

    def dynamic_top_k(self, sim_matrix, min_k=1, max_k=5, threshold=0.7):
        """
        动态Top-K分析（RGA匹配阶段）
        返回：[{
            "requirement_idx": int,
            "top_indices": List[int],
            "k": int
        }]
        """
        results = []
        for j in range(sim_matrix.shape[1]):
            qualified = np.sum(sim_matrix[:, j] > threshold)
            k = min(max(qualified, min_k), max_k)
            top_indices = np.argpartition(sim_matrix[:, j], -k)[-k:]
            top_indices = top_indices[np.argsort(-sim_matrix[top_indices, j])]
            results.append({
                "requirement_idx": j,
                "top_indices": top_indices.tolist(),
                "k": k
            })
        return results

    # ----------------------
    # 阶段4：结果生成
    # ----------------------
    def generate_analysis_report(self, sim_matrix, resume_chunks, job_requirements):
        """
        生成完整RGA报告（RGA报告阶段）
        返回结构：
        {
            "by_requirement": [],  # 岗位视角
            "by_chunk": [],        # 简历视角
            "gap_score": float     # 整体匹配度
        }
        """
        # 岗位要求 -> 简历匹配
        requirement_results = []
        for j in range(len(job_requirements)):
            top_indices = np.argsort(sim_matrix[:, j])[-3:][::-1]
            requirement_results.append({
                "requirement": job_requirements[j],
                "top_matches": [
                    {"chunk": resume_chunks[i], "similarity": float(sim_matrix[i, j])}
                    for i in top_indices
                ]
            })

        # 简历 -> 岗位匹配
        chunk_results = []
        for i in range(len(resume_chunks)):
            top_indices = np.argsort(sim_matrix[i, :])[-3:][::-1]
            chunk_results.append({
                "chunk": resume_chunks[i],
                "top_relevant_requirements": [
                    {"requirement": job_requirements[j], "similarity": float(sim_matrix[i, j])}
                    for j in top_indices
                ]
            })

        return {
            "by_requirement": requirement_results,
            "by_chunk": chunk_results,
            "gap_score": float(1 - np.mean(np.max(sim_matrix, axis=0)))
        }

    def format_report(self, analysis_result, job_title):
        """生成可读性报告（RGA报告阶段）"""
        report = [
            f"=== {job_title} RGA分析报告 ===",
            f"整体匹配度: {(1 - analysis_result['gap_score']) * 100:.1f}%",
            "\n【岗位要求匹配】"
        ]

        for req in analysis_result['by_requirement']:
            report.append(f"\n► {req['requirement']}")
            for match in req["top_matches"]:
                report.append(f"  ✓ {match['chunk'][:80]}... ({match['similarity']:.0%})")

        report.append("\n【简历优势模块】")
        for chunk in analysis_result['by_chunk']:
            if chunk['top_relevant_requirements'][0]['similarity'] > 0.7:
                report.append(f"\n■ {chunk['chunk'][:80]}...")
                for req in chunk['top_relevant_requirements']:
                    report.append(f"  ▸ 匹配: {req['requirement']} ({req['similarity']:.0%})")

        return '\n'.join(report)


def generate_prompt_from_rga(resume_text, job_description, top_k=3):
    """
    根据RGA分析结果生成求职信的Prompt，并包含Top-K筛选

    参数:
        resume_text (str): 简历文本
        job_description (str): 岗位描述
        top_k (int): 每个岗位要求和简历块的Top-K匹配数

    返回:
        str: 生成的求职信的Prompt
    """
    # 创建RGA分析器对象
    rga = RGAnalyzer()
    #0.读取简历
    resume_text = rga.load_resumes()

    # 1. 进行RGA分析阶段：
    # -----
    resume_chunks = rga.chunk_text(resume_text)  # 将简历文本分块
    job_requirements = job_description.split("\n")  # 将岗位要求按行拆分

    resume_emb = rga.encode_texts(resume_chunks)  # 将简历分块编码为嵌入向量
    job_emb = rga.encode_texts(job_requirements)  # 将岗位要求编码为嵌入向量

    # 计算简历和岗位要求之间的相似度矩阵
    sim_matrix = rga.calculate_similarity(resume_emb, job_emb)

    # 2. 生成RGA分析报告阶段：
    # -----
    analysis_result = rga.generate_analysis_report(sim_matrix, resume_chunks, job_requirements)

    # 3. 基于RGA报告生成求职信的Prompt：
    # -----
    prompt = f"""
    你是一位求职助手，请根据以下信息为求职者写一封求职信：

    - 岗位要求：{job_description}
    - 简历优势：根据RGA分析，简历在以下岗位要求上有显著优势：
    """

    # 使用 Top-K 策略进行筛选
    for req in analysis_result["by_requirement"]:
        prompt += f"\n  - 岗位要求：{req['requirement']}"  # 添加岗位要求
        top_matches = req["top_matches"][:top_k]  # 获取Top-K匹配项

        for match in top_matches:
            prompt += f"\n    - 简历中相关部分：{match['chunk'][:100]}... (相似度: {match['similarity'] * 100:.2f}%)"  # 添加简历中与该要求匹配的内容

    # 在Prompt末尾，要求AI生成一个简洁的求职信，突出求职者的优势
    prompt += "\n请根据这些信息，撰写一封简洁的、专业的求职信，突出求职者的优势。"

    return prompt  # 返回生成的求职信Prompt


# ---- 解释每个步骤的作用 ----




class JobApplicationHelper:
    """
    一个处理生成求职信的助手类。
    包含两种方式：本地生成和远程生成。
    """

    def __init__(self, use_local=True, local_url="http://127.0.0.1:11434/api/chat", model="deepseek-r1:1.5b"):
        """
        初始化生成求职信助手。

        参数:
            use_local (bool): 是否使用本地生成求职信。默认为True，表示使用本地。
            local_url (str): 本地生成请求的URL，默认为本地服务器的URL。
            model (str): 使用的模型，默认为"deepseek-r1:1.5b"。
        """
        self.use_local = use_local
        self.local_url = local_url
        self.model = model

    def generate_letter(self, prompt):
        """
        根据提供的prompt生成求职信。

        参数:
            prompt (str): 求职信的生成Prompt。

        返回:
            str: 生成的求职信。
        """
        if self.use_local:
            return self.generate_letter_local(prompt)
        else:
            return self.generate_letter_remote(prompt)

    def generate_letter_local(self, prompt):
        """
        向本地AI发送Prompt生成求职信。

        参数:
            prompt (str): 求职信的生成Prompt

        返回:
            str: 生成的求职信
        """
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.local_url, headers=headers, json=data)
            response_json = response.json()
            content = response_json.get("message", {}).get("content", "")

            # 清理AI的回复
            content = " ".join(content.split())
            return content

        except Exception as e:
            print(f"生成求职信时发生错误: {e}")
            return "生成求职信时出错"

    def generate_letter_remote(self, prompt):
        """
        向远程AI发送Prompt生成求职信。

        参数:
            prompt (str): 求职信的生成Prompt

        返回:
            str: 生成的求职信
        """
        try:
            # 调用远程API生成求职信
            response = client.chat.completions.create(
                model="deepseek-chat",  # 使用深度模型生成对话
                messages=[
                    {"role": "system", "content": "你是一位专业的求职助手，能够根据简历和工作描述生成高质量的求职信。"},
                    {"role": "user", "content": prompt},  # 将Prompt作为用户消息发送
                ],
                stream=False  # 不开启流式处理
            )

            # 提取AI生成的求职信
            letter = response.choices[0].message.content

            # 清理AI的回复：去除换行符，避免分段问题
            letter = letter.replace('\n', ' ').strip()

            return letter

        except Exception as e:
            print(f"生成求职信时发生错误: {e}")
            return "生成求职信时出错"

if __name__=="__main__":

    job_description = """
        这是一个高级Python开发工程师的职位要求。候选人需具备5年以上Python开发经验，并熟悉Django/Flask框架，具备云计算平台使用经验以及本科及以上学历。
    """

    # 假设简历文本已经准备好（通常你可以通过 `RGAnalyzer` 类来处理简历）
    resumes = """
        具备6年Python开发经验，熟悉Django和Flask框架，曾参与多个基于云平台的项目。拥有云计算平台的深厚理解，以及多项优秀的项目开发经验。
    """

    # 生成Prompt
    prompt = generate_prompt_from_rga(resumes, job_description,3)

    # 向AI发送请求生成求职信
    letter = JobApplicationHelper().generate_letter_local(prompt)
    print("\n生成的求职信：\n", letter)
