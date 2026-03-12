from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TransactionModel(Base):
    __tablename__ = "transactions"

    # Hash первичный ключ тк он уникально идентифицирует транзакцию
    hash: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    transaction_type: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    sign: Mapped[str] = mapped_column(Text, nullable=False)

    signer_cert: Mapped[str] = mapped_column(Text, nullable=False)
    transaction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    meta_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Предыдущая транзакция и следующая транзацкии
    transaction_in: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transaction_out: Mapped[str | None] = mapped_column(String(64), nullable=True)