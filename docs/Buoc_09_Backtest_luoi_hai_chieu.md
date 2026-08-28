# BƯỚC 9 — Backtest theo lưới hai chiều

## 9.1. Lưới thực nghiệm

| Chiều | Giá trị |
|---|---|
| Khối lượng vào lệnh | 0,1 · 0,2 · 0,3 · 0,5 lot |
| Khoảng cắt lỗ | 5 · 10 · 15 · 20 · 25 · 30 giá (USD/ounce) |
| Tỷ lệ R:R | 1:1,5 · 1:2,0 |
| Mô hình | XGBoost · LSTM · RandomForest · Baseline |
| Khung | D1 · H1 · M15 |

4 × 6 × 2 = **48 cấu hình lot cố định** mỗi mô hình mỗi khung, cộng **36 cấu hình định cỡ theo % rủi ro** (0,5 % · 1,0 % · 2,0 % × 6 mức cắt lỗ × 2 R:R) chạy song song để kiểm chứng độ vững. Tổng **1 008 dòng kết quả**.

## 9.2. Quy ước mô phỏng
- Vốn ban đầu **10 000 USD**; 1 lot XAU/USD = 100 ounce → 1 USD giá = 100 USD/lot.
- Chi phí: chênh lệch mua-bán **0,30 USD/ounce** (nửa khi vào, nửa khi ra) + hoa hồng khứ hồi **7 USD/lot**.
- Mỗi thời điểm giữ **tối đa một vị thế**; thoát khi chạm cắt lỗ, chạm chốt lời, hoặc hết chân trời `H` nến.
- Tín hiệu lấy từ dự báo **ngoài mẫu** của Bước 8, vào lệnh tại giá đóng nến phát tín hiệu.
- Định cỡ theo % rủi ro: `lot = (%rủi_ro × vốn) / (cắt_lỗ × 100)`, cập nhật theo vốn hiện hành.
- Dừng mô phỏng khi vốn còn dưới 20 % vốn ban đầu.

## 9.3. Mã nguồn
`src/step09_backtest.py` → `results/tables/buoc09_luoi_backtest.csv`

## 9.4. Cấu hình tốt nhất mỗi khung

| Khung | Mô hình | Lot | Cắt lỗ | R:R | Số lệnh | Lợi nhuận | Tỷ lệ thắng | Hệ số LN | Sharpe | Sụt giảm tối đa |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | **XGBoost** | 0,5 | 30 | 1:2,0 | 313 | +681,6 % | 46,7 % | 1,300 | 0,77 | −44,9 % |
| H1 | **Baseline** | 0,2 | 20 | 1:2,0 | 997 | +163,9 % | 47,2 % | 1,138 | 0,67 | −78,2 % |
| M15 | **Baseline** | 0,2 | 20 | 1:2,0 | 881 | +197,4 % | 49,7 % | 1,265 | 1,48 | −64,3 % |

> Các con số phần trăm ba chữ số là hệ quả của đòn bẩy cao trên tài khoản 10 000 USD; dùng để **xếp hạng tương đối**, không phải mức lợi nhuận kỳ vọng thực tế. Sụt giảm −64 % đến −78 % ở cấu hình "tốt nhất" cho thấy chính các cấu hình này cũng không dùng được trong thực tế.

## 9.5. Kết quả ở mức định cỡ hợp lý

Đọc lưới ở **0,1 lot** — mức nhỏ nhất, gần với quản trị rủi ro thực tế nhất (trung vị trên 12 cấu hình cắt lỗ × R:R):

| Khung | Mô hình | Lợi nhuận | Hệ số LN | Sharpe | Sụt giảm tối đa | Số lệnh |
|---|---|---|---|---|---|---|
| D1 | **Baseline** | **+48,7 %** | **1,126** | **0,336** | **−20,5 %** | 349 |
| D1 | XGBoost | +39,2 % | 1,080 | 0,310 | −38,9 % | 482 |
| D1 | RandomForest | −18,5 % | 0,958 | 0,010 | −57,8 % | 410 |
| D1 | LSTM | −80,4 % | 0,766 | −0,599 | −81,6 % | 311 |
| H1 | **Baseline** | **+52,5 %** | **1,084** | **0,508** | −56,1 % | 1 066 |
| H1 | RandomForest | +27,1 % | 1,044 | 0,364 | **−44,8 %** | 1 092 |
| H1 | XGBoost | −7,4 % | 0,990 | 0,126 | −53,9 % | 1 225 |
| H1 | LSTM | −59,7 % | 0,919 | −0,374 | −77,4 % | 1 151 |
| M15 | **Baseline** | **+60,5 %** | **1,154** | **1,311** | −33,0 % | 918 |
| M15 | LSTM | +6,4 % | 1,015 | 0,355 | −70,9 % | 941 |
| M15 | RandomForest | +5,5 % | 1,016 | 0,303 | **−33,7 %** | 875 |
| M15 | XGBoost | −0,8 % | 0,998 | 0,178 | −41,1 % | 979 |

**Baseline MACD + EMA thắng trên cả ba khung.** Đây là kết quả trung tâm của Bước 9 và nó **đảo ngược** kết luận của lần chạy trên dữ liệu ngắn hạn trước đó.

Cơ chế đọc được ngay từ cột "Số lệnh": ở H1, baseline vào 1 066 lệnh còn XGBoost vào 1 225 lệnh — nhiều hơn 15 %. Mỗi lệnh mất 0,30 USD chênh lệch cộng 7 USD/lot hoa hồng. Ưu thế phân loại +10,4 điểm phần trăm của XGBoost (Bước 8) bị chi phí giao dịch ăn hết và còn âm. **Baseline thắng không phải vì dự báo giỏi hơn mà vì im lặng đúng lúc.**

## 9.6. Ba quy luật về quản trị rủi ro

**(a) Tăng lot là con đường ngắn nhất tới cháy tài khoản.** Trung vị toàn lưới:

| Lot | D1 sụt giảm / lợi nhuận | H1 | M15 |
|---|---|---|---|
| 0,1 | −53,5 % / −21,6 % | −59,2 % / −2,0 % | −39,0 % / **+11,6 %** |
| 0,2 | −80,8 % / −80,4 % | −81,5 % / −80,7 % | −77,8 % / −38,4 % |
| 0,3 | −81,3 % / −80,4 % | −84,1 % / −81,1 % | −81,1 % / −80,7 % |
| 0,5 | −86,0 % / −81,1 % | −85,6 % / −82,5 % | −82,0 % / −82,0 % |

Từ 0,2 lot trở lên, trung vị lợi nhuận rơi thẳng xuống −80 % trên cả ba khung: phần lớn cấu hình chạm ngưỡng cháy tài khoản và bị dừng. Với vốn 10 000 USD, **0,1 lot là mức trần**, không phải mức khởi điểm.

**(b) Định cỡ theo % rủi ro cứu được mức sụt giảm nhưng không cứu được biên lợi nhuận.**

| Chế độ | D1 sụt giảm / hệ số LN | H1 | M15 |
|---|---|---|---|
| 0,5 % rủi ro | −16,2 % / 0,947 | −16,4 % / 0,992 | −12,6 % / **1,028** |
| 1,0 % rủi ro | −30,2 % / 0,941 | −30,5 % / 0,988 | −23,7 % / 1,023 |
| 2,0 % rủi ro | −52,6 % / 0,927 | −52,8 % / 0,976 | −42,3 % / 1,013 |

Sụt giảm giảm từ −80 % xuống −13 % đến −16 %, nhưng hệ số lợi nhuận trung vị vẫn quanh 0,93–1,03. Định cỡ theo rủi ro **kiểm soát được thiệt hại, không tạo ra lợi thế** — nó không biến một chiến lược thua thành thắng.

**(c) R:R 1:2,0 nhỉnh hơn 1:1,5 trên cả ba khung**, nhưng chênh lệch nhỏ (hệ số lợi nhuận trung vị 0,935 so với 0,868 ở D1; 0,738 so với 0,728 ở M15). Kéo dài mục tiêu làm tỷ lệ thắng tụt (D1: 38,9 % → 35,5 %) nhưng độ lớn thắng bù lại được.

## 9.7. Kết luận thẳng thắn về Bước 9
Trong **1 008 cấu hình**, hệ số lợi nhuận trung vị theo chế độ định cỡ theo rủi ro nằm trong khoảng **0,93–1,03**, tức quanh hòa vốn. Chỉ một nhóm nhỏ cấu hình có lãi thực, và chúng tập trung ở baseline quy tắc với lot nhỏ. Kết luận trung thực: **trên dữ liệu 2015–2025 với chi phí giao dịch thực tế, không có cấu hình nào trong lưới đạt hiệu suất đủ tốt để triển khai**. Đây là kết quả có giá trị hơn hẳn một con số lợi nhuận đẹp lấy từ giai đoạn hai tháng.
