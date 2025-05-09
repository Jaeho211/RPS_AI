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

from database.database import get_db, engine
from database.models import Base, Player, Game, GameParticipation, PlayerChoice, Choice
from models.predictor import RPSPredictor

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()
predictor = RPSPredictor()

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class StartGameRequest(BaseModel):
    player_name: str

class PlayGameRequest(BaseModel):
    player_id: int
    choice: str

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

@app.post("/start_game")
def start_game(request: StartGameRequest, db: Session = Depends(get_db)):
    # 플레이어 생성 또는 기존 플레이어 찾기
    player = db.query(Player).filter(Player.name == request.player_name).first()
    if not player:
        player = Player(name=request.player_name)
        db.add(player)
        db.commit()
        db.refresh(player)
    
    # 플레이어의 게임 통계 계산
    wins = db.query(GameParticipation).filter(
        GameParticipation.player_id == player.id,
        GameParticipation.is_winner == 1
    ).count()
    
    total_games = db.query(GameParticipation).filter(
        GameParticipation.player_id == player.id
    ).count()
    
    # AI 예측 가져오기
    prediction = predictor.predict_next_choice(player.id)
    prediction_probability = 0.33  # 초기 예측은 랜덤 확률

    return {
        "player_id": player.id,
        "player_name": player.name,
        "wins": wins,
        "losses": total_games - wins,
        "draws": 0,  # 나중에 구현
        "prediction": prediction,
        "prediction_probability": prediction_probability
    }

@app.post("/play")
def play_game(request: PlayGameRequest, db: Session = Depends(get_db)):
    # AI의 선택 (랜덤)
    ai_choice = random.choice(['rock', 'paper', 'scissors'])
    
    # 게임 생성
    game = Game()
    db.add(game)
    db.commit()
    
    # 플레이어의 선택 저장
    player_choice = PlayerChoice(
        game_id=game.id,
        player_id=request.player_id,
        choice=Choice(request.choice)
    )
    db.add(player_choice)
    
    # AI의 선택 저장
    ai_player = db.query(Player).filter(Player.name == 'AI').first()
    if not ai_player:
        ai_player = Player(name='AI')
        db.add(ai_player)
        db.commit()
    
    ai_player_choice = PlayerChoice(
        game_id=game.id,
        player_id=ai_player.id,
        choice=Choice(ai_choice)
    )
    db.add(ai_player_choice)
    
    # 승자 결정
    result = determine_winner(request.choice, ai_choice)
    
    # 참여 정보 저장
    player_participation = GameParticipation(
        game_id=game.id,
        player_id=request.player_id,
        is_winner=1 if result == "승리" else 0
    )
    db.add(player_participation)
    
    ai_participation = GameParticipation(
        game_id=game.id,
        player_id=ai_player.id,
        is_winner=1 if result == "패배" else 0
    )
    db.add(ai_participation)
    
    # AI 모델 업데이트
    predictor.update_model(request.player_id, [request.choice])
    
    # 플레이어의 게임 통계 계산
    wins = db.query(GameParticipation).filter(
        GameParticipation.player_id == request.player_id,
        GameParticipation.is_winner == 1
    ).count()
    
    total_games = db.query(GameParticipation).filter(
        GameParticipation.player_id == request.player_id
    ).count()
    
    # 다음 선택 예측
    next_prediction = predictor.predict_next_choice(request.player_id)
    prediction_probability = 0.33  # 초기 예측은 랜덤 확률
    
    db.commit()
    
    return {
        "player_choice": request.choice,
        "ai_choice": ai_choice,
        "result": result,
        "player_name": db.query(Player).get(request.player_id).name,
        "wins": wins,
        "losses": total_games - wins,
        "draws": 0,  # 나중에 구현
        "prediction": next_prediction,
        "prediction_probability": prediction_probability
    }

def determine_winner(player_choice: str, ai_choice: str) -> str:
    if player_choice == ai_choice:
        return "무승부"
    
    winning_moves = {
        'rock': 'scissors',
        'paper': 'rock',
        'scissors': 'paper'
    }
    
    return "승리" if winning_moves[player_choice] == ai_choice else "패배"

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