"""T6: source-separated star dossier, explicit unknown and unverified states."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

import streamlit as st
from urllib.parse import quote
from backend.app.services.star_dossier import SEED_STARS
from frontend.research_ui import setup
from frontend import research_transport

setup('Hồ sơ sao')
st.write('Đối chiếu ý nghĩa và điều kiện của một sao, giữ riêng tiếng nói từng sách.')
requested = st.query_params.get('star')
star = st.selectbox('Sao cần tra cứu', SEED_STARS,
                    index=SEED_STARS.index(requested) if requested in SEED_STARS else 0, key='dossier_star')
seeds = st.checkbox('Bổ sung tham khảo chưa đối chiếu sách KMS', value=False, key='dossier_seeds')
load = st.button('Tra cứu hồ sơ', type='primary', key='load_dossier')
if load or (requested in SEED_STARS and st.session_state.get('dossier_result',{}).get('name') != requested):
    try:
        with st.spinner('Đang tìm bản ghi và trang dẫn…'):
            payload = research_transport.api_get(
                '/api/v1/stars/'+quote(star,safe='')+'/dossier', include_seeds=seeds)
            if not isinstance(payload,dict) or not isinstance(payload.get('slots'),dict) or len(payload['slots']) != 14:
                raise ValueError('Invalid dossier response')
            st.session_state['dossier_result'] = payload
    except Exception:
        st.error('Chưa tải được hồ sơ sao. Kiểm tra kết nối dịch vụ và thử tra cứu lại.')

result = st.session_state.get('dossier_result')
if result:
    st.subheader(result['name'])
    st.caption(f"Nguồn KMS: {result['canonical_records']} bản ghi trong kết quả · "
               + (', '.join(result['books']) or 'Chưa có bản ghi có trang dẫn'))
    st.caption('Các đoạn dưới là lời ghi của từng nguồn truyền thống, chưa phải kết luận cho cá nhân.')
    tabs = st.tabs(['Từng sách và trang dẫn','Ý nghĩa và điều kiện','Tổ hợp và Tứ Hóa','Nghiệm lý'])
    reference=result.get('reference_meaning')
    if reference:
        with tabs[1]:
            with st.expander('Ý nghĩa sao từ skill tham khảo',expanded=True):
                st.caption(reference['source'])
                st.caption('Mục trong tài liệu: '+reference['group_heading'])
                st.text(reference['text'])
                if reference.get('omitted_lines'):
                    st.caption('Đã lược các dòng định mệnh, nhạy cảm hoặc không phù hợp.')
    groups = [['school_differences','source_citations'],list(result['slots'])[:6],
              list(result['slots'])[6:11],['case_notes']]
    for tab, keys in zip(tabs,groups):
        with tab:
            for key in keys:
                slot = result['slots'][key]
                if key == 'school_differences' and slot['entries']:
                    columns = st.columns(len(result['books']))
                    for col, book in zip(columns,result['books']):
                        with col:
                            entries = [e for e in slot['entries'] if e['book_code']==book]
                            st.subheader(book)
                            st.caption(f'{len(entries)} bản ghi trong kết quả')
                            for entry in entries[:3]:
                                st.write('Nguồn '+book+' ghi:')
                                st.markdown('> '+entry['text'].replace('\n','\n> '))
                                st.caption(entry['knowledge_id']+' · '+'; '.join(
                                    (f"Phần {c['part_number']}, " if c.get('part_number') else '')+f"PDF tr. {c['pdf_page']}"
                                    for c in entry['citations']))
                            if len(entries)>3:
                                with st.expander('Xem các bản ghi còn lại của '+book):
                                    for entry in entries[3:]:
                                        st.write(entry['text'])
                                        st.caption(entry['knowledge_id']+' · '+str(entry['citations']))
                    continue
                with st.expander(slot['label'], expanded=key in {'core_function','school_differences','case_notes'}):
                    st.caption(slot['message'])
                    for entry in slot['entries']:
                        if slot['status'] == 'seed_unverified':
                            st.write(entry['text'])
                            st.caption('Tham khảo, chưa đối chiếu sách KMS · '+entry['source'])
                            st.link_button('Xem tài liệu tham khảo gián tiếp', entry['reference'])
                        else:
                            st.write(('Nguồn '+entry['book_code']+' ghi: '+entry['text']) if entry.get('text') else entry.get('knowledge_id'))
                            citations = entry.get('citations',[])
                            st.caption('Nguồn '+entry['book_code']+' · '+entry['knowledge_id']+' · '
                                + '; '.join((f"Phần {c['part_number']}, " if c.get('part_number') else '')
                                            + f"PDF tr. {c['pdf_page']}" for c in citations))
                            if key == 'school_differences':
                                st.caption('Lập trường tác giả: '+str(entry.get('author_stance') or 'Chưa có metadata')
                                           +' · Xung đột: '+str(entry.get('conflict_status') or 'Chưa đánh giá'))
else:
    st.info('Chọn một sao để xem bản ghi, điều kiện và trang nguồn. Mục chưa có dữ liệu sẽ được để rõ.')
