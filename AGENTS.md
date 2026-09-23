# AGENTS.md — ekyc

Dự án học tập và portfolio: hệ thống eKYC gồm nhiều mô hình computer vision nối thành pipeline, phục vụ qua API.
Đọc `docs/PROJECT_SPEC.md` trước khi làm bất kỳ task nào để hiểu kiến trúc và hợp đồng giữa các module.

## Nguyên tắc quan trọng nhất
- Chủ repo đang HỌC machine learning. Phần lõi ML (kiến trúc mô hình, vòng lặp huấn luyện, hàm loss, thuật toán xử lý ảnh chính) để dạng stub có docstring mô tả input/output, shape tensor và `raise NotImplementedError("TODO: ...")`, trừ khi task yêu cầu rõ là cài đặt đầy đủ.
- Hạ tầng (cấu trúc thư mục, config, logging, API, Docker, CI, test khung) thì làm đầy đủ và chạy được.
- Mỗi task chỉ làm đúng phạm vi được giao. Nếu thấy cần thay đổi ngoài phạm vi, ghi vào phần báo cáo cuối thay vì tự làm.

## Dữ liệu và quyền riêng tư
- KHÔNG commit ảnh giấy tờ tùy thân hoặc ảnh khuôn mặt thật. `data/` nằm trong `.gitignore`.
- Test chỉ dùng ảnh sinh tổng hợp (tạo bằng numpy/PIL ngay trong fixture) hoặc ảnh mẫu công khai được ghi rõ nguồn trong `data/README.md`.
- Không log ảnh gốc hay số giấy tờ ra log; chỉ log metadata (kích thước, điểm số, lý do).

## Stack và quy ước
- Python 3.11, quản lý dependency bằng `uv` với `pyproject.toml`.
- PyTorch, OpenCV, FastAPI, pydantic v2, pytest, ruff.
- Code, tên biến, comment, docstring bằng tiếng Anh. Tài liệu trong `docs/` và README có thể bằng tiếng Việt.
- Có type hint đầy đủ. Mọi tham số (ngưỡng, đường dẫn, tên mô hình) đọc từ `configs/*.yaml`, không hard-code.
- Mỗi stage trong pipeline tuân theo interface `Stage` trong `src/ekyc/common/types.py`.

## Lệnh
- Cài đặt: `uv sync`
- Kiểm tra style: `uv run ruff check . && uv run ruff format --check .`
- Test: `uv run pytest -q`
- Chạy API local: `uv run uvicorn ekyc.api.main:app --reload`
- Tất cả có sẵn qua `make lint`, `make test`, `make api`.

## Trước khi báo xong một task
1. `make lint` và `make test` đều pass.
2. Không có file dữ liệu, checkpoint mô hình hay secret nào bị thêm vào git.
3. Báo cáo ngắn: đã làm gì, file nào thay đổi, còn TODO nào, gợi ý bước tiếp theo.
