import pygame
import globals as G; ply = G.ply
import modelinfo
import os, math

JumpSounds = [pygame.mixer.Sound("sounds/jump"+str(i)+".wav") for i in range(1,9)]

def LoadTiledImage(filepath):
	frames=[]
	Img = pygame.image.load(filepath)
	w,h = Img.get_size()
	tilewidth = w / 5.0
	Img.set_colorkey((0,0,0))

	for x in range(5):
		frames.append(Img.subsurface((x * tilewidth, 0, tilewidth, h)))
	return frames

class Player:
	def __init__(self):
		self.id = "ply" #Not an integer because he's a badass
		self.velx = 0
		self.vely = 0
		self.mass = 82 #Average adult male's weight in garries.
		self.Speed = 6
		self.Stationary = True #This is mostly just to function as an edge for xmovement
		self.LastCollision = False
		self.Physics = True
		self.rolls = False
		self.friction = 0
		model = "dudewalking.png"
		self.models = LoadTiledImage("models/images/"+model)
		nummodels = range(len(self.models))
		for k in nummodels: self.models.append(pygame.transform.flip(self.models[k],True,False))
		for k in nummodels: self.models.append(pygame.transform.flip(self.models[k],False,True))
		for k in nummodels: self.models.append(pygame.transform.flip(self.models[k],True,True))
		self.model = self.models[2]
		self.curframe = 2
		self.UpsideDown = self.FacingLeft = 0
		#self.model = pygame.image.load("models/images/malecharacter.png").convert_alpha() #Also consider colourkeys instead
		#self.gravity = (0,1)
		self.Holding = False
		if model in G.HitmaskCache: 
			tab = G.HitmaskCache[model]
			self.hitmask,self.renderoffsetx,self.width,self.height = tab["hitmask"],tab["renderoffsetx"],tab["width"],tab["height"]
		else: #Hasn't been generated yet
			mask=[]
			image = self.model
			width, height = image.get_size()
			rangeheight = range(height)
			for x in range(width):
				temp = []
				for y in rangeheight:
					pixel = image.get_at((x,y))
					temp.append(not (pixel[0]==0 and pixel[1]==0 and pixel[2]==0))
				mask.append(tuple(temp)) #For some reason tuples are faster at this layer
			for xrow in mask:
				if True in mask[0]: break #Trim off excess width before the model actually starts
				else: mask.pop(0)
			self.renderoffsetx = width - len(mask)
			for xrow in mask:
				if True in mask[-1]: break #After
				else: mask.pop()
			self.hitmask = mask
			self.width, self.height = len(self.hitmask), len(self.hitmask[0])
			G.HitmaskCache[model] = {"hitmask":mask,"renderoffsetx":self.renderoffsetx,"width":self.width,"height":self.height}
		self.area = math.sqrt(self.width*self.height)
		self.pos = pygame.Rect(50,50,self.width,self.height)

class CollisionEntity: #THESE ARE JUST SIMPLE THINGS FOR MAP WALLS, FLOOR ETC
	def __init__(self,pos):
		self.pos = pos
		self.mass = 1000
		self.hitmask = None
		self.Physics = False

class WireEntity: #Modelless, collisionless, shitty husks of stupid [trigger entities]
	modelstring = None
	WireName = ""
	Outputs = None
	OutputNames = None
	def __init__(self,map,modelclass,wiredetails):
		self.Outputs = []
		wiredefaults = { #Defaults to use if we're not given specifics.
			'DefaultState':False #On or off by default.
		}
		self.wiredetails = dict(wiredetails.items() + wiredefaults.items())
		print "Wire details for " + (self.modelstring or "[trigger entity]") + ": " + str(self.wiredetails)
		if self.modelstring and os.path.exists("models/images/"+self.modelstring[:-4]+"_activated"+self.modelstring[-4:]):
			self.model_activated = pygame.image.load("models/images/"+self.modelstring[:-4]+"_activated"+self.modelstring[-4:]).convert_alpha()
		
		if modelclass+"input" in self.wiredir: self.WireInput = eval("self."+modelclass+"input")
		if modelclass+"output" in self.wiredir: self.WireOutput = eval("self."+modelclass+"output")
		self.State = False
		
		if modelclass == "wire_pad":
			print "Yep, thats a pad!"
			G.Timer(30, 0, self.WireOutput)
		
		
		self.WireName = self.wiredetails.get("WireName",None)
		if self.WireName: map.WireEntities[self.WireName] = self
		self.OutputNames = self.wiredetails.get("Outputs",None)
	
	def WireInput(self,value): pass #Will be overwritten in init
	def wire_dispenserinput(self,value,prop="sphere.png"):
		print self.id,"Got a",value
		if value: 
			print "Prop is being delivered..."
			Entity(G.CurrentMap,self.pos.x,self.pos.y + 50,prop)
	def wire_gravitierinput(self,value):
		print "Gravitier","Got a",value
		if value:
			G.CurrentMap.Gravity = self.wiredetails.get("OnGravity",(0,1))
		else: G.CurrentMap.Gravity = self.wiredetails.get("OffGravity",(0,1))
		
	def WireOutput(self,value=False): pass
	def wire_buttonoutput(self,value):
		for v in self.Outputs: v.WireInput(value)
		self.model = self.modelactivated
		G.Timer(25,1,self._unactivatemodel)
	def wire_switchoutput(self,value):
		self.State = not self.State
		if self.State: self.model = self.modelactivated
		else: self.model = self.modelnormal
		for v in self.Outputs: v.WireInput(self.State)
	def wire_padoutput(self):
		print "lookin!"
		handx, handy = self.pos.centerx, self.pos.top
		for prop in G.CurrentMap.Entities.values():
			if math.sqrt((handx - prop.pos.centerx)**2 + (handy - prop.pos.centery)**2) < 80:
				if prop.mass and prop.modelclass == "prop":
					print "modelclass: "+prop.modelclass+" is on top of me! (I'm a pad)"
					for v in self.Outputs: v.WireInput(True)
					return
		for v in self.Outputs: v.WireInput(False)
	
	wiredir = None
	def _unactivatemodel(self): self.model = self.modelnormal
WireEntity.wiredir = dir(WireEntity)

class Entity(WireEntity):
	def __init__(self,map=G.CurrentMap,x=100,y=100,model="table.png",ang=0,gravity=True,wiredetails={}):
		#pygame.sprite.Sprite.__init__(self)
		G.EntIDIncrementer += 1
		self.id = G.EntIDIncrementer
		self.velx = 0
		self.vely = 0
		self.d_ang = 0
		self.ang = float(ang)
		self.modelstring = model
		self.model = self.modelnormal = pygame.image.load("models/images/"+model).convert_alpha()
		try: self.modelactivated = pygame.image.load("models/images/"+model[:-4]+"_activated"+model[-4:]).convert_alpha()
		except pygame.error: pass
		self.model0 = self.model
		self.LastCollision = False
		map.Entities[self.id] = self
		self.modeldata = modelinfo.Models.get(self.modelstring[:-4], {"Mass":5,"Class":"prop"}) #Default table
		self.mass = self.modeldata["Mass"]
		self.rolls = self.modeldata.get("Rolls",False)
		self.friction = self.modeldata.get("Friction",1)
		
		self.Physics = self.mass != 0
		if self.Physics: map.Gravities[self.id] = self

		self.ToleratesGravity = gravity
		#self.gravity = (0,1)
		self.HasCollisions = self.modeldata.get("Physical", True)
		self.modelclass = self.modeldata["Class"]
		
		if self.modelclass[:5] == "wire_": WireEntity.__init__(self, map, self.modelclass, wiredetails) #Become wire!
		
		if model in G.HitmaskCache: 
			tab = G.HitmaskCache[model]
			self.hitmask,self.renderoffsetx,self.width,self.height = tab["hitmask"],tab["renderoffsetx"],tab["width"],tab["height"]
		else: #Hasn't been generated yet
			mask=[]
			image = pygame.image.load("models/images/"+model) #Need an unconverted one
			width, height = image.get_size()
			rangeheight = range(height)
			for xrow in range(width):
				temp = []
				for yrow in rangeheight:
					pixel = image.get_at((xrow,yrow))
					temp.append(not (pixel[0]==0 and pixel[1]==0 and pixel[2]==0))
				mask.append(tuple(temp)) #For some reason tuples are faster at this layer
			for xrow in mask:
				if True in mask[0]: break #Trim off excess width before the model actually starts
				else: mask.pop(0)
			self.renderoffsetx = width - len(mask)
			for xrow in mask:
				if True in mask[-1]: break #After
				else: mask.pop()
			self.hitmask = mask
			self.width, self.height = len(self.hitmask), len(self.hitmask[0])
			G.HitmaskCache[model] = {"hitmask":mask,"renderoffsetx":self.renderoffsetx,"width":self.width,"height":self.height}
		self.area = math.sqrt(self.width*self.height)
		self.pos = pygame.Rect(x,y,self.width,self.height)
		if self.HasCollisions: map.Collisions.append(self)

def checkcollision(ent,velx=0,vely=0):
	pos,hitmask = ent.pos,ent.hitmask
	"""if ent.LastCollision:
		colpos, colhitmask = ent.LastCollision.pos, ent.LastCollision.hitmask
		hitrect = pos.clip(colpos) #hitrect is now only the parts of pos and colpos which intersect
		x1,y1,x2,y2 = hitrect.x-pos.x,hitrect.y-pos.y,hitrect.x-colpos.x,hitrect.y-colpos.y
		for x in xrange(hitrect.width): #Width is usually min(E1.width, E2.width) or less
			for y in xrange(hitrect.height): #Height is usually 5-10.
				if hitmask[x1+x][y1+y] and (not colhitmask or colhitmask[x2+x][y2+y]):
					foundhit=True
					ColUpwards = True
					for i in range(int(abs(vely))):
						pos.y += cmp(vely,0)
						hitrect = pos.clip(colpos)
						x1,y1,x2,y2 = hitrect.x-pos.x,hitrect.y-pos.y,hitrect.x-colpos.x,hitrect.y-colpos.y
						foundhit=False
						for x in xrange(hitrect.width):
							for y in xrange(hitrect.height):
								if hitmask[x1+x][y1+y] and (not colhitmask or colhitmask[x2+x][y2+y]): 
									foundhit=True; break
							if foundhit: break
						if not foundhit: break
					if foundhit:
						for i in range(int(abs(velx))):
							pos.x += cmp(velx,0)
							hitrect = pos.clip(colpos)
							x1,y1,x2,y2 = hitrect.x-pos.x,hitrect.y-pos.y,hitrect.x-colpos.x,hitrect.y-colpos.y
							foundhit=False
							for x in xrange(hitrect.width):
								for y in xrange(hitrect.height):
									if hitmask[x1+x][y1+y] and (not colhitmask or colhitmask[x2+x][y2+y]): 
										foundhit=True; break
								if foundhit: break
							if not foundhit: ColUpwards = False; break
					return ent.LastCollision, ColUpwards
	"""
	for colent in G.CurrentMap.Collisions: #Look through all collisionboxes, grabbing a Rect and a Hitmask.
		if ent == colent: continue #Don't collide with yourself stupid.
		colpos = colent.pos
		if pos.right > colpos.left and pos.left < colpos.right and pos.bottom > colpos.top and pos.top < colpos.bottom: #<-- Very efficient! 
			#The preliminary boundingbox filter. If we get this far, it means the squares around the entities are colliding.
			hitrect = pos.clip(colpos) #hitrect is now only the parts of pos and colpos which intersect
			x1,y1,x2,y2 = hitrect.x-pos.x,hitrect.y-pos.y,hitrect.x-colpos.x,hitrect.y-colpos.y
			colhitmask = colent.hitmask
			for x in xrange(hitrect.width): #Width is usually min(E1.width, E2.width) or less
				for y in xrange(hitrect.height): #Height is usually 5-10.
					if hitmask[x1+x][y1+y] and (not colhitmask or colhitmask[x2+x][y2+y]): 
						#The secondary pixel-perfect filter. This means a collision has DEFINATELY occured. The following backs E1 away from E2.
						ent.LastCollision = colent
						foundhit=True
						ColUpwards = True
						for i in range(int(abs(vely))):
							pos.y += cmp(vely,0)
							hitrect = pos.clip(colpos)
							x1,y1,x2,y2 = hitrect.x-pos.x,hitrect.y-pos.y,hitrect.x-colpos.x,hitrect.y-colpos.y
							foundhit=False
							for x in xrange(hitrect.width):
								for y in xrange(hitrect.height):
									if hitmask[x1+x][y1+y] and (not colhitmask or colhitmask[x2+x][y2+y]): 
										foundhit=True; break
								if foundhit: break
							if not foundhit: break
						if foundhit:
							for i in range(int(abs(velx))):
								pos.x += cmp(velx,0)
								hitrect = pos.clip(colpos)
								x1,y1,x2,y2 = hitrect.x-pos.x,hitrect.y-pos.y,hitrect.x-colpos.x,hitrect.y-colpos.y
								foundhit=False
								for x in xrange(hitrect.width):
									for y in xrange(hitrect.height):
										if hitmask[x1+x][y1+y] and (not colhitmask or colhitmask[x2+x][y2+y]): 
											foundhit=True; break
									if foundhit: break
								if not foundhit: ColUpwards = False; break
						return ent.LastCollision, ColUpwards
	return None, None