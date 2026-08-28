# -*- coding: utf-8 -*-
"""TANG 2 - Luat vao lenh cua ba chien luoc nen.

Quy uoc tin hieu:  +1 = MUA,  -1 = BAN,  0 = dung ngoai.

Moi ham tra ve DataFrame co cac cot:
    tin_hieu      : +1 / -1 / 0 sau khi da ap bo loc rui ro
    tin_hieu_tho  : +1 / -1 / 0 truoc khi ap bo loc (de do tac dong cua bo loc)
    ly_do         : chuoi mo ta dieu kien kich hoat, phuc vu kiem chung
"""
import numpy as np
import pandas as pd

# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import indicators as ta

CHIEN_LUOC = ["Scalping", "Swing", "Position"]

# Bo loc rui ro cuoi tuan: huy tin hieu tu gio nay tro di vao thu Sau (UTC)
GIO_CHAN_SCALPING = 18
GIO_CHAN_SWING = 20
THU_SAU = 4                       # Monday=0 ... Friday=4

NGUONG_ADX_POSITION = 28.0        # cao hon nguong phan dinh che do (25)


# --------------------------------------------------------------- tien ich
def _bo_loc_cuoi_tuan(idx, gio_chan):
    """True = duoc phep vao lenh. Huy tin hieu tu gio_chan:00 UTC thu Sau."""
    if gio_chan is None:
        return pd.Series(True, index=idx)
    la_thu_sau = idx.dayofweek == THU_SAU
    qua_gio = idx.hour >= gio_chan
    return pd.Series(~(la_thu_sau & qua_gio), index=idx)


def _dong_goi(idx, mua, ban, gio_chan, ten_mua="MUA", ten_ban="BAN"):
    tho = np.where(mua, 1, np.where(ban, -1, 0))
    cho_phep = _bo_loc_cuoi_tuan(idx, gio_chan).values
    out = pd.DataFrame(index=idx)
    out["tin_hieu_tho"] = tho
    out["tin_hieu"] = np.where(cho_phep, tho, 0)
    out["ly_do"] = np.where(out["tin_hieu"] == 1, ten_mua,
                            np.where(out["tin_hieu"] == -1, ten_ban, ""))
    return out


# ------------------------------------------------------- a) Scalping
def tin_hieu_scalping(d):
    """EMA8, EMA21, RSI7. Cho phep giao dich trong che do Uptrend/Sideway (MUA)
    va Downtrend/Sideway (BAN).

    MUA khi dong thoi:
        (1) che_do thuoc {Uptrend, Sideway}
        (2) Close > EMA8 > EMA21
        (3) RSI7 < 65 va RSI7_t >= RSI7_{t-1}
    BAN doi xung:
        (1) che_do thuoc {Downtrend, Sideway}
        (2) Close < EMA8 < EMA21
        (3) RSI7 > 35 va RSI7_t <= RSI7_{t-1}
    Bo loc: huy tin hieu tu 18:00 UTC thu Sau.
    """
    c = d["close"]
    ema8, ema21 = ta.ema(c, 8), ta.ema(c, 21)
    rsi7 = ta.rsi(c, 7)
    rsi7_truoc = rsi7.shift(1)

    mua = (d["che_do"].isin(["Uptrend", "Sideway"])
           & (c > ema8) & (ema8 > ema21)
           & (rsi7 < 65) & (rsi7 >= rsi7_truoc))
    ban = (d["che_do"].isin(["Downtrend", "Sideway"])
           & (c < ema8) & (ema8 < ema21)
           & (rsi7 > 35) & (rsi7 <= rsi7_truoc))
    mua, ban = mua.fillna(False), ban.fillna(False)
    return _dong_goi(d.index, mua, ban, GIO_CHAN_SCALPING)


# ---------------------------------------------------------- b) Swing
def tin_hieu_swing(d):
    """EMA Ribbon, MACD(12,26,9), RSI14, Bollinger Bands - phan tang theo che do.

    Uptrend    : chi MUA  - EMA10 > EMA20 > EMA50 va MACD Hist CAT LEN muc 0
    Downtrend  : chi BAN  - EMA10 < EMA20 < EMA50 va MACD Hist CAT XUONG muc 0
    Sideway    : hoi quy trung binh nguoc chieu
                 MUA khi Close <= dai Bollinger duoi va RSI14 < 30
                 BAN khi Close >= dai Bollinger tren va RSI14 > 70
    Transition : dung ngoai hoan toan
    Bo loc: huy tin hieu tu 20:00 UTC thu Sau.

    Luu y: dieu kien MACD cat muc 0 la dieu kien dang SU KIEN (chi dung tai
    dung mot nen trong moi chu ky dong luong), khong phai dang TRANG THAI.
    """
    c = d["close"]
    ema10, ema20, ema50 = ta.ema(c, 10), ta.ema(c, 20), ta.ema(c, 50)
    _, _, hist = ta.macd(c, 12, 26, 9)
    hist_truoc = hist.shift(1)
    rsi14 = ta.rsi(c, 14)
    bb_tren, _, bb_duoi, _ = ta.bollinger(c, 20, 2)

    cat_len = (hist_truoc <= 0) & (hist > 0)
    cat_xuong = (hist_truoc >= 0) & (hist < 0)

    up = d["che_do"] == "Uptrend"
    down = d["che_do"] == "Downtrend"
    side = d["che_do"] == "Sideway"

    mua = ((up & (ema10 > ema20) & (ema20 > ema50) & cat_len)
           | (side & (c <= bb_duoi) & (rsi14 < 30)))
    ban = ((down & (ema10 < ema20) & (ema20 < ema50) & cat_xuong)
           | (side & (c >= bb_tren) & (rsi14 > 70)))
    mua, ban = mua.fillna(False), ban.fillna(False)

    out = _dong_goi(d.index, mua, ban, GIO_CHAN_SWING)
    # nhan phu de phan ra tin hieu theo che do (phuc vu kiem chung tang 1)
    out["nhom"] = np.where(up & (out["tin_hieu"] != 0), "Uptrend",
                           np.where(down & (out["tin_hieu"] != 0), "Downtrend",
                                    np.where(side & (out["tin_hieu"] != 0), "Sideway", "")))
    return out


# ------------------------------------------------------- c) Position
def tin_hieu_position(d):
    """EMA50, EMA200, ADX14 - luat don gian nhat, co y giu don gian lam moc.

    MUA : Close > EMA50 > EMA200 va ADX14 >= 28
    BAN : Close < EMA50 < EMA200 va ADX14 >= 28
    Khong ap bo loc cuoi tuan vi ban chat chien luoc la giu lenh nhieu tuan.
    """
    c = d["close"]
    ema50 = d["ema50"] if "ema50" in d else ta.ema(c, 50)
    ema200 = d["ema200"] if "ema200" in d else ta.ema(c, 200)
    adx14 = d["adx14"] if "adx14" in d else ta.adx(d["high"], d["low"], c, 14)[0]

    manh = adx14 >= NGUONG_ADX_POSITION
    mua = ((c > ema50) & (ema50 > ema200) & manh).fillna(False)
    ban = ((c < ema50) & (ema50 < ema200) & manh).fillna(False)
    return _dong_goi(d.index, mua, ban, None)


# ------------------------------------------------------------------ gop
def sinh_tat_ca_tin_hieu(d):
    """Tra ve dict {ten_chien_luoc: DataFrame tin hieu}."""
    return {"Scalping": tin_hieu_scalping(d),
            "Swing": tin_hieu_swing(d),
            "Position": tin_hieu_position(d)}
