# Cách tìm class cần override trong Vesktop

## Mở DevTools
1. Trong Vesktop, nhấn **Ctrl+Shift+I** để mở DevTools
2. Chọn tab **Elements** (hoặc Inspector)

## Tìm vùng bị patchy
1. Click vào **icon hình ô vuông ở góc trái DevTools** (Inspector cursor)
2. Click vào **vùng bị sai màu** trong Discord
3. Nhìn panel bên phải: tab **Styles** → tìm `background-color` nào đang được applied
4. Copy tên class chính xác (ví dụ: `title_f75fb0`, `container__9293f`)

## Cách báo cáo
Gửi tên class (phần trước dấu `_` + số ngẫu nhiên), ví dụ:
- `title_f75fb0` → báo là `title_`
- `container__9293f` → báo là `container_`

## Kiểm tra CSS Variable có bị override chưa
Trong tab **Computed** của DevTools → tìm `background-color`:
- Nếu thấy `var(--background-primary)` → CSS var đã override đúng
- Nếu thấy màu hex cứng (ví dụ `#1e1f22`) → cần thêm selector override
