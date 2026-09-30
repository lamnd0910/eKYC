# PROJECT_SPEC — Hệ thống eKYC

## Mục tiêu
Người dùng gửi ảnh mặt trước CCCD và ảnh selfie. Hệ thống trả `ACCEPT`, `REJECT`
hoặc `MANUAL_REVIEW`, kèm lý do dạng mã ổn định và các trường OCR trích xuất.

## Pipeline
Các stage chạy tuần tự: detection → quality → antispoof → ocr → face → quyết định.
Stage `FAILED` với severity `blocking` dẫn tới `REJECT` và dừng sớm. Stage
`NOT_EVALUATED` không dừng pipeline. Lỗi bất ngờ trong stage dẫn tới HTTP 503.

| Stage | Module | Nhiệm vụ |
|---|---|---|
| Document detection | `detection/` | Tìm 4 góc, cắt và căn thẳng giấy tờ |
| Image quality | `quality/` | Đo mờ, lóa, tối và góc bị cắt |
| Anti-spoofing | `antispoof/` | Phát hiện ảnh selfie chụp lại từ màn hình hoặc ảnh in |
| OCR | `ocr/` | Trích xuất số CCCD, họ tên, ngày sinh |
| Face matching | `face/` | So sánh khuôn mặt trên giấy tờ và selfie |
| Decision | `pipeline.py` | Áp chính sách và ngưỡng từ `configs/pipeline.yaml` |

## Hợp đồng dữ liệu
- `StageResult`: `name`, `outcome: PASSED | FAILED | NOT_EVALUATED`, `severity:
  blocking | warning`, `reasons: list[ReasonCode]`, `scores: dict[str, float]`,
  `data: dict`, `latency_ms: float`. `data` chỉ dành cho giao tiếp nội bộ.
- Stage chỉ báo `FAILED` khi không thể tạo kết quả, ví dụ không tìm thấy giấy tờ
  hoặc khuôn mặt. Stage không tự áp ngưỡng số. `NOT_EVALUATED` biểu thị kiểm tra
  chưa thực hiện; không cung cấp điểm giả.
- `Stage` (Protocol): `name: str`, `run(ctx: PipelineContext) -> StageResult`.
- `PipelineContext`: ảnh đầu vào BGR uint8 `(H, W, 3)`, kết quả stage trước và
  các artefact có kiểu rõ: `rectified_document`, `document_face`, `selfie_face`.
  Context chỉ sống trong một request; không cache, log hoặc serialize ảnh.
- `Decision`: `status`, `reasons`, `fields`, `stage_results`, `total_latency_ms`.
  `fields` chỉ lấy từ OCR.

## Quy tắc quyết định
1. Stage `FAILED` với severity `blocking` → `REJECT`, dừng sớm.
2. Stage `NOT_EVALUATED`, stage bắt buộc thiếu, stage `FAILED` dạng warning, hoặc
   stage OCR/face `PASSED` nhưng thiếu điểm bắt buộc → `MANUAL_REVIEW` tối đa.
3. Điểm face match hay OCR confidence trong vùng không chắc chắn theo config →
   `MANUAL_REVIEW`.
4. Chỉ khi các kiểm tra bắt buộc hoàn tất và không có lý do duyệt tay → `ACCEPT`.

Các stage bắt buộc được liệt kê trong `configs/pipeline.yaml`. Mã lý do và thông
điệp không chứa điểm số hoặc dữ liệu cá nhân.

## API
- `POST /v1/verify`: multipart `id_front` và `selfie`, trả về response Pydantic
  riêng. `stage_results` không có `data`; mỗi reason có `{code, message}`.
  Trường OCR chỉ xuất hiện trong `fields`.
- Biên upload đọc giới hạn dung lượng, kiểm tra định dạng và kích thước pixel
  khai báo trước khi giải mã. Mã lỗi: 413 `FILE_TOO_LARGE`; 422
  `UNSUPPORTED_FORMAT`, `IMAGE_DECODE_FAILED`, `IMAGE_TOO_LARGE`.
- Lỗi stage bất ngờ → 503 `VERIFICATION_UNAVAILABLE`, không lộ chi tiết nội bộ.
- `GET /health`: trạng thái `ok` khi pipeline nạp thành công, version của model
  và danh sách stage stub `not_evaluated_stages`. Nạp pipeline lỗi khi khởi động
  thì dịch vụ không khởi động. Thông tin giấy tờ không được ghi vào log.

## Cấu trúc thư mục
`configs/` chứa cấu hình; `src/ekyc/` chứa stage, pipeline, API và common;
`tests/` chứa kiểm thử; `data/` và `models/` bị gitignore. Không commit ảnh thật,
checkpoint hoặc secret.

## Chỉ số đánh giá dự kiến
Toàn hệ thống: tỷ lệ chấp nhận nhầm, từ chối nhầm, chuyển duyệt tay, p50/p95.
Stage: detection IoU, OCR accuracy theo trường, face ROC-AUC và FAR/FRR.
