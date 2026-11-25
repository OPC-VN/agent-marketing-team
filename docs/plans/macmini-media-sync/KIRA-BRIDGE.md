---
title: Kira bridge — how the pipeline hands Facebook Group posts to the Kira browser agent
date: 2026-11-25
status: draft_waiting_owner_decisions
master: PLAN.md (this folder), section 6
---

# Cầu nối Kira — đơn đăng Facebook Group

## 1. Kira là gì (theo chủ máy, 25/11)

- **Kira** là một agent chủ máy dựng trên ChatGPT, có khả năng **thao tác trình duyệt như người**: mở group, soạn bài, đăng, bằng tài khoản Facebook chủ máy cho phép, trong trình duyệt đã đăng nhập sẵn.
- Lý do cần Kira: Meta đã bỏ đăng bài vào group qua Graph API, nên nhánh group trong `scripts/runners/post_facebook.py` và `scripts/pipeline/fb_publish.py` **không còn là đường đăng**. Agent trình duyệt là đường tự động duy nhất còn lại.
- **Chưa biết** (pha P1 phải làm rõ, Codex ghi vào bằng chứng ngoài repo): Kira chạy trên trình duyệt nào (trình duyệt agent của ChatGPT trên đám mây, hay trình duyệt có agent trên chính Mac mini); Kira đọc được nguồn nào (Google Drive/Sheets, Gmail, URL công khai); Kira có chạy theo lịch được không; chủ máy hiện gọi Kira thế nào.

## 2. Nguyên tắc

1. Pipeline **không đợi** Kira. S8 tạo đơn group rồi kết thúc lượt; Kira xử lý sau.
2. Đơn có **trạng thái** và **hạn**; mọi bên chỉ đổi trạng thái theo một chiều.
3. **Một bài chỉ đăng một lần**: khoá chống trùng `<package_id>:<group_key>`; Kira tìm bài đã có trong group trước khi đăng.
4. Kira gặp đăng nhập hết hạn, xác minh danh tính, CAPTCHA hay cảnh báo của Facebook → **dừng, đánh dấu `failed: needs_login`**, không cố vượt. Chủ máy tự xử lý trên trình duyệt.
5. Giới hạn nhịp: tối đa số bài/ngày và khoảng giãn giữa hai bài do chủ máy đặt trong `channel.yml`.
6. Không có mật khẩu, cookie hay token nào nằm trong đơn.

## 3. Báo cho Kira bằng cách nào — chủ máy chọn (DN-A4)

| Cách | Cách làm | Đánh đổi & rủi ro | Công sức | Khi nào chọn |
|---|---|---|---|---|
| **A — Hàng đợi chung + Kira tự quét theo lịch (KHUYẾN NGHỊ)** | S8 ghi đơn vào một **Google Sheet riêng** (hoặc thư mục Drive) Kira đọc được qua connector; Kira chạy theo lịch (ví dụ 3 lần/ngày trong giờ đăng), lấy đơn `pending`, đăng, ghi lại `posted` + URL bài | Trễ tối đa bằng chu kỳ quét; cần Kira có quyền đọc/ghi sheet và chạy theo lịch được; pipeline cần một khoá dịch vụ ghi sheet (để trong kho secret, chỉ biết **tên** biến) | vừa | Kira là agent ChatGPT trên đám mây có connector Google — **khả năng cao nhất** |
| B — Kích hoạt tại chỗ trên Mac | S8 mở trình duyệt có agent trên Mac với lời nhắc chứa đơn (lệnh `open` + đường dẫn sâu), Kira chạy ngay trong phiên đã đăng nhập | Gần như tức thời, nhưng phụ thuộc giao diện app (dễ gãy khi app cập nhật), cần phiên người dùng đang mở, khó biết kết quả | vừa–cao | Kira chạy trong trình duyệt agent cài ngay trên Mac mini và A không làm được |
| C — Nhắn chủ máy, chủ máy chuyển cho Kira | S8 gửi Telegram/email: nội dung bài + link + danh sách group; chủ máy dán cho Kira | An toàn nhất, nhưng không tự động | thấp | Dùng làm **đường dự phòng** khi đơn quá hạn ở A/B, hoặc tạm thời trong lúc dựng A |

Khuyến nghị: **A làm đường chính, C làm đường dự phòng** (đơn `pending` quá hạn → Telegram cho chủ máy).

## 4. Đơn đăng group (hợp đồng dữ liệu)

Mỗi đơn là một dòng (sheet) hoặc một file JSON (Drive). Pipeline giữ bản gốc ở `package/<id>/kira-orders.json`.

| Trường | Ai ghi | Nghĩa |
|---|---|---|
| `order_key` | pipeline | `<package_id>:<group_key>` — khoá chống trùng |
| `group_key`, `group_url` | pipeline | lấy từ `channel.yml: publish.targets.facebook_group.groups[]` (chủ máy khai) |
| `caption` | pipeline | lời đăng đã tái định dạng cho group (không lộ tên công cụ nội bộ — luật `AGENTS.md` §4.5) |
| `link` | pipeline | link YouTube hoặc trang website của bài (đã đăng ở bước trước) |
| `media_url` | pipeline | tuỳ chọn: link tải video/ảnh nếu chủ máy muốn đăng kèm file (DN-K2) |
| `not_before`, `expires_at` | pipeline | không đăng trước / sau mốc này (tin nóng: 24 giờ) |
| `state` | pipeline tạo `pending`; Kira đổi | `pending → claimed → posted / failed / expired` |
| `claimed_at` | Kira | Kira nhận đơn |
| `posted_url`, `posted_at` | Kira | link bài trong group |
| `error` | Kira | `needs_login`, `group_rejected`, `duplicate_found`, khác |

Pipeline đọc lại sheet ở lượt sau (hoặc job kiểm riêng) để cập nhật `publish-state.json` đích `facebook_group` và báo Telegram: số đơn `posted`, `failed`, quá hạn.

## 5. Bộ chỉ dẫn cho Kira (chủ máy dán vào cấu hình Kira)

Bản nháp — chủ máy chỉnh theo cách Kira đang chạy:

1. Mở hàng đợi đơn đăng group. Chỉ xét đơn `state = pending`, `not_before` đã qua, `expires_at` chưa qua.
2. Mỗi lượt xử lý tối đa `N` đơn (chủ máy đặt), giãn cách ít nhất `M` phút giữa hai bài.
3. Với mỗi đơn: đổi `state = claimed`, ghi `claimed_at`. Mở `group_url`. Tìm trong group bài gần đây có cùng link hoặc dòng đầu caption; có rồi → `state = failed`, `error = duplicate_found`, ghi link bài đã có, sang đơn khác.
4. Đăng caption + link (và file nếu có `media_url` và chủ máy cho phép). Chờ bài hiện ra, lấy link bài → `state = posted`, ghi `posted_url`, `posted_at`.
5. Gặp màn đăng nhập, xác minh, CAPTCHA, cảnh báo vi phạm, hay group yêu cầu duyệt bài → dừng đơn đó, `state = failed` với `error` tương ứng; **không** cố vượt; dừng cả lượt nếu là lỗi đăng nhập.
6. Đơn đã `expired` hoặc `posted` không bao giờ đăng lại.

## 6. Việc trong repo marketing

| Mã | Việc |
|---|---|
| TK-K1 — Adapter `kira` ở S8 | ghi đơn vào hàng đợi theo cách chủ máy chọn (A: Google Sheets API bằng khoá dịch vụ, tên biến `KIRA_QUEUE_CONFIG` trỏ file trong kho secret; C: Telegram qua `scripts/lib/telegram_io.py`); idempotent theo `order_key` |
| TK-K2 — Đọc lại trạng thái | job kiểm (hoặc đầu lượt S8) đọc hàng đợi, cập nhật `publish-state.json`, báo Telegram, chuyển đơn quá hạn sang đường C |
| TK-K3 — Tắt nhánh group Graph | `post_facebook.py`/`fb_publish.py`: nhánh group chỉ còn khi `adapter: graph` khai rõ (mặc định tắt), ghi CHANGELOG |
| TK-K4 — Mẫu cấu hình | `channel.yml` mẫu thêm `publish.targets.facebook_group` (adapter, groups, giới hạn nhịp); `.env.example` thêm tên `KIRA_QUEUE_CONFIG` |
| TK-K5 — Test | đơn trùng không tạo lần hai; đơn quá hạn chuyển C; thiếu cấu hình → exit 2 rõ ràng; không có giá trị secret trong log |

## 7. Quyết định riêng của cầu nối

| Mã | Câu hỏi | Khuyến nghị |
|---|---|---|
| DN-K1 — Cách báo Kira | A / B / C (mục 3) | A + C dự phòng |
| DN-K2 — Đăng group kèm file hay chỉ link | file cần Kira tải được từ link | **chỉ link + caption** ở bản đầu (Facebook tự hiện xem trước); thêm file sau khi A chạy ổn |
| DN-K3 — Giới hạn nhịp | số bài/ngày, giãn cách | bắt đầu thấp (ví dụ 3 bài/ngày, cách ≥ 30 phút) để giảm rủi ro tài khoản |
| DN-K4 — Thử ở đâu | group thử riêng trước khi bật group thật | có — pha P4 chỉ dùng group thử |
