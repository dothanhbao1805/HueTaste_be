# Pipeline thu thập dữ liệu & gợi ý theo ngữ cảnh

## Pipeline thu thập (tự động, không cần admin duyệt)
`app/services/thu_thap_service.py`. Điểm vào chung là `chay(loai, so_mon)`, được gọi từ:
- **Worker** `python -m scripts.worker [--chay-ngay]`: APScheduler, tiến trình riêng, không chạy chung uvicorn. Lịch đặt trong `.env`: `LICH_MON_AN` (mặc định 03:00 ngày 1 hằng tháng), `LICH_DIA_DIEM` (03:00 thứ Hai).
- **CLI** `python -m scripts.thu_thap_du_lieu --mon-an --so-mon 20` hoặc `--dia-diem`.
- **Admin** `POST /api/v1/admin/thu-thap` `{loai, soMon}`: chạy bằng BackgroundTasks, trả 202.

### LLM (`app/services/llm_service.py`)
- Thử lần lượt các nhà cung cấp; chưa có key thì bỏ qua, lỗi thì chuyển sang bên kế tiếp. Không có key nào → lỗi `LLM_NOT_CONFIGURED`.
- **Thứ tự riêng cho từng bước** (tham số `thu_tu` của `llm_service.generate_json`, mặc định `LLM_THU_TU`):
  - Liệt kê món mới: `LLM_THU_TU_DANH_SACH=gemini,groq`. Benchmark 31/10/2026: Groq `gpt-oss-120b` trả lại đúng 12 món đã có (lọc trùng xong còn 0 món mới), Gemini `3.6-flash` cho 20 món mới không trùng.
  - Trích tag theo lô: `LLM_THU_TU_TAG=groq,gemini`. Groq 5,6s, 5/5 món, enum đúng 49/49; Gemini Flash-Lite lặp vô hạn (JSON 66K ký tự), Flash chỉ trả 1/5 món.
- **Groq** (`groq_service`): model `openai/gpt-oss-120b`, dự phòng `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`; API tương thích OpenAI, có gói free. Key hiện tại không có Llama để chat; tên model phải lấy từ `GET https://api.groq.com/openai/v1/models`. Groq chỉ có chế độ `json_object` nên schema được đưa vào system prompt và mảng được bọc thành `{"ketQua": [...]}`. Model `GROQ_MODEL`, dự phòng `GROQ_MODEL_DU_PHONG` (model bị ngừng → 404/400 → chuyển ngay).
- **Gemini** (`gemini_service`): ép JSON đúng schema bằng `responseSchema`, giới hạn `maxOutputTokens=GEMINI_MAX_TOKEN_RA` để chặn lặp vô hạn. Model `GEMINI_MODEL` (`gemini-3.6-flash`) rồi `GEMINI_MODEL_DU_PHONG` (`gemini-3.5-flash-lite,gemini-flash-latest`; flash-latest để cuối vì có lúc mất >80s). 503/429 thử lại 3 lần; timeout, 404 (model bị ngừng) hoặc JSON hỏng thì chuyển ngay model kế. Model không dùng được bị bỏ qua 10 phút.
- Cả hai đều có thể trả giá trị ngoài enum: `thu_thap_service` luôn lọc lại theo `app/core/constants.py`.

### Thu thập món ăn (`thu_thap_mon_an`)
1. **LLM** (`llm_service.generate_json`, JSON theo schema) liệt kê món Huế. Prompt gửi kèm danh sách món đã có để LLM không đề xuất lại.
2. **Wikipedia vi** (`wikipedia_service`) xác minh từng món:
   - Tiêu đề bài khớp tên với độ tương đồng ≥ 0.8 → **khớp chắc**: món `active`, lưu `maWikipedia` (pageid), `nguonThamKhao` (URL), `hinhAnh`.
   - Tiêu đề chỉ gần giống (≥ 0.5) nhưng nội dung bài nhắc tới tên món và "Huế" → `active`, nhưng **không** lưu `maWikipedia` (tránh gộp nhầm nhiều món vào một bài chung như "Bún").
   - Không xác minh được → `unverified`: vẫn lưu nhưng API không hiển thị và không gợi ý.
3. **LLM** trích tag theo lô 5 món, đầu vào là đoạn trích Wikipedia. Chỉ nhận giá trị trong enum (`app/core/constants.py`):
   - `buoiPhuHop`, `thoiTietPhuHop` lưu dạng CSV.
   - `vi`/`kieu` → `SoThich` + `MonAnSoThich.trongSo`.
   - `cheDoAn` → `CheDoAn` + `MonAnCheDoAn`.
   - `nguyenLieu` → `NguyenLieu` + `MonAnNguyenLieu`.
   - Giá → `giaThamKhaoTu/Den`.

### Thu thập địa điểm (`thu_thap_dia_diem`)
- Nguồn quán: **Serper** (`serper_service`), gọi `POST https://google.serper.dev/maps` với header `X-API-KEY: SERPER_API_KEY`. Đây là kết quả Google Maps qua bên thứ ba, không cần billing Google Cloud.
  - Serper không công bố schema chi tiết nên `chuan_hoa` parse mềm dẻo: id lấy `placeId` → `cid` → `fid` (lưu vào cột `maGooglePlace`); giờ mở cửa nhận dạng dict hoặc list; mức giá đếm ký hiệu lặp ("₫₫" → 2).
  - Kết quả chuẩn hoá thành dict `id, ten, diaChi, viDo, kinhDo, rating, mucGia, soDienThoai, gioMoCua, anh` rồi mới đưa vào `_luu_quan`.
- Với mỗi món `active` **và `unverified`**, tìm `"<tên món> Huế"` (tên đã có "Huế" thì giữ nguyên) quanh tâm Huế (`HUE_VI_DO/KINH_DO`, zoom 14), rồi loại quán xa hơn `HUE_BAN_KINH_KM`. Mỗi món tốn 1 lượt Serper/tuần.
- **Lớp xác minh thứ hai:** món `unverified` (thường là món Huế ít tài liệu, không có bài Wikipedia) chuyển `active` khi có ít nhất 1 quán trong bán kính Huế **mang tên món** (`ten_mon_trong_ten_quan`), thống kê ở `monXacMinh`. Chỉ "có kết quả" thì chưa đủ vì Google Maps luôn trả quán gần đó. Lớp này chỉ chứng minh món có thật; mô tả/tag vẫn do LLM viết nên có thể sai.
- `ten_mon_trong_ten_quan`: so theo nguyên từ sau `chuan_hoa_ten`, bỏ đuôi "Huế" của tên món khi còn ≥ 2 từ ("Bánh ép Huế" khớp "Bánh ép Bà Đỏ", "Chè Huế" không rút thành "chè"). Dùng chung cho `laMonDacTrung` và cho món từ scan.
- Upsert `DiaDiem` theo `maGooglePlace`, thêm `MonAnDiaDiem`. `laMonDacTrung=True` khi quán mang tên món (`ten_mon_trong_ten_quan`).
- `hinhAnh` lưu `thumbnailUrl` (URL ảnh công khai). API trả nguyên URL này ở `anhUrl`, app tải ảnh thẳng.

### Nhiều ảnh cho món/quán (Serper Images)
- `serper_service.tim_anh` gọi `POST https://google.serper.dev/images`; `chuan_hoa_anh` → `{url, thumbnail, nguon, tieuDe, rong, cao}`. Ảnh lưu ở bảng `AnhMonAn` / `AnhDiaDiem` (migration 0004, unique `(idMonAn|idDiaDiem, urlHash)` với `urlHash = sha256(url)`). `MonAn.hinhAnh` / `DiaDiem.hinhAnh` vẫn là ảnh bìa; nếu trống thì lấy ảnh đầu tiên của gallery.
- Món: `_luu_anh_mon` chạy ngay sau khi món `active` được lưu (`_xu_ly_ung_vien`), sau bước tìm quán (`thu_thap_dia_diem`, cho món vừa được Serper xác minh) và trong `lam_giau_mon` (món từ scan). Từ khoá `"<tên món> Huế món ăn"`. Quán: `_luu_anh_quan` chạy sau `_luu_quan` trong `_tim_quan_cho_mon`; thêm thumbnail Maps rồi 1 lượt Serper Images `"<tên quán> <địa chỉ>"`.
- Lọc (`_them_anh`): URL http(s), `imageWidth` ≥ `THU_THAP_ANH_RONG_TOI_THIEU` (400), tiêu đề ảnh phải nhắc đến tên món/quán (`ten_mon_trong_ten_quan`), bỏ URL trùng. Tối đa `THU_THAP_SO_ANH_MON` (6) / `THU_THAP_SO_ANH_QUAN` (5).
- Tiết kiệm quota: món/quán đã có ≥ 2 ảnh thì không gọi lại. Tắt hẳn bằng `THU_THAP_ANH_BAT=false`. Lỗi tìm ảnh (kể cả thiếu `SERPER_API_KEY`) chỉ ghi log, không làm hỏng việc lưu món/quán.
- Thống kê thêm `anhMon` (trong `monAn` và `diaDiem`) và `anhQuan`. API chi tiết món (`GET /mon-an/{id}`) và quán (`GET /dia-diem/{id}`) trả thêm `anh: [{url, urlThumbnail, nguon}]` (món: ảnh bìa đứng đầu); danh sách vẫn chỉ trả ảnh bìa.

### Chống trùng (4 lớp)
1. **Unique ở DB** (migration 0002): `MonAn.tenChuanHoa`, `MonAn.maWikipedia`, `DanhMucMonAn.tenDanhMuc`, `NguyenLieu.tenNguyenLieu`, `SoThich(loai, tenSoThich)`, `CheDoAn.tenCheDo`. Đã có từ trước: `DiaDiem.maGooglePlace` (id quán từ Serper) và unique cặp id ở các bảng liên kết.
2. **Upsert:** tìm theo pageid Wikipedia, rồi `tenChuanHoa` (`app/core/chuan_hoa.py`: viết thường, bỏ dấu, `đ`→`d`), rồi theo tên gọi khác. Có thì cập nhật, chưa có mới thêm. Gặp `IntegrityError` thì rollback savepoint và chuyển sang cập nhật.
3. **Đầu vào:** gửi danh sách món đã có cho LLM; loại tên trùng trong cùng một danh sách.
4. **Khoá chạy:** `khoa_thu_thap` dùng `GET_LOCK('huetaste_thu_thap', 0)` trên một connection riêng. Lần chạy thứ hai sẽ bỏ qua và ghi log. Trên SQLite (test) không dùng khoá.

Thiếu `GEMINI_API_KEY` hoặc `SERPER_API_KEY` thì pipeline dừng và trả `{"loi": ...}`. Lỗi lẻ của một món chỉ được ghi log rồi chạy tiếp.

## Gợi ý `POST /api/v1/goi-y`
`app/services/goi_y_service.py`: **content-based + luật ngữ cảnh, chấm điểm có trọng số**. Không dùng ML và không gọi LLM khi người dùng bấm gợi ý.

**Ngữ cảnh** (`ngu_canh_service.tao_ngu_canh`): lưu vào `NguCanh`, kèm `NhuCauTheoNgay` nếu app gửi bữa, ngân sách, ghi chú hoặc nguyên liệu cần tránh (chỉ ghi các trường đó, giữ nguyên `gioAn` đã đặt). `bo_sung_tu_nhu_cau` điền `nganSach`/`ghiChu`/`nguyenLieuTranh` còn thiếu từ nhu cầu đã lưu của bữa hôm nay.
- Buổi: lấy từ `buaAn`; không có thì lấy bữa có `gioAn` hôm nay gần giờ hiện tại nhất trong ±2 giờ (`xac_dinh_bua`, `CUA_SO_GIO_AN`); vẫn không có thì tính theo khung giờ Việt Nam (`buoi_theo_gio`).
- Thời tiết: Open-Meteo (`thoi_tiet_service`, cache 15 phút, lỗi thì `None`).
- Ngày rằm: `app/core/am_lich.py` (âm lịch Việt Nam, mùng 1 hoặc rằm 15).

**Lọc cứng:** món `active`, thoả mọi chế độ ăn người dùng đã chọn (thuần chay = chế độ "Ăn chay" trong hồ sơ), và không chứa nguyên liệu cần tránh (`loc_nguyen_lieu_tranh` + `mon_an_repo.mon_chua_nguyen_lieu` trên `MonAnNguyenLieu`).

**Điểm món** (mỗi thành phần 0..1):

| Thành phần | Trọng số | Cách tính |
|---|---|---|
| Ngữ cảnh | 0.30 | Khớp buổi và thời tiết. Ngày rằm: món chay +0.5, món mặn ×0.6. `an_vat` ưu tiên ăn vặt/chè/bánh. |
| Sở thích | 0.30 | Noisy-OR của `trongSo × mucDo/5` trên các tag khớp. Chưa có sở thích thì 0.5, không khớp tag nào thì 0.1. |
| Ngân sách | 0.15 | 1 nếu giá ≤ ngân sách, giảm tuyến tính về 0 tại 1.5 × ngân sách. Không rõ giá thì 0.5. |
| Đánh giá | 0.15 | TB `DanhGia.diemSo`/5; chưa có thì TB rating Google của các quán bán món. |
| Ghi chú + yêu thích | 0.10 | Từ khoá không dấu ("ít cay", "nước dùng", "chay"…), mỗi tag tính một lần; món yêu thích +0.3. |

Đa dạng hoá: mỗi danh mục tối đa 2 món trong top.

**Điểm quán** (xét các quán bán 20 món điểm cao nhất):

| Thành phần | Trọng số |
|---|---|
| Món tốt nhất của quán | 0.35 |
| Khoảng cách (0 khi ≥ 5 km) | 0.25 |
| Rating / 5 | 0.20 |
| Ngân sách (`giaBan`, nếu không có thì ước lượng từ `mucGia`) | 0.10 |
| Món đặc trưng | 0.10 |

**Lý do:** ghép 3 câu có đóng góp điểm lớn nhất, nối bằng " · ". Mỗi món/quán trả về được lưu thành một dòng `GoiY` (`diemSo` 0..1, `thuHang`). App hiển thị `diemSo × 100` thành "% hợp vị".

Muốn chỉnh trọng số thì sửa `TRONG_SO_MON` / `TRONG_SO_QUAN`. Mọi hàm `cham_*` là hàm thuần, có test trong `tests/test_goi_y.py`.

## Scan ảnh món `POST /api/v1/scan`
`app/services/scan_service.py`. Ảnh lưu qua `luu_tru_service.luu_anh(..., "scan")`, mỗi lượt ghi 1 dòng `LichSuScan` (`ketQuaTho` = JSON gốc của model).

**Model vision** (`gemini_service.nhan_dien_anh`): thử lần lượt `GEMINI_MODEL_SCAN` (mặc định `gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemma-4-26b-a4b-it`, chọn theo benchmark ảnh món Huế với key free). Người dùng đang chờ nên không sleep/thử lại: timeout (`SCAN_TIMEOUT_GIAY`), 4xx/5xx hay JSON hỏng là chuyển ngay model kế. Gemma không nhận `responseSchema` nên chỉ dựa vào prompt rồi tách JSON bằng regex.

**Prompt** gửi kèm tên mọi món chưa bị ẩn (active + unverified) và hỏi: có phải món ăn, chọn tên trong danh sách (hoặc `KHAC`), tên thật, **có phải món đặc trưng Huế**, danh mục, độ tin cậy, mô tả ngắn, tối đa 3 món gần giống. Backend so khớp thêm 1 lớp bằng `do_tuong_dong` ≥ 0.85 để không tạo trùng khi model viết lệch tên. `doTinCay` do model tự chấm (thường 0.95–1 kể cả khi sai), chỉ để tham khảo.

| Kết quả | Xử lý | `trangThai` |
|---|---|---|
| Không phải món ăn | ghi lịch sử, 422 `KHONG_NHAN_DIEN_DUOC` | – |
| Khớp món `active` | trả `mon_an_service.get_chi_tiet` | `CO_TRONG_HE_THONG` |
| Món Huế chưa có | tạo `MonAn` `unverified` (moTa = mô tả ngắn), background task `lam_giau_mon` | `DANG_CAP_NHAT` |
| Khớp món `unverified` | tìm hiểu lại tối đa 1 lần/ngày | `DANG_CAP_NHAT` / `CHUA_XAC_MINH` |
| Không đặc trưng Huế | không lưu `MonAn`, `idMonAn` NULL, trả `monTuongTu` (món active) | `KHONG_LUU` |

**Tìm hiểu nền** (`thu_thap_service.lam_giau_mon`): khoá riêng từng món (`GET_LOCK('huetaste_mon_<tenChuanHoa>')`, không dùng khoá chung vì job hằng tháng giữ lâu) → `_xu_ly_ung_vien` (Wikipedia + LLM trích tag, như thu thập định kỳ) → `_tim_quan_cho_mon` (1 lượt Serper). Vì câu "đặc trưng Huế" của model có thể sai, món chỉ thành `active` khi **Wikipedia xác minh được hoặc Serper có quán ở Huế mang tên món**; không thì giữ `unverified` (ẩn) và app chỉ hiện thông tin cơ bản.

App gọi `GET /scan/{id}` khi `DANG_CAP_NHAT`. Trạng thái "đang tìm hiểu" giữ trong bộ nhớ tiến trình (`scan_service._dang_lam_giau`), quá `SCAN_CHO_LAM_GIAU_GIAY` thì coi như xong → `CHUA_XAC_MINH`, nên background task chết giữa chừng app cũng không chờ mãi. Chạy uvicorn nhiều worker thì worker khác có thể trả `CHUA_XAC_MINH` sớm.

Chống lạm dụng quota free: `SCAN_TOI_DA_MOI_NGAY` lượt/người/ngày (429 `SCAN_QUA_GIOI_HAN`). Admin xem món hay bị scan mà không lưu ở `GET /admin/scan/mon-khong-luu`.
