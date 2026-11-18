"""
law_store.py - Kho dữ liệu luật TỰ ĐỘNG CẬP NHẬT khi file dữ liệu thay đổi.

Chỉ dùng thư viện chuẩn của Python (không cần cài thêm gì).

Ý tưởng chính:
  1. Mọi file *.json trong thư mục dữ liệu (data/) đều được đọc và gộp lại.
  2. Một luồng nền (thread) kiểm tra thư mục mỗi vài giây. Khi có file mới,
     file bị sửa hoặc file bị xóa thì kho được nạp lại, KHÔNG cần tắt chương trình.
  3. File lỗi (JSON hỏng, đang ghi dở) KHÔNG làm hỏng kho: chương trình giữ
     nguyên dữ liệu tốt của lần trước và báo lỗi.
  4. Luật thay đổi -> thêm một file "bản vá" (patch) vào thư mục data/:
       - bản ghi mới (id mới)          -> được thêm vào
       - bản ghi cùng id, nội dung mới -> ghi đè bản cũ
       - bản ghi có status "removed"   -> gỡ bản ghi đó khỏi kho
     QUY TẮC THỨ TỰ: các file được áp dụng theo tên file, từ A đến Z; file đứng
     SAU thắng file đứng trước. Vì vậy hãy đặt tên có số thứ tự, ví dụ:
         01_nd168_2024.json      (bộ dữ liệu gốc)
         02_nd238_2026.json      (bản vá khi Nghị định 238/2026 được đưa vào)
  5. Chỉ các bản ghi có status "done" hoặc "needs_238_check" mới được dùng để
     trả lời. Bản ghi "todo" / "removed" bị bỏ qua.
"""

import hashlib
import json
import math
import os
import re
import threading
import time
import unicodedata
from collections import Counter

# ----------------------------------------------------------------------------
# Cấu hình (các giá trị này cũng là "biến thí nghiệm" bạn có thể đưa vào báo cáo)
# ----------------------------------------------------------------------------
ACTIVE_STATUSES = {"done", "needs_238_check"}
REQUIRED_FIELDS = ["id", "status", "behavior", "vehicle_type",
                   "fine_min", "fine_max", "legal_refs", "text"]
VEHICLE_WORDS = {
    "xe_may": "xe may mo to xe gan may",
    "o_to": "o to xe hoi",
}
VEHICLE_LABEL = {"xe_may": "xe máy", "o_to": "ô tô"}
# Từ trong câu hỏi để đoán loại xe (đã bỏ dấu, chữ thường)
MOTORBIKE_HINTS = ("xe may", "mo to", "moto", "xe gan may", "honda", "wave", "vision")
CAR_HINTS = ("o to", "oto", "xe hoi", "xe con", "xe 4 banh", "xe bon banh")


# ----------------------------------------------------------------------------
# Xử lý văn bản tiếng Việt
# ----------------------------------------------------------------------------
def normalize(text):
    """Chữ thường + bỏ dấu tiếng Việt, để người dùng gõ có dấu hay không dấu đều khớp."""
    text = unicodedata.normalize("NFD", str(text).lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")


def tokenize(text):
    """Tách từ (âm tiết) và thêm cặp 2 từ liền nhau (bigram) để bắt cụm như 'den do'."""
    words = re.findall(r"[a-z0-9]+", normalize(text))
    bigrams = [words[i] + "_" + words[i + 1] for i in range(len(words) - 1)]
    return words + bigrams


# ----------------------------------------------------------------------------
# Kiểm tra dữ liệu
# ----------------------------------------------------------------------------
def validate_record(r):
    """Trả về danh sách lỗi của một bản ghi (rỗng = hợp lệ)."""
    if not isinstance(r, dict):
        return ["bản ghi không phải là object JSON"]
    problems = [f"thiếu trường '{f}'" for f in REQUIRED_FIELDS if f not in r]
    if problems:
        return problems
    if r["status"] in ACTIVE_STATUSES:
        lo, hi = r["fine_min"], r["fine_max"]
        if not isinstance(lo, int) or not isinstance(hi, int):
            problems.append("fine_min/fine_max phải là số nguyên (đồng)")
        elif lo > hi:
            problems.append("fine_min lớn hơn fine_max")
        if not r["legal_refs"]:
            problems.append("legal_refs đang rỗng")
        if not r["text"]:
            problems.append("text đang rỗng")
    return problems


def search_text_of(r, include_keywords=True):
    """Chuỗi dùng để lập chỉ mục tìm kiếm cho một bản ghi."""
    parts = [r.get("behavior", ""), r.get("condition_detail") or "",
             VEHICLE_WORDS.get(r.get("vehicle_type"), ""), r.get("text") or ""]
    if include_keywords:
        parts.extend(r.get("keywords") or [])  # cách nói đời thường, nếu bạn thêm vào
    return " ".join(parts)


def keywords_text_of(r):
    """Chỉ phần keywords (cách nói đời thường) của một bản ghi."""
    return " ".join(r.get("keywords") or [])


# ----------------------------------------------------------------------------
# Chỉ mục TF-IDF (tự cài đặt, không cần thư viện ngoài)
# ----------------------------------------------------------------------------
class TfidfIndex:
    def __init__(self, docs):
        """docs: dict {id: văn bản}"""
        tokens = {doc_id: tokenize(text) for doc_id, text in docs.items()}
        df = Counter()
        for toks in tokens.values():
            df.update(set(toks))
        n = len(docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vectors = {}
        for doc_id, toks in tokens.items():
            self.vectors[doc_id] = self._to_vector(toks)

    def _to_vector(self, toks):
        tf = Counter(toks)
        vec = {t: (1 + math.log(c)) * self.idf[t] for t, c in tf.items() if t in self.idf}
        norm = math.sqrt(sum(v * v for v in vec.values()))
        return {t: v / norm for t, v in vec.items()} if norm else {}

    def scores(self, query):
        q = self._to_vector(tokenize(query))
        result = {}
        for doc_id, vec in self.vectors.items():
            s = sum(w * vec.get(t, 0.0) for t, w in q.items())
            if s > 0:
                result[doc_id] = s
        return result


# ----------------------------------------------------------------------------
# Kho dữ liệu luật tự cập nhật
# ----------------------------------------------------------------------------
def _file_signature(path):
    st = os.stat(path)
    return (st.st_mtime_ns, st.st_size)


def _record_hash(r):
    return hashlib.sha256(json.dumps(r, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


class LawStore:
    def __init__(self, data_dir, poll_seconds=2.0, keyword_weight=None):
        """keyword_weight:
             None  -> (v0/v1) keywords được gộp chung vào văn bản luật, một chỉ mục duy nhất
             số >= 0 -> (v2) keywords có chỉ mục RIÊNG; điểm = điểm_văn_bản + keyword_weight * điểm_keywords
        """
        self.data_dir = data_dir
        self.poll_seconds = poll_seconds
        self.keyword_weight = keyword_weight
        self.kw_index = None
        self._lock = threading.RLock()
        self._files = {}        # đường dẫn -> {"sig","hash","records","error"}
        self.records = {}       # id -> bản ghi đang dùng (chỉ bản ghi active)
        self._record_hashes = {}
        self.index = TfidfIndex({})
        self.version = 0        # tăng 1 mỗi lần kho thật sự thay đổi
        self.last_change_time = None
        self.errors = {}        # đường dẫn -> thông báo lỗi
        self._prev_errors = {}  # để biết lỗi nào mới xuất hiện / vừa hết
        self.warnings = []      # cảnh báo mức bản ghi (id trùng, bản ghi sai...)
        self._listeners = []
        self._stop = threading.Event()
        self._thread = None
        os.makedirs(data_dir, exist_ok=True)
        self.check_for_changes()  # nạp lần đầu

    # ---------- đăng ký nhận thông báo ----------
    def add_listener(self, fn):
        """fn(event) được gọi mỗi khi kho đổi. event là dict: version, added, changed, removed, errors, warnings."""
        self._listeners.append(fn)

    # ---------- luồng nền ----------
    def start_watching(self):
        if self._thread and self._thread.is_alive():
            return

        def loop():
            while not self._stop.wait(self.poll_seconds):
                try:
                    self.check_for_changes()
                except Exception as e:  # luồng nền không được chết vì một lỗi bất ngờ
                    self._notify({"version": self.version, "added": [], "changed": [], "removed": [],
                                  "errors": {"<watcher>": repr(e)}, "warnings": []})

        self._stop.clear()
        self._thread = threading.Thread(target=loop, name="law-watcher", daemon=True)
        self._thread.start()

    def stop_watching(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.poll_seconds + 1)

    # ---------- kiểm tra thay đổi ----------
    def check_for_changes(self):
        """Quét thư mục, nạp lại file mới/đã sửa/đã xóa. Trả về True nếu kho thay đổi."""
        paths = sorted(
            os.path.join(self.data_dir, name)
            for name in os.listdir(self.data_dir) if name.lower().endswith(".json")
        )
        with self._lock:
            touched = False
            # file bị xóa
            for p in list(self._files):
                if p not in paths:
                    del self._files[p]
                    self.errors.pop(p, None)
                    touched = True
            # file mới hoặc đã sửa
            for p in paths:
                try:
                    sig = _file_signature(p)
                except OSError:
                    continue
                state = self._files.get(p)
                if state is not None and state["sig"] == sig:
                    continue
                touched = True
                self._load_file(p, sig)
            if not touched:
                return False
            return self._rebuild()

    def _load_file(self, path, sig):
        """Đọc một file. Nếu lỗi thì giữ nguyên dữ liệu cũ của file đó."""
        old = self._files.get(path)
        try:
            with open(path, "rb") as f:
                raw = f.read()
            digest = hashlib.sha256(raw).hexdigest()
            if old is not None and old["hash"] == digest:
                old["sig"] = sig          # nội dung giống bản đã nạp tốt (chỉ bị "chạm" hoặc đã khôi phục)
                self.errors.pop(path, None)
                return
            data = json.loads(raw.decode("utf-8"))
            records = data["records"] if isinstance(data, dict) else data
            if not isinstance(records, list):
                raise ValueError("không tìm thấy danh sách 'records'")
            self._files[path] = {"sig": sig, "hash": digest, "records": records}
            self.errors.pop(path, None)
        except (OSError, ValueError, KeyError, UnicodeDecodeError) as e:
            self.errors[path] = f"{type(e).__name__}: {e}"
            if old is not None:
                old["sig"] = sig          # giữ records cũ, không thử lại cho đến khi file đổi tiếp
            else:
                self._files[path] = {"sig": sig, "hash": None, "records": []}

    # ---------- gộp tất cả file thành một kho ----------
    def _rebuild(self):
        merged, warnings = {}, []
        owner = {}
        for path in sorted(self._files):
            name = os.path.basename(path)
            for r in self._files[path]["records"]:
                rid = r.get("id") if isinstance(r, dict) else None
                problems = validate_record(r)
                if problems:
                    warnings.append(f"{name}: bản ghi '{rid}' bị bỏ qua ({'; '.join(problems)})")
                    continue
                if r["status"] in ACTIVE_STATUSES:
                    if rid in merged and owner[rid] != name:
                        warnings.append(f"id '{rid}' có ở {owner[rid]} và {name}: dùng bản của {name}")
                    merged[rid] = r
                    owner[rid] = name
                else:  # todo / removed -> gỡ khỏi kho
                    merged.pop(rid, None)
                    owner.pop(rid, None)

        new_hashes = {rid: _record_hash(r) for rid, r in merged.items()}
        added = sorted(set(new_hashes) - set(self._record_hashes))
        removed = sorted(set(self._record_hashes) - set(new_hashes))
        changed = sorted(rid for rid in new_hashes
                         if rid in self._record_hashes and new_hashes[rid] != self._record_hashes[rid])

        warnings_changed = warnings != self.warnings
        errors_event = dict(self.errors)
        errors_changed = errors_event != self._prev_errors
        self._prev_errors = dict(errors_event)
        self.warnings = warnings
        if not (added or removed or changed):
            if warnings_changed or errors_changed:
                self._notify({"version": self.version, "added": [], "changed": [], "removed": [],
                              "errors": errors_event, "warnings": warnings})
            return False

        if self.keyword_weight is None:
            index = TfidfIndex({rid: search_text_of(r) for rid, r in merged.items()})
            kw_index = None
        else:
            index = TfidfIndex({rid: search_text_of(r, include_keywords=False) for rid, r in merged.items()})
            kw_index = TfidfIndex({rid: keywords_text_of(r) for rid, r in merged.items()})
        self.records, self._record_hashes, self.index, self.kw_index = merged, new_hashes, index, kw_index
        self.version += 1
        self.last_change_time = time.time()
        self._notify({"version": self.version, "added": added, "changed": changed, "removed": removed,
                      "errors": errors_event, "warnings": warnings})
        return True

    def _notify(self, event):
        for fn in list(self._listeners):
            try:
                fn(event)
            except Exception:
                pass

    # ---------- tra cứu ----------
    def get(self, record_id):
        with self._lock:
            return self.records.get(record_id)

    def search(self, query, top_k=3, vehicle_type=None):
        """Trả về danh sách {"score","record"} tốt nhất. Tự đoán loại xe từ câu hỏi nếu không truyền vào."""
        with self._lock:
            scores = self.index.scores(query)
            if self.kw_index is not None and self.keyword_weight:
                for rid, ks in self.kw_index.scores(query).items():
                    scores[rid] = scores.get(rid, 0.0) + self.keyword_weight * ks
            vehicle = vehicle_type or self.detect_vehicle(query)
            results = []
            for rid, s in scores.items():
                r = self.records[rid]
                if vehicle:
                    s *= 1.5 if r["vehicle_type"] == vehicle else 0.7
                results.append({"score": s, "record": r})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    @staticmethod
    def detect_vehicle(query):
        q = " " + normalize(query) + " "
        if any(h in q for h in MOTORBIKE_HINTS):
            return "xe_may"
        if any(h in q for h in CAR_HINTS):
            return "o_to"
        return None

    def stats(self):
        with self._lock:
            by_status = Counter(r["status"] for r in self.records.values())
            return {"version": self.version, "records": len(self.records), "files": len(self._files),
                    "by_status": dict(by_status), "errors": dict(self.errors), "warnings": list(self.warnings)}


# ----------------------------------------------------------------------------
# Trình bày câu trả lời
# ----------------------------------------------------------------------------
def format_money(n):
    return f"{n:,}".replace(",", ".") + " đồng"


def format_ref(ref):
    parts = [f"Điều {ref['article']}"]
    if ref.get("clause") not in (None, 0):
        parts.append(f"khoản {ref['clause']}")
    if ref.get("point"):
        parts.append(f"điểm {ref['point']}")
    return " ".join(parts)


def describe(r):
    """Biến một bản ghi thành câu trả lời có trích dẫn nguồn (không tự suy diễn)."""
    lines = [f"[{VEHICLE_LABEL.get(r['vehicle_type'], r['vehicle_type'])}] {r['behavior']}"]
    lo, hi = r["fine_min"], r["fine_max"]
    lines.append("  - Mức phạt: " + (format_money(lo) if lo == hi else f"{format_money(lo)} đến {format_money(hi)}"))
    pts = r.get("points_deducted")
    if pts is None:
        lines.append("  - Trừ điểm giấy phép lái xe: chưa có dữ liệu")
    elif pts == 0:
        lines.append("  - Trừ điểm giấy phép lái xe: không")
    else:
        lines.append(f"  - Trừ điểm giấy phép lái xe: {pts} điểm")
    susp = r.get("license_suspension_months")
    if susp:
        lines.append(f"  - Tước quyền sử dụng giấy phép lái xe: {susp[0]} đến {susp[1]} tháng")
    if r.get("extra_penalties") and not susp:
        lines.append(f"  - Hình phạt bổ sung: {r['extra_penalties']}")
    refs = "; ".join(format_ref(x) for x in r["legal_refs"] if x.get("part") == "phat_tien")
    lines.append(f"  - Căn cứ: {r.get('document', '')}, {refs}")
    if r.get("effective_from"):
        lines.append(f"  - Có hiệu lực từ: {r['effective_from']}")
    if r["status"] == "needs_238_check":
        lines.append("  ! Lưu ý: nội dung này có thể đã được sửa đổi bởi Nghị định 238/2026/NĐ-CP, hãy kiểm tra lại.")
    return "\n".join(lines)
