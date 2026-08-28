# -*- coding: utf-8 -*-
"""Dieu phoi pipeline hoi quy da muc tieu cho he so delta OHLC XAU/USD vs PAXG/USDT.

    python src/run_delta_pipeline.py [khung...] [--window 500] [--alpha 1.0]
                                     [--engine fast|sklearn] [--model ridge|lasso|elasticnet|ols]

Vi du:  python src/run_delta_pipeline.py D1 H1 --window 500
"""
import json, time
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np
import pandas as pd
from common import RAW, PROC, TAB, ROOT, log, save
from delta_ohlc import (clean_and_align_ohlc, build_feature_matrix,
                        rolling_multi_output_regression, reconstruct_and_enforce_ohlc,
                        evaluate_residuals)
from delta_ohlc.features import kiem_tra_lookahead
from delta_ohlc.model import kiem_chung_hai_co_che
from delta_ohlc.reconstruct import do_sai_so_gia
from delta_ohlc.evaluate import kiem_dinh_dong_tich_hop
from delta_ohlc import datasources as ds

CUA_SO = {"D1": 500, "H1": 500, "M15": 500}      # W mac dinh theo yeu cau thiet ke


def chay(khung, window=None, alpha=1.0, engine="fast", model="ridge", step=1):
    t0 = time.time()
    log("=" * 70)
    log("KHUNG %s" % khung)

    # ---------------------------------------------------- 1. lam sach & dong bo
    xau, paxg, peg = ds.nap_gia(khung)
    rep_align = {}
    df = clean_and_align_ohlc(xau, paxg, peg, bao_cao=rep_align)
    log("1. Dong bo: %d moc chung (%s -> %s), phu song oracle %.3f"
        % (rep_align["so_moc_chung"], rep_align["tu"][:10], rep_align["den"][:10],
           rep_align["phu_song_oracle"]))
    log("   peg_dev trung binh %.2f bp, cuc dai %.1f bp"
        % (rep_align["peg_dev_tb_bp"], rep_align["peg_dev_max_bp"]))

    # ------------------------------------------------------------ 2. dac trung
    vimo = ds.nap_vi_mo()
    tin = ds.nap_tin_tuc()
    X, Y, nhom = build_feature_matrix(df, macro_df=vimo, news_df=tin, khung=khung)
    log("2. Ma tran dac trung: %d quan sat x %d dac trung" % (X.shape[0], X.shape[1]))
    for k, v in nhom.items():
        if v:
            log("     %-18s %d: %s" % (k, len(v), ", ".join(v)))

    la = kiem_tra_lookahead(X, Y)
    n_ngo = int((la["nghi_ngo"] == "CO").sum())
    log("   kiem tra lookahead: %d/%d dac trung dat dinh tuong quan o do tre DUONG (dau hieu lookahead)"
        % (n_ngo, len(la)))

    # --------------------------------------------- 3. hoi quy truot da muc tieu
    W = window or CUA_SO.get(khung, 500)
    log("3. Hoi quy truot: cua so %d nen, alpha=%.3g, engine=%s, model=%s"
        % (W, alpha, engine, model))
    pred, actual, _ = rolling_multi_output_regression(
        X, Y, window_size=W, alpha=alpha, engine=engine, model=model, step=step, log=log)
    log("   %d buoc du bao mot buoc (%s -> %s)"
        % (len(pred), str(pred.index.min())[:10], str(pred.index.max())[:10]))

    # ------------------------------------------ 4. tai tao gia + rang buoc OHLC
    rep_rc = {}
    recon = reconstruct_and_enforce_ohlc(pred, df, bao_cao=rep_rc)
    log("4. Tai tao gia: %d nen, vi pham hinh hoc truoc khi kep %d (%.4f%%), sau khi kep %d"
        % (rep_rc["so_nen"], rep_rc["so_vi_pham"], 100 * rep_rc["ty_le_vi_pham"],
           rep_rc["con_vi_pham_sau_kep"]))
    sai_so_gia = do_sai_so_gia(recon, df)

    # -------------------------------------------------------- 5. danh gia phan du
    bang = evaluate_residuals(actual, pred)
    dtd = kiem_dinh_dong_tich_hop(df)
    log("5. Danh gia phan du:")
    for _, r in bang.iterrows():
        log("   %-6s R2=%.4f (ngay tho %.4f) RMSE=%.6f  ADF p=%.3g -> %s"
            % (r["thanh_phan"], r["r2"], r.get("r2_ngay_tho", np.nan), r["rmse"],
               r.get("adf_p", np.nan), r.get("adf_ket_luan", "")))

    # ------------------------------------------------------------------ luu tru
    hau_to = "delta_%s" % khung
    save(pred.reset_index(), os.path.join(PROC, "%s_du_bao.csv" % hau_to))
    save(recon.reset_index(), os.path.join(PROC, "%s_tai_tao.csv" % hau_to))
    for ten, b in (("danh_gia", bang), ("sai_so_gia", sai_so_gia),
                   ("dong_tich_hop", dtd), ("lookahead", la)):
        b2 = b.copy(); b2.insert(0, "khung", khung)
        save(b2, os.path.join(TAB, "delta_%s_%s.csv" % (ten, khung)))

    tt = dict(khung=khung, cua_so=W, alpha=alpha, engine=engine, model=model,
              so_dac_trung=int(X.shape[1]), so_quan_sat=int(X.shape[0]),
              so_buoc_du_bao=int(len(pred)),
              phu_song_oracle=round(rep_align["phu_song_oracle"], 4),
              peg_dev_tb_bp=round(rep_align["peg_dev_tb_bp"], 3),
              ty_le_vi_pham_hinh_hoc=round(rep_rc["ty_le_vi_pham"], 6),
              lookahead_nghi_ngo=n_ngo,
              phut_chay=round((time.time() - t0) / 60, 2))
    for _, r in bang.iterrows():
        tt["r2_" + r["thanh_phan"]] = round(r["r2"], 4)
        tt["adf_p_" + r["thanh_phan"]] = float("%.3g" % r.get("adf_p", np.nan))
    for _, r in sai_so_gia.iterrows():
        tt["mae_usd_" + r["thanh_phan"]] = r["mae_usd"]
    log("   xong %s sau %.2f phut" % (khung, tt["phut_chay"]))
    return tt


if __name__ == "__main__":
    args = sys.argv[1:]
    khungs = [a for a in args if not a.startswith("--")] or ["D1", "H1"]
    def opt(ten, mac_dinh, kieu=str):
        return kieu(args[args.index("--" + ten) + 1]) if "--" + ten in args else mac_dinh
    window = opt("window", None, int) if "--window" in args else None
    alpha = opt("alpha", 1.0, float)
    engine = opt("engine", "fast")
    model = opt("model", "ridge")
    step = opt("step", 1, int)

    tong = [chay(k, window, alpha, engine, model, step) for k in khungs]
    t = pd.DataFrame(tong)
    save(t, os.path.join(TAB, "delta_tong_hop.csv"))
    print()
    print(t.to_string(index=False))
