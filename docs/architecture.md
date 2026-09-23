# Kiến trúc

API nhận ảnh mặt trước giấy tờ và selfie, giải mã thành mảng BGR `uint8`, rồi
chuyển vào pipeline tuần tự:

`detection -> quality -> antispoof -> ocr -> face -> decision`

Mỗi stage ghi `StageResult` vào `PipelineContext`. Một lỗi `blocking` làm dừng
pipeline và trả `REJECT`; các điểm OCR/face ở vùng bất định được chuyển sang
`MANUAL_REVIEW` theo ngưỡng trong `configs/pipeline.yaml`.
