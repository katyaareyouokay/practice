from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Integer, String, Text, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SearchPhrase(Base):
    __tablename__ = "search_phrases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phrase: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    top_requests: Mapped[List["TopRequest"]] = relationship(back_populates="search_phrase")
    dynamics: Mapped[List["Dynamics"]] = relationship(back_populates="search_phrase")

    def __repr__(self):
        return f"<SearchPhrase(id={self.id}, phrase='{self.phrase}')>"


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)

    top_requests: Mapped[List["TopRequest"]] = relationship(back_populates="region")
    dynamics: Mapped[List["Dynamics"]] = relationship(back_populates="region")

    def __repr__(self):
        return f"<Region(id={self.id}, label='{self.label}')>"


class TopRequest(Base):
    __tablename__ = "top_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_phrase_id: Mapped[int] = mapped_column(ForeignKey("search_phrases.id"), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regions.id"), nullable=True)
    device: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_count: Mapped[Optional[int]] = mapped_column(Integer)

    search_phrase: Mapped["SearchPhrase"] = relationship(back_populates="top_requests")
    region: Mapped[Optional["Region"]] = relationship(back_populates="top_requests")
    items: Mapped[List["TopRequestItem"]] = relationship(back_populates="top_request")

    def __repr__(self):
        return f"<TopRequest(id={self.id}, phrase_id={self.search_phrase_id}, total_count={self.total_count})>"


class TopRequestItem(Base):
    __tablename__ = "top_request_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    top_request_id: Mapped[int] = mapped_column(ForeignKey("top_requests.id"), nullable=False)
    phrase: Mapped[str] = mapped_column(Text, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)

    top_request: Mapped["TopRequest"] = relationship(back_populates="items")

    def __repr__(self):
        return f"<TopRequestItem(phrase='{self.phrase}', count={self.count})>"


class Dynamics(Base):
    __tablename__ = "dynamics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_phrase_id: Mapped[int] = mapped_column(ForeignKey("search_phrases.id"), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regions.id"), nullable=True)
    device: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    search_phrase: Mapped["SearchPhrase"] = relationship(back_populates="dynamics")
    region: Mapped[Optional["Region"]] = relationship(back_populates="dynamics")
    points: Mapped[List["DynamicsPoint"]] = relationship(back_populates="dynamics")

    def __repr__(self):
        return f"<Dynamics(id={self.id}, period={self.period}, from={self.from_date}, to={self.to_date})>"


class DynamicsPoint(Base):
    __tablename__ = "dynamics_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dynamics_id: Mapped[int] = mapped_column(ForeignKey("dynamics.id"), nullable=False)
    point_date: Mapped[date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    share: Mapped[float] = mapped_column(Float, nullable=False)

    dynamics: Mapped["Dynamics"] = relationship(back_populates="points")

    def __repr__(self):
        return f"<DynamicsPoint(date={self.date}, count={self.count}, share={self.share})>"
