"""
demo.py - Chạy thử chatbot tra cứu luật giao thông với kho dữ liệu tự cập nhật.

Cách dùng:
  1. Tạo thư mục data/ cạnh file này, chép traffic_law_corpus.json vào đó và đổi tên thành
     01_nd168_2024.json (file bản vá sau này đặt tên 02_..., 03_...: file có số lớn hơn thắng).
  2. Chạy:  python demo.py
  3. Gõ câu hỏi, ví dụ:  vượt đèn đỏ xe máy phạt bao nhiêu
  4. Trong lúc chương trình đang chạy, hãy mở file JSON trong data/, sửa một số
     tiền rồi lưu lại, hoặc thả thêm một file bản vá vào data/. Chương trình sẽ tự
     báo "Kho dữ liệu đã cập nhật" mà không cần khởi động lại.

Lệnh đặc biệt: /stats  /errors  /reload  /quit
"""

import sys
import time

from law_store import LawStore, describe

# Dưới ngưỡng này thì bot trả lời "không tìm thấy" thay vì đoán bừa.
# Đây là một tham số quan trọng để bạn thử nghiệm trong báo cáo nghiên cứu.
NOT_FOUND_THRESHOLD = 0.15
# Cấu hình tốt nhất tìm được trong các thí nghiệm (xem nhat_ky_thi_nghiem.md):
KEYWORD_WEIGHT = 5      # v2: trọng số của keywords (cần dữ liệu có trường "keywords")
MIN_COVERAGE = 0.6      # v3: độ phủ tối thiểu giữa câu hỏi và bản ghi, thấp hơn thì từ chối


def on_event(e):
    print("\n--- Kho dữ liệu đã cập nhật (phiên bản", e["version"], ") ---")
    if e["added"]:
        print("  Thêm:", ", ".join(e["added"]))
    if e["changed"]:
        print("  Sửa:", ", ".join(e["changed"]))
    if e["removed"]:
        print("  Gỡ:", ", ".join(e["removed"]))
    for path, msg in e["errors"].items():
        print(f"  LỖI file {path}: {msg}  (đang giữ dữ liệu cũ)")
    for w in e["warnings"]:
        print("  Cảnh báo:", w)
    print("Hỏi> ", end="", flush=True)


def answer(store, question):
    results = [r for r in store.search(question, top_k=3)
               if r["score"] >= NOT_FOUND_THRESHOLD and r["coverage"] >= MIN_COVERAGE]
    if not results:
        return "Mình không tìm thấy quy định phù hợp trong dữ liệu hiện có."
    out = [describe(results[0]["record"])]
    others = [r["record"]["behavior"] for r in results[1:]]
    if others:
        out.append("\nCó thể bạn cũng muốn hỏi về: " + "; ".join(others))
    out.append("\n(Thông tin chỉ mang tính tham khảo, không phải tư vấn pháp lý.)")
    return "\n".join(out)


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    store = LawStore(data_dir, poll_seconds=2.0, keyword_weight=KEYWORD_WEIGHT)
    store.add_listener(on_event)
    store.start_watching()

    s = store.stats()
    print(f"Đã nạp {s['records']} bản ghi từ {s['files']} file trong '{data_dir}' (phiên bản {s['version']}).")
    if s["records"] == 0:
        print("Chưa có dữ liệu: hãy chép file .json vào thư mục", data_dir, "(chương trình sẽ tự nạp).")
    print("Gõ câu hỏi, hoặc /stats /errors /reload /quit\n")

    while True:
        try:
            q = input("Hỏi> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q == "/quit":
            break
        if q == "/stats":
            print(store.stats())
        elif q == "/errors":
            print(store.errors or "Không có lỗi.", *store.warnings, sep="\n")
        elif q == "/reload":
            print("Có thay đổi." if store.check_for_changes() else "Không có thay đổi.")
        else:
            t0 = time.perf_counter()
            print(answer(store, q))
            print(f"({(time.perf_counter() - t0) * 1000:.1f} ms)")
    store.stop_watching()


if __name__ == "__main__":
    main()
