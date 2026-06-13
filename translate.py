# -*- coding: utf-8 -*-
"""
每日投资情报系统 · 翻译与标签模块（DeepSeek）
================================================
用 DeepSeek 把 GitHub 仓库描述、IPO 公司名翻成通顺中文，
并给 GitHub 项目打一个领域标签 + 对量化/交易类项目给一句点评。

为什么用 DeepSeek：国内可直连（不像 Binance 会 451），中文翻译
质量好，价格极低（一天十几条，月成本可忽略）。

环境变量（GitHub Secrets）：
  DEEPSEEK_KEY   DeepSeek API key（sk- 开头）

设计要点：
  1. 一次推送只调用一次大模型——把当天所有 GitHub 项目和 IPO 公司
     打包成一个 JSON 请求，让模型一次性返回，省钱省时、稳定。
  2. 严格要求模型只返回 JSON，本地安全解析；任何异常都降级
     （翻译失败就回退英文原文 / 标签留空），绝不让推送整体挂掉。
  3. 标签固定七类，模型只能选不能自由发挥，避免乱写。
"""

import os
import json
import requests

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "")
DEEPSEEK_BASE = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"   # 便宜够用，翻译质量好

# 固定的七类领域标签，模型只能从这里选
ALLOWED_TAGS = [
    "量化/交易", "数据/基础设施", "AI应用", "AI模型",
    "前端", "后端/工具", "其他",
]

REQUEST_TIMEOUT = 40


def _call_deepseek(system_prompt, user_payload):
    """调用 DeepSeek，返回解析后的 dict；任何失败返回 None。"""
    if not DEEPSEEK_KEY:
        print("缺少 DEEPSEEK_KEY，跳过 AI 翻译，回退英文原文")
        return None

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        # 强制 JSON 输出，最大限度避免模型加多余文字
        "response_format": {"type": "json_object"},
    }
    try:
        r = requests.post(DEEPSEEK_BASE, headers=headers, json=body,
                          timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        # 去掉可能的 ```json 包裹
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"DeepSeek 调用/解析失败，回退原文: {e}")
        return None


# ======================================================================
# GitHub：翻译描述 + 打标签 + 量化类点评
# ======================================================================
def enrich_github(repos):
    """
    输入 sources.fetch_github_trending 的结果列表，
    给每个 repo 增加三个字段：
        desc_cn  中文描述（翻译失败回退英文原文）
        tag      七类领域标签之一（失败留空 ""）
        note     仅当 tag=="量化/交易" 时的一句点评，否则 ""
    返回处理后的同一列表（原地补字段）。
    """
    if not repos:
        return repos

    # 先给所有 repo 填好默认值（降级用）
    for repo in repos:
        repo.setdefault("desc_cn", repo.get("description", ""))
        repo.setdefault("tag", "")
        repo.setdefault("note", "")

    payload = {
        "repos": [
            {
                "id": i,
                "full_name": repo["full_name"],
                "language": repo.get("language", ""),
                "description": repo.get("description", ""),
            }
            for i, repo in enumerate(repos)
        ]
    }

    system_prompt = (
        "你是一个面向中文量化交易者的技术情报助手。"
        "用户是一名做系统化量化交易的投资者，关注：股票/纳指、加密货币永续合约、"
        "回测框架、交易所 API、数据基础设施、自动化通知。\n"
        "给定一组 GitHub 热门仓库，对每个仓库返回三项：\n"
        "1) desc_cn：把英文描述翻成通顺、地道、简洁的中文（不超过40字，不要机翻腔，"
        "不要逐词直译，像懂技术的人介绍项目那样说人话）。若原描述为空则返回空字符串。\n"
        f"2) tag：从这七个里选最贴切的一个：{ALLOWED_TAGS}。\n"
        "3) note：仅当 tag 是“量化/交易”时，写一句不超过35字、具体说明它对量化交易者"
        "可能的用处（结合回测/交易所API/数据/通知等场景）；其它标签一律返回空字符串。\n"
        "严格只返回 JSON，格式：{\"repos\":[{\"id\":0,\"desc_cn\":\"...\",\"tag\":\"...\",\"note\":\"...\"}]}。"
        "不要输出任何额外文字、解释或 markdown。"
    )

    result = _call_deepseek(system_prompt, payload)
    if not result or "repos" not in result:
        return repos  # 降级：保留英文原文

    # 把结果按 id 回填
    by_id = {item.get("id"): item for item in result["repos"]
             if isinstance(item, dict)}
    for i, repo in enumerate(repos):
        item = by_id.get(i)
        if not item:
            continue
        desc_cn = (item.get("desc_cn") or "").strip()
        tag = (item.get("tag") or "").strip()
        note = (item.get("note") or "").strip()
        if desc_cn:
            repo["desc_cn"] = desc_cn
        if tag in ALLOWED_TAGS:
            repo["tag"] = tag
        # note 只在量化/交易类保留
        repo["note"] = note if repo.get("tag") == "量化/交易" else ""
    return repos


# ======================================================================
# IPO：翻译公司名为「中文（English）」
# ======================================================================
def enrich_ipos(ipos):
    """
    给每个 ipo 增加 name_cn 字段：公司名的简洁中文译名。
    翻译失败留空字符串，formatter 会自行回退只显示英文。
    """
    if not ipos:
        return ipos

    for ipo in ipos:
        ipo.setdefault("name_cn", "")

    payload = {
        "companies": [
            {"id": i, "name": ipo.get("name", ""), "symbol": ipo.get("symbol", "")}
            for i, ipo in enumerate(ipos)
        ]
    }

    system_prompt = (
        "你是金融翻译助手。给定一组即将美股 IPO 的公司英文名，"
        "为每家公司给出简洁、自然的中文公司名（不超过12字，体现行业，"
        "如生物医药、科技、金融、能源等；不确定时按字面+行业意译，"
        "不要音译成奇怪的人名）。\n"
        "严格只返回 JSON：{\"companies\":[{\"id\":0,\"name_cn\":\"...\"}]}。"
        "不要输出任何额外文字。"
    )

    result = _call_deepseek(system_prompt, payload)
    if not result or "companies" not in result:
        return ipos

    by_id = {item.get("id"): item for item in result["companies"]
             if isinstance(item, dict)}
    for i, ipo in enumerate(ipos):
        item = by_id.get(i)
        if not item:
            continue
        name_cn = (item.get("name_cn") or "").strip()
        if name_cn:
            ipo["name_cn"] = name_cn
    return ipos
