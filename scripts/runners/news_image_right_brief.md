## Hợp đồng bàn giao video ảnh phải

Mỗi cảnh có ảnh tĩnh riêng, lưu cục bộ cạnh JSON hoặc trong thư mục con của nó, và infographic
riêng dưới tiêu đề ở cột trái. Áp dụng cho mở đầu, toàn bộ các chương và cảnh kết, ở cả Full và Short.
Hợp đồng này bổ sung các trường sau vào schema của brief và ưu tiên hơn chỉ dẫn media cũ.

- Trong `top_story`, khai `cover_visual`, `sections` và `outro_visual`. Cảnh mở và kết cũng có
  `title`, `diagram`, `asset_proof`. Trong chương giữ lời đọc `lead` và `narration_short`.
  Lời mở/kết giữ tại `intro`, `intro_short`, `outro`, `outro_short`. Nếu số chương đã được chốt
  trong brief chiến dịch, giữ số đó.
- Trong mỗi `diagram`, có `type` (process, tags, bullets, timeline, compare, stats hoặc bars),
  `title`, `items` là 2–4 hành động ngắn; mỗi phần tử có `t`, `d`, `icon`. Chọn icon theo nghĩa:
  search, profile, chat, chart, edit, check, handoff, list, shield. HyperFrames làm các bước hiện lần lượt.
- Mỗi cảnh có `asset_proof` với `route: image`, `image` (đường tương đối),
  `asset_url`, `fact_source_url`, `credit`, `relevance`, `motion_cue`.
  Ảnh bên phải phải là file ảnh tĩnh, riêng cho cảnh, minh họa đúng đối tượng hoặc thao tác. Ảnh nguồn
  cần xem và đối chiếu chú thích, URL nguồn, căn cứ sử dụng; ảnh minh họa ghi rõ vai trò. Nếu thiếu,
  sai hay trùng, đổi truy vấn theo thực thể và thao tác rồi tìm lại. Nếu vẫn thiếu, báo `MEDIA_BLOCKED`
  kèm cảnh và lý do. Infographic, GIF, clip, logo chung và hình giữ chỗ không dùng thay ảnh.
- Trước khi bàn giao, nhìn hai tỷ lệ để kiểm hai cột xuất hiện đồng thời, thẻ đọc rõ và phụ đề
  không che ảnh. Nếu cột Short chật, rút nhãn và mô tả hành động trước.
