# -*- coding: utf-8 -*-
"""
每日投资情报系统 · 消息格式化模块（最终模板版）
================================================
最终模板要点：
  · 顶部「⚡ 今日速览」一行 TL;DR
  · GitHub：中文标签 + 🎯前置强相关 + 中文描述 + 量化类↳点评
  · IPO：公司名「中文（English）」并列
  · 财报：中文名 + 英文代码 + 「还有N天」+ 盘前/盘后
  · 经济数据：事件名「中文（English）」并列 + 相对时间（今晚/后天凌晨）
  · 结尾「高山仰止 景行行止」
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

# 经济事件英文名 → 中文名（本地映射，覆盖常见高影响事件）
ECON_NAME_CN = {
    "cpi": "CPI 通胀",
    "core cpi": "核心CPI",
    "cpi mom": "CPI 月率",
    "cpi yoy": "CPI 年率",
    "core cpi mom": "核心CPI 月率",
    "core cpi yoy": "核心CPI 年率",
    "ppi": "PPI 生产者物价",
    "core ppi": "核心PPI",
    "pce": "PCE 物价",
    "core pce": "核心PCE",
    "nonfarm payrolls": "非农就业",
    "non-farm payrolls": "非农就业",
    "nonfarm": "非农就业",
    "unemployment rate": "失业率",
    "initial jobless claims": "初请失业金",
    "retail sales": "零售销售",
    "core retail sales": "核心零售销售",
    "gdp": "GDP 经济增速",
    "gdp growth rate": "GDP 增速",
    "fed interest rate decision": "美联储利率决议",
    "interest rate decision": "利率决议",
    "fomc": "FOMC 会议",
    "fomc minutes": "FOMC 会议纪要",
    "ism manufacturing pmi": "ISM 制造业PMI",
    "ism services pmi": "ISM 服务业PMI",
    "consumer confidence": "消费者信心指数",
    "michigan consumer sentiment": "密歇根消费者信心",
    "durable goods orders": "耐用品订单",
}


# ======================================================================
# 顶部「今日速览」：抽取当天最该注意的 1-2 件事
# ======================================================================
def _build_tldr(earnings, econ_events):
    """从经济数据(高影响)和近期财报里挑出最该注意的，拼一行速览。"""
    highlights = []

    # 高影响经济事件（最多取2个，按时间）
    for ev in econ_events:
        if ev.get("impact") == "high":
            cn = _econ_name_cn(ev["event"])
            # 速览里只取中文部分（去掉英文括号），更紧凑
            cn_short = cn.split("（")[0]
            rel = _relative_day(ev.get("time", ""))
            rel_str = f"{rel}" if rel else ""
            highlights.append(f"{rel_str}{cn_short}")
        if len(highlights) >= 2:
            break

    # 近一周内的重点财报（最多补1个）
    now = datetime.utcnow() + timedelta(hours=8)
    for e in earnings:
        days = _days_until(e.get("date", ""))
        if days is not None and 0 <= days <= 7:
            sym = e["symbol"]
            cn = config.COMPANY_CN.get(sym, sym)
            highlights.append(f"{cn}{_fmt_hour(e.get('hour',''))}财报")
            break

    if not highlights:
        return ""
    return "**⚡ 今日速览**：" + "｜".join(highlights)


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
        tag   = repo.get("tag", "")
        note  = repo.get("note", "")
        # 中文描述优先，回退英文
        desc  = repo.get("desc_cn") or repo.get("description", "")
        if len(desc) > 100:
            desc = desc[:100] + "..."

        # 强相关（量化/交易、数据/基础设施）前置 🎯
        bullseye = "🎯 " if tag in ("量化/交易", "数据/基础设施") else ""
        tag_str = f"　`{tag}`" if tag else ""

        lines.append(f"**{bullseye}{num} {repo['full_name']}**{tag_str}")
        lines.append(f"⭐ {stars}　{icon} {repo['language']}")
        lines.append(f"> {desc}")
        if note:
            lines.append(f"　↳ {note}")
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
            name_en = ipo.get("name", "")
            name_cn = ipo.get("name_cn", "")
            # 「中文（English）」并列，没有中文译名就只显示英文
            if name_cn and name_en:
                name_disp = f"{name_cn}（{name_en}）"
            else:
                name_disp = name_cn or name_en or ipo.get("symbol", "")

            price = ipo.get("price") or "待定"
            price_str = f"${price}" if price != "待定" else "待定"

            # 币安镜像并到同一行
            from sources import check_binance_mirror
            has_spot, has_fut = check_binance_mirror(ipo["symbol"])
            if has_spot or has_fut:
                parts = []
                if has_fut:  parts.append(f"合约{ipo['symbol']}USDT")
                if has_spot: parts.append(f"现货{ipo['symbol']}")
                mirror = "💱 ✅ " + " ".join(parts)
            else:
                mirror = "💱 ❌ 无镜像"

            lines.append(f"\n**{date_str}　{name_disp}**")
            lines.append(f"`{ipo['symbol']}`　{price_str}　{ipo['exchange']}　{mirror}")
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

            # 「还有N天」
            days = _days_until(e.get("date", ""))
            if days is not None:
                if days == 0:
                    when = "今天"
                elif days == 1:
                    when = "明天"
                else:
                    when = f"还有{days}天"
                date_disp = f"{date_str}（{when}）"
            else:
                date_disp = date_str

            lines.append(f"\n**{date_disp}　{name_disp}**　{hour}")
            if eps_est is not None:
                bias = _earnings_bias(e)
                lines.append(f"预期EPS ${eps_est}　{bias}")
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
    if eps_prev is not None and eps_prev != 0:
        change = (eps_est - eps_prev) / abs(eps_prev) * 100
        if change > 5:
            return f"🟢 偏多：同比+{change:.0f}%，盈利改善"
        elif change < -5:
            return f"🔴 偏空：同比{change:.0f}%，盈利下滑"
        else:
            return f"⚪ 中性：预期与上期持平"
    if eps_est > 0:
        return f"🟢 偏多：预期盈利为正"
    else:
        return f"🔴 偏空：预期仍亏损"


# ======================================================================
# 板块三:经济数据
# ======================================================================
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


def _econ_name_cn(event_name):
    """事件英文名 → 「中文（English）」；查不到映射就只显示英文。"""
    key = event_name.lower().strip()
    cn = ECON_NAME_CN.get(key)
    if not cn:
        # 模糊匹配：包含关系
        for k, v in ECON_NAME_CN.items():
            if k in key:
                cn = v
                break
    if cn:
        return f"{cn}（{event_name}）"
    return event_name


def format_economic(events):
    lines = ["# 📊 本周重磅经济数据\n"]
    if not events:
        lines.append("> 本周暂无重磅经济数据")
        return "\n".join(lines)

    for i, ev in enumerate(events):
        bj_time = _utc_to_bj(ev.get("time", ""))
        rel = _relative_day(ev.get("time", ""))
        rel_str = f"（{rel}）" if rel else ""
        flag = "🇺🇸"
        impact_mark = " ⚠️ 高影响" if ev.get("impact") == "high" else ""

        lines.append(f"**{flag} {bj_time}{rel_str}**{impact_mark}")
        lines.append(f"### {_econ_name_cn(ev['event'])}")

        est = ev.get("estimate")
        prev = ev.get("prev")
        detail = []
        if est is not None:
            detail.append(f"预期 {est}")
        if prev is not None:
            detail.append(f"前值 {prev}")
        if detail:
            lines.append("　".join(detail))

        explain = _match_econ_explain(ev["event"])
        if explain:
            lines.append(f"> {explain['what']}")
            lines.append(f"📈 高于预期 → {explain['high']}")
            lines.append(f"📉 低于预期 → {explain['low']}")
        else:
            lines.append(f"> 重要经济指标，关注实际值与预期的差异")

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

    # 今日速览
    tldr = _build_tldr(earnings, econ_events)
    if tldr:
        parts.append(tldr)

    parts.append("═══════════════")

    parts.append(format_github(github_repos))
    parts.append("═══════════════")

    parts.append(format_us_stocks(ipos, earnings))
    parts.append("═══════════════")

    parts.append(format_economic(econ_events))
    parts.append("═══════════════")

    parts.append(f"📡 GitHub API · Finnhub")
    parts.append(f"**{config.FOOTER}**")

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


def _days_until(date_str):
    """距今天还有几天（按北京时间日期）。无法解析返回 None。"""
    try:
        target = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        today = (datetime.utcnow() + timedelta(hours=8)).date()
        return (target - today).days
    except Exception:
        return None


def _relative_day(utc_time_str):
    """根据北京时间日期返回 今晚/明天/后天凌晨 等相对描述；无则返回 ''。"""
    try:
        dt = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
    except Exception:
        try:
            dt = datetime.strptime(utc_time_str[:10], "%Y-%m-%d") + timedelta(hours=8)
        except Exception:
            return ""
    today = (datetime.utcnow() + timedelta(hours=8)).date()
    delta = (dt.date() - today).days
    hour = dt.hour
    # 凌晨判断（0-6点）
    is_dawn = 0 <= hour < 6
    if delta == 0:
        return "凌晨" if is_dawn else ("今晚" if hour >= 18 else "今天")
    if delta == 1:
        return "明天凌晨" if is_dawn else ("明晚" if hour >= 18 else "明天")
    if delta == 2:
        return "后天凌晨" if is_dawn else "后天"
    if 3 <= delta <= 6:
        return f"{delta}天后凌晨" if is_dawn else f"{delta}天后"
    return ""


def _utc_to_bj(utc_time_str):
    """UTC时间字符串转北京时间显示"""
    try:
        dt = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
        bj = dt + timedelta(hours=8)
        weekday = WEEKDAY_CN[bj.weekday()]
        return bj.strftime(f"%m-%d {weekday} %H:%M")
    except Exception:
        try:
            dt = datetime.strptime(utc_time_str[:10], "%Y-%m-%d")
            weekday = WEEKDAY_CN[dt.weekday()]
            return dt.strftime(f"%m-%d {weekday}")
        except Exception:
            return utc_time_str
