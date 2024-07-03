'''
main.py里的DesktopPet类的接口
'''
from abc import ABC, abstractmethod
from typing import Any
from PyQt5.QtWidgets import QWidget

class IModule(ABC):
	# 模块名
	@property
	@abstractmethod
	def moduleName()->str:...

	# cwd
	@property
	@abstractmethod
	def cwd()->str:...


class IDesktopPet(QWidget):
	@abstractmethod
	def loadPlugins()->None:
		'''
		加载所有插件
		'''
		...

	@abstractmethod
	def modulesFor(self,property: str,call=True,*args, **kwargs)->Any:
		'''
		遍历所有模块的指定属性
		:params property: 属性
		:params call: 是否调用,默认为True
		:return: 属性
		'''
		...

	@staticmethod
	@abstractmethod
	def callModuleMethod(module: IModule, method: str, catch:bool=True, *args, **kwargs)->Any:
		'''
		调用模块的方法,使用该方法会进入模块专属的cwd
		:params module: 模块
		:params catch: 是否捕捉异常
		:params method: 方法名
		:return: 方法返回值,如果捕获到异常会返回异常
		'''