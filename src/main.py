from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from datetime import datetime, timezone, timedelta
import time

from database.database import get_db, engine, SessionLocal
from database.models import Base, Player, Game, PlayerChoice
from schemas import GameCreate, Game as GameSchema, PlayerChoice as PlayerChoiceSchema, Player as PlayerSchema, Analysis as AnalysisSchema
from database.init_data import init_team_members

app = FastAPI()

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    init_team_members()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    version = int(time.time())
    return templates.TemplateResponse("index.html", {"request": request, "version": version})

@app.get("/players/", response_model=List[PlayerSchema])
def get_players(db: Session = Depends(get_db)):
    return db.query(Player).all()

def get_korean_time():
    return datetime.now(timezone(timedelta(hours=9)))

@app.post("/games/", response_model=GameSchema)
def create_game(game: GameCreate):
    db = SessionLocal()
    try:
        # 항상 현재 시간 사용 (클라이언트 전송값 무시)
        game_date = get_korean_time()
        print(f"사용된 시간: {game_date}")
        
        db_game = Game(game_date=game_date)
        db.add(db_game)
        db.flush()  # ID를 얻기 위해 flush
        
        # Determine winner(s) first
        submitted_choices = [pc.choice for pc in game.player_choices]
        unique_choices = list(set(submitted_choices))
        winning_choice = None

        if len(unique_choices) == 2:
            if 'rock' in unique_choices and 'scissors' in unique_choices:
                winning_choice = 'rock'
            elif 'scissors' in unique_choices and 'paper' in unique_choices:
                winning_choice = 'scissors'
            elif 'paper' in unique_choices and 'rock' in unique_choices:
                winning_choice = 'paper'
        # If len is 1 or 3, it's a tie, winning_choice remains None

        # Create and save player choices, setting is_winner
        for player_choice_data in game.player_choices:
            db_player = db.query(Player).filter(Player.name == player_choice_data.player_name).first()
            if not db_player:
                # If player does not exist, create them (should ideally not happen with pre-loaded players)
                db_player = Player(name=player_choice_data.player_name)
                db.add(db_player)
                # No flush needed here as we don't need player ID immediately for PlayerChoice

            is_winner = (player_choice_data.choice == winning_choice) if winning_choice else False

            db_player_choice = PlayerChoice(
                game_id=db_game.id,
                player_name=player_choice_data.player_name,
                choice=player_choice_data.choice,
                is_winner=is_winner
            )
            db.add(db_player_choice)

        # Debugging: Print is_winner status before commit (will now show correct status)
        print("--- Player Choices is_winner status before commit ---")
        # Iterate over the PlayerChoice objects added to the session
        for pc in db.new:
            if isinstance(pc, PlayerChoice):
                 print(f"Player: {pc.player_name}, Choice: {pc.choice}, Is Winner: {pc.is_winner}")
        print("------------------------------------------------------")

        db.commit()
        db.refresh(db_game)
        
        # 응답을 위한 딕셔너리 생성
        return {
            "id": db_game.id,
            "game_date": game_date.isoformat(),
            "created_at": db_game.created_at.isoformat() if db_game.created_at else None,
            "players": [
                {
                    "name": choice.player_name,
                    "choice": choice.choice,
                    "is_winner": choice.is_winner
                }
                for choice in db_game.player_choices
            ]
        }
    finally:
        db.close()

@app.get("/games/", response_model=List[GameSchema])
def get_games(db: Session = Depends(get_db)):
    # Return games ordered by newest first
    games = db.query(Game).order_by(Game.id.desc()).all()
    # ISO 형식으로 명확하게 변환하여 반환
    return [
        {
            "id": game.id,
            "game_date": game.game_date.isoformat() if game.game_date else None,
            "created_at": game.created_at.isoformat() if game.created_at else None,
            "players": [
                {
                    "name": choice.player_name, 
                    "choice": choice.choice,
                    "is_winner": choice.is_winner
                }
                for choice in game.player_choices
            ]
        }
        for game in games
    ]

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

@app.delete("/games/")
def delete_all_games(db: Session = Depends(get_db)):
    # Delete all player choices and games
    db.query(PlayerChoice).delete()
    db.query(Game).delete()
    db.commit()
    return {"message": "All games deleted successfully"}

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
        games_played = db.query(PlayerChoice).filter(
            PlayerChoice.player_name == player.name
        ).count()

        win_rate = (wins / games_played) * 100 if games_played > 0 else 0
        win_rates[player.name] = win_rate

        # Debugging: Print analysis calculation details
        print(f"--- Analysis for {player.name} ---")
        print(f"Wins: {wins}, Games Played: {games_played}, Calculated Win Rate: {win_rate}")
        print("----------------------------------")
    
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
