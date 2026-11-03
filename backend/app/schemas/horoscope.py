"""Schema Pydantic cho API Horoscope."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

InputConfidence = Literal["A", "B", "C", "D"]
GioSinhSource = Literal["document", "memory", "estimate", "unknown"]


class HoroscopeRequest(BaseModel):
    ho_ten: str = Field("", description="Họ và tên người xem")
    ngay: int = Field(..., ge=1, le=31, description="Ngày sinh (dương hoặc âm)")
    thang: int = Field(..., ge=1, le=12, description="Tháng sinh (dương hoặc âm)")
    nam: int = Field(..., ge=1900, le=2100, description="Năm sinh")
    chi_gio: int = Field(..., ge=1, le=12, description="Chi giờ (1: Tý, 2: Sửu, ..., 12: Hợi)")
    gioi_tinh: int = Field(1, description="Giới tính: 1 cho Nam, 2 hoặc -1 cho Nữ")
    duong_lich: bool = Field(True, description="True nếu ngày sinh là Dương lịch, False nếu Âm lịch")
    input_confidence: InputConfidence = Field(
        "A", description="Độ tin cậy giờ sinh: A rõ; B sai số nhỏ; C sát ranh giới/nhớ gần đúng; D thiếu dữ liệu"
    )
    gio_sinh_source: GioSinhSource = Field("memory", description="Nguồn giờ sinh: document, memory, estimate, unknown")
    gio_sinh_error_phut: int | None = Field(None, ge=0, description="Sai số ước tính của giờ sinh (phút)")
    target_year: int | None = Field(None, ge=1900, le=2100, description="Năm xem chiêm nghiệm")
    provider: str = Field("auto", description="Chế độ luận giải: 'auto' (luận giải thông minh) hoặc 'mock' (Dữ kiện thuần)")
    top_k_per_topic: int = Field(2, ge=1, le=10, description="Số đoạn trích dẫn mỗi chủ đề")


ASK_TOPICS = ("tong_quan", "su_nghiep", "tai_chinh", "tinh_cam", "van_han")


class HoroscopeAskRequest(BaseModel):
    """Hỏi nhanh theo chủ đề trên lá số, kèm nguồn sách."""
    ho_ten: str = Field("", description="Họ và tên người xem (tuỳ chọn)")
    ngay: int = Field(..., ge=1, le=31, description="Ngày sinh (dương hoặc âm)")
    thang: int = Field(..., ge=1, le=12, description="Tháng sinh (dương hoặc âm)")
    nam: int = Field(..., ge=1900, le=2100, description="Năm sinh")
    chi_gio: int = Field(..., ge=1, le=12, description="Chi giờ (1: Tý, 2: Sửu, ..., 12: Hợi)")
    gioi_tinh: int = Field(1, description="Giới tính: 1 cho Nam, 2 hoặc -1 cho Nữ")
    duong_lich: bool = Field(True, description="True nếu ngày sinh là Dương lịch, False nếu Âm lịch")
    input_confidence: InputConfidence = Field(
        "A", description="Độ tin cậy giờ sinh: A rõ; B sai số nhỏ; C sát ranh giới/nhớ gần đúng; D thiếu dữ liệu"
    )
    gio_sinh_source: GioSinhSource = Field("memory", description="Nguồn giờ sinh: document, memory, estimate, unknown")
    gio_sinh_error_phut: int | None = Field(None, ge=0, description="Sai số ước tính của giờ sinh (phút)")
    target_year: int | None = Field(None, ge=1900, le=2100, description="Năm xem chiêm nghiệm")
    topic: str = Field("tong_quan", description=f"Chủ đề hỏi: một trong {ASK_TOPICS} (hoặc 'van_han_hien_tai')")
    question: str = Field(..., min_length=1, max_length=300, description="Câu hỏi ngắn theo chủ đề")
    provider: str = Field("auto", description="'auto' (luận giải thông minh) hoặc 'mock' (chỉ dữ kiện lá số)")

