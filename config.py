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
    "JPM","BAC","GS","NFLX","AMD","INTC","BABA","PDD",
    "SPY","QQQ","DIA","IWM","XLF","XLE","XLK","XLV",
    "PLTR","AVGO","ORCL","CRM","ADBE","NOW","UBER",
    "KO","PEP","WMT","COST","HD","MCD","SBUX",
    "V","MA","AXP","DIS","NKE","BA","CAT","GE",
    "ABBV","PFE","MRK","UNH","LLY","JNJ","CVX","XOM",
    "TSM","SAP","CSCO","QCOM","SONY","TM","HMC",
    "HSBC","RY","BNS","TD","GME","AMC","RBLX","SNAP",
    "HOOD","COIN","MSTR",
    "SQQQ","TQQQ","LABU","SOXL","FNGU","FNGD",
    "BIDU","JD","NTES","LI","XPEV","NIO",
    "TME","BILI","BEKE","TCOM","YUMC","ZTO","IQ","FUTU","TIGR",
    "MARA","RIOT","CLSK","WULF","IREN",

]

# 公司中文名映射(常见大公司)
COMPANY_CN = {
    # 科技
    "NVDA":"英伟达","TSLA":"特斯拉","AAPL":"苹果","MSFT":"微软",
    "GOOGL":"谷歌","AMZN":"亚马逊","META":"Meta","NFLX":"奈飞",
    "AMD":"超威半导体","INTC":"英特尔","AVGO":"博通","ORCL":"甲骨文",
    "CRM":"赛富时","ADBE":"Adobe","NOW":"ServiceNow","UBER":"优步",
    "TSM":"台积电","CSCO":"思科","QCOM":"高通","SAP":"SAP",
    "SONY":"索尼","RBLX":"Roblox","SNAP":"Snap",
    # 金融
    "JPM":"摩根大通","BAC":"美国银行","GS":"高盛",
    "V":"Visa","MA":"万事达","AXP":"美国运通",
    "HSBC":"汇丰银行","RY":"加拿大皇家银行","BNS":"丰业银行","TD":"道明银行",
    "HOOD":"Robinhood","COIN":"Coinbase","MSTR":"微策略",
    "FUTU":"富途控股","TIGR":"老虎证券",
    # 消费
    "KO":"可口可乐","PEP":"百事可乐","WMT":"沃尔玛","COST":"好市多",
    "HD":"家得宝","MCD":"麦当劳","SBUX":"星巴克","NKE":"耐克",
    "DIS":"迪士尼","GME":"游戏驿站","AMC":"AMC院线",
    # 工业制造
    "BA":"波音","CAT":"卡特彼勒","GE":"通用电气",
    "TM":"丰田","HMC":"本田",
    # 医疗
    "ABBV":"艾伯维","PFE":"辉瑞","MRK":"默克","UNH":"联合健康",
    "LLY":"礼来","JNJ":"强生",
    # 能源
    "XOM":"埃克森美孚","CVX":"雪佛龙",
    # 中概股
    "BABA":"阿里巴巴","BIDU":"百度","JD":"京东","NTES":"网易",
    "PDD":"拼多多","LI":"理想汽车","XPEV":"小鹏汽车","NIO":"蔚来",
    "TME":"腾讯音乐","BILI":"哔哩哔哩","BEKE":"贝壳找房",
    "TCOM":"携程旅行","YUMC":"百胜中国","ZTO":"中通快递",
    "IQ":"爱奇艺",
    # ETF & 杠杆
    "SPY":"标普500ETF","QQQ":"纳斯达克ETF","DIA":"道指ETF",
    "IWM":"罗素2000ETF",
    "XLF":"金融ETF","XLE":"能源ETF","XLK":"科技ETF","XLV":"医疗ETF",
    "SQQQ":"三倍做空纳指","TQQQ":"三倍做多纳指",
    "LABU":"三倍做多生物科技","SOXL":"三倍做多半导体",
    "FNGU":"三倍做多FAANG+","FNGD":"三倍做空FAANG+",
    # 加密/矿场
    "MARA":"MARA Holdings","RIOT":"Riot Platforms",
    "CLSK":"CleanSpark","WULF":"TeraWulf","IREN":"Iris Energy",
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
