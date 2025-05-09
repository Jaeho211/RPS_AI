import numpy as np
from sklearn.ensemble import RandomForestClassifier
from collections import deque
import pandas as pd

class RPSPredictor:
    def __init__(self, sequence_length=5):
        self.sequence_length = sequence_length
        self.models = {}  # player_id: model
        self.histories = {}  # player_id: deque of choices
        self.choice_map = {'rock': 0, 'paper': 1, 'scissors': 2}
        self.reverse_choice_map = {0: 'rock', 1: 'paper', 2: 'scissors'}
    
    def _prepare_sequence(self, history):
        """과거 선택들을 시퀀스로 변환"""
        if len(history) < self.sequence_length:
            return None
        
        X = []
        y = []
        
        for i in range(len(history) - self.sequence_length):
            sequence = history[i:i + self.sequence_length]
            next_choice = history[i + self.sequence_length]
            
            X.append([self.choice_map[choice] for choice in sequence])
            y.append(self.choice_map[next_choice])
        
        return np.array(X), np.array(y)
    
    def update_model(self, player_id, choices):
        """특정 플레이어의 모델을 업데이트"""
        if player_id not in self.histories:
            self.histories[player_id] = deque(maxlen=100)  # 최근 100게임만 저장
        
        # 선택 기록 업데이트
        for choice in choices:
            self.histories[player_id].append(choice)
        
        # 충분한 데이터가 쌓였을 때만 모델 학습
        if len(self.histories[player_id]) > self.sequence_length:
            X, y = self._prepare_sequence(list(self.histories[player_id]))
            if X is not None and len(X) > 0:
                if player_id not in self.models:
                    self.models[player_id] = RandomForestClassifier(n_estimators=100)
                self.models[player_id].fit(X, y)
    
    def predict_next_choice(self, player_id):
        """다음 선택 예측"""
        if player_id not in self.models or player_id not in self.histories:
            return np.random.choice(['rock', 'paper', 'scissors'])
        
        history = list(self.histories[player_id])
        if len(history) < self.sequence_length:
            return np.random.choice(['rock', 'paper', 'scissors'])
        
        # 최근 시퀀스 준비
        recent_sequence = [self.choice_map[choice] for choice in history[-self.sequence_length:]]
        X = np.array([recent_sequence])
        
        # 예측
        prediction = self.models[player_id].predict(X)[0]
        return self.reverse_choice_map[prediction]
    
    def get_player_stats(self, player_id):
        """플레이어의 통계 정보 반환"""
        if player_id not in self.histories:
            return None
        
        history = list(self.histories[player_id])
        if not history:
            return None
        
        # 선택 빈도 계산
        choice_counts = pd.Series(history).value_counts()
        total_games = len(history)
        
        return {
            'total_games': total_games,
            'choice_distribution': {
                choice: count/total_games 
                for choice, count in choice_counts.items()
            }
        } 