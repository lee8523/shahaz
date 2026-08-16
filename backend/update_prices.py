#!/usr/bin/env python3
"""
价格刷新脚本（GitHub Actions 执行）
- 每日自动刷新当前价格 → prices.json
- 手动刷新期初价格 → initial_prices.json
读取 products.json 获取标的配置和产品列表
"""
import json
import os
from datetime import datetime, timedelta

try:
    import akshare as ak
except ImportError:
    print("Installing akshare...")
    os.system("pip install akshare")
    import akshare as ak

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_products():
    """加载 products.json"""
    path = os.path.join(SCRIPT_DIR, "products.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_close_by_date(df, target_date_str):
    """从 DataFrame 中查找目标日期的收盘价"""
    date_col = None
    for col in df.columns:
        cl = str(col).lower()
        if "日期" in cl or "date" in cl:
            date_col = col
            break
    if not date_col:
        return None, None
    
    close_col = None
    for col in df.columns:
        cl = str(col).lower()
        if "收盘" in cl or cl == "close":
            close_col = col
            break
    if not close_col:
        return None, None
    
    df["_date_str"] = df[date_col].astype(str).str[:10]
    target = target_date_str[:10]
    
    matched = df[df["_date_str"] == target]
    if len(matched) > 0:
        return float(matched.iloc[-1][close_col]), target
    
    # 找不到精确日期，取最接近的（前后7天内）
    try:
        target_dt = datetime.strptime(target, "%Y-%m-%d")
        best_diff = None
        best_price = None
        best_date = None
        for _, row in df.iterrows():
            try:
                row_dt = datetime.strptime(str(row["_date_str"]), "%Y-%m-%d")
                diff = abs((row_dt - target_dt).days)
                if diff <= 7 and (best_diff is None or diff < best_diff):
                    best_diff = diff
                    best_price = float(row[close_col])
                    best_date = str(row["_date_str"])
            except (ValueError, TypeError):
                continue
        if best_price and best_price > 0:
            return best_price, best_date
    except Exception:
        pass
    
    return None, None

def fetch_latest_sge_gold():
    """SGE 黄金 AU9999 最新收盘价"""
    try:
        df = ak.spot_hist_sge(symbol="Au99.99")
        if len(df) > 0:
            last = df.iloc[-1]
            close_col = None
            for col in df.columns:
                if "收盘" in str(col).lower() or str(col).lower() == "close":
                    close_col = col
                    break
            if close_col:
                price = float(last[close_col])
                date_col = next((c for c in df.columns if "日期" in str(c) or "date" in str(c).lower()), None)
                date_str = str(last[date_col])[:10] if date_col else "未知"
                if price > 0:
                    return price, date_str
    except Exception as e:
        print(f"  [spot_hist_sge] 失败: {e}")
    return None, None

def fetch_latest_index(code):
    """指数最新收盘价（带备选接口）"""
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=15)).strftime("%Y%m%d")
    
    # 主接口
    try:
        df = ak.index_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end)
        print(f"  [index_zh_a_hist] 共 {len(df)} 行")
        if len(df) > 0:
            last = df.iloc[-1]
            for col in ["收盘", "收盘价", "close", "Close"]:
                if col in df.columns:
                    price = float(last[col])
                    if price > 0:
                        date_str = str(last.get("日期", last.get("date", "")))[:10]
                        return price, date_str
    except Exception as e:
        print(f"  [index_zh_a_hist] 失败: {e}")
    
    # 备选接口
    try:
        prefix = "sh" if code.startswith("000") else "sz"
        df = ak.stock_zh_index_daily(symbol=f"{prefix}{code}")
        print(f"  [stock_zh_index_daily] 共 {len(df)} 行")
        if len(df) > 0:
            last = df.iloc[-1]
            for col in ["close", "收盘"]:
                if col in df.columns:
                    price = float(last[col])
                    if price > 0:
                        date_str = str(last.get("date", ""))[:10]
                        return price, date_str
    except Exception as e:
        print(f"  [stock_zh_index_daily] 失败: {e}")
    
    return None, None

def fetch_latest_futures(code):
    """期货最新收盘价"""
    try:
        df = ak.futures_zh_daily_sina(symbol=code)
        print(f"  [futures_zh_daily_sina] 共 {len(df)} 行")
        if len(df) > 0:
            last = df.iloc[-1]
            for col in ["close", "收盘"]:
                if col in df.columns:
                    price = float(last[col])
                    if price > 0:
                        date_str = str(last.get("date", ""))[:10]
                        return price, date_str
    except Exception as e:
        print(f"  [futures_zh_daily_sina] 失败: {e}")
    return None, None

def fetch_initial_price(code, start_date):
    """获取指定日期的历史价格（用于期初价）"""
    start_dt = datetime.strptime(start_date[:10], "%Y-%m-%d")
    s = (start_dt - timedelta(days=5)).strftime("%Y%m%d")
    e = (start_dt + timedelta(days=5)).strftime("%Y%m%d")
    
    # 判断标的类型
    if code == "AU9999":
        try:
            df = ak.spot_hist_sge(symbol="Au99.99")
            price, actual_date = find_close_by_date(df, start_date)
            if price:
                return price, actual_date
        except Exception as e:
            print(f"  [期初 spot_hist_sge] 失败: {e}")
    elif code.startswith("000") or code.startswith("399"):
        # 指数
        try:
            df = ak.index_zh_a_hist(symbol=code, period="daily", start_date=s, end_date=e)
            price, actual_date = find_close_by_date(df, start_date)
            if price:
                return price, actual_date
        except Exception as e:
            print(f"  [期初 index_zh_a_hist] 失败: {e}")
        
        # 备选
        try:
            prefix = "sh" if code.startswith("000") else "sz"
            df = ak.stock_zh_index_daily(symbol=f"{prefix}{code}")
            price, actual_date = find_close_by_date(df, start_date)
            if price:
                return price, actual_date
        except Exception as e:
            print(f"  [期初 stock_zh_index_daily] 失败: {e}")
    else:
        # 期货
        try:
            df = ak.futures_zh_daily_sina(symbol=code)
            price, actual_date = find_close_by_date(df, start_date)
            if price:
                return price, actual_date
        except Exception as e:
            print(f"  [期初 futures_zh_daily_sina] 失败: {e}")
    
    return None, None

def refresh_current_prices(products_data):
    """刷新当前价格"""
    print("\n[1/2] 刷新当前价格...")
    underlyings = products_data.get("underlyings", {})
    prices = {}
    
    for name, info in underlyings.items():
        code = info.get("code")
        if not code:
            continue
        
        print(f"\n  [{name}] {code}")
        price, date_str = None, None
        
        if code == "AU9999":
            price, date_str = fetch_latest_sge_gold()
        elif code.startswith("000") or code.startswith("399"):
            price, date_str = fetch_latest_index(code)
        else:
            price, date_str = fetch_latest_futures(code)
        
        if price and price > 0:
            prices[code] = {
                "price": price,
                "date": date_str,
                "time": f"{date_str} 收盘"
            }
            print(f"  => {price} ({date_str})")
        else:
            print(f"  => 未获取到")
    
    output_path = os.path.join(SCRIPT_DIR, "prices.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    
    print(f"\n已写入 prices.json，共 {len(prices)} 个标的")
    return prices

def refresh_initial_prices(products_data):
    """刷新期初价格"""
    print("\n[2/2] 刷新期初价格...")
    products = products_data.get("products", [])
    underlyings = products_data.get("underlyings", {})
    
    # 加载已有的期初价格
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
        
        # 期初观察日在未来则跳过
        if start_date > datetime.now().strftime("%Y-%m-%d"):
            print(f"\n  [{code}] 期初观察日 {start_date} 未到，跳过")
            continue
        
        # 已有期初价则跳过
        if code in initial_prices:
            print(f"\n  [{code}] 已有期初价，跳过")
            continue
        
        # 获取标的代码
        underlying_info = underlyings.get(underlying, {})
        underlying_code = underlying_info.get("code")
        if not underlying_code:
            print(f"\n  [{code}] 标的'{underlying}'未配置代码，跳过")
            continue
        
        print(f"\n  [{code}] {underlying} 期初日: {start_date}")
        price, actual_date = fetch_initial_price(underlying_code, start_date)
        
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
    
    # 刷新当前价格（每日执行）
    refresh_current_prices(products_data)
    
    # 刷新期初价格（手动触发时自动跳过已有数据的产品）
    refresh_initial_prices(products_data)
    
    print("\n完成!")

if __name__ == "__main__":
    main()
