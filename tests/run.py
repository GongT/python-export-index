import sys
from pathlib import Path


sys.path.insert(0, Path(__file__).parent.parent.parent.as_posix())

from python_export_index import create_exports

create_exports(Path(__file__).parent.joinpath("pkg"), "parts")

from pkg import some_function
some_function()
