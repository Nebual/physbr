import pygame
from random import random as rand, randint as randi
from math import copysign
from traceback import print_exc
import os
import operator,sys
pygame.font.init()

#DO NOT USE BEYOND TESTING (calling methods in this way is laggy)
class vec(tuple):
	"""A special tuple you can perform advanced math upon"""
	#Note: self.__class__ is just the same as vec
#	def __new__(cls,x,y=None):
#		if y != None: return tuple.__new__(cls,[x,y])
#		else:
#			if len(x) != 2: print "OMG A DIFF VEC! "+str(len(x)) 
	#		return tuple.__new__(cls,x)
	def __add__(self,other): 
		try:
			x,y = self; x2,y2 = other
			return vec((x+x2,y+y2))
		except ValueError: return vec(map(operator.add,self,other))
	def __sub__(self,other): 
		try:
			x,y = self; x2,y2 = other
			return vec((x-x2,y-y2))
		except ValueError: return vec(map(operator.sub,self,other))
	def __neg__(self): return vec(map(operator.neg,self))
	def __mul__(self,other):
		if isinstance(other,int) or isinstance(other,float): return vec([x * other for x in self])  
		else: return self.__class__(map(operator.mul,self,other))
	def __div__(self,other):
		if isinstance(other,int) or isinstance(other,float): return vec([x / other for x in self])  
		else: return self.__class__(map(operator.div,self,other))
	def __gt__(self,other): return all(map(operator.gt,self,other))
	def __lt__(self,other): return all(map(operator.lt,self,other))
	def __ge__(self,other): return all(map(operator.ge,self,other))
	def __le__(self,other): return all(map(operator.le,self,other))
	def length(self): 
		x,y = self
		return (x ** 2 + y ** 2) ** 0.5
	def normal(self,setlength=1):
		x,y = self
		if x == 0 and y == 0: return vec0
		length = setlength / ((x ** 2 + y ** 2) ** 0.5)
		return vec((x * length,y * length))
	def roundnormal(self,length=1):
		x,y = self
		if abs(x) > abs(y): return vec((copysign(length, self[0]),0))
		else: return vec((0, copysign(length, self[1])))
	def perpendicular(self):
		x,y = self
		return vec((-y,x))
	def roundperpendicular(self,length=1):
		if abs(self[0]) > abs(self[1]): return vec((0,copysign(length, self[0])))
		else: return vec((-copysign(length, self[1]),0))
	def simple(self,length=1):
		x,y = self
		if abs(x) > abs(y): return vec((cmp(x,0) * length,0))
		else: return vec((0,cmp(y,0) * length))
	def round(self):
		return vec((int(self[0]+0.5),int(self[1]+0.5)))
	def clamp(self,min,max):
		x,y = self; minx,miny = min; maxx,maxy = max
		if x < minx: x = minx
		elif x > maxx: x = maxx
		if y < miny: y = miny
		elif y > maxy: y = maxy
		return vec((x,y))
vec0 = vec((0,0))

rnd = lambda x: int(x+0.5)
ceil = lambda x: int(x+1)
lset = simplify = lambda x: list(set(x))
sign = lambda x: cmp(x,0) #-X returns -1, 0 returns 0, +x returns +1

ply = False
HitmaskCache = False #Becomes dict()
Maps = dict()
CurrentMap = True
EntIDIncrementer = 0
try: Units
except NameError:
	#This section will only be run on init!! These variables will persist "/reload"'s
	Server = None #The ServerSocket, will remain as None on clients
	Client = None #The ClientSocket
	World = None #The MiasmaCraft instance
	Settings = {}
	try: Settings["name"] = os.environ["USERNAME"].title()
	except KeyError: print "Wtf why you no have username"; Settings["name"] = "John"
	
	Units = dict()
	UnitCollisions = None #Setup in main.py
	EventQueue = []
	EventQueueLong = []
	Tick = 0
	Camerax = 0 #Vector for top left corner of the visible area
	Cameray = 0
	#Camera2 = vec0 #Bottom right corner of visible area
	#CameraMax = vec0
#This stuff can be safely reloaded
Pingtime = -1
#gaussgunsound = pygame.mixer.Sound("gun.ogg"); gaussgunsound.set_volume(0.5)

FontHP = pygame.font.Font(None,16)#.render(kind[0:int(self.size[0]/6)-1],True,(200,200,200))

def Timer(delay,reps,func,*args):
	if delay < 45: EventQueue.append([delay + Tick, delay, reps, func, args])
	else: EventQueueLong.append([delay + Tick, delay, reps, func, args])

#Copy to clipboard functions.
if sys.platform == "win32":
	import ctypes
	def copytoclipboard(text):
		ctypes.windll.user32.OpenClipboard(None) # Open Clip, Default task
		ctypes.windll.user32.EmptyClipboard()
		hCd = ctypes.windll.kernel32.GlobalAlloc( 0x2000, len( text )+1 )
		ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(ctypes.windll.kernel32.GlobalLock(hCd)), text)
		ctypes.windll.kernel32.GlobalUnlock(hCd)
		ctypes.windll.user32.SetClipboardData(1,hCd)
		ctypes.windll.user32.CloseClipboard()
else:
	from gtk import Clipboard as gtkClipboard
	def copytoclipboard(text):
		clip = gtkClipboard()
		clip.set_text(text)
		clip.store()

def CheckCollision(v1tl,v1br,v2tl,v2br):
	#if not v2br: return v1br[0] < v1tl[0] < v2tl[0] and v1br[1] < v1tl[1] < v2tl[1]
	return v1br[0] > v2tl[0] and v1tl[0] < v2br[0] and v1br[1] > v2tl[1] and v1tl[1] < v2br[1]
lvec,rvec,uvec,dvec = vec((-1,0)),vec((1,0)),vec((0,-1)),vec((0,1))
def CheckCollisionSides(v1tl,v1br,v2tl,v2br):
	"""Returns None or up(0,-1), right(1,0), down(0,1), left(-1,0) depending on which side of Obj2 Ob1 collided with"""
	xleft = abs(v1br[0] - v2tl[0]); xright = abs(v1tl[0] - v2br[0])
	ytop = abs(v1br[1] - v2tl[1]); ybottom = abs(v1tl[1] - v2br[1])
	xcomp =  min(xleft,xright)
	ycomp = min(ytop,ybottom)
	if xcomp < ycomp:
		if xleft < xright: return lvec
		else: return rvec
	else:
		if ytop < ybottom: return uvec
		else: return dvec

#Great for benchmarking
def timeit(code,setup="",times=1000000):
	from timeit import Timer as timeittimer
	base = timeittimer("True").timeit(times)
	print (timeittimer(code,setup).timeit(times) - base) / base

try: errorfile != None
except NameError: 
	errorfile = open(os.path.join(os.getenv("USERPROFILE") or os.getenv("HOME"),"physbr_errors.log"),"a")
	errorfile.write("\n")

def ErrorLog(msg=None):
	if msg: print "Error--"+msg+"--"
	print_exc()
	if errorfile.closed: return
	errorfile.write("-----------"+msg+"------------")
	#exctype,value = sys.exc_info()[:2]; sys.excepthook(exctype,value)
	print_exc(file=errorfile)
