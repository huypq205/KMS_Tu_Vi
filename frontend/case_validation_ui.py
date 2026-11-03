"""Independent, voluntary anonymous validation journal."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

import streamlit as st
from frontend.research_ui import setup
from frontend import research_transport as api
from backend.app.schemas.case_validation import ChartSnapshot

setup('Nhật ký nghiệm lý')
st.write('Lưu nhận định trước khi đối chiếu, giữ cả lần không khớp và lịch sử sửa đổi.')
st.caption('Chỉ dùng mã ca ẩn danh. Không nhập tên, ngày sinh, địa chỉ hay thông tin nhận diện vào các ghi chú.')


def call(method,path,payload=None):
    try:
        return api.api_get(path) if method=='get' else api.api_post(path,payload or {})
    except Exception as exc:
        st.error('Không thực hiện được thao tác. '+str(exc))
        return None


def report_snapshot(report):
    """Allowlist only calculated stars, anonymous fact summaries and table id."""
    palaces=[]
    for p in report.get('palaces',[]):
        stars=[s['ten'] for k in ('chinh_tinh','sat_tinh','cat_tinh','phu_tinh_khac') for s in p.get(k,[])]
        palaces.append({'cung_so':p['cung_so'],'ten_cung':p.get('ten'),'stars':stars})
    facts=[{'fact_id':str(f['fact_id']),'text':' · '.join(str(f.get(k,'')) for k in ('sao','cung','dia_chi','trang_thai','kind'))}
           for f in report.get('star_analysis',[])]
    return ChartSnapshot.model_validate({'palaces':palaces,'facts':facts,
          'tu_hoa_table':(report.get('thong_tin_co_ban',{}).get('tu_hoa_table') or {}).get('id','lasotuvi')}).model_dump()


cid=st.text_input('Mã ca',placeholder='TV-2026-001',key='journal_case_id')
if st.button('Mở ca đã lưu',key='journal_open'):
    case=call('get','/api/v1/validation/cases/'+cid)
    if case: st.session_state['journal_case']=case

tabs=st.tabs(['Tạo ca','Dự đoán và khóa','Đối chiếu sự kiện','Thống kê'])
with tabs[0]:
    st.write('Lá số và mức tin cậy đầu vào sẽ được cố định khi tạo ca.')
    report=st.session_state.get('report')
    candidate=None
    if report:
        try: candidate=report_snapshot(report)
        except (ValueError,KeyError,TypeError): st.info('Bài đọc hiện tại chưa có snapshot hợp lệ.')
    if candidate:
        st.caption('Có thể dùng dữ kiện sao của bài đọc hiện tại; tên và ngày giờ sinh không được đưa vào nhật ký.')
        st.download_button('Xem bản chụp ẩn danh',json.dumps(candidate,ensure_ascii=False,indent=2),
                           'chart_snapshot.json','application/json')
    upload=st.file_uploader('Hoặc mở bản chụp ẩn danh đã xuất',type=['json'],key='journal_upload')
    inherited=(report or {}).get('thong_tin_co_ban',{}).get('input_confidence','A')
    confidence=st.selectbox('Độ tin cậy đầu vào',['A','B','C','D'],
        index=['A','B','C','D'].index(inherited) if inherited in ['A','B','C','D'] else 0,
        disabled=bool(candidate and not upload),key='journal_confidence')
    if st.button('Tạo ca và cố định lá số',key='journal_create',type='primary'):
        try:
            snapshot=json.loads(upload.getvalue()) if upload else candidate
            if not snapshot: raise ValueError('Cần tạo bài đọc hoặc mở bản chụp trước.')
            data=call('post','/api/v1/validation/cases',{'case_id':cid,'chart_snapshot':snapshot,'input_confidence':confidence})
            if data:
                st.session_state['journal_case']={**data,'predictions':[],'events':[]}
                st.success('Đã tạo ca. Lá số được giữ nguyên.')
        except (ValueError,TypeError) as exc: st.error(str(exc))

case=st.session_state.get('journal_case')
with tabs[1]:
    if not case: st.info('Mở hoặc tạo ca để ghi nhận định.')
    else:
        st.subheader(case['case_id']+' · Đầu vào '+case['input_confidence'])
        with st.expander('Dữ kiện được cố định'):
            st.json(case['chart_snapshot'])
        with st.form('journal_prediction'):
            content=st.text_area('Nhận định có điều kiện',max_chars=3000)
            period=st.text_input('Năm hoặc khoảng năm',placeholder='2027 hoặc 2027-2028')
            level=st.selectbox('Mức tin cậy',['yeu','trung_binh','manh','rat_manh'])
            kind=st.selectbox('Loại kết luận',['cau_truc','thoi_diem'])
            evidence=st.multiselect('Chứng cứ trong bản chụp',[f['fact_id'] for f in case['chart_snapshot']['facts']])
            counter=st.text_area('Phản chứng và điều kiện còn thiếu',max_chars=2000)
            supersedes=st.selectbox('Phiên bản thay thế (nếu có)',['']+[p['prediction_id'] for p in case['predictions'] if p['locked_at']])
            reason=st.text_input('Lý do tạo phiên bản mới',max_chars=2000)
            save=st.form_submit_button('Lưu bản nháp')
        if save:
            payload={'noi_dung':content,'khoa_thoi_gian':period,'muc_tin_cay':level,
                     'loai_ket_luan':kind,'chung_cu_ids':evidence,'phan_chung':counter}
            path='/api/v1/validation/cases/'+case['case_id']+'/predictions'
            if supersedes:
                path='/api/v1/validation/predictions/'+supersedes+'/revisions'
                payload={'prediction':payload,'reason':reason}
            if call('post',path,payload):
                st.session_state['journal_case']=call('get','/api/v1/validation/cases/'+case['case_id'])
                st.rerun()
        for p in case['predictions']:
            with st.expander(('Đã khóa' if p['locked_at'] else 'Bản nháp')+' · '+p['prediction_id'][:8],expanded=True):
                st.write(p['noi_dung'])
                st.caption(p['khoa_thoi_gian']+' · '+p['muc_tin_cay']+' · Chứng cứ '+', '.join(p['chung_cu_ids']))
                st.write('Phản chứng: '+p['phan_chung'])
                if p.get('supersedes'): st.caption('Thay '+p['supersedes']+' · '+p['revision_reason'])
                if p['locked_at']: st.caption('Khóa lúc '+p['locked_at'])
                elif st.button('Khóa nhận định này',key='lock_'+p['prediction_id']):
                    if call('post','/api/v1/validation/predictions/'+p['prediction_id']+'/lock'):
                        st.session_state['journal_case']=call('get','/api/v1/validation/cases/'+case['case_id'])
                        st.rerun()
with tabs[2]:
    if not case: st.info('Mở ca đã có nhận định được khóa để đối chiếu.')
    else:
        graded={e['prediction_id'] for e in case['events']}
        eligible=[p['prediction_id'] for p in case['predictions'] if p['locked_at'] and p['prediction_id'] not in graded]
        if eligible:
            with st.form('journal_event'):
                pid=st.selectbox('Dự đoán đã khóa',eligible)
                year=st.number_input('Năm sự kiện',1900,2100,2026)
                category=st.selectbox('Nhóm sự kiện',['career','finance','marriage','children','family','health','relocation','other'])
                desc=st.text_area('Diễn biến thực tế (ẩn danh)',max_chars=3000)
                result=st.selectbox('Kết quả đối chiếu',['clear_match','partial_match','no_match','not_verifiable'])
                reveal=st.form_submit_button('Lưu đối chiếu và giữ nguyên kết quả')
            if reveal and call('post','/api/v1/validation/cases/'+case['case_id']+'/events',{
                'prediction_id':pid,'year':year,'category':category,'mo_ta':desc,'prediction_result':result}):
                st.session_state['journal_case']=call('get','/api/v1/validation/cases/'+case['case_id']);st.rerun()
        else: st.info('Chưa có dự đoán đã khóa cần đối chiếu.')
        for e in case['events']:
            st.write(f"{e['year']} · {e['category']} · {e['prediction_result']}")
            st.write(e['mo_ta']);st.caption('Ghi nhận lúc '+e['revealed_at'])
with tabs[3]:
    st.write('Chỉ hiển thị tổng hợp khi đủ 30 ca khác nhau đã có đối chiếu. Nhiều nhận định của một ca vẫn chỉ tính một ca.')
    if st.button('Xem tình trạng mẫu',key='journal_stats'):
        stats=call('get','/api/v1/validation/statistics')
        if stats:
            st.write(stats['message']);st.caption(str(stats['eligible_cases'])+' ca đã đối chiếu')
            if stats['counts'] is not None:
                st.table([{'Kết quả':k,'Số lượt':v} for k,v in stats['counts'].items()])
