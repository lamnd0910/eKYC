# Nhật ký buổi làm việc

Mục mới nhất ở trên cùng.

---

## 2026-09-30: Đồng bộ hạ tầng với các quyết định thiết kế, bịt các đường fail-open

**Đã làm**
- Review khung repo và phát hiện code đi sau các quyết định D6–D14.
- Giao Codex 3 vòng sửa hạ tầng, review từng vòng, rồi commit tách riêng (`bd4eda6` → `76f22f1`):
  - `StageResult.passed` được thay bằng `outcome: PASSED | FAILED | NOT_EVALUATED`. Stage chưa cài đặt trả NOT_EVALUATED tường minh (D14).
  - Thêm `required_stages`. Thiếu stage bắt buộc hoặc thiếu điểm thì không bao giờ ra ACCEPT.
  - `reasons` chuyển thành mã cố định dạng `{code, message}`. `data` bị bỏ khỏi response (D10).
  - `PipelineContext` có thêm các field ảnh có kiểu rõ (D9).
  - Biên API gồm 413/422 với mã lỗi riêng, kiểm tra kích thước pixel trước khi decode (D13). Lỗi stage trả 503 đã được làm sạch. `/health` trả 503 khi chưa sẵn sàng (D12).
  - Điểm được phân ba vùng, hành động cho vùng dưới ngưỡng đọc từ `below_action` trong config (D15).
- Chốt **D15**: face dưới ngưỡng thì REJECT, OCR dưới ngưỡng thì MANUAL_REVIEW. Có thêm phần làm rõ: ảnh mờ là trách nhiệm của stage quality.
- Lint pass, toàn bộ test pass, kể cả 243 test tổ hợp outcome.

**Học được**
- **Fail-open ẩn trong khoảng giá trị bị bỏ sót:** `face_match=0.05 → ACCEPT` vì code chỉ kiểm tra vùng giữa. 243 test tổ hợp vẫn không bắt được lỗi này, vì test duyệt không gian *outcome* chứ không duyệt không gian *score*.
- Face match thấp là **bằng chứng dương tính** rằng đây là người khác. OCR confidence thấp chỉ là **thiếu bằng chứng**. Hai tín hiệu có bản chất khác nhau nên cần chính sách khác nhau.
- Hạ REJECT xuống MANUAL_REVIEW khi ảnh mờ tạo ra đường tấn công: kẻ giả mạo có thể **cố tình chụp mờ**.
- Stage nên trả **điểm liên tục**, còn ngưỡng là chính sách. Phép thử là: người vận hành có muốn chỉnh nó không?
- Hai nguồn sự thật cho cùng một việc (như cờ `implemented` và hành vi `run()`) chắc chắn sẽ lệch nhau.
- Quy trình: commit trước mỗi vòng giao việc để `git diff` chỉ chứa thay đổi mới.

**Vướng**
- Chưa trả lời được: câu trả lời "quality trả điểm liên tục" ảnh hưởng thế nào tới `severity`. Đã được giải thích: `severity` đang gộp hai khái niệm, "stage sau không chạy được" và "có nên REJECT không".
- Câu trả lời ban đầu về face thấp do ảnh mờ ("chuyển duyệt tay") mâu thuẫn với D15 vừa chốt. Bài học: kiểm tra câu trả lời có nhất quán với quyết định đã có không.

**Việc tiếp theo**
1. Chốt **D16: xử lý `severity`** (A: bỏ khỏi `StageResult`, chuyển sang config / B: thu hẹp nghĩa / C: giữ nguyên).
2. Quyết định nhỏ: đổi tên `FACE_MISMATCH` thành `FACE_MATCH_LOW`, để mã lý do mô tả sự thật thay vì phán quyết.
3. Trả lời 2 câu hỏi phỏng vấn còn treo: vì sao `below_action` bắt buộc, không có mặc định? Vì sao assert `stages[-1].calls == 1`?
4. Việc tồn đọng: PROJECT_SPEC mục 2 tự mâu thuẫn; `/health` nạp pipeline qua DI trước khi khởi động xong; `contains` chỉ còn test dùng.
5. Sau D16: bắt đầu phần **lõi ML đầu tiên**, dự kiến là `quality._evaluate` (độ nét bằng Laplacian variance, lóa, tối). Stage này vốn là nền tảng của phương án A trong D15.

**Còn thiếu trong tài liệu:** D1–D3 còn **[CẦN BỔ SUNG]**, ngân sách p95 ở D11 chưa chốt. Chưa có `plan.md` và `code_map.md`.
