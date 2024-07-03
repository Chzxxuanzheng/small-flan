import os
import sys
from PyQt5.QtGui import QIcon, QMovie, QCursor, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QLabel\
	, QVBoxLayout, QSystemTrayIcon, QDesktopWidget, QAction

from PyQt5.QtMultimedia import QSound

import logging
from typing import Any, overload

from json import load, dump

logging.basicConfig(level=logging.INFO)

# 加载配置
def readConfig(key: str)->Any:
	if not os.path.exists('./config'): return None
	with open('./config', 'r')as f:
		data = load(f)
		if key not in data: return None
		return data[key]

# 设置配置
def saveConfig(key: str, value: Any)->None:
	if not os.path.exists('./config'): data = {}
	else:
		with open('./config', 'r')as f: data = load(f)
	data[key] = value
	with open('./config', 'w')as f:
		dump(data,f)

class DesktopPet(QWidget):
	center: QPoint = QPoint(0,0)
	def __init__(self, parent=None, **kwargs) -> None:
		super(DesktopPet,self).__init__(parent=parent)
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

	def setCenter(self, ax: int|QPoint, ay: int|None=None)->None:
		if isinstance(ax, QPoint): self.center = ax
		else: self.center = QPoint(ax,ay)

	def move(self, ax: int|QPoint, ay: int|None=None)->None:
		if isinstance(ax, QPoint): super().move(ax-self.center)
		else: self.move(QPoint(ax,ay))

	def x(self) -> int: return super().x()+self.center.x()
	def y(self) -> int: return super().y()+self.center.y()

	def pos(self)->QPoint:return super().pos()+self.center

class Food(DesktopPet):
	CATCH: int = 0
	DOWN: int = 1

	flag: int = 0
	# 初始化界面
	def __init__(self, father, **kwargs):
		super().__init__(parent=None)
		self.initWindow()
		self.setFocus()

		self.father: DesktopPet = father

		self.followTimer = QTimer()
		self.followTimer.timeout.connect(self.followMouse)
		self.followTimer.start(40)

		self.downTimer = QTimer()
		self.downTimer.timeout.connect(self.down)

		self.suckTimer = QTimer()
		self.suckTimer.timeout.connect(self.beSucked)

	def followMouse(self):
		self.move(QCursor.pos().x()-17,QCursor.pos().y()-14)

	def down(self):
		add = self.father.y() - 13 - self.y()
		if add == 0:
			self.father.walkStep = 0
			self.flag = self.DOWN
			self.downTimer.stop()
		if add > 10:add = 20
		elif add < -10: add = -20
		self.move(self.x(),self.y()+add)

	def startBeSucked(self):
		self.downTimer.stop()
		self.suckTimer.start(40)

	def beAte(self):
		self.destroy()

	times = 1
	def beSucked(self):
		move = self.times * 5
		if self.father.toward == self.father.RIGHT:
			distance = ((self.x() - self.father.x() - 20) ** 2 + (self.father.y() - 30 - self.y()) ** 2)**0.5
		else:
			distance = ((self.x() - self.father.x() + 20) ** 2 + (self.father.y() - 30 - self.y()) ** 2)**0.5
		if distance < 5:
			self.father.eat()
			return
		if move > distance: move = distance
		y = -int(move*abs(self.father.y() - 30 - self.y())/distance)
		if self.father.toward == self.father.RIGHT:
			x = int(move * abs(self.x() - 20 - self.father.x())/distance)
			if self.x() - 20 - self.father.x() > 0:x=-x
		else:
			x = int(move * abs(self.x() + 20 - self.father.x())/distance)
			if self.x() + 20 - self.father.x() > 0:x=-x
		self.move(self.pos()+QPoint(x,y))
		self.times += 1

	# 窗体初始化
	def initWindow(self):
		self.image = QLabel()
		# 初始化动画
		img = QPixmap('./assets/food.png')
		self.image.setPixmap(img.scaled(35,27,Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

		vbox = QVBoxLayout()
		vbox.addWidget(self.image)

		self.setLayout(vbox)

		# 设置中心
		self.setCenter(17,14)

		# 拖动时鼠标图形的设置
		self.setCursor(QCursor(Qt.OpenHandCursor))

	# 鼠标左键按下时, 释放草莓
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.followTimer.stop()
			self.downTimer.start(40)
		event.accept()
		# 还原鼠标设置
		self.setCursor(QCursor(Qt.ArrowCursor))

class Flan(DesktopPet):
	# 枚举
	# 朝向
	LEFT: int = 0
	RIGHT: int = 1

	# flag
	STAND: int = 0
	WALK: int = 1
	SUCK: int = 2
	EAT: int = 3
	FIND_FOOD: int = 4
	WAIT_FOOD: int = 5
	APPEAR: int = 6


	# 动画flag
	PLAYING: int = 1
	STOP: int = 0

	toward: int = RIGHT
	flag: int = 0
	movieFlag: int = 0
	posY: int = 0
	foodW: Food = None

	allowVideo: bool = False
	allowWalk: bool = True
	def __init__(self):
		super().__init__()

		# 初始化配置
		self.readConfig()

		# 托盘化初始
		self.initTray()
		# 初始化窗体
		self.initWindow()
		# 展示
		self.show()

		# 动画计时
		self.movieTimer = QTimer()
		self.movieTimer.timeout.connect(self.movieAfter)
		self.movieTimer.start(40)

	def readConfig(self):
		# 行走开关
		if allowWalk := readConfig('allowWalk'):
			self.allowWalk = allowWalk
		else: saveConfig('allowWalk',self.allowWalk)

		# 音频开关
		if allowVideo := readConfig('allowVideo'):
			self.allowVideo = allowVideo
		else: saveConfig('allowVideo', allowVideo)

		# 高度
		if posY := readConfig('height'):
			self.posY = posY
		else: self.posY = self.size().height()

	# 保存配置
	def saveConfig(self):
		saveConfig('allowWalk', self.allowWalk)
		saveConfig('allowVideo', self.allowVideo)
		saveConfig('height', self.posY)

	def changeMovie(self, name: str):
		self.movie = QMovie(self.assets(name))
		# 设置标签大小
		self.movie.setScaledSize(QSize(250, 220))
		# 将QMovie在定义的image中显示
		self.image.setMovie(self.movie)
		self.movie.start()
		self.movie.frameChanged.connect(self.moviePlay)

	def assets(self, name: str,lastName: str = 'webp'):
		return f'./assets/{name}-{"l" if self.toward == self.LEFT else "r"}.{lastName}'

	def sound(self, name):
		if not self.allowVideo: return
		QSound.play(f'./assets/{name}.wav')

	# 动画决策区 

	# 走路
	# 每走一次要162的距离
	walkStep = 0
	def walk(self):
		from random import randint
		if randint(0,5) != 0:return False
		if not self.allowWalk: return False

		screen_geo = QDesktopWidget().screenGeometry()
		pet_geo = self.geometry()

		# 计算有多少地方可以蹦
		if self.toward == self.LEFT:
			place = self.x() - pet_geo.width() / 2
			max = place // 162
		elif self.toward == self.RIGHT:
			place = screen_geo.width() - self.x() - pet_geo.width() / 2
			max = place // 162

		# 没地方蹦
		if max <= 0: return False

		self.walkStep = randint(1,max)
		return True

	# 转向
	def turnToward(self):
		from random import randint
		if randint(0,5) != 0:return False

		if self.toward == self.LEFT:
			self.toward = self.RIGHT
		else:
			self.toward = self.LEFT
		return True
	
	# 前往食物
	soundFlag: bool = True
	def toFood(self):
		distance = self.x() - self.foodW.x()
		if distance < 0:
			self.toward = self.RIGHT
		else:
			self.toward = self.LEFT
		distance = abs(distance)
		place = distance // 162
		# 可以吃到
		if place == 0: 
			self.suck()
			self.soundFlag = True
			return True
		else:
			if self.soundFlag:
				from random import randint
				self.sound(f'food{randint(1,3)}')
				self.soundFlag = False
			return False

	# 动画播放完一遍后的处理区

	def movieAfter(self):
		if not self.moviePlayAfter: return
		# 正在前进
		if self.walkStep > 0:
			self.walkStep -= 1
			self.forward()
		# 选择动画
		else:
			# 吸食物特殊处理
			if self.flag == self.WAIT_FOOD:
				self.moviePlayAfter = False
				return
			elif self.foodW and self.foodW.flag == self.foodW.DOWN:
				if not self.toFood():self.forward()
			# 走路
			elif self.walk():
				self.walkStep -= 1
				self.forward()
			# 转向
			elif self.turnToward(): 
				self.stand()
			# 啥都没有就站尸
			else:
				self.stand()

	# 动画执行区

	def appear(self):
		logging.debug('进入appear动画')
		self.moviePlayAfter = False
		self.changeMovie('appear')
		self.flag = self.APPEAR

	def stand(self):
		logging.debug('进入stand动画')
		self.moviePlayAfter = False
		self.changeMovie('stand')
		self.flag = self.STAND

	# 前进
	def forward(self):
		logging.debug('进入walk动画')
		self.moviePlayAfter = False
		self.changeMovie('walk')
		self.flag = self.WALK

	def suck(self):
		logging.debug('进入suck动画')
		self.moviePlayAfter = False
		self.changeMovie('suck')
		self.flag = self.SUCK

	def eat(self):
		logging.debug('进入eat动画')
		self.moviePlayAfter = False
		self.changeMovie('eat')
		self.flag = self.EAT
		self.sound('eat')

	# 动画播放
	moviePlayAfter = False
	def moviePlay(self, frame: int):
		# 播放完
		if frame == self.movie.frameCount() - 1:
			self.movie.stop()
			if self.flag == self.SUCK:self.flag = self.WAIT_FOOD
			self.moviePlayAfter = True
		# 走路
		if self.flag == self.WALK:
			if 13 <= frame <= 42:
				movieX = -5 if self.toward == self.LEFT else 5
			elif 42 < frame <= 48:
				movieX = -2 if self.toward == self.LEFT else 2
			else:
				movieX = 0
			self.move(self.x()+movieX,self.y())
		# 吸
		elif self.flag == self.SUCK:
			if frame == 5:
				self.foodW.startBeSucked()
		# 吃
		elif self.flag == self.EAT:
			if self.foodW:
				self.foodW.beAte()
				self.foodW = None
		# 出现
		elif self.flag == self.APPEAR:
			if frame == 40:
				self.sound('appear')

	# 窗体初始化
	def initWindow(self):
		self.image = QLabel()
		# 初始化动画
		self.appear()

		vbox = QVBoxLayout()
		vbox.addWidget(self.image)

		self.setLayout(vbox)

		# 设置中心
		self.setCenter(125,220)

		# 设置位置
		self.initPosition()

	# 托盘化设置初始化
	def initTray(self):
		# 创建托盘图标
		self.tray = QSystemTrayIcon(self)
		self.tray.setIcon(QIcon('./assets/favicon.ico'))

		trayMenu = QMenu(self)

		trayMenu.addAction(QAction('召唤草莓',self,triggered=self.food,icon=QIcon('./assets/food.png')))
		self.walkSwitchAction = QAction('',triggered=self.walkSwitch)
		trayMenu.addAction(self.walkSwitchAction)
		self.videoSwitchAction = QAction('',triggered=self.videoSwitch)
		trayMenu.addAction(self.videoSwitchAction)
		if self.allowWalk:
			self.walkSwitchAction.setText('禁止走路')
		else:
			self.walkSwitchAction.setText('允许走路')
		if self.allowVideo:
			self.videoSwitchAction.setText('禁用音频')
		else:
			self.videoSwitchAction.setText('启用音频')
		trayMenu.addAction(QAction('重设高度',self,triggered=self.resetHeight))
		trayMenu.addAction(QAction('退出',self,triggered=self.quit))

		# 设置托盘化菜单项
		self.tray.setContextMenu(trayMenu)
		# 展示
		self.tray.show()


	# 宠物右键点击交互
	def contextMenuEvent(self, event):
		# 定义菜单
		menu = QMenu(self)
		# 定义菜单项
		food = menu.addAction('召唤草莓')
		food.setIcon(QIcon('./assets/food.png'))
		menu.addSeparator()
		if self.allowWalk:
			walkSwitch = menu.addAction('禁止走路')
		else:
			walkSwitch = menu.addAction('允许走路')
		if self.allowVideo:
			videoSwitch = menu.addAction('禁用音频')
		else:
			videoSwitch = menu.addAction('启用音频')
		quit = menu.addAction('退出')

		action = menu.exec_(self.mapToGlobal(event.pos()))
		if action == food:
			self.food()
		elif action == walkSwitch:
			self.walkSwitch()
		elif action == videoSwitch:
			self.videoSwitch()
		elif action == quit:
			self.quit()

	def initPosition(self):
		'''
		初始化位置
		'''
		import random
		screen_geo = QDesktopWidget().screenGeometry()
		pet_geo = self.geometry()
		x = int((screen_geo.width() - pet_geo.width()) * random.random())
		self.posY = readConfig('height')
		if not self.posY:
			self.posY = self.size().height()
		y = self.posY
		self.move(x,y)


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
		# 记录高度
		self.posY = self.y()
		saveConfig('height', self.posY)

	# 鼠标移进时调用
	def enterEvent(self, event):
		# 设置鼠标形状 Qt.ClosedHandCursor   非指向手
		self.setCursor(Qt.ClosedHandCursor)

	def food(self):
		if self.foodW:return
		self.foodW = Food(self)
		self.foodW.show()

	def walkSwitch(self):
		self.allowWalk = not self.allowWalk
		if self.allowWalk:
			self.walkSwitchAction.setText('禁止走路')
		else:
			self.walkStep = 0
			self.walkSwitchAction.setText('允许走路')

	def videoSwitch(self):
		self.allowVideo = not self.allowVideo
		if self.allowVideo:
			self.videoSwitchAction.setText('禁用音频')
		else:
			self.videoSwitchAction.setText('启用音频')

	def quit(self):
		self.saveConfig()
		self.quit()
		sys.exit()

	def resetHeight(self):
		self.posY = self.size().height()
		self.move(self.x(),self.posY)
		with open('./height','w')as f:
			f.write(str(self.posY))

def main() -> None:
	app = QApplication(sys.argv)
	flan = Flan()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()