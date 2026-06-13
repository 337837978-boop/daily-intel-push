# -*- coding: utf-8 -*-
"""
每日投资情报推送系统 · 配置文件
================================================
三个板块:GitHub热门Top10 + 美股动态(IPO+财报) + 重磅经济数据
每日北京时间 07:30 推送到钉钉

数据源:
  GitHub热门  → GitHub官方REST API(免费,无需key)
  IPO日历     → Finnhub API(免费,需注册key)
  财报日历     → Finnhub API
  经济数据日历 → Finnhub API
"""

# ── Finnhub API Key(去 finnhub.io 免费注册) ──
# 部署时通过 GitHub Secrets 注入,不要硬编在这里
# 本地测试可临时填这里
FINNHUB_KEY = ""   # 留空则从环境变量 FINNHUB_KEY 读取

# ── GitHub热门设置 ──
GITHUB_TOP_N = 10              # 取前几名
GITHUB_DAYS_WINDOW = 7         # 过去几天创建的仓库算"热门"

# ── 美股动态设置 ──
IPO_DAYS_AHEAD = 30            # 未来几天的IPO
EARNINGS_DAYS_AHEAD = 30       # 未来几天的财报
# 财报只关注大公司(市值过滤,单位美元),避免小公司刷屏
EARNINGS_MIN_MARKETCAP = 50_000_000_000   # 500亿美元以上

# 重点关注的大公司(财报必显示,不受市值过滤影响)
WATCH_TICKERS = [
    "NVDA","TSLA","AAPL","MSFT","GOOGL","AMZN","META",
    "JPM","BAC","GS","NFLX","AMD","INTC","BABA","PDD"
]

# 公司中文名映射(常见大公司)
COMPANY_CN = {
    "NVDA":"英伟达","TSLA":"特斯拉","AAPL":"苹果","MSFT":"微软",
    "GOOGL":"谷歌","AMZN":"亚马逊","META":"Meta","JPM":"摩根大通",
    "BAC":"美国银行","GS":"高盛","NFLX":"奈飞","AMD":"超威半导体",
    "INTC":"英特尔","BABA":"阿里巴巴","PDD":"拼多多",
}

# ── 经济数据设置 ──
ECON_DAYS_AHEAD = 7           # 未来7天的经济数据
# 只关注高影响事件(Finnhub的impact字段:low/medium/high)
ECON_MIN_IMPACT = "medium"

# ── 币安镜像检查 ──
CHECK_BINANCE_MIRROR = True   # 检查IPO公司在币安有无镜像代币

# ── 推送设置 ──
REPORT_TITLE = "每日投资情报"
FOOTER = "高山仰止 景行行止"
