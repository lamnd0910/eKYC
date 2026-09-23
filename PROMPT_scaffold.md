Đọc AGENTS.md và docs/PROJECT_SPEC.md.

Task: dựng khung repo cho dự án ekyc theo đúng cấu trúc thư mục trong PROJECT_SPEC. Chưa cài đặt mô hình ML.

Trước khi viết code, đưa ra kế hoạch ngắn gồm danh sách file sẽ tạo, rồi thực hiện.

Yêu cầu cụ thể:
1. pyproject.toml dùng uv, gồm dependency chính (torch, torchvision, opencv-python-headless, fastapi, uvicorn, pydantic, pyyaml, numpy) và nhóm dev (pytest, ruff, httpx). Cấu hình ruff và pytest trong pyproject.
2. src/ekyc/common/: types.py cài đầy đủ các kiểu trong mục "Hợp đồng dữ liệu"; config.py đọc YAML thành pydantic model; logging.py cấu hình log dạng JSON.
3. Mỗi module detection, quality, antispoof, ocr, face có một class cài interface Stage. Phần xử lý chính để stub theo quy tắc trong AGENTS.md, nhưng class phải khởi tạo được và có docstring mô tả input, output, và gợi ý hướng cài đặt.
4. pipeline.py cài đầy đủ logic điều phối: chạy stage tuần tự, dừng sớm khi gặp lỗi blocking, đo latency, áp quy tắc quyết định. Logic này không phụ thuộc mô hình nên làm hoàn chỉnh.
5. api/: FastAPI với /v1/verify và /health như trong spec. Stage được inject qua dependency để test có thể thay bằng stage giả.
6. tests/: test cho config, cho pipeline dùng stage giả (đủ 3 nhánh ACCEPT, REJECT, MANUAL_REVIEW), và test API bằng TestClient với ảnh tổng hợp sinh trong fixture.
7. Makefile (install, lint, format, test, api), Dockerfile multi-stage, docker-compose.yml, .gitignore phù hợp dự án ML (data/, models/, checkpoint, .env, notebook output).
8. .github/workflows/ci.yml chạy lint và test.
9. README.md tiếng Việt: giới thiệu, sơ đồ pipeline, cách cài và chạy, trạng thái các module (bảng: module nào đã xong, module nào còn TODO).
10. docs/experiments.md với mẫu bảng ghi thí nghiệm, để trống nội dung.

Hoàn thành khi `make lint` và `make test` đều pass. Cuối cùng báo cáo theo mục "Trước khi báo xong một task" trong AGENTS.md.
