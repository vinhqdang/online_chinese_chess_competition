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
};

let ws = null;
let boardView = null;
let latestConfig = null;
let latestPhase = "lobby";
let tickTimer = null;
let turnDeadlineMs = null;
let currentTurnColor = null;

function fmtClock(seconds) {
  seconds = Math.max(0, Math.round(seconds));
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/admin`);
  ws.addEventListener("message", (ev) => handleMessage(JSON.parse(ev.data)));
  ws.addEventListener("close", () => {
    setTimeout(connect, 2000);
  });
}

function handleMessage(msg) {
  if (msg.type === "server_info") {
    latestConfig = msg.config;
    fillConfigForm(latestConfig);
  } else if (msg.type === "lobby_update") {
    latestPhase = msg.phase;
    latestConfig = msg.config;
    renderLobby(msg.players);
    fillConfigForm(latestConfig);
    updatePhaseUI();
  } else if (msg.type === "state") {
    latestPhase = msg.phase;
    renderLobbyFromState(msg.players);
    updatePhaseUI();
    renderState(msg);
  } else if (msg.type === "invalid_move") {
    showConfigMsg(`${msg.color}: ${t("warning_toast")} (${msg.warnings}/${msg.max_warnings})`);
  } else if (msg.type === "game_over") {
    showGameOver(msg);
  } else if (msg.type === "configure_result") {
    document.getElementById("config-msg").textContent = msg.ok ? t("config_saved") : msg.error;
  } else if (msg.type === "start_result") {
    document.getElementById("start-msg").textContent = msg.ok ? "" : msg.error;
  }
}

function fillConfigForm(cfg) {
  if (!cfg) return;
  document.getElementById("cfg-move-time").value = cfg.move_time_limit_sec;
  document.getElementById("cfg-match-time").value = cfg.match_time_limit_sec;
  document.getElementById("cfg-max-warnings").value = cfg.max_warnings;
  document.getElementById("cfg-draw-moves").value = Math.round(cfg.draw_no_progress_halfmoves / 2);
}

function renderLobby(players) {
  const red = players.red;
  const black = players.black;
  document.getElementById("red-name").textContent = red ? red.name : t("empty_seat");
  document.getElementById("black-name").textContent = black ? black.name : t("empty_seat");
  document.getElementById("kick-red").classList.toggle("hidden", !red);
  document.getElementById("kick-black").classList.toggle("hidden", !black);
  document.getElementById("start-btn").disabled = !(red && black) || latestPhase !== "lobby";
  document.getElementById("start-msg").textContent = red && black ? "" : t("need_two_players");
}

function renderLobbyFromState(players) {
  renderLobby(players);
}

function updatePhaseUI() {
  const inLobby = latestPhase === "lobby";
  document.getElementById("save-config-btn").disabled = !inLobby;
  document.querySelectorAll("#config-form input").forEach((i) => (i.disabled = !inLobby));
  document.getElementById("start-btn").classList.toggle("hidden", latestPhase === "finished");
  document.getElementById("reset-btn").classList.toggle("hidden", latestPhase !== "finished");
  if (!inLobby) document.getElementById("config-msg").textContent = t("config_locked");
}

function renderState(msg) {
  if (!boardView) {
    boardView = new BoardView(document.getElementById("board"), { interactive: false });
  }
  boardView.setState(msg.board, msg.last_move, null, []);
  const players = msg.players || {};
  document.getElementById("red-warn").textContent = players.red ? players.red.warnings : 0;
  document.getElementById("black-warn").textContent = players.black ? players.black.warnings : 0;
  document.getElementById("red-clock").textContent = players.red ? fmtClock(players.red.remaining_time) : "--:--";
  document.getElementById("black-clock").textContent = players.black ? fmtClock(players.black.remaining_time) : "--:--";
  document.getElementById("turn-indicator").textContent = msg.turn
    ? `${t(msg.turn === "red" ? "seat_red" : "seat_black")}${msg.in_check ? " (" + t("in_check") + ")" : ""}`
    : "—";

  currentTurnColor = msg.turn;
  turnDeadlineMs = msg.turn_deadline_epoch_ms;
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
  restartTick();
}

function restartTick() {
  if (tickTimer) clearInterval(tickTimer);
  tickTimer = setInterval(() => {
    if (latestPhase !== "in_progress" || !turnDeadlineMs || !currentTurnColor) return;
    const remaining = (turnDeadlineMs - Date.now()) / 1000;
    const el = document.getElementById(currentTurnColor === "red" ? "red-clock" : "black-clock");
    el.textContent = fmtClock(remaining);
    el.classList.toggle("low", remaining < 10);
  }, 250);
}

function showConfigMsg(text) {
  document.getElementById("config-msg").textContent = text;
}

function showGameOver(msg) {
  const overlay = document.getElementById("gameover-overlay");
  const text = document.getElementById("gameover-text");
  const reason = t(REASON_KEY[msg.reason] || msg.reason);
  if (msg.winner) {
    text.textContent = `${t("winner_is")}: ${t(msg.winner === "red" ? "seat_red" : "seat_black")} — ${reason}`;
  } else {
    text.textContent = `${t("draw_result")} — ${reason}`;
  }
  overlay.classList.remove("hidden");
  latestPhase = "finished";
  updatePhaseUI();
}

document.addEventListener("DOMContentLoaded", () => {
  initLanguageToggle(document.getElementById("lang-select"));
  document.addEventListener("xq:langchange", () => {
    if (boardView) boardView.render();
  });

  fetch("/api/server-info")
    .then((r) => r.json())
    .then((info) => {
      const host = info.local_ip || info.requested_host || location.hostname;
      document.getElementById("connect-url").textContent = `http://${host}:${info.port}/player`;
    })
    .catch(() => {
      document.getElementById("connect-url").textContent = `${location.origin}/player`;
    });

  document.getElementById("save-config-btn").addEventListener("click", () => {
    const config = {
      move_time_limit_sec: parseInt(document.getElementById("cfg-move-time").value, 10),
      match_time_limit_sec: parseInt(document.getElementById("cfg-match-time").value, 10),
      max_warnings: parseInt(document.getElementById("cfg-max-warnings").value, 10),
      draw_no_progress_halfmoves: parseInt(document.getElementById("cfg-draw-moves").value, 10) * 2,
    };
    ws.send(JSON.stringify({ type: "configure", config }));
  });

  document.getElementById("start-btn").addEventListener("click", () => {
    ws.send(JSON.stringify({ type: "start" }));
  });

  document.getElementById("reset-btn").addEventListener("click", () => {
    document.getElementById("gameover-overlay").classList.add("hidden");
    document.getElementById("move-log").innerHTML = "";
    ws.send(JSON.stringify({ type: "reset" }));
  });

  document.getElementById("kick-red").addEventListener("click", () => ws.send(JSON.stringify({ type: "kick", color: "red" })));
  document.getElementById("kick-black").addEventListener("click", () => ws.send(JSON.stringify({ type: "kick", color: "black" })));

  document.getElementById("gameover-close").addEventListener("click", () => {
    document.getElementById("gameover-overlay").classList.add("hidden");
  });

  connect();
});
