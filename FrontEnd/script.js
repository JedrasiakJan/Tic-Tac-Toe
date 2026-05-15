// Pobieramy elementy ze strony
const statusDiv = document.getElementById('status');
const errorDiv = document.getElementById('error');
const cells = document.querySelectorAll('.cell');
const myRoleDiv = document.getElementById('my-role');
const restartBtn = document.getElementById('restart-btn');
// Łączymy się z Twoim serwerem
const socket = new WebSocket(`ws://${window.location.hostname}:8000/ws/testowy`);

// Wszystkie możliwe linie wygrywające
const winningCombinations = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], // Poziomo
    [0, 3, 6], [1, 4, 7], [2, 5, 8], // Pionowo
    [0, 4, 8], [2, 4, 6]             // Na skos
];

// Funkcja, która szuka wygrywającej linii na podstawie planszy
function getWinningLine(board, winner) {
    if (!winner || winner === "Draw") return null;
    for (let combo of winningCombinations) {
        if (board[combo[0]] === winner && 
            board[combo[1]] === winner && 
            board[combo[2]] === winner) {
            return combo; // Zwraca np. [0, 1, 2]
        }
    }
    return null;
}

socket.onopen = () => {
    console.log("Połączono z serwerem!");
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    errorDiv.textContent = "";

    if (data.message) statusDiv.textContent = data.message;
    
    if (data.your_role) {
        myRoleDiv.textContent = `Twój znak: ${data.your_role}`;
        myRoleDiv.className = `role-badge ${data.your_role}`;
    }

    if (data.error) errorDiv.textContent = data.error;

    if (data.board) {
        // Sprawdzamy, czy ktoś wygrał i pobieramy numery jego pól
        const winningLine = getWinningLine(data.board, data.winner);

        data.board.forEach((cellValue, index) => {
            cells[index].textContent = cellValue === " " ? "" : cellValue;
            
            // Zawsze najpierw czyścimy stare klasy (tzw. twardy reset wyglądu)
            cells[index].className = "cell"; 
            
            if (cellValue === "X") cells[index].classList.add("X");
            if (cellValue === "O") cells[index].classList.add("O");

            // Efekty wizualne wygranej
            if (winningLine) {
                if (winningLine.includes(index)) {
                    // To pole jest częścią wygrywającej linii!
                    cells[index].classList.add("winning-cell");
                } else {
                    // To pole przegrało - przyciemniamy je
                    cells[index].classList.add("dimmed");
                }
            }
        });

        // Aktualizacja statusu
        if (data.winner) {
            restartBtn.style.display = "block"; // POKAŻ PRZYCISK PO ZAKOŃCZENIU GRY
            if (data.winner === "Draw") {
                statusDiv.textContent = "KONIEC GRY: REMIS! 🤝";
            } else {
                statusDiv.textContent = `WYGRYWA GRACZ ${data.winner}! 🏆`;
            }
        } else {
            restartBtn.style.display = "none"; // UKRYJ PRZYCISK PODCZAS GRY
            statusDiv.textContent = `TURA GRACZA: ${data.turn}`;
        }
    }
};
// Obsługa kliknięcia "Zagraj ponownie"
restartBtn.addEventListener('click', () => {
    socket.send(JSON.stringify({ index: -1 }));
});

cells.forEach(cell => {
    cell.addEventListener('click', () => {
        const index = cell.getAttribute('data-index');
        // Tutaj też musi być zapakowane!
        socket.send(JSON.stringify({ index: parseInt(index) }));
    });
});