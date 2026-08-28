# -*- coding: utf-8 -*-
"""TANG 1 - Phan dinh che do thi truong.

Bon che do, phan dinh bang ADX14 va tuong quan vi tri cua EMA50 / EMA200:

    Uptrend     : ADX14 >= 25, EMA50 > EMA200, Close > EMA50
    Downtrend   : ADX14 >= 25, EMA50 < EMA200, Close < EMA50
    Sideway     : ADX14 <  25
    Transition  : ADX14 >= 25 nhung cau truc EMA va vi tri gia KHONG dong thuan
                  (vi du xu huong manh nhung gia dang cat nguoc lai EMA50, hoac
                  EMA50 va EMA200 vua giao nhau) - giai doan chuyen pha.

Nguong ADX = 25 la nguong PHAN DINH CHE DO. Rieng chien luoc Position dung
nguong cao hon (28) de chi tham gia xu huong that su manh - xem chien_luoc.py.
"""
import numpy as np
import pandas as pd

# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import indicators as ta

CHE_DO = ["Uptrend", "Downtrend", "Sideway", "Transition"]
NGUONG_ADX_CHE_DO = 25.0


def phan_dinh_che_do(df, nguong_adx=NGUONG_ADX_CHE_DO):
    """Tra ve DataFrame co them cot che_do va cac chi bao phuc vu phan dinh."""
    d = df.copy()
    c, h, l = d["close"], d["high"], d["low"]

    d["ema50"] = ta.ema(c, 50)
    d["ema200"] = ta.ema(c, 200)
    d["adx14"], d["pdi"], d["mdi"] = ta.adx(h, l, c, 14)

    manh = d["adx14"] >= nguong_adx
    len_ = (d["ema50"] > d["ema200"]) & (c > d["ema50"])
    xuong = (d["ema50"] < d["ema200"]) & (c < d["ema50"])

    d["che_do"] = np.where(~manh, "Sideway",
                           np.where(len_, "Uptrend",
                                    np.where(xuong, "Downtrend", "Transition")))
    # cac nen chua du du lieu tinh EMA200 thi khong phan dinh duoc
    d.loc[d["ema200"].isna() | d["adx14"].isna(), "che_do"] = np.nan
    return d


def thong_ke_che_do(d):
    """Bang phan bo che do - dung de kiem chung tang 1 hoat dong dung."""
    t = d["che_do"].value_counts(dropna=False).rename_axis("che_do").reset_index(name="so_nen")
    t["ty_le_pct"] = (100 * t["so_nen"] / len(d)).round(2)
    t["adx_trung_binh"] = [round(float(d.loc[d["che_do"] == r, "adx14"].mean()), 2)
                           if isinstance(r, str) else np.nan for r in t["che_do"]]
    return t.sort_values("so_nen", ascending=False).reset_index(drop=True)
