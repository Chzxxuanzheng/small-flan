from abc import abstractmethod, ABC

class IModule(ABC):
	# 模块名
	@property
	@abstractmethod
	def moduleName()->str:...

	# cwd
	@property
	@abstractmethod
	def cwd()->str:...