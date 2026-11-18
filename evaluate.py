"""
evaluate.py - Chấm điểm chatbot tra cứu luật bằng bộ câu hỏi kiểm thử (questions.csv).

Cách dùng (đặt cạnh law_store.py, thư mục data/ chứa file dữ liệu):
    python evaluate.py questions.csv                      # chấm tập dev (mặc định)
    python evaluate.py questions.csv --split test         # chấm tập test (CHỈ chạy ở bước cuối!)
    python evaluate.py questions.csv --split all --sweep  # thêm bảng so sánh các ngưỡng "không tìm thấy"
    python evaluate.py questions.csv --repeat 20          # đo thời gian chính xác hơn

Các cột của questions.csv:
    q_id, question, asker, style_tag, expected_ids, answerable, split, notes
  - expected_ids : id bản ghi đúng, có thể viết ngắn (gt01) hoặc đầy đủ, nhiều id ngăn cách bằng |
  - answerable   : yes/no (no = câu hỏi nằm ngoài dữ liệu, bot nên trả lời "không tìm thấy")
  - split        : dev (dùng để chỉnh bot) hoặc test (đóng băng, chỉ chấm lúc báo cáo cuối)
  - dòng có q_id bắt đầu bằng # sẽ bị bỏ qua (dùng làm ví dụ/ghi chú)
"""

import argparse
import csv
import statistics
import sys
import time
from collections import defaultdict

from law_store import LawStore


# ----------------------------------------------------------------------------
# Đọc dữ liệu
# ----------------------------------------------------------------------------
def split_ids(text):
    return [x.strip() for x in text.replace(";", "|").replace(",", "|").split("|") if x.strip()]


def id_matches(record_id, expected):
    """expected có thể là id đầy đủ hoặc phần đầu 'gt01'."""
    short = record_id.split("_")[0]
    return any(record_id == e or short == e for e in expected)


def load_questions(path, split):
    rows, skipped = [], []
    with open(path, encoding="utf-8-sig", newline="") as f:  # utf-8-sig: file CSV xuất từ Excel/Google Sheets
        for line_no, raw in enumerate(csv.DictReader(f), start=2):
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            qid = row.get("q_id", "")
            if not qid or qid.startswith("#"):
                continue
            if split != "all" and row.get("split", "").lower() != split:
                continue
            row["answerable"] = row.get("answerable", "yes").lower() in ("yes", "y", "có", "co", "1", "true")
            row["expected"] = split_ids(row.get("expected_ids", ""))
            if not row.get("question"):
                skipped.append(f"dòng {line_no} ({qid}): thiếu câu hỏi")
                continue
            if row["answerable"] and not row["expected"]:
                skipped.append(f"dòng {line_no} ({qid}): answerable=yes nhưng thiếu expected_ids")
                continue
            rows.append(row)
    return rows, skipped


# ----------------------------------------------------------------------------
# Chạy bot và chấm điểm
# ----------------------------------------------------------------------------
def run_queries(store, rows, repeat):
    """Chạy mỗi câu hỏi 'repeat' lần để đo thời gian; trả về top-3 thô (có điểm)."""
    out = []
    for row in rows:
        times, raw = [], None
        for _ in range(repeat):
            t0 = time.perf_counter()
            raw = store.search(row["question"], top_k=3)
            times.append((time.perf_counter() - t0) * 1000)
        out.append({"row": row, "raw": raw, "ms": statistics.mean(times)})
    return out


def judge(item, threshold, min_cov=0.0):
    """Áp ngưỡng 'không tìm thấy' (điểm >= threshold VÀ độ phủ >= min_cov) lên kết quả thô và chấm đúng/sai."""
    row, raw = item["row"], item["raw"]
    shown = [r for r in raw if r["score"] >= threshold and r.get("coverage", 1.0) >= min_cov]
    ids = [r["record"]["id"] for r in shown]
    rank = next((i + 1 for i, rid in enumerate(ids) if id_matches(rid, row["expected"])), 0)
    if row["answerable"]:
        correct = (rank == 1)
    else:
        correct = (len(shown) == 0)
    return {"shown_ids": ids, "rank": rank, "correct": correct, "rejected": len(shown) == 0,
            "top1_id": ids[0] if ids else "", "top1_score": raw[0]["score"] if raw else 0.0}


def pct(a, b):
    return f"{100 * a / b:5.1f}%" if b else "  n/a "


def summarize(items, threshold, min_cov=0.0):
    results = [judge(it, threshold, min_cov) for it in items]
    ans = [(it, r) for it, r in zip(items, results) if it["row"]["answerable"]]
    una = [(it, r) for it, r in zip(items, results) if not it["row"]["answerable"]]
    top1 = sum(1 for _, r in ans if r["rank"] == 1)
    top3 = sum(1 for _, r in ans if r["rank"] >= 1)
    mrr = statistics.mean([1 / r["rank"] if r["rank"] else 0 for _, r in ans]) if ans else 0
    wrongly_rejected = sum(1 for _, r in ans if r["rejected"])
    rejected_ok = sum(1 for _, r in una if r["rejected"])
    overall = sum(1 for r in results if r["correct"])
    return {"results": results, "n_ans": len(ans), "n_una": len(una), "top1": top1, "top3": top3, "mrr": mrr,
            "wrongly_rejected": wrongly_rejected, "rejected_ok": rejected_ok, "overall": overall, "n": len(items)}


# ----------------------------------------------------------------------------
# In báo cáo
# ----------------------------------------------------------------------------
def print_report(items, s, threshold, min_cov=0.0):
    extra = f", độ phủ tối thiểu = {min_cov}" if min_cov else ""
    print(f"\n=== KẾT QUẢ (ngưỡng điểm 'không tìm thấy' = {threshold}{extra}) ===")
    print(f"Số câu hỏi: {s['n']}  (có đáp án: {s['n_ans']}, ngoài phạm vi: {s['n_una']})")
    print(f"Top-1 (câu có đáp án)       : {s['top1']}/{s['n_ans']}  {pct(s['top1'], s['n_ans'])}")
    print(f"Top-3 (câu có đáp án)       : {s['top3']}/{s['n_ans']}  {pct(s['top3'], s['n_ans'])}")
    print(f"MRR (top-3)                 : {s['mrr']:.3f}")
    print(f"Từ chối nhầm (có đáp án)    : {s['wrongly_rejected']}/{s['n_ans']}  {pct(s['wrongly_rejected'], s['n_ans'])}")
    print(f"Từ chối đúng (ngoài phạm vi): {s['rejected_ok']}/{s['n_una']}  {pct(s['rejected_ok'], s['n_una'])}")
    print(f"Đúng tổng thể               : {s['overall']}/{s['n']}  {pct(s['overall'], s['n'])}")
    ms = [it["ms"] for it in items]
    if len(ms) > 1:
        print(f"Thời gian trả lời           : trung bình {statistics.mean(ms):.3f} ms, độ lệch chuẩn {statistics.stdev(ms):.3f} ms")

    # theo từng kiểu câu hỏi
    groups = defaultdict(list)
    for it, r in zip(items, s["results"]):
        groups[it["row"].get("style_tag") or "(chưa gắn nhãn)"].append((it, r))
    print("\n--- Theo kiểu câu hỏi (style_tag) ---")
    print(f"{'kiểu':<18}{'số câu':>7}{'đúng':>8}")
    for tag, lst in sorted(groups.items()):
        ok = sum(1 for _, r in lst if r["correct"])
        print(f"{tag:<18}{len(lst):>7}{pct(ok, len(lst)):>9}")

    # theo người hỏi (kiểm tra độ lệch do người viết)
    askers = defaultdict(list)
    for it, r in zip(items, s["results"]):
        askers[it["row"].get("asker") or "(không rõ)"].append(r["correct"])
    if len(askers) > 1:
        print("\n--- Theo người viết câu hỏi (asker) ---")
        for a, lst in sorted(askers.items()):
            print(f"{a:<18}{len(lst):>7}{pct(sum(lst), len(lst)):>9}")


def print_failures(items, s, limit=25):
    fails = [(it, r) for it, r in zip(items, s["results"]) if not r["correct"]]
    print(f"\n--- Các câu bot trả lời sai ({len(fails)}) - dùng để phân tích lỗi ---")
    for it, r in fails[:limit]:
        row = it["row"]
        want = "(nên từ chối)" if not row["answerable"] else "|".join(row["expected"])
        got = "(từ chối)" if r["rejected"] else r["top1_id"].split("_")[0] + f" (điểm {r['top1_score']:.2f})"
        print(f"  [{row['q_id']}] {row.get('style_tag', '')}: \"{row['question']}\"\n      cần: {want}   bot: {got}")
    if len(fails) > limit:
        print(f"  ... và {len(fails) - limit} câu nữa (xem file kết quả CSV)")


def print_sweep_cov(items, threshold):
    print("\n=== SO SÁNH CÁC NGƯỠNG ĐỘ PHỦ (v3) ===")
    print(f"{'độ phủ':>7}{'top-1':>9}{'từ chối đúng':>14}{'từ chối nhầm':>14}{'đúng tổng':>11}")
    for i in range(0, 11):
        c = round(i * 0.1, 2)  # round: tránh lỗi số thực (6*0.1 = 0.6000000000000001)
        s = summarize(items, threshold, c)
        print(f"{c:>7.1f}{pct(s['top1'], s['n_ans']):>9}{pct(s['rejected_ok'], s['n_una']):>14}"
              f"{pct(s['wrongly_rejected'], s['n_ans']):>14}{pct(s['overall'], s['n']):>11}")


def print_sweep(items):
    print("\n=== SO SÁNH CÁC NGƯỠNG 'KHÔNG TÌM THẤY' ===")
    print(f"{'ngưỡng':>7}{'top-1':>9}{'từ chối đúng':>14}{'từ chối nhầm':>14}{'đúng tổng':>11}")
    for i in range(0, 11):
        thr = round(i * 0.05, 2)
        s = summarize(items, thr)
        print(f"{thr:>7.2f}{pct(s['top1'], s['n_ans']):>9}{pct(s['rejected_ok'], s['n_una']):>14}"
              f"{pct(s['wrongly_rejected'], s['n_ans']):>14}{pct(s['overall'], s['n']):>11}")


def save_results(path, items, s):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["q_id", "question", "style_tag", "asker", "answerable", "expected_ids",
                    "top1_id", "top1_score", "rank_in_top3", "correct", "latency_ms"])
        for it, r in zip(items, s["results"]):
            row = it["row"]
            w.writerow([row["q_id"], row["question"], row.get("style_tag", ""), row.get("asker", ""),
                        "yes" if row["answerable"] else "no", "|".join(row["expected"]),
                        r["top1_id"], f"{r['top1_score']:.3f}", r["rank"], "1" if r["correct"] else "0",
                        f"{it['ms']:.3f}"])
    print(f"\nĐã lưu kết quả từng câu vào: {path}")


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Chấm điểm chatbot tra cứu luật giao thông")
    ap.add_argument("questions", help="file CSV câu hỏi kiểm thử")
    ap.add_argument("--data", default="data", help="thư mục dữ liệu luật (mặc định: data)")
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"], help="tập câu hỏi cần chấm")
    ap.add_argument("--threshold", type=float, default=0.15, help="ngưỡng điểm tối thiểu để bot dám trả lời")
    ap.add_argument("--repeat", type=int, default=5, help="số lần chạy mỗi câu để đo thời gian")
    ap.add_argument("--kw-weight", type=float, default=None,
                    help="v2: trọng số của keywords (chỉ mục riêng). Bỏ trống = v0/v1 (keywords gộp chung vào văn bản)")
    ap.add_argument("--min-coverage", type=float, default=0.0,
                    help="v3: độ phủ tối thiểu (0-1) giữa câu hỏi và bản ghi tìm được; thấp hơn thì bot từ chối. 0 = tắt")
    ap.add_argument("--sweep", action="store_true", help="in bảng so sánh nhiều ngưỡng điểm")
    ap.add_argument("--sweep-cov", action="store_true", help="in bảng so sánh nhiều ngưỡng độ phủ (v3)")
    ap.add_argument("--out", default="results.csv", help="file CSV lưu kết quả từng câu")
    args = ap.parse_args()

    store = LawStore(args.data, keyword_weight=args.kw_weight)  # không bật luồng nền: chấm điểm cần dữ liệu cố định
    if args.kw_weight is not None:
        print(f"Chế độ v2: keywords có chỉ mục riêng, trọng số = {args.kw_weight}")
    st = store.stats()
    print(f"Dữ liệu: {st['records']} bản ghi (phiên bản {st['version']}) từ '{args.data}'")
    if st["warnings"] or st["errors"]:
        print("CẢNH BÁO dữ liệu:", *st["warnings"], *st["errors"].items(), sep="\n  ")

    rows, skipped = load_questions(args.questions, args.split)
    for msg in skipped:
        print("Bỏ qua:", msg)
    if not rows:
        sys.exit(f"Không có câu hỏi nào để chấm (split={args.split}). Kiểm tra cột 'split' trong {args.questions}.")
    if args.split == "test":
        print("LƯU Ý: bạn đang chấm tập TEST. Chỉ làm vậy ở bước cuối, sau khi đã ngừng chỉnh bot.")

    items = run_queries(store, rows, max(1, args.repeat))
    s = summarize(items, args.threshold, args.min_coverage)
    print_report(items, s, args.threshold, args.min_coverage)
    print_failures(items, s)
    if args.sweep:
        print_sweep(items)
    if args.sweep_cov:
        print_sweep_cov(items, args.threshold)
    save_results(args.out, items, s)


if __name__ == "__main__":
    main()
