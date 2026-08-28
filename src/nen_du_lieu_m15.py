# -*- coding: utf-8 -*-
"""Nen cac tep du lieu M15 trong data/processed thanh mot tep .zip de dua len git.

Ly do: data/processed/ bi loai khoi git vi bo_du_lieu_M15.csv nang 164 MB, vuot
gioi han cung 100 MB moi tep cua GitHub. Ban nen cua toan bo du lieu M15 nho hon
nhieu lan nen dua len duoc, giup nguoi khac tai lap ma khong phai chay lai
toan bo quy trinh.

    python src/nen_du_lieu_m15.py            # tao data/m15_processed.zip
    python src/nen_du_lieu_m15.py --giai-nen # giai nen tro lai data/processed/
"""
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import glob
import zipfile
from common import PROC, ROOT, log

TEP_ZIP = os.path.join(ROOT, "data", "m15_processed.zip")
GIOI_HAN_GITHUB_MB = 100


def _mb(n):
    return n / 1024.0 / 1024.0


def nen(tep_zip=TEP_ZIP, mau="*M15*"):
    ds = sorted(glob.glob(os.path.join(PROC, mau)))
    if not ds:
        raise SystemExit("Khong tim thay tep nao khop mau %s trong %s" % (mau, PROC))

    tong_goc = sum(os.path.getsize(f) for f in ds)
    log("Nen %d tep, tong %.1f MB" % (len(ds), _mb(tong_goc)))

    os.makedirs(os.path.dirname(tep_zip), exist_ok=True)
    # BZIP2 thay vi DEFLATED: do tren chinh bo du lieu nay, ty le nen 2.73x so voi
    # 2.37x cua DEFLATED-9 va con nhanh hon (19s so voi 28s). LZMA cho 2.62x nhung
    # mat 208s nen khong dang. Chenh lech nay quyet dinh viec tep co lot duoi
    # gioi han 100 MB cua GitHub hay khong.
    with zipfile.ZipFile(tep_zip, "w", zipfile.ZIP_BZIP2, compresslevel=9) as z:
        for f in ds:
            z.write(f, arcname="data/processed/" + os.path.basename(f))
            log("   + %-34s %7.1f MB" % (os.path.basename(f), _mb(os.path.getsize(f))))

    kich_thuoc = os.path.getsize(tep_zip)
    log("-> %s  %.1f MB (ty le nen %.1fx)"
        % (os.path.relpath(tep_zip, ROOT), _mb(kich_thuoc), tong_goc / max(1, kich_thuoc)))

    if _mb(kich_thuoc) >= GIOI_HAN_GITHUB_MB:
        log("!! VUOT gioi han %d MB cua GitHub - khong dua len duoc"
            % GIOI_HAN_GITHUB_MB)
    elif _mb(kich_thuoc) >= 50:
        log("   Luu y: GitHub canh bao voi tep tren 50 MB (van chap nhan).")
    return tep_zip, kich_thuoc


def giai_nen(tep_zip=TEP_ZIP, dich=None):
    dich = dich or ROOT
    with zipfile.ZipFile(tep_zip) as z:
        z.extractall(dich)
        log("Da giai nen %d tep vao %s" % (len(z.namelist()), dich))


if __name__ == "__main__":
    if "--giai-nen" in sys.argv:
        giai_nen()
    else:
        nen()
