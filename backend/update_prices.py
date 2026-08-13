#!/usr/bin/env python3
"""
每日收盘价刷新脚本（GitHub Actions 定时执行）
使用 akshare 获取各标的当日收盘价，写入 prices.json
"""
import json
import os
from datetime import datetime

try:
    import akshare as ak
except ImportError:
    print("Installing akshare...")
    os.system("pip install akshare")
    import akshare as ak

# 标的配置（根据实际产品标的调整）
UNDERLYINGS = {
    "AU9999": {"name": "黄金", "market": "sge"},
    "000852": {"name": "中证1000", "market": "cn_index"},
    "000905": {"name": "中证500", "market": "cn_index"},
    "000300": {"name": "沪深300", "market": "cn_index"},
}

def fetch_sge_gold():
    """SGE 黄金 AU9999 当日收盘价"""
    try:
        df = ak.spot_hist_sge(symbol="Au99.99")
        if len(df) > 0:
            last = df.iloc[-1]
            date_col = next((c for c in df.columns if "日期" in str(c)), None)
            close_col = next((c for c in df.columns if "收盘" in str(c).lower()), None)
            if date_col and close_col:
                price = float(last[close_col])
                date_str = str(last[date_col])[:10]
                return price, date_str
    except Exception as e:
        print(f"  [SGE] 失败: {e}")
    return None, None

def fetch_index(code):
    """A股指数当日收盘价"""
    try:
        df = ak.index_zh_a_hist(symbol=code, period="daily", 
                                 start_date=datetime.now().strftime("%Y%m%d"),
                                 end_date=datetime.now().strftime("%Y%m%d"))
        if len(df) > 0:
            last = df.iloc[-1]
            close_col = next((c for c in ["收盘", "收盘价", "close"] if c in df.columns), None)
            if close_col:
                price = float(last[close_col])
                date_str = str(last.get("日期", ""))[:10]
                return price, date_str
    except Exception as e:
        print(f"  [Index {code}] 失败: {e}")
    return None, None

def main():
    print("=" * 50)
    print(f"  每日收盘价刷新 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    prices = {}
    
    for code, info in UNDERLYINGS.items():
        print(f"\n  [{info['name']}] {code}")
        price, date_str = None, None
        
        if info["market"] == "sge":
            price, date_str = fetch_sge_gold()
        elif info["market"] == "cn_index":
            price, date_str = fetch_index(code)
        
        if price and price > 0:
            prices[code] = {
                "price": price,
                "date": date_str,
                "time": f"{date_str} 收盘"
            }
            print(f"  => {price} ({date_str})")
        else:
            print(f"  => 未获取到")
    
    # 写入 JSON
    output_path = os.path.join(os.path.dirname(__file__), "prices.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    
    print(f"\n已写入 {output_path}")
    print(f"共更新 {len(prices)} 个标的")

if __name__ == "__main__":
    main()
