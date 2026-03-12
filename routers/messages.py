import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import TransactionModel
from schemas import SignedApiData, SearchRequest, TransactionsDataSchema, TransactionSchema
from utils import decode_base64, encode_base64

from datetime import datetime, timezone
from schemas import MessageSchema, ReceiptMessageSchema
from utils import calculate_hash, emulate_signature

router = APIRouter(prefix="/api/messages", tags=["Messages"])


@router.post("/outgoing", response_model=SignedApiData, status_code=200)
async def get_outgoing_messages(payload: SignedApiData, db: AsyncSession = Depends(get_db)):
    try:
        decoded_data_str = decode_base64(payload.Data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 in Data")

    try:
        search_req = SearchRequest.model_validate_json(decoded_data_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid SearchRequest JSON")

    # Находим в хранилище все транзакции и фильтруем по дате
    query = select(TransactionModel).where(
        TransactionModel.transaction_time >= search_req.StartDate,
        TransactionModel.transaction_time <= search_req.EndDate
    ).order_by(TransactionModel.transaction_time)

    result = await db.execute(query)
    transactions = result.scalars().all()

    filtered_transactions = []

    # Перебираем транзакции и проверяем получателя внутри Message
    for tx in transactions:
        try:
            msg_json_str = decode_base64(tx.data)
            msg_dict = json.loads(msg_json_str)

            if msg_dict.get("ReceiverBranch") == "SYSTEM_A":
                tx_schema = TransactionSchema(
                    transaction_type=tx.transaction_type,
                    data=tx.data,
                    hash=tx.hash,
                    sign=tx.sign,
                    signer_cert=tx.signer_cert,
                    transaction_time=tx.transaction_time,
                    metadata=tx.meta_data,
                    transaction_in=tx.transaction_in,
                    transaction_out=tx.transaction_out
                )
                filtered_transactions.append(tx_schema)
        except Exception:
            continue

    # пагинация
    total_count = len(filtered_transactions)
    paginated_txs = filtered_transactions[search_req.Offset: search_req.Offset + search_req.Limit]

    transactions_data = TransactionsDataSchema(
        Transactions=paginated_txs,
        Count=total_count
    )

    response_json = transactions_data.model_dump_json(by_alias=True)
    encoded_response_data = encode_base64(response_json)

    final_response = SignedApiData(
        Data=encoded_response_data,
        Sign=encode_base64("SYSTEM_B_RESPONSE_SIGN"),
        SignerCert=encode_base64("SYSTEM_B")
    )

    return final_response


@router.post("/incoming", response_model=SignedApiData, status_code=200)
async def receive_incoming_messages(payload: SignedApiData, db: AsyncSession = Depends(get_db)):
    try:
        decoded_data_str = decode_base64(payload.Data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 in envelope Data")

    try:
        transactions_data = TransactionsDataSchema.model_validate_json(decoded_data_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid TransactionsData JSON: {e}")

    receipt_transactions = []

    # Обработка каждой транзакции
    for tx_schema in transactions_data.Transactions:
        if not tx_schema.sign:
            raise HTTPException(status_code=400, detail="Transaction signature is missing")

        tx_dict = tx_schema.model_dump(by_alias=True, mode="json")
        calculated_hash = calculate_hash(tx_dict)

        if calculated_hash != tx_schema.hash:
            raise HTTPException(
                status_code=400,
                detail=f"Hash mismatch. Expected: {calculated_hash}, Got: {tx_schema.hash}"
            )

        new_tx_model = TransactionModel(
            hash=tx_schema.hash,
            transaction_type=tx_schema.transaction_type,
            data=tx_schema.data,
            sign=tx_schema.sign,
            signer_cert=tx_schema.signer_cert,
            transaction_time=tx_schema.transaction_time,
            meta_data=tx_schema.metadata,
            transaction_in=tx_schema.transaction_in,
            transaction_out=tx_schema.transaction_out
        )
        db.add(new_tx_model)

        try:
            msg_json_str = decode_base64(tx_schema.data)
            msg_schema = MessageSchema.model_validate_json(msg_json_str)
        except Exception:
            # Если не удалось прочитать сообщение сохраняем транзакцию но квиток не генерим
            continue

        if msg_schema.info_message_type != 215:
            try:
                inner_data_json = decode_base64(msg_schema.data)
                inner_data_dict = json.loads(inner_data_json)
                bg_hash = inner_data_dict.get("BankGuaranteeHash", "UNKNOWN_HASH")
            except Exception:
                bg_hash = "ERROR_PARSING_HASH"

            receipt_payload = ReceiptMessageSchema(bank_guarantee_hash=bg_hash)
            receipt_data_b64 = encode_base64(receipt_payload.model_dump_json(by_alias=True))

            receipt_msg = MessageSchema(
                data=receipt_data_b64,
                sender_branch="SYSTEM_B",
                receiver_branch="SYSTEM_A",
                info_message_type=215,
                message_time=datetime.now(timezone.utc),
                chain_guid=msg_schema.chain_guid,
                metadata=f"Receipt for {bg_hash}"
            )
            receipt_msg_b64 = encode_base64(receipt_msg.model_dump_json(by_alias=True))

            receipt_tx = TransactionSchema(
                transaction_type=9,
                data=receipt_msg_b64,
                transaction_time=datetime.now(timezone.utc),
                sign="",
                signer_cert=encode_base64("SYSTEM_B"),
                hash=None
            )

            # хэш и подпись для транзакции квитка
            receipt_tx_dict = receipt_tx.model_dump(by_alias=True, mode="json")
            receipt_tx.hash = calculate_hash(receipt_tx_dict)
            receipt_tx.sign = emulate_signature(receipt_tx.hash)

            receipt_transactions.append(receipt_tx)

            # Сохраняем квиток
            receipt_tx_model = TransactionModel(
                hash=receipt_tx.hash,
                transaction_type=receipt_tx.transaction_type,
                data=receipt_tx.data,
                sign=receipt_tx.sign,
                signer_cert=receipt_tx.signer_cert,
                transaction_time=receipt_tx.transaction_time,
                meta_data=receipt_tx.metadata
            )
            db.add(receipt_tx_model)

    await db.commit()

    response_data = TransactionsDataSchema(
        Transactions=receipt_transactions,
        Count=len(receipt_transactions)
    )

    encoded_response_data = encode_base64(response_data.model_dump_json(by_alias=True))

    final_response = SignedApiData(
        Data=encoded_response_data,
        Sign=encode_base64("SYSTEM_B_RECEIPT_BATCH"),
        SignerCert=encode_base64("SYSTEM_B")
    )

    return final_response