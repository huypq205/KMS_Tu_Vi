"""Consume progress records without treating a partial/disconnected report as success."""
import json
import os

import requests


def _headers() -> dict:
    """Gửi X-API-Key khi backend yêu cầu (env KMS_API_KEY); bỏ qua khi chưa bật."""
    key = os.getenv("KMS_API_KEY", "").strip()
    return {"X-API-Key": key} if key else {}


def _raise_for_status(response) -> None:
    """raise_for_status + thông điệp thân thiện cho lỗi 429 (rate limit)."""
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        if response.status_code == 429:
            raise ValueError(
                "Bạn đã gửi quá nhiều yêu cầu trong 1 phút (giới hạn của dịch vụ). "
                "Chờ ít phút rồi thử lại."
            ) from exc
        raise


def ask_horoscope(api_base: str, payload: dict):
    """Hỏi nhanh theo chủ đề (/api/v1/horoscope/ask); trả JSON hoặc raise."""
    if os.getenv("KMS_UI_FIXTURE") == "1":
        from frontend.ui_fixture import mock_ask_horoscope
        return mock_ask_horoscope(payload)
    response = requests.post(f'{api_base}/api/v1/horoscope/ask', json=payload,
                             headers=_headers(), timeout=(5, 75))
    _raise_for_status(response)
    data = response.json()
    if not isinstance(data, dict) or data.get('status') != 'ok':
        raise ValueError(data.get('detail') or data.get('message') or 'Dịch vụ chưa trả được câu trả lời.')
    return data


def reading_events(api_base: str, payload: dict):
    if os.getenv("KMS_UI_FIXTURE") == "1":
        from frontend.ui_fixture import mock_reading_events
        yield from mock_reading_events(payload)
        return
    response = requests.post(f'{api_base}/api/v1/horoscope/read-stream', json=payload,
                             headers=_headers(), stream=True, timeout=(5, 75))
    try:
        _raise_for_status(response)
        finished = False
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError('Dịch vụ trả tiến độ không hợp lệ.')
            if event.get('event') == 'error':
                raise ValueError(event.get('message', 'Dịch vụ chưa tạo được bài đọc.'))
            if event.get('event') == 'result':
                report = event.get('report')
                if not isinstance(report, dict) or report.get('status') != 'ok' or not isinstance(report.get('reading'), dict):
                    raise ValueError('Dịch vụ trả báo cáo không hợp lệ.')
                finished = True
            yield event
        if not finished:
            raise ValueError('Kết nối kết thúc trước khi hoàn tất bài đọc. Hãy thử lại; báo cáo trước vẫn được giữ.')
    finally:
        response.close()
