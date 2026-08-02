"""Bounded context-free grammar tools with finite generation and CYK parsing.

The grammar is an observed compatibility model.  Acceptance on a bounded corpus
is not proof of the original parser or language implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Mapping, Sequence

Symbol = str
Production = tuple[Symbol, ...]


@dataclass(frozen=True)
class ParseResult:
    accepted: bool
    token_count: int
    chart_cells: int
    witnesses: tuple[str, ...]
    claim: str = "bounded_cfg_compatibility_only"


class BoundedCFG:
    """Small Chomsky-normal-form grammar with optional terminal unit rules."""

    def __init__(
        self,
        *,
        start: Symbol,
        terminal_rules: Mapping[Symbol, Iterable[Symbol]],
        binary_rules: Mapping[Symbol, Iterable[tuple[Symbol, Symbol]]],
    ) -> None:
        self.start = start
        self.terminal_rules = {
            left: tuple(dict.fromkeys(str(token) for token in tokens))
            for left, tokens in terminal_rules.items()
        }
        self.binary_rules = {
            left: tuple(dict.fromkeys((str(a), str(b)) for a, b in pairs))
            for left, pairs in binary_rules.items()
        }
        if start not in set(self.terminal_rules) | set(self.binary_rules):
            raise ValueError("start symbol must have a rule")
        if any(not tokens for tokens in self.terminal_rules.values()):
            raise ValueError("terminal rule sets cannot be empty")
        if any(not pairs for pairs in self.binary_rules.values()):
            raise ValueError("binary rule sets cannot be empty")
        self._terminal_index: dict[str, set[str]] = {}
        self._binary_index: dict[tuple[str, str], set[str]] = {}
        for left, tokens in self.terminal_rules.items():
            for token in tokens:
                self._terminal_index.setdefault(token, set()).add(left)
        for left, pairs in self.binary_rules.items():
            for pair in pairs:
                self._binary_index.setdefault(pair, set()).add(left)

    def parse(self, tokens: Sequence[str], *, max_tokens: int = 64) -> ParseResult:
        items = tuple(str(token) for token in tokens)
        if len(items) > max_tokens:
            raise ValueError("token budget exceeded")
        if not items:
            return ParseResult(False, 0, 0, ())
        n = len(items)
        chart: list[list[set[str]]] = [[set() for _ in range(n)] for _ in range(n)]
        witness: dict[tuple[int, int, str], str] = {}
        for index, token in enumerate(items):
            for nonterminal in self._terminal_index.get(token, ()):
                chart[index][index].add(nonterminal)
                witness[(index, index, nonterminal)] = f"{nonterminal}->{token}"
        for span in range(2, n + 1):
            for start in range(0, n - span + 1):
                end = start + span - 1
                for split in range(start, end):
                    for left_symbol in sorted(chart[start][split]):
                        for right_symbol in sorted(chart[split + 1][end]):
                            for parent in self._binary_index.get((left_symbol, right_symbol), ()):
                                chart[start][end].add(parent)
                                witness[(start, end, parent)] = (
                                    f"{parent}->{left_symbol} {right_symbol}@{split}"
                                )
        accepted = self.start in chart[0][n - 1]
        witnesses = tuple(
            witness[key]
            for key in sorted(witness)
            if key[2] == self.start or (key[0] == key[1] and len(witness) <= 32)
        )
        return ParseResult(
            accepted=accepted,
            token_count=n,
            chart_cells=n * (n + 1) // 2,
            witnesses=witnesses[:64],
        )

    def generate(self, *, max_tokens: int = 8, max_sentences: int = 256) -> tuple[tuple[str, ...], ...]:
        if max_tokens <= 0 or max_sentences <= 0:
            raise ValueError("budgets must be positive")
        memo: dict[tuple[str, int], set[tuple[str, ...]]] = {}

        def expand(symbol: str, budget: int) -> set[tuple[str, ...]]:
            key = (symbol, budget)
            if key in memo:
                return memo[key]
            result: set[tuple[str, ...]] = set()
            for terminal in self.terminal_rules.get(symbol, ()):
                if budget >= 1:
                    result.add((terminal,))
            for left, right in self.binary_rules.get(symbol, ()):
                for left_budget in range(1, budget):
                    right_budget = budget - left_budget
                    for first, second in product(expand(left, left_budget), expand(right, right_budget)):
                        sentence = first + second
                        if len(sentence) <= budget:
                            result.add(sentence)
                            if len(result) >= max_sentences:
                                memo[key] = result
                                return result
            memo[key] = result
            return result

        generated: set[tuple[str, ...]] = set()
        for budget in range(1, max_tokens + 1):
            generated.update(expand(self.start, budget))
            if len(generated) >= max_sentences:
                break
        return tuple(sorted(generated, key=lambda item: (len(item), item))[:max_sentences])


def propose_terminal_extensions(
    grammar: BoundedCFG,
    accepted_examples: Iterable[Sequence[str]],
    rejected_examples: Iterable[Sequence[str]],
) -> tuple[tuple[str, str], ...]:
    """Conservatively propose unknown terminals without mutating the grammar."""
    known = set(grammar._terminal_index)
    accepted_unknown = {
        token for example in accepted_examples for token in example if token not in known
    }
    rejected_unknown = {
        token for example in rejected_examples for token in example if token not in known
    }
    safe = sorted(accepted_unknown - rejected_unknown)
    lexical_symbols = sorted(grammar.terminal_rules)
    target = lexical_symbols[0] if lexical_symbols else grammar.start
    return tuple((target, token) for token in safe)
