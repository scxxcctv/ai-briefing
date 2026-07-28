#!/usr/bin/env python3
"""
API 连通性验证脚本 - 验证 DeepSeek API 密钥是否有效
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    # 加载 .env 文件
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("[FAIL] DEEPSEEK_API_KEY not set")
        print("  Edit .env file with your API key from https://platform.deepseek.com/api_keys")
        print('  Or set environment: set DEEPSEEK_API_KEY=sk-...')
        sys.exit(1)

    print(f"Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Model: {model}")
    print(f"Base URL: {base_url}")
    print("Testing connection...")

    from openai import OpenAI
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": "回复'API连通正常'"}],
        )
        text = response.choices[0].message.content or ""

        print(f"[OK] API connected")
        print(f"  Response: {text.strip()}")
        print(f"  Model: {response.model}")
        print(f"  Tokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")
        return 0
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
