---
name: repo-today
description: >
  Use when the user wants a deep-dive video about today's top trending GitHub repo (storyboard with source visuals and narration), or about one repo they name. Not: general AI-news or topic videos (toptoday); standalone video editing (video-routing).
---

# repo-today

Tạo video **deep-dive** cho repo GitHub trending hôm nay, theo Top Story ảnh phải (infographic động dưới tiêu đề và giọng OmniVoice). Yêu cầu thêm (nếu có): yêu cầu của người dùng trong phiên này

## Quy trình
1. **Fetch dữ liệu thật:**
   ```
   $env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
   Import-Module (Join-Path $env:OPCOS_ROOT 'system\operations\lib\opcos.psm1') -Force
   $voiceRoot = (Resolve-OpcosArea -Area voice -Quiet).Path
   $venv = (Get-Content (Join-Path $voiceRoot 'station.json') -Raw | ConvertFrom-Json).venv     # venv engine giọng (runtime/)
   $py = Join-Path $venv 'Scripts\python.exe'
   & $py -m video_studio.templates.news.repo_today fetch
   ```
   → `<trạm video>/scratch/repo-today/input.json` (đổi bằng `REPO_TODAY_INPUT`) (full_name, description, language, stars_total, stars_today, topics, avatar, README). Nếu user nêu repo cụ thể trong yêu cầu của người dùng thì ưu tiên repo đó.

2. **Tạo storyboard** từ README thật. Giữ năm cảnh: mở với lý do chọn repo, ba chương giải thích
   chức năng, giá trị và cách áp dụng với agent, rồi kết với bài tập hoặc bước thử. Phân biệt ví dụ
   đề xuất với tính năng thực tế. Viết lời Full/Short riêng, số viết kiểu đọc được.
   Theo [brief ảnh phải](../../../scripts/runners/news_image_right_brief.md): mỗi cảnh có file ảnh
   riêng đã kiểm và 2–4 bước có icon. Ưu tiên ảnh giao diện, demo hoặc kết quả chạy cụ thể.
3. **Kiểm và dựng** trong thư mục số thử. Chuẩn bị `<ngày>-top.json` cùng assets và bản chụp
   cấu hình thương hiệu của chiến dịch. Chạy cổng trước khi dựng:
   ```powershell
   & $py scripts/runners/news_asset_gate.py <ngày>-top.json --expected-chapters 3
   & $py scripts/runners/topstory_spec.py --top <ngày>-ready.json --config <config.json> --date <ngày> --out <ngày>-spec.json
   & $py -m video_studio render --project topstory --input <ngày>-spec.json --out <output> --json
   ```
   Chỉ sang lệnh tiếp nếu mã thoát bằng 0. Nếu cổng giữ, tìm lại ảnh theo cảnh được nêu.
   Kiểm ảnh cột phải và các bước cột trái trên cả MP4 trước khi gửi.

4. **Xong:** verify frame, gửi video (SendUserFile) + tóm tắt repo làm gì / ý nghĩa / ứng dụng agent.

## Lưu ý
- Phân tích phải TRUNG THỰC với README; phần vibe-coder/agent là ứng dụng hợp lý, nói rõ "có thể".
- Không lộ tên tool nội bộ ở nội dung công khai (xem memory feedback_ainews_no_tool_names): giọng = giọng mặc định của trạm (không truyền `--profile`).
- Chi tiết layout: tài liệu TOPSTORY_IMAGE_RIGHT trong repo Video Studio.
