__all__ = ["some_value"]
from python_export_index.export_mark import export

from .file2 import some_other_function


@export()
def some_function():
    print("Hello from some_function!")
    some_other_function()


@export()
class SomeClass:
    pass


some_value = 42
