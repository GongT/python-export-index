import importlib
import re
import sys
from pathlib import Path

from . import my_name
from ._ctx import ctx

GEN_MARK = "08b6691a-40b9-4b6a-9bb1-34ff0acc281b"
GEN_WARNING = (
    "# 这个文件是自动生成的，不要手动修改任何内容！！\n##### " + GEN_MARK + " #####\n"
)


def write_file_if_change(f: Path, content: str):
    """
    写入文件，如果内容没有变化则不写入
    :param file: 文件路径
    :param content: 文件内容
    """
    if f.exists():
        current: str = f.read_text()
        if current == content:
            # print("[loader] 文件没有改变:", f.as_posix())
            return
        if current and GEN_MARK not in current:
            raise ValueError(
                "将会覆盖非自动生成的文件，请检查是否正确，如果确实需要，则可删除该文件"
            )

    print("[loader] 更新index文件:", f.as_posix(), file=sys.stderr)
    f.write_text(content)


def create_exports(base: Path, dir: str, index: str = "__init__.py"):
    output_file = base.joinpath(index)
    scan_dir = base.joinpath(dir)
    all_symbols = {}
    empty_files = []

    for path in scan_dir.rglob("*.py"):
        if not path.is_file() or path.name.startswith("_") or path.name.startswith("."):
            continue

        # print("==== path", path)

        out_mdl_name = (
            path.relative_to(base).as_posix().replace("/", ".").replace("\\", ".")
        )
        out_mdl_name = f".{out_mdl_name[:-3]}"

        # print(f" import {name} [as {base.stem}]")
        ctx.active = True
        ctx.exports.clear()

        mdl = importlib.import_module(out_mdl_name, base.stem)

        all = getattr(mdl, "__all__", None)
        # print(f"  __all__ = {all}")
        if all is None:
            patch_file(path)
            all = []
        elif len(all):
            for i in all:
                all_symbols[i] = path

        for symbol in ctx.exports:
            out_mdl_name = symbol["name"]
            file = Path(symbol["file"])
            if out_mdl_name in all_symbols and all_symbols[out_mdl_name] != file:
                print(f"Found duplicate symbol '{out_mdl_name}' in", file=sys.stderr)
                print(f"    * previous: {all_symbols[out_mdl_name]}", file=sys.stderr)
                print(f"    * current:  {file}", file=sys.stderr)
                raise TypeError("duplicate symbol")

            all_symbols[out_mdl_name] = file
            # print(f"  * {name}")

        if not len(ctx.exports) and not len(all):
            empty_files.append(path)
            # print(f"  * empty file: {path.relative_to(base)}")

        ctx.active = False
        ctx.exports.clear()

    # pprint.pprint(all_symbols)

    import_stmts = ""
    for out_mdl_name, path in all_symbols.items():
        p = create_from_clause(output_file, path)
        import_stmts += f"  from {p} import {out_mdl_name}\n"

    for path in empty_files:
        p = create_from_clause(output_file, path)
        import_stmts += f"  from {p} import __all__ as _a\n  del _a\n"

    # pycode += f"  print('all files loaded!!')\n"

    pycode = [GEN_WARNING]
    # pycode.append("import traceback")
    # pycode.append('print(f"IM Imported with {__name__}")')
    # pycode.append("for line in traceback.format_stack():")
    # pycode.append("""  if line.startswith('  File "/'): print(line.rstrip())""")
    # pycode.append("""  else: break""")

    if output_file.name == "__init__.py":
        import_stmts = wrap_try_catch(import_stmts)

    pycode.append(import_stmts)
    pycode.append("__all__ = [")
    for i in all_symbols.keys():
        pycode.append(f"  '{i}',")
    pycode.append("]")

    write_file_if_change(output_file, "\n".join(pycode))

    out_mdl_name = create_from_clause(base.joinpath("fake.py"), output_file)
    # print("reload module:", name)
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


def wrap_try_catch(content: str):
    pycode = "try:\n"
    pycode += re.sub(r"^", "  ", content, flags=re.MULTILINE)
    pycode += "\n"
    pycode += "except ImportError as e:\n"
    # pycode += f"  print('error during try load:',e)\n"
    pycode += f"  try:\n"
    pycode += f"    from {my_name}._ctx import ctx\n"
    pycode += f"    if not ctx.active: raise e\n"
    pycode += f"  except ImportError as ee:\n"
    # pycode += f"    print('error during load this library:',ee)\n"
    pycode += f"    pass\n"
    return pycode


def patch_file(path: Path):
    content = path.read_text()
    content = "__all__ = []\n" + content
    path.write_text(content)
    print(f"  * patch {path.relative_to(path.parent.parent)}")
