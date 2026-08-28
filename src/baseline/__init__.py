# -*- coding: utf-8 -*-
"""Chien luoc nen (Baseline) ba tang cho doi chung voi chien luoc AI.

    che_do.py      - tang 1: phan dinh che do thi truong
    chien_luoc.py  - tang 2: luat vao lenh rieng cho tung che do
    thong_ke.py    - tang 3: mo phong thoat lenh va thong ke tin hieu
"""
from .che_do import phan_dinh_che_do, CHE_DO
from .chien_luoc import (tin_hieu_scalping, tin_hieu_swing, tin_hieu_position,
                         sinh_tat_ca_tin_hieu, CHIEN_LUOC)
from .thong_ke import mo_lenh_mot_vi_the, thong_ke_tin_hieu

__all__ = ["phan_dinh_che_do", "CHE_DO",
           "tin_hieu_scalping", "tin_hieu_swing", "tin_hieu_position",
           "sinh_tat_ca_tin_hieu", "CHIEN_LUOC",
           "mo_lenh_mot_vi_the", "thong_ke_tin_hieu"]
