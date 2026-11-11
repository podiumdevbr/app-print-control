
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Equipment(Base):
    """Cadastro permanente dos equipamentos."""

    __tablename__ = "equipments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    identifier: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    first_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    readings: Mapped[list["Reading"]] = relationship(
        back_populates="equipment",
    )


class Location(Base):
    """Cadastro das localizações dos equipamentos."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    readings: Mapped[list["Reading"]] = relationship(
        back_populates="location",
    )


class Competency(Base):
    """Representa um mês e ano de referência."""

    __tablename__ = "competencies"

    __table_args__ = (
        UniqueConstraint(
            "year",
            "month",
            name="uq_competency_year_month",
        ),
        CheckConstraint(
            "month >= 1 AND month <= 12",
            name="ck_competency_month",
        ),
        CheckConstraint(
            "year >= 2015",
            name="ck_competency_year",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    imports: Mapped[list["Import"]] = relationship(
        back_populates="competency",
    )

    readings: Mapped[list["Reading"]] = relationship(
        back_populates="competency",
    )


class Import(Base):
    """Registra cada arquivo recebido e processado."""

    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    competency_id: Mapped[int] = mapped_column(
        ForeignKey("competencies.id"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    total_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    imported_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    imported_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    competency: Mapped["Competency"] = relationship(
        back_populates="imports",
    )

    readings: Mapped[list["Reading"]] = relationship(
        back_populates="source_import",
    )


class Reading(Base):
    """Armazena os dados mensais de cada equipamento."""

    __tablename__ = "readings"

    __table_args__ = (
        UniqueConstraint(
            "competency_id",
            "equipment_id",
            name="uq_reading_competency_equipment",
        ),
        CheckConstraint(
            "impressions >= 0",
            name="ck_reading_impressions_nonnegative",
        ),
        Index(
            "ix_readings_competency_location",
            "competency_id",
            "location_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    competency_id: Mapped[int] = mapped_column(
        ForeignKey("competencies.id"),
        nullable=False,
    )

    import_id: Mapped[int] = mapped_column(
        ForeignKey("imports.id"),
        nullable=False,
        index=True,
    )

    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipments.id"),
        nullable=False,
        index=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
        index=True,
    )

    group_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    scanning: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    impressions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    added_to_system: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_successful_collection: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    competency: Mapped["Competency"] = relationship(
        back_populates="readings",
    )

    equipment: Mapped["Equipment"] = relationship(
        back_populates="readings",
    )

    location: Mapped["Location | None"] = relationship(
        back_populates="readings",
    )

    source_import: Mapped["Import"] = relationship(
        back_populates="readings",
    )
