from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import random
from pydantic import BaseModel
from datetime import datetime

from database.database import get_db, engine, SessionLocal
from database.models import Base, Player, Game, PlayerChoice
from schemas import GameCreate, Game as GameSchema, PlayerChoice as PlayerChoiceSchema, Player as PlayerSchema, Analysis as AnalysisSchema

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/players/", response_model=List[PlayerSchema])
def get_players(db: Session = Depends(get_db)):
    return db.query(Player).all()

@app.post("/games/", response_model=GameSchema)
def create_game(game: GameCreate, db: Session = Depends(get_db)):
    try:
        # 게임 생성 (game_date는 이미 기본값으로 설정되어 있음)
        db_game = Game(created_at=game.game_date)
        db.add(db_game)
        db.flush()
        
        print(f"Created game with ID: {db_game.id} at {game.game_date}")
        
        # 플레이어 선택 저장
        choices = {}
        for player_choice in game.player_choices:
            choices[player_choice.player_name] = player_choice.choice
            db_player_choice = PlayerChoice(
                game_id=db_game.id,
                player_name=player_choice.player_name,
                choice=player_choice.choice,
                is_winner=False  # 초기값 설정
            )
            db.add(db_player_choice)
            print(f"Added choice for {player_choice.player_name}: {player_choice.choice}")
        
        # 승자 결정
        winners = determine_winners(choices)
        print(f"Winners: {winners}")
        
        # 승자 표시 업데이트
        for player_choice in db_game.player_choices:
            if player_choice.player_name in winners:
                player_choice.is_winner = True
                print(f"Marked {player_choice.player_name} as winner")
        
        db.commit()
        db.refresh(db_game)
        
        # 결과 확인
        result = db_game.to_dict()
        print(f"Final game result: {result}")
        
        return result
    except Exception as e:
        print(f"Error creating game: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

def determine_winners(choices):
    if len(set(choices.values())) == 1:
        return list(choices.keys())  # 모두 같은 선택이면 무승부
    
    if len(set(choices.values())) == 2:
        # 두 가지 선택만 있는 경우
        choice1, choice2 = set(choices.values())
        if (choice1 == "rock" and choice2 == "scissors") or \
           (choice1 == "scissors" and choice2 == "paper") or \
           (choice1 == "paper" and choice2 == "rock"):
            winner_choice = choice1
        else:
            winner_choice = choice2
        
        return [name for name, choice in choices.items() if choice == winner_choice]
    
    # 세 가지 선택이 모두 있는 경우
    if "rock" in choices.values() and "paper" in choices.values() and "scissors" in choices.values():
        return [name for name, choice in choices.items() if choice == "paper"]
    
    return []

@app.get("/games/", response_model=List[GameSchema])
def get_games(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return [game.to_dict() for game in games]

@app.delete("/games/{game_id}")
def delete_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # 관련된 플레이어 선택 기록도 함께 삭제
    db.query(PlayerChoice).filter(PlayerChoice.game_id == game_id).delete()
    db.delete(game)
    db.commit()
    
    return {"message": "Game deleted successfully"}

@app.get("/analysis/", response_model=AnalysisSchema)
def get_analysis(db: Session = Depends(get_db)):
    # 승률 분석
    total_games = db.query(Game).count()
    if total_games == 0:
        return AnalysisSchema(
            win_rates={},
            choice_patterns={},
            predictions={}
        )
    
    # 각 플레이어의 승률 계산
    win_rates = {}
    for player in db.query(Player).all():
        wins = db.query(PlayerChoice).filter(
            PlayerChoice.player_name == player.name,
            PlayerChoice.is_winner == True
        ).count()
        win_rates[player.name] = (wins / total_games) * 100 if total_games > 0 else 0
    
    # 선택 패턴 분석
    choice_patterns = {}
    for player in db.query(Player).all():
        choices = db.query(PlayerChoice).filter(
            PlayerChoice.player_name == player.name
        ).all()
        
        pattern = {
            'rock': len([c for c in choices if c.choice == 'rock']),
            'paper': len([c for c in choices if c.choice == 'paper']),
            'scissors': len([c for c in choices if c.choice == 'scissors'])
        }
        choice_patterns[player.name] = pattern
    
    # 다음 선택 예측 (간단한 패턴 기반 예측)
    predictions = {}
    for player in db.query(Player).all():
        recent_choices = db.query(PlayerChoice).filter(
            PlayerChoice.player_name == player.name
        ).order_by(PlayerChoice.game_id.desc()).limit(5).all()
        
        if recent_choices:
            # 가장 최근 선택을 기반으로 예측
            last_choice = recent_choices[0].choice
            if last_choice == 'rock':
                predictions[player.name] = 'paper'
            elif last_choice == 'paper':
                predictions[player.name] = 'scissors'
            else:
                predictions[player.name] = 'rock'
        else:
            predictions[player.name] = 'rock'  # 기본값
    
    return AnalysisSchema(
        win_rates=win_rates,
        choice_patterns=choice_patterns,
        predictions=predictions
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 