import hashlib


class DuplicateChecker:
    def __init__(self):
        pass

    def check_with_hash(self, hash: str, value: bytes) -> bool:
        """hash 값과 같은지 확인

        Args:
            hash (str): 해시 값
            value (bytes): 비교할 값

        Returns:
            bool: 같으면 True, 다르면 False
        """
        return hashlib.sha256(value).hexdigest() == hash

    def check_with_text(self, text: str, value: bytes) -> bool:
        """text 값이 value 값에 포함되는지 확인

        Args:
            text (str): 확인할 텍스트
            value (bytes): 비교할 값

        Returns:
            bool: 포함되면 True, 포함되지 않으면 False
        """
        return text == value.decode("utf-8")
