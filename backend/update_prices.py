#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格刷新脚本（GitHub Actions 执行）
- 实时价 + 期初价，统一走共享行情模块 market_data（submodule）
- 多数据源 fallback；全部标的全失败才 exit(1)，单个失败不整次红
"""
import json
import os
import sys
from datetime import datetime

# 共享行情模块（submodule）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'vendor', 'market-data'))
import market_data as md


def load_products():
    with open(os.path.join(SCRIPT_DIR, "products.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def refresh_current_prices(products_data):
    print("\n[1/2] 刷新当前价格...")
    underlyings = products_data.get("underlyings", {})
    prices_path = os.path.join(SCRIPT_DIR, "prices.json")
    old_prices = {}
    if os.path.exists(prices_path):
        with open(prices_path, "r", encoding="utf-8") as f:
            old_prices = json.load(f)

    prices = {}
    failed = []
    seen_codes = set()  # 去重，同一 code 只请求一次

    for name, info in underlyings.items():
        code = info.get("code")
        if not code:
            continue
        if code in seen_codes:
            print(f"\n  [{name}] {code} (已获取，跳过)")
            continue
        seen_codes.add(code)

        print(f"\n  [{name}] {code}")
        price, date_str = md.fetch_price(code)
        if price and price > 0:
            prices[code] = {"price": price, "date": date_str, "time": f"{date_str} 收盘"}
            print(f"  => {price} ({date_str})")
        elif code in old_prices:
            # 获取失败时保留旧值，避免价格丢失
            prices[code] = old_prices[code]
            print(f"  => 获取失败，保留旧值 {old_prices[code].get('price')}")
            failed.append(f"{name}({code})")
        else:
            print("  => 未获取到（所有数据源均失败）")
            failed.append(f"{name}({code})")

    with open(prices_path, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    print(f"\n已写入 prices.json，共 {len(prices)} 个标的")

    # 全部标的全失败才退出；部分失败只告警，不整次红
    if failed and len(failed) >= len(seen_codes):
        print(f"\n!!! 全部标的获取失败: {', '.join(failed)}")
        sys.exit(1)
    if failed:
        print(f"\n⚠ 部分标的失败（已跳过/保留旧值）: {', '.join(failed)}")
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

        underlying_code = underlyings.get(underlying, {}).get("code")
        if not underlying_code:
            print(f"\n  [{code}] 标的'{underlying}'未配置代码，跳过")
            continue

        print(f"\n  [{code}] {underlying} 期初日: {start_date}")
        price, actual_date = md.fetch_initial_price(underlying_code, start_date)
        if price and price > 0:
            initial_prices[code] = {"price": price, "date": actual_date, "underlying": underlying}
            print(f"  => {price} ({actual_date})")
        else:
            print("  => 未获取到")

    with open(initial_path, "w", encoding="utf-8") as f:
        json.dump(initial_prices, f, ensure_ascii=False, indent=2)
    print(f"\n已写入 initial_prices.json")
    return initial_prices


def detect_knockout(products_data):
    """单鲨结构敲出检测：历史收盘价触及敲出价则锁定敲出基准"""
    print("\n[3/3] 单鲨敲出检测...")
    products = products_data.get("products", [])
    underlyings = products_data.get("underlyings", {})

    initial_path = os.path.join(SCRIPT_DIR, "initial_prices.json")
    if not os.path.exists(initial_path):
        print("  无期初价文件，跳过")
        return
    with open(initial_path, "r", encoding="utf-8") as f:
        initial_prices = json.load(f)

    changed = 0
    today = datetime.now().strftime("%Y-%m-%d")

    for prod in products:
        if prod.get("product_type") != "single_shark":
            continue
        code = prod.get("product_code")
        # 已敲出跳过
        if prod.get("event_record", {}).get("knockout_occur_date"):
            continue
        start_date = prod.get("start_obs_date")
        underlying = prod.get("underlying")
        if not code or not start_date or not underlying:
            continue
        init = initial_prices.get(code, {}).get("price")
        if not init:
            continue
        up_barrier = (prod.get("structure_params") or {}).get("up_barrier_pct")
        if not up_barrier:
            continue
        underlying_code = underlyings.get(underlying, {}).get("code")
        if not underlying_code:
            continue

        # 期初观察日未到，不检测
        if start_date > today:
            continue

        knockout_price = init * up_barrier
        klines = md.fetch_kline(underlying_code, start_date, today)
        if not klines:
            print(f"  ⚠ [{code}] {underlying} K线获取失败，敲出检测跳过")
            continue

        # 找首个收盘价触及敲出价的日期
        hit_date = None
        for date in sorted(klines.keys()):
            if klines[date] >= knockout_price:
                hit_date = date
                break
        if hit_date:
            prod.setdefault("event_record", {})["knockout_occur_date"] = hit_date
            print(f"  [{code}] {underlying} 敲出日 {hit_date}（收盘 {klines[hit_date]} >= 敲出价 {knockout_price:.2f}）")
            changed += 1

    if changed:
        products_path = os.path.join(SCRIPT_DIR, "products.json")
        with open(products_path, "w", encoding="utf-8") as f:
            json.dump(products_data, f, ensure_ascii=False, indent=1)
        print(f"\n已回写 products.json，新增敲出 {changed} 个")
    else:
        print("\n无新增敲出产品")


def main():
    print("=" * 50)
    print(f"  价格刷新脚本 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    products_data = load_products()
    print(f"  产品数: {len(products_data.get('products', []))}")
    print(f"  标的数: {len(products_data.get('underlyings', {}))}")

    refresh_current_prices(products_data)
    refresh_initial_prices(products_data)
    detect_knockout(products_data)

    print("\n完成!")


if __name__ == "__main__":
    main()
