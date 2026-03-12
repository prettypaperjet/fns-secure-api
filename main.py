import uuid
import json
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker
from models import TransactionModel
from routers.messages import router as messages_router

from schemas import GuaranteeMessageSchema, MessageSchema, TransactionSchema
from utils import encode_base64, calculate_hash, emulate_signature

logger = logging.getLogger(__name__)


async def create_test_transaction(session: AsyncSession):
    """
    Создаем тестовую транзакцию с сообщением о выдаче гарантии (201)
    """

    example_1_dict = {
        "Information Type": 201,
        "Information TypeString": "Выдача гарантии",
        "Number": "BG-2024-001",
        "IssuedDate": "2024-05-20T10:00:00Z",
        "Guarantor": "ООО 'Финансовая гарантия'",
        "Beneficiary": "Государственное учреждение 'Получатель'",
        "Principal": "ООО 'Должник'",
        "Obligations": [
            {
                "Type": 1,
                "StartDate": "2024-06-01T00:00:00Z",
                "EndDate": "2024-12-01T00:00:00Z",
                "ActDate": "2024-05-15T00:00:00Z",
                "ActNumber": "ПР-2024/05/15-001",
                "Taxs": [
                    {
                        "Number": "1",
                        "NameTax": "Обязательство по контракту №K-2024-01",
                        "Amount": 50000.00,
                        "PennyAmount": 0.00
                    },
                    {
                        "Number": "2",
                        "NameTax": "Гарантийное обеспечение",
                        "Amount": 15000.00,
                        "PennyAmount": 500.00
                    }
                ]
            }
        ],
        "StartDate": "2024-06-01T00:00:00Z",
        "EndDate": "2024-12-15T00:00:00Z",
        "CurrencyCode": "USD",
        "CurrencyName": "Доллар США",
        "Amount": 65000.00,
        "RevokationInfo": "Безотзывная",
        "ClaimRight Transfer": "Не допускается",
        "PaymentPeriod": "5 рабочих дней с момента получения требования",
        "SignerName": "Иванов Иван Иванович",
        "Authorized Position": "Генеральный директор",
        "BankGuaranteeHash": "5D6F8E2A1C3B9F4D7E8A2C5B1D3F6E8A9C2D4F6A8B1C3E5F7A9D2B4C6E8F0A1"
    }

    guarantee_schema = GuaranteeMessageSchema.model_validate(example_1_dict)
    guarantee_json = guarantee_schema.model_dump_json(by_alias=True)
    guarantee_b64 = encode_base64(guarantee_json)

    message_schema = MessageSchema(
        data=guarantee_b64,
        sender_branch="SYSTEM_B",
        receiver_branch="SYSTEM_A",
        info_message_type=201,
        message_time=datetime.now(timezone.utc),
        chain_guid=uuid.uuid4(),
        metadata="Тестовая гарантия при запуске"
    )
    message_json = message_schema.model_dump_json(by_alias=True)
    message_b64 = encode_base64(message_json)

    transaction_schema = TransactionSchema(
        transaction_type=9,
        data=message_b64,
        transaction_time=datetime.now(timezone.utc),
        metadata="init_transaction",
        sign="",
        signer_cert=encode_base64("SYSTEM_B")
    )

    tx_dict = transaction_schema.model_dump(by_alias=True, mode="json")
    calculated_hash = calculate_hash(tx_dict)

    transaction_schema.hash = calculated_hash
    transaction_schema.sign = emulate_signature(calculated_hash)

    new_tx_model = TransactionModel(
        hash=transaction_schema.hash,
        transaction_type=transaction_schema.transaction_type,
        data=transaction_schema.data,
        sign=transaction_schema.sign,
        signer_cert=transaction_schema.signer_cert,
        transaction_time=transaction_schema.transaction_time,
        meta_data=transaction_schema.metadata
    )

    session.add(new_tx_model)
    await session.commit()
    logger.info("Тестовая транзакция успешно создана в БД")


app = FastAPI(
    title="API Центрального реестра (Система Б)",
    description="Эмуляция системы обмена юридически значимыми документами",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    async with async_session_maker() as session:
        # Проверяем есть ли уже транзакции в базе
        result = await session.execute(select(TransactionModel).limit(1))
        first_tx = result.scalars().first()

        if not first_tx:
            logger.info("База данных пуста. Создаем тестовую транзакцию")
            await create_test_transaction(session)


@app.get("/api/health", status_code=200, response_class=Response)
async def health_check():
    return Response(content="OK", media_type="text/plain")


app.include_router(messages_router)