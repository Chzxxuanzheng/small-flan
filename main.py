import os
import sys
from PyQt5.QtGui import QIcon, QMovie, QCursor
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QLabel\
	, QVBoxLayout, QSystemTrayIcon, QDesktopWidget, QAction

from importlib.util import module_from_spec, spec_from_file_location
import logging
from typing import Any

from interface import *

logging.basicConfig(level=logging.DEBUG)

def loadModule(path: str) -> object:
	spec = spec_from_file_location('module_name', path)
	module = module_from_spec(spec)
	spec.loader.exec_module(module)
	return module

class DesktopPet(QWidget):
	modules: list[IModule] = []

	def __init__(self, parent=None, **kwargs):
		super(DesktopPet, self).__init__(parent)
		# 加载插件
		self.loadPlugins()
		# 窗体初始化
		self.initWindow()
		# 托盘化初始
		self.initTray()
		# 展示
		self.show()

	def loadPlugins(self) -> None:
		'''
		加载模块用,模块位于plugins的文件夹里,模板看base.py
		'''
		logging.info('-------------------------------')
		logging.info('开始加载模块')
		cwd = os.getcwd()
		for moduleDirName in os.listdir('./plugins'):
			moduleCwd = f'./plugins/{moduleDirName}'
			modulePath = f'{moduleCwd}/main.py'
			if not os.path.exists(modulePath):continue
			# 进入cwd,设置path
			os.chdir(cwd)
			os.chdir(moduleCwd)
			sys.path.append('./')
			module = loadModule('./main.py')
			module.moduleInit(self)
			try:
				module.moduleInit(self)
			except AttributeError:
				...
			property = dir(module)
			if 'moduleName' not in property:
				logging.error(f'{modulePath}缺少模块名')
				continue
			if 'preference' not in property:
				logging.warning(f'{module.moduleName}缺少优先级')
				module.preference = 500
			else:
				if type(module.preference) != int:
					logging.warning(f'{module.moduleName}优先级不为整数')
					module.preference = 500
			# 设置cwd
			module.cwd = os.getcwd()
			self.modules.append(module)
		os.chdir(cwd)
		logging.info(f'共计加载{len(self.modules)}个模块:')
		self.modules.sort(key=lambda module: module.preference)
		logging.info('-------------------------------')
		[logging.info(i.moduleName) for i in self.modules]

	# 窗体初始化
	def initWindow(self):
		# 初始化
		# 设置窗口属性:窗口无标题栏且固定在最前面
		# FrameWindowHint:无边框窗口
		# WindowStaysOnTopHint: 窗口总显示在最上面
		# SubWindow: 新窗口部件是一个子窗口，而无论窗口部件是否有父窗口部件
		self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
		# setAutoFillBackground(True)表示的是自动填充背景,False为透明背景
		self.setAutoFillBackground(False)
		# 窗口透明，窗体空间不透明
		self.setAttribute(Qt.WA_TranslucentBackground, True)

		# 重绘组件、刷新
		self.repaint()

		# 插件
		[... for _ in self.modulesFor('initWindow')]

	# 托盘化设置初始化
	def initTray(self):
		# 创建托盘图标
		self.tray = QSystemTrayIcon(self)
		# 设置托盘化图标
		for icon in self.modulesFor('createTrayIcon'):
			if isinstance(icon, QIcon):
				self.tray.setIcon(icon)
				break
		else:
			logging.error('托盘图标缺失')

		# 设置按钮
		# 新建一个菜单项控件
		self.trayMenu = None
		for configs in self.modulesFor('createTrayChoiceList'):
			if self.trayMenu: self.trayMenu.addSeparator()
			else:self.trayMenu = QMenu(self)
			for config in configs:
				# 划线
				if config[0] == '__line__':
					self.trayMenu.addSeparator()
				else:
					action = QAction(config[0],self,triggered=config[1])
					if type(config[2]) == QIcon:
						action.setIcon(config[2])
					self.trayMenu.addAction(action)

		# 设置托盘化菜单项
		self.tray.setContextMenu(self.trayMenu)
		# 展示
		self.tray.show()

	# 宠物静态gif图加载
	def initPet(self):
		# 对话框定义
		self.talkLabel = QLabel(self)
		# 对话框样式设计
		self.talkLabel.setStyleSheet("font:15pt '楷体';border-width: 1px;color:blue;")
		# 定义显示图片部分
		self.image = QLabel(self)
		# QMovie是一个可以存放动态视频的类，一般是配合QLabel使用的,可以用来存放GIF动态图
		self.movie = QMovie("./assets/stand-l.webp")
		# 设置标签大小
		self.movie.setScaledSize(QSize(200, 200))
		# 将Qmovie在定义的image中显示
		self.image.setMovie(self.movie)
		self.movie.start()
		self.resize(300, 300)

		# 调用自定义的randomPosition，会使得宠物出现位置随机
		self.randomPosition()

		# 布局设置
		vbox = QVBoxLayout()
		vbox.addWidget(self.talkLabel)
		vbox.addWidget(self.image)

		#加载布局：前面设置好的垂直布局
		self.setLayout(vbox)

		# 展示
		self.show()

	# 宠物正常待机动作
	def petNormalAction(self):
		# 每隔一段时间做个动作
		# 宠物状态设置为正常
		self.condition = 0
		# 对话状态设置为常态
		self.talk_condition = 0

	# 显示宠物
	def showwin(self):
		# setWindowOpacity（）设置窗体的透明度，通过调整窗体透明度实现宠物的展示和隐藏
		self.setWindowOpacity(1)

	# 宠物随机位置
	def randomPosition(self):
		# screenGeometry（）函数提供有关可用屏幕几何的信息
		screen_geo = QDesktopWidget().screenGeometry()
		# 获取窗口坐标系
		pet_geo = self.geometry()
		# width = (screen_geo.width() - pet_geo.width()) * random.random()
		# height = (screen_geo.height() - pet_geo.height()) * random.random()
		self.move(int(0), int(0))

	# 鼠标左键按下时, 宠物将和鼠标位置绑定
	def mousePressEvent(self, event):
		# 更改宠物状态为点击
		self.condition = 1
		# 更改宠物对话状态
		self.talk_condition = 1
		if event.button() == Qt.LeftButton:
			self.is_follow_mouse = True
		# globalPos() 事件触发点相对于桌面的位置
		# pos() 程序相对于桌面左上角的位置，实际是窗口的左上角坐标
		self.mouse_drag_pos = event.globalPos() - self.pos()
		event.accept()
		# 拖动时鼠标图形的设置
		self.setCursor(QCursor(Qt.OpenHandCursor))

	# 鼠标移动时调用，实现宠物随鼠标移动
	def mouseMoveEvent(self, event):
		# 如果鼠标左键按下，且处于绑定状态
		if Qt.LeftButton and self.is_follow_mouse:
			# 宠物随鼠标进行移动
			self.move(event.globalPos() - self.mouse_drag_pos)
		event.accept()

	# 鼠标释放调用，取消绑定
	def mouseReleaseEvent(self, event):
		self.is_follow_mouse = False
		# 鼠标图形设置为箭头
		self.setCursor(QCursor(Qt.ArrowCursor))

	# 鼠标移进时调用
	def enterEvent(self, event):
		# 设置鼠标形状 Qt.ClosedHandCursor   非指向手
		self.setCursor(Qt.ClosedHandCursor)

	# 宠物右键点击交互
	def contextMenuEvent(self, event):
		# 定义菜单
		menu = QMenu(self)
		# 定义菜单项
		hide = menu.addAction("隐藏")
		question_answer = menu.addAction("故事大会")
		menu.addSeparator()
		quitAction = menu.addAction("退出")

		# 使用exec_()方法显示菜单。从鼠标右键事件对象中获得当前坐标。mapToGlobal()方法把当前组件的相对坐标转换为窗口（window）的绝对坐标。
		action = menu.exec_(self.mapToGlobal(event.pos()))
		# 点击事件为退出
		if action == quitAction:
			...
		# 点击事件为隐藏
		if action == hide:
			# 通过设置透明度方式隐藏宠物
			self.setWindowOpacity(0)
		# 点击事件为故事大会
		if action == question_answer:
			# self.client = Client()
			# self.client.show()
			logging.info('test')

	# ========================
	# 模块使用相关
	# ========================

	def modulesFor(self,property: str,call=True,*args, **kwargs)->Any:
		'''
		遍历所有模块的指定属性
		:params property: 属性
		:params call: 是否调用,默认为True
		:return: 属性
		'''
		for module in self.modules:
			# 没有这个属性
			if property not in dir(module): continue
			# 调用这个属性
			if call:
				# 该属性不可调用
				if not callable(getattr(module,property)):continue
				try:
					yield self.callModuleMethod(module, property, catch=False, *args, **kwargs)
				except Exception as ex:
					logging.exception(ex)
			# 不调用这个属性
			else: yield getattr(module,property)

	@staticmethod
	def callModuleMethod(module: IModule, method: str, catch:bool=True, *args, **kwargs)->Any:
		'''
		调用模块的方法,使用该方法会进入模块专属的cwd
		:params module: 模块
		:params catch: 是否捕捉异常
		:params method: 方法名
		:return: 方法返回值,如果捕获到异常会返回异常
		'''

		if catch:
			try:
				return DesktopPet.callModuleMethod(module, method, catch=False, *args, **kwargs)
			except Exception as ex: 
				logging.exception(ex)
				return ex

		property = getattr(module,method)
		cwd = os.getcwd()
		os.chdir(module.cwd)
		result = property(*args, **kwargs)
		os.chdir(cwd)
		return result

def main() -> None:
	# 创建了一个QApplication对象，对象名为app，带两个参数argc,argv
	# 所有的PyQt5应用必须创建一个应用（Application）对象。sys.argv参数是一个来自命令行的参数列表。
	app = QApplication(sys.argv)
	# 窗口组件初始化
	pet = DesktopPet()
	# 1. 进入时间循环；
	# 2. wait，直到响应app可能的输入；
	# 3. QT接收和处理用户及系统交代的事件（消息），并传递到各个窗口；
	# 4. 程序遇到exit()退出时，机会返回exec()的值。
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()