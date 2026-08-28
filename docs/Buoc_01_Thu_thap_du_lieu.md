# BƯỚC 1 — Thu thập song song ba luồng dữ liệu

## 1.1. Mục tiêu
Thu thập đồng thời ba luồng dữ liệu độc lập, mỗi luồng lấy từ **một nguồn duy nhất** — không ghép nhiều sàn vào cùng một chuỗi.

| Luồng | Nội dung | Khung | Giai đoạn yêu cầu |
|---|---|---|---|
| A | XAU/USD | M15 / H1 / D1 | 2015–2025 |
| B | PAXG/USDT | M15 / H1 / D1 | 2019–2025 |
| C | Tin GDELT: vàng — vĩ mô — địa chính trị | ngày | 2017–2025 |

## 1.2. Nguyên tắc một nguồn cho một chuỗi
Ghép hai sàn vào cùng một chuỗi giá tạo ra gãy cấu trúc tại điểm nối: chênh lệch mua-bán, giờ chốt phiên và quy ước làm tròn của hai sàn khác nhau, nên log return tại mốc nối là **giả tạo**. Với dữ liệu dùng để đo tương quan và gán nhãn theo ATR, một điểm gãy như vậy đủ làm lệch hệ số beta và sinh nhãn sai. Vì vậy mỗi chuỗi trong nghiên cứu này chỉ có một nguồn.

## 1.3. Nguồn cuối cùng cho từng chuỗi

| Chuỗi | Nguồn | Ghi chú |
|---|---|---|
| XAU/USD M15 / H1 / D1 | **Dukascopy**, phân phối qua `data.forexsb.com` | Cùng một nguồn cho cả ba khung |
| PAXG/USDT M15 / H1 / D1 | **Binance** REST `/api/v3/klines` | Sàn có lịch sử PAXG sớm nhất truy cập được |
| USDT/USD D1 / H1 | **Bitfinex** `tUSTUSD` | Sàn fiat độc lập với Binance, dùng cho Bước 2 |
| XAUT/USD M15 / H1 / D1 | **Bitfinex** `tXAUT:USD` | Vàng token thứ hai, dùng kiểm chứng chéo |
| GDELT (6 chuỗi) | GDELT DOC 2.0 API | `timelinevol` và `timelinetone` |
| GLD D1 | Yahoo Finance | **Chỉ dùng kiểm chứng chéo**, không đưa vào mô hình |

## 1.4. Chi tiết luồng A — XAU/USD từ Dukascopy
Nhà cung cấp phát hành tệp nhị phân `.lb.gz`, mỗi tệp tối đa 200 000 nến:

```
bản ghi 24 byte : int32 phút-kể-từ-2000-01-01 | open | high | low | close | volume
bản ghi 28 byte : như trên, thêm int32 spread ở cuối
giá thực = số nguyên / priceScale     (XAUUSD: priceScale = 1000)
```

Vì giới hạn 200 000 nến, mỗi khung lấy từ tệp có độ phân giải phù hợp nhất — **vẫn cùng một nguồn**:

| Khung | Tệp gốc | Cách dựng | Kết quả |
|---|---|---|---|
| M15 | `XAUUSD15.lb.gz` | dùng trực tiếp | 2018-03-07 → 2025-12-31 |
| H1 | `XAUUSD30.lb.gz` | gộp 2 nến M30 | 2015-01-01 → 2025-12-31 |
| D1 | `XAUUSD30.lb.gz` | gộp theo phiên | 2015-01-01 → 2025-12-30 |

**Nến D1 gộp theo phiên ngoại hối 22:00 → 22:00 UTC**, không theo mốc 00:00 UTC. Nếu gộp theo 00:00, phiên mở cửa tối Chủ nhật (22:00–24:00) trở thành một nến D1 riêng chỉ dài 2 giờ — lần chạy đầu sinh ra 565 nến giả loại này, đẩy số nến lên 311/năm. Sau khi sửa: **258 nến/năm**, đúng số phiên giao dịch thực của thị trường 24/5.

## 1.5. Kiểm chứng chất lượng dữ liệu mới
Trước khi dùng, chuỗi Dukascopy được kiểm tra lệch dấu thời gian bằng tương quan chéo có độ trễ giữa log return XAU và PAXG:

| Độ trễ | H1 | M15 |
|---|---|---|
| −2 | 0,018 | 0,033 |
| −1 | 0,074 | 0,104 |
| **0** | **0,658** | **0,467** |
| +1 | −0,003 | −0,003 |
| +2 | −0,004 | 0,006 |

Đỉnh nằm đúng tại độ trễ 0 trên cả hai khung → **dấu thời gian chuẩn UTC, không lệch múi giờ**. Đây là bước kiểm tra bắt buộc khi đổi nguồn dữ liệu; nếu bỏ qua, một sai lệch 1–2 giờ sẽ phá hủy toàn bộ kết quả từ Bước 3 trở đi mà không để lại dấu hiệu rõ ràng.

## 1.6. Mã nguồn

| Tệp | Chức năng |
|---|---|
| `src/step01e_forexsb.py` | XAU/USD M15 / H1 / D1 — **nguồn chính** |
| `src/step01_collect.py` | PAXG/USDT; GLD kiểm chứng chéo |
| `src/step01c_bitfinex.py` | USDT/USD và XAUT/USD |
| `src/step01b_gdelt.py` | Sáu chuỗi tin GDELT |
| `src/step01d_xau_intraday.py` | Dự phòng: XAU nội phiên qua Twelve Data / Polygon (cần API key) |

## 1.7. Kết quả thu được

| Tệp | Số nến | Giai đoạn thực tế |
|---|---|---|
| `xau_D1.csv` | 2 838 | 2015-01-01 → 2025-12-30 |
| `xau_H1.csv` | 65 126 | 2015-01-01 → 2025-12-31 |
| `xau_M15.csv` | 184 882 | 2018-03-07 → 2025-12-31 |
| `paxg_D1.csv` | 2 186 | 2020-08-28 → 2026-08-22 |
| `paxg_H1.csv` | 52 424 | 2020-08-28 → 2026-08-22 |
| `paxg_M15.csv` | 209 681 | 2020-08-28 → 2026-08-22 |
| `usdtusd_D1.csv` | 2 827 | 2018-11-27 → 2026-08-23 |
| `usdtusd_H1.csv` | 67 738 | 2018-11-27 → 2026-08-23 |
| `xaut_D1 / H1 / M15.csv` | 2 403 / 45 354 / 134 316 | 2020-01-24 → 2026-08-23 |
| `gdelt_{gold,macro,geopolitics}_{vol,tone}.csv` | 3 496 mỗi tệp | 2017-01-01 → 2026-08-22 |

## 1.8. Ba khoảng trống còn lại và nguyên nhân

**1. XAU M15 chỉ từ 2018-03, không phải 2015.** Nguyên nhân là giới hạn cứng 200 000 nến mỗi tệp của nhà cung cấp: 200 000 nến M15 ≈ 8 năm giao dịch. Không thể dựng M15 từ tệp thô hơn. Hai đường ra: (a) `src/step01d_xau_intraday.py` với API key Twelve Data hoặc Polygon — đã kiểm tra cả hai máy chủ đều truy cập được, chỉ thiếu khóa; (b) xuất lịch sử M1 của XAUUSD từ MetaTrader 5 của một sàn. **H1 và D1 đã đủ trọn 2015–2025** nên đây chỉ ảnh hưởng đến khung M15.

**2. PAXG không thể có trước 09/2019.** Token PAX Gold phát hành tháng 9/2019 — **dữ liệu 2015–2019 không tồn tại**, đây là giới hạn của bản thân tài sản chứ không phải của nguồn. Binance niêm yết 08/2020 và là sàn có lịch sử sớm nhất truy cập được; Kraken niêm yết muộn hơn, Bitfinex không có cặp PAXG. Đã bổ sung **XAUT/USD từ 01/2020** làm chuỗi vàng token thứ hai.

**3. USDT/USD từ 2018-11.** Bitfinex là sàn fiat có lịch sử USDT sớm nhất truy cập được. Vì PAXG chỉ bắt đầu 08/2020, chuỗi này **phủ trọn giai đoạn cần dùng** — độ phủ oracle ở Bước 2 đạt 100 %.

## 1.9. Các nguồn đã thử và không dùng được
Ghi lại để lần sau khỏi thử lại:

| Nguồn | Kết quả |
|---|---|
| Dukascopy `datafeed` / `freeserv` (trực tiếp) | Không thiết lập được kết nối |
| HistData.com | Trang chủ mở được qua HTTP nhưng `get.php` yêu cầu token do trình duyệt sinh; trả 0 byte |
| Stooq | Chặn bằng cơ chế xác minh trình duyệt |
| FXCM `candledata` | Máy chủ còn sống nhưng không còn ký hiệu XAUUSD (404) |
| Yahoo Finance nội phiên | Giới hạn cứng H1 730 ngày, M15 60 ngày |
| Twelve Data / Polygon / Alpha Vantage / Tiingo | Truy cập được, **chỉ thiếu API key** |

## 1.10. Ghi chú về FinBERT
FinBERT phân loại sắc thái trên **văn bản** tin. GDELT DOC API chỉ trả chuỗi tổng hợp (khối lượng, tone trung bình), không trả toàn văn ở quy mô 9 năm. Trong triển khai này, vai trò "cường độ tin tức FinBERT–GDELT" ở Bước 4 được đảm nhiệm bởi **cường độ đưa tin và tone GDELT đã chuẩn hóa**. Muốn dùng đúng FinBERT cần tải danh sách bài (`mode=artlist`) rồi chấm điểm từng tiêu đề.
