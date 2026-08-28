# Nghiên cứu định lượng XAU/USD — AI so với tín hiệu kỹ thuật

Quy trình mười bước tái tạo chuỗi tham chiếu 24/7 neo theo tương quan PAXG, so sánh có kiểm soát XGBoost · LSTM · Random Forest với chiến lược nền ba tầng, kèm pipeline hồi quy delta OHLC và khung kiểm chứng weekend gap.

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [`docs/QUY_TRINH_TONG_HOP.md`](docs/QUY_TRINH_TONG_HOP.md) | **Bắt đầu đọc tại đây** — tổng hợp quy trình mười bước |
| [`docs/WEEKEND_GAP_Tong_Hop.md`](docs/WEEKEND_GAP_Tong_Hop.md) | Tổng hợp đầy đủ về weekend gap: 5 phát hiện, 6 cách xử lý, trần lý thuyết |
| [`docs/Baseline_Ba_Tang_Luat_Vao_Lenh.md`](docs/Baseline_Ba_Tang_Luat_Vao_Lenh.md) | Luật vào lệnh Scalping / Swing / Position và Bảng 2.4 |
| [`docs/So_Sanh_Hai_Phuong_Phap_Xu_Ly.md`](docs/So_Sanh_Hai_Phuong_Phap_Xu_Ly.md) | So sánh phương pháp cũ với phương pháp mới |
| [`docs/Do_Chinh_Xac_Bo_Du_Lieu_Tai_Tao.md`](docs/Do_Chinh_Xac_Bo_Du_Lieu_Tai_Tao.md) | Độ chính xác thực tế của bộ dữ liệu tái tạo |
| [`docs/Pipeline_Delta_OHLC_Hoi_Quy_Da_Muc_Tieu.md`](docs/Pipeline_Delta_OHLC_Hoi_Quy_Da_Muc_Tieu.md) | Pipeline hồi quy delta OHLC đa mục tiêu |
| `docs/Buoc_01…Buoc_10` | Tài liệu từng bước của quy trình mười bước |
| `Quy_Trinh_Xu_Ly_Du_Lieu_Moi.docx` | Báo cáo quy trình xử lý mới (bản Word) |

## Cấu trúc mã nguồn

```
src/
  common.py, indicators.py     tiện ích dùng chung
  thu_thap/                    Bước 1 — thu thập dữ liệu
  quy_trinh/                   Bước 2 → 10
  delta_ohlc/                  gói pipeline hồi quy delta OHLC
  baseline/                    chiến lược nền ba tầng
  kiem_dinh/                   thí nghiệm kiểm chứng weekend gap
  bao_cao/                     sinh báo cáo .docx
  run_delta_pipeline.py        điểm chạy pipeline delta OHLC
  run_baseline_thong_ke.py     điểm chạy thống kê chiến lược nền
```

Chi tiết: [`src/README.md`](src/README.md)

## Dữ liệu M15 đã xử lý

`data/processed/` không được lưu trên git (379 MB, riêng `bo_du_lieu_M15.csv` nặng 164 MB — vượt giới hạn 100 MB/tệp của GitHub). Thay vào đó, toàn bộ 9 tệp M15 đã xử lý được nén trong [`data/m15_processed.zip`](data/m15_processed.zip) (87,8 MB, nén BZIP2 tỉ lệ 3,2×, giải nén ra 278 MB).

```bash
python src/nen_du_lieu_m15.py --giai-nen   # giải nén về data/processed/
python src/nen_du_lieu_m15.py              # nén lại sau khi chạy lại pipeline
```

Dữ liệu của các khung D1 và H1 tái tạo được bằng `python src/quy_trinh/run_all.py 02`.

## Cách chạy

```bash
python src/thu_thap/step01e_forexsb.py       # XAU/USD M15 + H1 + D1 (nguồn chính)
python src/thu_thap/step01_collect.py paxg   # PAXG/USDT
python src/thu_thap/step01c_bitfinex.py      # USDT/USD, XAUT/USD
python src/thu_thap/step01b_gdelt.py         # GDELT (~45 phút vì bị giới hạn tốc độ)
python src/quy_trinh/run_all.py 02           # Bước 2 → 10 (~13 phút)
python src/run_baseline_thong_ke.py D1 H1 M15
python src/run_delta_pipeline.py D1 H1 M15
python src/kiem_dinh/run_delta_gap_test.py D1 H1 M15
python src/kiem_dinh/run_so_sanh_hai_phuong_phap.py D1 H1 M15
```

Môi trường: Python 3.11 · numpy · pandas · scipy · scikit-learn · xgboost · statsmodels · shap · torch (CPU) · python-docx · requests. Hạt giống ngẫu nhiên cố định `SEED = 42`.
