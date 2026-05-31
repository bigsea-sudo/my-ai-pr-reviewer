from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import logging
from app.diff_parser import DiffParser
from app.llm_service import LLMReviewService  # 👈 新增：引入大模型驱动引擎

logger = logging.getLogger("app")
router = APIRouter(prefix="/api", tags=["Webhook"])

WEBHOOK_SECRET = "my_secure_secret_123"

async def verify_signature(request: Request, x_hub_signature_256: str):
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Invalid signature")
    body = await request.body()
    hash_object = hmac.new(WEBHOOK_SECRET.encode('utf-8'), msg=body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

@router.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    await verify_signature(request, x_hub_signature_256)
    
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    action = payload.get("action")
    pr_data = payload.get("pull_request")
    
    if pr_data and action in ["opened", "synchronize"]:
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name")
        diff_url = pr_data.get("diff_url")
        
        logger.info(f"🚀 [Webhook] 监听到 PR #{pr_number}，正在调用引擎拉取并解析代码...")
        
        try:
            # 1. 抓取并进行流式代码切片
            raw_diff = await DiffParser.fetch_diff_text(diff_url)
            structured_diff = DiffParser.parse_diff(raw_diff)
            logger.info(f"✅ [Parser] 成功完成代码切片，共解析了 {len(structured_diff)} 个有效业务文件")
            
            # 2. 【最终合体】将切片后的数据定向喂给大模型评审引擎
            logger.info(f"🤖 [AI-Review] 正在将代码流传送至大模型适配层...")
            review_report = await LLMReviewService.review_code_chunks(structured_diff)
            logger.info(f"🎉 [AI-Review] 大模型自动化审计报告生成完毕！")
            
        except Exception as e:
            logger.error(f"❌ [Pipeline] 全链路通信故障: {str(e)}")
            review_report = f"# ❌ 自动评审链条故障\n解析与AI交互阶段崩溃: {str(e)}"

        # 最终返回给 GitHub 或前端的工业级结构化载荷
        return {
            "success": True,
            "message": f"Successfully reviewed PR #{pr_number}",
            "data": {
                "repo": repo_name,
                "pr_number": pr_number,
                "report": review_report  # 🌟 核心亮点：里面包裹着惊艳的 Markdown 自动化评审报告
            }
        }
        
    return {"success": True, "message": "Event ignored"}