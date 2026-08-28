# BƯỚC 7 — Gán nhãn ba trạng thái bằng Triple Barrier Method

## 7.1. Phương pháp
Trên **chuỗi 24/5 gốc**, với mỗi nến `i`:

- rào cản trên: `C_i + m·ATR14_i`
- rào cản dưới: `C_i − m·ATR14_i`
- rào cản dọc: tối đa `H` nến (D1: 10, H1: 24, M15: 32)

Nhãn = **Tăng (+1)** nếu chạm rào trên trước, **Giảm (−1)** nếu chạm rào dưới trước, **Sideway (0)** nếu hết hạn chưa chạm rào nào, hoặc chạm cả hai trong cùng một nến (trường hợp mơ hồ, xử lý thận trọng thành Sideway).

## 7.2. Hiệu chỉnh độ rộng rào cản
Với `m = 1,5` như thiết kế ban đầu, tỷ lệ Sideway chỉ 2–18 % — bài toán ba lớp suy biến thành nhị phân. `m` được dò trên lưới {1,0 … 4,0} và chọn giá trị đưa tỷ lệ Sideway gần **25 %** nhất (`results/tables/buoc07_hieu_chinh_rao_can.csv`). Ví dụ khung D1: m=1,0 → 2,4 % Sideway; m=1,75 → 27,9 %; m=3,0 → 68,8 %.

## 7.3. Mã nguồn
`src/step07_label.py` (kèm `src/indicators.py`) → `data/processed/bo_du_lieu_{tf}.csv`

## 7.4. Kết quả gán nhãn

| Khung | Số mẫu | Giai đoạn | Tăng | Sideway | Giảm | Số nến giữ TB | m (ATR) | Khớp EMA200–ADX | Cohen κ |
|---|---|---|---|---|---|---|---|---|---|
| D1 | 2 837 | 2015-01-01 → 2025-12-29 | 43,4 % | 27,9 % | 28,7 % | 6,42 | 1,75 | 34,8 % | +0,033 |
| H1 | 65 125 | 2015-01-01 → 2025-12-31 | 41,7 % | 19,3 % | 39,0 % | 13,00 | 2,50 | 27,0 % | −0,010 |
| M15 | 184 881 | 2018-03-07 → 2025-12-31 | 36,8 % | 28,0 % | 35,3 % | 18,51 | 3,00 | 29,1 % | −0,026 |

Quy mô mẫu tăng rất mạnh so với lần chạy trên dữ liệu ngắn hạn: H1 từ 13 747 lên **65 125**, M15 từ 4 624 lên **184 881**. Đây là điều kiện tối thiểu để kết luận ở Bước 8–10 có ý nghĩa.

**Bất đối xứng Tăng / Giảm ở D1** (43,4 % so với 28,7 %) phản ánh đúng thực tế: 2015–2025 là một chu kỳ tăng dài của vàng. Ở H1 và M15, bất đối xứng thu hẹp — xu hướng dài hạn không hiện rõ ở khung nội phiên.

## 7.5. Đối chiếu chéo với bộ quy tắc EMA200 – ADX
Quy tắc: `ADX ≥ 25` **và** `Close > EMA200` **và** `+DI > −DI` → Tăng; đối xứng cho Giảm; còn lại Sideway.

Ma trận đối chiếu khung D1 (`results/tables/buoc07_doi_chieu_D1.csv`):

| | QT Tăng | QT Sideway | QT Giảm |
|---|---|---|---|
| **TBM Tăng** | 394 | 718 | 120 |
| **TBM Sideway** | 203 | 509 | 80 |
| **TBM Giảm** | 244 | 484 | 85 |

**Đây là một kết quả âm tính, và nó ổn định qua mọi lần chạy.** Cohen κ nằm trong khoảng −0,026 đến +0,033 trên cả ba khung — tức hai phương pháp **thống nhất ở mức không hơn ngẫu nhiên**. Nguyên nhân đọc thẳng từ ma trận: quy tắc gán 1 711/2 837 nến (60 %) vào Sideway vì `ADX < 25` phần lớn thời gian, trong khi TBM chỉ gán 28 %.

Diễn giải: hai phương pháp **đo hai đại lượng khác nhau** — EMA200–ADX đo *cường độ xu hướng tại thời điểm hiện tại*, TBM đo *kết quả giá trong tương lai có kiểm soát rủi ro*. Vì vậy EMA200–ADX **không phải bộ kiểm chứng hợp lệ** cho nhãn TBM. Giữ nó trong báo cáo như một quan sát so sánh thì được, nhưng không được dùng làm bằng chứng "nhãn đã được xác nhận chéo".

## 7.6. Bộ đặc trưng (40 biến đưa vào mô hình)
Log return đa kỳ (1/2/3/5/10/20), khoảng cách tới EMA10/20/50/200, ba chênh lệch EMA, MACD chuẩn hóa theo giá, RSI 7/14, ATR%, ADX/+DI/−DI, độ rộng và vị trí Bollinger, Stochastic K/D, biến động trượt 5/20/60, tỷ số biến động, biên độ nến, thân nến, z-score khối lượng, giờ, thứ, cùng **ba đặc trưng cuối tuần từ Bước 6** và ba cờ nhị phân đi kèm.

Riêng khung M15 có thêm biến `spread` — dữ liệu Dukascopy ghi kèm chênh lệch mua-bán trung bình của từng nến. Đây là thông tin đã biết tại thời điểm ra quyết định nên không gây rò rỉ.

Các cột bị loại khỏi đầu vào để chống rò rỉ: `gia_cham`, `so_nen_giu`, `rao_tren`, `rao_duoi`, `nhan_ema_adx`, giá thô OHLC và các đường EMA/ATR ở đơn vị tuyệt đối.
