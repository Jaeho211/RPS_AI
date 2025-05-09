from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import enum

Base = declarative_base()

class Choice(enum.Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    game_participations = relationship("GameParticipation", back_populates="player")
    choices = relationship("PlayerChoice", back_populates="player")

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    participations = relationship("GameParticipation", back_populates="game")
    choices = relationship("PlayerChoice", back_populates="game")

class GameParticipation(Base):
    __tablename__ = "game_participations"
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    is_winner = Column(Integer, default=0)  # 0: 패배, 1: 승리
    
    # Relationships
    game = relationship("Game", back_populates="participations")
    player = relationship("Player", back_populates="game_participations")

class PlayerChoice(Base):
    __tablename__ = "player_choices"
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    choice = Column(Enum(Choice), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    game = relationship("Game", back_populates="choices")
    player = relationship("Player", back_populates="choices") 