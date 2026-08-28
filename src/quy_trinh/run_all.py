# -*- coding: utf-8 -*-
"""Chay toan bo quy trinh (Buoc 2 -> Buoc 10). Buoc 1 chay rieng vi phu thuoc mang."""
import time, importlib
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
from common import log

BUOC = [("02", "step02_normalize_paxg"), ("03", "step03_baseline_corr"),
        ("05", "step05_calibrate"), ("06", "step06_weekend_features"),
        ("07", "step07_label"), ("08", "step08_models"),
        ("09", "step09_backtest"), ("10", "step10_evaluate")]

if __name__ == "__main__":
    tu = sys.argv[1] if len(sys.argv) > 1 else "02"
    t0 = time.time()
    for so, mod in BUOC:
        if so < tu: continue
        log("=== BUOC %s : %s ===" % (so, mod))
        m = importlib.import_module(mod)
        if mod == "step08_models":
            import pandas as pd
            from common import TFS, TAB, save, PROC
            import json
            out, cols = [], None
            for tf in TFS:
                r, cols = m.run(tf); out.append(r)
            t = pd.concat(out, ignore_index=True)
            save(t, os.path.join(TAB, "buoc08_so_sanh_mo_hinh.csv"))
            json.dump(cols, open(os.path.join(PROC, "danh_sach_dac_trung.json"), "w"), indent=1)
        else:
            m.run()
    log("HOAN TAT toan bo quy trinh sau %.1f phut" % ((time.time() - t0) / 60))
