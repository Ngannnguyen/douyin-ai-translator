# Hướng dẫn tải gói lên GitHub

Repository: `https://github.com/Ngannnguyen/douyin-ai-translator`

## Bước 1 — Giải nén

Giải nén tệp `Douyin_AI_Translator_GitHub_Upload_v0.2.1.zip` vào một thư mục mới.

Sau khi giải nén, bạn phải nhìn thấy trực tiếp các mục như:

- `.github`
- `douyin_translator`
- `app.py`
- `requirements.txt`
- `README.md`

Không tải nguyên tệp ZIP vào repository vì GitHub Actions không đọc mã nguồn bên trong ZIP.

## Bước 2 — Tải mã nguồn

1. Mở repository trên trình duyệt.
2. Bấm **uploading an existing file**. Nếu nút này không còn, chọn **Add file → Upload files**.
3. Trong thư mục vừa giải nén, nhấn `Ctrl + A` để chọn toàn bộ.
4. Kéo tất cả vào vùng **Drag files here** trên GitHub.
5. Chờ danh sách tệp xuất hiện đầy đủ.
6. Ở ô commit message, nhập: `Khoi tao Douyin AI Translator Sprint 1`.
7. Bấm **Commit changes**.

## Bước 3 — Theo dõi build EXE

1. Mở thẻ **Actions** của repository.
2. Chọn workflow **Tao ban Windows EXE**.
3. Chờ dấu tròn chuyển thành dấu tích xanh.
4. Mở lần chạy mới nhất.
5. Cuộn xuống mục **Artifacts**.
6. Tải `Douyin_AI_Translator_Windows_v0.2.1`.

Tệp tải từ Artifacts là tệp ZIP. Giải nén rồi mở `Douyin_AI_Translator.exe`.

## Nếu GitHub Actions không tự chạy

Vào **Actions → Tao ban Windows EXE → Run workflow → Run workflow**.

## Lưu ý

- Không cần nhập mật khẩu, token hoặc API key vào mã nguồn.
- Artifact được giữ 30 ngày; mã nguồn vẫn còn trong repository.
- Chỉ xác nhận bản EXE hoàn chỉnh sau khi workflow có dấu tích xanh và ứng dụng mở được trên Windows.
