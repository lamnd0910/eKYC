# PROJECT_SPEC — Hệ thống eKYC

## Mục tiêu
Người dùng gửi ảnh mặt trước CCCD và một ảnh selfie. Hệ thống trả về quyết định
`ACCEPT`, `REJECT` hoặc `MANUAL_REVIEW`, kèm danh sách lý do có thể hiểu được
(ví dụ: "ảnh bị mờ", "không tìm thấy khuôn mặt trên giấy tờ") và các trường thông tin trích xuất.

## Pipeline
Các stage chạy tuần tự. Stage nào trả `passed=False` với mức độ nghiêm trọng `blocking` thì pipeline dừng sớm.

| Thứ tự | Stage | Module | Nhiệm vụ |
|---|---|---|---|
| 1 | Document detection | `detection/` | Tìm 4 góc giấy tờ, cắt và căn thẳng bằng perspective transform |
| 2 | Image quality | `quality/` | Đo độ mờ, lóa sáng, độ tối, giấy tờ bị cắt mất góc |
| 3 | Anti-spoofing | `antispoof/` | Phát hiện ảnh chụp lại từ màn hình hoặc ảnh in |
| 4 | OCR | `ocr/` | Nhận dạng và trích xuất các trường: số CCCD, họ tên, ngày sinh |
| 5 | Face matching | `face/` | Phát hiện khuôn mặt trên giấy tờ và selfie, tính độ tương đồng embedding |
| 6 | Decision | `pipeline.py` | Tổng hợp kết quả, áp ngưỡng từ config, ra quyết định cuối |

## Hợp đồng dữ liệu (định nghĩa trong `src/ekyc/common/types.py`)
- `StageResult`: `name`, `passed: bool`, `severity: Literal["blocking","warning"]`, `reasons: list[str]`, `scores: dict[str, float]`, `data: dict`, `latency_ms: float`.
- `Stage` (Protocol): `name: str`, `def run(self, ctx: PipelineContext) -> StageResult`.
- `PipelineContext`: ảnh đầu vào dạng `np.ndarray` (BGR, uint8) và kết quả các stage trước.
- `Decision`: `status`, `reasons`, `fields`, `stage_results`, `total_latency_ms`.

## Quy tắc quyết định
- Có stage `blocking` thất bại → `REJECT`.
- Điểm face match hoặc độ tin cậy OCR nằm trong vùng không chắc chắn (hai ngưỡng trong config) → `MANUAL_REVIEW`.
- Còn lại → `ACCEPT`.

## API
- `POST /v1/verify`: multipart gồm `id_front` và `selfie`, trả về `Decision` dạng JSON.
- `GET /health`: trạng thái dịch vụ và phiên bản các mô hình đã nạp.
- Mô hình được nạp một lần lúc khởi động.

## Cấu trúc thư mục mong muốn
```
ekyc/
├── AGENTS.md  README.md  pyproject.toml  Makefile  Dockerfile  docker-compose.yml  .gitignore
├── configs/            base.yaml, pipeline.yaml (ngưỡng), từng mô hình một file
├── data/               README.md (mô tả nguồn dữ liệu); raw/ interim/ processed/ bị gitignore
├── docs/               PROJECT_SPEC.md, architecture.md, experiments.md (nhật ký thí nghiệm)
├── notebooks/          khám phá dữ liệu, đánh số 01_, 02_...
├── src/ekyc/
│   ├── common/         types.py, config.py, logging.py, image_io.py
│   ├── detection/  quality/  antispoof/  ocr/  face/
│   ├── pipeline.py
│   └── api/            main.py, schemas.py, deps.py
├── training/           script huấn luyện và đánh giá cho từng mô hình
├── models/             checkpoint, bị gitignore
├── tests/              unit/ cho từng stage, integration/ cho pipeline và API
└── .github/workflows/ci.yml
```

## Chỉ số đánh giá (để sau này điền vào docs/experiments.md)
- Toàn hệ thống: tỉ lệ chấp nhận nhầm, tỉ lệ từ chối nhầm, tỉ lệ chuyển duyệt tay, latency p50/p95.
- Từng stage: detection IoU, OCR độ chính xác theo trường, face match ROC-AUC và FAR/FRR tại ngưỡng đã chọn.
