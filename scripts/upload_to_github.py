#!/usr/bin/env python3
"""
通过 GitHub Contents API 上传简报文件，避免 shell 命令行参数长度限制。
使用 requests 直接发送 JSON body，无参数长度问题。
"""
import base64
import json
import os
import sys
from datetime import datetime, timezone, timedelta

import requests


def beijing_date() -> str:
    """返回北京时间当前日期 YYYY-MM-DD"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).strftime("%Y-%m-%d")


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    date_str = beijing_date()

    if not repo or not token:
        print(f"Missing GITHUB_REPOSITORY or GITHUB_TOKEN: repo={repo!r}")
        sys.exit(1)

    file_path = f"docs/briefings/{date_str}.json"

    if not os.path.isfile(file_path):
        print(f"No briefing file generated: {file_path}")
        sys.exit(0)

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    # 检查远程文件是否已存在（获取 SHA）
    sha = None
    resp = requests.get(api_url, headers=headers, timeout=30)
    if resp.status_code == 200:
        sha = resp.json().get("sha")

    # 构建请求体
    body = {
        "message": f"Auto: daily briefing {date_str}",
        "content": b64_content,
    }
    if sha:
        body["sha"] = sha

    # 上传
    resp = requests.put(api_url, headers=headers, json=body, timeout=60)

    if resp.status_code in (200, 201):
        print(f"Briefing uploaded: {file_path}")
        sys.exit(0)
    else:
        print(f"Upload failed: HTTP {resp.status_code}")
        print(resp.text[:500])
        sys.exit(1)


if __name__ == "__main__":
    main()
