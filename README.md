# python index文件生成器

将一个目录中所有文件的内容提取出来，生成一个索引文件。

并且禁止直接从文件夹内部import文件

总之更加符合nodejs的理念

# 使用方法

## 外部模式：通过一个脚本来生成索引文件
* 优点：运行时不需要这个包
* 缺点：必须注意不能有额外效应，因为生成过程需要import所有python脚本    
    不能禁止import子文件夹

**外部模式不可以使用export、export_primitive、disable_import**

示例：

假设有目录`my_py_lib`，其中`public`是一个子目录，里面有很多python脚本。

要生成一个索引放在`my_py_lib`中，名为`__init__.py`

可以使用以下代码，此文件可保存为`scripts/generate.py`:

```python
from python_export_index import create_exports
from pathlib import Path

create_exports(Path(__file__).parent.joinpath("my_py_lib"), "public/", "__init__.py")
```

## 运行模式: 侵入实际要用的代码中
* 优点：不需要额外脚本
* 缺点：导入过程会多运行一些不必要的代码，运行时依赖这个包


示例：

假设有目录`my_py_lib`，其中`public`是一个子目录，里面有很多python脚本。

编写`my_py_lib/__init__.py`，内容如下：

```python
from python_export_index import create_exports
from pathlib import Path

create_exports(Path(__file__).parent, "public/", "_generated.py")

# 注意这个import不能提到上面去
from _generated import *

# 这里可以放一些其他的代码
```

## 如何导出

```python
## 通过装饰器来声明导出
from python_export_index import export, export_primitive

@export()
class SomeClass:
	pass

@export()
def some_function():
	pass

some_value = SomeClass()
export_primitive('some_value')


## 通过设置__all__来声明导出
def another_way():
	pass
value = 42

__all__ = ["value", "another_way"]
```

## 防止文件被从外部导入
由于不是所有文件都在`/public`目录中，其他文件可以用这种方法防止被导入，实际上只需要在最外层`__init__.py`中使用即可

例如`/my_py_lib/internal/__init__.py`中使用后，整个`/my_py_lib/internal`目录都不能被导入

```python
from python_export_index import disable_import
disable_import()
```
