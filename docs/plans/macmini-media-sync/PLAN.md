---
title: PLAN — macmini-media-sync (master, marketing side)
date: 2026-11-25
revision: 3
status: draft_waiting_owner_decisions
scope: three repos — agent-marketing-team (this file, orchestration + publish), agent-video-studio (asset-first production), agent-voice-studio (voice station)
companions:
  - KIRA-BRIDGE.md (this folder)
  - HANDOFF-CODEX.md (this folder)
  - PROGRESS.md (this folder, shared log between the two Codex sessions)
  - agent-video-studio/docs/plans/macmini-media-sync/PLAN.md
  - agent-voice-studio/docs/plans/macmini-media-sync/PLAN.md
executor: Codex — two sessions, Codex-W (Windows) and Codex-M (Mac mini); allowed to push branch macmini-media-sync and open PRs
coordination: PROGRESS.md (this folder) on branch macmini-media-sync + owner pastes prompts between sessions
evaluator: Claude — advisory only, at plan start (done) and at the end (final assessment and recommendations)
reviews_applied: independent review rev 1 (26 findings) — data-safety rules carried over
---

# PLAN — macmini-media-sync

> Ba repo dùng **cùng một tên kế hoạch** `macmini-media-sync`. File này là kế hoạch **chủ**: mục tiêu, pha, cổng, bảo vệ dữ liệu, đăng bài. Phần sản xuất video theo tài nguyên nằm ở repo video, phần trạm giọng ở repo voice.
> Repo là **công khai**: kế hoạch không ghi tên người, tên giọng thật, tên tài khoản, đường máy. Chi tiết riêng của máy, Codex tự đọc tại chỗ trên Mac mini và ghi vào thư mục bằng chứng **ngoài repo**.

## 0. Mục tiêu

Ba yêu cầu của chủ máy:

1. **Đóng gói 3 repo từ GitHub xuống Mac mini** (bản mới song song với bản cũ đang chạy) mà **không ảnh hưởng tài liệu, dữ liệu chiến dịch** đang làm trên Mac.
2. **Áp dụng skill, quy trình, template mới** để làm video, và **dời việc rà soát lên trước**: rà **tài nguyên** (icon, GIF, ảnh tin, logo, footage) **trước khi dựng video**, không còn rà video thành phẩm rồi bắt làm lại trước khi đăng.
3. **Đăng tự động sau khi đóng gói**: YouTube, Facebook Page, website, bình luận trong Page chạy tự động; **Facebook Group** do **Kira** đăng. Kira là một agent chủ máy dựng trên ChatGPT, thao tác trình duyệt như người, đăng bằng tài khoản chủ máy cho phép, trong trình duyệt đã đăng nhập sẵn. Meta đã bỏ đăng group qua Graph API nên đây là đường duy nhất. Pipeline phải **báo được cho Kira** khi có bài cần đăng group (`KIRA-BRIDGE.md`).

## 1. Bối cảnh đã xác minh trên Windows (25/11)

| Mảng | Sự thật |
|---|---|
| Mã | marketing `main` = `8d5fdd3`; voice `main` = `c9a5e6c` (0.7.0, API 1.2.0); video `main` = `75fac7a` (0.10.1). Video còn commit `ac72677` (skill video-long-to-shorts, có `qa_short.py`) **chưa push**, chưa có tag `v0.10.1`. Cả 3 repo có README sửa dở chưa commit. |
| Rà soát hiện tại | Trong repo chỉ có `scripts/pipeline/prepublish_check.py` (kiểm file tồn tại) và render preflight trong `scripts/runners/brand-paths.ps1`. **Script dò ảnh/tài nguyên rồi bắt làm lại chỉ nằm trên Mac mini** — Windows không có, Codex phải đọc tại chỗ (pha 1). |
| Đăng | `scripts/runners/youtube_upload.py` (mặc định public), `scripts/runners/post_facebook.py` (Page; nhánh group qua Graph **không còn dùng được** vì Meta đã bỏ), `scripts/pipeline/fb_publish.py`, cập nhật web qua repo `news`. Khoá chống đăng lại: sidecar `<ngày>-top.json.published.json` (**không đổi tên**), `publish.json`. |
| Chuẩn video mới | Repo video 0.10.1: chuẩn chuyển động/bố cục, icon động, storyboard ảnh tĩnh trước (`skills/video-storyboard-design/references/`). Các mã kiểm CK-* và G21 **mới là tài liệu**, chưa có code. |
| Mac mini | Đo lần cuối 04/10: bản cũ ở `~/Repo/`, trạm nhúng `workspace/`, 6 plist `studio.marketing.*` vá tay, python mặc định 3.9, `ffmpeg-full`. Trạng thái hiện tại **chưa đo**. |
| Lệnh có sẵn quan trọng | `-ResolveOnly` ở cả 4 runner; `-Uat` ở Hot/Weekly/Repo (không upload, không push, không ghi sidecar); **runner truyện không có `-Uat`**. `install_launchd.py --dry-run` an toàn; `--uninstall` **xoá file plist**; cài mới **ghi đè** plist cùng tên. |

## 2. Tiêu chí thành công

Kế hoạch có 7 **tiêu chí thành công** (SC):

| Mã | Tiêu chí | Đo bằng |
|---|---|---|
| SC1 — Dữ liệu Mac nguyên vẹn | Manifest sha256 vùng bảo vệ ở hai thời điểm **không có job nào đang chạy** (M0 pha 1, M1 trước chuyển lịch): 0 file mất; file đổi chỉ thuộc danh sách cho phép (mục 4.3) | `manifest-diff.txt` |
| SC2 — Bản mới cài xong | 3 doctor exit 0 trên Mac; `-ResolveOnly` đạt mọi chiến dịch đang chạy; mọi đường in ra nằm dưới gốc mới | log + `path-audit.txt` |
| SC3 — Rà tài nguyên trước dựng | Mỗi lượt sản xuất có `asset-manifest.json` + `asset-report.json` **trước** bước render; bước render từ chối chạy khi chưa có báo cáo đạt (test tự động trong repo video) | test + log UAT |
| SC4 — Không còn rà video đầu ra chặn đăng | Script rà-video-làm-lại cũ của Mac **không còn nằm trên đường chạy** của cây mới; 7 ngày không lượt nào bị chặn đăng vì rà video | log 7 ngày |
| SC5 — Đăng tự động đủ đích | Gói `READY` → YouTube, FB Page, website, bình luận Page tự chạy; đơn đăng group xuất hiện trong hàng đợi Kira và được Kira xác nhận `posted` | `publish-state.json` + hàng đợi Kira |
| SC6 — Không đăng trùng | 7 ngày: mỗi id đăng (YouTube, FB, group) xuất hiện một lần; đơn Kira có khoá chống trùng | đối chiếu sidecar + hàng đợi |
| SC7 — Lùi được | Diễn tập lùi một job trong cửa sổ trống ≤ 15 phút | `ROLLBACK-DRILL.md` |

## 3. Kiến trúc chạy mới (ba repo)

```
[marketing] runner chiến dịch
   S1 nghiên cứu → S1b kịch bản + asset-requirements.json
[video]  S2 gom tài nguyên → S3 RÀ TÀI NGUYÊN (cổng duy nhất có vòng làm lại, có trần)
         → khoá asset-manifest → S4 storyboard ảnh tĩnh → S5 giọng [voice] → S6 render
         → S7 kiểm kỹ thuật tự động + đóng gói package/<id> (state READY)
[marketing] S8 hàng chờ đăng (tiến trình riêng, từng đích):
         YouTube dài + Short → website (repo news) → FB Page (Reel/bài) → bình luận Page
         → đơn đăng group cho Kira (KIRA-BRIDGE.md)
```

Nguyên tắc:
- **Vòng làm lại chỉ sống ở S2–S3** (trần `runtime.asset_retry_max`, mặc định 2). Hết lượt: thiếu tài nguyên **không bắt buộc** thì hạ cấp tự động (ảnh dự phòng của kênh, cảnh icon/chữ) và gắn cờ `degraded`; thiếu tài nguyên **bắt buộc** hoặc lỗi tất định (file hỏng, không có quyền dùng) thì job dừng `needs-human`, báo Telegram, không dựng.
- **S7 chỉ kiểm kỹ thuật bằng máy** (độ dài, âm thanh không im đầu, đủ khung, đúng tỉ lệ, phụ đề có). Không còn agent "xem video rồi bắt làm lại".
- **S8 không bao giờ gọi lại S2–S3.** Đăng lỗi chỉ thử lại đích đó, có trần.
- Chi tiết S1b–S7: `agent-video-studio/docs/plans/macmini-media-sync/PLAN.md`. Chi tiết S8 và Kira: mục 6 và `KIRA-BRIDGE.md`.

## 4. Bảo vệ dữ liệu Mac — luật cứng

### 4.1 Vùng bảo vệ
`~/Repo/**` (clone cũ, trạm nhúng, repo web) · mọi `~/Library/LaunchAgents/*.plist` · crontab · thư mục automation của Codex và các agent khác trên máy · cấu hình harness (`~/.codex`, `~/.claude`) · mọi thư mục chiến dịch, tài liệu, script riêng mà pha 1 tìm thấy. Kho secret và mọi `.env*`: **cấm đọc**, chỉ `stat`.

### 4.2 Luật
1. Không `git pull/checkout/clean/reset --hard/stash/commit` trong clone hay trạm cũ; không `migrate-layout --apply`, `import --force`, `init` trỏ vào trạm cũ.
2. Chép bằng `rsync -a` **không** `--delete`/`--remove-source-files`, hoặc `cp -Rp`. Không `mv` từ vùng bảo vệ. Không xoá gì.
3. Không chép `.env` cũ sang cây mới: Codex sinh `.env.example` chỉ có **tên** khoá, chủ máy tự điền.
4. Lịch cũ **không bị dừng** trước P5. Ở P5, đổi một job chỉ bằng `launchctl bootout gui/$UID/<label>` rồi cài plist mới, trong **khe trống** giữa hai lượt của job đó (khe gợi ý 12:00–16:30 giờ Mac, Codex xác nhận lại bằng lịch thật ở P1), khi `launchctl print` = `not running` và `logs/jobs/running/` rỗng. Cấm `install_launchd.py --uninstall`; `install_launchd.py` không `--dry-run` chỉ ở P5, sau khi plist cũ đã sao lưu và so băm.
4b. UAT và lệnh nặng của cây mới (render, TTS, `claude -p`) chỉ chạy khi không có job cũ đang chạy, một lượt một lần, để không tranh RAM và hạn mức với lịch thật.
5. `brew`: chỉ cài gói thiếu, `HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1`, cấm `brew upgrade`.
6. Mọi lệnh của cây mới chạy dưới `env -i` + PATH tối thiểu; đường nào in ra nằm dưới `~/Repo` → dừng.
7. Không đẩy dữ liệu máy (inventory, script riêng, log) lên repo công khai. Code mới đẩy lên GitHub phải qua cổng chống rò của từng repo (`tests/test_no_identity_leak.py`, `tests/test_no_leak.py`).

### 4.3 Thay đổi được phép trong vùng bảo vệ (danh sách đóng)
| Thay đổi | Khi nào |
|---|---|
| File do lịch cũ tự ghi (`out/**`, `logs/**`, sổ đăng, repo web) | trước cutover |
| Nối dòng vào `MAY-DANG-CHAY.md` | sau sao lưu, lúc cutover |
| Plist `studio.marketing.*` được `bootout` và thay bằng plist cây mới | cutover |
| Chép **bản sao** sổ đăng của cây mới về trạm cũ | chỉ khi lùi |

### 4.4 Sao lưu nóng (lịch vẫn chạy)

1. Đọc lịch thật (P1) để chọn thời điểm **không có job nào đang chạy và không job nào sắp chạy trong 60 phút**; xác nhận bằng `launchctl print` từng job + `logs/jobs/running/` rỗng ở mọi chiến dịch.
2. Chép plist hiện có vào sao lưu trước (không đổi gì ở `~/Library/LaunchAgents/`).
3. `tar` vùng bảo vệ (trừ secret, `.env*`, venv, cache, `out/**/*.mp4`), rồi manifest M0.
4. Nếu trong lúc sao lưu có job bắt đầu chạy (kiểm lại bằng `launchctl print` sau khi tar xong) → đánh dấu bản sao lưu là **không nhất quán**, chờ job xong và làm lại ở khe trống kế tiếp.
5. Sổ đăng (`*.published.json`, `truyen-state.json`, `covered-repos.json`…) lấy ở sao lưu này **chỉ để chạy khô**; bản dùng chạy thật được chép lại ngay lúc chuyển từng job ở P5.

## 5. Pha và cổng

Kế hoạch có 6 **pha** với 4 cổng người. Việc chi tiết từng repo nằm trong PLAN của repo đó; bảng dưới là thứ tự chung.

**Ai làm gì (chủ máy chốt 25/11):** **Codex** làm toàn bộ tác vụ, ở hai phiên: **Codex-W** (Windows) và **Codex-M** (Mac mini); Codex được tự đẩy nhánh `macmini-media-sync` và mở PR. **Claude** chỉ tham mưu ở **đầu** (lập kế hoạch — đã xong) và **cuối** (đọc tài liệu, đánh giá, khuyến nghị chốt). **Chủ máy** chuyển prompt giữa các phiên (chưa có kênh gọi chéo chuẩn), trả lời câu hỏi ở cổng, gộp PR.

**Kênh phối hợp hai máy = chính tài liệu kế hoạch trong repo:** mỗi phiên Codex đọc và cập nhật `PROGRESS.md` (thư mục này) trên nhánh `macmini-media-sync`, đẩy lên GitHub; phiên bên kia `git pull` để đọc. `PROGRESS.md` chỉ ghi bản **đã làm sạch** (số đếm, trạng thái, mã lỗi, quyết định) — repo công khai. Chi tiết máy (tên giọng, đường máy, nội dung script riêng, log thô) ở lại Mac trong `~/Studio-next/_sprint-evidence/`.

| Pha | Phiên | Việc | Cổng ra |
|---|---|---|---|
| P0 — Chuẩn bị mã | Codex-W | Tạo nhánh `macmini-media-sync` ở 3 repo; commit 5 file kế hoạch + `PROGRESS.md`; xử lý commit `ac72677` (đưa lên nhánh/PR riêng của repo video) và đề xuất tag `v0.10.1`; README sửa dở: **hỏi chủ máy**, không tự commit; đẩy nhánh | tự kiểm, ghi `PROGRESS.md` |
| P1 — Kiểm kê + sao lưu (chỉ đọc) | Codex-M | Kiểm kê máy, lịch, chiến dịch, **script rà ảnh/làm lại cũ**, cách Kira đang được dùng; sao lưu **nóng** (lịch vẫn chạy) + manifest M0 + thử khôi phục mẫu | **Cổng A**: chủ máy chốt quyết định (mục 7) theo bản tóm tắt trong `PROGRESS.md` |
| P2 — Đóng gói xuống Mac | Codex-M | `git clone` 3 repo vào `~/Studio-next/`; venv chung python3.12; `libs fetch gsap`; dựng 3 trạm mới bằng **bản chép** dữ liệu Mac; 3 doctor; `-ResolveOnly` | tự kiểm |
| P3 — Chuẩn hoá theo cơ chế mới | Codex-W hoặc Codex-M (một phiên một repo tại một lúc) | Video: cổng tài nguyên S1b–S3, đóng gói S7. Marketing: runner đổi thứ tự, bỏ rà video đầu ra, hàng chờ S8, cầu Kira. Voice: khoá `darwin`, ghi số đo MPS. Test trước; PR; CI Windows + macOS xanh; Codex tự review bằng agent review riêng trước khi báo xong | **Cổng B**: chủ máy gộp PR |
| P4 — Chạy khô đầu–cuối | Codex-M (cây mới, sau khi kéo bản gộp) | `-Uat` Hot/Weekly/Repo khi không có job đang chạy; truyện chỉ kiểm rời; thử Kira với **group thử**; manifest vùng bảo vệ trước/sau mỗi lượt | **Cổng C**: chủ máy duyệt danh sách job chuyển lịch |
| P5 — Chuyển lịch | Codex-M | Từng job tin: đổi plist cũ → mới trong khe trống giữa hai lượt, đồng bộ sổ đăng cũ→mới (so băm), lượt thật đầu có người xem. Truyện sau cùng | **Cổng D** (truyện): chủ máy duyệt riêng |
| P6 — Theo dõi 7 ngày + đánh giá cuối | Codex-M; Claude | `REPORT.md` + `MONITOR-7D.md` (bản làm sạch vào repo); **Claude đọc toàn bộ tài liệu và ra khuyến nghị chốt**. Lùi ngay nếu job đỏ 2 lượt liền hoặc đăng trùng | đóng |

**Lịch chạy tự động không dừng** trong suốt kế hoạch (chủ máy chốt 25/11). Hệ quả: sao lưu là sao lưu nóng (mục 4.4); việc đổi lịch duy nhất là ở P5, đổi từng job trong khe trống giữa hai lượt của chính job đó, nên kênh không mất lượt nào.

## 5b. Gói dữ liệu ngoài git từ Windows sang Mac (P0, Codex-W)

Ba repo chỉ mang mã. Những thứ Mac cần mà **không có trên GitHub** được Codex-W gom thành một gói zip ở máy Windows, chủ máy chuyển sang Mac (ổ ngoài, AirDrop hoặc chép trong mạng nhà — **không** qua repo, không qua dịch vụ công khai). Gói nằm ngoài mọi repo, không bao giờ commit.

| Phần | Nguồn trên Windows | Cách gom | Mặc định |
|---|---|---|---|
| Giọng | trạm voice: `profiles/*/voice`, `music/library`, `music/channels`, `station.json` | `voice-studio export --personal --with-music-channels --out <gói>/voice.zip` (gói tự bỏ `raw/`, `lab/`, `report/`, `archive/`, khoá `venv`) | có |
| Bản thu gốc giọng | `profiles/*/raw` (~1,2 GB, nhạy cảm) | zip riêng `voice-raw.zip` | **chỉ khi chủ máy cho** |
| Kho giọng cũ đã cất | trạm voice `archive/` (~1,8 GB) | zip riêng `voice-archive.zip` (đồng thời là bản sao lưu ngoài máy — việc mở #10 của STATUS-HANDOFF trạm voice) | chủ máy chọn |
| Asset hình | trạm video `assets/` (~40 MB: font, overlay, nền, logo kênh, ảnh tham chiếu thiết kế) | zip `video-assets.zip`, giữ đường tương đối | có |
| Cấu hình kênh/chiến dịch | trạm marketing (git cục bộ): `channel.yml`, `campaign.md`, `run.ps1`, tài liệu kênh, `_agent-call/engines.json` | `git bundle create <gói>/marketing.bundle --all` | có — Mac chỉ **đối chiếu**, không đè (DN-A1) |
| Sổ đăng, `out/`, `logs/` của Windows | trạm marketing | không gom | không — Mac là máy chạy lịch, sổ Mac thắng |
| Dự án video cũ | trạm video `projects/` (~8 GB) | không gom | không |

Gói kèm `PACK-MANIFEST.sha256` (mọi file) và `PACK-README.md` (danh sách phần, cỡ, lệnh nhập ở Mac). Ở Mac, Codex-M kiểm sha256 trước khi dùng và chỉ nhập vào **trạm mới** (P2).

**Thứ tự engine agent (đã đồng bộ 25/11):** cả hai máy dùng `codex Astra → codex Sol → claude Opus → Antigravity (agy)`. Cấu hình theo máy ở `<trạm marketing>/_agent-call/engines.json` (ngoài repo). Windows đã sửa theo Mac; ở P2 Codex-M giữ nguyên file của Mac khi chép trạm và đọc lại slug model từ cache Codex của Mac.

## 6. Đăng bài sau đóng gói (S8)

- Đầu vào duy nhất: `package/<id>/package.json` ở trạng thái `READY` (do repo video tạo, đổi tên nguyên tử từ `package.tmp-<id>/`).
- Trạng thái từng đích trong `package/<id>/publish-state.json`: `pending → claimed(lease_until) → posted(id,url) | failed(n) | expired`. Ghi `claimed` **trước** khi gọi API; lượt sau gặp `claimed` hết hạn thì đọc lại kênh trước khi thử lại. Sidecar cũ `<ngày>-top.json.published.json` vẫn ghi song song để guard hiện có còn hiệu lực.
- Thứ tự mặc định: YouTube (dài, Short) → website (repo web) → FB Page → bình luận Page (link YouTube/website) → **đơn group cho Kira**.
- Khoá chiến dịch (lock + lease) để hai lượt launchd không cùng đăng. Trần thử lại mỗi đích 3; hết hạn mức (exit 4) không tính lỗi. Tin nóng quá 24 giờ: `expired`, không đăng tự động.
- mp4 chỉ xoá khi mọi đích đã ở trạng thái cuối.
- Mỗi đích đúng **một** adapter, khai trong `channel.yml: publish.targets`. Đích group luôn là `kira`; nhánh Graph group cũ tắt.
- Hợp đồng với Kira: `KIRA-BRIDGE.md`.

## 7. Quyết định cần chủ máy

**Đã chốt (chủ máy, 25/11):**

| Mã | Quyết định |
|---|---|
| DN-PRE1 — Lịch khi sao lưu | **Không dừng.** Lịch tự động tiếp tục chạy trên Mac; sao lưu nóng theo mục 4.4 |
| DN-PRE2 — Phối hợp Windows ↔ Mac | Qua tài liệu kế hoạch trong repo (`PROGRESS.md` trên nhánh `macmini-media-sync`) + chủ máy dán prompt vào từng phiên; chỉ ghi bản đã làm sạch |
| DN-PRE4 — Quyền của Codex | Codex làm toàn bộ tác vụ, **được đẩy nhánh và mở PR**; không đẩy thẳng `main`, không tag, không tự gộp PR khi chủ máy chưa cho |
| Vai Claude | Chỉ tham mưu đầu (kế hoạch) và cuối (đánh giá, khuyến nghị chốt) |

**Còn mở, có mặc định:**

| Mã | Câu hỏi | Mặc định nếu chủ máy không nói khác |
|---|---|---|
| DN-PRE3 — Nơi sao lưu | ổ ngoài / ổ trong | ổ ngoài nếu đang cắm; không có thì `~/Studio-next/_backup/` (chỉ chống lỗi thao tác, không chống hỏng ổ) và Codex ghi rõ điều này vào `PROGRESS.md` |

**Ở Cổng A (sau kiểm kê):**

| Mã | Câu hỏi | Khuyến nghị |
|---|---|---|
| DN-A1 — Nguồn sự thật theo loại file | cấu hình chiến dịch lấy mẫu mới từ repo; sổ đăng + `out/` + `logs/` lấy từ Mac | như khuyến nghị; chiến dịch chỉ có ở Mac nâng tay từng cái, có diff cho Cổng C |
| DN-A2 — Kênh nào chạy máy nào lâu dài | bảng kênh → máy | Codex đề xuất từ kiểm kê; Windows tắt task trùng trước cutover |
| DN-A3 — Script rà ảnh/làm lại cũ | phần nào giữ làm luật cho cổng S3, phần nào bỏ | quyết theo báo cáo pha 1 |
| DN-A4 — Kira được báo bằng cách nào | xem `KIRA-BRIDGE.md` mục 3 | hàng đợi + Kira tự quét theo lịch |
| DN-A5 — YouTube privacy | lượt thật đầu mỗi job sau cutover | `private` rồi chủ máy chuyển public |

**Điều kiện cứng Cổng A:** đĩa trống ≥ 3 × (cỡ sao lưu + cỡ trạm chép).

## 8. Rủi ro

Kế hoạch có 8 **rủi ro** (RK):

| Mã | Rủi ro | Giảm thiểu |
|---|---|---|
| RK1 — Đăng trùng | sổ đăng lệch lúc cutover/lùi; hai máy cùng chạy | đồng bộ sổ có danh sách + so băm; luật một máy (`docs/RUNBOOK-DOI-MAY.md`); khoá chống trùng trong đơn Kira |
| RK2 — Mất dữ liệu chiến dịch | lệnh chạm cây cũ | mục 4; manifest M0/M1; sao lưu ngoài có thử khôi phục |
| RK3 — Cây mới ghi vào cây cũ | biến môi trường cũ | không chép `.env`; `env -i`; `path-audit` |
| RK4 — Đăng thật khi đang kiểm | runner truyện không có `-Uat` | không chạy runner truyện trước Cổng D |
| RK5 — Cổng tài nguyên quá chặt | tin nóng không ra bài | hạ cấp `degraded` thay vì chặn; chỉ tài nguyên bắt buộc mới chặn |
| RK6 — Kira không nhận/đăng sai | agent trình duyệt có thể lỗi, phiên đăng nhập hết hạn | đơn có trạng thái + hạn; quá hạn báo Telegram cho chủ máy đăng tay; không bao giờ tự đăng lại khi chưa rõ |
| RK7 — Rủi ro tài khoản Facebook | thao tác tự động trên tài khoản cá nhân | giới hạn số bài/ngày, giãn cách, chỉ group chủ máy liệt kê |
| RK8 — Lộ dữ liệu máy lên repo công khai | Codex chép chi tiết máy vào code/tài liệu | cổng chống rò bắt buộc xanh; bằng chứng máy để ngoài repo |

## 9. Đường lùi

Trong cửa sổ trống: `bootout` plist mới của job → chờ `running/` rỗng → chép bản sao sổ đăng mới về trạm cũ (so băm) → `bootstrap` plist cũ từ sao lưu → nối dòng vào `MAY-DANG-CHAY.md`. Cây cũ không dọn trong kế hoạch này; sao lưu giữ ≥ 30 ngày.
