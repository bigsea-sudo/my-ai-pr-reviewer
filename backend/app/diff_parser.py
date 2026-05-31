import re
import httpx
import logging

logger = logging.getLogger("app")

class DiffParser:
    """
    智能 Git Diff 解析引擎
    负责将纯文本的 Git Diff 转换为结构化的 Python 数据对象，并过滤工程噪音。
    """
    
    # 工业级规范：过滤无需 AI Review 的噪音文件后缀
    IGNORE_EXTENSIONS = [
        '.json', '.lock', '.yaml', '.yml', '.md', '.png', 
        '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.toml'
    ]

    @classmethod
    async def fetch_diff_text(cls, diff_url: str) -> str:
        """异步从 GitHub 抓取原始 Diff 文本"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # GitHub Diff 接口支持直接请求获取纯文本
                response = await client.get(diff_url)
                if response.status_code != 200:
                    raise Exception(f"无法获取 Diff 文本，状态码: {response.status_code}")
                return response.text
            except Exception as e:
                logger.error(f"抓取云端 Diff 失败: {str(e)}")
                raise

    @classmethod
    def parse_diff(cls, diff_text: str) -> list:
        """
        核心原创算法：将复杂的 Git Diff 文本流式切片为结构化字典字典列表
        """
        if not diff_text:
            return []

        # 按照 Git 标准的 "diff --git" 进行文件级切割
        file_diffs = re.split(r'^diff --git ', diff_text, flags=re.M)
        parsed_files = []

        for file_data in file_diffs:
            if not file_data.strip():
                continue
                
            lines = file_data.splitlines()
            filename = None
            
            # 提取文件名
            for line in lines:
                if line.startswith('+++ b/'):
                    filename = line[6:]
                    break
            
            if not filename:
                continue

            # 噪声拦截：如果文件属于锁文件、图片或文档，直接跳过，节省大模型 Token
            if any(filename.endswith(ext) for ext in cls.IGNORE_EXTENSIONS):
                logger.info(f"过滤噪音文件: {filename}")
                continue

            current_file_chunks = []
            current_chunk = None

            # 遍历每一行，解析出变动的代码块
            for line in lines:
                # 匹配 Git 的 Hunk 头部（例如：@@ -12,8 +12,9 @@）
                hunk_match = re.match(r'^@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
                if hunk_match:
                    if current_chunk:
                        current_file_chunks.append(current_chunk)
                    
                    # 锚定变动的起始行号
                    new_start_line = int(hunk_match.group(2))
                    current_chunk = {
                        "line_start": new_start_line,
                        "changes": []
                    }
                    continue

                if current_chunk is not None:
                    # 如果是以 '+' 开头，代表是本次新增的代码（AI 评审的核心核心靶向目标）
                    if line.startswith('+') and not line.startswith('+++'):
                        current_chunk["changes"].append({
                            "type": "addition",
                            "code": line[1:]
                        })
                    # 如果是以 '-' 开头，代表是被删除的代码
                    elif line.startswith('-') and not line.startswith('---'):
                        current_chunk["changes"].append({
                            "type": "deletion",
                            "code": line[1:]
                        })
                    # 普通上下文行号顺延
                    elif line.startswith(' '):
                        current_chunk["changes"].append({
                            "type": "context",
                            "code": line[1:]
                        })

            if current_chunk and current_chunk["changes"]:
                current_file_chunks.append(current_chunk)

            if current_file_chunks:
                parsed_files.append({
                    "filename": filename,
                    "chunks": current_file_chunks
                })

        return parsed_files