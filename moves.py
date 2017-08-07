import pygame, sys, abc
import numpy as np
from PIL import Image

from utilities import *
from abstractEntities import Move

# Pokeball instance parameters:
POKEBALL_SCALE = 0.15
POKEBALL_SPEED_PCT_PER_FRAME = 0.15
PB_STAGE0, PB_STAGE1, PB_STAGE2 = 0,1,2
PB_NSTAGES = 3
PB_OPENFRAMES = 30.0

class Pokeball(Move):
    #def __init__(mv_tpb, gm, pkmn_info, thrower_tpos, targ_tpos):
    def __init__(mv_tpb, gm, pkmn_info, thrower_ppos, targ_ppos):
        pbsize = multvec(gm.tile_size, POKEBALL_SCALE)
        Move.__init__(mv_tpb, gm, gm.Plyr, pbsize)
        mv_tpb.team = 'plyr'
        mv_tpb.string_sub_class = 'move:throw'
        mv_tpb.spr.image = gm.imgs['pokeball']
        mv_tpb.spr.rect = mv_tpb.spr.image.get_rect()
        mv_tpb.spr.rect = mv_tpb.get_ppos_rect()
        #mv_tpb.spr.rect = pygame.Rect((0,0), pbsize)
        #mv_tpb.spr.rect.topleft = mv_tpb.get_ppos()
        mv_tpb._set_ppos(thrower_ppos)
        mv_tpb.spr.dirty=1

        mv_tpb.initloc = thrower_ppos
        #mv_tpb.targ = sub_aFb(divvec(mv_tpb.spr.rect.size,2), targ_ppos)
        mv_tpb.targ = sub_aFb(mv_tpb.spr.rect.size,\
                sub_aFb(divvec(mv_tpb.gm.tile_size,2), targ_ppos))
        #mv_tpb.targ = sub_aFb(mv_tpb.spr.rect.size, targ_ppos) # Raw mouse position
        mv_tpb.unit_move = multpos( addpos(thrower_ppos, mv_tpb.targ, 'aFb'), \
                            POKEBALL_SPEED_PCT_PER_FRAME)
        mv_tpb.travel_dist = dist(mv_tpb.initloc, mv_tpb.targ, 'eucl') 
#        print thrower_ppos, '->',targ_ppos, mv_tpb.travel_dist

        mv_tpb.stage = PB_STAGE0


    def update_move(mv_tpb):
        if mv_tpb.stage==PB_STAGE0 and mv_tpb.travel_dist <= \
                dist(mv_tpb.initloc, mv_tpb.get_ppos_rect().center, 'eucl'):
            mv_tpb.stage = PB_STAGE1
            mv_tpb.open_itr = 0;#PB_OPENFRAMES
            #mv_tpb._set_ppos( addvec(mv_tpb.targ, divvec(mv_tpb.spr.rect.size,2)) )
#            mv_tpb._set_ppos( addvec(mv_tpb.targ, divvec(mv_tpb.spr.rect.size,2),'bFa') )
            mv_tpb._set_ppos( mv_tpb.targ)
            mv_tpb.spr.dirty=1

#            mv_tpb.gm.notify_catching(mv_tpb.get_tpos(mv_tpb.targ), mv_tpb)

        elif mv_tpb.stage==PB_STAGE0: # Throw pokeball
            #mv_tpb._move_ppos( multvec(mv_tpb.unit_move, mv_tpb.gm.fps/delt_tick) )
            mv_tpb._move_ppos( mv_tpb.unit_move, no_log=True)
            mv_tpb.spr.dirty=1
        elif mv_tpb.stage == PB_STAGE1: # Pokeball is opening
            mv_tpb.pokeball_open() #delt_tick )
        elif mv_tpb.stage == PB_STAGE2: # Pokeball has finished; terminate.
            mv_tpb.pokeball_kill()

    def how_open(mv_tpb): return mv_tpb.open_itr/PB_OPENFRAMES

    def pokeball_open(mv_tpb):#, dt):
        mv_tpb.open_itr += 1
        #if mv_tpb.open_itr < PB_OPENFRAMES:
        if mv_tpb.open_itr >= PB_OPENFRAMES:
            mv_tpb.pokeball_kill()
            return
        mv_tpb.spr.image = mv_tpb.gm.imgs['pokeball-fade-'+str(mv_tpb.open_itr)]
        mv_tpb.spr.dirty=1
        tid = tid_x, tid_y = mv_tpb._ppos_to_tpos(mv_tpb.get_center())
        tid = tid_x, tid_y = mv_tpb.get_tpos()
        occ = mv_tpb.gm.get_tile_occupants(tid)
        catches = []
        for o in occ:
            a_type, uniq_id, team = o
            if a_type=='pkmn' and team=='wild':
                catches.append(uniq_id)
        mv_tpb.gm.notify_catching(mv_tpb._ppos_to_tpos(mv_tpb.get_center()), \
                mv_tpb, catches)




    def pokeball_kill(mv_tpb):
        mv_tpb.gm.Plyr.set_plyr_actionable(True)
        mv_tpb.gm.move_effects.remove(mv_tpb)
#        mv_tpb.notify_gm_move(mv_tpb.get_tpos(), NULL_POSITION)
        mv_tpb.gm.notify_kill(mv_tpb)
        del mv_tpb

    def kill_self(mv_tpb): mv_tpb.mv_tpb.pokeball_kill()

