# Chatbot tra cứu luật giao thông

Đây là chatbot Python để tra cứu mức xử phạt vi phạm giao thông từ dữ liệu JSON, có giao diện cửa sổ và dòng lệnh.

Tài liệu dành cho người dùng: [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md)

## Cấu trúc dự án

```text
Customprogram-Law/
├── law_store.py
├── demo.py
├── gui.py
├── evaluate.py
├── questions_draft_claude.csv
├── results_v0.csv
├── README.md
├── HUONG_DAN_SU_DUNG.md
└── data/
    └── traffic_law_corpus.json
```

Chương trình không yêu cầu thư viện Python ngoài.

## Chạy nhanh

```powershell
# Chạy chatbot
python demo.py

# Mở giao diện cửa sổ để thử câu hỏi
python gui.py

# Chấm tập phát triển
python evaluate.py questions_draft_claude.csv --split dev

# Chấm tập test chỉ ở bước cuối
python evaluate.py questions_draft_claude.csv --split test
```

## Workflow nạp dữ liệu

```text
Khởi tạo LawStore
        │
        ▼
Tìm và đọc mọi file *.json trong data/
        │
        ▼
Kiểm tra JSON và từng bản ghi
        │
        ├── Hợp lệ       → giữ bản ghi
        └── Lỗi dữ liệu   → bỏ bản ghi hoặc giữ bản ghi cũ
        │
        ▼
Gộp các file theo thứ tự tên
        │
        ▼
Lọc theo trạng thái done/needs_238_check
        │
        ▼
Xây dựng lại chỉ mục TF-IDF
        │
        ▼
Cập nhật kho và thông báo thay đổi
```

## Workflow tìm kiếm

```text
Câu hỏi người dùng
        │
        ▼
Chuẩn hóa chữ thường và bỏ dấu
        │
        ▼
Tách từ đơn và tạo cụm hai từ
        │
        ▼
Tính vector TF-IDF của câu hỏi
        │
        ▼
Tính điểm tương đồng với từng bản ghi
        │
        ▼
Suy đoán loại xe
        │
        ▼
Tăng điểm xe cùng loại, giảm điểm xe khác loại
        │
        ▼
Sắp xếp và trả tối đa 3 kết quả
```

## Workflow đánh giá

```text
evaluate.py
    │
    ▼
Đọc và lọc câu hỏi theo split
    │
    ▼
Gọi LawStore.search() cho từng câu
    │
    ▼
Áp dụng ngưỡng không tìm thấy
    │
    ▼
Tính Top-1, Top-3, MRR và độ trễ
    │
    ▼
In báo cáo và lưu results.csv
```

## Luồng cập nhật tự động

`LawStore` khởi luồng nền, quét thư mục `data/` mỗi 2 giây.

```text
So sánh mtime và kích thước file
        │
        ▼
File không đổi → không nạp lại
File JSON hợp lệ → nạp và xây dựng lại index
File JSON lỗi   → giữ dữ liệu cũ và lưu lỗi
        │
        ▼
Gửi sự kiện added/changed/removed cho listener
```

## Phân tích từng module

### `law_store.py`

- [Các hằng và cấu hình](/d%3A/COS10009/Customprogram-Law/law_store.py:37): trạng thái hoạt động, trường bắt buộc và từ khóa nhận diện loại xe.
- [normalize()](/d%3A/COS10009/Customprogram-Law/law_store.py:53): chuyển chữ thường, bỏ dấu và chuẩn hóa `đ`.
- [tokenize()](/d%3A/COS10009/Customprogram-Law/law_store.py:60): tạo từ đơn và bigram.
- [validate_record()](/d%3A/COS10009/Customprogram-Law/law_store.py:70): kiểm tra bản ghi JSON.
- [search_text_of()](/d%3A/COS10009/Customprogram-Law/law_store.py:90): tạo chuỗi dùng để lập index.
- [TfidfIndex](/d%3A/COS10009/Customprogram-Law/law_store.py:101): tính TF-IDF và độ tương đồng.
- [LawStore](/d%3A/COS10009/Customprogram-Law/law_store.py:142): quản lý file, kho dữ liệu, luồng theo dõi và tìm kiếm.
- [check_for_changes()](/d%3A/COS10009/Customprogram-Law/law_store.py:190): phát hiện file thêm/sửa/xóa.
- [_rebuild()](/d%3A/COS10009/Customprogram-Law/law_store.py:244): gộp bản ghi, tạo index và phát thông báo.
- [search()](/d%3A/COS10009/Customprogram-Law/law_store.py:301): tìm kết quả và điều chỉnh điểm theo loại xe.
- [detect_vehicle()](/d%3A/COS10009/Customprogram-Law/law_store.py:316): suy đoán xe máy hoặc ô tô.
- [describe()](/d%3A/COS10009/Customprogram-Law/law_store.py:347): định dạng câu trả lời kèm căn cứ pháp lý.

### `demo.py`

- Tạo `LawStore`.
- Bật luồng theo dõi dữ liệu.
- Nhận câu hỏi người dùng.
- Áp dụng ngưỡng `0.15`.
- Hiển thị luật phù hợp nhất và thông báo cập nhật.

### `evaluate.py`

- Đọc câu hỏi từ CSV.
- Lọc câu theo `dev`, `test` hoặc `all`.
- Chạy bot nhiều lần để đo thời gian.
- Tính Top-1, Top-3, MRR và tỷ lệ từ chối.
- Lưu kết quả từng câu vào CSV.

## Cơ chế hợp nhất dữ liệu

Các file JSON được nạp theo thứ tự tên. File đứng sau được ưu tiên:

```text
01_nd168_2024.json
02_nd238_2026.json
03_patch.json
```

Quy tắc hợp nhất:

```text
id mới             → thêm bản ghi
cùng id, khác dữ liệu → ghi đè bản ghi cũ
status = removed   → gỡ bản ghi
status = todo      → không đưa vào kho
```

Chi tiết cấu trúc bản ghi và cách sửa dữ liệu được mô tả trong [hướng dẫn sử dụng](HUONG_DAN_SU_DUNG.md).

## Cấu trúc bản ghi tối thiểu

```json
{
  "id": "gt01_vuot_den_do_xe_may",
  "status": "done",
  "behavior": "Vượt đèn đỏ",
  "vehicle_type": "xe_may",
  "fine_min": 400000,
  "fine_max": 600000,
  "legal_refs": [],
  "text": "Nội dung điều luật",
  "keywords": ["đèn đỏ", "tín hiệu"]
}
```

Trường bắt buộc:

```text
id
status
behavior
vehicle_type
fine_min
fine_max
legal_refs
text
```

Trạng thái được chấp nhận:

```text
todo             Chưa hoàn thành
done             Đã hoàn thành và đang sử dụng
needs_238_check  Chờ đối chiếu Nghị định 238/2026
removed          Gỡ khỏi kho
```

Chỉ `done` và `needs_238_check` được đưa vào index tìm kiếm.

## Đánh giá

Các chỉ số chính:

- **Top-1:** kết quả đứng đầu có đúng không.
- **Top-3:** bản ghi đúng có trong ba kết quả không.
- **MRR:** trung bình nghịch đảo vị trí kết quả đúng.
- **Từ chối nhầm:** câu có đáp án nhưng bot từ chối.
- **Từ chối đúng:** câu ngoài phạm vi và bot từ chối.
- **Đúng tổng thể:** tổng câu bot trả lời đúng.

Luồng phát triển được khuyến nghị:

1. Chạy `dev`.
2. Phân tích câu sai.
3. Bổ sung `keywords`, sửa dữ liệu hoặc kiểm tra TF-IDF.
4. Chạy lại `dev`.
5. Dùng `--sweep` để chọn ngưỡng.
6. Chỉ chạy `test` một lần ở bước cuối.
