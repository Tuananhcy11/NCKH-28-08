# BƯỚC 2 — Chuẩn hóa PAXG về mặt bằng USD

## 2.1. Mục tiêu
Khử sai lệch neo giá (de-peg) của USDT trước khi so sánh PAXG với XAU/USD.

## 2.2. Công thức

$$P^{PAXG}_{USD}(t) = P^{PAXG}_{USDT}(t) \times \frac{USDT}{USD}(t)$$

Tỷ giá `USDT/USD` lấy từ **Bitfinex `tUSTUSD`** — một nguồn duy nhất, là sàn fiat **độc lập với Binance** (nơi cung cấp báo giá PAXG). Nhờ vậy sai số neo được đo bằng hệ thống không cùng nguồn với chuỗi cần hiệu chỉnh.

Ghép theo `merge_asof` lùi, dung sai 3 ngày. Chuỗi Bitfinex bắt đầu 2018-11, sớm hơn PAXG (2020-08), nên **độ phủ oracle đạt 100 %** — không mốc nào phải giả định neo = 1,0.

## 2.3. Mã nguồn
`src/step02_normalize_paxg.py` → `data/processed/paxg_usd_{D1,H1,M15}.csv`

## 2.4. Kết quả (`results/tables/buoc02_chuan_hoa_paxg.csv`)

| Khung | Số nến | Giai đoạn | Độ phủ oracle | Lệch neo TB (bp) | Độ lệch chuẩn (bp) | Lệch max (bp) | Ảnh hưởng lên log return (bp) |
|---|---|---|---|---|---|---|---|
| D1 | 2 186 | 2020-08-28 → 2026-08-22 | **100 %** | +5,69 | 8,03 | 39,0 | 5,46 |
| H1 | 52 424 | nt | **100 %** | +5,76 | 8,18 | 58,0 | 2,00 |
| M15 | 209 681 | nt | **100 %** | +5,76 | 8,18 | 58,0 | 1,00 |

## 2.5. Nhận xét
- Sai lệch neo trung bình **+5,8 bp** (0,058 %): trên Bitfinex, USDT giao dịch nhỉnh hơn USD một chút và ổn định. Con số này nhỏ nhưng **có hệ thống** — bỏ qua bước chuẩn hóa sẽ tạo một độ trôi cố định giữa PAXG và XAU.
- Lệch cực đại 39–58 bp, thấp hơn nhiều so với con số 280 bp đo trên nguồn ghép hai sàn ở lần chạy trước. Điều này cho thấy phần lớn "đuôi lệch 280 bp" trước đây **là hiện vật của việc ghép nguồn**, không phải de-peg thật — một minh chứng cụ thể cho nguyên tắc một chuỗi một nguồn.
- Đóng góp vào độ lệch chuẩn log return chỉ 1,0–5,5 bp → chuẩn hóa **không làm méo** cấu trúc biến động của PAXG.

## 2.6. Hạn chế
Chỉ dùng một sàn để đo neo giá nghĩa là chấp nhận đặc thù thanh khoản của sàn đó. Muốn chặt hơn có thể lấy **trung vị của ba nguồn độc lập** (Bitfinex, Kraken `USDTZUSD`, oracle Chainlink) — nhưng đó là một ước lượng tổng hợp có chủ đích, khác hẳn với việc nối đuôi hai chuỗi vào nhau.
