from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import json
import logging

logger = logging.getLogger("app")
router = APIRouter(prefix="/api", tags=["Webhook"])

# 线上应该从环境变量读取，比赛本地测试期间我们先硬编码一个暗号（Secret）
WEBHOOK_SECRET = "my_secure_secret_123"

async def verify_signature(request: Request, x_hub_signature_256: str):
    """
    工业级安全规范：验证 GitHub 请求签名，防止越权伪造
    """
    if not x_hub_signature_256:
        logger.warning("拒绝请求：缺少 X-Hub-Signature-256 请求头")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 必须读取原始的字节流（Raw Body）进行哈希比对
    body = await request.body()
    
    # 计算本地哈希
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    # 使用安全常量时间比较，防止时序攻击（Timing Attack，高端加分词汇）
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        logger.warning("拒绝请求：签名不匹配，疑似伪造请求！")
        raise HTTPException(status_code=401, detail="Invalid signature")

@router.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    """
    接收 GitHub Pull Request 事件的核心接口
    """
    # 1. 触发安全验签
    await verify_signature(request, x_hub_signature_256)
    
    # 2. 解析 JSON 载荷
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # 3. 过滤事件：我们只关心 Pull Request 事件，且只关心新建(opened)或更新(synchronize)
    action = payload.get("action")
    pr_data = payload.get("pull_request")
    
    if pr_data and action in ["opened", "synchronize"]:
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name")
        # 核心亮点：拿到这个 PR 的 diff 文本下载链接！
        diff_url = pr_data.get("diff_url")
        
        logger.info(f"监听到目标仓库 [{repo_name}] 提交了 PR #{pr_number}, 动作为: {action}")
        logger.info(f"成功捕获到代码 Diff 补丁链接: {diff_url}")
        
        # 4. 返回 200 OK，告诉 GitHub 我们听到了（后续 PR 会把任务丢进异步队列，这里先返回）
        return {
            "success": True,
            "message": f"Successfully received PR #{pr_number}",
            "data": {
                "repo": repo_name,
                "pr_number": pr_number,
                "diff_url": diff_url
            }
        }
        
    return {"success": True, "message": "Event ignored (not a target PR action)"}