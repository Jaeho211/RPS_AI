from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from database.database import get_db, engine
from database.models import Base, Player, Game, GameParticipation, PlayerChoice, Choice
from models.predictor import RPSPredictor

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()
predictor = RPSPredictor()

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/players/")
def create_player(name: str, db: Session = Depends(get_db)):
    player = Player(name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player

@app.get("/players/", response_model=List[dict])
def get_players(db: Session = Depends(get_db)):
    players = db.query(Player).all()
    return [{"id": p.id, "name": p.name} for p in players]

@app.post("/games/")
def create_game(player_ids: List[int], choices: List[str], db: Session = Depends(get_db)):
    if len(player_ids) != len(choices):
        raise HTTPException(status_code=400, detail="Number of players and choices must match")
    
    if not (3 <= len(player_ids) <= 6):
        raise HTTPException(status_code=400, detail="Number of players must be between 3 and 6")
    
    # 게임 생성
    game = Game()
    db.add(game)
    db.commit()
    
    # 각 플레이어의 선택과 참여 정보 저장
    winners = []
    for player_id, choice in zip(player_ids, choices):
        # 선택 저장
        player_choice = PlayerChoice(
            game_id=game.id,
            player_id=player_id,
            choice=Choice(choice)
        )
        db.add(player_choice)
        
        # 참여 정보 저장
        participation = GameParticipation(
            game_id=game.id,
            player_id=player_id
        )
        db.add(participation)
        
        # AI 모델 업데이트
        predictor.update_model(player_id, [choice])
    
    # 승자 결정
    choices_dict = {player_id: choice for player_id, choice in zip(player_ids, choices)}
    winners = determine_winners(choices_dict)
    
    # 승자 정보 업데이트
    for winner_id in winners:
        participation = db.query(GameParticipation).filter(
            GameParticipation.game_id == game.id,
            GameParticipation.player_id == winner_id
        ).first()
        if participation:
            participation.is_winner = 1
    
    db.commit()
    return {"game_id": game.id, "winners": winners}

@app.get("/predict/{player_id}")
def predict_next_choice(player_id: int):
    prediction = predictor.predict_next_choice(player_id)
    stats = predictor.get_player_stats(player_id)
    return {
        "prediction": prediction,
        "stats": stats
    }

def determine_winners(choices_dict):
    """가위바위보 게임의 승자 결정"""
    choices = list(choices_dict.values())
    if len(set(choices)) == 1:  # 모두 같은 선택
        return list(choices_dict.keys())
    
    # 각 선택별로 이길 수 있는 선택들
    beats = {
        'rock': 'scissors',
        'paper': 'rock',
        'scissors': 'paper'
    }
    
    winners = []
    for player_id, choice in choices_dict.items():
        # 이 플레이어의 선택이 이길 수 있는 선택을 한 플레이어가 있는지 확인
        can_beat_anyone = any(
            beats[choice] == other_choice
            for other_choice in choices
            if other_choice != choice
        )
        
        # 이 플레이어의 선택이 질 수 있는 선택을 한 플레이어가 없는지 확인
        cannot_be_beaten = not any(
            beats[other_choice] == choice
            for other_choice in choices
            if other_choice != choice
        )
        
        if can_beat_anyone and cannot_be_beaten:
            winners.append(player_id)
    
    return winners

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 