from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import DateTime as _DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class PhotoItem(Base):
    __tablename__ = "photo_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True, index=True
    )
    filename: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(
        _DateTime(timezone=True), nullable=True
    )
    sha256: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        _DateTime(timezone=True), server_default=func.now()
    )

    # relationships
    shortlist_entries = relationship(
        "ShortlistEntry", back_populates="photo", cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="photo", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(
        _DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        _DateTime(timezone=True), nullable=True
    )
    status: Mapped[RunStatus] = mapped_column(
        String(32), nullable=False, default=RunStatus.PENDING.value
    )

    shortlist_entries = relationship(
        "ShortlistEntry", back_populates="run", cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="run", cascade="all, delete-orphan")


class ShortlistEntry(Base):
    __tablename__ = "shortlist_entries"
    __table_args__ = (
        UniqueConstraint("photo_id", "run_id", name="uq_shortlist_photo_run"),
        Index("ix_shortlist_rank", "rank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photo_items.id"), nullable=False, index=True
    )
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id"), nullable=False, index=True
    )
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        _DateTime(timezone=True), server_default=func.now()
    )

    photo = relationship("PhotoItem", back_populates="shortlist_entries")
    run = relationship("Run", back_populates="shortlist_entries")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_external_id", "external_order_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("runs.id"), nullable=True, index=True
    )
    photo_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("photo_items.id"), nullable=True, index=True
    )
    external_order_id: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, unique=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        String(32), nullable=False, default=OrderStatus.PENDING.value
    )
    created_at: Mapped[datetime] = mapped_column(
        _DateTime(timezone=True), server_default=func.now()
    )

    run = relationship("Run", back_populates="orders")
    photo = relationship("PhotoItem", back_populates="orders")
