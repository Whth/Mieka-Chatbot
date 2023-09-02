import importlib

# 从指定文件位置加载模块
module = importlib.import_module('test1', r'L:\pycharm projects\chatBotComponents')
module.hi()
print(module.__all__)
