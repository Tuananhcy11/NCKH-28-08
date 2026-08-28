# -*- coding: utf-8 -*-
"""BUOC 2 - Chuan hoa PAXG ve mat bang USD.
   P_PAXG_USD = P_PAXG_USDT x (USDT/USD),  ty gia USDT/USD lay tu Coinbase
   (san giao dich fiat doc lap voi Binance) nham khu sai lech neo gia.
"""
import os
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np, pandas as pd
from common import *

def peg(tf):
    """Chuoi ty gia USDT/USD theo khung thoi gian, ffill, mac dinh 1.0 khi thieu."""
    f = os.path.join(RAW, "usdtusd_%s.csv" % ("H1" if tf in ("H1", "M15") else "D1"))
    d = load(f)[["time", "close"]].rename(columns={"close": "usdtusd"})
    return d.sort_values("time")

def run():
    rep = []
    for tf in TFS:
        px = load(os.path.join(RAW, "paxg_%s.csv" % tf))
        pg = peg(tf)
        m = pd.merge_asof(px.sort_values("time"), pg, on="time",
                          direction="backward", tolerance=pd.Timedelta("3D"))
        cov = m["usdtusd"].notna().mean()
        m["usdtusd"] = m["usdtusd"].ffill().fillna(1.0)          # truoc khi co oracle: gia dinh neo = 1
        for c in ("open", "high", "low", "close"):
            m[c + "_usd"] = m[c] * m["usdtusd"]
        out = m[["time", "open_usd", "high_usd", "low_usd", "close_usd", "volume", "usdtusd"]]
        out.columns = ["time", "open", "high", "low", "close", "volume", "usdtusd"]
        out["logret"] = logret(out["close"])
        save(out, os.path.join(PROC, "paxg_usd_%s.csv" % tf))

        dev = (m["usdtusd"] - 1.0)
        rep.append({
            "khung": tf, "so_nen": len(out),
            "tu": str(out["time"].min())[:10], "den": str(out["time"].max())[:10],
            "phu_song_oracle": round(float(cov), 4),
            "lech_neo_tb_bp": round(float(dev.mean() * 1e4), 3),
            "lech_neo_do_lech_chuan_bp": round(float(dev.std() * 1e4), 3),
            "lech_neo_max_abs_bp": round(float(dev.abs().max() * 1e4), 3),
            "anh_huong_len_logret_bp": round(float(logret(m["usdtusd"]).std() * 1e4), 4),
        })
    r = pd.DataFrame(rep)
    save(r, os.path.join(TAB, "buoc02_chuan_hoa_paxg.csv"))
    print(r.to_string(index=False))

if __name__ == "__main__":
    run()
