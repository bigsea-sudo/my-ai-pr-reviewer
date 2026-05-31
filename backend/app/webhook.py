from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import logging
from app.diff_parser import DiffParser  # 👈 新增：引入解析器

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
        
        # 👈 核心亮点：触发异步抓取与智能切片解析
        try:
            raw_diff = await DiffParser.fetch_diff_text(diff_url)
            structured_diff = DiffParser.parse_diff(raw_diff)
            logger.info(f"✅ [Parser] 成功完成代码切片，共解析了 {len(structured_diff)} 个有效业务文件")
        except Exception as e:
            logger.error(f"❌ [Parser] 代码解析链条崩溃: {str(e)}")
            structured_diff = []

        return {
            "success": True,
            "message": f"Successfully processed PR #{pr_number}",
            "data": {
                "repo": repo_name,
                "pr_number": pr_number,
                "review_files_count": len(structured_diff),
                "structured_chunks": structured_diff  # 包含切片后的结构化数据
            }
        }
        
    return {"success": True, "message": "Event ignored"}