# -*- coding: utf-8 -*-
"""
每日投资情报系统 · 消息格式化模块
================================================
把抓取的数据组装成钉钉markdown推送
按确认的排版:三大板块,粗细分隔线,结尾"高山仰止 景行行止"
"""

from datetime import datetime, timedelta

import config

# 语言图标映射
LANG_ICON = {
    "Python":"🐍","JavaScript":"📜","TypeScript":"📘","C++":"⚙️",
    "C":"⚙️","Go":"🐹","Rust":"🦀","Java":"☕","Ruby":"💎",
    "Shell":"🐚","HTML":"🌐","其他":"📦",
}

WEEKDAY_CN = ["周一","周二","周三","周四","周五","周六","周日"]


# ======================================================================
# 板块一:GitHub热门
# ======================================================================
def format_github(repos):
    if not repos:
        return "# 🔥 GitHub 今日热门\n\n> 暂无数据\n"

    circled = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩"]
    lines = ["# 🔥 GitHub 今日热门 Top 10\n"]

    for i, repo in enumerate(repos):
        num   = circled[i] if i < 10 else f"{i+1}."
        icon  = LANG_ICON.get(repo["language"], "📦")
        stars = f"{repo['stars']:,}"
        desc  = repo["description"]
        # 描述截断到合理长度
        if len(desc) > 100:
            desc = desc[:100] + "..."

        lines.append(f"**{num} {repo['full_name']}**")
        lines.append(f"⭐ {stars}　{icon} {repo['language']}")
        lines.append(f"> {desc}")
        lines.append(f"🔍 GitHub搜索 `{repo['name']}`")
        if i < len(repos) - 1:
            lines.append("─────────────")

    return "\n".join(lines)


# ======================================================================
# 板块二:美股动态(IPO + 财报)
# ======================================================================
def format_us_stocks(ipos, earnings):
    lines = ["# 📅 美股动态（近一个月）\n"]

    # ── 新股上市 ──
    lines.append("### 🆕 新股上市")
    if ipos:
        for ipo in ipos:
            date_str = _fmt_date(ipo["date"])
            name = ipo["name"]
            price = ipo.get("price") or "待定"
            price_str = f"${price}" if price != "待定" else "待定"
            lines.append(f"\n**{date_str}　{name}**")
            lines.append(f"`{ipo['symbol']}`　{price_str}　{ipo['exchange']}")
            # 币安镜像
            from sources import check_binance_mirror
            has_spot, has_fut = check_binance_mirror(ipo["symbol"])
            if has_spot or has_fut:
                parts = []
                if has_fut:  parts.append(f"✅合约 {ipo['symbol']}USDT")
                if has_spot: parts.append(f"✅现货 {ipo['symbol']}")
                lines.append(f"💱 币安：{' '.join(parts)}")
            else:
                lines.append(f"💱 币安：❌ 暂无镜像")
    else:
        lines.append("> 近一个月暂无确定的新股上市")

    lines.append("\n─────────────")

    # ── 重点财报 ──
    lines.append("### 📊 重点财报")
    if earnings:
        for e in earnings:
            date_str = _fmt_date(e["date"])
            sym = e["symbol"]
            cn = config.COMPANY_CN.get(sym, "")
            name_disp = f"{cn} {sym}" if cn else sym
            hour = _fmt_hour(e.get("hour", ""))
            eps_est = e.get("eps_est")

            lines.append(f"\n**{date_str}　{name_disp}**（{hour}）")
            if eps_est is not None:
                lines.append(f"预期EPS ${eps_est}")
                # 偏多偏空判断
                bias = _earnings_bias(e)
                lines.append(bias)
            else:
                lines.append("预期EPS 待定")
    else:
        lines.append("> 近一个月暂无重点公司财报")

    return "\n".join(lines)


def _earnings_bias(e):
    """根据EPS预期和上期对比,判断偏多偏空"""
    eps_est = e.get("eps_est")
    eps_prev = e.get("eps_prev")
    if eps_est is None:
        return "⚪ 中性：数据不足"
    # 如果有上期数据,对比
    if eps_prev is not None and eps_prev != 0:
        change = (eps_est - eps_prev) / abs(eps_prev) * 100
        if change > 5:
            return f"🟢 偏多：预期同比+{change:.0f}%，盈利改善"
        elif change < -5:
            return f"🔴 偏空：预期同比{change:.0f}%，盈利下滑"
        else:
            return f"⚪ 中性：预期与上期持平"
    # 无上期数据,只看EPS正负
    if eps_est > 0:
        return f"🟢 偏多：预期盈利为正"
    else:
        return f"🔴 偏空：预期仍亏损"


# ======================================================================
# 板块三:经济数据
# ======================================================================
# 常见经济指标的解释和影响逻辑
ECON_EXPLAIN = {
    "CPI": {
        "what": "衡量物价上涨速度，是美联储降息的最关键依据。",
        "high": "通胀比想象顽固，美联储不敢降息 → **利空股市、利空黄金、利空加密**",
        "low":  "通胀降温，降息预期升温 → **利好股市、利好加密**",
    },
    "Core CPI": {
        "what": "剔除食品能源的核心通胀，美联储更看重这个。",
        "high": "核心通胀顽固，降息推迟 → **利空风险资产**",
        "low":  "核心通胀回落，降息可期 → **利好股市和加密**",
    },
    "PCE": {
        "what": "美联储最看重的通胀指标。",
        "high": "通胀压力大 → **利空股市**",
        "low":  "通胀缓和 → **利好股市**",
    },
    "Nonfarm": {
        "what": "非农就业人数，反映经济和就业强弱。",
        "high": "就业强劲但可能延缓降息 → **影响中性偏空**",
        "low":  "就业疲软，衰退担忧但降息预期升温 → **影响中性偏多**",
    },
    "Unemployment": {
        "what": "失业率，越低说明就业市场越紧。",
        "high": "失业上升，经济转弱 → **利空股市**",
        "low":  "就业强劲 → **中性，过低或推高通胀**",
    },
    "Retail Sales": {
        "what": "零售销售，反映消费者花钱意愿。",
        "high": "消费强劲，经济健康 → **多数利好股市**",
        "low":  "消费疲软，衰退担忧 → **利空股市**",
    },
    "Interest Rate": {
        "what": "直接决定全球资金成本，对所有风险资产影响最大。",
        "high": "鹰派加息，抽走流动性 → **利空股市和加密**",
        "low":  "鸽派降息，流动性宽松 → **利好股市和加密**",
    },
    "GDP": {
        "what": "经济总量增速，衡量经济整体健康度。",
        "high": "经济强劲 → **利好股市**",
        "low":  "经济放缓 → **利空股市**",
    },
    "PPI": {
        "what": "生产者价格指数，是CPI的先行指标。",
        "high": "上游通胀压力大 → **利空股市**",
        "low":  "上游通胀缓和 → **利好股市**",
    },
}


def _match_econ_explain(event_name):
    """根据事件名匹配解释"""
    name_lower = event_name.lower()
    if "core cpi" in name_lower or ("core" in name_lower and "cpi" in name_lower):
        return ECON_EXPLAIN["Core CPI"]
    if "cpi" in name_lower:
        return ECON_EXPLAIN["CPI"]
    if "pce" in name_lower:
        return ECON_EXPLAIN["PCE"]
    if "nonfarm" in name_lower or "non-farm" in name_lower or "payroll" in name_lower:
        return ECON_EXPLAIN["Nonfarm"]
    if "unemployment" in name_lower:
        return ECON_EXPLAIN["Unemployment"]
    if "retail sales" in name_lower:
        return ECON_EXPLAIN["Retail Sales"]
    if "interest rate" in name_lower or "fed" in name_lower or "fomc" in name_lower or "rate decision" in name_lower:
        return ECON_EXPLAIN["Interest Rate"]
    if "gdp" in name_lower:
        return ECON_EXPLAIN["GDP"]
    if "ppi" in name_lower:
        return ECON_EXPLAIN["PPI"]
    return None


def format_economic(events):
    lines = ["# 📊 本周重磅经济数据\n"]
    if not events:
        lines.append("> 本周暂无重磅经济数据")
        return "\n".join(lines)

    for i, ev in enumerate(events):
        # 时间(UTC转北京时间)
        bj_time = _utc_to_bj(ev.get("time", ""))
        flag = "🇺🇸"
        impact_mark = " ⚠️ 高影响" if ev.get("impact") == "high" else ""

        lines.append(f"**{flag} {bj_time}**{impact_mark}")
        lines.append(f"### {ev['event']}")

        # 预期值和前值
        est = ev.get("estimate")
        prev = ev.get("prev")
        detail = []
        if est is not None:
            detail.append(f"预期 {est}")
        if prev is not None:
            detail.append(f"前值 {prev}")
        if detail:
            lines.append("　".join(detail))

        # 解释和影响
        explain = _match_econ_explain(ev["event"])
        if explain:
            lines.append(f"> {explain['what']}")
            lines.append(f"📈 **高于预期** → {explain['high']}")
            lines.append(f"📉 **低于预期** → {explain['low']}")
        else:
            lines.append(f"> 重要经济指标,关注实际值与预期的差异")

        if i < len(events) - 1:
            lines.append("─────────────")

    return "\n".join(lines)


# ======================================================================
# 组装完整推送
# ======================================================================
def build_full_report(github_repos, ipos, earnings, econ_events):
    now_bj = datetime.utcnow() + timedelta(hours=8)
    weekday = WEEKDAY_CN[now_bj.weekday()]
    date_str = now_bj.strftime("%Y-%m-%d")

    parts = []

    # 标题
    parts.append(f"# 📰 {config.REPORT_TITLE}")
    parts.append(f"### {date_str} {weekday} · 07:30")
    parts.append("═══════════════")

    # 板块一
    parts.append(format_github(github_repos))
    parts.append("═══════════════")

    # 板块二
    parts.append(format_us_stocks(ipos, earnings))
    parts.append("═══════════════")

    # 板块三
    parts.append(format_economic(econ_events))
    parts.append("═══════════════")

    # 结尾
    parts.append(f"📡 GitHub API · Finnhub")
    parts.append(f"\n**{config.FOOTER}**")

    return "\n\n".join(parts)


# ======================================================================
# 辅助函数
# ======================================================================
def _fmt_date(date_str):
    """2026-06-18 → 06-18"""
    try:
        return date_str[5:] if len(date_str) >= 10 else date_str
    except Exception:
        return date_str


def _fmt_hour(hour_code):
    """bmo→盘前 amc→盘后"""
    mapping = {"bmo":"盘前","amc":"盘后","dmh":"盘中"}
    return mapping.get(hour_code, hour_code or "时间待定")


def _utc_to_bj(utc_time_str):
    """UTC时间字符串转北京时间显示"""
    try:
        dt = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
        bj = dt + timedelta(hours=8)
        weekday = WEEKDAY_CN[bj.weekday()]
        return bj.strftime(f"%m-%d {weekday} %H:%M")
    except Exception:
        try:
            # 只有日期的情况
            dt = datetime.strptime(utc_time_str[:10], "%Y-%m-%d")
            weekday = WEEKDAY_CN[dt.weekday()]
            return dt.strftime(f"%m-%d {weekday}")
        except Exception:
            return utc_time_str
