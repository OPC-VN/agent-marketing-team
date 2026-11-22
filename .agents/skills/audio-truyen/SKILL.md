---
name: audio-truyen
description: >
  Use when the user asks to read a story from tamhoan.com aloud with the OmniVoice cloned voice (xianxia voice) and build the finished audio or video for a chapter range, for example "đọc truyện Phàm Nhân Tu Tiên chương 1141-1150". Not: general voice or script work with no story pipeline (voice-routing); standalone video editing (video-routing).
---

# audio-truyen

Bạn là agent thực thi pipeline **Nghe Tiên Truyện**. Yêu cầu của người dùng là yêu cầu được giao trong phiên này (nguyên văn lời người dùng).

## 1. Bóc tham số từ yêu cầu
- **URL / slug**: tìm link `tamhoan.com/<slug>/` trong yêu cầu (vd `https://tamhoan.com/pham-nhan-tu-tien/` → slug `pham-nhan-tu-tien`). Nếu chỉ có tên truyện và là Phàm Nhân Tu Tiên thì slug = `pham-nhan-tu-tien`.
- **Phạm vi chương**: dạng "từ chương X-Y", "X đến Y", "chương X-Y" → `--start X --end Y`. Nếu chỉ 1 chương → `--start X --end X`.
- **Video hay không**: nếu có "video" / "hoàn chỉnh video" / "tạo video" → để mặc định (CÓ video). Nếu nói "chỉ audio" / "không video" / "chỉ mp3" → thêm `--no-video`.
- Mặc định khác (chỉ đổi khi người dùng nêu): giọng `giong-tien-hiep` (cấu hình kênh: `channel.yml: voice_profile`), speed 0.9, nghỉ giữa chương 10s, text gấp đôi, có logo + phụ đề + outro, 1280×720, xuất ra `<chiến dịch>/out/` (đặt `TRUYEN_CAMPAIGN_DIR` = thư mục chiến dịch; không đặt thì cảnh báo và ghi nháp ở trạm giọng; đổi bằng `--out-dir`).

## 2. Chạy (CHẠY NỀN — job dài, ~thời lượng audio thực)
Dùng đúng Python của venv. Đặt biến môi trường UTF-8. Ví dụ với PNTT 1141–1150 có video:

```
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'; $env:HF_HUB_OFFLINE='0'
# <python giọng> = python của venv trạm giọng (`voice-studio doctor` chỉ ra; biến OMNIVOICE_PY nếu đã đặt)
# <repo> = bản clone agent-marketing-team; chiến dịch = thư mục chứa truyen-state.json
$env:TRUYEN_CAMPAIGN_DIR = '<thư mục chiến dịch, vd <trạm marketing>/nghe-tien-truyen/pham_nhan_tu_tien_phan_2>'
& <python giọng> -u '<repo>/scripts/runners/story/audio_truyen.py' `
  --url 'https://tamhoan.com/pham-nhan-tu-tien/' --start 1141 --end 1150 --video
```

- Chạy bằng **run_in_background = true** (mỗi chương ~10–13 phút synth; 10 chương ≈ 2 giờ). Ghi log để theo dõi.
- `audio_truyen.py` tự: resolve số chương → URL id, crawl đúng text, đọc (ASR-verify số tiêu đề, đọc lại nếu sai), xuất `<slug>_<start>-<end>.mp3` + `.manifest.json` + `.srt`, rồi dựng `<slug>_<start>-<end>.mp4` ra `<chiến dịch>/out/` (local). Nhạc nền ở `<trạm giọng>/music/channels/<kênh>/`, hình (nền/logo/font) ở `<trạm video>/assets/…` — khai ở `channel.yml: media`.

## 3. Khi xong
- Đọc log xác nhận exit 0, kiểm tra file `.mp4` (hoặc `.mp3` nếu `--no-video`) tồn tại trong `<chiến dịch>/out/`.
- (Tuỳ chọn) verify nhanh tiêu đề bằng Whisper như pipeline đã làm.
- Gửi file kết quả cho người dùng (SendUserFile) + báo thời lượng, số chương.

## Ghi chú
- Tài liệu chi tiết + tham số tinh chỉnh: (Join-Path $marketingRoot 'nghe-tien-truyen\AGENT_AUDIO_TRUYEN.md').
- Truyện MỚI (slug khác) chưa có "anchor" số-chương→id: cần 1 mốc `(chương, id)` thêm vào `ANCHORS` trong `read_story.py`, hoặc truyền thẳng `--start-id`.
- KHÔNG bịa kết quả: nếu một bước lỗi, báo log thật và dừng.
