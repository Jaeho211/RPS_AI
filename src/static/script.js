document.addEventListener('DOMContentLoaded', () => {
    const playerSelection = document.getElementById('playerSelection');
    const startGameBtn = document.getElementById('startGame');
    const gamePlay = document.getElementById('gamePlay');
    const choiceInputs = document.getElementById('choiceInputs');
    const submitChoicesBtn = document.getElementById('submitChoices');
    const analysisContent = document.getElementById('analysisContent');
    const historyList = document.getElementById('historyList');

    let selectedPlayers = new Set();
    let playerChoices = new Map();

    // 플레이어 목록 로드
    async function loadPlayers() {
        try {
            const response = await fetch('/players/');
            const players = await response.json();
            
            playerSelection.innerHTML = players.map(player => `
                <label class="player-checkbox">
                    <input type="checkbox" value="${player.id}" data-name="${player.name}">
                    ${player.name}
                </label>
            `).join('');

            // 체크박스 이벤트 리스너 추가
            document.querySelectorAll('.player-checkbox input').forEach(checkbox => {
                checkbox.addEventListener('change', updateStartButton);
            });
        } catch (error) {
            console.error('플레이어 목록 로드 실패:', error);
        }
    }

    // 시작 버튼 상태 업데이트
    function updateStartButton() {
        selectedPlayers.clear();
        document.querySelectorAll('.player-checkbox input:checked').forEach(checkbox => {
            selectedPlayers.add({
                id: checkbox.value,
                name: checkbox.dataset.name
            });
        });
        startGameBtn.disabled = selectedPlayers.size < 2;
    }

    // 선택 입력 UI 생성
    function showChoiceInputs() {
        choiceInputs.innerHTML = Array.from(selectedPlayers).map(player => `
            <div class="player-choice">
                <h3>${player.name}</h3>
                <div class="choice-buttons">
                    <button class="choice-btn" data-choice="rock">✊</button>
                    <button class="choice-btn" data-choice="paper">✋</button>
                    <button class="choice-btn" data-choice="scissors">✌️</button>
                </div>
            </div>
        `).join('');

        // 선택 버튼 이벤트 리스너 추가
        document.querySelectorAll('.player-choice').forEach(choiceDiv => {
            const playerName = choiceDiv.querySelector('h3').textContent;
            choiceDiv.querySelectorAll('.choice-btn').forEach(btn => {
                btn.addEventListener('click', () => handleChoice(playerName, btn));
            });
        });

        gamePlay.style.display = 'block';
    }

    // 선택 처리
    function handleChoice(playerName, button) {
        const choiceDiv = button.closest('.player-choice');
        choiceDiv.querySelectorAll('.choice-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        button.classList.add('selected');
        playerChoices.set(playerName, button.dataset.choice);
        updateSubmitButton();
    }

    // 제출 버튼 상태 업데이트
    function updateSubmitButton() {
        submitChoicesBtn.disabled = playerChoices.size !== selectedPlayers.size;
    }

    // 게임 결과 저장
    async function saveGameResult() {
        const dateInput = document.getElementById('gameDate');
        const gameData = {
            player_choices: Array.from(selectedPlayers).map(player => ({
                player_name: player.name,
                choice: playerChoices.get(player.name)
            })),
            game_date: dateInput ? dateInput.value : undefined
        };

        try {
            const response = await fetch('/games/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(gameData)
            });

            if (response.ok) {
                const result = await response.json();
                updateAnalysis(result.analysis);
                updateHistory(result.history);
                resetGame();
            }
        } catch (error) {
            console.error('게임 결과 저장 실패:', error);
        }
    }

    // 분석 결과 업데이트
    function updateAnalysis(analysis = { winRates: {}, patterns: {}, predictions: {} }) {
        if (!analysis) return;
        const { winRates, patterns, predictions } = analysis;
        
        // 승률 분석
        document.getElementById('winRateAnalysis').innerHTML = `
            <div class="stats">
                <ul>
                    ${Object.entries(winRates).map(([player, rate]) => `
                        <li>${player}: ${(rate * 100).toFixed(1)}%</li>
                    `).join('')}
                </ul>
            </div>
        `;

        // 패턴 분석
        document.getElementById('patternAnalysis').innerHTML = `
            <div class="stats">
                <ul>
                    ${Object.entries(patterns).map(([player, pattern]) => `
                        <li>${player}: ${pattern}</li>
                    `).join('')}
                </ul>
            </div>
        `;

        // 예측 분석
        document.getElementById('predictionAnalysis').innerHTML = `
            <div class="stats">
                <ul>
                    ${Object.entries(predictions).map(([player, prediction]) => `
                        <li>${player}: ${prediction}</li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    // 게임 기록 업데이트
    async function updateHistory() {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        try {
            const response = await fetch('/games/');
            const games = await response.json();
            
            games.forEach(game => {
                const li = document.createElement('li');
                li.className = 'history-item';
                
                const gameDate = new Date(game.created_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                const gameInfo = document.createElement('div');
                gameInfo.className = 'game-info';
                gameInfo.innerHTML = `
                    <div class="game-date">${gameDate}</div>
                    <div class="game-players">
                        ${game.players.map(player => `
                            <div class="player-result ${player.is_winner ? 'winner' : 'loser'}">
                                ${player.name}: ${player.choice}
                            </div>
                        `).join('')}
                    </div>
                `;
                
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'delete-btn';
                deleteBtn.textContent = '삭제';
                deleteBtn.onclick = () => deleteGame(game.id);
                
                li.appendChild(gameInfo);
                li.appendChild(deleteBtn);
                historyList.appendChild(li);
            });
        } catch (error) {
            console.error('게임 기록을 불러오는데 실패했습니다:', error);
        }
    }

    // 게임 삭제
    async function deleteGame(gameId) {
        if (!confirm('이 게임 기록을 삭제하시겠습니까?')) {
            return;
        }
        
        try {
            const response = await fetch(`/games/${gameId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                updateHistory();
                updateAnalysis();
            } else {
                alert('게임 기록 삭제에 실패했습니다.');
            }
        } catch (error) {
            console.error('게임 기록 삭제 중 오류가 발생했습니다:', error);
            alert('게임 기록 삭제 중 오류가 발생했습니다.');
        }
    }

    // 게임 초기화
    function resetGame() {
        selectedPlayers.clear();
        playerChoices.clear();
        document.querySelectorAll('.player-checkbox input').forEach(checkbox => {
            checkbox.checked = false;
        });
        gamePlay.style.display = 'none';
        startGameBtn.disabled = true;
    }

    // 이벤트 리스너
    startGameBtn.addEventListener('click', showChoiceInputs);
    submitChoicesBtn.addEventListener('click', saveGameResult);

    // 초기 로드
    loadPlayers();
    updateHistory();
    updateAnalysis();

    // 오늘 날짜를 기본값으로 설정 (id가 'gameDate'인 input에만 적용)
    const dateInput = document.getElementById('gameDate');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
}); 