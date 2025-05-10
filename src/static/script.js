document.addEventListener('DOMContentLoaded', () => {
    const playerSelection = document.getElementById('playerSelection');
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
                    <input type="checkbox" value="${player.id}" data-name="${player.name}" ${player.name === '이재호' ? 'checked' : ''}>
                    ${player.name}
                </label>
            `).join('');

            // 체크박스 이벤트 리스너 추가
            document.querySelectorAll('.player-checkbox input').forEach(checkbox => {
                checkbox.addEventListener('change', updateStartButton);
            });

            // 초기 상태 반영
            updateStartButton();
        } catch (error) {
            console.error('플레이어 목록 로드 실패:', error);
        }
    }

    // 선택 상태 변경 시 자동 렌더링
    function updateStartButton() {
        // 현재 선택된 플레이어 집합 업데이트
        selectedPlayers.clear();
        document.querySelectorAll('.player-checkbox input:checked').forEach(checkbox => {
            selectedPlayers.add({ id: checkbox.value, name: checkbox.dataset.name });
        });
        
        if (selectedPlayers.size >= 2) {
            // 두 명 이상 선택 시 입력 UI 표시
            showChoiceInputs();
        } else {
            // 선택이 두 명 미만이면 입력 UI 숨김 및 초기화
            gamePlay.style.display = 'none';
            choiceInputs.innerHTML = '';
            playerChoices.clear();
            submitChoicesBtn.disabled = true;
        }
    }

    // 선택 입력 UI 생성
    function showChoiceInputs() {
        // 이전 입력란 초기화
        choiceInputs.innerHTML = '';
        
        // 날짜 시간 입력란 추가 (더 눈에 띄게 스타일링)
        const dateInputContainer = document.createElement('div');
        dateInputContainer.className = 'date-input-container';
        dateInputContainer.style.padding = '15px';
        dateInputContainer.style.margin = '0 0 20px 0';
        dateInputContainer.style.backgroundColor = '#f5f5f5';
        dateInputContainer.style.borderRadius = '5px';
        dateInputContainer.style.border = '1px solid #ddd';
        
        // 제목과 설명 추가
        const dateTitle = document.createElement('h3');
        dateTitle.textContent = '게임 일시';
        dateTitle.style.marginBottom = '10px';
        dateInputContainer.appendChild(dateTitle);
        
        const dateDescription = document.createElement('p');
        dateDescription.textContent = '현재 시간이 자동으로 설정됩니다. 이 시간은 게임 저장 시에 사용됩니다.';
        dateDescription.style.fontSize = '0.9em';
        dateDescription.style.marginBottom = '10px';
        dateInputContainer.appendChild(dateDescription);
        
        // 현재 시간 표시 (읽기 전용)
        const timeDisplay = document.createElement('div');
        timeDisplay.id = 'currentTimeDisplay';
        timeDisplay.style.fontSize = '1.2em';
        timeDisplay.style.fontWeight = 'bold';
        timeDisplay.style.padding = '10px';
        timeDisplay.style.backgroundColor = '#e9e9e9';
        timeDisplay.style.borderRadius = '3px';
        timeDisplay.style.textAlign = 'center';
        
        // 현재 시간 설정 및 업데이트
        function updateCurrentTime() {
            const now = new Date();
            timeDisplay.textContent = now.toLocaleString('ko-KR', {
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
        
        updateCurrentTime();
        // 1초마다 시간 업데이트
        const timeInterval = setInterval(updateCurrentTime, 1000);
        
        // 페이지 언로드 시 인터벌 정리
        window.addEventListener('beforeunload', () => {
            clearInterval(timeInterval);
        });
        
        dateInputContainer.appendChild(timeDisplay);
        choiceInputs.appendChild(dateInputContainer);
        
        // 플레이어 선택 UI 추가
        Array.from(selectedPlayers).forEach(player => {
            const playerChoiceContainer = document.createElement('div');
            playerChoiceContainer.className = 'player-choice';
            playerChoiceContainer.innerHTML = `
                <h3>${player.name}</h3>
                <div class="choice-buttons">
                    <button class="choice-btn" data-choice="rock">✊</button>
                    <button class="choice-btn" data-choice="paper">✋</button>
                    <button class="choice-btn" data-choice="scissors">✌️</button>
                </div>
            `;
            
            // 선택 버튼 이벤트 리스너 추가
            const playerName = player.name;
            playerChoiceContainer.querySelectorAll('.choice-btn').forEach(btn => {
                // 터치, 마우스 즉시 반영: pointerdown 및 mousedown 사용
                const listener = () => handleChoice(playerName, btn);
                btn.addEventListener('pointerdown', listener);
                btn.addEventListener('mousedown', listener);
                // 모바일 터치 이벤트 지원
                btn.addEventListener('touchstart', listener);
            });
            
            choiceInputs.appendChild(playerChoiceContainer);
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
        const gameData = {
            player_choices: Array.from(selectedPlayers).map(player => ({
                player_name: player.name,
                choice: playerChoices.get(player.name)
            }))
        };
        
        console.log('전송 데이터:', gameData);

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
                updateHistory();
                updateAnalysis();
                resetGame();
            } else {
                console.error('에러 응답:', await response.text());
                alert('게임 결과 저장에 실패했습니다.');
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

                // 정확한 시간 표시 (초 단위 포함)
                const gameDate = game.game_date || game.created_at;
                const parsedDate = new Date(gameDate);
                const formattedDate = parsedDate.toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });

                const gameInfo = document.createElement('div');
                gameInfo.className = 'game-info';
                gameInfo.innerHTML = `
                    <div class="game-date">${formattedDate}</div>
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
    }

    // 이벤트 리스너
    submitChoicesBtn.addEventListener('click', saveGameResult);

    // 초기 로드
    loadPlayers();
    updateHistory();
    updateAnalysis();
}); 