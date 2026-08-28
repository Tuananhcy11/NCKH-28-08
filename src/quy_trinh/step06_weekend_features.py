# -*- coding: utf-8 -*-
"""BUOC 6 - Chuoi 24/7 KHONG dung de sinh lenh.
   No duoc nen thanh BA dac trung gan vao cay nen mo phien thu Hai cua chuoi 24/5:
     (1) bien_dong_cuoi_tuan   - bien dong cuoi tuan uoc luong
     (2) lech_tich_luy         - do lech tich luy PAXG - XAU
     (3) diem_tam_ly_cuoi_tuan - diem tam ly cuoi tuan
   Moi giao dich va moi chi tieu hieu suat ve sau deu tinh tren chuoi 24/5 goc.
"""
import os
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np, pandas as pd
from common import *

def nhom_cuoi_tuan(ref):
    """Danh so tung khoang cuoi tuan lien tuc."""
    w = ref["cuoi_tuan"].values.astype(bool)
    gid = np.where(w, np.cumsum(~w), -1)
    ref = ref.copy(); ref["gid"] = gid
    return ref[w]

def run():
    bang = []
    for tf in TFS:
        ref = load(os.path.join(PROC, "chuoi_247_%s.csv" % tf))
        xau = load(os.path.join(RAW, "xau_%s.csv" % tf))
        w = nhom_cuoi_tuan(ref)
        if w.empty:
            log("  ! %s khong co khoang cuoi tuan" % tf); continue

        g = w.groupby("gid")
        f = pd.DataFrame({
            "ket_thuc":               g["time"].max(),
            "so_moc":                 g["time"].size(),
            # (1) bien dong cuoi tuan uoc luong = can bac hai tong binh phuong r_hat
            "bien_dong_cuoi_tuan":    np.sqrt(g["r_hat"].apply(lambda s: float((s ** 2).sum()))),
            # (2) do lech tich luy PAXG - XAU uoc luong trong ky nghi
            "lech_tich_luy":          g["r_paxg"].sum() - g["r_hat"].sum(),
            # (3) diem tam ly cuoi tuan (GDELT/FinBERT)
            "diem_tam_ly_cuoi_tuan":  g["S"].mean(),
            # phu tro: loi suat tham chieu tich luy va cuong do tin tuc
            "loi_suat_247_cuoi_tuan": g["r_hat"].sum(),
            "cuong_do_tin_tuc":       g["I"].mean(),
        }).reset_index(drop=True)
        f = f[f["so_moc"] >= (1 if tf == "D1" else 4)]

        # gan vao cay nen mo phien dau tuan ke tiep cua chuoi 24/5
        xau = xau.sort_values("time")
        f = f.sort_values("ket_thuc")
        g2 = pd.merge_asof(f, xau[["time"]].assign(nen_mo_phien=xau["time"]),
                           left_on="ket_thuc", right_on="time", direction="forward",
                           tolerance=pd.Timedelta("4D")).dropna(subset=["nen_mo_phien"])
        out = g2[["nen_mo_phien", "ket_thuc", "bien_dong_cuoi_tuan", "lech_tich_luy",
                  "diem_tam_ly_cuoi_tuan", "loi_suat_247_cuoi_tuan", "cuong_do_tin_tuc", "so_moc"]]
        out = out.rename(columns={"nen_mo_phien": "time"}).drop_duplicates("time", keep="last")
        save(out, os.path.join(PROC, "dac_trung_cuoi_tuan_%s.csv" % tf))
        bang.append(dict(khung=tf, so_ky_cuoi_tuan=len(out),
                         tu=str(out["time"].min())[:10], den=str(out["time"].max())[:10],
                         bien_dong_tb_bp=round(float(out["bien_dong_cuoi_tuan"].mean() * 1e4), 1),
                         lech_tb_bp=round(float(out["lech_tich_luy"].mean() * 1e4), 1),
                         lech_do_lech_chuan_bp=round(float(out["lech_tich_luy"].std() * 1e4), 1),
                         tam_ly_tb=round(float(out["diem_tam_ly_cuoi_tuan"].mean()), 4)))
    b = pd.DataFrame(bang)
    save(b, os.path.join(TAB, "buoc06_dac_trung_cuoi_tuan.csv"))
    print(b.to_string(index=False))

if __name__ == "__main__":
    run()
