# Cấu trúc thư mục `src/`

| Thư mục | Nội dung |
|---|---|
| `common.py`, `indicators.py`, `_duong_dan.py` | Tiện ích dùng chung cho toàn dự án |
| `thu_thap/` | Bước 1 — thu thập dữ liệu từ các nguồn |
| `quy_trinh/` | Bước 2 → 10 của quy trình mười bước |
| `delta_ohlc/` | Gói pipeline hồi quy delta OHLC đa mục tiêu |
| `baseline/` | Chiến lược nền ba tầng: phân định chế độ + Scalping / Swing / Position |
| `kiem_dinh/` | Các thí nghiệm kiểm chứng (weekend gap, độ nhạy, so sánh phương pháp) |
| `bao_cao/` | Sinh báo cáo .docx |
| `run_delta_pipeline.py` | Điểm chạy chính của pipeline delta OHLC |

Mọi tệp trong thư mục con bắt đầu bằng `import _duong_dan` để nạp đúng đường dẫn.
