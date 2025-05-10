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

            // Render checkboxes with inline choice buttons
            playerSelection.innerHTML = players.map(player => `
                <label class="player-checkbox">
                    <input type="checkbox" value="${player.id}" data-name="${player.name}" ${player.name === '이재호' ? 'checked' : ''} />
                    ${player.name}
                    <div class="inline-choice-buttons" style="display:flex; margin-top:10px; gap:5px;">
                        <button class="choice-btn" data-choice="rock">✊</button>
                        <button class="choice-btn" data-choice="paper">✋</button>
                        <button class="choice-btn" data-choice="scissors">✌️</button>
                    </div>
                </label>
            `).join('');

            // Attach checkbox and choice button event listeners
            document.querySelectorAll('.player-checkbox').forEach(container => {
                const checkbox = container.querySelector('input[type="checkbox"]');
                const choiceDiv = container.querySelector('.inline-choice-buttons');
                // Checkbox change event
                checkbox.addEventListener('change', () => {
                    if (!checkbox.checked) {
                        // clear selection if unchecked
                        choiceDiv.querySelectorAll('.choice-btn').forEach(btn => btn.classList.remove('selected'));
                        playerChoices.delete(checkbox.dataset.name);
                    }
                    // Update selectedPlayers set
                    selectedPlayers.clear();
                    document.querySelectorAll('.player-checkbox input:checked').forEach(cb => {
                        selectedPlayers.add({ id: cb.value, name: cb.dataset.name });
                    });
                    updateSubmitButton();
                });
                // Choice button events
                const playerName = checkbox.dataset.name;
                choiceDiv.querySelectorAll('.choice-btn').forEach(btn => {
                    const listener = () => handleChoice(playerName, btn);
                    btn.addEventListener('pointerdown', listener);
                    btn.addEventListener('mousedown', listener);
                    btn.addEventListener('touchstart', listener);
                });
            });

            // Apply initial checkbox state
            document.querySelectorAll('.player-checkbox input:checked').forEach(cb => cb.dispatchEvent(new Event('change')));
        } catch (error) {
            console.error('플레이어 목록 로드 실패:', error);
        }
    }

    // 선택 처리
    function handleChoice(playerName, button) {
        const container = button.closest('.player-checkbox');
        const checkbox = container.querySelector('input[type="checkbox"]');
        // Auto-check player if not already selected
        if (checkbox && !checkbox.checked) {
            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change'));
        }
        // Clear previous choice highlight
        container.querySelectorAll('.choice-btn').forEach(btn => btn.classList.remove('selected'));
        button.classList.add('selected');
        playerChoices.set(playerName, button.dataset.choice);
        updateSubmitButton();
    }

    // 제출 버튼 상태 업데이트
    function updateSubmitButton() {
        // 2명 이상 선택 && 모두 선택값 입력
        submitChoicesBtn.disabled = !(selectedPlayers.size >= 2 && playerChoices.size === selectedPlayers.size);
    }

    // 게임 결과 저장
    async function saveGameResult() {
        const gameData = {
            player_choices: Array.from(selectedPlayers).map(player => ({
                player_name: player.name,
                choice: playerChoices.get(player.name)
            }))
        };
        
        console.log('saveGameResult:', gameData);

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

        // Uncheck all checkboxes and clear any previous selection highlights
        document.querySelectorAll('.player-checkbox input').forEach(checkbox => {
            checkbox.checked = false;
            const choiceDiv = checkbox.closest('.player-checkbox').querySelector('.inline-choice-buttons');
            if (choiceDiv) {
                choiceDiv.querySelectorAll('.choice-btn').forEach(btn => btn.classList.remove('selected'));
            }
        });

        // Only check the checkbox for "이재호"
        const jaehoCheckbox = document.querySelector('input[type="checkbox"][data-name="이재호"]');
        if (jaehoCheckbox) {
            jaehoCheckbox.checked = true;
        }

        // Update submit button state
        updateSubmitButton();
    }

    // 이벤트 리스너
    submitChoicesBtn.addEventListener('click', saveGameResult);

    // 초기 로드
    loadPlayers();
    updateHistory();
    updateAnalysis();
}); 