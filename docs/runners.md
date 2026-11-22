# Bộ chạy tin/truyện — `scripts/runners/`

Từ 1.1.0 bộ chạy của các chiến dịch tin (hằng ngày, hằng tuần, repo tuần) và lượt truyện sống
trong repo, không còn chép vào `<trạm>/engine`. Máy nào cũng lấy CÙNG một mã bằng `git`
(Windows: `git pull`; máy lịch Mac: `git checkout <tag>`). Nội dung và cấu hình của từng kênh vẫn
ở trạm: `channel.yml`, `campaign.md`, prompt, `build-index.ps1`/`build_yt_desc.py`/`send_newsletter.py`
của kênh, state truyện.

## Ai gọi ai

`run.ps1` của chiến dịch (khuôn: `templates/station/_channel/_campaign/run.ps1`) đọc
`runtime.runner` trong `campaign.md`, sinh bản chụp cấu hình, rồi tìm runner theo thứ tự
**thư mục chiến dịch → `<repo>/scripts/runners/` → `<trạm>/engine/` (bản cũ)**.

| Runner | Chiến dịch | Việc |
|---|---|---|
| `run-toptoday-hot.ps1` | tin nóng hằng ngày (`-Brand ai|data -Publish`) | nghiên cứu (`agent_call --engine order` + last30days) → dựng video (`video-studio render`) → `publish-hot-news.ps1` |
| `run-weekly-news.ps1` | bản tin tuần | nghiên cứu → media (audio + recap + short) → YouTube → web → email → Facebook |
| `run-weekly-repo.ps1` | repo tuần | nghiên cứu một repo → video → YouTube → Facebook → sổ chống lặp |
| `run-daily-truyen.ps1` | truyện hằng ngày | `story/daily_truyen.py --state <chiến dịch>/truyen-state.json` |

Bước nghiên cứu của ba runner tin đi qua `Invoke-AgentCall` (`brand-paths.ps1`) →
`scripts/pipeline/agent_call.py --engine order`: engine chạy theo `order` trong
`<trạm>/_agent-call/engines.json`, lỗi tạm được thử lại rồi lùi sang engine kế, hết hạn mức ở
MỌI engine thì runner thoát **mã 4** (🟡, không phải hỏng). Model của agy trong `order` nên viết
bằng mẫu (`agy:claude-opus-*-high`) — `agent_call` phân giải theo `agy models` lúc chạy, chọn bản có
số phiên bản cao nhất; không khớp gì thì coi như `model_access` và lùi sang engine kế. Không runner tin nào gọi `claude -p`
thô nữa (P1-21: Hot Data 01/10 chết vì hạn mức `claude` dùng chung với phiên tương tác, trong khi
agy đứng đầu `order` chạy được).

`brand-paths.ps1` là chỗ DUY NHẤT phân giải đường cho mọi runner PowerShell; `paths.py` và
`story/truyen_paths.py` là bản Python của cùng luật.

## Luật đường dẫn

Không ổ đĩa, không tên người dùng, không tên thư mục chứa repo (`Code`, `Repo`…) nào được viết
sẵn làm câu trả lời. Thứ tự, cho mọi đường:

    biến môi trường (Windows: + registry User) → <repo>/.env (chỉ embedded)
    → repo anh em cùng thư mục cha (nhận bằng pyproject.toml: name)
    → hết: không có nấc "thư mục cũ trong thư mục nhà". Trạm không thấy thì DỪNG, nêu tên biến;
      trạm giọng / video không thấy thì trả $null (runner tự xử); nhạc nền không thấy thì tắt kèm WARN

| Cần gì | Nguồn |
|---|---|
| Trạm | đi lên từ bản chụp `-Config` tới `CHANNELS.md` → `MARKETING_STUDIO_DATA` → `studio.local.json` → `<repo>/workspaces` |
| Trạm giọng / video | `VOICE_STATION` (`OMNIVOICE_DIR`) / `VIDEO_STATION` (`VIDEO_ROOT`) → `studio.local.json` → repo anh em |
| Python giọng | `OMNIVOICE_PY` → `station.json: venv` → (máy có OpcOS) `$OPCOS_RUNTIME/venvs/agent-voice-studio/omnivoice` → `<trạm giọng>/omnivoice/.venv` → `.venv` của repo anh em video, rồi giọng |
| Repo web | `repo` của `channel.yml` (hiểu `${TÊN}`, `~`, đường tương đối theo thư mục cha) |
| last30days | `L30_SCRIPT` → thư mục plugin của Claude |
| Nhạc nền | `VOICE_BGM_DIR` → `station.json: bgm_dir` của trạm giọng (`music/library`) → (cũ) `<trạm video>/assets/news-bgm` |
| Con trỏ bí mật | `YT_TOKEN_PATH`, `YT_CLIENT_SECRET`, `FB_CONFIG`, `EMAIL_CONFIG` (+ hậu tố kênh) — chỉ ĐƯỜNG DẪN |

### Giọng đọc, media và nơi ghi (voice-station-restructure)

Ranh giới ba trạm: **nội dung + cấu hình kênh + log chạy** ở trạm marketing; **âm thanh** (giọng, nhạc) ở trạm giọng;
**hình** (nền, logo, lửa tiêu đề, font) ở trạm video; **mã runner** ở repo này. Hệ quả cho runner:

- **Giọng là CẤU HÌNH, không phải mã.** Runner tin đọc theo thứ tự: tham số `-Profile` → `campaign.md: runtime.voice_profile`
  → `channel.yml: voice_profile` → không khai (`voice-studio` dùng profile mặc định của trạm). Hàm: `Resolve-VoiceProfile`
  (`brand-paths.ps1`); bản chụp `campaign_cfg.py` mang `voice_profile` + `voice_profile_source`. Không còn `pick-voice.ps1`,
  không còn bảng series → giọng trong mã; đa dạng giọng đến từ marker sắc thái trong kịch bản. Runner truyện thêm
  `runtime.voice_pool` (luân phiên theo dải chương; state `voice` vẫn ép được).
- **Danh sách giọng hỏi bằng `voice-studio profiles list --json`** (`scripts/lib/voice.py: list_profiles`), không đọc thư mục
  kho. Lệnh chưa có (voice-studio cũ) thì `doctor` lùi đọc kho kiểu phẳng và nói ra một dòng.
- **Chạy khô:** `run-toptoday-hot.ps1 | run-weekly-news.ps1 | run-weekly-repo.ps1 -Config <config.json> -ResolveOnly` và
  `run-daily-truyen.ps1 -Campaign <thư mục> -ResolveOnly` chỉ phân giải giọng + đường, in ra rồi thoát 0 (không nghiên cứu,
  không TTS, không đăng).
- **Truyện** ghi theo chiến dịch: `<chiến dịch>/out` (thành phẩm) · `work` (cache + `_resume.json`) · `logs`. Runner đưa thư
  mục chiến dịch cho tiến trình con qua `TRUYEN_CAMPAIGN_DIR`. Nhạc/intro/outro ở `<trạm giọng>/music/channels/<kênh>/`,
  hình ở `<trạm video>/assets/channels/<kênh>/` + `assets/shared/` — tên file khai ở `channel.yml: media.music.*` /
  `media.video_kit.*` (xem `templates/station/_channel/channel.yml`). Trạm chưa dời thì lùi về cây cũ
  `<trạm giọng>/omnivoice/…` kèm cảnh báo. Không còn script nào BẮT BUỘC `OMNIVOICE_DIR`.
- **Log:** runner ghi `<kênh>/<chiến dịch>/logs/`; log tầng lịch (wrapper) ở `logs/scheduler/<nhãn>/` của trạm marketing —
  cả hai bị `.gitignore` trạm chặn. Wrapper `notify-run.ps1` chưa có tham số `-LogDir` (đề xuất DN7, việc của hạ tầng).
- **Việc mở:** (1) `run-weekly-news.ps1` còn gọi module nội bộ `video_studio.templates.news.daily_news_media` — chờ lệnh
  `video-studio … --json` tương ứng (audio từng mục + chèn HTML) ở repo video; (2) `story/make_video.py` là bộ dựng video
  nằm trong marketing — về lâu dài là template `story` của video-studio.

Bảng biến đầy đủ: `knowledge/toolchains/SECRETS.md`. Cổng giữ luật: `tests/test_runners_portable.py`,
`tests/test_ps1_portable.py`, `tests/test_khong_gia_dinh_thu_muc_cha.py`.

## Phụ thuộc ngoài repo (`doctor` kiểm, không cài)

- gói Python của bộ chạy trong **venv giọng**: `requirements-runners.txt`. Máy có OpcOS: venv giọng ở `$OPCOS_RUNTIME/venvs/agent-voice-studio/omnivoice`; gói runner được cài vào đó bằng `opcos-runtime ensure --repo-dir <repo marketing>` (tệp `opcos-runtime.json` khai `use`). Không có OpcOS: như trước.
- script `last30days` (plugin Claude);
- mp3 của từng style trong `bgm-library.json` — style thiếu mp3 thì AI không được chọn;
- các CLI agent trong `order` (`agy`, `codex`, `claude`) đã đăng nhập (`NOT_CHECKED`: doctor
  không gọi agent — tự kiểm bằng `python scripts/pipeline/agent_call.py --engine <tên>
  --on-quota fail` với một prompt ngắn).

## Chạy tay / UAT

```
pwsh -File <trạm>/<kênh>/<chiến dịch>/run.ps1 -Uat -SkipResearch -Date <yyyy-mm-dd>
```

`-Uat`: không upload YouTube, không git push, Facebook dry-run, Excel ghi sheet `UAT *`.

## Sửa mã

Sửa ở repo, qua PR có CI hai hệ điều hành — không sửa bản trong trạm. `.ps1` có tiếng Việt phải
giữ BOM (PS 5.1). Mã truyện trong repo không tự sửa mình (`heal_agent`) trừ khi `TRUYEN_HEAL=1`.
