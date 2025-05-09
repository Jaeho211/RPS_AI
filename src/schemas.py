from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Player(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class PlayerChoice(BaseModel):
    player_name: str
    choice: str

class GameCreate(BaseModel):
    player_choices: List[PlayerChoice]
    game_date: datetime = datetime.now()

class Game(BaseModel):
    id: int
    created_at: datetime
    players: List[dict]

    class Config:
        from_attributes = True

class Analysis(BaseModel):
    win_rates: dict
    choice_patterns: dict
    predictions: dict 