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
    """
    Represents a registered user of the platform.

    Attributes:
        id (int): Unique database identifier.
        username (str): Unique name used for authentication and display.
        user_words (list[UserWord]): Collection of words currently being tracked by the user.
        user_sources (list[UserSource]): Collection of sources (books, articles, etc) linked to the user.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    user_words: Mapped[List["UserWord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    user_sources: Mapped[List["UserSource"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Word(Base):
    """
    Represents a word received from sources.

    Attributes:
        id (int): Unique database identifier.
        word_text (str): The normalized text of the lemma.
        pos (str): Part of Speech tag (e.g., NOUN, VERB) used to distinguish homonyms.
        user_words (list[UserWord]): Collection of words currently being tracked by the user.
    """
    __tablename__ = "words"

    __table_args__ = (
        UniqueConstraint("word_text", "pos", name="uq_word_text_pos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    word_text: Mapped[str] = mapped_column(String(50))
    pos: Mapped[str] = mapped_column(String(15))

    user_words: Mapped[List["UserWord"]] = relationship(back_populates="word", cascade="all, delete-orphan")


class Source(Base):
    """
    Represents a source (book, article) which was uploaded by a user.

    Attributes:
        id (int): Unique database identifier.
        title (str): Title used for display.
        source_parts (list[SourcePart]): Segments of the source text, split for efficient storage and processing.
        user_sources (list[UserSource]): Collection of sources (books, articles, etc) linked to the user.
    """
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String) 

    source_parts: Mapped[List["SourcePart"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    user_sources: Mapped[List["UserSource"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class SourcePart(Base):
    """
    Represents a segment of the source text, split for efficient storage and processing.

    Attributes:
        id (int): Unique database identifier.
        source_id (int): Foreign Key referencing the source.
        order (int): A number used to locate the part of the source in the right order.
        source_part_text (str): The unnormalized part of the raw text.
        source (Source): The source object associated with this link.
        sentences (list[Sentence]): Collection of sentences which constructs this source part.
    """
    __tablename__ = "source_parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id")) 
    order: Mapped[int] = mapped_column(Integer) 
    source_part_text: Mapped[str] = mapped_column(Text) 

    source: Mapped["Source"] = relationship(back_populates="source_parts")
    sentences: Mapped[List["Sentence"]] = relationship(back_populates="source_part", cascade="all, delete-orphan")


class UserSource(Base):
    """
    Represents a link between user and a source.

    Attributes:
        id (int): Unique database identifier.
        user_id (int): Foreign Key referencing the user.
        source_id (int): Foreign Key referencing the source.
        user (User): The user object associated with this link.
        source (Source): The source object associated with this link.
    """
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
    """
    Defines the learning progress stages for a specific word.

    Attributes:
        NEW: The word has been discovered but not yet started in the SRS cycle.
        LEARNING: The word is currently being studied via flashcards.
        LEARNED: The word is considered mastered or manually marked as known.
    """
    NEW = 'new'
    LEARNING = 'learning'
    LEARNED = 'learned'


class UserWord(Base):
    """
    Represents a word lemma currently being tracked by the user.
    Aggregates statistics for the word regardless of its specific meaning or context.

    Attributes:
        id (int): Unique database identifier.
        user_id (int): Foreign Key referencing the user.
        word_id (int): Foreign Key referencing the global word lemma.
        status (UserStatus): Current learning stage (New, Learning, Learned).
        quantity (int): Total occurrence count of this word lemma across all user sources.
        flashcards (list[Flashcard]): Collection of specific meanings/translations (cards) derived from this word.
        user (User): The user object associated with this record.
        word (Word): The global word object associated with this record.
    """
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
    """
    Represents a single parsed sentence from a source part.
    Stores both the raw text and a pre-computed vector for fast searching.

    Attributes:
        id (int): Unique database identifier.
        source_part_id (int): Foreign Key referencing the source chunk this sentence belongs to.
        sentence_text (str): The full text content of the sentence.
        sentence_start_index (int): Character index where the sentence starts in the original source part.
        sentence_end_index (int): Character index where the sentence ends.
        search_vector (Any): Pre-computed PostgreSQL TSVECTOR for optimized full-text search.
        flashcard_sentences (list[FlashcardSentence]): Collection of links to flashcards that use this sentence as an example.
        source_part (SourcePart): The source part object containing this sentence.
    """
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
    """
    Represents a specific meaning/translation of a word to be studied (SRS Card).
    Stores the state required for the SuperMemo-2 (Anki) spaced repetition algorithm.

    Attributes:
        id (int): Unique database identifier.
        user_word_id (int): Foreign Key referencing the parent user word lemma.
        translation (str): The specific translation or definition for this context.
        quantity (int): Number of times this specific meaning was encountered (contextual frequency).
        ease_factor (float): SM-2 multiplier indicating how easy the card is (default 2.5).
        interval (int): Current interval in days between reviews.
        repetition_number (int): Number of consecutive successful recalls.
        next_repeat (datetime): The calculated timestamp when the card is due for review.
        flashcard_sentences (list[FlashcardSentence]): Collection of example sentences linked to this card.
        user_word (UserWord): The parent user word object.
    """
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
    """
    Association object linking a Flashcard to an example Sentence.
    Allows a single flashcard to have multiple example sentences and vice versa.

    Attributes:
        id (int): Unique database identifier.
        flashcard_id (int): Foreign Key referencing the flashcard.
        sentence_id (int): Foreign Key referencing the sentence.
        flashcard (Flashcard): The flashcard object.
        sentence (Sentence): The sentence object used as an example context.
    """
    __tablename__ = "flashcard_sentences"

    id: Mapped[int] = mapped_column(primary_key=True)
    flashcard_id: Mapped[int] = mapped_column(ForeignKey("flashcards.id"))
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentences.id"))

    flashcard: Mapped["Flashcard"] = relationship(back_populates="flashcard_sentences")
    sentence: Mapped["Sentence"] = relationship(back_populates="flashcard_sentences")