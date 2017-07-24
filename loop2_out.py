# IPython log file
import pygame, random, sys

map_num_tiles = (num_x_tiles, num_y_tiles) = (9,7)
tile_size = (tile_x_size, tile_y_size) = (48,44)
map_pix_size = (map_x, map_y) = tuple( \
        [map_num_tiles[i] * tile_size[i] for i in (0,1)])
world_center = ( map_x//2-tile_x_size//2, map_y//2-tile_y_size//2 )

pygame.init()
screen = pygame.display.set_mode(map_pix_size)
tiles = {}
tiles['a'] = pygame.image.load('./apricorn_img.png').convert_alpha()
tiles['g'] = pygame.image.load('./grass_tile_img.png').convert_alpha()
tiles['d'] = pygame.image.load('./dirt_tile_img.png').convert_alpha()
tiles['gb']= pygame.image.load('./grass_tile_img_bordered.png').convert_alpha()
tiles['db']= pygame.image.load('./grass_tile_img_bordered.png').convert_alpha() # Todo: get *actual* bordered dirt tile!
tiles['player sprite'] = pygame.image.load('./player/1.png').convert_alpha()
for tnm, t in tiles.items():
    tmp = pygame.Surface(tile_size).convert_alpha()
    pygame.transform.scale(t, tile_size, tmp)
    t.fill((255,255,255,255), None, pygame.BLEND_RGBA_MULT)
    tiles[tnm]=tmp.convert_alpha()
    
def draw_background(surface=screen, bordered=False):
    b = 'b' if bordered else ''
    for i in range(num_x_tiles): 
        for j in range(num_y_tiles):
            if random.random()<0.5:
                surface.blit(tiles['g'+b], (i*tile_x_size, j*tile_y_size))
            else:
                surface.blit(tiles['d'+b], (i*tile_x_size, j*tile_y_size))
            if i==0 or j==0 or i==num_x_tiles-1 or j==num_y_tiles-1:
                surface.blit(tiles['a'], (i*tile_x_size, j*tile_y_size))
    pygame.display.update()

draw_background()
background = pygame.Surface(map_pix_size)
draw_background(background)
raw_input()

plyr = pygame.sprite.DirtySprite()
plyr.image = tiles['player sprite']
plyr.rect = pygame.Rect( world_center, tile_size ).move((0,-tile_y_size//8))
plyr.dirty=1

all_sprites = pygame.sprite.LayeredDirty([plyr])
an_update_rect = all_sprites.draw(screen)

pygame.display.update(an_update_rect)

raw_input()
screen.blit(background,(0,0))
pygame.display.update()
raw_input()
pygame.display.update(all_sprites.draw(screen))
raw_input()
sys.exit()

def commented_out():
    all_sprites.clear(screen, screen)
    pygame.display.update(all_sprites.draw(screen))
    all_sprites.clear(screen, screen)
    all_sprites.clear(screen, redraw_background())
    all_sprites.clear(screen, screen)
    pygame.display.update(all_sprites.draw(screen))
    all_sprites
    pygame.display.update(all_sprites.draw(screen))
    screen.blit(plyr.image, (32,32))
    ''' ok, avoid doing < all_sprites.clear(screen, *) > done above -- that fucks things up '''
