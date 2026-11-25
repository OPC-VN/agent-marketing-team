---
title: PROGRESS — macmini-media-sync (shared log between Codex-W and Codex-M)
date: 2026-11-25
status: open
rules: append-only; sanitized (public repo — no real voice names, account names, machine paths, raw logs); each entry = date-time · session (W/M) · phase
---

# PROGRESS — macmini-media-sync

Nhật ký chung của hai phiên Codex. Thêm mục ở cuối, không sửa mục cũ. Định dạng: `HANDOFF-CODEX.md` mục 5.

## Đang giữ repo

| Repo | Phiên đang sửa | Từ lúc |
|---|---|---|
| agent-marketing-team | — | — |
| agent-video-studio | — | — |
| agent-voice-studio | — | — |

## Quyết định của chủ máy

| Mã | Giá trị | Ngày |
|---|---|---|
| Lịch Mac | không dừng; sao lưu nóng | 25/11 |
| Phối hợp | PROGRESS.md + chủ máy dán prompt | 25/11 |
| Quyền đẩy | Codex đẩy nhánh `macmini-media-sync`, mở PR; chủ máy gộp | 25/11 |
| Thứ tự engine | codex Astra → codex Sol → claude Opus → agy (Windows đã đổi theo Mac) | 25/11 |
| DN-PRE3 nơi sao lưu | mặc định: ổ ngoài, không có thì `~/Studio-next/_backup/` | 25/11 |
| DN-A1…A5, DN-K1…K4 | (điền ở Cổng A) | |

## Cần chủ máy

- W-P0 · Chủ máy đã chốt ba lựa chọn. Xem mục chốt W-P0 trong nhật ký.

## Nhật ký

- 2026-11-25 · Claude (Windows) · lập kế hoạch — Kế hoạch rev 4 viết vào 3 repo. Chưa có phiên Codex nào chạy.

- 2026-11-25 10:45 ICT · Codex-W · W-P0 — Đã đẩy kế hoạch từ `origin/main` lên nhánh `macmini-media-sync` ở ba repo. Gói chuyển máy đang chờ quyết định về phần marketing.

  | Repo | Commit kế hoạch | PR nháp | Cổng chống rò |
  |---|---|---|---|
  | Marketing | `2aa882f` | [#19](https://github.com/OPC-VN/agent-marketing-team/pull/19) | 31 đạt |
  | Video | `006b602` | [#18](https://github.com/OPC-VN/agent-video-studio/pull/18) | 17 đạt |
  | Voice | `691a243` | [#7](https://github.com/OPC-VN/agent-voice-studio/pull/7) | 10 đạt |

  - **Chứng cứ Git.** `python -m pytest -q --tb=no tests/test_no_identity_leak.py` ở ba repo, thêm `tests/test_no_leak.py` ở marketing, đều thoát 0. GitHub xác nhận ba PR nháp đều mở, đích `main`. Commit gốc `ac72677` có [PR riêng #17](https://github.com/OPC-VN/agent-video-studio/pull/17). Cổng chống rò và bốn tệp test của skill short đạt 52 kiểm tra, thoát 0. Đề xuất chủ máy cân nhắc tag `v0.10.1` ở mốc phát hành `75fac7a`. Đây là mốc đã gộp bản phát hành.
  - **Chứng cứ gói.** Voice Studio export thoát 0. Hai ZIP qua kiểm danh sách tệp và CRC. `PACK-README.md` cùng hai ZIP khớp `PACK-MANIFEST.sha256`, xác minh ba tệp. Dung lượng dùng MB thập phân.

  | Tệp | MB | SHA-256 |
  |---|---:|---|
  | `voice.zip` | 157,86 | `fcacfcd57777121a6ae1fc7f6822f366c99866dca1687c8afa8c0b13bcf2da56` |
  | `video-assets.zip` | 40,95 | `b407953b3dfff45762c624bb96673e24d71a97871cab2eed62e634e055e2a56d` |

  - **Lệch so với kế hoạch.** Tạm dừng `marketing.bundle` vì lịch sử nguồn có sổ đăng, đầu ra, log và đường dẫn tệp có nguy cơ chứa thông tin xác thực. Cần quyết định về bản chụp cấu hình đã lọc.
  - **Cần chủ máy.** Chọn cách đóng gói marketing, giữ hay bỏ các sửa dở trong README, và có kèm hai ZIP giọng tùy chọn hay không. Các sửa dở trong README vẫn ở checkout gốc.

- 2026-11-25 · Codex-W · W-P0 — GitHub Actions trên nhánh của PR video riêng báo lỗi ở ba job pytest Windows. Test `test_effect_distribution_build.py::test_isolated_wheel_and_sdist_round_trip` cũng lỗi trên `main` ở Python 3.12. Cổng chống rò và test short chạy riêng trên Windows đạt. [CI nhánh video](https://github.com/OPC-VN/agent-video-studio/actions/runs/45541897461) · [CI main](https://github.com/OPC-VN/agent-video-studio/actions/runs/45250908785).

- 2026-11-25 10:54 ICT · Codex-W · W-P0 — Hoàn tất phần Windows. Chủ máy chọn bản chụp marketing đã lọc, giữ các sửa dở README ở checkout gốc và bỏ hai ZIP giọng tùy chọn.

  - **Gói hoàn chỉnh.** `marketing.bundle` gồm 28 tệp cấu hình kênh, chiến dịch, runner, tài liệu kênh và cấu hình engine trong một commit trên nhánh `macmini-snapshot`. Dung lượng 0,127 MB. SHA-256 `b7e8add1c97478563ddd057e64b4f150e7c567787453ba5f9ad41ec109bb43dd`.
  - **Chứng cứ.** `git bundle verify` và clone từ bundle đều thoát 0. Đã đối chiếu danh sách, nội dung từng tệp và xác nhận bundle có một nhánh, một commit. `sha256sum -c PACK-MANIFEST.sha256` thoát 0 với cả bốn tệp được liệt kê. Cổng chống rò marketing trên bản cập nhật cuối đạt 31 kiểm tra, thoát 0.
  - **Lệch so với kế hoạch.** Bundle dùng lịch sử mới theo quyết định của chủ máy. Bản chụp dùng để đối chiếu khi thực hiện DN-A1. Mac giữ cấu hình máy đích, lịch và sổ đăng.
  - **Bàn giao.** Chủ máy chuyển thư mục gói sang Mac. Codex-M bắt đầu P1 theo `HANDOFF-CODEX.md` và kiểm manifest trước khi dùng dữ liệu ở P2.
