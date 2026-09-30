# Các quyết định thiết kế — eKYC

Mỗi quyết định gồm: chốt gì, vì sao, phương án bị loại và lý do loại.
Khi thay đổi một quyết định, không xóa bản cũ: ghi thêm mục "Thay đổi" kèm ngày và lý do.

> D1–D3 được tái dựng từ bảng tổng hợp. Phần lý do và phương án bị loại đánh dấu
> **[CẦN BỔ SUNG]** cần được điền từ phiên thảo luận gốc.

## Nguyên tắc xuyên suốt

1. **Stage báo sự thật, pipeline áp chính sách.** Phép thử: nếu người vận hành có thể muốn
   chỉnh nó thì nó là chính sách và nằm trong `configs/pipeline.yaml`.
2. **Không bao giờ fail-open.** Không có đường nào dẫn tới ACCEPT khi có lỗi hoặc khi một
   kiểm tra chưa được thực hiện.
3. **Dữ liệu cá nhân không thể rò rỉ về mặt cấu trúc**, không dựa vào việc nhớ lọc.

---

## D1 — Nguồn dữ liệu
**Chốt:** Lai: dữ liệu tổng hợp + bộ dữ liệu công khai. Bộ tự chụp chỉ dùng để test, không dùng để huấn luyện.
**Lý do:** [CẦN BỔ SUNG] Không dùng ảnh CCCD thật vì là dữ liệu cá nhân. Bộ sinh ảnh tổng hợp cho nhãn miễn phí (tọa độ 4 góc cho D3, nhãn mờ/lóa/tối cho mô hình quality). Bộ tự chụp giữ độc lập làm phép thử thực tế nhất.
**Phương án bị loại:** [CẦN BỔ SUNG]
**Ghi chú:** Chỉ chụp người đồng ý rõ ràng; không đưa ảnh vào repo.

## D2 — Phần tự huấn luyện
**Chốt:** Tự huấn luyện anti-spoof và quality. Detection, OCR, face dùng pretrained hoặc cổ điển.
**Lý do:** [CẦN BỔ SUNG] Hai mô hình tự huấn luyện là chất liệu cho câu hỏi phỏng vấn về CNN và các vấn đề khi huấn luyện.
**Phương án bị loại:** [CẦN BỔ SUNG]
**Ghi chú:** Mô hình quality học trên ảnh suy giảm nhân tạo, nên cũng phải được đánh giá theo giao thức D8 (so sánh với bộ tự chụp).

## D3 — Detection
**Chốt:** Xử lý ảnh cổ điển, đo IoU trên ảnh tổng hợp, ghi nhận rõ giới hạn.
**Lý do:** [CẦN BỔ SUNG]
**Phương án bị loại:** [CẦN BỔ SUNG]

## D4 — OCR
**Chốt:** Thư viện có sẵn + tầng hậu kiểm bằng luật.
**Lý do:** Gần như không tốn thêm thời gian so với dùng thư viện nguyên bản, nhưng có phần tự thiết kế. Mô hình nào cũng sai, lớp kiểm tra chéo phát hiện kết quả vô lý và đẩy sang MANUAL_REVIEW.
**Luật hậu kiểm:** Số CCCD **không có chữ số kiểm tra (checksum)**. Kiểm tra cấu trúc thay thế: mã tỉnh (3 số đầu), số thứ 4 mã hóa giới tính và thế kỷ sinh, 2 số tiếp theo là năm sinh; đối chiếu chéo với ngày sinh và giới tính đọc được. (Cần xác minh lại quy định hiện hành trước khi cài đặt.)
**Phương án bị loại:**
- Thư viện nguyên bản, không hậu kiểm: không có phần tự thiết kế, độ chính xác phụ thuộc hoàn toàn vào mô hình người khác.
- Fine-tune ngay: khối lượng quá lớn so với thời gian hiện tại → chuyển thành giai đoạn 2.
**Giai đoạn 2 (tùy chọn, tuần 5):** Fine-tune recognizer trên crop tổng hợp, so CER với bản gốc, đo số ca MANUAL_REVIEW giảm được. Đây là phần duy nhất trong dự án chạm tới mô hình xử lý chuỗi.

## D5 — Ngưỡng
**Chốt:** Điểm face match dùng ngưỡng chọn trên ROC (FAR và FRR mục tiêu). OCR dùng luật rời rạc.
**Lý do:** Hai tín hiệu bản chất khác nhau: face là điểm liên tục, OCR sau hậu kiểm là kết quả rời rạc. Ép chung một thang điểm tạo ra con số khó giải thích.
**Ghi chú:** Muốn khẳng định FAR ≤ 1e-3 đáng tin cần khoảng 3.000 cặp khác người trở lên trên validation. Lập luận "chấp nhận nhầm kẻ giả mạo đắt hơn từ chối nhầm người thật" dùng để giải thích vì sao FAR khắt khe hơn FRR.
**Phương án bị loại:**
- Ngân sách review cố định theo %: không gắn với rủi ro thật.
- Tối ưu hàm chi phí: phải bịa các con số chi phí. Giữ làm lập luận, không cài đặt.

## D6 — Sở hữu chính sách
**Chốt:** Lai. Stage chỉ tự đặt `passed=False` khi không thể tạo ra kết quả (không tìm thấy giấy tờ, không tìm thấy mặt). Mọi ngưỡng số và việc ánh xạ sang REJECT/MANUAL_REVIEW nằm trong `configs/pipeline.yaml`.
**Làm rõ với D5:** Luật OCR bị vi phạm là sự thật (stage báo mã luật); vi phạm đó dẫn tới quyết định nào là chính sách (pipeline).
**Phương án bị loại:**
- Pipeline sở hữu toàn bộ: phải mã hóa ca hiển nhiên thành điểm số, gượng ép.
- Stage sở hữu: chính sách rải 5 nơi, đổi FAR phải sửa nhiều file (vấn đề A1).
**Hệ quả:** Cập nhật ý nghĩa `passed`/`severity` trong PROJECT_SPEC và `types.py`.

## D7 — Anti-spoof
**Chốt:** Làm nhánh selfie. Nhánh giấy tờ để stub kèm ghi chú: vì sao chưa làm (không có dữ liệu công khai), rủi ro (ảnh chụp lại CCCD người khác), cách làm nếu có dữ liệu.
**Ghi chú:** Kiểm tra giấy phép dataset trước khi tải; không đưa dữ liệu vào repo; xem điều khoản có cho công bố trọng số không. Dùng tập con có kiểm soát; chỉ kênh RGB.
**Phương án bị loại:** Chỉ giấy tờ (không có dữ liệu, mâu thuẫn D1); cả hai model (gấp đôi khối lượng).

## D8 — Giao thức đánh giá
**Chốt:** Báo cáo song song intra-dataset và cross-dataset. Khoảng cách giữa hai con số là nội dung chính của experiments.md.
**Quy tắc:**
- Ngưỡng chọn trên validation của bộ huấn luyện, giữ nguyên khi sang bộ khác.
- Báo cáo AUC cạnh APCER/BPCER/ACER để phân biệt lệch thang điểm với mất khả năng phân biệt.
- Tiền xử lý giống hệt nhau trên mọi bộ dữ liệu.
**Phương án bị loại:** Chỉ intra (số đẹp, không nói gì về tổng quát hóa); chỉ cross (thiếu mốc so sánh).

## D9 — Kênh truyền artefact
**Chốt:** Field có kiểu rõ trong `PipelineContext` (ảnh giấy tờ đã căn thẳng, crop khuôn mặt).
**Lý do:** Dữ liệu cá nhân nhạy cảm; schema trả về không đọc tới các field này nên không thể rò rỉ. Sửa `types.py` khi thêm stage là ưu điểm: hợp đồng dữ liệu được khai báo rõ.
**Ghi chú:** Context chỉ tồn tại trong một request, không cache, không log.
**Phương án bị loại:** `artifacts: dict[str, Any]` (không an toàn kiểu); giữ data + lọc lúc serialize (rủi ro rò rỉ cao nhất).

## D10 — Bề mặt API
**Chốt:** Bỏ `data` khỏi `stage_results`. Trường OCR chỉ nằm trong `fields`, trả đầy đủ (phía gọi cần để đối chiếu).
**Quy tắc:** `reasons` là mã lỗi cố định kèm mô tả **không chứa giá trị cụ thể** (ví dụ `OCR_ID_DOB_MISMATCH`). Response là pydantic model riêng, không serialize object nội bộ. Số giấy tờ được che trong log, không che trong response.
**Phương án bị loại:** Che số CCCD trong response (API mất mục đích nghiệp vụ); cờ debug (quyền riêng tư phụ thuộc một dòng config). Nhu cầu debug đáp ứng bằng script chạy local, ngoài API.

## D11 — Runtime
**Chốt:** PyTorch trước, chuyển ONNX nếu p95 vượt ngân sách.
**Ngân sách p95:** [CẦN CHỐT CON SỐ] đề xuất tạm: ≤ 3 giây/request trên CPU, đo lại sau lát cắt đầu tiên.
**Cách đo:** Bỏ request khởi động, dùng ảnh kích thước thật, xem `latency_ms` từng stage để tìm điểm nghẽn trước khi tối ưu.
**Ghi chú:** Dùng bản PyTorch chỉ cho CPU để giảm kích thước image. Kiểm tra runtime riêng của các thư viện pretrained.
**Phương án bị loại:** PyTorch vĩnh viễn không đo; ONNX ngay (tối ưu trước khi đo).

## D12 — Chính sách lỗi
**Chốt:** Phân loại theo loại lỗi, không theo stage:

| Loại lỗi | Ví dụ | Xử lý |
|---|---|---|
| Lỗi nội dung của ảnh **đã giải mã được** | không tìm thấy giấy tờ, ảnh quá tối | Stage báo sự thật → REJECT kèm mã lỗi |
| Lỗi lúc khởi động | nạp mô hình thất bại | Dịch vụ không khởi động, `/health` báo chưa sẵn sàng |
| Lỗi ngoài dự kiến lúc chạy | OOM, bug | 503, ghi metric lỗi theo stage |

Không trường hợp lỗi nào được dẫn tới ACCEPT.
**Phương án bị loại:** Mọi lỗi → MANUAL_REVIEW (bug lặng lẽ đẩy toàn bộ lưu lượng vào duyệt tay); mọi lỗi → 5xx (chặn người dùng cả với lỗi dữ liệu); phân theo stage (không phản ánh bản chất lỗi).

## D13 — Biên API
**Chốt:** Phép thử ranh giới: **đã tạo được mảng ảnh hợp lệ từ file chưa?** Chưa → lỗi giao thức ở biên. Đã có → mọi vấn đề thuộc stage (D12).

| Tình huống | HTTP | Mã lỗi |
|---|---|---|
| File vượt dung lượng | 413 | `FILE_TOO_LARGE` |
| Sai định dạng | 422 | `UNSUPPORTED_FORMAT` |
| Không giải mã được | 422 | `IMAGE_DECODE_FAILED` |
| Kích thước pixel vượt giới hạn | 422 | `IMAGE_TOO_LARGE` |

**Ghi chú:** Kiểm tra dung lượng và kích thước pixel trước khi giải mã toàn bộ, tránh OOM do file nén khai báo kích thước khổng lồ.
**Phương án bị loại:** Đẩy vào pipeline thành REJECT (làm méo thống kê REJECT, HTTP 200 cho request sai định dạng).

## D14 — Kết quả "chưa đánh giá"
**Chốt:** Stage chưa được cài đặt hoặc chưa có mô hình trả trạng thái `NOT_EVALUATED` tường minh, không trả điểm giả. Pipeline gặp bất kỳ stage `NOT_EVALUATED` nào thì kết quả tốt nhất có thể là MANUAL_REVIEW, với mã `STAGE_NOT_EVALUATED`. REJECT từ stage khác vẫn được ưu tiên.
**Lý do:** Phát hiện khi review lát cắt xuyên suốt: nếu stage trung tính không trả điểm, logic hiện tại có thể trả ACCEPT, vi phạm nguyên tắc không fail-open. Hệ quả chấp nhận được: trong giai đoạn lát cắt, mọi request hợp lệ sẽ ra MANUAL_REVIEW, và đó là câu trả lời trung thực.
**Test bắt buộc:** Mọi tổ hợp có ít nhất một stage `NOT_EVALUATED` không bao giờ ra ACCEPT.

## D15 — Điểm dưới ngưỡng dưới
**Chốt:** Face match dưới `manual_review_low` → REJECT với mã `FACE_MISMATCH`. OCR confidence dưới `manual_review_low` → MANUAL_REVIEW với mã `OCR_CONFIDENCE_LOW`. Quy tắc đầy đủ cho mỗi điểm: `< low` / `[low, high)` / `>= high`.
**Lý do:** Phát hiện khi review: `_decide` chỉ kiểm tra điểm có nằm trong khoảng không chắc chắn, nên điểm dưới ngưỡng dưới rơi thẳng xuống ACCEPT (`face_match=0.05 → ACCEPT`), vi phạm nguyên tắc không fail-open. Hai tín hiệu có bản chất khác nhau (nhất quán với D5): điểm face thấp là bằng chứng dương tính rằng đây là hai người khác nhau; OCR confidence thấp chỉ là thiếu bằng chứng, do mô hình đọc kém chứ không chứng minh gian lận.
**Phương án bị loại:**
- Cả hai → REJECT: từ chối nhầm người thật chỉ vì ảnh chụp khó đọc; biến lỗi mô hình thành lỗi của người dùng.
- Cả hai → MANUAL_REVIEW: đẩy các ca rõ ràng là khác người vào duyệt tay, lãng phí nguồn lực duyệt và làm yếu vai trò của ngưỡng FAR (D5).
**Ghi chú:** REJECT do điểm face được pipeline áp sau khi tất cả stage chạy xong, không phải stage tự đặt FAILED (D6). REJECT được ưu tiên hơn MANUAL_REVIEW khi cả hai cùng xảy ra.
**Test bắt buộc:** Điểm dưới ngưỡng dưới, đúng bằng `low`, và đúng bằng `high` cho cả face và OCR.
