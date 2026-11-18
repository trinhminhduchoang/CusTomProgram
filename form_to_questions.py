"""
form_to_questions.py - Biến câu trả lời Google Form (hoặc file .txt) thành questions.csv.

Cách 1 - từ Google Form:
    Google Form -> tab "Câu trả lời" -> dấu ba chấm -> "Tải câu trả lời xuống (.csv)"
    python form_to_questions.py "Ten file tai ve.csv"

Cách 2 - từ file .txt (bạn bè nhắn tin cho bạn, bạn dán vào), mỗi dòng một câu:
    Tên người hỏi | câu hỏi
    python form_to_questions.py cau_hoi.txt

Kết quả: questions.csv, đã điền sẵn q_id, câu hỏi, người hỏi, tình huống (ở cột notes),
gợi ý style_tag=no_diacritics khi câu hỏi gõ không dấu, và chia ngẫu nhiên dev/test 50/50.
Bạn chỉ còn phải điền: expected_ids, answerable (mặc định yes) và style_tag còn trống.
"""

import csv
import random
import sys
import unicodedata

SEED = 42  # cố định để chia dev/test không đổi giữa các lần chạy


def has_diacritics(text):
    return any(unicodedata.category(c) == "Mn" for c in unicodedata.normalize("NFD", text.replace("đ", "d")))


def read_form_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        name_col = next((i for i, h in enumerate(header) if "tên" in h.lower() or "ten" in h.lower() or "name" in h.lower()), None)
        skip = {0} if header and ("dấu thời gian" in header[0].lower() or "timestamp" in header[0].lower()) else set()
        if name_col is not None:
            skip.add(name_col)
        for line in reader:
            asker = line[name_col].strip() if name_col is not None and name_col < len(line) else "?"
            for i, cell in enumerate(line):
                if i in skip or not cell.strip():
                    continue
                rows.append({"asker": asker, "question": " ".join(cell.split()), "scenario": header[i].strip()[:80]})
    return rows


def read_txt(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if "|" not in line:
                continue
            asker, question = line.split("|", 1)
            if question.strip():
                rows.append({"asker": asker.strip() or "?", "question": " ".join(question.split()), "scenario": ""})
    return rows


def main():
    if len(sys.argv) < 2:
        sys.exit("Cách dùng: python form_to_questions.py <file .csv của Google Form hoặc file .txt>")
    src = sys.argv[1]
    rows = read_txt(src) if src.lower().endswith(".txt") else read_form_csv(src)
    if not rows:
        sys.exit("Không đọc được câu hỏi nào. Kiểm tra lại file.")

    random.Random(SEED).shuffle(rows)  # xáo trộn rồi xen kẽ dev/test để hai tập cân bằng
    with open("questions.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["q_id", "question", "asker", "style_tag", "expected_ids", "answerable", "split", "notes"])
        for n, r in enumerate(rows, start=1):
            tag = "" if has_diacritics(r["question"]) else "no_diacritics"
            w.writerow([f"Q{n:03d}", r["question"], r["asker"], tag, "", "yes",
                        "dev" if n % 2 else "test", r["scenario"]])
    print(f"Đã tạo questions.csv với {len(rows)} câu hỏi (dev: {(len(rows) + 1) // 2}, test: {len(rows) // 2}).")
    print("Bước tiếp theo: mở file, điền expected_ids cho từng câu (và sửa answerable thành no nếu câu nằm ngoài dữ liệu).")


if __name__ == "__main__":
    main()
