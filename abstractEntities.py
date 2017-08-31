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
    ''' Master class for any object that interacts non-trivially with the 
        game manager reference and interaction, sql-ready IDs. All other 
        attributes are specifically excluded, and contains no functions of 
        its own. '''
    def __init__(ent, gm):
        ''' Usage: use this as a super, provide a game manager GM, and 
        that's it! '''
        gm.uniq_id_counter = gm.uniq_id_counter + 1
        gm.entities[gm.uniq_id_counter] = ent
        ent.uniq_id = gm.uniq_id_counter
        ent.gm = gm
        ent.species = 'Stub None you must override!! : Entity'
        ent.has_logic=False

class VisualStepAgent(Entity):
    ''' VisualStepAgent: an abstract super class that structures the 
    fundamentals of entities that move and give imagery in the game world 
    environment. '''
    def __init__(ta, gm, init_ppos=None, init_tpos=None):
        Entity.__init__(ta, gm)
        if not init_tpos: init_tpos = divvec(init_ppos, ta.gm.ts())
        ta.species += '> Stub: VisualStepAgent'
        ta.initialized=False
        ta.master=True
        ta.store_reservations=False
        ta.image_offset = DEFAULT_IMAGE_OFFSET # change manually per subclass.
        gm.notify_new_agent(ta, tpos=init_tpos)

    ''' set_img and get_pstep: these are the two core functionalities that 
        VisualStepAgents must have. You must implement them. '''
    @abc.abstractmethod
    def set_img(ta, img_info): raise Exception("Stub Error!")
    @abc.abstractmethod
    def get_pstep(ta): raise Exception("Stub Err! Return 2-ple of nonneg ints.")


    def _scale_pvec(ta, pvec): 
        ''' _scale_pvec: convenience function that yields a converted 
        version of a vector. '''
        return multvec(ta.get_pstep(), X)
    # Local positions should be phased out before being sent to the game manager.

    def _set_new_ppos(ta, ppos, sp=None): 
        ''' _set_new_ppos: Internal motion function for motion. 
        Developer: please use THIS. '''
        if not (ta.initialized or sp=='initializing'): 
            raise Exception("Not initialized")
        if not andvec(ta.get_pstep(),'>=',0): raise Exception("Factor not set.")
        if ta.store_reservations and ta.gm.notify_pmove(ta.uniq_id, ppos): 
            ta._logic.update_global('most recently reserved', \
                                    divvec(ppos,ta.gm.ts()))
        
    
    def move_in_direction(ta, delta_xy):
        ''' move_in_direction: user-facing function meant to take, 
            specifically, Motion Actions. The type of agent (Pixel~, 
            Tile~, Step~) converts unit vectors into appropriate 
            pixel-conforming motions. Call via Logic if applicable.'''
        p= addvec(multvec(ta.get_pstep(), delta_xy), 
                ta._logic.view_sensor("ppos", agent_id=ta.uniq_id))
        ta._set_new_ppos(p)

    
    def get_tpos(ta):  
        '''public access method: get the gm's standard current tile pos.'''
        return ta.gm.request_tpos(ta.uniq_id)
        
    def get_ppos(ta):  # Not currently used!
        '''public access method: get the gm's standard current pixel pos.'''
        return ta.gm.request_ppos(ta.uniq_id)

    def query_image(ta): return ta._logic.view("Image")


class PixelAgent(VisualStepAgent):
    def __init__(ta, gm, init_ppos):
        VisualStepAgent.__init__(ta, gm, init_tpos=divvec(init_tpos, gm.ts()), \
                init_ppos = init_ppos)
        ta.species += '[Stub: PixelAgent]'
    def get_pstep(ta): return (1,1)


class TileAgent(VisualStepAgent): 
    # Standard agent that operates in increments of TILES.
    def __init__(ta, gm, init_tpos):
        VisualStepAgent.__init__(ta, gm, init_tpos=(0,0))
        ta._set_new_ppos(multvec(init_tpos, ta.gm.ts()), sp="initializing")
        ta.species += '[Stub: TileAgent]'
    def get_pstep(ta): return ta.gm.ts()
      

class Highlighter(TileAgent):
    ''' An abstract highlighter class. Provide the <targeter> a sensor that
        returns a TPOS to put this highlighter on. '''
    def __init__(h, gm):
        TileAgent.__init__(h, gm, (0,0))
        h.default_color = (0,0,0,255)
        h.species='target'
        h.team = '--targets--'
        h.prev_position = (0,0)
        h.targeter = None;
        h.image_offset = (-2,-2)
        h.gm.notify_update_agent(h, tx=0,ty=0,px=0,py=0,\
                    team=h.team, species=h.species)

    def update_position(h): 
        ''' update_position: call every frame to update. '''
        #print 'Sense my tpos by highlighter',h,':',h.targeter.sense()
        h.gm.notify_tmove(h.uniq_id, h.targeter.sense())

    def draw_highlight(h, tile_location):
        '''  Draw a target on specified tile. '''
        try:      r,g,b,a = h.color
        except:   r,g,b,a = h.default_color
        image = pygame.Surface(h.gm.ts()).convert_alpha()
        image.fill((0,0,0,0))
        tx,ty = h.gm.tile_size
        tx = tx-2; ty=ty-2
        M = MOUSE_CURSOR_DISPL = 2; # stub!
        for i in [1,3,6,5]:
            for d in DIRECTIONS:
                rect_size = { UDIR: (tx-2*(i+1)*M, M),  
                              DDIR: (tx-2*(i+1)*M, M),
                              LDIR: (M, ty-2*(i+1)*M), 
                              RDIR: (M, ty-2*(i+1)*M) }[d]
                location = {
                    UDIR: ((i+1)*M, i*M),    DDIR: ((i+1)*M, ty-(i+1)*M), 
                    LDIR: (i*M, (i+1)*M),    RDIR: (tx-(i+1)*M, (i+1)*M), }[d]
                if rect_size[X]<=0 or rect_size[Y]<=0: continue
                s = pygame.Surface( rect_size ).convert_alpha()
                s.fill( h.color )
                image.blit( s, addvec(location,1) )
        h.display_parameters = (-1, image, addvec((1,1),\
                        multvec(tile_location,h.gm.ts())))
        return image

    def Reset(h): pass
    def PrepareAction(h): h.targeter.rescan(); return EVAL_T
    def DoAction(h): h.update_position()

