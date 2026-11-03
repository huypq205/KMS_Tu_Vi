"""T9: four explicit layers and bounded adjacent-year comparison."""
import copy
import json
import pytest
from fastapi.testclient import TestClient
from backend.app.services.horoscope_annual import build_annual_report, validate_annual_report
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.horoscope_interpreter import generate_mock_reading, response_schema
from frontend.horoscope_view import annual_activation_panel
from tests.horoscope_support import make_features, BIRTH


@pytest.mark.parametrize('year',[1900,2026,2100])
def test_four_layers_and_adjacent_year_boundaries(year):
    features=make_features(year);facts=build_star_facts(features)
    report=build_annual_report(features,facts)
    assert len(report['bang_kich_hoat'])==3
    for row in report['bang_kich_hoat']:
        assert all(key in row for key in ('la_so_goc','dai_han','luu_nien','luu_nguyet','phan_chung','muc_tin_cay'))
        assert row['luu_nguyet']['status']=='missing' and row['luu_nguyet']['fact_ids']==[]
    compared=report['so_sanh_nam']
    assert [x['year'] for x in compared]==[year-1,year,year+1]
    assert all(x['status']=='out_of_range' for x in compared if not 1900<=x['year']<=2100)
    assert all(x['can_chi'] is None for x in compared if x['status']=='out_of_range')
    validate_annual_report(report,facts)
    assert '%' not in json.dumps(report,ensure_ascii=False)


def test_lunar_month_claim_and_invented_or_wrong_layer_facts_rejected():
    f=make_features(2026);facts=build_star_facts(f);report=build_annual_report(f,facts)
    for path,value in [('month',{'status':'available','noi_dung':'Tháng 5 có sự kiện','fact_ids':['1']}),
                       ('unknown',{'status':'available','noi_dung':'Dữ kiện','fact_ids':['invented']})]:
        bad=copy.deepcopy(report)
        bad['bang_kich_hoat'][0]['luu_nguyet' if path=='month' else 'la_so_goc']=value
        with pytest.raises(ValueError): validate_annual_report(bad,facts)


def test_cd_only_structure_and_missing_basis_are_explicit():
    f=make_features(2026,input_confidence='D');facts=build_star_facts(f)
    report=build_annual_report(f,facts)
    assert all(r['loai_ket_luan']=='cau_truc' and r['muc_tin_cay']=='yeu' for r in report['bang_kich_hoat'])
    assert any('C/D' in line for line in report['viec_chua_du_can_cu'])
    reading=generate_mock_reading(f)
    assert reading['van_han_hien_tai']['bang_kich_hoat']==report['bang_kich_hoat']
    assert 'bang_kich_hoat' in response_schema()['properties']['van_han_hien_tai']['properties']


def test_selected_tu_hoa_table_and_real_year_differences_preserved(monkeypatch):
    monkeypatch.setenv('KMS_TU_HOA_TABLE','hung_ngm_reference')
    f=make_features(2029);report=build_annual_report(f,build_star_facts(f))
    compared=report['so_sanh_nam']
    assert [x['can_chi'] for x in compared]==['Mậu Thân','Kỷ Dậu','Canh Tuất']
    assert all(x['tu_hoa_table']=='hung_ngm_reference' for x in compared)
    assert compared[0]['luu_tu_hoa']!=compared[1]['luu_tu_hoa']


def test_annual_api_is_deterministic_and_rejects_invalid_year():
    from backend.app.main import app
    client=TestClient(app)
    response=client.post('/api/v1/horoscope/annual',json={**BIRTH,'target_year':2100})
    assert response.status_code==200,response.text
    assert response.json()['annual_report']['so_sanh_nam'][-1]['status']=='out_of_range'
    assert client.post('/api/v1/horoscope/annual',json={**BIRTH,'target_year':2101}).status_code==422


def test_annual_ui_escapes_data_and_shows_four_layers():
    f=make_features(2026);report=build_annual_report(f,build_star_facts(f))
    report['bang_kich_hoat'][0]['phan_chung']='<script>unsafe()</script>'
    html=annual_activation_panel(report)
    assert '<script>' not in html
    assert all(label in html for label in ['Lá số gốc','Đại hạn','Lưu niên','Lưu nguyệt','So sánh năm','Chưa đủ căn cứ'])


def test_no_year_fallback_keeps_missing_instead_of_inventing_year():
    reading=generate_mock_reading({})
    assert all(y['year'] is None and y['status']=='missing' for y in reading['van_han_hien_tai']['so_sanh_nam'])


def test_decade_joins_by_branch_instead_of_mixing_branch_and_domain():
    f=make_features(2026);facts=build_star_facts(f);fact_map={x['fact_id']:x for x in facts}
    report=build_annual_report(f,facts)
    for row in report['bang_kich_hoat']:
        assert row['dai_han']['status']=='available'
        assert all(fact_map[i]['dia_chi']==f['dai_han_hien_tai']['cung_ten'] for i in row['dai_han']['fact_ids'])
