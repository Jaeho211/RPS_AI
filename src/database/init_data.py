from database.database import SessionLocal
from database.models import Player, Game, GameResult

def init_team_members():
    team_members = [
        "이재호",
        "이정용",
        "이혜진",
        "김경모",
        "김기남"
    ]
    
    db = SessionLocal()
    try:
        # 기존 플레이어 확인
        existing_players = {p.name: p for p in db.query(Player).all()}
        
        # 새로운 팀원 추가
        for name in team_members:
            if name not in existing_players:
                player = Player(name=name)
                db.add(player)
        
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    init_team_members() 