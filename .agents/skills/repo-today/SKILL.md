---
name: repo-today
description: >
  Use when the user wants a deep-dive video about today's top trending GitHub repo (News v2: animated background, infographic, OmniVoice subtitles), or about one repo they name. Not: general AI-news or topic videos (toptoday); standalone video editing (video-routing).
---

# repo-today

Tạo video **deep-dive** cho repo GitHub trending hôm nay, theo News v2 (nền động + infographic + phụ đề OmniVoice). Yêu cầu thêm (nếu có): yêu cầu của người dùng trong phiên này

## Quy trình
1. **Fetch dữ liệu thật:**
   ```
   $env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
   Import-Module (Join-Path $env:OPCOS_ROOT 'system\operations\lib\opcos.psm1') -Force
   $voiceRoot = (Resolve-OpcosArea -Area voice -Quiet).Path
   & (Join-Path $voiceRoot 'omnivoice\.venv\Scripts\python.exe') (Join-Path $voiceRoot 'omnivoice\apps\news\repo_today.py') fetch
   ```
   → `repo_today_input.json` (full_name, description, language, stars_total, stars_today, topics, avatar, README). Nếu user nêu repo cụ thể trong yêu cầu của người dùng thì ưu tiên repo đó.

2. **Đọc input + SOẠN kịch bản** `repo_today_scenes.json` (BÁM README, KHÔNG bịa repo làm gì). Cấu trúc 5 cảnh:
   - `stat`: eyebrow "🔥 REPO NỔI BẬT HÔM NAY", headline "owner / repo" (accent = tên repo), big "+<stars_today> ⭐", spec rows (ngôn ngữ, tổng sao, xếp hạng #1, chủ đề/topics), hero_image = avatar.
   - `pillars` **"Repo này làm gì?"** — 3 trụ rút từ README (chức năng thật).
   - `pillars` **"Ý nghĩa với vibe coder?"** — 3 trụ: vì sao hữu ích để vibe-code nhanh (dữ liệu/SDK/template sẵn, đỡ việc gì).
   - `pillars` **"Ứng dụng khi làm việc cùng agent?"** — 3 trụ: agent có thể dùng repo này thế nào (framing "có thể", không gán tính năng không có).
   - `outro`: "Mã nguồn mở" + url repo.
   JSON format: `{"epi":"GitHub Trending · <ngày>","scenes":[...]}`. Mỗi scene có `narration` (giọng kể, **số viết kiểu đọc được**: "hai nghìn sáu trăm" thay vì 2650). Icon dùng emoji hoặc ký tự ◈★▲◷◆. Ghi đè `repo_today_scenes.json`.

3. **Render:**
   ```
   & '...\.venv\Scripts\python.exe' '...\repo_today.py' render
   ```
   (chạy NỀN — ~5-7 phút: synth + HyperFrames). Video ra `$voiceRoot\omnivoice\truyen-out\out\RepoToday_<repo>.mp4` (local).

4. **Xong:** verify frame, gửi video (SendUserFile) + tóm tắt repo làm gì / ý nghĩa / ứng dụng agent.

## Lưu ý
- Phân tích phải TRUNG THỰC với README; phần vibe-coder/agent là ứng dụng hợp lý, nói rõ "có thể".
- Không lộ tên tool nội bộ ở nội dung công khai (xem memory feedback_ainews_no_tool_names): giọng = Duc Nguyen.
- Chi tiết kỹ thuật: (Join-Path $voiceRoot 'omnivoice\apps\news\NEWS_V2_DESIGN.md'); component/layout trong `news_v2.py`.
