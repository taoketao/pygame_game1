import pygame
from os.path import  join
from PIL import Image, ImageOps

from abstractEntities import Entity
from utilities import *

IMGS_LOC = './resources/images/'

class Display(Entity):
    def __init__(disp, gm):
        Entity.__init__(disp, gm)
        disp._init_display()
        disp._init_load_tilesize_images()
        disp._init_process_images()
        disp._init_load_free_images()
        disp.draw_background()
        disp.map_background = pygame.Surface(gm.map_pix_size)
        disp.draw_background(disp.map_background)
        disp._wipe_queues()

    def _init_display(disp):
        disp.screen = pygame.display.set_mode(disp.gm.screen_size)
        disp.screen.convert()
        hud_color = (220,220,20)
        disp.screen.fill(hud_color, rect = \
                pygame.Rect((0,disp.gm.map_y), disp.gm.hud_size))

    def _init_load_tilesize_images(disp):
        disp.imgs = {}
        ''' >>> Tiles:  '''
        for k,v in zip(['a','g','d'], ['apricorn','grass_tile','dirt_tile']):
            disp.imgs[k] = pygame.image.load(join(IMGS_LOC, 'environment',\
                            v+'_img.png')).convert_alpha()
        ''' >>> Plyr:  '''
        for i in range(12): # ...
            save_spnm = 'player sprite '+str(i+1)
            load_spnm = join(IMGS_LOC, 'player', str(i+1)+'.png')
            disp.imgs[save_spnm] = pygame.image.load(load_spnm).convert_alpha()

        ''' >>> PKMN:  '''
        for i in range(1):
            for d in ['u','d','r','l']:
                save_spnm = 'pkmn sprite '+str(i+1)+d
                load_spnm = join(IMGS_LOC, 'pkmn', str(i+1)+d+'.png')
                disp.imgs[save_spnm] = pygame.image.load(load_spnm).convert_alpha()

    def _init_load_free_images(disp):
        ''' >>> Pokeballs:  '''
        # Pokeball sizes: see moves.py.
        pball = pygame.image.load(join(IMGS_LOC, 'moves',\
                            'pokeball.png')).convert_alpha()
        pball_size = multvec(disp.gm.ts(), POKEBALL_SCALE, 'int')

#        pball_size = disp.gm.ts()
        pbimg = pygame.transform.scale(pball, pball_size)
        disp.imgs['pokeball'] = pbimg
        for i in range(PB_OPENFRAMES): # see moves.py
            pb_i = disp._get_whitened_img(pbimg, float(i)/PB_OPENFRAMES, pball_size)
            disp.imgs['pokeball-fade-'+str(i)] = pb_i


    def _init_process_images(disp):
        for tnm, t in disp.imgs.items():
            tmp = pygame.Surface(disp.gm.ts()).convert_alpha()
            pygame.transform.scale(t, disp.gm.ts(), tmp)
            t.fill((255,255,255,255), None, pygame.BLEND_RGBA_MULT)
            disp.imgs[tnm]=tmp.convert_alpha()


    def _get_whitened_img(disp, base_pygame_img, frac, size=None): 
        mode = 'RGBA'
        if not size:
            size = base_pygame_img.get_rect().size
        base = Image.frombytes(mode, size, \
                    pygame.image.tostring(base_pygame_img, mode, False))
        arr_base = np.array(base)
        arr_targ = np.copy(arr_base)
        for i in range(arr_targ.shape[0]):
            for j in range(arr_targ.shape[1]):
                    arr_targ[i,j,1] = 255
                    arr_targ[i,j,2] = 255
                    arr_targ[i,j,0] = 255
        blended = Image.blend(base, Image.fromarray(arr_targ, mode), frac)
        return pygame.image.fromstring(blended.tobytes(), size, mode)

    def draw_background(disp, targ_surface=None, update_me=True):
        if not targ_surface: targ_surface = disp.screen
        query = "SELECT px,py,base_tid,ent_tid FROM tilemap"
        for px,py,base,ent in disp.gm.db.execute(query).fetchall():
            base, ent = str(base), str(ent)
            targ_surface.blit(disp.imgs[base], (px,py))
            if not ent=='-':
                targ_surface.blit(disp.imgs[ent], (px,py))
        if update_me: pygame.display.update()

#-----------#-----------#-----------#-----------#-----------#-----------
#     Runtime functions
#-----------#-----------#-----------#-----------#-----------#-----------

# offload all pygame sprites to here?


    def queue_reset_tile(disp, pos, tpos_or_ppos='tpos'):
        if tpos_or_ppos=='tpos':    
            disp._tiles_to_reset.append(pos)
        elif tpos_or_ppos=='ppos':  
            disp._tiles_to_reset.append(divvec(pos, disp.gm.ts()))
    def queue_A_img(disp, img, ppos):
        disp._agent_update_tups.insert(0, (img, ppos) )
    def queue_E_img(disp, img, ppos):
        disp._effect_update_tups.append( (img, ppos) )
    def queue_AE_img(disp, img, ppos):
        disp._aftereffect_update_tups.append( (img, ppos) )
#        print "--------------------Queueing effect:",img,ppos

    def std_render(disp):
        if False:
            _='This chunk prints a map of what tile are updated.'
            for y in range(disp.gm.num_y_tiles):
                for x in range(disp.gm.num_x_tiles):
                    if (x,y) in disp._tiles_to_reset: print '0',
                    else: print '.',
                print ''
            print ''

        query = "SELECT base_tid,ent_tid FROM tilemap WHERE tx=? AND ty=?;"
        for tile in disp._tiles_to_reset+[(0,0)]:
            tmp = disp.gm.db.execute(query, tile).fetchone()
            if tmp==None: continue
            base,obstr = tmp
            ploc = multvec(tile, disp.gm.ts())
            disp.screen.blit(disp.imgs[base], ploc)
            if not obstr=='-':
                disp.screen.blit(disp.imgs[obstr], ploc)

        upd_ents = disp._effect_update_tups+disp._agent_update_tups
        upd_ents.sort(key=lambda x: x[1][1])
        upd_ents = disp._aftereffect_update_tups+upd_ents#+disp._effect_update_tups
        for img_str,ploc in upd_ents:
            img = disp.imgs[img_str]
            disp.screen.blit(img, ploc)
        pygame.display.update([ pygame.Rect(ppos, disp.gm.ts()) \
                                for ppos in disp._tiles_to_reset])
        disp._wipe_queues()

    # Wipe the render-update queues:
    def _wipe_queues(disp):
        disp._effect_update_tups        =[]
        disp._aftereffect_update_tups   =[]
        disp._agent_update_tups         =[]
        disp._tiles_to_reset            =[]
