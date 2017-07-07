import pygame, ConfigParser
import numpy as np
import pygame.locals

path='/Users/morganbryant/Desktop/Files/17/07_July/game/'

def init_config(filename):
    cp = ConfigParser.ConfigParser()
    cp.read(path+filename)
    return cp

def load_tile_table(cp, screen):
    images = {}
    for tile in cp.get('tiles','alltiles'):
        images[tile] = pygame.image.load(cp.get(tile, 'file')).convert_alpha()
        images[tile].fill((255, 255, 255, 255), None, pygame.BLEND_RGBA_MULT)

    mapcode = cp.get("map","map")
    row, col = int(cp.get("mapsize",'x')), int(cp.get('mapsize','y'))
    gamemap = np.empty((row, col))
    curR, curC = 0,0
    for char in mapcode:
        if char=='\n': 
            curC += 1
            curR = 0
            continue
        gamemap[curR,curC] = cp.get(char, 'code')
        if char=='a':
            screen.blit(images['g'], (1+17*curR, 1+17*curC))
        screen.blit(images[char], (1+17*curR, 1+17*curC))
        curR += 1
    print(gamemap)
            
    
if __name__=='__main__':
    pygame.init()
    cp = init_config('./config1.ini')
    X, Y = int(cp.get("mapsize",'x')), int(cp.get('mapsize','y'))
    screen = pygame.display.set_mode((1+17*X,1+17*Y))
    screen.fill((0,0,0))
    load_tile_table(cp, screen)
    pygame.display.flip()
    while pygame.event.wait().type != pygame.locals.QUIT:
        pass
