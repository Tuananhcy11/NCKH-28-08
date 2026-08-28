# -*- coding: utf-8 -*-
"""BUOC 1 (bo sung) - Thu thap XAU/USD noi phien (M15 / H1) cho ca giai doan 2015-2025.

   Cac nguon mien phi khong co API key deu gioi han cung:
     Yahoo Finance : H1 toi da 730 ngay, M15 toi da 60 ngay
     Dukascopy / HistData / Stooq : khong truy cap duoc tu moi truong nay
   Vi vay module nay dung nha cung cap co API key. Dat bien moi truong roi chay:

       set TWELVEDATA_API_KEY=xxxxx     (hoac)   set POLYGON_API_KEY=xxxxx
       python src/step01d_xau_intraday.py

   Script tu dong chon nha cung cap theo key co san, tai theo lat cat thoi gian,
   ghep lai, khu trung lap va ghi de data/raw/xau_{H1,M15}.csv.
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

TD_KEY  = os.environ.get("TWELVEDATA_API_KEY", "").strip()
PG_KEY  = os.environ.get("POLYGON_API_KEY", "").strip()

TD_TF = {"H1": "1h", "M15": "15min"}
PG_TF = {"H1": (1, "hour"), "M15": (15, "minute")}

# ------------------------------------------------------------------ Twelve Data
def twelvedata(tf, start, end):
    """Tai theo lat 5000 nen moi lan, lui dan ve qua khu."""
    out, moc_cuoi = [], pd.Timestamp(end, tz="UTC")
    moc_dau = pd.Timestamp(start, tz="UTC")
    while moc_cuoi > moc_dau:
        p = {"symbol": "XAU/USD", "interval": TD_TF[tf], "outputsize": 5000,
             "start_date": moc_dau.strftime("%Y-%m-%d %H:%M:%S"),
             "end_date":   moc_cuoi.strftime("%Y-%m-%d %H:%M:%S"),
             "timezone": "UTC", "order": "ASC", "apikey": TD_KEY}
        r = S.get("https://api.twelvedata.com/time_series", params=p, timeout=60)
        j = r.json()
        if j.get("status") == "error" or "values" not in j:
            log("   Twelve Data tra loi: %s" % str(j)[:200]); break
        v = pd.DataFrame(j["values"])
        if v.empty:
            break
        v["time"] = pd.to_datetime(v["datetime"], utc=True)
        out.append(v)
        moc_moi = v["time"].min() - pd.Timedelta(seconds=1)
        log("   %s: %d nen, som nhat %s" % (tf, len(v), str(v["time"].min())[:16]))
        if moc_moi >= moc_cuoi:
            break
        moc_cuoi = moc_moi
        time.sleep(8)                       # goi mien phi: 8 request moi phut
    if not out:
        return pd.DataFrame()
    d = pd.concat(out, ignore_index=True)
    for c in ("open", "high", "low", "close"):
        d[c] = d[c].astype(float)
    d["volume"] = d["volume"].astype(float) if "volume" in d else 0.0
    return d[["time", "open", "high", "low", "close", "volume"]]

# ---------------------------------------------------------------------- Polygon
def polygon(tf, start, end):
    """Polygon gioi han 50 000 nen moi lan -> chia theo tung nam."""
    mult, span = PG_TF[tf]
    out = []
    for nam in range(pd.Timestamp(start).year, pd.Timestamp(end).year + 1):
        u = ("https://api.polygon.io/v2/aggs/ticker/C:XAUUSD/range/%d/%s/%d-01-01/%d-12-31"
             % (mult, span, nam, nam))
        cur = u
        while cur:
            r = S.get(cur, params={"limit": 50000, "sort": "asc", "apiKey": PG_KEY}, timeout=90)
            if r.status_code != 200:
                log("   Polygon %d tra ma %s: %s" % (nam, r.status_code, r.text[:160])); break
            j = r.json()
            if j.get("results"):
                out.append(pd.DataFrame(j["results"]))
                log("   %s %d: +%d nen" % (tf, nam, len(j["results"])))
            cur = j.get("next_url")
            time.sleep(13)                  # goi mien phi: 5 request moi phut
    if not out:
        return pd.DataFrame()
    d = pd.concat(out, ignore_index=True)
    d["time"] = pd.to_datetime(d["t"], unit="ms", utc=True)
    d = d.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
    return d[["time", "open", "high", "low", "close", "volume"]]

# ------------------------------------------------------------------------ chay
def run():
    if TD_KEY:
        nguon, ham = "Twelve Data", twelvedata
    elif PG_KEY:
        nguon, ham = "Polygon", polygon
    else:
        print(__doc__)
        log("! Chua co API key. Dat TWELVEDATA_API_KEY hoac POLYGON_API_KEY roi chay lai.")
        return
    log("Nguon XAU/USD noi phien: %s" % nguon)
    for tf in ("H1", "M15"):
        d = ham(tf, START, END)
        if d.empty:
            log("! %s: khong tai duoc" % tf); continue
        f = os.path.join(RAW, "xau_%s.csv" % tf)
        if os.path.exists(f):
            cu = load(f)
            d = pd.concat([d, cu[~cu["time"].isin(d["time"])]])
            os.replace(f, f.replace(".csv", "_yahoo_backup.csv"))
        d = d.drop_duplicates("time").sort_values("time").reset_index(drop=True)
        save(d, f)
        log("   %s: %s -> %s" % (tf, str(d["time"].min())[:10], str(d["time"].max())[:10]))

if __name__ == "__main__":
    run()
