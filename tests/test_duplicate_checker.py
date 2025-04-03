import pytest
import hashlib

from src.services.duplicate_checker import DuplicateChecker


@pytest.fixture
def checker():
    """DuplicateChecker 인스턴스를 생성하는 fixture"""
    return DuplicateChecker()


def test_check_with_hash(checker):
    """check_with_hash 메서드가 올바르게 동작하는지 테스트"""
    hash_value = hashlib.sha256(b"test_hash").hexdigest()
    value = b"test_hash"
    assert checker.check_with_hash(hash_value, value) is True


def test_check_with_text(checker):
    """check_with_text 메서드가 올바르게 동작하는지 테스트"""
    text = "test_text"
    value = b"test_text"
    assert checker.check_with_text(text, value) is True
