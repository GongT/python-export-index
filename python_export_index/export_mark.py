import traceback
from typing import Any, Callable

from ._ctx import ctx


def export():
    assert ctx.active, "export() can only be used when dynamic importer running"
    current_file = traceback.extract_stack()[-2].filename

    def decorator(thing):
        _register(current_file, thing.__name__)
        return thing

    return decorator


def export_primitive(name):
    assert ctx.active, "export_primitive() can only be used when dynamic importer running"
    current_file = traceback.extract_stack()[-2].filename

    _register(current_file, name)


def _register(file, symbol_name):
    ctx.exports.append({"file": file, "name": symbol_name})
