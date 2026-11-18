# Nhật ký thí nghiệm

Tập câu hỏi: `questions_draft_claude.csv`, split = dev (38 câu: 32 có đáp án, 6 ngoài phạm vi)
Ngưỡng "không tìm thấy": 0,15 (cố định cho cả ba phiên bản)

| Phiên bản | Thay đổi | Top-1 | Top-3 | MRR | Từ chối đúng | Từ chối nhầm | Đúng tổng thể |
|---|---|---|---|---|---|---|---|
| v0 | Ban đầu (TF-IDF) | 75,0% | 84,4% | 0,792 | 33,3% | 0% | 68,4% |
| v1 | Thêm keywords đời thường (gộp chung vào văn bản) | 87,5% | 100,0% | 0,932 | 33,3% | 0% | 78,9% |
| v2 | Keywords có chỉ mục riêng, w = 5 | 96,9% | 96,9% | 0,969 | 0% | 0% | 81,6% |

## Cách chạy từng phiên bản

- v0: `python evaluate.py questions_draft_claude.csv --split dev --repeat 5 --out results_v0.csv` (thư mục `data`)
- v1: `python evaluate.py questions_draft_claude.csv --data data_v1 --split dev --repeat 5 --out results_v1.csv`
- v2: `python evaluate.py questions_draft_claude.csv --data data_v1 --split dev --repeat 5 --kw-weight 5 --out results_v2.csv`

## Ghi chú v1
- Sửa được: C015, C017, C027, C039, C059.
- Thoái lui: C013 ("xe máy 110cc không có bằng lái") từ đúng thành sai, vì từ khóa "bằng lái" được thêm đều cho ba bản ghi giấy phép lái xe.
- Vẫn sai: C003, C009, C075 (thiếu từ hoặc xếp hạng sai), C023, C037, C061, C063 (câu ngoài phạm vi vẫn bị trả lời).

## Ghi chú v2
- w = 5 được chọn trên tập dev: từ w = 5 trở lên top-1 không đổi (31/32), nên chọn giá trị nhỏ nhất của đoạn bằng phẳng.
- Sửa được: C003, C009 và lỗi thoái lui C013. Trong các câu có đáp án chỉ còn C075 sai.
- Top-3 giảm từ 100% xuống 96,9% (C075 không còn nằm trong ba kết quả đầu).
- Khả năng từ chối giảm từ 2/6 xuống 0/6: khi w tăng, thang điểm thay đổi nên ngưỡng 0,15 không còn phù hợp (ví dụ "Cách nộp thuế thu nhập cá nhân" được 0,97 điểm).
- Không chọn tổ hợp (w, ngưỡng) chỉ vì từ chối đúng 6/6 trên 6 câu ngoài phạm vi: dễ quá khớp. Xử lý việc từ chối bằng một thí nghiệm riêng (v3).
- Thời gian trả lời đo trên máy cá nhân dao động lớn giữa các lần chạy (0,2 ms đến 2 ms), chỉ mang tính tham khảo.

## Việc tiếp theo
- v3: cải thiện việc từ chối bằng độ phủ của câu hỏi so với bản ghi tìm được.
- Đo lại v0, v1, v2 trên câu hỏi của bạn bè (Google Form) khi có.
