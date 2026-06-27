from omega_game.engines import BoardGameEngine, BoardPiece


def test_boardgame_accepts_inside_move_and_records_positive_memory():
    board = BoardGameEngine(width=3, height=3)
    board.add_player("p1", "Player")
    board.add_piece(BoardPiece("seed", "p1", "seed", (0, 0)))

    board.move_piece("seed", (1, 0))

    assert board.pieces["seed"].position == (1, 0)
    assert board.world.memory[-1]["type"] == "board_move"
    assert board.gm.m_plus.entries


def test_boardgame_rejects_outside_move_and_records_negative_memory():
    board = BoardGameEngine(width=3, height=3)
    board.add_player("p1", "Player")
    board.add_piece(BoardPiece("seed", "p1", "seed", (0, 0)))

    board.move_piece("seed", (9, 9))

    assert board.pieces["seed"].position == (0, 0)
    assert board.gm.m_minus.entries
    assert "outside board" in str(board.gm.m_minus.last())


def test_boardgame_legal_neighbors_respect_edges():
    board = BoardGameEngine(width=2, height=2)

    assert sorted(board.legal_neighbors((0, 0))) == [(0, 1), (1, 0)]
    assert sorted(board.legal_neighbors((1, 1))) == [(0, 1), (1, 0)]


def test_boardgame_gm_tick_generates_valid_oak_quest():
    board = BoardGameEngine(width=3, height=3)
    board.add_player("p1", "Player")
    board.add_piece(BoardPiece("seed", "p1", "seed", (0, 0)))

    proposal = board.tick_gm()

    assert proposal.oak_report is not None
    assert proposal.oak_report.accepted
    assert proposal.quest["objective"]
