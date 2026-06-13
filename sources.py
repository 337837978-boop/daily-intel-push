# -*- coding: utf-8 -*-
"""
每日投资情报系统 · 数据抓取模块
================================================
四个数据源:
  fetch_github_trending  GitHub热门(官方API)
  fetch_ipo_calendar     IPO日历(Finnhub)
  fetch_earnings         财报日历(Finnhub)
  fetch_economic         经济数据日历(Finnhub)
  check_binance_mirror   币安镜像代币检查
"""

import os
import time
from datetime import datetime, timedelta

import requests

import config

FINNHUB_KEY = config.FINNHUB_KEY or os.environ.get("FINNHUB_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"


# ======================================================================
# 1. GitHub热门(官方REST API,无需key)
# ======================================================================
def fetch_github_trending(top_n=10, days=7):
    """
    用GitHub官方搜索API:过去N天创建、按star排序的仓库
    等价于trending效果,且最稳定
    """
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"created:>{since}",
        "sort": "stars",
        "order": "desc",
        "per_page": top_n,
    }
    headers = {"Accept": "application/vnd.github+json"}
    # 如果有GITHUB_TOKEN可提高速率限制
    gh_token = os.environ.get("GITHUB_TOKEN", "")
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        items = r.json().get("items", [])
    except Exception as e:
        print(f"GitHub抓取失败: {e}")
        return []

    results = []
    for repo in items[:top_n]:
        results.append({
            # 【健壮性】全部用 .get 兜默认值，避免异常 item 缺键时 KeyError
            "full_name":   repo.get("full_name", ""),
            "name":        repo.get("name", ""),
            "stars":       repo.get("stargazers_count", 0),
            "language":    repo.get("language") or "其他",
            "description": repo.get("description") or "(暂无描述)",
            "url":         repo.get("html_url", ""),
        })
    return results


# ======================================================================
# 2. IPO日历(Finnhub)
# ======================================================================
def fetch_ipo_calendar(days_ahead=30):
    if not FINNHUB_KEY:
        print("缺少Finnhub key,跳过IPO")
        return []
    today = datetime.utcnow().date()
    to_date = today + timedelta(days=days_ahead)
    url = f"{FINNHUB_BASE}/calendar/ipo"
    params = {
        "from": today.isoformat(),
        "to":   to_date.isoformat(),
        "token": FINNHUB_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        ipos = r.json().get("ipoCalendar", [])
    except Exception as e:
        print(f"IPO抓取失败: {e}")
        return []

    results = []
    for ipo in ipos:
        # 只保留有日期和代码的
        if not ipo.get("date") or not ipo.get("symbol"):
            continue
        results.append({
            "date":     ipo.get("date"),
            "symbol":   ipo.get("symbol"),
            "name":     ipo.get("name", ""),
            "exchange": ipo.get("exchange", ""),
            "price":    ipo.get("price", ""),       # 预期价格区间
            "shares":   ipo.get("numberOfShares", ""),
            "status":   ipo.get("status", ""),
        })
    # 按日期排序
    results.sort(key=lambda x: x["date"])
    return results


# ======================================================================
# 3. 财报日历(Finnhub)
# ======================================================================
def fetch_earnings(days_ahead=30, watch_tickers=None):
    if not FINNHUB_KEY:
        print("缺少Finnhub key,跳过财报")
        return []
    today = datetime.utcnow().date()
    to_date = today + timedelta(days=days_ahead)
    url = f"{FINNHUB_BASE}/calendar/earnings"
    params = {
        "from": today.isoformat(),
        "to":   to_date.isoformat(),
        "token": FINNHUB_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        earnings = r.json().get("earningsCalendar", [])
    except Exception as e:
        print(f"财报抓取失败: {e}")
        return []

    watch = set(watch_tickers or [])
    results = []
    for e in earnings:
        sym = e.get("symbol", "")
        # 只保留关注列表里的大公司
        if watch and sym not in watch:
            continue
        # 【健壮性】跳过无日期条目：否则下面 results.sort(key=x["date"]) 会拿
        # None 与字符串比较抛 TypeError（与上面 IPO 路径的守卫保持一致）
        if not e.get("date"):
            continue
        eps_est = e.get("epsEstimate")
        # 注意：Finnhub 财报日历的 epsActual 是「本次」实际值，财报未发布时为 None，
        # 不能当作「上期」用来算同比（原代码 bug）。日历接口不提供上期 EPS，
        # 因此这里 eps_prev 保持 None，formatter 会安全地走「预期盈利正/负」判断，
        # 避免给出虚假的同比涨跌。
        eps_prev = None
        results.append({
            "date":     e.get("date"),
            "symbol":   sym,
            "hour":     e.get("hour", ""),        # bmo=盘前 amc=盘后
            "eps_est":  eps_est,
            "eps_prev": eps_prev,
            "rev_est":  e.get("revenueEstimate"),
        })
    results.sort(key=lambda x: x["date"])
    return results


# ======================================================================
# 4. 经济数据日历(Finnhub)
# ======================================================================
def fetch_economic(days_ahead=7, min_impact="medium"):
    if not FINNHUB_KEY:
        print("缺少Finnhub key,跳过经济数据")
        return []
    today = datetime.utcnow().date()
    to_date = today + timedelta(days=days_ahead)
    url = f"{FINNHUB_BASE}/calendar/economic"
    params = {
        "from": today.isoformat(),
        "to":   to_date.isoformat(),
        "token": FINNHUB_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        events = r.json().get("economicCalendar", [])
    except Exception as e:
        print(f"经济数据抓取失败: {e}")
        return []

    impact_rank = {"low":1, "medium":2, "high":3}
    min_rank = impact_rank.get(min_impact, 2)

    results = []
    for ev in events:
        # 只保留美国的高影响事件
        if ev.get("country") != "US":
            continue
        # 【健壮性】统一转小写，避免 API 返回 "High"/"HIGH"/None 等被当成 low 静默丢弃
        imp = str(ev.get("impact") or "low").strip().lower()
        if impact_rank.get(imp, 1) < min_rank:
            continue
        results.append({
            "date":     ev.get("time", "")[:10],
            "time":     ev.get("time", ""),
            "event":    ev.get("event", ""),
            "impact":   imp,
            "estimate": ev.get("estimate"),
            "prev":     ev.get("prev"),
            "actual":   ev.get("actual"),
        })
    results.sort(key=lambda x: x["time"])
    return results


# ======================================================================
# 5. 币安镜像代币检查
# ======================================================================
_binance_symbols_cache = None

def _load_binance_symbols():
    """加载币安所有现货和合约交易对,缓存。

    注意：GitHub Actions 服务器在境外，访问 api.binance.com 会被地域封锁
    返回 451。此时直接降级为空集合（视为无镜像），并用短超时避免拖慢整个
    推送。绝大多数美股本来就没有币安镜像，降级不影响主要信息。
    """
    global _binance_symbols_cache
    if _binance_symbols_cache is not None:
        return _binance_symbols_cache

    spot = set()
    futures = set()
    try:
        r = requests.get("https://api.binance.com/api/v3/exchangeInfo",
                         timeout=6)
        if r.status_code == 451:
            print("币安现货 451（地域封锁），降级为无镜像")
        elif r.ok:
            for s in r.json().get("symbols", []):
                spot.add(s["baseAsset"])
    except Exception as e:
        print(f"币安现货列表获取失败（降级无镜像）: {e}")
    try:
        r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo",
                         timeout=6)
        if r.status_code == 451:
            print("币安合约 451（地域封锁），降级为无镜像")
        elif r.ok:
            for s in r.json().get("symbols", []):
                futures.add(s["baseAsset"])
    except Exception as e:
        print(f"币安合约列表获取失败（降级无镜像）: {e}")

    _binance_symbols_cache = {"spot": spot, "futures": futures}
    return _binance_symbols_cache


def check_binance_mirror(symbol):
    """
    检查某个美股代码在币安有无镜像代币
    返回: (有无现货, 有无合约)
    注意:绝大多数美股在币安没有镜像,只有极少数(如QQQ/CRCL等)
    """
    if not config.CHECK_BINANCE_MIRROR or not symbol:
        return (False, False)
    syms = _load_binance_symbols()
    sym_upper = symbol.upper()
    has_spot = sym_upper in syms["spot"]
    has_futures = sym_upper in syms["futures"]
    return (has_spot, has_futures)
