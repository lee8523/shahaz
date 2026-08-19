#!/usr/bin/env python3
"""
价格刷新脚本（GitHub Actions 执行）
- 每日自动刷新当前价格 → prices.json
- 手动刷新期初价格 → initial_prices.json
- 纯 requests，不依赖 akshare
- 每个标的双数据源 fallback，全部失败则 exit(1)
"""
import json
import os
import sys
import time
import re
from datetime import datetime, timedelta

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ── 工具函数 ──────────────────────────────────────────────

def safe_get(url, headers=None, timeout=15, retries=3):
    """带重试的 HTTP GET"""
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=h, timeout=timeout)
            if r.status_code == 200:
                return r
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
        if i < retries - 1:
            time.sleep(2 ** i)
    raise Exception(last_err)


# ── 指数行情 ──────────────────────────────────────────────

def fetch_index_sina(code):
    """新浪指数行情"""
    r = safe_get(f"https://hq.sinajs.cn/list=s_sh{code}",
                 headers={"Referer": "https://finance.sina.com.cn"})
    text = r.text
    m = re.search(r'"([^"]+)"', text)
    if not m:
        return None, None
    parts = m.group(1).split(",")
    if len(parts) < 2:
        return None, None
    try:
        price = float(parts[1])
        if price > 0:
            return price, datetime.now().strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        pass
    return None, None


def fetch_index_tencent(code):
    """腾讯指数行情"""
    r = safe_get(f"https://qt.gtimg.cn/q=s_sh{code}")
    text = r.text
    m = re.search(r'"([^"]+)"', text)
    if not m:
        return None, None
    parts = m.group(1).split("~")
    if len(parts) < 4:
        return None, None
    try:
        price = float(parts[3])
        if price > 0:
            return price, datetime.now().strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        pass
    return None, None


def fetch_index_eastmoney(code):
    """东方财富指数行情（带 Referer）"""
    r = safe_get(
        f"https://push2.eastmoney.com/api/qt/stock/get?secid=1.{code}&fields=f43,f58,f57",
        headers={"Referer": "https://quote.eastmoney.com"})
    data = r.json()
    d = data.get("data")
    if not d:
        return None, None
    price = d.get("f43")
    if price and price > 0:
        price = price / 100 if price > 10000 else price
        date_str = datetime.now().strftime("%Y-%m-%d")
        return price, date_str
    return None, None


def fetch_index(code):
    """获取指数最新价，双数据源 fallback"""
    fetchers = [
        ("新浪", lambda: fetch_index_sina(code)),
        ("腾讯", lambda: fetch_index_tencent(code)),
        ("东方财富", lambda: fetch_index_eastmoney(code)),
    ]
    for name, fn in fetchers:
        try:
            price, date_str = fn()
            if price and price > 0:
                print(f"    [{name}] {price} ({date_str})")
                return price, date_str
        except Exception as e:
            print(f"    [{name}] 失败: {e}")
    return None, None


# ── ETF 行情 ──────────────────────────────────────────────

def fetch_etf_sina(code):
    """新浪 ETF 行情"""
    prefix = "sh" if code.startswith(("5", "6")) else "sz"
    r = safe_get(f"https://hq.sinajs.cn/list=s_{prefix}{code}",
                 headers={"Referer": "https://finance.sina.com.cn"})
    text = r.text
    m = re.search(r'"([^"]+)"', text)
    if not m:
        return None, None
    parts = m.group(1).split(",")
    if len(parts) < 2:
        return None, None
    try:
        price = float(parts[1])
        if price > 0:
            return price, datetime.now().strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        pass
    return None, None


def fetch_etf_tencent(code):
    """腾讯 ETF 行情"""
    prefix = "sh" if code.startswith(("5", "6")) else "sz"
    r = safe_get(f"https://qt.gtimg.cn/q=s_{prefix}{code}")
    text = r.text
    m = re.search(r'"([^"]+)"', text)
    if not m:
        return None, None
    parts = m.group(1).split("~")
    if len(parts) < 4:
        return None, None
    try:
        price = float(parts[3])
        if price > 0:
            return price, datetime.now().strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        pass
    return None, None


def fetch_etf_eastmoney(code):
    """东方财富 ETF 行情"""
    prefix = "1" if code.startswith(("5", "6")) else "0"
    r = safe_get(
        f"https://push2.eastmoney.com/api/qt/stock/get?secid={prefix}.{code}&fields=f43,f58,f57",
        headers={"Referer": "https://quote.eastmoney.com"})
    data = r.json()
    d = data.get("data")
    if not d:
        return None, None
    price = d.get("f43")
    if price and price > 0:
        price = price / 100 if price > 10000 else price
        return price, datetime.now().strftime("%Y-%m-%d")
    return None, None


def fetch_etf(code):
    """获取 ETF 最新价"""
    fetchers = [
        ("新浪", lambda: fetch_etf_sina(code)),
        ("腾讯", lambda: fetch_etf_tencent(code)),
        ("东方财富", lambda: fetch_etf_eastmoney(code)),
    ]
    for name, fn in fetchers:
        try:
            price, date_str = fn()
            if price and price > 0:
                print(f"    [{name}] {price} ({date_str})")
                return price, date_str
        except Exception as e:
            print(f"    [{name}] 失败: {e}")
    return None, None


# ── 期货行情 ──────────────────────────────────────────────

def fetch_futures_sina(code):
    """新浪期货行情"""
    r = safe_get(f"https://hq.sinajs.cn/list=nf_{code}",
                 headers={"Referer": "https://finance.sina.com.cn"})
    text = r.text
    m = re.search(r'"([^"]+)"', text)
    if not m:
        return None, None
    parts = m.group(1).split(",")
    if len(parts) < 4:
        return None, None
    # parts[3] 是昨收, 新浪期货实时价用 parts[8] (最新价)
    try:
        # 优先用最新价(parts[8]), 回退到昨收(parts[3])
        for idx in [8, 3]:
            price = float(parts[idx])
            if price > 0:
                # 日期在倒数位置
                date_str = datetime.now().strftime("%Y-%m-%d")
                return price, date_str
    except (ValueError, IndexError):
        pass
    return None, None


def fetch_futures_eastmoney(code):
    """东方财富期货行情"""
    r = safe_get(
        f"https://push2.eastmoney.com/api/qt/stock/get?secid=113.{code}&fields=f43,f58,f57",
        headers={"Referer": "https://quote.eastmoney.com"})
    data = r.json()
    d = data.get("data")
    if not d:
        return None, None
    price = d.get("f43")
    if price and price > 0:
        return price, datetime.now().strftime("%Y-%m-%d")
    return None, None


def fetch_futures(code):
    """获取期货最新价"""
    fetchers = [
        ("新浪", lambda: fetch_futures_sina(code)),
        ("东方财富", lambda: fetch_futures_eastmoney(code)),
    ]
    for name, fn in fetchers:
        try:
            price, date_str = fn()
            if price and price > 0:
                print(f"    [{name}] {price} ({date_str})")
                return price, date_str
        except Exception as e:
            print(f"    [{name}] 失败: {e}")
    return None, None


# ── 黄金 AU9999 ──────────────────────────────────────────

def fetch_gold_eastmoney():
    """东方财富黄金行情（尝试多个 secid）"""
    for secid in ["118.AU9999", "113.AU9999"]:
        try:
            r = safe_get(
                f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f58,f57",
                headers={"Referer": "https://quote.eastmoney.com"})
            data = r.json()
            d = data.get("data")
            if not d:
                continue
            price = d.get("f43")
            if price and price > 0:
                price = price / 100 if price > 10000 else price
                return price, datetime.now().strftime("%Y-%m-%d")
        except Exception:
            continue
    return None, None


def fetch_gold_tencent():
    """腾讯黄金行情"""
    r = safe_get("https://qt.gtimg.cn/q=sgeAU9999")
    text = r.text
    m = re.search(r'"([^"]+)"', text)
    if not m or "none_match" in m.group(1):
        return None, None
    parts = m.group(1).split("~")
    if len(parts) < 4:
        return None, None
    try:
        price = float(parts[3])
        if price > 0:
            return price, datetime.now().strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        pass
    return None, None


def fetch_gold():
    """获取黄金 AU9999 最新价"""
    fetchers = [
        ("东方财富", fetch_gold_eastmoney),
        ("腾讯", fetch_gold_tencent),
    ]
    for name, fn in fetchers:
        try:
            price, date_str = fn()
            if price and price > 0:
                print(f"    [{name}] {price} ({date_str})")
                return price, date_str
        except Exception as e:
            print(f"    [{name}] 失败: {e}")
    return None, None


# ── 期初价格（历史数据） ──────────────────────────────────

def fetch_initial_index(code, target_date):
    """获取指数历史收盘价"""
    # 新浪历史日K
    try:
        r = safe_get(
            f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
            f"?symbol=sh{code}&scale=240&ma=no&datalen=30",
            headers={"Referer": "https://finance.sina.com.cn"})
        data = r.json()
        target = target_date[:10]
        for item in data:
            if item.get("day") == target:
                price = float(item["close"])
                if price > 0:
                    return price, target
        # 取最近一个交易日
        for item in reversed(data):
            if item.get("day", "") <= target:
                price = float(item["close"])
                if price > 0:
                    return price, item["day"]
    except Exception as e:
        print(f"    [期初-新浪K线] 失败: {e}")

    # 东方财富历史
    try:
        r = safe_get(
            f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
            f"secid=1.{code}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
            f"&klt=101&fqt=0&end=20500101&lmt=60",
            headers={"Referer": "https://quote.eastmoney.com"})
        data = r.json()
        klines = data.get("data", {}).get("klines", [])
        target = target_date[:10]
        for line in reversed(klines):
            parts = line.split(",")
            if len(parts) >= 3:
                day = parts[0]
                close = float(parts[2])
                if day <= target and close > 0:
                    return close, day
    except Exception as e:
        print(f"    [期初-东方财富K线] 失败: {e}")

    return None, None


def fetch_initial_futures(code, target_date):
    """获取期货历史收盘价"""
    # 新浪期货历史
    try:
        r = safe_get(
            f"https://stock2.finance.sina.com.cn/futures/api/json_v2.php/"
            f"IndexService.getInnerFuturesDailyKLine?symbol={code}",
            headers={"Referer": "https://finance.sina.com.cn"})
        data = r.json()
        target = target_date[:10]
        for item in data:
            if item.get("date") == target:
                price = float(item["close"])
                if price > 0:
                    return price, target
        for item in reversed(data):
            if item.get("date", "") <= target:
                price = float(item["close"])
                if price > 0:
                    return price, item["date"]
    except Exception as e:
        print(f"    [期初-新浪期货K线] 失败: {e}")

    # 东方财富期货历史
    try:
        r = safe_get(
            f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
            f"secid=113.{code}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
            f"&klt=101&fqt=0&end=20500101&lmt=60",
            headers={"Referer": "https://quote.eastmoney.com"})
        data = r.json()
        klines = data.get("data", {}).get("klines", [])
        target = target_date[:10]
        for line in reversed(klines):
            parts = line.split(",")
            if len(parts) >= 3:
                day = parts[0]
                close = float(parts[2])
                if day <= target and close > 0:
                    return close, day
    except Exception as e:
        print(f"    [期初-东方财富期货K线] 失败: {e}")

    return None, None


def fetch_initial_gold(target_date):
    """获取黄金 AU9999 历史收盘价（尝试多个 secid）"""
    for secid in ["118.AU9999", "113.AU9999"]:
        try:
            r = safe_get(
                f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
                f"secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
                f"&klt=101&fqt=0&end=20500101&lmt=60",
                headers={"Referer": "https://quote.eastmoney.com"})
            data = r.json()
            klines = data.get("data", {}).get("klines", [])
            target = target_date[:10]
            for line in reversed(klines):
                parts = line.split(",")
                if len(parts) >= 3:
                    day = parts[0]
                    close = float(parts[2])
                    if day <= target and close > 0:
                        return close, day
        except Exception as e:
            print(f"    [期初-黄金K线 {secid}] 失败: {e}")
    return None, None


# ── 标的分类 ──────────────────────────────────────────────

INDEX_CODES = {"000852", "000905", "000300"}
ETF_CODES = {"588000", "159915"}
GOLD_CODES = {"AU9999"}


def classify_code(code):
    if code in INDEX_CODES:
        return "index"
    if code in ETF_CODES:
        return "etf"
    if code in GOLD_CODES:
        return "gold"
    return "futures"


# ── 主流程 ──────────────────────────────────────────────

def load_products():
    path = os.path.join(SCRIPT_DIR, "products.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def refresh_current_prices(products_data):
    print("\n[1/2] 刷新当前价格...")
    underlyings = products_data.get("underlyings", {})
    prices = {}
    failed = []
    seen_codes = set()  # 去重，同一 code 只请求一次

    for name, info in underlyings.items():
        code = info.get("code")
        if not code:
            continue

        # 去重：同一 code 只获取一次
        if code in seen_codes:
            print(f"\n  [{name}] {code} (已获取，跳过)")
            continue
        seen_codes.add(code)

        print(f"\n  [{name}] {code}")
        cat = classify_code(code)

        if cat == "index":
            price, date_str = fetch_index(code)
        elif cat == "etf":
            price, date_str = fetch_etf(code)
        elif cat == "gold":
            price, date_str = fetch_gold()
        elif cat == "futures":
            price, date_str = fetch_futures(code)
        else:
            print(f"  => 未知类型，跳过")
            continue

        if price and price > 0:
            prices[code] = {
                "price": price,
                "date": date_str,
                "time": f"{date_str} 收盘"
            }
            print(f"  => {price} ({date_str})")
        else:
            print(f"  => 未获取到（所有数据源均失败）")
            failed.append(f"{name}({code})")

    if failed:
        print(f"\n!!! 以下标的获取失败: {', '.join(failed)}")
        sys.exit(1)

    output_path = os.path.join(SCRIPT_DIR, "prices.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    print(f"\n已写入 prices.json，共 {len(prices)} 个标的")
    return prices


def refresh_initial_prices(products_data):
    print("\n[2/2] 刷新期初价格...")
    products = products_data.get("products", [])
    underlyings = products_data.get("underlyings", {})

    initial_path = os.path.join(SCRIPT_DIR, "initial_prices.json")
    if os.path.exists(initial_path):
        with open(initial_path, "r", encoding="utf-8") as f:
            initial_prices = json.load(f)
    else:
        initial_prices = {}

    for prod in products:
        code = prod.get("product_code")
        underlying = prod.get("underlying")
        start_date = prod.get("start_obs_date")

        if not code or not underlying or not start_date:
            continue

        if start_date > datetime.now().strftime("%Y-%m-%d"):
            print(f"\n  [{code}] 期初观察日 {start_date} 未到，跳过")
            continue

        if code in initial_prices:
            print(f"\n  [{code}] 已有期初价，跳过")
            continue

        underlying_info = underlyings.get(underlying, {})
        underlying_code = underlying_info.get("code")
        if not underlying_code:
            print(f"\n  [{code}] 标的'{underlying}'未配置代码，跳过")
            continue

        print(f"\n  [{code}] {underlying} 期初日: {start_date}")
        cat = classify_code(underlying_code)

        if cat in ("index", "etf"):
            price, actual_date = fetch_initial_index(underlying_code, start_date)
        elif cat == "gold":
            price, actual_date = fetch_initial_gold(start_date)
        elif cat == "futures":
            price, actual_date = fetch_initial_futures(underlying_code, start_date)
        else:
            print(f"  => 未知类型")
            continue

        if price and price > 0:
            initial_prices[code] = {
                "price": price,
                "date": actual_date,
                "underlying": underlying
            }
            print(f"  => {price} ({actual_date})")
        else:
            print(f"  => 未获取到")

    output_path = os.path.join(SCRIPT_DIR, "initial_prices.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(initial_prices, f, ensure_ascii=False, indent=2)
    print(f"\n已写入 initial_prices.json")
    return initial_prices


def main():
    print("=" * 50)
    print(f"  价格刷新脚本 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    products_data = load_products()
    print(f"  产品数: {len(products_data.get('products', []))}")
    print(f"  标的数: {len(products_data.get('underlyings', {}))}")

    refresh_current_prices(products_data)
    refresh_initial_prices(products_data)

    print("\n完成!")


if __name__ == "__main__":
    main()
