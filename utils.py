import base64
import hashlib
import json
from typing import Any, Dict


def encode_base64(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')


def decode_base64(data: str) -> str:
    return base64.b64decode(data).decode('utf-8')


def calculate_hash(data_dict: Dict[str, Any]) -> str:
    """
    Вычисляет SHA-256 хэш объекта по правилам
    """

    obj = data_dict.copy()

    if "Hash" in obj:
        obj["Hash"] = None
    if "Sign" in obj:
        obj["Sign"] = ""

    if "SignerCert" in obj:
        obj["SignerCert"] = ""

    json_str = json.dumps(obj, ensure_ascii=False)
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))

    # результат в виде HEX строки
    return hash_obj.hexdigest().upper()


# Эмулирует создание ЭЦП на основе хэша
def emulate_signature(hash_hex: str) -> str:
    return encode_base64(hash_hex)


def verify_signature(hash_hex: str, sign_base64: str) -> bool:
    expected_sign = emulate_signature(hash_hex)
    return expected_sign == sign_base64