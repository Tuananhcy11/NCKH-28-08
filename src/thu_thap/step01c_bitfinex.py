# -*- coding: utf-8 -*-
"""BUOC 1 (bo sung) - Mo rong lich su bang nguon Bitfinex.

   Muc dich: lay hai chuoi tu MOT nguon duy nhat, khong ghep nhieu san.
     - USDT/USD  (ky hieu tUSTUSD)  : Bitfinex co tu 2018-11, phu tron giai doan
                                      co PAXG (tu 2020-08). Dung rieng nguon nay,
                                      khong tron voi Coinbase.
     - XAUT/USD  (Tether Gold)      : vang token 24/7 thu hai, co tu 2020-01,
                                      som hon PAXG tren Binance (2020-08) - dung lam
                                      chuoi neo bo sung va kiem chung cheo cho Buoc 3-5.
"""
import os, time
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import requests, pandas as pd
from common import *

S = requests.Session(); S.headers.update({"User-Agent": UA})
BF = "https://api-pub.bitfinex.com/v2/candles/trade:{tf}:{sym}/hist"
TF_BF = {"D1": "1D", "H1": "1h", "M15": "15m"}
LIMIT = 10000

def bitfinex(sym, tf, start, end):
    """Tai toan bo nen trong khoang [start, end], phan trang tien theo thoi gian."""
    rows, cur = [], int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    end_ms = int(pd.Timestamp(end, tz="UTC").timestamp() * 1000)
    while cur < end_ms:
        for k in range(6):
            r = S.get(BF.format(tf=TF_BF[tf], sym=sym),
                      params={"start": cur, "end": end_ms, "limit": LIMIT, "sort": 1}, timeout=40)
            if r.status_code == 200:
                break
            log("   bi tu choi (%s), cho %ds" % (r.status_code, 5 * (k + 1)))
            time.sleep(5 * (k + 1))
        if r.status_code != 200:
            break
        b = r.json()
        if not b:
            break
        rows += b
        nxt = b[-1][0] + 1
        if nxt <= cur:
            break
        cur = nxt
        time.sleep(1.6)                      # Bitfinex gioi han ~30 req/phut
        if len(b) < LIMIT:
            break
    if not rows:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
    d = pd.DataFrame(rows, columns=["ts", "open", "close", "high", "low", "volume"])
    d["time"] = pd.to_datetime(d["ts"], unit="ms", utc=True)
    return (d[["time", "open", "high", "low", "close", "volume"]]
            .drop_duplicates("time").sort_values("time").reset_index(drop=True))

def run():
    # ---- USDT/USD: chi mot nguon Bitfinex, ghi de hoan toan
    for tf in ("D1", "H1"):
        log("USDT/USD %s tu Bitfinex (nguon duy nhat)" % tf)
        d = bitfinex("tUSTUSD", tf, "2015-01-01", NOW)
        if d.empty:
            log("   ! khong lay duoc, giu nguyen"); continue
        log("   %d moc, %s -> %s" % (len(d), str(d["time"].min())[:10], str(d["time"].max())[:10]))
        save(d, os.path.join(RAW, "usdtusd_%s.csv" % tf))

    # ---- XAUT/USD: chuoi vang token 24/7 bo sung
    for tf in TFS:
        log("XAUT/USD %s tu Bitfinex" % tf)
        d = bitfinex("tXAUT:USD", tf, "2019-01-01", NOW)
        if d.empty:
            log("   ! khong co du lieu"); continue
        save(d, os.path.join(RAW, "xaut_%s.csv" % tf))

if __name__ == "__main__":
    run()
