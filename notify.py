# -*- coding: utf-8 -*-
"""
比特币长线系统 · 钉钉推送模块（2026-06-10 审查修复版）
=======================================================
HMAC-SHA256 加签推送，与纳指/BTC短线系统同一套机制。

本次修复：增加推送重试（3次，间隔5秒）。钉钉偶发抖动不应吞掉
11年仅约4次的买卖信号；重试仍失败则返回 False，由 main.py 决定
是否抛异常阻止状态落盘。

环境变量（GitHub Secrets）：
  DINGTALK_WEBHOOK   钉钉机器人 webhook
  DINGTALK_SECRET    钉钉机器人加签密钥（SEC 开头）
"""

import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests

WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
SECRET = os.environ.get("DINGTALK_SECRET", "")

PUSH_RETRIES = 3
RETRY_WAIT = 5  # 秒


def _signed_url():
    # 时间戳每次重试需重新生成（钉钉要求签名时间戳与服务器时差<1小时）
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{SECRET}"
    hmac_code = hmac.new(
        SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"{WEBHOOK}&timestamp={timestamp}&sign={sign}"


def push(text, title="每日投资情报"):
    """发送 Markdown 消息到钉钉。成功返回 True，失败返回 False，未配置返回 None。"""
    if not WEBHOOK or not SECRET:
        print("未配置钉钉密钥，消息内容如下：\n", text)
        return None

    payload = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": text},
    }
    for attempt in range(1, PUSH_RETRIES + 1):
        try:
            r = requests.post(_signed_url(), json=payload, timeout=10)
            result = r.json()
            if result.get("errcode") == 0:
                print("钉钉推送成功")
                return True
            print(f"钉钉推送失败({attempt}/{PUSH_RETRIES})：{result}")
        except Exception as e:
            print(f"钉钉推送异常({attempt}/{PUSH_RETRIES})：{e}")
        if attempt < PUSH_RETRIES:
            time.sleep(RETRY_WAIT)
    return False
