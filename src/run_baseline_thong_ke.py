# -*- coding: utf-8 -*-
"""Sinh Bang 2.4 - Thong ke tin hieu vao lenh cua chien luoc Baseline ba tang.

    python src/run_baseline_thong_ke.py [khung...]      (mac dinh H1)
"""
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np
import pandas as pd
from common import RAW, TAB, log, save, load
from baseline.che_do import phan_dinh_che_do, thong_ke_che_do
from baseline.chien_luoc import sinh_tat_ca_tin_hieu
from baseline.thong_ke import thong_ke_tin_hieu, phan_ra_swing_theo_che_do


def chay(khung="H1"):
    log("=" * 68)
    log("CHIEN LUOC NEN BA TANG - khung %s" % khung)
    d = load(os.path.join(RAW, "xau_%s.csv" % khung)).sort_values("time")
    d = d.set_index("time")
    log("Tap du lieu: %d nen, %s -> %s"
        % (len(d), str(d.index.min())[:10], str(d.index.max())[:10]))

    # ---- tang 1
    d = phan_dinh_che_do(d)
    bang_cd = thong_ke_che_do(d)
    bang_cd.insert(0, "khung", khung)
    save(bang_cd, os.path.join(TAB, "baseline_che_do_%s.csv" % khung))
    log("Tang 1 - phan bo che do:")
    print(bang_cd.to_string(index=False))

    # ---- tang 2 + 3
    bo = sinh_tat_ca_tin_hieu(d)
    bang = thong_ke_tin_hieu(d, bo)
    bang.insert(0, "khung", khung)
    bang.insert(1, "so_nen", len(d))
    save(bang, os.path.join(TAB, "baseline_bang_2_4_%s.csv" % khung))
    log("Tang 2-3 - Bang 2.4:")
    print(bang.to_string(index=False))

    # ---- kiem chung tang 1 qua phan ra Swing
    pr = phan_ra_swing_theo_che_do(bo["Swing"])
    pr.insert(0, "khung", khung)
    save(pr, os.path.join(TAB, "baseline_swing_theo_che_do_%s.csv" % khung))
    log("Kiem chung tang 1 - phan ra tin hieu Swing theo che do:")
    print(pr.to_string(index=False))

    hop_le = (int(pr.loc[pr.che_do == "Uptrend", "tin_hieu_ban"].iloc[0]) == 0
              and int(pr.loc[pr.che_do == "Downtrend", "tin_hieu_mua"].iloc[0]) == 0
              and int(pr.loc[pr.che_do == "Transition", "tong"].iloc[0]) == 0)
    log("   -> tang phan dinh che do van hanh %s"
        % ("CHINH XAC" if hop_le else "SAI - can kiem tra lai"))

    # ---- luu tin hieu chi tiet
    chi_tiet = pd.DataFrame({"che_do": d["che_do"]})
    for ten, th in bo.items():
        chi_tiet[ten] = th["tin_hieu"]
    save(chi_tiet.reset_index(), os.path.join(TAB, "baseline_tin_hieu_%s.csv" % khung))
    return bang, bang_cd, pr


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or ["H1"]
    tong = [chay(k)[0] for k in args]
    if len(tong) > 1:
        save(pd.concat(tong, ignore_index=True),
             os.path.join(TAB, "baseline_bang_2_4_tong_hop.csv"))
