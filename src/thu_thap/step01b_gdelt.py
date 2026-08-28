# -*- coding: utf-8 -*-
"""BUOC 1 (phan C) - Luong tin GDELT, truy van gop toan giai doan.
   GDELT DOC 2.0 gioi han toc do rat chat, nen goi 1 request cho ca giai doan,
   gian cach rong va lui theo cap so nhan khi bi tu choi.
"""
import os, time
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import requests, pandas as pd
from common import *
from step01_collect import THEMES, GD

S = requests.Session(); S.headers.update({"User-Agent": UA})
GAP = 75

def fetch(query, mode, s="20170101000000", e=None):
    e = e or (pd.Timestamp(NOW).strftime("%Y%m%d") + "000000")
    p = {"query": query + " sourcelang:english", "mode": mode, "format": "json",
         "startdatetime": s, "enddatetime": e, "timelinesmooth": "0"}
    for k in range(20):
        try:
            r = S.get(GD, params=p, timeout=180)
            if r.status_code == 200 and r.text.lstrip().startswith("{"):
                j = r.json()
                if j.get("timeline"):
                    return pd.DataFrame(j["timeline"][0]["data"])
                log("   phan hoi rong"); 
            else:
                log("   bi tu choi (%s), lui %ds" % (r.status_code, GAP * (k + 1)))
        except Exception as ex:
            log("   loi:", ex)
        time.sleep(GAP * (k + 1))
    return None

def run():
    for name, q in THEMES.items():
        for mode, tag in (("timelinevol", "vol"), ("timelinetone", "tone")):
            out = os.path.join(RAW, "gdelt_%s_%s.csv" % (name, tag))
            if os.path.exists(out) and len(pd.read_csv(out)) > 500:
                log("C. GDELT %s/%s - da co, bo qua" % (name, tag)); continue
            log("C. GDELT %s / %s" % (name, tag))
            d = fetch(q, mode)
            if d is None:
                log("   ! that bai: %s/%s" % (name, tag)); continue
            d["time"] = pd.to_datetime(d["date"], utc=True)
            d = d[["time", "value"]].rename(columns={"value": "%s_%s" % (name, tag)})
            save(d, out)
            time.sleep(GAP)

if __name__ == "__main__":
    run()
