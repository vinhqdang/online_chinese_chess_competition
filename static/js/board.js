const BOARD_FILES = 9;
const BOARD_RANKS = 10;

class BoardView {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.flip = !!options.flip;
    this.margin = 40;
    this.matrix = null;
    this.selected = null;
    this.targets = [];
    this.lastMove = null;
    this.onSquareClick = options.onSquareClick || null;
    this.interactive = options.interactive !== false;
    canvas.addEventListener("click", (ev) => this._handleClick(ev));
    this._resize();
    window.addEventListener("resize", () => this._resize());
  }

  _resize() {
    const size = Math.min(this.canvas.parentElement.clientWidth, 560);
    this.canvas.width = size;
    this.canvas.height = Math.round((size * (BOARD_RANKS - 1)) / (BOARD_FILES - 1));
    this.render();
  }

  setFlip(flip) {
    this.flip = flip;
    this.render();
  }

  setState(matrix, lastMove, selected, targets) {
    this.matrix = matrix;
    this.lastMove = lastMove || null;
    this.selected = selected || null;
    this.targets = targets || [];
    this.render();
  }

  _cellSize() {
    return (this.canvas.width - 2 * this.margin) / (BOARD_FILES - 1);
  }

  _toScreen(file, rank) {
    const displayFile = this.flip ? BOARD_FILES - 1 - file : file;
    const displayRank = this.flip ? rank : BOARD_RANKS - 1 - rank;
    const cell = this._cellSize();
    return {
      x: this.margin + displayFile * cell,
      y: this.margin + displayRank * cell,
    };
  }

  _toBoard(px, py) {
    const cell = this._cellSize();
    const displayFile = Math.round((px - this.margin) / cell);
    const displayRank = Math.round((py - this.margin) / cell);
    if (displayFile < 0 || displayFile > 8 || displayRank < 0 || displayRank > 9) return null;
    const file = this.flip ? BOARD_FILES - 1 - displayFile : displayFile;
    const rank = this.flip ? displayRank : BOARD_RANKS - 1 - displayRank;
    return [file, rank];
  }

  _handleClick(ev) {
    if (!this.interactive || !this.onSquareClick) return;
    const rect = this.canvas.getBoundingClientRect();
    const px = (ev.clientX - rect.left) * (this.canvas.width / rect.width);
    const py = (ev.clientY - rect.top) * (this.canvas.height / rect.height);
    const square = this._toBoard(px, py);
    if (square) this.onSquareClick(square);
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#e8c992";
    ctx.fillRect(0, 0, w, h);

    ctx.strokeStyle = "#5b3a1e";
    ctx.lineWidth = 1.4;

    for (let file = 0; file < BOARD_FILES; file++) {
      const top = this._toScreen(file, 9);
      const bottom = this._toScreen(file, 0);
      if (file === 0 || file === 8) {
        ctx.beginPath();
        ctx.moveTo(top.x, top.y);
        ctx.lineTo(bottom.x, bottom.y);
        ctx.stroke();
      } else {
        const riverTopRank = this.flip ? 4 : 5;
        const riverBottomRank = this.flip ? 5 : 4;
        const a = this._toScreen(file, this.flip ? 9 : 9);
        const riverA = this._toScreen(file, riverTopRank);
        const riverB = this._toScreen(file, riverBottomRank);
        ctx.beginPath();
        ctx.moveTo(top.x, top.y);
        ctx.lineTo(riverA.x, riverA.y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(riverB.x, riverB.y);
        ctx.lineTo(bottom.x, bottom.y);
        ctx.stroke();
      }
    }
    for (let rank = 0; rank < BOARD_RANKS; rank++) {
      const left = this._toScreen(0, rank);
      const right = this._toScreen(8, rank);
      ctx.beginPath();
      ctx.moveTo(left.x, left.y);
      ctx.lineTo(right.x, right.y);
      ctx.stroke();
    }

    this._drawPalaceCross(3, 0, 2);
    this._drawPalaceCross(3, 7, 9);

    ctx.fillStyle = "#5b3a1e";
    ctx.font = `${Math.round(this._cellSize() * 0.4)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const riverMid = this._toScreen(4, this.flip ? 4.5 : 4.5);
    const riverText = getLang() === "vi" ? "SÔNG" : "RIVER";
    ctx.fillText(riverText, riverMid.x, riverMid.y);

    if (this.matrix) {
      for (let rank = 0; rank < BOARD_RANKS; rank++) {
        for (let file = 0; file < BOARD_FILES; file++) {
          const cell = this.matrix[rank][file];
          if (cell) this._drawPiece(file, rank, cell);
        }
      }
    }

    if (this.lastMove) {
      this._highlightSquare(this.lastMove.from, "rgba(30,120,220,0.55)");
      this._highlightSquare(this.lastMove.to, "rgba(30,120,220,0.55)");
    }
    if (this.selected) {
      this._highlightSquare(this.selected, "rgba(20,160,60,0.7)");
    }
    for (const target of this.targets) {
      const p = this._toScreen(target[0], target[1]);
      ctx.beginPath();
      ctx.arc(p.x, p.y, this._cellSize() * 0.16, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(20,160,60,0.65)";
      ctx.fill();
    }
  }

  _drawPalaceCross(centerFile, r1, r2) {
    const ctx = this.ctx;
    const corners = [
      this._toScreen(centerFile - 1, r1),
      this._toScreen(centerFile + 1, r1),
      this._toScreen(centerFile - 1, r2),
      this._toScreen(centerFile + 1, r2),
    ];
    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    ctx.lineTo(corners[3].x, corners[3].y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(corners[1].x, corners[1].y);
    ctx.lineTo(corners[2].x, corners[2].y);
    ctx.stroke();
  }

  _highlightSquare(square, color) {
    const p = this._toScreen(square[0], square[1]);
    const ctx = this.ctx;
    const r = this._cellSize() * 0.42;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.stroke();
  }

  _drawPiece(file, rank, piece) {
    const ctx = this.ctx;
    const p = this._toScreen(file, rank);
    const r = this._cellSize() * 0.42;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fillStyle = "#f6e6c8";
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = piece.color === "r" ? "#b32020" : "#1a1a1a";
    ctx.stroke();
    ctx.fillStyle = piece.color === "r" ? "#b32020" : "#1a1a1a";
    ctx.font = `bold ${Math.round(r * 0.85)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(pieceLabel(piece.type), p.x, p.y);
  }
}
