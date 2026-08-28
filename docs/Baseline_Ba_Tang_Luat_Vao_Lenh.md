# CHIẾN LƯỢC NỀN BA TẦNG — LUẬT VÀO LỆNH VÀ THỐNG KÊ TÍN HIỆU

**Ngày chạy:** 28/08/2026 · **Mã nguồn:** `src/baseline/` + `src/run_baseline_thong_ke.py`
**Tập dữ liệu:** XAU/USD Dukascopy, D1 / H1 / M15

---

## 1. Kiến trúc ba tầng

Chiến lược Tín hiệu Kỹ thuật đóng vai trò nền để đối chứng với chiến lược Trí tuệ Nhân tạo. Đây không phải một quy tắc đơn lẻ mà là hệ thống ba tầng:

| Tầng | Mô-đun | Trách nhiệm |
|---|---|---|
| 1 | `baseline/che_do.py` | Phân định chế độ thị trường |
| 2 | `baseline/chien_luoc.py` | Luật vào lệnh riêng cho từng chế độ |
| 3 | `baseline/thong_ke.py` | Quản trị thoát lệnh và thống kê |

---

## 2. Tầng 1 — Phân định chế độ thị trường

Bốn chế độ, phân định bằng ADX14 và tương quan vị trí của EMA50 / EMA200:

| Chế độ | Điều kiện |
|---|---|
| **Uptrend** | ADX14 ≥ 25 **và** EMA50 > EMA200 **và** Close > EMA50 |
| **Downtrend** | ADX14 ≥ 25 **và** EMA50 < EMA200 **và** Close < EMA50 |
| **Sideway** | ADX14 < 25 |
| **Transition** | ADX14 ≥ 25 nhưng cấu trúc EMA và vị trí giá không đồng thuận |

Ngưỡng ADX = 25 là ngưỡng **phân định chế độ**. Chiến lược Position dùng ngưỡng cao hơn (28) — xem mục 3c.

### Phân bố chế độ thực tế

| Khung | Sideway | Uptrend | Downtrend | Transition |
|---|---|---|---|---|
| D1 (2 838 nến) | 52,47 % | 28,68 % | 8,25 % | 10,57 % |
| H1 (65 126 nến) | 50,17 % | 19,71 % | 15,04 % | 15,08 % |
| M15 (184 882 nến) | 55,91 % | 16,74 % | 14,88 % | 12,47 % |

ADX trung bình theo chế độ xác nhận tầng phân định hoạt động đúng: Sideway 17,9–18,4; Uptrend 35,8–37,9; Downtrend 35,5–37,3; Transition 32,0–33,5.

Tỷ trọng Uptrend vượt trội Downtrend ở khung D1 (28,7 % so với 8,3 %) phản ánh đúng thực tế 2015–2025 là chu kỳ tăng dài của vàng.

---

## 3. Tầng 2 — Luật vào lệnh của ba chiến lược

### a) Scalping — EMA8, EMA21, RSI7

**MUA** khi thỏa mãn đồng thời:
1. Chế độ thị trường là **Uptrend hoặc Sideway**
2. `Close > EMA8 > EMA21`
3. `RSI7 < 65` **và** RSI7 tại nến hiện tại không thấp hơn RSI7 của nến liền trước

**BÁN** khi thỏa mãn đồng thời:
1. Chế độ thị trường là **Downtrend hoặc Sideway**
2. `Close < EMA8 < EMA21`
3. `RSI7 > 35` **và** RSI7 tại nến hiện tại không cao hơn RSI7 của nến liền trước

**Bộ lọc rủi ro:** hủy toàn bộ tín hiệu từ **18:00 UTC thứ Sáu**.

Điều kiện thứ ba không dùng ngưỡng quá mua – quá bán kinh điển 70/30 mà dùng cặp ngưỡng lệch **65/35**, kết hợp điều kiện đạo hàm của RSI. Thiết kế này bảo đảm hệ thống chỉ vào lệnh khi động lượng vẫn còn dư địa và đang vận động đúng chiều, tránh mua vào đúng đỉnh của chỉ báo.

### b) Swing — EMA Ribbon, MACD(12,26,9), RSI14, Bollinger Bands

Đây là chiến lược duy nhất **phân tầng luật theo từng chế độ**:

| Chế độ | Luật |
|---|---|
| **Uptrend** | Chỉ được phép MUA: `EMA10 > EMA20 > EMA50` và MACD Histogram **cắt lên** mức 0 |
| **Downtrend** | Chỉ được phép BÁN: `EMA10 < EMA20 < EMA50` và MACD Histogram **cắt xuống** mức 0 |
| **Sideway** | Hồi quy về trung bình theo chiều ngược: MUA khi `Close ≤ Bollinger dưới` và `RSI14 < 30`; BÁN khi `Close ≥ Bollinger trên` và `RSI14 > 70` |
| **Transition** | Đứng ngoài thị trường hoàn toàn |

**Bộ lọc rủi ro:** hủy toàn bộ tín hiệu từ **20:00 UTC thứ Sáu**.

Điểm đáng chú ý nhất về mặt thiết kế: **cùng một chỉ báo RSI được vận dụng theo hai logic trái ngược tùy chế độ**. Trong pha xu hướng, RSI cao được hiểu là dấu hiệu của sức mạnh nên hệ thống mua thuận chiều. Trong pha đi ngang, RSI cao lại được hiểu là trạng thái quá mua nên hệ thống bán ngược chiều. Đây là lý do gọi đây là chiến lược **thích ứng theo chế độ**, không phải chiến lược chỉ báo thuần túy.

Điều kiện MACD cắt mức 0 là điều kiện dạng **SỰ KIỆN**, không phải dạng **TRẠNG THÁI**: nó chỉ đúng tại đúng một nến duy nhất trong mỗi chu kỳ động lượng. Hệ quả là Swing có độ phủ tín hiệu rất thấp.

### c) Position — EMA50, EMA200, ADX14

- **MUA:** `Close > EMA50 > EMA200` và `ADX14 ≥ 28`
- **BÁN:** `Close < EMA50 < EMA200` và `ADX14 ≥ 28`
- **Không áp bộ lọc cuối tuần** vì bản chất chiến lược là giữ lệnh trong nhiều tuần.

Ngưỡng ADX được nâng lên 28, cao hơn mức 25 dùng để phân định chế độ, nhằm chỉ tham gia những xu hướng thực sự mạnh. Đây là luật đơn giản nhất trong ba chiến lược và được giữ đơn giản một cách cố ý để làm mốc đối chứng.

---

## 4. Tầng 3 — Quản trị thoát lệnh

Mô phỏng tuần tự với quy tắc **một vị thế tại một thời điểm**. Thoát lệnh khi chạm chốt lời (2,0 × ATR14), chạm cắt lỗ (1,5 × ATR14), hoặc hết chân trời.

---

## 5. Bảng 2.4 — Thống kê tín hiệu vào lệnh

### Khung H1 (65 126 nến, 2015-01-01 → 2025-12-31)

| Chiến lược | Tín hiệu MUA | Tín hiệu BÁN | Tổng tín hiệu | Độ phủ | Số lệnh thực mở |
|---|---|---|---|---|---|
| Scalping | 5 248 | 4 637 | 9 885 | 15,18 % | 3 015 |
| Swing | 692 | 826 | 1 518 | 2,33 % | 1 032 |
| Position | 10 531 | 8 046 | 18 577 | 28,52 % | 2 378 |

### Khung D1 (2 838 nến)

| Chiến lược | Tín hiệu MUA | Tín hiệu BÁN | Tổng tín hiệu | Độ phủ | Số lệnh thực mở |
|---|---|---|---|---|---|
| Scalping | 239 | 194 | 433 | 15,26 % | 125 |
| Swing | 36 | 29 | 65 | 2,29 % | 43 |
| Position | 670 | 187 | 857 | 30,20 % | 143 |

### Khung M15 (184 882 nến)

| Chiến lược | Tín hiệu MUA | Tín hiệu BÁN | Tổng tín hiệu | Độ phủ | Số lệnh thực mở |
|---|---|---|---|---|---|
| Scalping | 16 648 | 14 653 | 31 301 | 16,93 % | 8 408 |
| Swing | 1 566 | 1 991 | 3 557 | 1,92 % | 2 511 |
| Position | 24 807 | 22 387 | 47 194 | 25,53 % | 6 301 |

### Chỉ tiêu bổ sung

| Khung | Chiến lược | Số nến trung bình / tín hiệu | Tỷ lệ tín hiệu thành lệnh | Bị bộ lọc cuối tuần cắt |
|---|---|---|---|---|
| H1 | Scalping | 6,6 | 30,50 % | 2,92 % |
| H1 | Swing | 42,9 | 67,98 % | 0,39 % |
| H1 | Position | 3,5 | 12,80 % | 0 % |
| M15 | Scalping | 5,9 | 26,86 % | 3,14 % |
| M15 | Swing | 52,0 | 70,59 % | 0,36 % |
| M15 | Position | 3,9 | 13,35 % | 0 % |

---

## 6. Kiểm chứng tầng phân định chế độ

Phân rã tín hiệu Swing theo từng chế độ:

| Khung | Chế độ | Tín hiệu MUA | Tín hiệu BÁN | Tổng |
|---|---|---|---|---|
| **H1** | Uptrend | 295 | **0** | 295 |
| | Downtrend | **0** | 221 | 221 |
| | Sideway | 397 | 605 | 1 002 |
| | Transition | **0** | **0** | **0** |
| **D1** | Uptrend | 17 | **0** | 17 |
| | Downtrend | **0** | 6 | 6 |
| | Sideway | 19 | 23 | 42 |
| | Transition | **0** | **0** | **0** |
| **M15** | Uptrend | 637 | **0** | 637 |
| | Downtrend | **0** | 600 | 600 |
| | Sideway | 929 | 1 391 | 2 320 |
| | Transition | **0** | **0** | **0** |

**Ba điều kiện nghiệm thu đều đạt trên cả ba khung:**
1. Không có tín hiệu BÁN nào lọt vào chế độ Uptrend
2. Không có tín hiệu MUA nào lọt vào chế độ Downtrend
3. Không có lệnh nào phát sinh trong chế độ Transition

Điều này xác nhận tầng phân định chế độ vận hành chính xác. Kiểm chứng được tự động hóa trong `run_baseline_thong_ke.py` và in ra kết luận ở mỗi lần chạy.

---

## 7. Độ phủ tín hiệu khác số lệnh thực mở

Cần lưu ý sự khác biệt giữa **độ phủ tín hiệu** và **số lệnh thực tế được mở**, đặc biệt ở chiến lược Position: 18 577 tín hiệu nhưng chỉ 2 378 lệnh được mở (12,80 %).

Nguyên nhân: điều kiện của Position thuộc dạng **TRẠNG THÁI** nên tín hiệu duy trì liên tục suốt cả xu hướng, trong khi quy tắc một vị thế tại một thời điểm khiến mọi tín hiệu phát sinh khi đang có lệnh mở đều bị bỏ qua.

Ngược lại, Swing có tỷ lệ chuyển đổi cao nhất (67,98 % ở H1) vì điều kiện MACD cắt mức 0 thuộc dạng **SỰ KIỆN** — mỗi tín hiệu là một thời điểm riêng biệt, hiếm khi trùng với thời gian đang giữ lệnh.

Thứ tự tỷ lệ chuyển đổi nhất quán trên cả ba khung: **Swing (66–71 %) > Scalping (27–31 %) > Position (13–17 %)**.

---

## 8. Đối chiếu với bảng tham chiếu của nhóm

Bảng 2.4 trong bản thảo của nhóm dựa trên 62 592 nến H1. Tập dữ liệu hiện tại có 65 126 nến H1 (Dukascopy, 2015-01-01 → 2025-12-31), nên các con số tuyệt đối khác nhau. Đối chiếu tỷ lệ:

| Chỉ tiêu | Bản thảo nhóm | Kết quả chạy lại | Chênh lệch |
|---|---|---|---|
| Số nến H1 | 62 592 | 65 126 | +4,0 % |
| Độ phủ Scalping | 10,60 % | 15,18 % | +4,6 điểm |
| Độ phủ Swing | 1,95 % | 2,33 % | +0,4 điểm |
| Độ phủ Position | 26,89 % | 28,52 % | +1,6 điểm |
| Số nến / tín hiệu Swing | 51 | 42,9 | −16 % |

Ba nguyên nhân chênh lệch:
1. **Tập dữ liệu khác nhau** — nguồn và giai đoạn không trùng khớp hoàn toàn.
2. **Định nghĩa Transition chưa được đặc tả trong bản thảo.** Tôi định nghĩa là "ADX ≥ 25 nhưng cấu trúc EMA và vị trí giá không đồng thuận", chiếm 15,08 % số nến ở H1. Một định nghĩa khác sẽ dịch chuyển ranh giới Sideway và thay đổi độ phủ Scalping — đây là nguyên nhân chính của chênh lệch 4,6 điểm.
3. **Quy tắc thoát lệnh chưa được đặc tả.** Tôi dùng chốt lời 2,0 × ATR14 và cắt lỗ 1,5 × ATR14; tham số khác sẽ cho số lệnh thực mở khác.

Hai hạng mục cần nhóm xác nhận để tái lập chính xác: **định nghĩa chế độ Transition** và **tham số thoát lệnh**.

---

## 9. Cách chạy lại

```bash
python src/run_baseline_thong_ke.py D1 H1 M15
```

Tệp kết quả trong `results/tables/`: `baseline_bang_2_4_{tf}.csv`, `baseline_bang_2_4_tong_hop.csv`, `baseline_che_do_{tf}.csv`, `baseline_swing_theo_che_do_{tf}.csv`, `baseline_tin_hieu_{tf}.csv`.
