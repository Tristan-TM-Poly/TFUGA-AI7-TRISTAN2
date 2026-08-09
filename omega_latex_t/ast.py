from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


class Latex:
    def render(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Raw(Latex):
    value: str

    def render(self) -> str:
        return self.value


@dataclass(frozen=True)
class Text(Latex):
    value: str

    def render(self) -> str:
        table = {
            "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
            "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
            "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        }
        return "".join(table.get(ch, ch) for ch in self.value)


@dataclass(frozen=True)
class Command(Latex):
    name: str
    args: tuple[Latex, ...] = ()
    options: tuple[str, ...] = ()

    def render(self) -> str:
        opt = "".join(f"[{x}]" for x in self.options)
        args = "".join("{" + x.render() + "}" for x in self.args)
        return f"\\{self.name}{opt}{args}"


@dataclass(frozen=True)
class Environment(Latex):
    name: str
    body: tuple[Latex, ...] = ()
    options: tuple[str, ...] = ()

    def render(self) -> str:
        opt = "".join(f"[{x}]" for x in self.options)
        inner = "\n".join(x.render() for x in self.body)
        return f"\\begin{{{self.name}}}{opt}\n{inner}\n\\end{{{self.name}}}"


@dataclass(frozen=True)
class Sequence(Latex):
    items: tuple[Latex, ...] = field(default_factory=tuple)

    @classmethod
    def of(cls, items: Iterable[Latex]) -> "Sequence":
        return cls(tuple(items))

    def render(self) -> str:
        return "\n".join(item.render() for item in self.items)
