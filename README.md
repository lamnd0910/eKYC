# eKYC pipeline

Đây là dự án học tập/portfolio cho hệ thống eKYC: nhận ảnh mặt trước CCCD và
selfie, sau đó trả về `ACCEPT`, `REJECT` hoặc `MANUAL_REVIEW` cùng lý do và
trường OCR.

## Pipeline

```text
id_front + selfie
       |
 detection -> quality -> anti-spoof -> OCR -> face matching -> decision
       |
    Decision JSON
```

Stage chạy tuần tự. Một stage lỗi ở mức `blocking` khiến pipeline dừng sớm và
trả `REJECT`; điểm face/OCR trong vùng bất định của cấu hình sẽ trả
`MANUAL_REVIEW`.

## Cài đặt và chạy

Yêu cầu Python 3.11 và [uv](https://docs.astral.sh/uv/).

```bash
make install
make lint
make test
make api
```

API local cung cấp `GET /health` và `POST /v1/verify` (multipart fields
`id_front`, `selfie`). Docker: `docker compose up --build`.

## Trạng thái module

| Module | Trạng thái | Ghi chú |
| --- | --- | --- |
| Common/config/logging | Hoàn thành | Hợp đồng dữ liệu, YAML và JSON log |
| Pipeline/decision | Hoàn thành | Điều phối, dừng sớm, latency, quyết định |
| API | Hoàn thành | Có dependency injection để test |
| Detection | TODO | Stub ML |
| Quality | TODO | Stub ML |
| Anti-spoof | TODO | Stub ML |
| OCR | TODO | Stub ML |
| Face matching | TODO | Stub ML |

Không đưa ảnh giấy tờ/khuôn mặt thật, dữ liệu cục bộ hay checkpoint vào Git.
