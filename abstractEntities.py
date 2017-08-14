'''
abstractEntities.py:
Implements backend abstract classes for objects. A legend of sorts.
- Entity: the base object that anything spawnable should take.
- GhostEntity: the base object that has sprites.
- Agent: the base object with sprites and colliders.
- Move: the base object class for anything that is spawned by Game
    objects for a specific (visible) purpose and later destroyed.
'''

import pygame, abc

from utilities import *


class Entity(object):
    # Master class for any object that interacts non-trivially with the broader
    # system. Key components: game manager reference and interaction, sql-ready
    # IDs. Attributes of Sprites are specifically excluded.
    def __init__(ent, gm):
        gm.uniq_id_counter = gm.uniq_id_counter + 1
        gm.entities[gm.uniq_id_counter] = ent
        ent.uniq_id = gm.uniq_id_counter
        ent.gm = gm
        ent.species = 'Stub None you must override!! : Entity'

#class GhostEntity(Entity):
#    # 'half-subclass' that is an entity augmented with Sprite essentials like
#    # movement and localized imagery, but doesn't experience any interaction 
#    # with other visual object, receptively or affectively, eg via collisions.
#    def __init__(gent, gm, diff_ppos_rect_size=None):
#        Entity.__init__(gent, gm)
#        gent.img_size = gm.tile_size
#        if diff_ppos_rect_size==None:
#            gent.ppos_rect = pygame.Rect((0,0),gm.tile_size)
#        else:
#            gent.ppos_rect = pygame.Rect((0,0),diff_ppos_rect_size)
#        gent.spr = pygame.sprite.DirtySprite()
#        gent.spr.rect = gent.ppos_rect # tie these two
#        gent.stepsize_x, gent.stepsize_y = 0,0
#        gent.init_shift = (0,0)
#        gent.img_id = None
#        gent.species = 'Stub: GhostEntity'
#
#    ''' GameManager: database update '''
#    # Tells the Game Manager to update my logged position in the database.
#    def notify_gm_move(agent, prev_tid=NULL_POSITION, next_tid=NULL_POSITION):
#        if prev_tid==None and next_tid==None:
#            next_tid = agent.get_tpos()
#        if prev_tid==next_tid: return
#        # Otherwise, update the database to reflect the change:
#        agent.gm.notify_move(prev_tid, next_tid, agent.uniq_id, \
#                              agent.team, agent.species)
#
#    ''' Core GhostEntity movement methods '''
#    # Movement method:  Set position according to tile(x,y) id 
#    def _set_tpos(gent, abs_tpos):
#        return gent._set_ppos(gent._tpos_to_ppos(abs_tpos))
#    # Movement method:  Move position relatvely according to tile(x,y) id 
#    def _move_tpos(gent, move_tid, no_log=False): 
#        return gent._move_ppos(gent._tpos_to_ppos(move_tid), no_log)
#    # Movement method:  Set position according to top-left pixel 
#    def _set_ppos(gent, abs_ppos):
#        return gent._move_ppos((abs_ppos[X]-gent.ppos_rect.x, \
#                                abs_ppos[Y]-gent.ppos_rect.y  ))
#    # Movement method:  Move position according to top-left pixel
#    #                   This is the <base> method. Updates gm. 
#    #                   Return value: check OOB. 
#    def _move_ppos(gent, move_pix, no_log=False):
#        #prev_tile = gent.get_tile_under()
##        targ = (targ_x, targ_y) = gent.ppos_rect.x+move_pix[X], \
##                         gent.ppos_rect.y+move_pix[Y]
#        targ = (targ_x, targ_y) = addvec(gent.ppos_rect.center, move_pix)
#        if targ_x<0 or targ_x>gent.gm.map_x or \
#                            targ_y<0 or targ_y>gent.gm.map_y:
#            return 'out of bounds'
#        mov_tid = gent._ppos_to_tpos(targ)
#        gent.ppos_rect.move_ip(move_pix)
#        gent.spr.dirty=1
#        if not no_log: 
#            prev_tile = gent.get_tpos(addvec(gent.get_ppos(), \
#                                divvec(gent.ppos_rect.size,2)))
#            #gent.gm.notify_move(prev_tid, mov_tid, gent.uniq_id)
#            gent.gm.notify_move(gent)
##            gent.notify_gm_move(prev_tile, mov_tid)
##        gent.gm.notify_move(prev_tile, targ, gent.uniq_id, gent.team,\
##                gent.species)
#        return 'success'
#
#    
#    ''' Arithmetic conversion utilities '''
#    # Conversion method: take pixel coords to (proper) tile coords
#    def _ppos_to_tpos(gent, ppos):
#        return multvec(ppos, gent.gm.tile_size, '//')
#    # Conversion method: take tile coords to pixel coords
#    def _tpos_to_ppos(gent, tpos):
#        return multvec(tpos, gent.gm.tile_size, int)
#
#    ''' GET field access '''
#    # Get methods: get my coords as Tile Rect
#    def get_tpos_rect(gent): 
#        return pygame.Rect(gent._ppos_to_tpos(gent.ppos_rect), (1,1))
#    def get_ppos_rect(gent): return gent.ppos_rect
#    def get_ppos(gent): return gent.ppos_rect.topleft
#    def get_tpos(gent, targp=None): 
#        return gent._ppos_to_tpos(targp if targp else gent.get_ppos())
#    # Get utility: get the tile under (me, target pixel position, plus coords)
#    def get_position(gent):
#        return gent._ppos_to_tpos(gent.get_center())
#
#    def get_center(gent, targ=None):
#        return divvec(addvec(gent.ppos_rect.center, gent.ppos_rect.midbottom),2)
#    def get_bottom(gent, tile=True):
#        if tile: return gent._ppos_to_tpos(gent.ppos_rect.midbottom)
#        return gent.ppos_rect.midbottom
#
#    def get_ppos_center(gent): return gent.spr.rect.center
#    def __get_tpos_under(gent): 
#        t = gent._ppos_to_tpos(pygame.Rect(gent.ppos_rect.midbottom, \
#                gent.gm.tile_size).move(gent.init_shift))
#        return (t[X],t[Y])
#
#
#
#DEFAULT_MOVE_SCALE = 0.15 # ...tiles wide/high
#class Move(GhostEntity):
#    def __init__(mv, gm, parent, move_rect_size):
#        GhostEntity.__init__(mv, gm, diff_ppos_rect_size = \
#                                     move_rect_size)
#        mv.parent = parent
#    
#    ''' Update move method: for being called by Game Manager. '''
#    @abc.abstractmethod
#    def update_move(mv, **kwargs): raise Exception("ABC")
#    @abc.abstractmethod
#    def kill_self(mv): raise Exception("ABC")
#
#
#
#

class VisualStepAgent(Entity):
    def __init__(ta, gm, init_ppos=None, init_tpos=None, belt_init=None):
        Entity.__init__(ta, gm)
        if not init_tpos: init_tpos = divvec(init_ppos, ta.gm.ts())

        gm.notify_new_agent(ta, init_tpos)

        ta.species = 'Stub: VisualStepAgent'
        ta.initialized=False
        ta.default_img_offset = multvec(gm.ts(), (0.3,1))

    ''' set_img and get_pstep: these are the two core functionalities that 
        VisualStepAgents must have. You must implement them. '''
    @abc.abstractmethod
    def set_img(ta, img_info): raise Exception("Stub Error!")
    @abc.abstractmethod
    def get_pstep(ta): raise Exception("Stub Err! Return 2-tuple of nonneg ints.")


    # scale: convenience function that yields a converted version of a vector.
    def _scale_pvec(ta, pvec): 
        return multvec(ta.get_pstep(), X)
    # Local positions should be phased out before being sent to the game manager.

    # Initialize: run ONCE or overwrite.
    def std_initialize(ta, species):
        if ta.initialized: raise Exception("I have already been initialized. Reset?")
        ta.species = species
        ta._belt = Belt(gm, ta, belt_init) # ? default convention - always give Belt?
        ta._logic = Logic(gm, ta, ta._belt)
   
    # Internal (gateway) motion function.
    def _set_new_ppos(ta, ppos): 
        if not ta.initialized: raise Exception("Not initialized")
        if not andvec(ta.get_pstep(),'>=',0): raise Exception("Factor not set.")
#        if ta._logic.view("ppos")==loc: return # optimization?
        ta.gm.notify_pmove(ta.uniq_id, ppos)
    
    # Public access function: move in Delta(X,Y) *local units*. Call by Logic.
    def move_in_direction(ta, delta_xy):
        p= addvec(ta._scale_pvec(delta_xy), ta._logic.access_sensor("ppos"))
        print '\t\tmoving by delta:',delta_xy,'from',ta._logic.access_sensor("ppos"),'to',p
        ta._set_new_ppos(p)

    # position for local scaling: not exactly recommended...
    def get_pos(ta): raise Exception('not implemented out of necessity')
    def get_tpos(ta):  return ta.gm.request_tpos(ta.uniq_id)
    def get_ppos(ta):  return ta.gm.request_ppos(ta.uniq_id)
    def query_image(ta): return ta._logic.view("Image")
    def query_ppos(ta): return ta._logic.view("ppos")
    def query_tpos(ta): return ta._logic.view("tpos")


class PixelAgent(VisualStepAgent):
    def __init__(ta, gm, init_ppos, belt_init=None):
        VisualStepAgent.__init__(ta, gm, init_tpos=divvec(init_tpos, gm.ts()), \
                init_ppos = init_ppos, belt_init=belt_init)
        ta.species += '[Stub: PixelAgent]'
    def get_pstep(ta): return (1,1)

class TileAgent(VisualStepAgent): # Standard agent that operates in increments of TILES.
    def __init__(ta, gm, init_tpos, belt_init=None):
        VisualStepAgent.__init__(ta, gm, init_tpos=init_tpos, \
                init_ppos = multvec(init_tpos, gm.ts()), belt_init=belt_init)
        ta.species += '[Stub: TileAgent]'
    def get_pstep(ta): return ta.gm.ts()
        

