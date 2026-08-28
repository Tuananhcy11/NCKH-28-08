# -*- coding: utf-8 -*-
"""BUOC 1 (nguon chinh cho XAU/USD noi phien) - Du lieu lich su Dukascopy
   phan phoi qua Forex Software (data.forexsb.com).

   Ly do dung nguon nay:
     - Mot nguon duy nhat cho ca ba khung M15 / M30 / M1 -> KHONG phai ghep nguon.
     - Goc du lieu la Dukascopy, dung chuan nghien cuu dinh luong ngoai hoi.
     - Khong can API key, khong bi gioi han 730 ngay nhu Yahoo.

   Dinh dang tep .lb.gz (giai nen gzip roi doc nhi phan little-endian):
     ban ghi 24 byte : int32 phut-ke-tu-2000-01-01 | open | high | low | close | volume
     ban ghi 28 byte : nhu tren, co them int32 spread o cuoi
     Gia thuc = so nguyen / priceScale ; khoi luong thuc = so nguyen / volumeScale
"""
import gzip, struct, json, io, shutil
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import requests, numpy as np, pandas as pd
from common import *

S = requests.Session(); S.headers.update({"User-Agent": UA})
GOC   = "https://data.forexsb.com/datafeed"
INFO  = GOC + "/info/premium.json.gz"
DATA  = GOC + "/data/dukascopy/{sym}{chu_ky}.lb.gz"
MOC_2000 = pd.Timestamp("2000-01-01", tz="UTC")

# chu ky tinh bang phut, dung dung ky hieu cua nha cung cap
CHU_KY = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}

def bung(noi_dung):
    """May chu co the da tu giai nen o tang HTTP; thu gzip truoc, khong duoc thi dung nguyen."""
    try:
        return gzip.decompress(noi_dung)
    except OSError:
        return noi_dung

def thong_tin_san(sym):
    r = S.get(INFO, timeout=60); r.raise_for_status()
    info = json.loads(bung(r.content).decode("utf8"))
    if sym not in info:
        raise SystemExit("Khong co ky hieu %s. Cac ky hieu vang: %s"
                         % (sym, [k for k in info if "XAU" in k or "GOLD" in k.upper()]))
    return info[sym]

def tai(sym, chu_ky_phut):
    u = DATA.format(sym=sym, chu_ky=chu_ky_phut)
    r = S.get(u, timeout=180)
    if r.status_code != 200:
        log("   ! %s tra ma %s" % (u, r.status_code)); return None
    return bung(r.content)

def giai_ma(buf, price_scale, volume_scale):
    """Tu dong nhan dien ban ghi 24 hay 28 byte dua vao tinh don dieu cua truong thoi gian."""
    kich_thuoc = 24
    if len(buf) % 28 == 0:
        t = np.frombuffer(buf, dtype="<i4")[0::7]
        if np.all(np.diff(t.astype(np.int64)) >= 0):
            kich_thuoc = 28
    n_truong = kich_thuoc // 4
    a = np.frombuffer(buf[:len(buf) - len(buf) % kich_thuoc], dtype="<i4").reshape(-1, n_truong)
    d = pd.DataFrame({
        "time":   MOC_2000 + pd.to_timedelta(a[:, 0].astype("int64"), unit="m"),
        "open":   a[:, 1] / price_scale,
        "high":   a[:, 2] / price_scale,
        "low":    a[:, 3] / price_scale,
        "close":  a[:, 4] / price_scale,
        "volume": np.ceil(np.where(a[:, 5] == 0, 1, a[:, 5]) / volume_scale),
    })
    if kich_thuoc == 28:
        d["spread"] = a[:, 6]
    return d

def lay(sym, ten_khung, price_scale, volume_scale):
    buf = tai(sym, CHU_KY[ten_khung])
    if buf is None:
        return None
    d = giai_ma(buf, price_scale, volume_scale)
    d = d.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    log("   %s %s: %d nen, %s -> %s" % (sym, ten_khung, len(d),
        str(d["time"].min())[:10], str(d["time"].max())[:10]))
    return d

def run(sym="XAUUSD"):
    tt = thong_tin_san(sym)
    ps, vs = tt.get("priceScale", 1000), tt.get("volumeScale", 1)
    log("Nguon: Dukascopy qua data.forexsb.com | %s | priceScale=%s volumeScale=%s"
        % (tt.get("description", sym), ps, vs))

    # May chu gioi han 200 000 nen moi tep, nen moi khung lay tu tep co do phan giai
    # phu hop nhat de phu het giai doan nghien cuu:
    #   M15 <- tep M15  (do phan giai goc)
    #   H1, D1 <- tep M30, gop len bang resample cua CHINH nguon nay
    # Tuyet doi khong tron voi nguon khac.
    m15 = lay(sym, "M15", ps, vs)
    m30 = lay(sym, "M30", ps, vs)
    if m15 is None or m30 is None:
        raise SystemExit("Khong tai duoc du lieu goc")
    # Nen D1 gop theo phien ngoai hoi: mot ngay giao dich chay tu 22:00 UTC
    # hom truoc den 22:00 UTC hom sau. Neu gop theo moc 00:00 UTC thi phien mo
    # cua toi Chu nhat (22:00-24:00) se thanh mot nen D1 rieng chi dai 2 gio.
    # dung "24h" chu khong phai "1D": pandas 3 bo qua offset voi freq kieu ngay
    d1 = m30.set_index("time").resample("24h", offset="22h").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["close"]).reset_index()
    ket_qua = {"M15": m15,
               "H1": resample_ohlc(m30, "1h"),
               "D1": d1}

    for tf, d in ket_qua.items():
        d = d[(d["time"] >= pd.Timestamp(START, tz="UTC")) &
              (d["time"] <= pd.Timestamp(END, tz="UTC") + pd.Timedelta(days=1))]
        d = d.reset_index(drop=True)
        f = os.path.join(RAW, "xau_%s.csv" % tf)
        if os.path.exists(f):
            try:
                shutil.copy2(f, os.path.join(RAW, "cu_yahoo_xau_%s.csv" % tf))
            except OSError as ex:
                log("   (khong sao luu duoc ban cu: %s)" % ex)
        save(d, f)
        log("   -> %s: %s -> %s (%d nen trong giai doan nghien cuu)"
            % (tf, str(d["time"].min())[:10], str(d["time"].max())[:10], len(d)))

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "XAUUSD")
