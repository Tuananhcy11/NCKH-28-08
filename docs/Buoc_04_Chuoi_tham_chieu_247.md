# BƯỚC 4 — Xây dựng chuỗi tham chiếu cuối tuần bằng mô hình neo tương quan

## 4.1. Mục tiêu
Ước lượng biến động của vàng trong khoảng thị trường 24/5 đóng cửa (từ 21:00 UTC thứ Sáu đến 22:00 UTC Chủ nhật), dựa trên log return của PAXG — tài sản giao dịch liên tục 24/7.

## 4.2. Mô hình

$$\hat r_t = \beta(\text{chế độ}_t)\cdot s\cdot r^{PAXG}_t \cdot \big(1 + \lambda I_t\big) + \varepsilon_t,\qquad \varepsilon_t\sim\mathcal N(0,\ \kappa^2\sigma_e^2)$$

| Ký hiệu | Ý nghĩa | Nguồn |
|---|---|---|
| `β(chế độ)` | hệ số neo tương quan phân tầng theo chế độ biến động | Bước 3 |
| `s` | hệ số co giãn hiệu chỉnh | Bước 5 |
| `I_t` | cường độ tin tức chuẩn hóa (z-score, cắt ở ±3, lấy trị tuyệt đối) | GDELT |
| `λ` | biên độ điều biến tin tức, đặt 0,30 | tham số thiết kế |
| `ε_t` | phần dư đặc thù của vàng | mô phỏng |
| `σ_e` | `σ_XAU·√(1−R²)` lấy từ Bước 3 | Bước 3 |
| `κ` | hệ số hiệu chỉnh biên độ phần dư | Bước 5 |

**Vì sao phải có `ε_t`.** Nếu chỉ nhân beta với return PAXG, chuỗi tái tạo sẽ tương quan **1,00** với PAXG — một bản sao tuyến tính, không phải một chuỗi vàng. Phần dư có phương sai suy ra từ `1−R²` của Bước 3 khôi phục đúng lượng biến động đặc thù mà vàng có nhưng PAXG không giải thích được. Chính `κ` là tham số được vòng lặp Bước 5 hiệu chỉnh.

## 4.3. Cường độ tin tức
Ba nhóm từ khóa được gộp theo trọng số **gold 0,5 · macro 0,3 · geopolitics 0,2**, mỗi chuỗi chuẩn hóa bằng z-score trượt 180 ngày, cắt ở ±3.

- `I_t` (**cường độ tin tức**) gộp từ ba chuỗi `timelinevol`, lấy **trị tuyệt đối** — đây là đại lượng đo *độ lớn* của dòng tin, không phải chiều.
- `S_t` (**điểm tâm lý**) gộp từ ba chuỗi `timelinetone`, **giữ nguyên dấu** — âm là sắc thái tiêu cực, dương là tích cực. `S_t` không tham gia công thức `r̂_t`; nó là đặc trưng thứ ba của Bước 6.

Cả sáu chuỗi GDELT đều khả dụng trong lần chạy này (3 496 điểm ngày mỗi chuỗi, 2017-01 → 2026-08).

## 4.3b. Vì sao beta phân tầng là bắt buộc
Kết quả Bước 3 cho thấy β dao động từ 0,207 (M15, biến động thấp) đến 0,925 (D1, biến động cao) — chênh nhau **4,5 lần**. Dùng một β chung sẽ ước lượng sai biến động cuối tuần theo hệ số tương ứng. Vì vậy `build()` tra β theo đúng cặp (khung thời gian, chế độ biến động) của từng mốc, với chế độ biến động suy ra từ chính PAXG — chuỗi có sẵn 24/7.

## 4.4. Chuỗi 24/7 được ghép thế nào
- Trong phiên 24/5: dùng **log return thật của XAU/USD**.
- Ngoài phiên (cuối tuần): dùng `r̂_t`.
- Giá: `P_247(t) = P_0 · exp(Σ r)`.

Kết quả: `data/processed/chuoi_247_{D1,H1,M15}.csv`. Tỷ trọng mốc cuối tuần: 28,6 % (D1) và 29,2 % (H1, M15).

## 4.5. Mã nguồn
`src/step04_reference_series.py` — hàm `build(tf, lam, shrink, kappa, ...)` được Bước 5 gọi lặp.
