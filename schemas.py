from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# 1 слой
class SignedApiData(BaseModel):
    Data: str
    Sign: str
    SignerCert: str


class SearchRequest(BaseModel):
    StartDate: datetime = Field(..., description="Начало периода поиска (UTC)")
    EndDate: datetime = Field(..., description="Конец периода поиска (UTC)")
    Limit: int = Field(..., description="Максимальное количество сообщений")
    Offset: int = Field(..., description="Смещение для пагинации")


# 2 слой
class TransactionSchema(BaseModel):
    transaction_type: int = Field(alias="Transaction Type")
    data: str = Field(alias="Data", description="Сериализованный JSON пакет данных")
    hash: Optional[str] = Field(None, alias="Hash")

    sign: str = Field(alias="Sign")
    signer_cert: str = Field(alias="SignerCert")

    transaction_time: datetime = Field(alias="Transaction Time")
    metadata: Optional[str] = Field(None, alias="Metadata")

    transaction_in: Optional[str] = Field(None, alias="TransactionIn")
    transaction_out: Optional[str] = Field(None, alias="TransactionOut")

    class Config:
        populate_by_name = True


class TransactionsDataSchema(BaseModel):
    Transactions: List[TransactionSchema]
    Count: int


# 3 слой
class MessageSchema(BaseModel):
    data: str = Field(alias="Data", description="Сериализованный JSON пакет данных информационного сообщения")
    sender_branch: str = Field(alias="SenderBranch")
    receiver_branch: str = Field(alias="ReceiverBranch")
    info_message_type: int = Field(alias="InfoMessageType")
    message_time: datetime = Field(alias="MessageTime")
    chain_guid: UUID = Field(alias="ChainGuid")
    previous_transaction_hash: Optional[str] = Field(None, alias="Previous TransactionHash")
    metadata: Optional[str] = Field(None, alias="Metadata")

    model_config = ConfigDict(populate_by_name=True)


# 4 слой
class ReceiptMessageSchema(BaseModel):
    bank_guarantee_hash: str = Field(alias="BankGuaranteeHash")

    model_config = ConfigDict(populate_by_name=True)


class TaxsSchema(BaseModel):
    number: str = Field(alias="Number")
    name_tax: str = Field(alias="NameTax")
    name_tax_json: Optional[str] = Field(None, alias="Name Tax")
    amount: Decimal = Field(alias="Amount")
    penny_amount: Decimal = Field(alias="PennyAmount")

    model_config = ConfigDict(populate_by_name=True)


class ObligationSchema(BaseModel):
    type_id: int = Field(alias="Type")
    start_date: Optional[datetime] = Field(None, alias="StartDate")
    end_date: Optional[datetime] = Field(None, alias="EndDate")
    act_date: Optional[datetime] = Field(None, alias="ActDate")
    act_number: Optional[str] = Field(None, alias="ActNumber")
    taxs: Optional[List[TaxsSchema]] = Field(None, alias="Taxs")

    model_config = ConfigDict(populate_by_name=True)


class GuaranteeMessageSchema(BaseModel):
    information_type: int = Field(201, alias="Information Type")
    information_type_string: str = Field("Выдача гарантии", alias="Information TypeString")
    number: str = Field(alias="Number")
    issued_date: datetime = Field(alias="IssuedDate")
    guarantor: str = Field(alias="Guarantor")
    beneficiary: str = Field(alias="Beneficiary")
    principal: str = Field(alias="Principal")
    obligations: List[ObligationSchema] = Field(alias="Obligations")
    start_date: datetime = Field(alias="StartDate")
    end_date: datetime = Field(alias="EndDate")
    currency_code: str = Field(alias="CurrencyCode")
    currency_name: str = Field(alias="CurrencyName")
    amount: Decimal = Field(alias="Amount")
    revokation_info: str = Field(alias="RevokationInfo")
    claim_right_transfer: str = Field(alias="ClaimRight Transfer")
    payment_period: str = Field(alias="PaymentPeriod")
    signer_name: str = Field(alias="SignerName")
    authorized_position: str = Field(alias="Authorized Position")
    bank_guarantee_hash: str = Field(alias="BankGuaranteeHash")

    model_config = ConfigDict(populate_by_name=True)


class AcceptanceMessageSchema(BaseModel):
    name: str = Field(alias="Name")
    bank_guarantee_hash: str = Field(alias="BankGuaranteeHash")
    sign: str = Field(alias="Sign")
    signer_cert: str = Field(alias="SignerCert")

    model_config = ConfigDict(populate_by_name=True)


class RejectionMessageSchema(BaseModel):
    name: str = Field(alias="Name")
    bank_guarantee_hash: str = Field(alias="BankGuaranteeHash")
    sign: str = Field(alias="Sign")
    signer_cert: str = Field(alias="SignerCert")
    reason: str = Field(alias="Reason")

    model_config = ConfigDict(populate_by_name=True)




