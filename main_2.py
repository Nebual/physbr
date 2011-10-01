#!/usr/bin/python
import pygame,os,sys,threading
#import cProfile
from time import time, sleep
import math, random, zlib #Zombob libraries

#==============
#INITIALIZATION
#==============
pygame.mixer.init(buffer=512) #Sound library
pygame.init()
import globals as G
from entities import *
#pygame.key.set_repeat(300,50)

if sys.platform[:5] == "linux": screen = pygame.display.set_mode((0,0),pygame.NOFRAME) #Fullscreen!
else: 
	screen = pygame.display.set_mode((1024,768)) #Dunno how to fullscreen nicely in windows yet
screen_w, screen_h = screen.get_size()
print "Rendering at xy "+str(screen.get_size())
try:
	with open("models/hitmasks.cache","rb") as f: G.HitmaskCache = eval(zlib.decompress(f.read()))
except IOError: G.HitmaskCache = {} 

JumpSounds = [pygame.mixer.Sound("sounds/jump"+str(i)+".wav") for i in range(1,9)]
for sound in JumpSounds: sound.set_volume(0.4)

class Map:
	def __init__(self,name="ATestForTheHardOfThinking"):
		filehandler = open("maps/"+name+".shark","r")
		self.leveldata = eval(filehandler.read().replace("\n","").replace("	",""))
		self.PlayerSpawn = self.leveldata["PlayerSpawn"]
		self.Background = pygame.image.load("maps/backgrounds/" + self.leveldata["Background"]).convert()
		self.BackgroundWidth, self.BackgroundHeight = self.Background.get_size()
		G.Camerax,G.Cameray = self.leveldata["CameraStart"]
		self.Entities = {}
		self.WireEntities = {}
		self.Gravities = {}
		self.Collisions = []
		for v in self.leveldata["Entities"]:
			ent=Entity(self,v["x"],v["y"],v["model"],ang=v.get("ang",0),gravity=v.get("gravity",True),wiredetails=v.get("wiredetails",{}))
			#ent = Entity(G.CurrentMap,x,y,model,gravity,wiredetails)
		for k,ent in self.Entities.items():
			if ent.OutputNames:
				for wirename in ent.OutputNames:
					ent.Outputs.append(self.WireEntities[wirename])
		for v in self.leveldata["Collisions"]:
			self.Collisions.append(CollisionEntity(pygame.Rect(v[0],v[1],v[2]-v[0],v[3]-v[1])))
		try:
			self.Music = "music/" + self.leveldata.get("Music","")
			pygame.mixer.music.load(self.Music)
			pygame.mixer.music.play()
		except:
			pass
		G.Maps[name] = self

ply = G.ply = Player()
def ChangeMap(name):
	if not name in G.Maps: Map(name)
	G.CurrentMap = G.Maps[name]
	ply.pos.x,ply.pos.y = G.CurrentMap.PlayerSpawn
	G.CurrentMap.Gravities["ply"]=ply
	with open("models/hitmasks.cache","wb") as f: f.write(zlib.compress(repr(G.HitmaskCache),4))
ChangeMap("ATestForTheHardOfThinking")

#==============
#Main loop
#==============
#def loop():
while True:
	TickTime = time()
	G.Tick += 1
	key = pygame.key.get_pressed()
	ply.velx += (key[pygame.K_d] and ply.Speed) - (key[pygame.K_a] and ply.Speed)
	alt,shift,ctrl = key[pygame.K_LALT] or key[pygame.K_RALT], key[pygame.K_LSHIFT] or key[pygame.K_RSHIFT], key[pygame.K_LCTRL] or key[pygame.K_RCTRL]
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN:
			ekey = event.key
			#print "I got a "+pygame.key.name(event.key)+" ("+str(event.key)+"), my modifiers are "+str(pygame.key.get_mods())
			#if ekey == pygame.K_d: ply.velx += ply.Speed
			#elif ekey == pygame.K_a: ply.velx -= ply.Speed
			if ekey == pygame.K_e and not ply.Holding: #Pick up stuff.
				print "Pressing e..."
				if ply.FacingLeft: handx = ply.pos.centerx - 40; print "Left"
				else: handx = ply.pos.centerx + 40
				handy = ply.pos.centery
				print handx,handy, ply.pos.centerx
				print ply.width
			
				for prop in G.CurrentMap.Entities.values():
					if math.sqrt((handx - prop.pos.centerx)**2 + (handy - prop.pos.centery)**2) < 80:
						print "Pressing modelclass: "+prop.modelclass
						if prop.mass and prop.mass < 40 and prop.modelclass == "prop":
							print "Picking up entity " + str(prop.id)
							ply.Holding = (prop, prop.pos.x - ply.pos.x, prop.pos.y - ply.pos.y)
						elif prop.modelclass == "wire_switch" or prop.modelclass == "wire_button":
							print "Pressing wire switch or lever."
							prop.WireOutput(True)
			elif (ekey == pygame.K_SPACE or ekey == pygame.K_w) and ply.vely == 0: 
				ply.vely = ply.Speed*-2
				JumpSounds[random.randint(0,7)].play()
			elif (ekey == pygame.K_F4 and alt) or (ekey == pygame.K_q and ctrl):
				pygame.display.quit()
				sys.exit()
			
		elif event.type == pygame.KEYUP:
			ekey = event.key 
			
			#if ekey == pygame.K_d:
			#	if ply.velx > 0:
			#		ply.velx -= min(ply.Speed, ply.velx)
			#elif ekey == pygame.K_a:
			#	if ply.velx < 0:
			#		ply.velx += min(ply.Speed, -ply.velx)
			if ekey == pygame.K_e and ply.Holding: 
				ply.Holding[0].velx, ply.Holding[0].vely = ply.velx,ply.vely# + (key[pygame.K_d] - key[pygame.K_a])*ply.Speed
				ply.Holding = False
			
		elif event.type == pygame.MOUSEBUTTONDOWN:
			mouseposx, mouseposy = event.pos
			mouseposx += G.Camerax; mouseposy += G.Cameray
			
			#pygame.mouse.get_pos() works anywhere, event.pos works in here
			print "I clicked "+str(mouseposx)+", "+str(mouseposy)
			if event.button is 1: 
				pass
			elif event.button is 3:
				G.copytoclipboard(str(int(mouseposx))+", "+str(int(mouseposy)))
		#elif event.type == pygame.MOUSEBUTTONUP:
		#	pass
		elif event.type == pygame.QUIT:
			pygame.display.quit()
			sys.exit()

	#==== Timer System ====#
	threshold = G.Tick + 1
	for entry in G.EventQueue[:]: #[endtime, delay, repetitions, func, *args...]
		if entry[0] < threshold:
			if entry[2] == 1:
				G.EventQueue.remove(entry)
			else:
				entry[2] -= 1
				entry[0] = G.Tick + entry[1]
				if entry[1] < 45: G.EventQueue.append(entry)
				else: G.EventQueueLong.append(entry)
			entry[3](*entry[4])
	if G.Tick % 45 == 0:
		threshold = G.Tick + 45
		for entry in G.EventQueueLong[:]: #Iterate over a copy of the list so we can remove things from the original list as we go
			if entry[0] < threshold:
				G.EventQueue.append(entry)
				G.EventQueueLong.remove(entry)

	#==== Physics System ====#
	oldposx=ply.pos.x
	oldposy=ply.pos.y
	#ply.pos.x += (key[pygame.K_d] - key[pygame.K_a])*ply.Speed
	for ent in G.CurrentMap.Gravities.values(): #Basically all entities/ply with physics
		gx, gy = ent.gravity
		ent.velx += gx; ent.vely += gy #GRAVITY
		ent.velx -= cmp(ent.velx,0)*ent.area/250 * ent.friction
		if abs(ent.velx) < 1: ent.velx = 0
		ent.pos.x += ent.velx
		if abs(ent.vely) < 1: ent.vely = 0
		ent.pos.y += ent.vely
		#emass 50
		#evel 10
		#vmass 200
		#vvel 0
		otherent, colupwards = checkcollision(ent,velx=-ent.velx, vely=-ent.vely)
		if otherent:
			#if ent == ply: print ent.vely
			if ent.mass > otherent.mass: portion1 =  0.5 * otherent.mass / ent.mass; portion2 = 1 - portion1
			#elif ent.mass == otherent.mass: 
			else: portion2 = 0.5 * ent.mass / otherent.mass; portion1 = 1 - portion2
			portion1 /= 2; portion2 /= 2
			if colupwards: 
				ent.vely = -ent.vely * portion1
				if abs(ent.vely) < 1: ent.vely = 0
				if ent.rolls and ent.velx: ent.ang -= ent.velx * 4
			else: ent.velx = -ent.velx * portion1
			
			if otherent.Physics:
				if colupwards: 
					otherent.vely += portion2 * ent.mass * ent.vely / otherent.mass
					if abs(otherent.vely) < 1: otherent.vely = 0
				else: otherent.velx += portion2 * ent.mass * ent.velx / otherent.mass

			#CHECK FOR A SECOND COLLISION :P
			otherent, colupwards = checkcollision(ent,velx=-ent.velx, vely=-ent.vely)
			if otherent:
				#if ent == ply: print ent.vely
				if ent.mass > otherent.mass: portion1 =  0.5 * otherent.mass / ent.mass; portion2 = 1 - portion1
				#elif ent.mass == otherent.mass: 
				else: portion2 = 0.5 * ent.mass / otherent.mass; portion1 = 1 - portion2
				portion1 /= 2; portion2 /= 2
				if colupwards: 
					ent.vely = -ent.vely * portion1
					if abs(ent.vely) < 1: ent.vely = 0
					if ent.rolls and ent.velx: ent.ang -= ent.velx * 4
				else: ent.velx = -ent.velx * portion1
			
				if otherent.Physics:
					if colupwards: 
						otherent.vely += portion2 * ent.mass * ent.vely / otherent.mass
						if abs(otherent.vely) < 1: otherent.vely = 0
					else: otherent.velx += portion2 * ent.mass * ent.velx / otherent.mass
	if oldposx != ply.pos.x:
		#We're moving on the X plane :D
		if ply.Stationary:
			ply.Stationary = False
			ply.FacingLeft = (oldposx > ply.pos.x) and 5 or 0
			ply.curframe = 3
			ply.model = ply.models[ply.curframe + ply.FacingLeft]
		elif G.Tick % 4 == 0:
			ply.curframe += 1
			if ply.curframe > 4: ply.curframe = 0
			ply.FacingLeft = (oldposx > ply.pos.x) and 5 or 0 
			ply.model = ply.models[ply.curframe + ply.FacingLeft]
		#if checkcollision(ply, velx=oldposx - ply.pos.x):
		#	ply.velx = 0
		camdiffx = ply.pos.x - G.Camerax
		if camdiffx < screen_w * 0.35: G.Camerax -= screen_w * 0.35 - camdiffx
		elif camdiffx > screen_w * 0.65: G.Camerax += camdiffx - screen_w * 0.65
		if G.Camerax < 0: G.Camerax = 0
		elif G.Camerax + screen_w > G.CurrentMap.BackgroundWidth: G.Camerax = G.CurrentMap.BackgroundWidth - screen_w
	else:
		ply.Stationary = True
		ply.curframe=2
		ply.model = ply.models[2 + ply.FacingLeft]
	if oldposy != ply.pos.y:
		#We moved on Y plane!
		camdiffy = ply.pos.y - G.Cameray
		if camdiffy < screen_h * 0.2: G.Cameray -= screen_h * 0.2 - camdiffy
		elif camdiffy > screen_h * 0.8: G.Cameray += camdiffy - screen_h * 0.8
		if G.Cameray < 0: G.Cameray = 0
		elif G.Cameray > G.CurrentMap.BackgroundHeight: G.Cameray = G.CurrentMap.BackgroundHeight 

	if ply.Holding:
		ent,x,y = ply.Holding
		entvelx,entvely = ply.pos.x + x - ent.pos.x,ply.pos.y + y - ent.pos.y
		ent.pos.x = ply.pos.x + x
		ent.pos.y = ply.pos.y + y

		checkcollision(ent,velx=-entvelx, vely=-entvely)
		ent.vely = 0

	#Undo the player's movement, since Velocity persists
	ply.velx -= (key[pygame.K_d] and ply.velx >= ply.Speed and ply.Speed) - (key[pygame.K_a] and ply.velx <= -ply.Speed and ply.Speed)
	#==============
	#DRAWING
	#==============
	screen.blit(G.CurrentMap.Background, (-G.Camerax,-G.Cameray)) #It's position minus camera position; or else things invert in the camera movement
	for k,ent in G.CurrentMap.Entities.items():
		if ent.d_ang != ent.ang:
			ent.model = pygame.transform.rotate(ent.model0,ent.ang)
			ent.d_ang = ent.ang
		screen.blit(ent.model,(ent.pos.x - G.Camerax - ent.renderoffsetx,ent.pos.y - G.Cameray))
	screen.blit(ply.model, (ply.pos.x - G.Camerax - ply.renderoffsetx,ply.pos.y - G.Cameray))
	pygame.display.flip() #Swaps between drawing buffer (what we write sprites to), and rendering buffer (sent to video card), "Double Buffering"
	
	delay = 30.3 - (time() - TickTime)*1000
	if delay > 0: pygame.time.delay(int(delay)) #Updates x times per second

#import cProfile
#while True:
#	if G.Tick % 30 == 0:
#		cProfile.runctx("loop()",locals(),globals())
#	else:
#		loop()