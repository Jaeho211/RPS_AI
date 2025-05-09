# RPS AI (Rock Paper Scissors AI)

여러 명이 참여하는 가위바위보 게임의 패턴을 분석하고 예측하는 AI 시스템입니다.

## 기능

- 다중 참여자(3-6명) 가위바위보 게임 기록 저장
- 각 참여자별 과거 기록 기반 다음 선택 예측
- 참여자별 승률 및 패턴 분석
- 웹 인터페이스를 통한 쉬운 사용

## 기술 스택

- Backend: Python (FastAPI)
- Frontend: React
- Database: SQLite
- AI: scikit-learn

## 설치 및 실행

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 서버 실행:
```bash
python src/main.py
```

3. 웹 브라우저에서 `http://localhost:8000` 접속

## 사용 방법

1. 게임 시작 버튼을 클릭
2. 참여자 수와 이름 입력 (3-6명)
3. 각 참여자의 선택(가위/바위/보) 입력
4. AI가 각 참여자별로 다음 게임에서의 선택을 예측해줍니다
5. 승자 정보와 함께 게임 결과 저장

## 데이터 분석

- 각 참여자별 승률 통계
- 참여자별 선호하는 선택 패턴 분석
- 특정 참여자와의 대결에서의 승률 분석
- 전체 게임 기록 조회 및 통계