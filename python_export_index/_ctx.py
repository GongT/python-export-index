from typing import TypedDict


class SymbolDef(TypedDict):
    file: str
    name: str


class Context:
    active = False
    exports: list[SymbolDef] = []


ctx = Context()
