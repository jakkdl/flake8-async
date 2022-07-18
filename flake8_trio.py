"""A highly opinionated flake8 plugin for Trio-related problems.

This can include anything from outright bugs, to pointless/dead code,
to likely performance issues, to minor points of idiom that might signal
a misunderstanding.

It may well be too noisy for anyone with different opinions, that's OK.

Pairs well with flake8-async and flake8-bugbear.
"""

import ast
from typing import Any, Generator, List, Optional, Tuple, Type

# CalVer: YY.month.patch, e.g. first release of July 2022 == "22.7.1"
__version__ = "22.7.1"


def is_trio_call(node: ast.AST, *names: str) -> Optional[str]:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "trio"
        and node.func.attr in names
    ):
        return "trio." + node.func.attr
    return None


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.problems: List[Error] = []

    def visit_With(self, node: ast.With) -> None:
        # Context manager with no `await` call within
        for item in (i.context_expr for i in node.items):
            call = is_trio_call(item, "fail_after", "move_on_after")
            if call and not any(isinstance(x, ast.Await) for x in ast.walk(node)):
                self.problems.append(TRIO100(item.lineno, item.col_offset, call))

        # Don't forget to visit the child nodes for other errors!
        self.generic_visit(node)


class Plugin:
    name = __name__
    version = __version__

    def __init__(
        self, tree: Optional[ast.AST] = None, filename: Optional[str] = None
    ) -> None:
        if tree is not None:
            self._tree = tree
            return
        assert filename is not None
        with open(filename, encoding="utf-8") as file:
            self._tree = ast.parse(file.read())

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = Visitor()
        visitor.visit(self._tree)
        for problem in visitor.problems:
            yield problem.flake_yield()


class Error:
    def __init__(self, lineno: int = -1, col: int = -1, message: str = ""):
        self.lineno = lineno
        self.col = col
        self.message = message
        self.err_type = type(Plugin)

    def flake_yield(self):
        return (self.lineno, self.col, self.message, self.err_type)


class TRIO100(Error):
    def __init__(self, lineno: int, col: int, context: str):
        super().__init__(
            lineno,
            col,
            f"TRIO100: {context} context contains no checkpoints, "
            "add `await trio.sleep(0)`",
        )
