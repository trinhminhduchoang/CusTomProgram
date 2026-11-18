# Nhật ký thí nghiệm

## Bảng chính: tập dev mở rộng (`questions_draft_claude_v2.csv`, split = dev)
62 câu: 32 có đáp án, 30 ngoài phạm vi (6 câu cũ + 24 câu mới, trong đó 8 câu "data_gap": luật có nhưng dữ liệu chưa có).
Ngưỡng điểm "không tìm thấy" = 0,15 cho mọi phiên bản.

| Phiên bản | Thay đổi | Top-1 | Top-3 | MRR | Từ chối đúng | Từ chối nhầm | Đúng tổng thể |
|---|---|---|---|---|---|---|---|
| v0 | Ban đầu (TF-IDF) | 75,0% | 84,4% | 0,792 | 12/30 (40,0%) | 0% | 36/62 (58,1%) |
| v1 | Thêm keywords (gộp chung vào văn bản) | 87,5% | 100,0% | 0,932 | 15/30 (50,0%) | 0% | 43/62 (69,4%) |
| v2 | Keywords chỉ mục riêng, w = 5 | 96,9% | 96,9% | 0,969 | 1/30 (3,3%) | 0% | 32/62 (51,6%) |
| v3 | v2 + độ phủ tối thiểu 0,6 | 96,9% | 96,9% | 0,969 | 25/30 (83,3%) | 0% | 56/62 (90,3%) |

## Cách chạy từng phiên bản (thay `--split dev` bằng `--split test` chỉ ở bước cuối)
- v0: `python evaluate.py questions_draft_claude_v2.csv --split dev --repeat 5 --out results_v0.csv`
- v1: `python evaluate.py questions_draft_claude_v2.csv --data data_v1 --split dev --repeat 5 --out results_v1.csv`
- v2: `python evaluate.py questions_draft_claude_v2.csv --data data_v1 --split dev --repeat 5 --kw-weight 5 --out results_v2.csv`
- v3: `python evaluate.py questions_draft_claude_v2.csv --data data_v1 --split dev --repeat 5 --kw-weight 5 --min-coverage 0.6 --out results_v3.csv`

## Bảng cũ: tập dev 38 câu (`questions_draft_claude.csv`, 32 có đáp án, 6 ngoài phạm vi)
| Phiên bản | Top-1 | Top-3 | MRR | Từ chối đúng | Đúng tổng thể |
|---|---|---|---|---|---|
| v0 | 75,0% | 84,4% | 0,792 | 2/6 | 68,4% |
| v1 | 87,5% | 100,0% | 0,932 | 2/6 | 78,9% |
| v2 | 96,9% | 96,9% | 0,969 | 0/6 | 81,6% |

Bài học: với chỉ 6 câu ngoài phạm vi, v2 trông tốt hơn v1 ("đúng tổng thể" 81,6% so với 78,9%). Khi tăng lên 30 câu ngoài phạm vi, v2 lại thấp hơn v1 (51,6% so với 69,4%). Số câu ngoài phạm vi quá ít che mất việc v2 làm hỏng khả năng từ chối.

## Ghi chú v1
- Sửa được: C015, C017, C027, C039, C059. Thoái lui: C013 (từ khóa "bằng lái" thêm đều cho 3 bản ghi giấy phép lái xe).

## Ghi chú v2
- w = 5 chọn trên tập dev: từ w = 5 trở lên top-1 không đổi (31/32), chọn giá trị nhỏ nhất của đoạn bằng phẳng.
- Sửa được C003, C009 và lỗi thoái lui C013; còn sai C075 (typo, "lái xe máy" kéo về nhóm giấy phép lái xe).
- Khả năng từ chối giảm mạnh: thang điểm thay đổi nên ngưỡng 0,15 không còn phù hợp.

## Ghi chú v3
- Độ phủ = tỉ lệ "từ nội dung" của câu hỏi (bỏ số và từ chức năng như "bị phạt bao nhiêu") có trong bản ghi tìm được.
- Bảng quét ngưỡng độ phủ (dev mở rộng, v2): 0,4 -> 46,7% từ chối đúng; 0,5 -> 56,7%; **0,6 -> 83,3% (0 câu bị từ chối nhầm)**; 0,7 -> 86,7% nhưng 12,5% từ chối nhầm; 0,8 -> 18,8% từ chối nhầm.
- Chọn 0,6 vì cho "đúng tổng thể" cao nhất mà không từ chối nhầm câu nào. Lưu ý: kết quả nhảy vọt giữa 0,5 và 0,6 (56,7% lên 83,3%), tức ngưỡng nằm sát một "vách đá", cần kiểm tra lại trên câu hỏi của bạn bè.
- Sau khi thấy C059 ("theo nghị định 100") bị từ chối nhầm, thêm "theo", "luật", "nghị", "định" vào danh sách từ chức năng: đây là điều chỉnh sau khi xem lỗi dev, ghi lại để minh bạch.
- Còn sai 6 câu: C075 (xếp hạng), C037, N019, N022 (data_gap: luật có nhưng dữ liệu chưa có, bot trả lời bản ghi gần nghĩa), N015, N016 (câu về "phạt nguội", "đăng ký biển số" có nhiều từ trùng với dữ liệu). Độ phủ không giải được nhóm này: cần thêm dữ liệu hoặc nhận diện ý định hỏi.
- Lỗi tìm thấy khi làm: quét ngưỡng bằng `i * 0.1` cho giá trị 0,6000000000000001 thay vì 0,6 (lỗi số thực), làm lệch kết quả; đã sửa bằng `round()`.

## Việc tiếp theo
- Đo v0 đến v3 trên câu hỏi của bạn bè (Google Form), split = test, và tách riêng bảng này khỏi bảng dev.
- Phân tích các câu sai; không chỉnh bot dựa trên tập test.
