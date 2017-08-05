import pygame, sys, abc
import numpy as np
from PIL import Image

from utilities import *
from agents import GhostEntity

# Pokeball instance parameters:
POKEBALL_SCALE = 0.15
POKEBALL_SPEED_PCT_PER_FRAME = 0.15
PB_STAGE0, PB_STAGE1, PB_STAGE2 = 0,1,2
PB_NSTAGES = 3
PB_OPENFRAMES = 40.0

class Move(GhostEntity):
    def __init__(mv, gm, parent):
        GhostEntity.__init__(mv, gm, diff_ppos_rect_size = \
                                multvec(gm.tile_size, POKEBALL_SCALE))
        mv.parent = parent
    
    @abc.abstractmethod
    def update_move(mv, **kwargs): raise Exception("ABC")
    @abc.abstractmethod
    def set_img(mv, img): raise Exception("ABC")

class Pokeball(Move):
    #def __init__(mv_tpb, gm, pkmn_info, thrower_tpos, targ_tpos):
    def __init__(mv_tpb, gm, pkmn_info, thrower_ppos, targ_ppos):
        Move.__init__(mv_tpb, gm, gm.Plyr)
        mv_tpb.team = 'plyr'
#        mv_tpb.cur_tick = mv_tpb.gm.last_tick
        
#        mv_tpb.img = Image.frombytes("RGBA",gm.imgs['pokeball'].get_rect().size,\
#                    pygame.image.tostring(gm.imgs['pokeball'],"RGBA",False))
#        targ_img = np.array(mv_tpb.img.copy())
#        targ_img[targ_img>0] = 255
#        mv_tpb.targ_img = Image.fromarray(targ_img)
#
#        mv_tpb.spr.image = pygame.image.fromstring(mv_tpb.img.tobytes(), mv_tpb.img.size, mv_tpb.img.mode)
        mv_tpb.spr.image = gm.imgs['pokeball']
        mv_tpb.spr.rect = mv_tpb.spr.image.get_rect()
        mv_tpb.spr.rect = mv_tpb.get_ppos_rect()
        mv_tpb._set_ppos(thrower_ppos)
        mv_tpb.spr.dirty=1
        #gm.screen.blit(mv_tpb.spr.image, mv_tpb.spr.rect)

#        mv_tpb.open_img_spr = gm.imgs['pokeball-wh']
#        print 256/(PB_OPENFRAMES**2)
#        mv_tpb.open_img_spr.set_alpha(256/PB_OPENFRAMES)

        mv_tpb.initloc = thrower_ppos
        mv_tpb.targ = sub_aFb(divvec(mv_tpb.spr.rect.size,2), targ_ppos)
        mv_tpb.unit_move = multpos( addpos(thrower_ppos, mv_tpb.targ, 'aFb'), \
                            POKEBALL_SPEED_PCT_PER_FRAME)
        mv_tpb.travel_dist = dist(mv_tpb.initloc, mv_tpb.targ, 'eucl') 

        mv_tpb.stage = PB_STAGE0

    def update_move(mv_tpb):
#        prev_tick = mv_tpb.cur_tick
#        this_tick = mv_tpb.gm.last_tick
#        delt_tick = 1000.0/(this_tick - prev_tick)
#        print delt_tick, mv_tpb.gm.fps, mv_tpb.gm.fps/delt_tick
        if mv_tpb.stage==PB_STAGE0 and mv_tpb.travel_dist <= \
                dist(mv_tpb.initloc, mv_tpb.get_ppos_rect(), 'eucl'):
            mv_tpb.stage = PB_STAGE1
            mv_tpb.open_itr = 0;#PB_OPENFRAMES
            mv_tpb._set_ppos( addvec(mv_tpb.targ, divvec(mv_tpb.spr.rect.size,2)) )
            mv_tpb.spr.dirty=1

            mv_tpb.gm._notify_catching_tile(mv_tpb.get_tile_under(mv_tpb.targ), mv_tpb)

        elif mv_tpb.stage==PB_STAGE0: # Throw pokeball
            #mv_tpb._move_ppos( multvec(mv_tpb.unit_move, mv_tpb.gm.fps/delt_tick) )
            mv_tpb._move_ppos( mv_tpb.unit_move )
            mv_tpb.spr.dirty=1
        elif mv_tpb.stage == PB_STAGE1: # Pokeball is opening
            mv_tpb.pokeball_open() #delt_tick )
        elif mv_tpb.stage == PB_STAGE2: # Pokeball has finished; terminate.
            mv_tpb.pokeball_kill()
#        mv_tpb.cur_tick = this_tick

    def how_open(mv_tpb): return mv_tpb.open_itr/PB_OPENFRAMES

    def pokeball_open(mv_tpb):#, dt):
        mv_tpb.open_itr += 1
        #if mv_tpb.open_itr < PB_OPENFRAMES:
        if mv_tpb.open_itr < PB_OPENFRAMES:
            mv_tpb.spr.image = mv_tpb.gm.imgs.get('pokeball-fade-'+str(mv_tpb.open_itr))
#            pil_img = Image.blend(mv_tpb.targ_img, mv_tpb.img, \
#                                    mv_tpb.open_itr/PB_OPENFRAMES)
#            mv_tpb.spr.image = pygame.image.fromstring(pil_img.tobytes(), mv_tpb.img.size, mv_tpb.img.mode)
            mv_tpb.spr.dirty=1
        else:
            mv_tpb.pokeball_kill()
        #if cur_tick-


    def pokeball_kill(mv_tpb):
        mv_tpb.gm.Plyr.set_plyr_actionable(True)
        mv_tpb.gm.move_effects.remove(mv_tpb)
        del mv_tpb

