"""Small sizing helper."""


def size_mode(lines: int) -> str:
    if lines <= 120:
        return "small"
    return "split"
