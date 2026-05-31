import requests
import hmac
import hashlib
import json

# 1. 对应配置
WEBHOOK_SECRET = "my_secure_secret_123"
url = "http://127.0.0.1:8000/api/webhook"

# 2. 模拟标准的 GitHub Pull Request 载荷 (Payload)
mock_payload = {
    "action": "opened",
    "number": 42,
    "repository": {
        "full_name": "bigsea-sudo/my-ai-pr-reviewer"
    },
    "pull_request": {
        "diff_url": "https://patch-diff.githubusercontent.com/raw/bigsea-sudo/my-ai-pr-reviewer/pull/1.diff" # 👈 亮点：换成你真实 PR #1 的公开 Diff 补丁链接，测试可以真正联网抓取！
    }
}

body_bytes = json.dumps(mock_payload, separators=(',', ':')).encode('utf-8')

# 3. 计算签名
hash_object = hmac.new(WEBHOOK_SECRET.encode('utf-8'), msg=body_bytes, digestmod=hashlib.sha256)
signature = "sha256=" + hash_object.hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Hub-Signature-256": signature
}

print("🚀 正在向本地 FastAPI 发送模拟 GitHub PR 触发请求...")
try:
    response = requests.post(url, data=body_bytes, headers=headers)
    print(f"状态码 (Status Code): {response.status_code}")
    print(f"响应内容 (Response JSON): {response.json()}")
except Exception as e:
    print(f"❌ 请求失败: {str(e)}")