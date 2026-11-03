"""Data-only annual report contract; no invented monthly calculation."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')


class AnnualLayer(Strict):
    status: Literal['available','missing']
    noi_dung: str = Field(min_length=1)
    fact_ids: list[str]


class ActivationRow(Strict):
    chu_de: str
    la_so_goc: AnnualLayer
    dai_han: AnnualLayer
    luu_nien: AnnualLayer
    luu_nguyet: AnnualLayer
    phan_chung: str = Field(min_length=1)
    muc_tin_cay: Literal['rat_manh','manh','trung_binh','yeu']
    loai_ket_luan: Literal['cau_truc']


class YearComparison(Strict):
    year: int | None
    status: Literal['available','out_of_range','missing']
    can_chi: str | None
    dai_han: str
    tieu_han: str
    luu_tu_hoa: list[str]
    tu_hoa_table: str | None
    gioi_han: str


class AnnualReport(Strict):
    bang_kich_hoat: list[ActivationRow] = Field(min_length=3,max_length=3)
    so_sanh_nam: list[YearComparison] = Field(min_length=3,max_length=3)
    viec_chua_du_can_cu: list[str] = Field(min_length=1)
