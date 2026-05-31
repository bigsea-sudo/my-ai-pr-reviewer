import requests
import hmac
import hashlib
import json

# 1. 对应你在 webhook.py 里配置的暗号和地址
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
        "diff_url": "https://github.com/bigsea-sudo/my-ai-pr-reviewer/pull/42.diff"
    }
}

# 将字典转为紧凑的 JSON 字符串字节流（防止空格导致哈希不一致）
body_bytes = json.dumps(mock_payload, separators=(',', ':')).encode('utf-8')

# 3. 工业级加密：计算 HMAC-SHA256 签名
hash_object = hmac.new(WEBHOOK_SECRET.encode('utf-8'), msg=body_bytes, digestmod=hashlib.sha256)
signature = "sha256=" + hash_object.hexdigest()

# 4. 配置 GitHub 特有的请求头
headers = {
    "Content-Type": "application/json",
    "X-Hub-Signature-256": signature  # 👈 验签核心
}

# 5. 发射请求
print("🚀 正在向本地 FastAPI 发送模拟 GitHub PR 触发请求...")
response = requests.post(url, data=body_bytes, headers=headers)

print(f"状态码 (Status Code): {response.status_code}")
print(f"响应内容 (Response JSON): {response.json()}")