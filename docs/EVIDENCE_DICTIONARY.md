# Từ điển chứng cứ KMS (T3)

Nguồn enum chuẩn: [evidence_types.py](../backend/app/core/evidence_types.py).

| Giá trị | Nhãn | Nghĩa |
|---|---|---|
| toa_thu | Tọa thủ | Sao ở cung được xét |
| tam_hop | Tam hợp | Sao trong cung tam hợp với Mệnh |
| xung_chieu | Xung chiếu | Sao ở đối cung Mệnh |
| giap_cung | Giáp cung | Sao tại cung kề Mệnh |
| tu_hoa | Tứ hóa | Hóa tinh/sao nhận hóa gốc hoặc lưu niên |
| menh_cuc | Mệnh – Cục | Quan hệ Mệnh/Cục được cấp |
| van_han | Vận hạn | Dữ kiện vận hạn theo lớp đã tính |
| nghiem_ly | Nghiệm lý | Ca kiểm chứng thật được cung cấp |
| truong_phai | Trường phái | Quan điểm nguồn/trường phái có ghi nhãn |
| suy_luan | Suy luận | Nối mạch của người viết, không thay fact_id |

Các nhãn quan hệ hiện được phân loại tương đối với Mệnh trong fact sao/cung;
không được tự hiểu mọi nhãn là quan hệ tương đối với một cung chủ đề khác.
`loi_chung_cu` phải khớp `kind` của fact dẫn. Có thể thêm `suy_luan` bên cạnh
loại được dẫn, không thêm nhãn nghiệm lý/trường phái không có dữ kiện thật.
`phan_chung` bắt buộc: nếu nguồn lấy không có, ghi “Không ghi nhận phản chứng
trong nguồn đã lấy.” Câu này không có nghĩa là không tồn tại phản chứng.

Mức tin cậy: rất mạnh/mạnh cần ít nhất ba fact_id khác nhau, trung bình ít nhất
một; yếu không bảo đảm đủ chứng cứ. Số fact là ngưỡng tối thiểu, không phải
xác suất hay bằng chứng các tầng độc lập. C/D chỉ kết luận cấu trúc.
