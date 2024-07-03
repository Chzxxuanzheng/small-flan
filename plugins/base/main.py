import sys
from api import IDesktopPet
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtCore import QSize
from typing import Callable

# 模块名
moduleName = '基础包'

# 优先级
preference = 495

# 定义一个指向全局的app的指针
pApp: IDesktopPet = None

def moduleInit(app: IDesktopPet) -> None:
	'''模块初始化,存在这个函数先调用这个函数,再进行模块合法性检测
	:params: app 桌宠的DesktopPet类
	'''
	global pApp
	pApp = app

# 任务栏相关
def food():
	...

def close():
	pApp.close()
	sys.exit()

def createTrayIcon()->QIcon:
	return QIcon('./assets/favicon.png')

def createTrayChoiceList()->list[tuple[str,Callable,None|QIcon]]:
	return [
		('召唤草莓',food,None),
		('__line__',None,None),
		('退出',close,None),
	]

def placeInit():
	...