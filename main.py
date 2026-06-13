# -*- coding: utf-8 -*-
"""
每日投资情报推送系统 · 主程序
================================================
每日北京时间 07:30 运行,抓取三大板块数据,推送到钉钉

流程:
  1. 抓GitHub热门Top10
  2. 抓IPO日历(近一个月)
  3. 抓财报日历(近一个月,重点公司)
  4. 抓经济数据日历(近一周,高影响)
  5. 组装推送钉钉
"""

from datetime import datetime, timezone

import config
import sources
import formatter
import notify


def main():
    print("=" * 50)
    print(f"每日投资情报系统启动 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    # ── 1. GitHub热门 ──
    print("\n[1/4] 抓取GitHub热门...")
    github_repos = sources.fetch_github_trending(
        top_n=config.GITHUB_TOP_N,
        days=config.GITHUB_DAYS_WINDOW,
    )
    print(f"  获取到 {len(github_repos)} 个热门项目")

    # ── 2. IPO日历 ──
    print("\n[2/4] 抓取IPO日历...")
    ipos = sources.fetch_ipo_calendar(days_ahead=config.IPO_DAYS_AHEAD)
    print(f"  获取到 {len(ipos)} 个即将上市公司")

    # ── 3. 财报日历 ──
    print("\n[3/4] 抓取财报日历...")
    earnings = sources.fetch_earnings(
        days_ahead=config.EARNINGS_DAYS_AHEAD,
        watch_tickers=config.WATCH_TICKERS,
    )
    print(f"  获取到 {len(earnings)} 个重点财报")

    # ── 4. 经济数据 ──
    print("\n[4/4] 抓取经济数据日历...")
    econ = sources.fetch_economic(
        days_ahead=config.ECON_DAYS_AHEAD,
        min_impact=config.ECON_MIN_IMPACT,
    )
    print(f"  获取到 {len(econ)} 个重磅经济事件")

    # ── 组装并推送 ──
    print("\n组装推送内容...")
    report = formatter.build_full_report(github_repos, ipos, earnings, econ)

    # 数据健康检查:如果三个板块全空,可能是数据源全挂了,告警
    if not github_repos and not ipos and not earnings and not econ:
        err = ("## ⚠️ 每日情报系统告警\n\n"
               "四个数据源全部返回空,可能是网络问题或API key失效,"
               "请检查 GitHub Actions 日志和 Finnhub key。")
        notify.push(err, title="情报系统告警")
        print("所有数据源为空,已告警")
        return

    result = notify.push(report, title=config.REPORT_TITLE)
    if result:
        print("推送成功")
    elif result is None:
        print("未配置钉钉密钥,已打印内容")
    else:
        print("推送失败")


if __name__ == "__main__":
    main()
