# 这个文件是自动生成的，不要手动修改任何内容！！
##### 08b6691a-40b9-4b6a-9bb1-34ff0acc281b #####

import traceback
print(f"[index] I'm imported with name \"{__name__}\"")
for line in traceback.format_stack():
  if line.startswith('  File "/'): print(line.rstrip())
  else: break
from .parts.file import some_value
from .parts.file2 import some_other_function
from .parts.file import some_function
from .parts.file import SomeClass
from .parts.file2 import __all__ as _a
del _a
from .parts.empty import __all__ as _a
del _a
print('all files loaded!!')
__all__ = [
  'some_value',
  'some_other_function',
  'some_function',
  'SomeClass',
]