const REASON_KEY = {
  checkmate: "reason_checkmate",
  no_legal_moves: "reason_no_legal_moves",
  warnings_exceeded: "reason_warnings_exceeded",
  move_time_exceeded: "reason_move_time_exceeded",
  match_time_exceeded: "reason_match_time_exceeded",
  disconnect: "reason_disconnect",
  resign: "reason_resign",
  kicked: "reason_kicked",
  draw_no_progress: "reason_draw_no_progress",
  threefold_repetition: "reason_threefold_repetition",
};

let ws = null;
let myColor = null;
let boardView = null;
let latestMatrix = null;
let selectedSquare = null;
let currentTargets = [];
let latestTurn = null;
let tickTimer = null;
let turnDeadlineMs = null;

function fmtClock(seconds) {
  seconds = Math.max(0, Math.round(seconds));
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function showToast(text) {
  const toast = document.getElementById("toast");
  toast.textContent = text;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 3000);
}

function pieceAt(square) {
  if (!latestMatrix) return null;
  return latestMatrix[square[1]][square[0]];
}

function onSquareClick(square) {
  if (latestTurn !== myColor) return;
  const piece = pieceAt(square);
  if (selectedSquare && currentTargets.some((t) => t[0] === square[0] && t[1] === square[1])) {
    ws.send(JSON.stringify({ type: "move", from: selectedSquare, to: square }));
    selectedSquare = null;
    currentTargets = [];
    boardView.setState(latestMatrix, boardView.lastMove, null, []);
    return;
  }
  if (piece && piece.color === myColor) {
    selectedSquare = square;
    ws.send(JSON.stringify({ type: "legal_moves", square }));
    boardView.setState(latestMatrix, boardView.lastMove, selectedSquare, []);
    return;
  }
  selectedSquare = null;
  currentTargets = [];
  boardView.setState(latestMatrix, boardView.lastMove, null, []);
}

function connect(name) {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/player`);
  ws.addEventListener("open", () => {
    ws.send(JSON.stringify({ type: "join", name }));
  });
  ws.addEventListener("message", (ev) => handleMessage(JSON.parse(ev.data)));
  ws.addEventListener("close", () => {
    if (myColor) showToast(t("connection_lost"));
  });
}

function handleMessage(msg) {
  if (msg.type === "join_rejected") {
    document.getElementById("join-msg").textContent = t(msg.reason);
  } else if (msg.type === "joined") {
    myColor = msg.color;
    document.getElementById("join-panel").classList.add("hidden");
    document.getElementById("waiting-panel").classList.remove("hidden");
    const label = t(myColor === "red" ? "seat_red" : "seat_black");
    document.getElementById("you-are").textContent = `${t("you_are")}: ${label}`;
    document.getElementById("you-are-2").textContent = `${t("you_are")}: ${label}`;
  } else if (msg.type === "lobby_update") {
    const count = Object.keys(msg.players || {}).length;
    document.getElementById("players-count").textContent = `${count}/2`;
  } else if (msg.type === "game_started") {
    document.getElementById("waiting-panel").classList.add("hidden");
    document.getElementById("game-panel").classList.remove("hidden");
    boardView = new BoardView(document.getElementById("board"), {
      flip: myColor === "black",
      onSquareClick,
    });
  } else if (msg.type === "state") {
    renderState(msg);
  } else if (msg.type === "legal_destinations") {
    currentTargets = msg.targets;
    boardView.setState(latestMatrix, boardView.lastMove, selectedSquare, currentTargets);
  } else if (msg.type === "invalid_move") {
    showToast(`${t("warning_toast")} (${msg.warnings}/${msg.max_warnings})`);
  } else if (msg.type === "game_over") {
    showGameOver(msg);
  } else if (msg.type === "kicked") {
    showToast(t("kicked_message"));
  } else if (msg.type === "error") {
    showToast(msg.message);
  }
}

function renderState(msg) {
  latestMatrix = msg.board;
  latestTurn = msg.turn;
  selectedSquare = null;
  currentTargets = [];
  if (boardView) boardView.setState(msg.board, msg.last_move, null, []);

  const players = msg.players || {};
  document.getElementById("red-warn").textContent = players.red ? players.red.warnings : 0;
  document.getElementById("black-warn").textContent = players.black ? players.black.warnings : 0;
  document.getElementById("red-clock").textContent = players.red ? fmtClock(players.red.remaining_time) : "--:--";
  document.getElementById("black-clock").textContent = players.black ? fmtClock(players.black.remaining_time) : "--:--";

  const statusEl = document.getElementById("turn-status");
  if (msg.turn === myColor) {
    statusEl.textContent = t("your_turn");
    statusEl.classList.remove("warn");
  } else {
    statusEl.textContent = t("opponent_turn");
  }

  turnDeadlineMs = msg.turn_deadline_epoch_ms;
  restartTick(msg.turn);

  const log = document.getElementById("move-log");
  if (msg.last_move) {
    const mv = msg.last_move;
    const from = String.fromCharCode(97 + mv.from[0]) + mv.from[1];
    const to = String.fromCharCode(97 + mv.to[0]) + mv.to[1];
    const line = document.createElement("div");
    line.textContent = `${msg.move_count}. ${from}-${to}${mv.captured ? " x" : ""}${mv.check ? "+" : ""}`;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
  }
}

function restartTick(turnColor) {
  if (tickTimer) clearInterval(tickTimer);
  tickTimer = setInterval(() => {
    if (!turnDeadlineMs) return;
    const remaining = (turnDeadlineMs - Date.now()) / 1000;
    const el = document.getElementById(turnColor === "red" ? "red-clock" : "black-clock");
    el.textContent = fmtClock(remaining);
    el.classList.toggle("low", remaining < 10);
  }, 250);
}

function showGameOver(msg) {
  const overlay = document.getElementById("gameover-overlay");
  const text = document.getElementById("gameover-text");
  const reason = t(REASON_KEY[msg.reason] || msg.reason);
  if (msg.winner) {
    const youWon = msg.winner === myColor;
    text.textContent = `${t("winner_is")}: ${t(msg.winner === "red" ? "seat_red" : "seat_black")} — ${reason}`;
  } else {
    text.textContent = `${t("draw_result")} — ${reason}`;
  }
  overlay.classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  initLanguageToggle(document.getElementById("lang-select"));

  document.getElementById("join-btn").addEventListener("click", () => {
    const name = document.getElementById("name-input").value.trim() || "Player";
    connect(name);
  });

  document.getElementById("resign-btn").addEventListener("click", () => {
    if (confirm(t("confirm_resign"))) {
      ws.send(JSON.stringify({ type: "resign" }));
    }
  });
});
