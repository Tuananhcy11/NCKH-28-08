# BƯỚC 6 — Nén chuỗi 24/7 thành ba đặc trưng gắn vào nến mở phiên thứ Hai

## 6.1. Nguyên tắc bất di bất dịch
> **Chuỗi 24/7 không dùng để sinh lệnh.**

Chuỗi tái tạo chỉ là công cụ **trích xuất thông tin**. Mọi giao dịch và mọi chỉ tiêu hiệu suất từ Bước 7 trở đi đều tính trên **chuỗi 24/5 gốc**. Đây là điểm mấu chốt bảo vệ nghiên cứu khỏi phản biện "giao dịch trên dữ liệu không tồn tại".

## 6.2. Ba đặc trưng

| # | Tên | Công thức | Ý nghĩa |
|---|---|---|---|
| 1 | `bien_dong_cuoi_tuan` | `√(Σ r̂_t²)` trên toàn kỳ nghỉ | biến động cuối tuần ước lượng |
| 2 | `lech_tich_luy` | `Σ r_PAXG − Σ r̂` | độ lệch tích lũy PAXG–XAU |
| 3 | `diem_tam_ly_cuoi_tuan` | trung bình `S_t` (GDELT tone) trong kỳ nghỉ | điểm tâm lý cuối tuần |

Bổ trợ (lưu kèm, không tính là ba đặc trưng chính): `loi_suat_247_cuoi_tuan`, `cuong_do_tin_tuc`.

Mỗi kỳ nghỉ được gán vào **cây nến 24/5 đầu tiên xuất hiện sau đó** (`merge_asof` hướng tới, dung sai 4 ngày) — tức nến mở phiên thứ Hai. Các nến khác nhận giá trị 0 kèm cờ nhị phân `co_*` báo "nến này có/không có thông tin cuối tuần", tránh để mô hình hiểu nhầm 0 là một quan sát thật.

## 6.3. Mã nguồn
`src/step06_weekend_features.py` → `data/processed/dac_trung_cuoi_tuan_{tf}.csv`

## 6.4. Kết quả

| Khung | Số kỳ cuối tuần | Giai đoạn | Biến động TB (bp) | Lệch tích lũy TB (bp) | Độ lệch chuẩn lệch (bp) | Tâm lý TB |
|---|---|---|---|---|---|---|
| D1 | 279 | 2020-08-30 → 2025-12-28 | 95,8 | +2,0 | 88,6 | +0,052 |
| H1 | 279 | 2020-08-30 → 2025-12-28 | 181,3 | −1,5 | 172,2 | +0,049 |
| M15 | 279 | 2020-08-30 → 2025-12-28 | 203,4 | +7,7 | 188,3 | +0,049 |

So với lần chạy trên dữ liệu ngắn hạn, số kỳ cuối tuần ở H1 tăng từ 125 lên **279** và ở M15 từ 11 lên **279** — cả ba khung giờ phủ trọn cùng một giai đoạn 2020-08 → 2025-12.

## 6.5. Nhận xét
- Biến động cuối tuần ước lượng trung bình **0,96 % (D1) đến 2,03 % (M15)** — không hề nhỏ. Đây chính là lượng thông tin mà một mô hình chỉ nhìn chuỗi 24/5 sẽ bỏ sót ở nến mở phiên đầu tuần.
- Con số tăng dần theo độ phân giải (95,8 → 181,3 → 203,4 bp) là hệ quả trực tiếp của cách đo `√(Σ r̂²)`: khung càng nhỏ càng nhiều mốc nên tổng bình phương càng lớn. Khi so sánh giữa các khung phải nhớ điều này, không được đọc như "cuối tuần biến động mạnh hơn ở khung M15".
- Điểm tâm lý cuối tuần trung bình **dương nhẹ và nhất quán** (+0,049 đến +0,052 độ lệch chuẩn) trên cả ba khung — nay đo trên cùng 279 kỳ nghỉ nên ba con số hội tụ, khác hẳn giá trị +0,384 rời rạc của lần chạy trước trên 11 kỳ.
- Độ lệch tích lũy PAXG–XAU có trung bình gần 0 nhưng độ lệch chuẩn 83–130 bp: **không có thiên lệch hệ thống, nhưng có khoảng trống định giá đáng kể từng tuần** — đúng dạng biến số mà mô hình học máy có thể khai thác.

## 6.6. Hạn chế phải khai báo
- **Số kỳ quan sát rất ít ở khung nội phiên**: 125 kỳ nghỉ (H1) và 11 kỳ (M15). Ba đặc trưng này chỉ khác 0 ở khoảng 1/5 số nến D1 và dưới 1 % số nến H1 — đóng góp của chúng vì thế khó phát hiện bằng SHAP trung bình toàn tập (xem phân tích riêng ở Bước 10, mục 10.5).
- **Điểm tâm lý là tone tổng hợp của GDELT, không phải điểm FinBERT trên từng tiêu đề** (xem Bước 1, mục 1.6). Đây là xấp xỉ hợp lý về mặt tín hiệu nhưng thô hơn thiết kế gốc.
