import json
import uuid
import logging
import requests
from datetime import datetime, timezone
from schemas import MessageSchema, TransactionSchema, TransactionsDataSchema, SignedApiData
from utils import encode_base64, calculate_hash, emulate_signature

logger = logging.getLogger(__name__)

# Слой 4
inner_data = {"BankGuaranteeHash": "TEST-HASH-12345", "Status": "Accepted"}
inner_data_b64 = encode_base64(json.dumps(inner_data))

# Слой 3
message = MessageSchema(
    data=inner_data_b64,
    sender_branch="SYSTEM_A",
    receiver_branch="SYSTEM_B",
    info_message_type=202,
    message_time=datetime.now(timezone.utc),
    chain_guid=uuid.uuid4(),
    metadata="Тестовое входящее сообщение от Системы А"
)
message_b64 = encode_base64(message.model_dump_json(by_alias=True))

# Слой 2
transaction = TransactionSchema(
    transaction_type=1,
    data=message_b64,
    transaction_time=datetime.now(timezone.utc),
    metadata="incoming_test",
    sign="",
    signer_cert=encode_base64("SYSTEM_A"),
    hash=None
)

# вычисляем хэн и подпись
tx_dict = transaction.model_dump(by_alias=True, mode="json")
tx_hash = calculate_hash(tx_dict)

transaction.hash = tx_hash
transaction.sign = emulate_signature(tx_hash)

transactions_data = TransactionsDataSchema(
    Transactions=[transaction],
    Count=1
)
transactions_data_b64 = encode_base64(transactions_data.model_dump_json(by_alias=True))

# Слой 1
payload = SignedApiData(
    Data=transactions_data_b64,
    Sign=encode_base64("SYSTEM_A_SIGNATURE"),
    SignerCert=encode_base64("SYSTEM_A")
)

print("Отправляем входящую транзакцию в Систему Б")

payload_dict = payload.model_dump(by_alias=True, mode="json") # Превращаем схему в JSON
response = requests.post("http://localhost:8000/api/messages/incoming", json=payload_dict)

print(f"\nСтатус код: {response.status_code}")

if response.status_code == 200:
    print(f"Ответ сервера (Квиток успешно сгенерирован):")
else:
    print(f"Ошибка:")
print(json.dumps(response.json(), indent=2))