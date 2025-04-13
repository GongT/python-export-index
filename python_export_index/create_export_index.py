import importlib
import re
import sys
from pathlib import Path
from typing import Callable

from . import my_name
from ._ctx import ctx

GEN_MARK = "08b6691a-40b9-4b6a-9bb1-34ff0acc281b"
GEN_WARNING = (
    "# 这个文件是自动生成的，不要手动修改任何内容！！\n##### " + GEN_MARK + " #####\n"
)


def write_file_if_change(f: Path, content: str, dprint: Callable):
    """
    写入文件，如果内容没有变化则不写入
    :param file: 文件路径
    :param content: 文件内容
    """
    if f.exists():
        current: str = f.read_text()
        if current == content:
            dprint("[loader] 文件没有改变:", f.as_posix())
            return
        if current and GEN_MARK not in current:
            raise ValueError(
                "将会覆盖非自动生成的文件，请检查是否正确，如果确实需要，则可删除该文件"
            )

    dprint("[loader] 更新index文件:", f.as_posix())
    f.write_text(content)


def debug_tools(debug: bool):
    if debug:

        def dprint(
            *args,
        ):
            print(*args, file=sys.stderr)

        def dappend(lines: list[str], line: str):
            lines.append(line)

        return (dprint, dappend)
    else:

        def noop(*args, **kwargs):
            pass

        return (noop, noop)


def create_exports(base: Path, dir: str, index: str = "__init__.py", debug=False):
    output_file = base.joinpath(index)
    scan_dir = base.joinpath(dir)
    all_symbols = {}
    empty_files = []

    (dprint, dappend) = debug_tools(debug)

    topic_file = output_file
    is_init = output_file.name == "__init__.py"
    if is_init and output_file.exists():
        topic_file = output_file.with_name(name=f"{output_file.stem}.bak")
        topic_file.unlink(True)
        dprint("move __init__.py to backup")
        output_file.rename(topic_file)
        output_file = output_file.with_name(name=f"{output_file.stem}.py")
        output_file.touch()

    for path in scan_dir.rglob("*.py"):
        if not path.is_file() or path.name.startswith("_") or path.name.startswith("."):
            continue

        dprint("==== process file:", path)

        mdl_name = (
            path.relative_to(base).as_posix().replace("/", ".").replace("\\", ".")
        )
        mdl_name = f".{mdl_name[:-3]}"

        dprint(f" import {mdl_name} [as {base.stem}]")
        ctx.active = True
        ctx.exports.clear()

        mdl = importlib.import_module(mdl_name, base.stem)

        all = getattr(mdl, "__all__", None)
        dprint(f"  __all__ = {all}")
        if all is None:
            patch_file(path)
            all = []
        elif len(all):
            for i in all:
                all_symbols[i] = path

        for symbol in ctx.exports:
            sym_name = symbol["name"]
            file = Path(symbol["file"])
            if sym_name in all_symbols and all_symbols[sym_name] != file:
                print(f"Found duplicate symbol '{sym_name}' in", file=sys.stderr)
                print(f"    * previous: {all_symbols[sym_name]}", file=sys.stderr)
                print(f"    * current:  {file}", file=sys.stderr)
                raise TypeError("duplicate symbol")

            all_symbols[sym_name] = file
            dprint(f"  * {sym_name}")

        if not len(ctx.exports) and not len(all):
            empty_files.append(path)
            dprint(f"  * empty file: {path.relative_to(base)}")

        ctx.active = False
        ctx.exports.clear()

    # pprint.pprint(all_symbols)

    import_stmts = []
    for name, path in all_symbols.items():
        p = create_from_clause(output_file, path)
        import_stmts.append(f"from {p} import {name}")

    for path in empty_files:
        p = create_from_clause(output_file, path)
        import_stmts.append(f"from {p} import __all__ as _a")
        import_stmts.append(f"del _a")
    dappend(import_stmts, f"print('all files loaded!!')")

    pycode = [GEN_WARNING]
    dappend(pycode, "import traceback")
    dappend(pycode, 'print(f"[index] I\'m imported with name \\"{__name__}\\"")')
    dappend(pycode, "for line in traceback.format_stack():")
    dappend(pycode, "  if line.startswith('  File \"/') and 'site-packages' not in line and '/importlib/' not in line: print(line.rstrip())")
    dappend(pycode, "  else: continue")

    pycode.extend(import_stmts)
    pycode.append("__all__ = [")
    for i in all_symbols.keys():
        pycode.append(f"  '{i}',")
    pycode.append("]")

    write_file_if_change(topic_file, "\n".join(pycode), dprint=dprint)
    if is_init:
        topic_file.rename(output_file)

    # 重新加载模块
    out_mdl_name = create_from_clause(base.joinpath("fake.py"), output_file)
    dprint("reload module:", out_mdl_name)
    if out_mdl_name.endswith(".__init__"):
        out_mdl_name = out_mdl_name[:-9]
        if out_mdl_name == "":
            out_mdl_name = "."
    mdl = importlib.import_module(out_mdl_name, base.stem)
    importlib.reload(mdl)


def create_from_clause(source: Path, imported: Path):
    return "." + (
        imported.relative_to(source.parent)
        .as_posix()
        .replace("/", ".")
        .replace("\\", ".")[:-3]
    )


def wrap_try_catch(content: list[str], dappend: Callable):
    lines = ["try:"]
    for line in content:
        lines.append(re.sub(r"^", "  ", line, flags=re.MULTILINE))
    lines.append("except ImportError as e:")
    dappend(lines, f"  print('error during try load:',e)")
    lines.append(f"  try:")
    lines.append(f"    from {my_name}._ctx import ctx")
    lines.append(f"    if not ctx.active: raise e")
    lines.append(f"  except ImportError as ee:")
    dappend(lines, f"    print('error during load this library:',ee)")
    lines.append(f"    pass")
    return lines


def patch_file(path: Path):
    content = path.read_text()
    content = "__all__ = []\n" + content
    path.write_text(content)
    print(f"  * patch {path.relative_to(path.parent.parent)}")
