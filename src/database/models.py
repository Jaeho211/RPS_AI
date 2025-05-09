from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
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
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    game_results = relationship("GameResult", back_populates="player")

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    player_choices = relationship("PlayerChoice", back_populates="game", cascade="all, delete-orphan")
    
    # Relationships
    results = relationship("GameResult", back_populates="game")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "players": [
                {
                    "name": pc.player_name,
                    "choice": pc.choice,
                    "is_winner": pc.is_winner
                }
                for pc in self.player_choices
            ]
        }

class GameResult(Base):
    __tablename__ = "game_results"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    choice = Column(String)  # 'rock', 'paper', 'scissors'
    is_winner = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    game = relationship("Game", back_populates="results")
    player = relationship("Player", back_populates="game_results")

class PlayerChoice(Base):
    __tablename__ = "player_choices"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_name = Column(String)
    choice = Column(String)  # 'rock', 'paper', 'scissors'
    is_winner = Column(Boolean, default=False)
    
    game = relationship("Game", back_populates="player_choices") 