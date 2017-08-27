'''
abstractEntities.py:
Implements backend abstract classes for all game objects. A legend of sorts.
- Entity: the base object that anything spawnable should take.
- VisualStepAgent: an agent super that takes steps and maintains an image.
- PixelAgent: a VisualStepAgent whose steps are one pixel.
- TileAgent: a VisualStepAgent whose steps are one game tile.
'''

import pygame, abc

from utilities import *


class Entity(object):
    ''' Master class for any object that interacts non-trivially with the broader
    system; a common protocol for access by others. Key components: game 
    manager reference and interaction, sql-ready IDs. All other attributes 
    are specifically excluded, and contains no functions of its own. '''
    def __init__(ent, gm):
        ''' Usage: use this as a super, provide a game manager GM, and that's it! '''
        gm.uniq_id_counter = gm.uniq_id_counter + 1
        gm.entities[gm.uniq_id_counter] = ent
        ent.uniq_id = gm.uniq_id_counter
        ent.gm = gm
        ent.species = 'Stub None you must override!! : Entity'
        ent.has_logic=False

class VisualStepAgent(Entity):
    ''' VisualStepAgent: an abstract super class that structures the fundamentals 
            of entities that move and give imagery in the game world environment. '''
    def __init__(ta, gm, init_ppos=None, init_tpos=None):
        Entity.__init__(ta, gm)
        if not init_tpos: init_tpos = divvec(init_ppos, ta.gm.ts())
        ta.species += '> Stub: VisualStepAgent'
        ta.initialized=False
        ta.store_reservations=False
        ta.image_offset = DEFAULT_IMAGE_OFFSET # Please change manually per subclass.
        gm.notify_new_agent(ta, tpos=init_tpos)

    ''' set_img and get_pstep: these are the two core functionalities that 
        VisualStepAgents must have. You must implement them. '''
    @abc.abstractmethod
    def set_img(ta, img_info): raise Exception("Stub Error!")
    @abc.abstractmethod
    def get_pstep(ta): raise Exception("Stub Err! Return 2-tuple of nonneg ints.")


    def _scale_pvec(ta, pvec): 
        ''' _scale_pvec: convenience function that yields a converted version of a vector. '''
        return multvec(ta.get_pstep(), X)
    # Local positions should be phased out before being sent to the game manager.

    def _set_new_ppos(ta, ppos, sp=None): 
        ''' _set_new_ppos: Internal motion function for motion. Developer: please use THIS. '''
        if not (ta.initialized or sp=='initializing'): raise Exception("Not initialized")
        if not andvec(ta.get_pstep(),'>=',0): raise Exception("Factor not set.")
        if ta.store_reservations and ta.gm.notify_pmove(ta.uniq_id, ppos): 
            ta._logic.update_global('most recently reserved', divvec(ppos,ta.gm.ts()))
        
    
    def move_in_direction(ta, delta_xy):
        ''' move_in_direction: user-facing function meant to take, specifically, Motion 
                Actions. The type of agent (Pixel~, Tile~, Step~) converts unit vectors
                into appropriate pixel-conforming motions. Call via Logic if applicable.'''
        p= addvec(multvec(ta.get_pstep(), delta_xy), 
                ta._logic.view_sensor("ppos", agent_id=ta.uniq_id))
        ta._set_new_ppos(p)

    
    def get_tpos(ta):  
        '''public access method: get the Game Manager's standard current tile pos.'''
        return ta.gm.request_tpos(ta.uniq_id)
        
    def get_ppos(ta):  
        '''public access method: get the Game Manager's standard current pixel pos.'''
        return ta.gm.request_ppos(ta.uniq_id)

    def query_image(ta): return ta._logic.view("Image")


class PixelAgent(VisualStepAgent):
    def __init__(ta, gm, init_ppos):
        VisualStepAgent.__init__(ta, gm, init_tpos=divvec(init_tpos, gm.ts()), \
                init_ppos = init_ppos)
        ta.species += '[Stub: PixelAgent]'
    def get_pstep(ta): return (1,1)


class TileAgent(VisualStepAgent): # Standard agent that operates in increments of TILES.
    def __init__(ta, gm, init_tpos):
        VisualStepAgent.__init__(ta, gm, init_tpos=(0,0))
        ta._set_new_ppos(multvec(init_tpos, ta.gm.ts()), sp="initializing")
        ta.species += '[Stub: TileAgent]'
    def get_pstep(ta): return ta.gm.ts()
      
