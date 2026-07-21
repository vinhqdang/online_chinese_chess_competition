const STRINGS = {
  en: {
    app_title: "Online Xiangqi Competition Server",
    subtitle: "Chinese Chess referee server — the server is the sole judge.",
    choose_role: "Choose your role",
    role_admin: "Admin (organize match)",
    role_player: "Player (competitor)",
    language: "Language",
    admin_title: "Admin Dashboard",
    connect_info: "Share this address with competitors so they can connect:",
    player_url_label: "Player connect URL",
    lan_note: "Works over LAN or the internet, as long as this address/port is reachable from the client.",
    lobby: "Lobby",
    seat_red: "Red",
    seat_black: "Black",
    empty_seat: "— waiting for a player to connect —",
    kick: "Kick",
    configure: "Match configuration",
    move_time_limit: "Time limit per move (seconds)",
    match_time_limit: "Time limit per match, per player (seconds)",
    max_warnings: "Illegal-move warnings before automatic loss",
    draw_moves: "Draw after N moves each with no capture/check",
    save_config: "Save configuration",
    config_saved: "Configuration saved.",
    config_locked: "Configuration is locked once the match has started.",
    start_game: "Start Match",
    need_two_players: "Waiting for both Red and Black to connect before you can start.",
    reset_button: "New Match",
    spectate_title: "Live match",
    move_log: "Move log",
    warnings_label: "Warnings",
    move_clock: "Move clock",
    match_clock: "Match clock",
    in_check: "in check",
    turn_label: "To move",
    game_over: "Game Over",
    winner_is: "Winner",
    draw_result: "Draw",
    none: "—",
    reason_checkmate: "Checkmate",
    reason_no_legal_moves: "No legal moves available (loss under Xiangqi rules)",
    reason_warnings_exceeded: "Too many illegal-move warnings",
    reason_move_time_exceeded: "Move time limit exceeded",
    reason_match_time_exceeded: "Match time limit exceeded",
    reason_disconnect: "Opponent disconnected",
    reason_resign: "Resignation",
    reason_kicked: "Player was kicked by the admin",
    reason_draw_no_progress: "Draw — no capture or check in the required number of moves",
    reason_threefold_repetition: "Draw — the same position occurred three times",
    player_title: "Player",
    enter_name: "Your name",
    join_button: "Join match",
    waiting_room: "Waiting room",
    waiting_for_opponent: "Waiting for the admin to start the match…",
    players_connected: "Players connected",
    you_are: "You are playing",
    your_turn: "Your turn — select a piece to move",
    opponent_turn: "Waiting for opponent's move…",
    resign_button: "Resign",
    confirm_resign: "Are you sure you want to resign?",
    warning_toast: "Illegal move",
    kicked_message: "You have been removed from the match by the admin.",
    connection_lost: "Connection to server lost.",
    lobby_full: "The lobby is already full.",
    game_in_progress: "A match is already in progress.",
    game_finished: "The previous match has finished — waiting for the admin to start a new one.",
    back_home: "Back",
  },
  vi: {
    app_title: "Máy Chủ Thi Đấu Cờ Tướng Trực Tuyến",
    subtitle: "Máy chủ trọng tài Cờ Tướng — máy chủ là trọng tài duy nhất.",
    choose_role: "Chọn vai trò của bạn",
    role_admin: "Quản trị viên (tổ chức trận đấu)",
    role_player: "Người chơi (thí sinh)",
    language: "Ngôn ngữ",
    admin_title: "Bảng Điều Khiển Quản Trị",
    connect_info: "Chia sẻ địa chỉ này cho các kỳ thủ để họ kết nối:",
    player_url_label: "Địa chỉ kết nối cho người chơi",
    lan_note: "Hoạt động qua mạng LAN hoặc Internet, miễn là địa chỉ/cổng này có thể truy cập được từ máy khách.",
    lobby: "Phòng chờ",
    seat_red: "Bên Đỏ",
    seat_black: "Bên Đen",
    empty_seat: "— đang chờ người chơi kết nối —",
    kick: "Loại",
    configure: "Cấu hình trận đấu",
    move_time_limit: "Giới hạn thời gian mỗi nước đi (giây)",
    match_time_limit: "Giới hạn thời gian cả trận, mỗi người chơi (giây)",
    max_warnings: "Số lần cảnh báo nước đi phạm luật trước khi xử thua",
    draw_moves: "Hòa sau N nước mỗi bên không ăn quân/không chiếu tướng",
    save_config: "Lưu cấu hình",
    config_saved: "Đã lưu cấu hình.",
    config_locked: "Cấu hình bị khóa sau khi trận đấu đã bắt đầu.",
    start_game: "Bắt Đầu Trận Đấu",
    need_two_players: "Đang chờ cả hai bên Đỏ và Đen kết nối trước khi bắt đầu.",
    reset_button: "Trận Mới",
    spectate_title: "Trận đấu trực tiếp",
    move_log: "Lịch sử nước đi",
    warnings_label: "Cảnh báo",
    move_clock: "Đồng hồ nước đi",
    match_clock: "Đồng hồ trận đấu",
    in_check: "đang bị chiếu",
    turn_label: "Đến lượt",
    game_over: "Kết Thúc Trận Đấu",
    winner_is: "Người thắng",
    draw_result: "Hòa",
    none: "—",
    reason_checkmate: "Chiếu bí",
    reason_no_legal_moves: "Không còn nước đi hợp lệ (thua theo luật Cờ Tướng)",
    reason_warnings_exceeded: "Quá số lần cảnh báo nước đi phạm luật",
    reason_move_time_exceeded: "Hết giờ cho nước đi",
    reason_match_time_exceeded: "Hết giờ toàn trận đấu",
    reason_disconnect: "Đối thủ đã mất kết nối",
    reason_resign: "Đầu hàng",
    reason_kicked: "Người chơi đã bị quản trị viên loại",
    reason_draw_no_progress: "Hòa — không ăn quân hoặc chiếu tướng trong số nước quy định",
    reason_threefold_repetition: "Hòa — cùng một thế cờ lặp lại ba lần",
    player_title: "Người Chơi",
    enter_name: "Tên của bạn",
    join_button: "Tham gia trận đấu",
    waiting_room: "Phòng chờ",
    waiting_for_opponent: "Đang chờ quản trị viên bắt đầu trận đấu…",
    players_connected: "Người chơi đã kết nối",
    you_are: "Bạn đang chơi bên",
    your_turn: "Đến lượt bạn — chọn quân để đi",
    opponent_turn: "Đang chờ đối thủ đi…",
    resign_button: "Đầu Hàng",
    confirm_resign: "Bạn có chắc muốn đầu hàng không?",
    warning_toast: "Nước đi không hợp lệ",
    kicked_message: "Bạn đã bị quản trị viên loại khỏi trận đấu.",
    connection_lost: "Mất kết nối với máy chủ.",
    lobby_full: "Phòng chờ đã đủ người.",
    game_in_progress: "Trận đấu đang diễn ra.",
    game_finished: "Trận trước đã kết thúc — đang chờ quản trị viên bắt đầu trận mới.",
    back_home: "Quay lại",
  },
};

// Traditional Xiangqi piece characters -- Red and Black use different
// characters for the same piece type (this is standard, not a language
// choice), so these are shown regardless of the EN/VI UI language.
const PIECE_GLYPHS = {
  r: { G: "帥", A: "仕", E: "相", H: "傌", R: "俥", C: "炮", P: "兵" },
  b: { G: "將", A: "士", E: "象", H: "馬", R: "車", C: "砲", P: "卒" },
};

function getLang() {
  return localStorage.getItem("xq_lang") || "en";
}

function setLang(lang) {
  localStorage.setItem("xq_lang", lang);
}

function t(key) {
  const lang = getLang();
  return (STRINGS[lang] && STRINGS[lang][key]) || STRINGS.en[key] || key;
}

function pieceLabel(color, kind) {
  return (PIECE_GLYPHS[color] && PIECE_GLYPHS[color][kind]) || kind;
}

function applyTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")));
  });
}

function initLanguageToggle(selectEl) {
  selectEl.value = getLang();
  applyTranslations();
  selectEl.addEventListener("change", () => {
    setLang(selectEl.value);
    applyTranslations();
    document.dispatchEvent(new CustomEvent("xq:langchange"));
  });
}
