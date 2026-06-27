"""Run a minimal BoardGame-T demo.

Usage from this directory:

    python -m omega_game.examples.boardgame_t_demo
"""

from __future__ import annotations

from omega_game.engines import BoardGameEngine, BoardPiece


def main() -> None:
    board = BoardGameEngine(width=4, height=4)
    board.add_player("player_tristan", "Tristan")
    board.add_piece(BoardPiece("piece_seed", "player_tristan", "seed", (0, 0), power=0.6))

    accepted_move = board.move_piece("piece_seed", (1, 0))
    rejected_move = board.move_piece("piece_seed", (99, 99))
    gm_proposal = board.tick_gm()

    print("Ω-GAME-T / BoardGame-T demo")
    print("=" * 40)
    print("Accepted move:", accepted_move.description)
    print("Rejected move:", rejected_move.description)
    print("Piece position:", board.pieces["piece_seed"].position)
    print("M+ entries:", len(board.gm.m_plus.entries))
    print("M- entries:", len(board.gm.m_minus.entries))
    print("GM quest:", gm_proposal.quest["quest"])
    print("GM OAK accepted:", gm_proposal.oak_report.accepted if gm_proposal.oak_report else None)


if __name__ == "__main__":
    main()
