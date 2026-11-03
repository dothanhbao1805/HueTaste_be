# API guidelines

- Base path: `/api/v1`. Docs tự sinh: `/docs`. Health: `/health`.
- Xác thực: header `Authorization: Bearer <accessToken>`. Access token 30 phút, refresh token 7 ngày (đổi qua `/auth/refresh`).
- Route admin nằm dưới `/admin/...`; user thường nhận 403 `NOT_ADMIN`.
- Response lỗi thống nhất: `{"code": "EMAIL_EXISTS", "message": "..."}`; lỗi validate 422: `{"code":"VALIDATION_ERROR","message":"...","errors":[{"field","message"}]}`.
- Danh sách phân trang: query `page` (≥1), `size` (1–100); response `Page[T]` = `{items,total,page,size}`.
- Tham số lọc/tìm kiếm đặt tên camelCase như field (`vaiTro`, `trangThai`, `q`).
- Mã HTTP: 201 khi tạo, 400 lỗi nghiệp vụ, 401 chưa/ sai token, 403 không đủ quyền/bị khóa, 404 không thấy, 409 trùng.
- CORS cho origin trong `CORS_ORIGINS` (.env) – thêm origin của web admin React ở đó.

## Endpoint hiện có
| Method | Path | Quyền |
|---|---|---|
| POST | /auth/register, /auth/login, /auth/admin/login, /auth/refresh | public |
| POST | /auth/forgot-password, /auth/reset-password | public |
| GET, PATCH | /users/me | user |
| POST | /users/me/change-password | user |
| GET | /admin/users (q, vaiTro, trangThai, page, size), /admin/users/{idNguoiDung} | admin |
| PATCH | /admin/users/{idNguoiDung}/status | admin |
| GET | /danh-muc, /so-thich, /che-do-an, /nguyen-lieu (`?q=&size=`) | public |
| GET | /mon-an (q không dấu, idDanhMucMonAn, nguyenLieu, page, size), /mon-an/{idMonAn} | public |
| GET | /dia-diem (q, viDo, kinhDo, banKinhKm, idMonAn, page, size), /dia-diem/{idDiaDiem} (`anhUrl` là URL ảnh công khai) | public |
| GET, PUT | /users/me/so-thich `{soThich:[{idSoThich,mucDo}]}`, /users/me/che-do-an `{cheDoAn:[{idCheDoAn,ghiChu}]}` | user |
| POST | /goi-y `{viDo,kinhDo,buaAn,nganSach,ghiChu,nguyenLieuTranh,soMon,soDiaDiem}` | user |
| POST | /admin/thu-thap `{loai: mon_an\|dia_diem\|tat_ca, soMon}` → 202 | admin |
| GET, POST | /admin/danh-muc (`soMon` kèm theo; trùng tên 409 `DANH_MUC_EXISTS`) | admin |
| PATCH, DELETE | /admin/danh-muc/{idDanhMucMonAn} (còn món → 409 `DANH_MUC_IN_USE`) | admin |
| GET, PUT | /users/me/nhu-cau (`?ngay=`, mặc định hôm nay) `{ngay?, buaAn, gioAn?, nganSach?, ghiChu?, nguyenLieuTranh?:[idNguyenLieu]}` upsert theo ngày+bữa (PUT ghi đè toàn bộ) | user |
| DELETE | /users/me/nhu-cau/{idNhuCauTheoNgay} | user |
| POST | /uploads (multipart `file`, `?loai=avatar\|mon_an`) → 201 `{url}`; JPEG/PNG/WEBP ≤ `UPLOAD_MAX_MB` | user |
| POST | /users/me/avatar (multipart `file`) → `NguoiDungOut` | user |
| POST | /scan (multipart `file`) → `ScanOut` `{trangThai: CO_TRONG_HE_THONG\|DANG_CAP_NHAT\|CHUA_XAC_MINH\|KHONG_LUU, monAn?, monTuongTu}`; không phải món ăn → 422 `KHONG_NHAN_DIEN_DUOC`; quá `SCAN_TOI_DA_MOI_NGAY` → 429 `SCAN_QUA_GIOI_HAN`; model lỗi hết → 502 `SCAN_KHONG_KHA_DUNG`. App nên thu ảnh về ~1024px trước khi gửi | user |
| GET | /scan/{idLichSuScan} (gọi lại ~3s/lần khi `DANG_CAP_NHAT`), /users/me/lich-su-scan (`page`, `size`) | user |
| GET | /users/me/yeu-thich (`?loai=mon_an\|dia_diem`) → `{monAn, diaDiem}` | user |
| POST | /users/me/yeu-thich `{idMonAn}` hoặc `{idDiaDiem}` → 201 (lặp lại không lỗi) | user |
| DELETE | /users/me/yeu-thich/mon-an/{idMonAn}, /users/me/yeu-thich/dia-diem/{idDiaDiem} | user |
| POST | /danh-gia `{idMonAn\|idDiaDiem, diemSo 1-5, noiDung?}` → 201 (viết lại = cập nhật) | user |
| DELETE | /danh-gia/{idDanhGia} (chỉ chủ đánh giá) | user |
| GET | /mon-an/{id}/danh-gia, /dia-diem/{id}/danh-gia (`page`, `size`) → `{items,total,page,size,diemTrungBinh}` | public |
| POST | /bao-cao `{idDiaDiem, lyDo, moTa?, idMonAn: [..]}` → 201; món phải có ở quán (400 `MON_KHONG_THUOC_QUAN`); đang có báo cáo chờ cho quán → 409 `BAO_CAO_DANG_CHO` | user |
| GET | /users/me/bao-cao (`page`, `size`) | user |
| GET | /admin/bao-cao (`trangThai=CHO_XU_LY\|DA_XU_LY`, `page`, `size`), /admin/bao-cao/{idBaoCao} | admin |
| POST | /admin/bao-cao/{idBaoCao}/xu-ly `{chiTiet:[{idChiTietBaoCao, ketQua: VI_PHAM\|KHONG_VI_PHAM}], anQuan, ketQuaXuLy?}` (đủ mọi món; đã xử lý → 409) | admin |
| GET | /admin/scan/mon-khong-luu → `[{tenMon, soLanScan, soNguoiScan, lanCuoi}]` (món scan không đặc trưng Huế) | admin |
| GET | /admin/thong-ke (`soNgay` 1–90, mặc định 7) → `{tongQuan, goiYTheoNgay, topMonGoiY}` | admin |
| GET | /uploads/{đường dẫn} (ảnh đã tải lên, ngoài `/api/v1`) | public |

`GET /mon-an/{id}`, `GET /dia-diem/{id}` trả thêm `daYeuThich` (true khi gửi token của người đã yêu thích).

`register/login/refresh` trả `TokenOut`: `accessToken`, `refreshToken`, `tokenType`, `nguoiDung`.
