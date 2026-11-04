# Phân tích cách tổ chức dữ liệu của tuvisonkhiem.vn — áp dụng vào KMS

> Ngày: 2026-07-14 · Nguồn: phân tích trực tiếp (bằng chứng lưu trong thư mục này)
>
> Bằng chứng đã lưu:
> - `tvsk-laso.html` — HTML raw của trang lá số mẫu `/tu-vi-tron-doi/1/091510101990/2026/nguyenvanaa/`
> - `tvsk_get_daivan_sample.json` — payload an sao chuẩn từ `admin-ajax.php?action=tvsk_get_daivan`
> - `tvsk_get_cachcuc_sample.txt` — nội dung cách cục từ `tvsk_get_cachcuc`
>
> Quy ước: **Quan sát** = thấy trực tiếp trong bằng chứng; **Suy luận** = kết luận từ bằng chứng (ghi rõ).

---

## 1. Kiến trúc tổng thể

**Quan sát:**

| Lớp | Công nghệ | Vai trò |
|---|---|---|
| CMS | WordPress (theme riêng `tvsk-theme`, Tailwind) | Nội dung web: trang, bài viết, menu, thư viện |
| SEO | Rank Math PRO | JSON-LD (Organization/Article/Breadcrumb), OG, sitemap |
| App nghiệp vụ | PHP viết trong WP: REST namespace `tvsk/v1` (chỉ expose `/health`) + hàng loạt action `admin-ajax.php` (`tvsk_*`) | An sao, render SVG, cách cục, luận giải, lưu hồ sơ, tìm kiếm |
| Auth | `/auth/` (email OTP 6 số + Google GSI + mật khẩu) | Đăng nhập không cần mật khẩu, callback quay lại đúng trang lá số |
| Thương mại | `/orders/create`, `/orders/`, plugin `kk-star-ratings` | Đơn hàng (luận giải trả phí), đánh giá sao |
| Tracking | Script inline đầu `<head>` (trước GTM) | Attribution first/last-touch |

**Suy luận:** Họ tách "nội dung tri thức" (WordPress, quản trị qua admin) khỏi "máy an sao" (cụm PHP/AJAX), và dữ liệu tri thức được trả về dưới dạng HTML/text cho từng module luận giải — không phải 1 API JSON duy nhất.

### 1.1 Dữ liệu tri thức = Custom Post Types (quan sát được qua `wp-json/wp/v2/types`)

4 CPT đặc thù Tử Vi, mỗi CPT kèm taxonomy riêng để lọc đa chiều:

| CPT (`rest_base`) | Tên | Taxonomy (mặt cắt dữ liệu) |
|---|---|---|
| `tv_sao` | Thư viện sao | `tv_danh_muc`, `tv_nhom`, `tv_an_theo`, `tv_nhom_tinh_chat` |
| `tv_cach_cuc` | Cách cục | `tv_nhom_cach` |
| `tv_thuat_ngu` | Thuật ngữ | `tv_chu_de` |
| `tv_sach` | Thư viện sách | `tv_phai` (phái/bản) |

Mô hình dữ liệu ở đây: **1 bản ghi = 1 thực thể** (sao, cách cục, thuật ngữ, sách) + **taxonomies làm facet** (nhóm, an theo cung nào, nhóm tính chất...) phục vụ bộ lọc/tra cứu. Cùng họ với `knowledge_items.knowledge_type` + `taxonomy_code` trong KMS, nhưng KMS hiện đang là 1 bảng phẳng trong khi họ tách bảng/loại riêng cho mỗi thực thể.

---

## 2. URL scheme lá số: dữ liệu nhúng trong đường dẫn (stateless)

**Quan sát** (từ JS submit của form lập lá số trong `tvsk-laso.html`):

```
/<view_type_slug>/<g>/<HHMMDDMMYYYY>/<year_watch>[/<month_watch>]/<encoded_name>/?daivan_watch=N
```

- `view_type_slug` map do PHP tiêm: `tvskSlugConfig = {tron_doi: "tu-vi-tron-doi", dai_van: "dai-van", tieu_van: "tieu-van", nguyet_van: "nguyet-van"}`
- `g`: `1`=Nam, `0`=Nữ
- `HHMMDDMMYYYY`: packed 14 ký tự (giờ:phút + ngày + tháng + năm, pad 0)
- `year_watch` = năm xem (tiểu vận/nguyệt vận), `month_watch` = tháng âm (nguyệt vận)
- `daivan_watch` = số đại vận 1..8 (query param, kèm `itm_source=form_lls` cho attribution)
- Tên đương số = `encodeURIComponent` (khoảng trắng → `+`), nằm ở đoạn cuối URL

Ví dụ thực: `/tu-vi-tron-doi/1/091510101990/2026/nguyenvanaa/` = Nam, 09:15, 10/10/1990, xem năm 2026, tên "nguyenvanaa".

**Hệ quả thiết kế (suy luận):**
- Lá số **không cần session/DB để mở lại**: URL là trạng thái đầy đủ. Chia sẻ link = chia sẻ lá số.
- Vì an sao là hàm thuần `f(g, packed, view_year)` nên **cache được vô hạn** (họ cache phía client bằng key `g_packed_year`).
- Đánh đổi: PII (giờ sinh, tên) nằm trần trong URL → họ khắc phục ở tầng tracking (script attribution redact slug lá số và mọi tham số có số ≥8 chữ số; `cleanPath()` bỏ phần sau slug). **Với KMS: đây là điểm KHÔNG nên copy** (xem §5.3), KMS đang đúng khi `ChartSnapshot` anonymous ("No birth or identity fields are persisted").

---

## 3. Payload an sao chuẩn (hợp đồng dữ liệu trung tâm)

**Quan sát** (full payload trong `tvsk_get_daivan_sample.json`):

```jsonc
{
  "solarData":  { "name", "day","month","year","hour","minute", "gender" },
  "lunarData":  { "lunarDay","lunarMonth","lunarYear",
                  "namCanChi","thangCanChi","ngayCanChi","gioCanChi","namXemCanChi",
                  "age","amDuong" },
  "palaceData": {
    "palaces":        { "12":"Mệnh","1":"Phụ Mẫu", ... },          // index 1..12, 12=Mệnh
    "palaceCans":     { "10":"Mậu","11":"Kỷ", ... },               // can của 12 cung
    "stars":          { "1":[{name,group,state,element}, ...] },  // sao chính 14 (group: tuvi/thienphu)
    "starsLeft":      { "1":[{name,state,color,isImportant,element}, ...] }, // sao phụ trái
    "starsRight":     { "1":[{name,state,color,isImportant,element}, ...] }, // sao phụ phải
    "trangSinhStars": { "1":"Tràng Sinh", ..., "12":"Dưỡng" },     // 12 trường sinh theo cung
    "trietPosition"/"tuanPosition": { row,col,orientation,palaces[] }, // Tuần/Triệt
    "daiVan":     { "12":4, "1":14, ... "7":74 },                 // tuổi khởi theo cung
    "daiVanDetails":[ { box,palace,startAge,endAge,ageRange } ×8 ],
    "tieuVanYears": { "12":"Ngọ","1":"Mùi", ... },                 // chi năm tiểu vận theo cung
    "nguyetVanMonths":{ "10":1, ..., "9":12 },                     // tháng âm xem theo cung
    "cuc":"Kim Tú Cúc","amDuongLy":"Âm Dương thuận lý",
    "menhNguHanh":"Lộ Bàng Thổ","menhCucRelationship":"Mệnh sinh Cục",
    "thanCu":"Thân cư Tội","menhChu":"Liêm Trinh","thanChu":"Hóa Tinh"
  },
  "viewYear": 2026
}
```

Điểm đáng chú ý:
- **Sao chia 3 vế mỗi cung** (`stars`/`starsLeft`/`starsRight`) — đúng bố cục bàn tử vi cổ (chính tinh giữa, phụ tinh hai bên), nên render bảng 12×3 rất trực tiếp.
- Mỗi sao 1–3 trường: `group` (tuvi = 14 chính tinh / thienphu = phụ), `state` (M/V/H/D/B = vượng/hãm...), `element` (hành), `color` (đỏ = đánh dấu), `isImportant`.
- `daiVanDetails` + `tieuVanYears` + `nguyetVanMonths` là **bảng tra cứu tiền tính sẵn** để UI (dropdown đại vận, tiểu vận, nguyệt vận) dùng ngay — không cần client tính lại.

**Suy luận:** Đây chính là "hợp đồng dữ liệu" mà KMS cần chuẩn hoá: payload lá số là hàm thuần, đủ để bất kỳ tầng nào (UI, LLM, cache, share link) tiêu thụ cùng một JSON.

---

## 4. Flow trang lá số: progressive loading + gate miễn phí/trả phí

**Quan sát** (từ HTML lá số mẫu):

1. **SSR shell + Tổng quan**: server render khung trang + "Nhận xét tổng quan" (Mệnh thủ cung, cách cục, ngũ hành) ngay trong HTML → có nội dung cho SEO dù JS chết.
2. **SVG lá số lazy**: `<img data-real-src="...admin-ajax.php?action=tvsk_render_laso&g=1&t=091510101990&y=2026&n=...&format=svg">` — JS fetch qua proxy admin-ajax (để "mở ảnh tab mới" không lộ endpoint thật), blob URL.
3. **Cách cục lazy**: `tvsk_get_cachcuc&mode=&g&t&y&month=0&daivan=0` → trả HTML (mục "TỔNG QUÁT CÁCH CỤC" + "Phá cách"), nội dung lấy từ CPT `tv_cach_cuc`.
4. **Luận giải 2 nhánh**:
   - `tvsk_get_luan_giai_content` (bản đầy đủ, kèm `token=` — gate trả phí theo module),
   - `tvsk_get_luangiai_free&module=luan_giai` (bản miễn phí: trích dẫn từng cung, mỗi trích dẫn **gắn nguồn sách** — "(Tử Vân Tiên Sinh...)", "(Chìa khoá Tử Vi - Quản Xuân Thịnh)"...).
5. **Lưu hồ sơ**: `POST tvsk_save_laso` (JSON + header `X-WP-Nonce`) với payload:
   ```jsonc
   { "module_key":"luan_giai","gender":"1","packed":"091510101990","viewYear":"2026","name":"...","extra_param":"" }
   ```
   → ghi hồ sơ (profile) của user; chưa đăng nhập thì 401 → popup đăng nhập (OTP/Google) rồi retry. Trang hồ sơ: `/ho-so/`, đơn hàng: `/orders/`.
6. **Attribution**: cookie/localStorage first-party `tvsk_attr_v1` (first-touch không ghi đè, last non-direct, `itm_source` cho CTA nội bộ) — PHP đọc cookie và gắn vào body `/auth/register`, `/auth/google`, `/auth/otp/verify`, `/orders/create`. Không upload từ trình duyệt.

**Suy luận:** Kiến trúc "1 URL lá số → N module dữ liệu (SVG, cách cục, luận giải free, luận giải premium) load riêng, mỗi module 1 endpoint nhận cùng bộ tham số (g,t,y,n)" — module hoá rất sạch: thêm module mới = thêm 1 action + 1 nút gate, không đụng URL.

---

## 5. Áp dụng vào KMS

### 5.1 Đối chiếu nhanh (TVSK ↔ KMS hiện có)

| TVSK | KMS hiện tại | Trạng thái |
|---|---|---|
| Payload an sao chuẩn (3 khối solar/lunar/palace + viewYear) | `ValidationCase.chart_snapshot` = JSON text tự do; `ChartSnapshot` (case_validation) = 12 cung + facts + tu_hoa_table | KMS **đã có dạng snapshot 12 cung** nhưng chưa có khối can-chi/lịch/lưu năm xem; snapshot chưa versioned |
| `horoscope_cache` (cache_key, payload_hash, target_year, model_name, response_json) | **Đã có** `HoroscopeCache` | Giống họ: cache theo năm xem + payload hash. Cần chuẩn hoá input của cache_key = (g, packed, view_year, schema_version) |
| CPT + taxonomy (sao/cách cục/thuật ngữ/sách + facet) | `knowledge_items` (knowledge_type, taxonomy_code) + bảng `star_meanings_reference`, `star_dossier`, `star_classification`, `cach_cuc_catalog` | KMS có catalog riêng rồi — hướng đúng; nên làm rõ facet "sao + cung + tính chất" để query được |
| Luận giải free gắn trích dẫn nguồn sách | `search`/`chat/ask` trả `citations` (book_code, page, trust_tier, ui_badge) | KMS **đã vượt** họ về citation (có page + tier). Module luận giải nên dùng citations này thay vì text trần |
| Hồ sơ user lưu (module_key, gender, packed, viewYear, name, extra) | `ValidationCase` (anon, không PII) | KMS đúng theo triết lý riêng — giữ anon, chỉ nên đồng bộ key |

### 5.2 Đề xuất (theo thứ tự ưu tiên)

1. **Chuẩn hoá payload lá số thành contract versioned** (làm đầu, giá trị lớn nhất):
   - Mở rộng `ChartSnapshot` (hoặc tách schema mới `LasoPayload` trong `backend/app/schemas/`) theo bố cục TVSK: `solar` → `lunar` (can chi 4 trụ + tuổi + âm/dương) → `palace` (12 cung: tên, can, sao chính/phụ trái phải, 12 trường sinh, Tuần/Triệt) → `views` (daiVanDetails, tieuVanYears, nguyetVanMonths) → `view_year` + `schema_version`.
   - KMS đang có `CONTRACT_VERSION` trong `horoscope_contract.py` — dùng cùng cơ chế bump version này cho payload lá số. Mọi consumer (UI, LLM prompt, cache, ValidationCase) đọc 1 contract.
   - `ValidationCase.chart_snapshot` (hiện `model_dump_json()` tự do) nên ràng buộc bằng schema Pydantic mới + ghi `schema_version` để snapshot cũ không bị đọc nhầm.
2. **Packed key thống nhất**: định nghĩa 1 chỗ (ví dụ `HoroscopeRequest`) kiểu key `gender + HHMMDDMMYYYY + view_year`, dùng chung cho (a) cache key của `HoroscopeCache`, (b) snapshot validation case, (c) sau này nếu có share link. TVSK chứng minh: 1 key deterministic là đủ state cho toàn bộ lá số → cache & dedup cực đơn giản (`horoscope_cache.payload_hash` nên hash đúng bộ input này).
3. **Module hoá dữ liệu lá số kiểu TVSK**: mỗi module (tổng quan, cách cục, luận giải free, đại vận...) là 1 endpoint trả về nhận cùng bộ tham số (g, packed, view_year). KMS đã có hướng này với các `horoscope_*` service (annual, features, analysis, confidence...) — chỉ cần chốt lại contract response của từng module và nối citation KMS (`source_refs` trong hợp đồng 6 nhóm) vào đầu ra, thay vì để text trần như module free của TVSK.
4. **Facet thư viện sao**: bổ sung trục tra cứu "sao × cung × tính chất" (đối chiếu taxonomy `tv_nhom`/`tv_an_theo`/`tv_nhom_tinh_chat` của TVSK) vào `knowledge_items.taxonomy_code` / bảng sao của KMS để trả lời kiểu "cung Mệnh có sao X/Y" (đây là mẫu query thường gặp trong luận giải — TVSK query chính theo mẫu này).

### 5.3 Những điểm KHÔNG nên copy

- **PII trần trong URL** (giờ sinh + tên): TVSK chấp nhận trade-off này cho tính shareable và phải viết thêm logic redact ở tầng tracking. KMS đã chọn hướng an toàn hơn (snapshot anon, không lưu birth) — giữ nguyên; nếu cần share link, share **case_id + token có hạn** thay vì nhúng dữ liệu.
- **admin-ajax làm API công khai**: không version, không OpenAPI, không schema — khó bảo trì. KMS (FastAPI) nên giữ API có schema Pydantic + version `/api/v1/`.
- **Trả HTML nội dung cách cục/luận giải**: nội dung nên trả **cấu trúc** (tên cách cục + điều kiện + trích dẫn nguồn), để LLM/UI tự render — KMS đang đúng hướng này với `rule_ids` + `source_refs` trong hợp đồng.

---

*Ghi chú phương pháp: toàn bộ kết luận trên dựa trên bằng chứng HTTP trực tiếp (HTML page, response AJAX, danh sách CPT từ REST API). Hành vi bên trong server (DB schema PHP, cách cache phía server) là suy luận từ payload, chưa xác minh.*
