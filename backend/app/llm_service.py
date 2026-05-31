import httpx
import logging
import textwrap

logger = logging.getLogger("app")

class LLMReviewService:
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"
    MODEL_NAME = "deepseek-chat"

    SYSTEM_PROMPT = """你是一位世界顶尖的资深架构师。请对 Git Diff 代码块进行代码评审。
    格式要求：
    ### 🛠️ 文件: [文件名]
    - **Bug 评级**: [🔴致命 / 🟡警告 / 🔵优化]
    - **原因分析**: [原因]
    - **修改建议**: 
    ```python
    # 代码范例

    """


    ###
    @classmethod
    async def review_code_chunks(cls, structured_chunks: list) -> str:
        if not structured_chunks:
            return "### 📝 评审简报\n本次 PR 无代码变更。"

        final_report = "# 🚀 AI 自动化代码评审报告\n\n"
        async with httpx.AsyncClient(timeout=30.0) as client:
            for file_data in structured_chunks:
                filename = file_data.get("filename")
                chunks = file_data.get("chunks")
                
                user_content = f"待评审文件名: {filename}\n"
                for chunk in chunks:
                    for change in chunk.get("changes"):
                        sign = "+" if change["type"] == "addition" else "-"
                        user_content += f"{sign} {change['code']}\n"

                if "xxxx" in cls.API_KEY:
                    final_report += cls._generate_mock_review(filename)
                    continue
                
                # 此处省略 API 调用逻辑...
        return final_report

    @classmethod
    def _generate_mock_review(cls, filename: str) -> str:
        # 使用 textwrap.dedent 自动消除字符串内多余的行首缩进
        return textwrap.dedent(f"""
            ### 🛠️ 文件: {filename}
            - **Bug 评级**: 🔵 优化
            - **原因分析**: 代码结构健康。
            - **修改建议**: 
              ```python
              # 保持现状，批准合并！
              ```
            ---
        """).strip() # .strip() 可以确保字符串开头没有多余的空行