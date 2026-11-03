"""Anonymous, bounded journal input. No birth or identity fields are persisted."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class PalaceSnapshot(StrictModel):
    cung_so: int = Field(ge=1, le=12)
    stars: list[str] = Field(max_length=150)
    ten_cung: str | None = Field(default=None, max_length=40)


class FactSnapshot(StrictModel):
    fact_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=2000)


class ChartSnapshot(StrictModel):
    palaces: list[PalaceSnapshot] = Field(min_length=12, max_length=12)
    facts: list[FactSnapshot] = Field(min_length=1, max_length=1000)
    tu_hoa_table: str = Field(min_length=1, max_length=80)

    @field_validator('palaces')
    @classmethod
    def unique_palaces(cls, value):
        if {p.cung_so for p in value} != set(range(1,13)):
            raise ValueError('Cần đủ 12 cung khác nhau.')
        return value

    @field_validator('facts')
    @classmethod
    def unique_facts(cls, value):
        if len({f.fact_id for f in value})!=len(value):
            raise ValueError('fact_id không được trùng.')
        return value


class CaseInput(StrictModel):
    case_id: str = Field(pattern=r'^TV-\d{4}-\d{3}$')
    chart_snapshot: ChartSnapshot
    input_confidence: Literal['A','B','C','D']


class PredictionInput(StrictModel):
    noi_dung: str = Field(min_length=5, max_length=3000)
    khoa_thoi_gian: str = Field(pattern=r'^(?:19|20|21)\d{2}(?:-(?:19|20|21)\d{2})?$')
    muc_tin_cay: Literal['rat_manh','manh','trung_binh','yeu']
    loai_ket_luan: Literal['cau_truc','thoi_diem'] = 'thoi_diem'
    chung_cu_ids: list[str] = Field(min_length=1, max_length=100)
    phan_chung: str = Field(min_length=3, max_length=2000)

    @field_validator('noi_dung','phan_chung')
    @classmethod
    def no_percentage(cls, value):
        if '%' in value:
            raise ValueError('Không dùng phần trăm trong kết luận.')
        return value


class RevisionInput(StrictModel):
    prediction: PredictionInput
    reason: str = Field(min_length=3, max_length=2000)


class EventInput(StrictModel):
    prediction_id: str = Field(min_length=1, max_length=32)
    year: int = Field(ge=1900, le=2100)
    category: Literal['career','finance','marriage','children','family','health','relocation','other']
    mo_ta: str = Field(min_length=3, max_length=3000)
    prediction_result: Literal['clear_match','partial_match','no_match','not_verifiable']
