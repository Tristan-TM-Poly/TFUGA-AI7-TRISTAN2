"""BoardGame-T: grid/board engine for Ω-GAME-T.

This module is intentionally generic: it can support chess-like experiments,
roguelike prototypes, pathfinding labs, tactical puzzles, and AIT-ChessMaster
benchmarks without encoding one specific game.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from ..core import Entity, Event, RuleKernel, WorldGraph
from ..gm import GameMasterAgent, GMProposal

Position = tuple[int, int]


@dataclass(slots=True)
class BoardPiece:
    piece_id: str
    owner: str
    kind: str
    position: Position
    power: float = 0.5


@dataclass(slots=True)
class BoardGameEngine:
    """Minimal grid/plateau engine with OAK validation hooks."""

    width: int
    height: int
    world: WorldGraph = field(default_factory=WorldGraph)
    gm: GameMasterAgent = field(default_factory=GameMasterAgent)
    rule_kernel: RuleKernel = field(default_factory=RuleKernel)
    pieces: dict[str, BoardPiece] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Board dimensions must be positive.")
        self.rule_kernel.add_rule(self._move_stays_inside_board_rule)

    def add_player(self, player_id: str, name: str) -> None:
        if player_id not in self.world.entities:
            self.world.add_entity(Entity(player_id, "player", name, {"power": 0.5}))

    def add_piece(self, piece: BoardPiece) -> None:
        self._require_inside(piece.position)
        if piece.piece_id in self.pieces:
            raise ValueError(f"Piece already exists: {piece.piece_id}")
        self.pieces[piece.piece_id] = piece
        self.world.add_entity(
            Entity(
                entity_id=piece.piece_id,
                kind="piece",
                name=f"{piece.owner}:{piece.kind}",
                attributes={"owner": piece.owner, "kind": piece.kind, "power": piece.power},
            )
        )
        if piece.owner in self.world.entities:
            self.world.add_relation(piece.owner, "controls", piece.piece_id)

    def legal_neighbors(self, position: Position) -> list[Position]:
        x, y = position
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [candidate for candidate in candidates if self.inside(candidate)]

    def move_piece(self, piece_id: str, destination: Position) -> Event:
        if piece_id not in self.pieces:
            raise KeyError(f"Unknown piece: {piece_id}")
        piece = self.pieces[piece_id]
        event = Event(
            event_id=f"move_{piece_id}_{destination[0]}_{destination[1]}",
            kind="move",
            description=f"Move {piece_id} to {destination}",
            actors=[piece.owner] if piece.owner in self.world.entities else [],
            targets=[piece_id],
            payload={
                "piece_id": piece_id,
                "from": list(piece.position),
                "to": list(destination),
                "fair": True,
                "fun": True,
                "agency": 1.0,
                "metric": "legal_move_and_board_control_delta",
                "expected_signal": "piece changes board position",
                "risk_flags": [],
            },
        )
        report = self.gm.oak_gate.validate(self.world, event, self.rule_kernel)
        if not report.accepted:
            self.gm.m_minus.record("rejected_board_move", {"event": event.description, "reasons": report.reasons})
            return event

        piece.position = destination
        self.world.remember(
            {
                "type": "board_move",
                "piece_id": piece_id,
                "from": event.payload["from"],
                "to": event.payload["to"],
                "oak": report.metrics,
            }
        )
        self.gm.m_plus.record("accepted_board_move", {"piece_id": piece_id, "to": destination})
        return event

    def tick_gm(self) -> GMProposal:
        return self.gm.step(self.world, self.rule_kernel)

    def occupied_positions(self) -> dict[Position, str]:
        return {piece.position: piece_id for piece_id, piece in self.pieces.items()}

    def cells(self) -> Iterator[Position]:
        for y in range(self.height):
            for x in range(self.width):
                yield (x, y)

    def inside(self, position: Position) -> bool:
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def _require_inside(self, position: Position) -> None:
        if not self.inside(position):
            raise ValueError(f"Position outside board: {position}")

    def _move_stays_inside_board_rule(self, _world: WorldGraph, event: Event) -> tuple[bool, str]:
        if event.kind != "move":
            return True, "not a move"
        raw_destination = event.payload.get("to")
        if not isinstance(raw_destination, list | tuple) or len(raw_destination) != 2:
            return False, "move destination is invalid"
        destination = (int(raw_destination[0]), int(raw_destination[1]))
        if not self.inside(destination):
            return False, "move destination outside board"
        return True, "move stays inside board"


__all__ = ["BoardGameEngine", "BoardPiece", "Position"]
