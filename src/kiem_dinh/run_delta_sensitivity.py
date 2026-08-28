# -*- coding: utf-8 -*-
"""Do do vung cua pipeline delta OHLC theo cua so truot W, he so phat alpha
va dang mo hinh tuyen tinh.

    python src/run_delta_sensitivity.py [khung] [--step 10]

Dung buoc nhay (step) de lay mau thua tren truc thoi gian cho nhanh; ket luan ve
thu hang giua cac cau hinh khong doi vi moi cau hinh deu danh gia tren cung tap moc.
"""
import time, itertools
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np
import pandas as pd
from common import TAB, log, save
from delta_ohlc import clean_and_align_ohlc, build_feature_matrix
from delta_ohlc.model import rolling_multi_output_regression
from delta_ohlc.evaluate import evaluate_residuals
from delta_ohlc import datasources as ds

CUA_SO = [250, 500, 1000]
ALPHA = [0.1, 1.0, 10.0, 100.0]
MO_HINH = ["ridge", "ols"]


def run(khung="H1", step=10):
    xau, paxg, peg = ds.nap_gia(khung)
    df = clean_and_align_ohlc(xau, paxg, peg)
    X, Y, _ = build_feature_matrix(df, macro_df=ds.nap_vi_mo(),
                                   news_df=ds.nap_tin_tuc(), khung=khung)
    log("Do nhay tren %s: %d quan sat x %d dac trung, buoc nhay %d"
        % (khung, X.shape[0], X.shape[1], step))

    rows = []
    for W, a in itertools.product(CUA_SO, ALPHA):
        t0 = time.time()
        pred, actual, _ = rolling_multi_output_regression(
            X, Y, window_size=W, alpha=a, engine="fast", step=step, log=lambda *x: None)
        b = evaluate_residuals(actual, pred).set_index("thanh_phan")
        rows.append(dict(khung=khung, mo_hinh="ridge", cua_so=W, alpha=a,
                         so_buoc=len(pred),
                         **{"r2_" + c: round(float(b.loc[c, "r2"]), 4) for c in b.index},
                         r2_tb=round(float(b["r2"].mean()), 4),
                         rmse_tb=float("%.3g" % b["rmse"].mean()),
                         giay=round(time.time() - t0, 1)))
        log("   W=%-5d alpha=%-6.3g R2 trung binh=%.4f" % (W, a, rows[-1]["r2_tb"]))

    # OLS de doi chieu: alpha = 0 (khong phat)
    for W in CUA_SO:
        pred, actual, _ = rolling_multi_output_regression(
            X, Y, window_size=W, alpha=0.0, engine="fast", step=step, log=lambda *x: None)
        b = evaluate_residuals(actual, pred).set_index("thanh_phan")
        rows.append(dict(khung=khung, mo_hinh="ols", cua_so=W, alpha=0.0,
                         so_buoc=len(pred),
                         **{"r2_" + c: round(float(b.loc[c, "r2"]), 4) for c in b.index},
                         r2_tb=round(float(b["r2"].mean()), 4),
                         rmse_tb=float("%.3g" % b["rmse"].mean()), giay=np.nan))
        log("   OLS  W=%-5d R2 trung binh=%.4f" % (W, rows[-1]["r2_tb"]))

    t = pd.DataFrame(rows)
    save(t, os.path.join(TAB, "delta_do_nhay_%s.csv" % khung))
    print(t.to_string(index=False))
    return t


if __name__ == "__main__":
    args = sys.argv[1:]
    khung = next((a for a in args if not a.startswith("--")), "H1")
    step = int(args[args.index("--step") + 1]) if "--step" in args else 10
    run(khung, step)
