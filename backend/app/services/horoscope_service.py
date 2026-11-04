"""One orchestration path for JSON and progress-stream endpoints."""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from uuid import uuid4

from backend.app.schemas.horoscope import HoroscopeRequest
from backend.app.schemas.horoscope_contract import CONTRACT_VERSION
from backend.app.core.config import HOROSCOPE_TIMEOUT_SECONDS, HOROSCOPE_MODEL
from backend.app.services import horoscope_cache
from backend.app.services.cache import get_index_version
from backend.app.services.horoscope_features import generate_raw_horoscope, extract_horoscope_features
from backend.app.services.horoscope_rag_bridge import retrieve_horoscope_context, format_context_for_prompt
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.horoscope_interpreter import interpret_horoscope, HoroscopeGenerationError
from backend.app.services.pages import format_page_label
from backend.app.services.star_meanings_reference import select_meanings

logger = logging.getLogger(__name__)


def reading_events(req: HoroscopeRequest):
    started = time.perf_counter()
    timings = {}
    request_id = str(uuid4())
    def progress(stage, message):
        return {'event': 'progress', 'stage': stage, 'message': message,
                'elapsed_ms': round((time.perf_counter() - started) * 1000, 1), 'request_id': request_id}
    try:
        yield progress('chart', 'Đang lập lá số và xác định cung tiểu hạn…')
        mark = time.perf_counter()
        raw = generate_raw_horoscope(req.ngay, req.thang, req.nam, req.chi_gio, req.gioi_tinh, req.duong_lich)
        features = extract_horoscope_features(
            raw, req.target_year, req.input_confidence, req.gio_sinh_source, req.gio_sinh_error_phut,
        )
        timings['chart'] = round((time.perf_counter() - mark) * 1000, 1)
        chart_report = {
            'status': 'chart_ready',
            'ho_ten': req.ho_ten or 'Người Xem',
            'thong_tin_co_ban': features['thong_tin_co_ban'],
            'menh_cuc': features.get('menh_cuc'),
            'la_so': {'thap_ni_cung': raw['thap_ni_cung']},
            'annual': features['nam_xem'],
            'luu_nien': features.get('luu_nien'),
            'palaces': features['palaces'],
            'meta': {
                'request_id': request_id,
                'target_year': features['nam_xem']['year'],
                'reading_mode': req.reading_mode,
                'contract_version': CONTRACT_VERSION,
            },
        }
        yield {'event': 'chart_ready', 'report': chart_report}
        yield progress('retrieval', 'Đã lập lá số. Đang tìm nguồn theo tên sao và tổ hợp…')
        mark = time.perf_counter()
        context = retrieve_horoscope_context(features, req.top_k_per_topic)
        facts = build_star_facts(features, context)
        meaning_references=select_meanings(facts)
        from backend.app.services.cach_cuc_detector import detect_cach_cuc
        from backend.app.services.star_meanings_reference import select_all_references_for_chart
        detection = detect_cach_cuc(features, facts=facts, context=context)
        knowledge_references = select_all_references_for_chart(features, facts, cach_cuc=detection)
        features['_knowledge_references'] = knowledge_references
        context['knowledge_references'] = knowledge_references
        features['_star_meaning_references']=meaning_references
        context['star_meaning_references']=meaning_references
        timings['retrieval'] = round((time.perf_counter() - mark) * 1000, 1)
        citations = [{
            'ref_id': s['ref_id'], 'chunk_id': s['chunk_id'], 'book_code': s['book_code'],
            'chapter': s.get('chapter', ''), 'part_number': s.get('part_number'),
            'pdf_page_start': s.get('pdf_page_start'), 'pdf_page_end': s.get('pdf_page_end'),
            'page_label': format_page_label(s['book_code'], s.get('part_number'), s.get('pdf_page_start')),
            'trust_tier': s.get('trust_tier'), 'verification_status': 'unverified',
            'excerpt': s.get('excerpt', s['text'][:500]), 'matched_query': s.get('matched_query', ''),
        } for s in context['reference_list']]
        report = {
            'status': 'ok', 'ho_ten': req.ho_ten or 'Người Xem',
            'thong_tin_co_ban': features['thong_tin_co_ban'], 'reading': {},
            'menh_cuc': features.get('menh_cuc'),
            'la_so': {'thap_ni_cung': raw['thap_ni_cung']}, 'citations': citations,
            'star_analysis': facts, 'annual': features['nam_xem'],
            'star_meaning_references': meaning_references,
            'knowledge_references': knowledge_references,
            'luu_nien': features.get('luu_nien'), 'palaces': features['palaces'],
            'meta': {'request_id': request_id, 'provider': req.provider, 'cached': False,
                     'reading_mode': req.reading_mode, 'contract_version': CONTRACT_VERSION,
                     'target_year': features['nam_xem']['year'],
                     'total_chunks_retrieved': len(citations), 'queries_evaluated': context['query_count']},
        }
        yield {'event': 'prepared', 'report': report}

        if req.reading_mode == 'du_lieu':
            from backend.app.services.horoscope_interpreter import generate_mock_reading
            reading = generate_mock_reading(features, context)
            timings['generation'] = 0.0
            timings['total'] = round((time.perf_counter() - started) * 1000, 1)
            generation = {
                'actual_provider': 'mock', 'is_mock': True, 'reason': 'requested',
                'actual_reading_mode': 'du_lieu', 'fallback_reason': None, 'elapsed_ms': 0.0,
            }
            report = {
                **report, 'reading': reading,
                'meta': {**report['meta'], **generation, 'timings_ms': timings,
                         'reading_mode': 'du_lieu', 'actual_reading_mode': 'du_lieu', 'fallback_reason': None,
                         'star_meanings_provided_to_ai': False},
            }
            yield {'event': 'result', 'report': report}
            return

        birth = {
            'ngay': req.ngay, 'thang': req.thang, 'nam': req.nam, 'chi_gio': req.chi_gio,
            'gioi_tinh': req.gioi_tinh, 'duong_lich': req.duong_lich,
            'input_confidence': req.input_confidence, 'gio_sinh_source': req.gio_sinh_source,
            'gio_sinh_error_phut': req.gio_sinh_error_phut,
            'target_year': features['nam_xem']['year'], 'top_k_per_topic': req.top_k_per_topic,
            'tu_hoa_table': features['thong_tin_co_ban']['tu_hoa_table'],
        }
        cache_key = horoscope_cache.compute_key(
            birth, req.provider, HOROSCOPE_MODEL, horoscope_cache.context_hash(context),
            get_index_version(), req.reading_mode,
        )
        cached = horoscope_cache.lookup(cache_key) if req.provider != 'mock' else None
        if cached:
            generation = {**cached.get('generation', {}), 'cached': True, 'elapsed_ms': 0.0}
            timings['cache'] = 0.0
            timings['generation'] = 0.0
            timings['total'] = round((time.perf_counter() - started) * 1000, 1)
            logger.info('horoscope_read request_id=%s cache_hit=True timings_ms=%s', request_id, timings)
            yield {'event': 'result', 'report': {
                **report, 'reading': cached.get('reading', {}),
                'meta': {**report['meta'], **generation, 'timings_ms': timings,
                         'star_meanings_provided_to_ai':bool(meaning_references)},
            }}
            return

        yield progress('generation', f"Đã có {len(citations)} nguồn. Đang luận giải thông minh; mỗi lượt chờ tối đa {HOROSCOPE_TIMEOUT_SECONDS:g} giây, tự chuyển bộ xử lý dự phòng nếu quá tải.")
        mark = time.perf_counter()
        # Heartbeats report real elapsed time while the single bounded request runs.
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(interpret_horoscope, features, format_context_for_prompt(context), req.provider, context, req.reading_mode)
            while True:
                try:
                    reading = future.result(timeout=1)
                    break
                except FutureTimeout:
                    yield progress('generation', 'Đang luận giải thông minh; dữ kiện lá số đã sẵn sàng bên dưới.')
        timings['generation'] = round((time.perf_counter() - mark) * 1000, 1)
        timings['total'] = round((time.perf_counter() - started) * 1000, 1)
        generation = reading.pop('_generation')
        if generation.get('actual_provider') in ('gemini', 'groq', 'deepseek'):
            horoscope_cache.save(
                cache_key, horoscope_cache.hash_payload(birth), features['nam_xem']['year'],
                HOROSCOPE_MODEL, reading, generation,
            )
        actual_mode = generation.get('actual_reading_mode', req.reading_mode)
        fallback_reason = generation.get('fallback_reason')
        report = {**report, 'reading': reading,
                  'meta': {**report['meta'], **generation, 'timings_ms': timings,
                           'reading_mode': req.reading_mode,
                           'actual_reading_mode': actual_mode,
                           'fallback_reason': fallback_reason,
                           'star_meanings_provided_to_ai': generation.get('actual_provider') in ('gemini', 'groq', 'deepseek') and bool(meaning_references)}}
        logger.info('horoscope_read request_id=%s provider=%s reason=%s timings_ms=%s',
                    request_id, generation['actual_provider'], generation['reason'], timings)
        yield {'event': 'result', 'report': report}
    except HoroscopeGenerationError as exc:
        yield {'event': 'error', 'code': exc.code, 'message': str(exc), 'request_id': request_id}
    except Exception:
        logger.exception('horoscope_read failed request_id=%s', request_id)
        yield {'event': 'error', 'code': 'processing_error', 'message': 'Không xử lý được lá số hoặc nguồn sách. Xem log backend với mã yêu cầu.', 'request_id': request_id}


def read_horoscope(req: HoroscopeRequest) -> dict:
    for event in reading_events(req):
        if event['event'] == 'result':
            return event['report']
        if event['event'] == 'error':
            return {'status': 'error', 'error_code': event['code'], 'detail': event['message'],
                    'ho_ten': req.ho_ten or '', 'thong_tin_co_ban': {}, 'reading': {},
                    'meta': {'request_id': event['request_id'], 'reading_mode': req.reading_mode,
                             'actual_reading_mode': 'du_lieu', 'fallback_reason': event['code'],
                             'contract_version': CONTRACT_VERSION}}
    raise RuntimeError('Reading stream ended without a terminal event.')
