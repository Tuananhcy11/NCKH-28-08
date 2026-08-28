# -*- coding: utf-8 -*-
"""BUOC 1 - Thu thap song song ba luong du lieu:
   (A) XAU/USD  M15 / H1 / D1
   (B) PAXG/USDT tren Binance
   (C) Luong tin GDELT loc theo tu khoa vang - vi mo - dia chinh tri
"""
import time, json
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import requests, numpy as np, pandas as pd
from common import *

S = requests.Session(); S.headers.update({"User-Agent": UA})

# ---------------------------------------------------------------- A. XAU/USD
YF = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
XAU_SYMBOL = "GC=F"          # hop dong vang COMEX - dai dien XAU/USD 24/5
XAU_XCHECK = "GLD"           # ETF vang - dung de kiem chung chat luong

def yahoo(sym, interval, period1=None, period2=None, rng=None):
    p = {"interval": interval, "includePrePost": "false", "events": "div,split"}
    if rng: p["range"] = rng
    else:   p.update({"period1": int(period1), "period2": int(period2)})
    for k in range(6):
        r = S.get(YF.format(sym=sym), params=p, timeout=30)
        if r.status_code == 200: break
        time.sleep(3 * (k + 1))
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({
        "time":  pd.to_datetime(res["timestamp"], unit="s", utc=True),
        "open":  q["open"], "high": q["high"], "low": q["low"],
        "close": q["close"], "volume": q.get("volume"),
    }).dropna(subset=["close"]).reset_index(drop=True)
    return df

def collect_xau():
    out = {}
    p1 = int(pd.Timestamp(START, tz="UTC").timestamp())
    p2 = int(pd.Timestamp(END, tz="UTC").timestamp()) + 86400
    log("A. XAU/USD (%s) D1 %s..%s" % (XAU_SYMBOL, START, END))
    out["D1"] = yahoo(XAU_SYMBOL, "1d", p1, p2)
    log("A. XAU/USD H1 (cua so toi da nha cung cap cho phep: 730 ngay)")
    out["H1"] = yahoo(XAU_SYMBOL, "1h", rng="730d")
    log("A. XAU/USD M15 (cua so toi da: 60 ngay)")
    out["M15"] = yahoo(XAU_SYMBOL, "15m", rng="60d")
    for tf, df in out.items():
        save(df, os.path.join(RAW, "xau_%s.csv" % tf))
    xc = yahoo(XAU_XCHECK, "1d", p1, p2)
    save(xc, os.path.join(RAW, "xau_crosscheck_GLD_D1.csv"))
    return out

# ------------------------------------------------------------- B. PAXG/USDT
BN = "https://api.binance.com/api/v3/klines"
BN_TF = {"D1": "1d", "H1": "1h", "M15": "15m"}

def binance(symbol, interval, start_ms, end_ms):
    rows, cur = [], start_ms
    while cur < end_ms:
        for k in range(6):
            r = S.get(BN, params={"symbol": symbol, "interval": interval,
                                  "startTime": cur, "endTime": end_ms, "limit": 1000}, timeout=30)
            if r.status_code == 200: break
            time.sleep(2 * (k + 1))
        r.raise_for_status()
        b = r.json()
        if not b: break
        rows += b
        nxt = b[-1][0] + 1
        if nxt <= cur: break
        cur = nxt
        if len(b) < 1000: break
        time.sleep(0.12)
    df = pd.DataFrame(rows, columns=["ot","open","high","low","close","volume","ct","qv","n","tb","tq","ig"])
    df["time"] = pd.to_datetime(df["ot"], unit="ms", utc=True)
    df = df[["time","open","high","low","close","volume","n"]].astype(
        {"open":float,"high":float,"low":float,"close":float,"volume":float,"n":int})
    return df.drop_duplicates("time").reset_index(drop=True)

def collect_paxg():
    s = int(pd.Timestamp("2019-01-01", tz="UTC").timestamp() * 1000)
    e = int(pd.Timestamp(NOW, tz="UTC").timestamp() * 1000) + 86400000
    out = {}
    for tf, iv in BN_TF.items():
        log("B. PAXG/USDT %s" % tf)
        out[tf] = binance("PAXGUSDT", iv, s, e)
        save(out[tf], os.path.join(RAW, "paxg_%s.csv" % tf))
    return out

# --------------------------------------------- B'. Ty gia USDT/USD (oracle)
CB = "https://api.exchange.coinbase.com/products/{p}/candles"

def coinbase(product, gran, start, end):
    rows, cur = [], pd.Timestamp(start, tz="UTC")
    end = pd.Timestamp(end, tz="UTC")
    step = pd.Timedelta(seconds=gran * 290)
    while cur < end:
        nxt = min(cur + step, end)
        for k in range(6):
            r = S.get(CB.format(p=product), params={"granularity": gran,
                      "start": cur.isoformat(), "end": nxt.isoformat()}, timeout=30)
            if r.status_code == 200: break
            time.sleep(2 * (k + 1))
        if r.status_code == 200:
            rows += r.json()
        cur = nxt
        time.sleep(0.25)
    df = pd.DataFrame(rows, columns=["ts","low","high","open","close","volume"])
    df["time"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df[["time","open","high","low","close","volume"]].drop_duplicates("time").sort_values("time").reset_index(drop=True)

def collect_usdt():
    log("B'. USDT/USD tu Coinbase (oracle doc lap voi Binance) - D1")
    d1 = coinbase("USDT-USD", 86400, "2019-01-01", END)
    save(d1, os.path.join(RAW, "usdtusd_D1.csv"))
    log("B'. USDT/USD - H1 (2019 -> nay)")
    h1 = coinbase("USDT-USD", 3600, "2019-01-01", NOW)
    save(h1, os.path.join(RAW, "usdtusd_H1.csv"))
    return d1, h1

# ------------------------------------------------------------------ C. GDELT
GD = "https://api.gdeltproject.org/api/v2/doc/doc"
THEMES = {
    "gold":        '("gold price" OR "gold prices" OR bullion OR "spot gold" OR "gold market")',
    "macro":       '("Federal Reserve" OR "interest rate" OR inflation OR "CPI report" OR "monetary policy")',
    "geopolitics": '(war OR sanctions OR "geopolitical risk" OR conflict OR "military strike")',
}

def gdelt_series(query, mode, y0, y1):
    frames = []
    for y in range(y0, y1 + 1):
        p = {"query": query + " sourcelang:english", "mode": mode, "format": "json",
             "startdatetime": "%d0101000000" % y,
             "enddatetime": "%d0101000000" % (y + 1),
             "timelinesmooth": "0"}
        ok = None
        for k in range(5):
            try:
                r = S.get(GD, params=p, timeout=60)
                if r.status_code == 200 and r.text.lstrip().startswith("{"):
                    ok = r.json(); break
            except Exception as ex:
                log("   gdelt loi:", ex)
            time.sleep(6 + 4 * k)
        time.sleep(6)
        if not ok or not ok.get("timeline"):
            log("   ! khong co du lieu %s %s %d" % (mode, query[:18], y)); continue
        d = pd.DataFrame(ok["timeline"][0]["data"])
        d["time"] = pd.to_datetime(d["date"], utc=True)
        frames.append(d[["time", "value"]])
        log("   %s %d: %d diem" % (mode, y, len(d)))
    if not frames:
        return pd.DataFrame(columns=["time", "value"])
    return pd.concat(frames).drop_duplicates("time").sort_values("time").reset_index(drop=True)

def collect_gdelt():
    y0, y1 = 2017, pd.Timestamp(END).year      # GDELT DOC 2.0 phu tu 2017
    for name, q in THEMES.items():
        for mode, tag in (("timelinevol", "vol"), ("timelinetone", "tone")):
            log("C. GDELT %s / %s" % (name, tag))
            df = gdelt_series(q, mode, y0, y1)
            df = df.rename(columns={"value": "%s_%s" % (name, tag)})
            save(df, os.path.join(RAW, "gdelt_%s_%s.csv" % (name, tag)))

if __name__ == "__main__":
    t0 = time.time()
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "xau"):   collect_xau()
    if what in ("all", "paxg"):  collect_paxg()
    if what in ("all", "usdt"):  collect_usdt()
    if what in ("all", "gdelt"): collect_gdelt()
    log("BUOC 1 hoan tat sau %.1f phut" % ((time.time() - t0) / 60))
