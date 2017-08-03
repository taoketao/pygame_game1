import pygame, sys, abc
import numpy as np

from utilities import *
from agents import GhostEntity

POKEBALL_SCALE = 0.15
POKEBALL_FRAMERATE = 0.5


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

#        targ_ppos = mv_tpb.get_tile_center(targ_ppos)
    
        mv_tpb.spr.image = gm.imgs['pokeball']
        mv_tpb.spr.rect = mv_tpb.spr.image.get_rect()
        mv_tpb.spr.rect = mv_tpb.get_ppos_rect()
        print '==',mv_tpb.get_ppos_rect()
        mv_tpb.spr.dirty=1
        gm.screen.blit(mv_tpb.spr.image, mv_tpb.spr.rect)

        #thrower_ppos = subvec(multvec(mv_tpb.spr.rect.size,2,'//'), thrower_ppos)
#        thrower_ppos = addvec(divvec(mv_tpb.spr.rect.size,2), thrower_ppos, 'aFb')
#        mv_tpb._set_ppos(subvec(multvec(mv_tpb.spr.rect.size,2,'//'), thrower_ppos))
        mv_tpb._set_ppos(thrower_ppos)
#        mv_tpb._move_ppos( multpos( gm.tile_size, POKEBALL_SCALE, int) )
        mv_tpb.initloc = thrower_ppos
        print '----',targ_ppos,
        mv_tpb.targ = sub_aFb(divvec(mv_tpb.spr.rect.size,2), targ_ppos)
        mv_tpb.targ = sub_aFb(mv_tpb.spr.rect.size, targ_ppos)
        print mv_tpb.targ, mv_tpb.spr.rect.size
#        mv_tpb.targ = targ_ppos
        travel_vec = addpos(thrower_ppos, mv_tpb.targ, 'aFb')
#        mv_tpb.targ = mv_tpb.get_tile_center(targ_ppos)
        mv_tpb.unit_move = multpos(travel_vec, POKEBALL_FRAMERATE*mv_tpb.gm.fps, '/')
        mv_tpb.sign = sign_vec(travel_vec)
        mv_tpb.travel_dist = dist(mv_tpb.initloc, mv_tpb.targ, 'eucl') 
        print thrower_ppos, targ_ppos, mv_tpb.travel_dist

    def update_move(mv_tpb):
#        if mv_tpb.
#        print multvec(mv_tpb.sign, mv_tpb.targ), multvec(mv_tpb.sign, mv_tpb.get_ppos_rect().center)
        #print multvec(mv_tpb.sign, subvec(mv_tpb.targ,mv_tpb.get_ppos_rect().topleft))
#        print has_surpassed(mv_tpb.sign, mv_tpb.targ, mv_tpb.get_ppos_rect().center)
#        if has_surpassed(mv_tpb.sign, mv_tpb.targ, mv_tpb.get_ppos_rect().center):
        print mv_tpb.initloc, mv_tpb.targ, mv_tpb.get_ppos_rect().center,'\t',
        print dist(mv_tpb.initloc, mv_tpb.get_ppos_rect().center, 'eucl') , mv_tpb.travel_dist
        if dist(mv_tpb.initloc, mv_tpb.get_ppos_rect(), 'eucl') >= mv_tpb.travel_dist:
            mv_tpb.pokeball_open()
        mv_tpb.spr.dirty=1
        #mv_tpb._move_iter += 1
        mv_tpb._move_ppos( mv_tpb.unit_move)
        #mv_tpb.gm.screen.blit(mv_tpb.spr.image, mv_tpb.spr.rect)
        #if mv_tpb._move_iter>=POKEBALL_FRAMERATE*mv_tpb.gm.fps:

    def pokeball_open(mv_tpb):
        mv_tpb.gm.Plyr.set_plyr_actionable(True)
#        gm.move_effect_sprites.remove(mv_tpb)
        mv_tpb.gm.move_effects.remove(mv_tpb)
        del mv_tpb

