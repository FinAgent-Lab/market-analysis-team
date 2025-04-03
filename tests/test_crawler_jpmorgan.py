import pytest
from unittest.mock import patch
import requests

from src.services.crawler_jpmorgan import CrawlerJPMorgan


@pytest.fixture
def crawler():
    """CrawlerJPMorgan 인스턴스를 생성하는 fixture"""
    return CrawlerJPMorgan()


def test_weekly_recap_url_constant(crawler):
    """WEEKLY_RECAP_URL 상수가 올바른 URL을 가지고 있는지 테스트"""
    expected_url = "https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/insights/market-insights/wmr/weekly_market_recap.pdf"
    assert crawler.WEEKLY_RECAP_URL == expected_url


@patch("requests.get")
def test_get_weekly_recap_success(mock_get, crawler):
    """get_weekly_recap 메서드가 성공적으로 PDF 콘텐츠를 반환하는지 테스트"""
    # Mock 응답 설정
    mock_content = b"fake pdf content"
    mock_get.return_value.content = mock_content

    # 메서드 실행
    result = crawler.get_weekly_recap()

    # 검증
    mock_get.assert_called_once_with(crawler.WEEKLY_RECAP_URL)
    assert result == mock_content


@patch("requests.get")
def test_get_weekly_recap_response_type(mock_get, crawler):
    """반환된 콘텐츠가 bytes 타입인지 테스트"""
    # Mock 응답 설정
    mock_content = b"fake pdf content"
    mock_get.return_value.content = mock_content

    # 메서드 실행
    result = crawler.get_weekly_recap()

    # 검증
    assert isinstance(result, bytes)


@patch("requests.get")
def test_get_weekly_recap_error_handling(mock_get, crawler):
    """네트워크 오류 발생 시 적절히 처리되는지 테스트"""
    # Mock에서 예외 발생하도록 설정
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    # 예외가 발생하는지 확인
    with pytest.raises(requests.exceptions.RequestException):
        crawler.get_weekly_recap()
