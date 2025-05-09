document.addEventListener('DOMContentLoaded', () => {
    const playerNameInput = document.getElementById('playerName');
    const startGameBtn = document.getElementById('startGame');
    const gameArea = document.getElementById('gameArea');
    const choices = document.getElementById('choices');
    const result = document.getElementById('result');
    const history = document.getElementById('history');
    const historyList = document.getElementById('historyList');
    const playerInfo = document.getElementById('playerInfo');
    const predictionInfo = document.getElementById('predictionInfo');

    let currentPlayer = null;

    // 게임 시작
    startGameBtn.addEventListener('click', async () => {
        const playerName = playerNameInput.value.trim();
        if (!playerName) {
            alert('플레이어 이름을 입력해주세요!');
            return;
        }

        try {
            const response = await fetch('/start_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ player_name: playerName }),
            });

            if (response.ok) {
                const data = await response.json();
                currentPlayer = data.player_id;
                gameArea.style.display = 'block';
                startGameBtn.style.display = 'none';
                playerNameInput.disabled = true;
                updatePlayerInfo(data);
            } else {
                alert('게임 시작에 실패했습니다.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('서버와 통신 중 오류가 발생했습니다.');
        }
    });

    // 선택 버튼 이벤트
    choices.addEventListener('click', async (e) => {
        if (!e.target.matches('.choice-btn')) return;
        
        const choice = e.target.dataset.choice;
        if (!choice || !currentPlayer) return;

        try {
            const response = await fetch('/play', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_id: currentPlayer,
                    choice: choice
                }),
            });

            if (response.ok) {
                const data = await response.json();
                updateResult(data);
                updateHistory(data);
                updatePlayerInfo(data);
            } else {
                alert('게임 진행에 실패했습니다.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('서버와 통신 중 오류가 발생했습니다.');
        }
    });

    // 결과 업데이트
    function updateResult(data) {
        result.innerHTML = `
            <h3>${data.result}</h3>
            <p>당신: ${data.player_choice}</p>
            <p>AI: ${data.ai_choice}</p>
        `;
    }

    // 히스토리 업데이트
    function updateHistory(data) {
        const li = document.createElement('li');
        li.className = 'history-item';
        li.textContent = `${data.player_choice} vs ${data.ai_choice} - ${data.result}`;
        historyList.insertBefore(li, historyList.firstChild);
    }

    // 플레이어 정보 업데이트
    function updatePlayerInfo(data) {
        playerInfo.innerHTML = `
            <h2>플레이어 정보</h2>
            <p>이름: ${data.player_name}</p>
            <p>승리: ${data.wins}</p>
            <p>패배: ${data.losses}</p>
            <p>무승부: ${data.draws}</p>
        `;

        if (data.prediction) {
            predictionInfo.innerHTML = `
                <h2>AI 예측</h2>
                <p>다음 선택 예측: ${data.prediction}</p>
                <p>예측 확률: ${(data.prediction_probability * 100).toFixed(1)}%</p>
            `;
        }
    }
}); 