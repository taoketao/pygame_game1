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
        ent.has_logic=False

class VisualStepAgent(Entity):
    def __init__(ta, gm, init_ppos=None, init_tpos=None, belt_init=None):
#        print ta, gm, init_ppos, init_tpos, belt_init
        Entity.__init__(ta, gm)
        if not init_tpos: init_tpos = divvec(init_ppos, ta.gm.ts())
        ta.species = 'Stub: VisualStepAgent'
        ta.initialized=False
        ta.image_offset = DEFAULT_IMAGE_OFFSET # Please change manually elsewhere for now.
#        ta.img_offset = multvec(gm.ts(), (0.4,0.9))
        gm.notify_new_agent(ta, tpos=init_tpos)

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
    def _set_new_ppos(ta, ppos, sp=None): 
        print 'MOVING'
        if not (ta.initialized or sp=='initializing'): raise Exception("Not initialized")
        if not andvec(ta.get_pstep(),'>=',0): raise Exception("Factor not set.")
#        if ta._logic.view("ppos")==loc: return # optimization?
        ta.gm.notify_pmove(ta.uniq_id, ppos)
    
    # Public access function: move in Delta(X,Y) *local units*. Call by Logic.
    def move_in_direction(ta, delta_xy):
        p= addvec(multvec(ta.get_pstep(), delta_xy), 
                ta._logic.view_sensor("ppos", agent_id=ta.uniq_id))
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
        VisualStepAgent.__init__(ta, gm, init_tpos=(0,0), init_ppos=(0,0), \
                                                         belt_init=belt_init)
        ta._set_new_ppos(multvec(init_tpos, ta.gm.ts()), sp="initializing")
#        VisualStepAgent.__init__(ta, gm, init_tpos=init_tpos, \
#                init_ppos = multvec(init_tpos, gm.ts()), belt_init=belt_init)
        ta.species += '[Stub: TileAgent]'
    def get_pstep(ta): return ta.gm.ts()
      
