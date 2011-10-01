import pygame
def LoadTiledImage(filepath):
	frames=[]
	Img = pygame.image.load(filepath)
	w,h = Img.get_size()
	tilewidth = w / 5.0
	Img.set_colorkey((0,0,0))
	for x in range(5):
		frames.append(Img.subsurface((x * tilewidth, 0, tilewidth, h)))
	return frames