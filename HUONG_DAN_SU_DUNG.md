# Hướng dẫn sử dụng ứng dụng tra cứu luật giao thông

Ứng dụng là chatbot giúp tra cứu mức xử phạt vi phạm giao thông trên đường bộ.

Bạn chỉ cần:

1. Mở ứng dụng.
2. Nhập câu hỏi.
3. Đọc kết quả từ chatbot.

Không cần biết lập trình.

---

## 1. Mở ứng dụng

### Mở giao diện cửa sổ

Trong Terminal của VS Code hoặc PowerShell tại thư mục ứng dụng, chạy:

```powershell
python gui.py
```

Nhập câu hỏi vào ô tìm kiếm và nhấn **Tra cứu** hoặc Enter. Giao diện cho phép
chọn thư mục dữ liệu, nạp lại dữ liệu, điều chỉnh ngưỡng từ chối và thử chế độ
keywords gộp (v0/v1) hoặc keywords riêng (v2). Để trống trọng số keywords để
dùng v0/v1; nhập số không âm để bật v2. Chọn **Nạp lại** sau khi thay đổi file
JSON để dùng dữ liệu mới.

### Cách mở bằng VS Code

1. Mở **Visual Studio Code**.
2. Chọn **File → Open Folder**.
3. Chọn thư mục chứa ứng dụng.
4. Chọn **Terminal → New Terminal**.
5. Nhập:

```powershell
python demo.py
```

6. Nhấn **Enter**.

### Cách mở bằng PowerShell

1. Mở thư mục chứa ứng dụng.
2. Nhấn chuột phải vào vùng trống.
3. Chọn **Open in Terminal**.
4. Nhập:

```powershell
python demo.py
```

Sau khi mở thành công, màn hình sẽ có dòng:

```text
Hỏi>
```

---

## 2. Đặt câu hỏi

Gõ câu hỏi sau `Hỏi>` và nhấn Enter.

Ví dụ:

```text
Hỏi> vượt đèn đỏ xe máy phạt bao nhiêu
```

```text
Hỏi> ô tô nồng độ cồn 70mg phạt bao nhiêu
```

```text
Hỏi> xe máy không đội mũ bảo hiểm bị phạt không
```

```text
Hỏi> xe máy chạy quá tốc độ 30km/h bị phạt bao nhiêu
```

Bạn có thể gõ tiếng Việt có dấu hoặc không dấu.

---

## 3. Cách hỏi để nhận kết quả tốt

Nên ghi rõ:

- Loại xe: xe máy hay ô tô.
- Hành vi: vượt đèn đỏ, nồng độ cồn, quá tốc độ...
- Điều kiện: mức cồn, mức vượt tốc độ, số người chở...

Ví dụ câu dễ hiểu:

```text
Ô tô có nồng độ cồn từ 50 đến 80 mg trong máu bị phạt bao nhiêu?
```

```text
Xe máy vượt đèn đỏ bị phạt bao nhiêu?
```

```text
Xe máy đi với tốc độ vượt mức cho phép 30 km/h bị phạt bao nhiêu?
```

Câu càng cụ thể, kết quả càng dễ khớp.

---

## 4. Đọc kết quả

Ứng dụng có thể hiển thị:

- Loại phương tiện.
- Hành vi vi phạm.
- Mức phạt tiền tối thiểu.
- Mức phạt tiền tối đa.
- Số điểm bị trừ trên giấy phép lái xe.
- Thời gian tước giấy phép lái xe.
- Điều, Khoản và Điểm của văn bản.
- Tên văn bản pháp luật.

Ví dụ:

```text
[Xe máy] Vượt đèn đỏ
  - Mức phạt: 4.000.000 đồng đến 6.000.000 đồng
  - Trừ điểm giấy phép lái xe: 4 điểm
  - Căn cứ: Nghị định 168/2024/NĐ-CP
```

Các mức phạt trong kết quả được lấy từ dữ liệu của ứng dụng.

---

## 5. Khi ứng dụng không tìm thấy câu trả lời

Ứng dụng có thể trả lời:

```text
Mình không tìm thấy quy định phù hợp trong dữ liệu hiện có.
```

Khi đó, hãy:

1. Viết lại câu ngắn gọn hơn.
2. Ghi rõ loại xe.
3. Ghi rõ hành vi vi phạm.
4. Ghi rõ mức vi phạm nếu có.

Ví dụ thay vì:

```text
Phạt sao?
```

Hãy hỏi:

```text
Xe máy vượt đèn đỏ phạt bao nhiêu?
```

---

## 6. Thoát khỏi ứng dụng

Gõ:

```text
/quit
```

Hoặc nhấn `Ctrl+C`.

---

## 7. Các lệnh hỗ trợ

Trong màn hình chatbot, bạn có thể gõ:

| Lệnh | Khi nào dùng |
|---|---|
| `/stats` | Muốn xem ứng dụng đang dùng bao nhiêu quy định |
| `/errors` | Muốn xem dữ liệu có lỗi không |
| `/reload` | Muốn kiểm tra dữ liệu vừa được cập nhật |
| `/quit` | Muốn thoát ứng dụng |

Ví dụ:

```text
Hỏi> /stats
```

```text
Hỏi> /errors
```

```text
Hỏi> /reload
```

---

## 8. Cập nhật dữ liệu khi ứng dụng đang mở

Nếu người quản trị dữ liệu sửa hoặc thêm quy định pháp luật:

1. Ứng dụng tiếp tục chạy.
2. Người quản trị lưu file dữ liệu trong thư mục `data`.
3. Đợi vài giây.
4. Ứng dụng tự nạp dữ liệu mới.

Không cần thoát rồi mở lại ứng dụng.

Khi dữ liệu cập nhật, ứng dụng có thể hiển thị:

```text
Kho dữ liệu đã cập nhật
```

Sau đó, bạn có thể tiếp tục đặt câu hỏi bình thường.

---

## 9. Không nên hỏi ứng dụng

Ứng dụng chưa hỗ trợ đầy đủ:

- Tư vấn luật chung.
- Giải thích mọi tình huống thực tế.
- Câu hỏi không liên quan đến giao thông.
- Tính toán mức phạt quá phức tạp.
- Cập nhật luật ngoài dữ liệu hiện có.

Ví dụ:

```text
Tôi nên làm gì sau vụ tai nạn?
```

```text
Giá vé xe buýt Hà Nội bao nhiêu?
```

Với các câu này, ứng dụng có thể không tìm thấy kết quả.

---

## 10. Cách đặt câu hỏi tiếng Việt

Các cách viết sau đều có thể được hiểu:

```text
Ô tô vượt đèn đỏ bị phạt bao nhiêu?
```

```text
oto vuot den do phat bao nhieu?
```

Bạn có thể gõ có dấu hoặc không dấu.

Hãy tránh viết quá ngắn hoặc thiếu loại xe:

```text
Phạt bao nhiêu?
```

```text
Nồng độ cồn thì sao?
```

---

## 11. Ví dụ hội thoại

### Ví dụ 1

```text
Hỏi> xe máy vượt đèn đỏ phạt bao nhiêu
```

```text
[Xe máy] Vượt đèn đỏ
  - Mức phạt: 4.000.000 đồng đến 6.000.000 đồng
  - Trừ điểm giấy phép lái xe: 4 điểm
```

### Ví dụ 2

```text
Hỏi> ô tô nồng độ cồn từ 50 đến 80 mg trong máu phạt bao nhiêu
```

```text
[Ô tô] Sử dụng rượu bia mức 2
  - Mức phạt: 18.000.000 đồng đến 20.000.000 đồng
```

### Ví dụ 3

```text
Hỏi> xe máy không đội mũ bảo hiểm bị phạt bao nhiêu
```

Ứng dụng sẽ tìm quy định liên quan đến mũ bảo hiểm đối với người lái xe máy.

---

## 12. Nếu ứng dụng báo lỗi

### Không nhận lệnh `python`

Thử:

```powershell
py demo.py
```

Nếu vẫn không chạy:

1. Cài Python 3.
2. Chọn **Add Python to PATH** khi cài.
3. Mở lại Terminal.
4. Chạy lại `python demo.py`.

### Không tìm thấy thư mục dữ liệu

Hãy kiểm tra trong thư mục ứng dụng có thư mục:

```text
data
```

Trong thư mục `data` cần có ít nhất một file có đuôi:

```text
.json
```

### Ứng dụng báo dữ liệu không hợp lệ

Gõ:

```text
Hỏi> /errors
```

Sau đó hỏi người quản trị dữ liệu kiểm tra file báo lỗi.

### Ứng dụng mở nhưng không trả lời

Thử:

- Gõ lại câu hỏi ngắn gọn.
- Ghi rõ loại xe.
- Ghi rõ hành vi vi phạm.
- Khởi động lại bằng `python demo.py`.

---

## 13. Lưu ý khi sử dụng

- Luật giao thông có thể thay đổi theo văn bản mới.
- Mức phạt trong ứng dụng được lấy từ dữ liệu hiện có.
- Một số quy định có thể đang chờ kiểm tra hoặc đối chiếu.
- Kết quả chỉ mang tính hỗ trợ tra cứu.
- Với trường hợp pháp lý quan trọng, hãy kiểm tra văn bản pháp luật chính thức hoặc hỏi cơ quan có thẩm quyền.
