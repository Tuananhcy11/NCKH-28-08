# -*- coding: utf-8 -*-
"""Pipeline hoi quy da muc tieu cho he so tuong quan delta OHLC giua XAU/USD va PAXG/USDT.

Cau truc:
    preprocessing.clean_and_align_ohlc          - lam sach, khu de-peg, dong bo UTC
    features.build_feature_matrix               - ma tran muc tieu Y va dac trung X
    model.rolling_multi_output_regression       - hoi quy truot da muc tieu
    reconstruct.reconstruct_and_enforce_ohlc    - tai tao gia + rang buoc hinh hoc OHLC
    evaluate.evaluate_residuals                 - MAE/RMSE/R2 + kiem dinh ADF phan du
"""
from .preprocessing import clean_and_align_ohlc
from .features import build_feature_matrix
from .model import rolling_multi_output_regression
from .reconstruct import reconstruct_and_enforce_ohlc
from .evaluate import evaluate_residuals

COLS = ["open", "high", "low", "close"]

__all__ = ["clean_and_align_ohlc", "build_feature_matrix",
           "rolling_multi_output_regression", "reconstruct_and_enforce_ohlc",
           "evaluate_residuals", "COLS"]
