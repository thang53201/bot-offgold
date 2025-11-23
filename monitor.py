import requests
from datetime import datetime, timedelta

GVZ_THRESHOLD = 25.0
GVZ_DAY_PCT = 0.10
VIX_THRESHOLD = 30.0
VIX_DAY_PCT = 0.08
YIELD_THRESHOLD = 0.25  # 0.25 điểm
SPDR_TON_THRESHOLD = 5.0

def get_json(url, headers=None):
    try:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        return r.json()
    except:
        return None

def fetch_price_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    data = get_json(url)
    if not data:
        return None
    try:
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        return float(price) if price is not None else None
    except:
        return None

def fetch_vix():
    return fetch_price_yahoo("%5EVIX")

def fetch_gvz():
    return fetch_price_yahoo("%5EGVZ")

def fetch_10y():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX"
    data = get_json(url)
    if not data:
        return None
    try:
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        return float(price) / 10.0
    except:
        return None

def fetch_spdr_holdings():
    url = "https://www.ssga.com/library-content/products/fund-docs/etfs/us/holdings/ssga-spdr-gld-holdings.json"
    data = get_json(url)
    if not data:
        url2 = "https://api.spdrgoldshares.com/info/holdings"
        return get_json(url2)
    return data

def parse_spdr_tons(data):
    try:
        if isinstance(data, dict):
            for key in ("total_ounces", "totalOunces", "total_ounces_held"):
                if key in data:
                    ounces = float(data[key])
                    tonnes = (ounces * 31.1034768) / 1e6
                    return tonnes

            if "holdings" in data and isinstance(data["holdings"], dict):
                h = data["holdings"]
                for key in ("total_ounces", "totalOunces"):
                    if key in h:
                        ounces = float(h[key])
                        tonnes = (ounces * 31.1034768) / 1e6
                        return tonnes
        return None
    except:
        return None

def fetch_prev_close(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2d&interval=1d"
    data = get_json(url)
    if not data:
        return None, None
    try:
        res = data["chart"]["result"][0]
        closes = res["indicators"]["quote"][0]["close"]
        if len(closes) < 2:
            return (closes[-1] if closes else None), None
        return float(closes[1]), float(closes[0])
    except:
        return None, None

def build_alerts(last):
    alerts = []
    vix_today, vix_yesterday = fetch_prev_close("%5EVIX")
    if vix_today is not None:
        if vix_today > VIX_THRESHOLD:
            alerts.append(f"⚠️ VIX cao: {vix_today:.2f} (> {VIX_THRESHOLD})")
        if vix_yesterday and vix_yesterday > 0:
            pct = (vix_today - vix_yesterday) / vix_yesterday
            if abs(pct) >= VIX_DAY_PCT:
                alerts.append(f"⚠️ VIX biến động {pct*100:.1f}%: {vix_yesterday:.2f} → {vix_today:.2f}")

    gvz_today, gvz_yesterday = fetch_prev_close("%5EGVZ")
    if gvz_today is not None:
        if gvz_today > GVZ_THRESHOLD:
            alerts.append(f"⚠️ GVZ cao: {gvz_today:.2f} (> {GVZ_THRESHOLD})")
        if gvz_yesterday and gvz_yesterday > 0:
            pct = (gvz_today - gvz_yesterday) / gvz_yesterday
            if abs(pct) >= GVZ_DAY_PCT:
                alerts.append(f"⚠️ GVZ biến động {pct*100:.1f}%: {gvz_yesterday:.2f} → {gvz_today:.2f}")

    y10 = fetch_10y()
    if y10 is not None:
        if last.get("y10") is not None and abs(y10 - last["y10"]) >= YIELD_THRESHOLD:
            alerts.append(f"⚠️ US10Y biến động: {last['y10']:.2f}% → {y10:.2f}%")
        last["y10"] = y10

    spdr = fetch_spdr_holdings()
    tons = None
    if spdr:
        tons = parse_spdr_tons(spdr)
    if tons is not None:
        if last.get("spdr_tons") is not None:
            diff = tons - last["spdr_tons"]
            if diff >= SPDR_TON_THRESHOLD:
                alerts.append(f"⚠️ SPDR MUA mạnh: +{diff:.2f} tấn")
            if diff <= -SPDR_TON_THRESHOLD:
                alerts.append(f"⚠️ SPDR XẢ mạnh: {diff:.2f} tấn")
        last["spdr_tons"] = tons

    return alerts, last
