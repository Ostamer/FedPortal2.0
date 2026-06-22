"""
Клиент для взаимодействия с Федеральным порталом.
"""
from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from src.config.logging import get_logger
from src.config.main import settings

logger = get_logger(__name__)


class ExternalApiClient:
    """HTTP-клиент для внешнего API федерального портала."""

    api_path = 'api/federal/v2/rest'

    def __init__(self, base_url: str, api_key: str, host: Optional[str] = None):
        self._base_url = base_url.rstrip('/')
        self._api_key = api_key
        self._host = host
        self._client = httpx.AsyncClient(
            timeout=30.0,
            verify=settings.fed_portal_verify_ssl,
        )

    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        await self._client.aclose()

    @staticmethod
    def _apply_body_error(result: Dict[str, Any], body: Any) -> None:
        """Отметить ответ как ошибочный, если тело содержит признак ошибки.

        Портал отдаёт `{err_code, errors, message, ...}`; успех — это err_code 0
        и отсутствие success=false. HTTP-статус при этом может быть 200.
        """
        if not isinstance(body, dict):
            return

        err_code = body.get('err_code')
        body_success = body.get('success')
        has_error = (body_success is False) or (err_code not in (None, 0, '0'))
        if not has_error:
            return

        result['success'] = False
        result['err_code'] = err_code if err_code is not None else 'portal_error'
        result['message'] = body.get('message') or body.get('errors')
        if body.get('errors') is not None:
            result['errors'] = body['errors']
        # Если портал прислал HTTP-подобный код ошибки в теле при статусе 200 —
        # используем его, чтобы handler корректно маршрутизировал (fatal/retry).
        if isinstance(err_code, int) and 400 <= err_code <= 599:
            result['http_status_code'] = err_code

    def _build_url(self, endpoint: str, concrete_id: Optional[int | str] = None) -> str:
        """Собрать полный URL для запроса."""
        path = endpoint.strip('/')
        if concrete_id is not None:
            path = f'{path}/{concrete_id}'
        return f'{self._base_url}/{self.api_path}/{path}'

    def _get_headers(self) -> Dict[str, str]:
        """Заголовки для каждого запроса."""
        headers = {'Authorization': f'Bearer {self._api_key}'}
        if self._host:
            headers['Host'] = self._host
        return headers

    def _get_params(self) -> Dict[str, str]:
        """Query-параметры для каждого запроса."""
        return {'key': self._api_key}

    async def send(
        self,
        endpoint: str,
        method: str,
        concrete_id: Optional[int | str] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Отправить запрос во внешнее API и привести ответ к единому формату."""
        url = self._build_url(endpoint, concrete_id)

        try:
            response = await self._client.request(
                method=method.upper(),
                url=url,
                params=self._get_params(),
                headers=self._get_headers(),
                json=json_data,
            )
        except httpx.TimeoutException as exc:
            logger.error('external_api_timeout', method=method, url=url, error=str(exc))
            return {
                'http_status_code': HTTPStatus.GATEWAY_TIMEOUT,
                'success': False,
                'err_code': 'timeout',
                'message': str(exc),
            }
        except httpx.RequestError as exc:
            logger.error('external_api_error', method=method, url=url, error=str(exc))
            return {
                'http_status_code': HTTPStatus.BAD_GATEWAY,
                'success': False,
                'err_code': 'request_error',
                'message': str(exc),
            }

        result: Dict[str, Any] = {
            'http_status_code': response.status_code,
            'success': response.is_success,
        }

        if response.status_code == HTTPStatus.NO_CONTENT or not response.content:
            result['data'] = None
        else:
            content_type = response.headers.get('content-type', '').lower()
            is_json_content = 'application/json' in content_type

            if is_json_content:
                try:
                    response_json = response.json()
                    result['data'] = response_json
                    # Федеральный портал может вернуть HTTP 200, но с ошибкой
                    # в теле ответа (err_code != 0 / success=false). Проверяем
                    # тело, а не только статус-код (как в старом client.py).
                    self._apply_body_error(result, response_json)
                except ValueError:
                    result['success'] = False
                    result['err_code'] = 'invalid_json_response'
                    result['message'] = 'Response is not valid JSON'
                    result['data'] = {'raw_response': response.text}
            else:
                # Контракт портала — JSON. Не-JSON тело (например HTML-страница
                # «Error 404» при статусе 200) считаем ошибкой независимо от кода.
                result['data'] = {'raw_response': response.text}
                result['success'] = False
                result['message'] = response.text
                result['err_code'] = 'non_json_error_response'

        logger.info(
            'external_api_request',
            method=method,
            url=url,
            status_code=response.status_code,
            success=result.get('success', False),
        )
        return result
