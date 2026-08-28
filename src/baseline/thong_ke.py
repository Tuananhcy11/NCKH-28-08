# -*- coding: utf-8 -*-
"""TANG 3 - Quan tri thoat lenh va thong ke tin hieu.

Diem mau chot: DO PHU TIN HIEU khac SO LENH THUC MO. Quy tac mot vi the tai
mot thoi diem khien moi tin hieu phat sinh khi dang co lenh mo deu bi bo qua.
Voi chien luoc dang TRANG THAI (Position), tin hieu duy tri lien tuc suot ca
xu huong nen chenh lech nay rat lon.
"""
import numpy as np
import pandas as pd

# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import indicators as ta


def mo_lenh_mot_vi_the(d, tin_hieu, he_so_atr_tp=2.0, he_so_atr_sl=1.5,
                       so_nen_toi_da=None):
    """Mo phong tuan tu voi quy tac MOT vi the tai mot thoi diem.

    Thoat lenh khi cham chot lai (he_so_atr_tp x ATR14), cham cat lo
    (he_so_atr_sl x ATR14), hoac het so nen toi da.

    Tra ve DataFrame cac lenh da mo.
    """
    c = d["close"].values
    h = d["high"].values
    l = d["low"].values
    atr = ta.atr(d["high"], d["low"], d["close"], 14).values
    s = np.asarray(tin_hieu).astype(float)
    n = len(c)
    if so_nen_toi_da is None:
        so_nen_toi_da = n

    lenh = []
    i = 0
    while i < n - 1:
        if not np.isfinite(s[i]) or s[i] == 0 or not np.isfinite(atr[i]) or atr[i] <= 0:
            i += 1
            continue
        huong = int(s[i])
        vao = c[i]
        tp = vao + huong * he_so_atr_tp * atr[i]
        sl = vao - huong * he_so_atr_sl * atr[i]
        ket = min(i + so_nen_toi_da, n - 1)
        ra, ly_do = c[ket], "het_han"
        for j in range(i + 1, ket + 1):
            if huong > 0:
                if l[j] <= sl:
                    ra, ket, ly_do = sl, j, "cat_lo"; break
                if h[j] >= tp:
                    ra, ket, ly_do = tp, j, "chot_lai"; break
            else:
                if h[j] >= sl:
                    ra, ket, ly_do = sl, j, "cat_lo"; break
                if l[j] <= tp:
                    ra, ket, ly_do = tp, j, "chot_lai"; break
        lenh.append(dict(vao_i=i, ra_i=ket, thoi_diem_vao=d.index[i],
                         thoi_diem_ra=d.index[ket], huong=huong,
                         gia_vao=vao, gia_ra=ra, ly_do_thoat=ly_do,
                         loi_nhuan_gia=huong * (ra - vao),
                         so_nen_giu=ket - i))
        i = ket + 1                      # <-- quy tac mot vi the
    return pd.DataFrame(lenh)


def thong_ke_tin_hieu(d, bo_tin_hieu, so_nen_toi_da=None):
    """Bang thong ke tin hieu va so lenh thuc mo cho tung chien luoc."""
    n = len(d)
    rows = []
    for ten, th in bo_tin_hieu.items():
        s = th["tin_hieu"]
        mua = int((s == 1).sum())
        ban = int((s == -1).sum())
        tho = th["tin_hieu_tho"]
        lenh = mo_lenh_mot_vi_the(d, s.values, so_nen_toi_da=so_nen_toi_da)
        rows.append(dict(
            chien_luoc=ten,
            tin_hieu_mua=mua, tin_hieu_ban=ban, tong_tin_hieu=mua + ban,
            do_phu_pct=round(100.0 * (mua + ban) / n, 2),
            so_lenh_thuc_mo=len(lenh),
            ty_le_loc_boi_bo_loc_pct=round(
                100.0 * (int((tho != 0).sum()) - (mua + ban)) / max(1, int((tho != 0).sum())), 2),
            trung_binh_nen_moi_tin_hieu=round(n / max(1, mua + ban), 1),
            ty_le_tin_hieu_thanh_lenh_pct=round(100.0 * len(lenh) / max(1, mua + ban), 2)))
    return pd.DataFrame(rows)


def phan_ra_swing_theo_che_do(th_swing):
    """Phan ra tin hieu Swing theo tung che do - bang kiem chung tang 1."""
    d = th_swing[th_swing["tin_hieu"] != 0]
    rows = []
    for cd in ["Uptrend", "Downtrend", "Sideway", "Transition"]:
        m = d[d["nhom"] == cd] if cd != "Transition" else d[d["nhom"] == ""]
        rows.append(dict(che_do=cd,
                         tin_hieu_mua=int((m["tin_hieu"] == 1).sum()),
                         tin_hieu_ban=int((m["tin_hieu"] == -1).sum())))
    t = pd.DataFrame(rows)
    t["tong"] = t["tin_hieu_mua"] + t["tin_hieu_ban"]
    return t
