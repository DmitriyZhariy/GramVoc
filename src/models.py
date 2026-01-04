import datetime
from typing import Optional, List, Any

import enum
from sqlalchemy import ForeignKey, Text, String, Integer, Float, DateTime, UniqueConstraint, Index, Computed
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    user_words: Mapped[List["UserWord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    user_sources: Mapped[List["UserSource"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Word(Base):
    __tablename__ = "words"

    __table_args__ = (
        UniqueConstraint("word_text", "pos", name="uq_word_text_pos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    word_text: Mapped[str] = mapped_column(String(50))
    pos: Mapped[str] = mapped_column(String(15))

    user_words: Mapped[List["UserWord"]] = relationship(back_populates="word", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String) 

    source_parts: Mapped[List["SourcePart"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    user_sources: Mapped[List["UserSource"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class SourcePart(Base):
    __tablename__ = "source_parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id")) 
    order: Mapped[int] = mapped_column(Integer) 
    source_part_text: Mapped[str] = mapped_column(Text) 

    source: Mapped["Source"] = relationship(back_populates="source_parts")
    sentences: Mapped[List["Sentence"]] = relationship(back_populates="source_part", cascade="all, delete-orphan")


class UserSource(Base):
    __tablename__ = "user_sources"

    __table_args__ = (
        UniqueConstraint("user_id", "source_id", name="uq_user_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) 
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id")) 

    user: Mapped["User"] = relationship(back_populates="user_sources")
    source: Mapped["Source"] = relationship(back_populates="user_sources")


class UserStatus(enum.Enum):
    NEW = 'new'
    LEARNING = 'learning'
    LEARNED = 'learned'


class UserWord(Base):
    __tablename__ = "user_words"

    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_user_word"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) 
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id")) 
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus, name="user_status_enum"), nullable=False) 
    quantity: Mapped[int] = mapped_column(Integer, default=0) 

    flashcards: Mapped[List["Flashcard"]] = relationship(back_populates="user_word", cascade="all, delete-orphan")
    user: Mapped["User"] = relationship(back_populates="user_words")
    word: Mapped["Word"] = relationship(back_populates="user_words")


class Sentence(Base):
    __tablename__ = "sentences"

    __table_args__ = (
        Index("ix_sentences_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_part_id: Mapped[int] = mapped_column(ForeignKey("source_parts.id"))
    sentence_text: Mapped[str] = mapped_column(Text) 
    sentence_start_index: Mapped[int] = mapped_column(Integer)
    sentence_end_index: Mapped[int] = mapped_column(Integer)
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', sentence_text)", persisted=True)
    )

    flashcard_sentences: Mapped[List["FlashcardSentence"]] = relationship(back_populates="sentence", cascade="all, delete-orphan")
    source_part: Mapped["SourcePart"] = relationship(back_populates="sentences")


class Flashcard(Base):
    __tablename__ = "flashcards"

    __table_args__ = (
        UniqueConstraint("user_word_id", "translation", name="uq_user_translation"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_word_id: Mapped[int] = mapped_column(ForeignKey("user_words.id"))
    translation: Mapped[str] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval: Mapped[int] = mapped_column(Integer, default=1)
    repetition_number: Mapped[int] = mapped_column(Integer, default=0)
    next_repeat: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    flashcard_sentences: Mapped[List["FlashcardSentence"]] = relationship(back_populates="flashcard", cascade="all, delete-orphan")
    user_word: Mapped["UserWord"] = relationship(back_populates="flashcards")


class FlashcardSentence(Base):
    __tablename__ = "flashcard_sentences"

    id: Mapped[int] = mapped_column(primary_key=True)
    flashcard_id: Mapped[int] = mapped_column(ForeignKey("flashcards.id"))
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentences.id"))

    flashcard: Mapped["Flashcard"] = relationship(back_populates="flashcard_sentences")
    sentence: Mapped["Sentence"] = relationship(back_populates="flashcard_sentences")