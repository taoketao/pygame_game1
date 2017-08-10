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
        ent.string_sub_class = 'None Stub you must override!! : Entity'

class GhostEntity(Entity):
    # 'half-subclass' that is an entity augmented with Sprite essentials like
    # movement and localized imagery, but doesn't experience any interaction 
    # with other visual object, receptively or affectively, eg via collisions.
    def __init__(gent, gm, diff_ppos_rect_size=None):
        Entity.__init__(gent, gm)
        gent.img_size = gm.tile_size
        if diff_ppos_rect_size==None:
            gent.ppos_rect = pygame.Rect((0,0),gm.tile_size)
        else:
            gent.ppos_rect = pygame.Rect((0,0),diff_ppos_rect_size)
        gent.spr = pygame.sprite.DirtySprite()
        gent.spr.rect = gent.ppos_rect # tie these two
        gent.stepsize_x, gent.stepsize_y = 0,0
        gent.init_shift = (0,0)
        gent.img_id = None
        gent.string_sub_class = 'None Stub you must override!! : GhostEntity'

    ''' GameManager: database update '''
    # Tells the Game Manager to update my logged position in the database.
    def notify_gm_move(agent, prev_tid=NULL_POSITION, next_tid=NULL_POSITION):
        if prev_tid==None and next_tid==None:
            next_tid = agent.get_tpos()
        if prev_tid==next_tid: return
        # Otherwise, update the database to reflect the change:
        agent.gm.notify_move(prev_tid, next_tid, agent.uniq_id, \
                              agent.team, agent.string_sub_class)

    ''' Core GhostEntity movement methods '''
    # Movement method:  Set position according to tile(x,y) id 
    def _set_tpos(gent, abs_tpos):
        return gent._set_ppos(gent._tpos_to_ppos(abs_tpos))
    # Movement method:  Move position relatvely according to tile(x,y) id 
    def _move_tpos(gent, move_tid, no_log=False): 
        return gent._move_ppos(gent._tpos_to_ppos(move_tid), no_log)
    # Movement method:  Set position according to top-left pixel 
    def _set_ppos(gent, abs_ppos):
        return gent._move_ppos((abs_ppos[X]-gent.ppos_rect.x, \
                                abs_ppos[Y]-gent.ppos_rect.y  ))
    # Movement method:  Move position according to top-left pixel
    #                   This is the <base> method. Updates gm. 
    #                   Return value: check OOB. 
    def _move_ppos(gent, move_pix, no_log=False):
        #prev_tile = gent.get_tile_under()
#        targ = (targ_x, targ_y) = gent.ppos_rect.x+move_pix[X], \
#                         gent.ppos_rect.y+move_pix[Y]
        targ = (targ_x, targ_y) = addvec(gent.ppos_rect.center, move_pix)
        if targ_x<0 or targ_x>gent.gm.map_x or \
                            targ_y<0 or targ_y>gent.gm.map_y:
            return 'out of bounds'
        mov_tid = gent._ppos_to_tpos(targ)
        gent.ppos_rect.move_ip(move_pix)
        gent.spr.dirty=1
        if not no_log: 
            prev_tile = gent.get_tpos(addvec(gent.get_ppos(), \
                                divvec(gent.ppos_rect.size,2)))
            #gent.gm.notify_move(prev_tid, mov_tid, gent.uniq_id)
            gent.gm.notify_move(gent)
#            gent.notify_gm_move(prev_tile, mov_tid)
#        gent.gm.notify_move(prev_tile, targ, gent.uniq_id, gent.team,\
#                gent.string_sub_class)
        return 'success'

    
    ''' Arithmetic conversion utilities '''
    # Conversion method: take pixel coords to (proper) tile coords
    def _ppos_to_tpos(gent, ppos):
        return multvec(ppos, gent.gm.tile_size, '//')
    # Conversion method: take tile coords to pixel coords
    def _tpos_to_ppos(gent, tpos):
        return multvec(tpos, gent.gm.tile_size, int)

    ''' GET field access '''
    # Get methods: get my coords as Tile Rect
    def get_tpos_rect(gent): 
        return pygame.Rect(gent._ppos_to_tpos(gent.ppos_rect), (1,1))
    def get_ppos_rect(gent): return gent.ppos_rect
    def get_ppos(gent): return gent.ppos_rect.topleft
    def get_tpos(gent, targp=None): 
        return gent._ppos_to_tpos(targp if targp else gent.get_ppos())
    # Get utility: get the tile under (me, target pixel position, plus coords)
    def get_position(gent):
        return gent._ppos_to_tpos(gent.get_center())

    def get_center(gent, targ=None):
        return divvec(addvec(gent.ppos_rect.center, gent.ppos_rect.midbottom),2)
    def get_bottom(gent, tile=True):
        if tile: return gent._ppos_to_tpos(gent.ppos_rect.midbottom)
        return gent.ppos_rect.midbottom

    def get_ppos_center(gent): return gent.spr.rect.center
    def __get_tpos_under(gent): 
        t = gent._ppos_to_tpos(pygame.Rect(gent.ppos_rect.midbottom, \
                gent.gm.tile_size).move(gent.init_shift))
        return (t[X],t[Y])


class Agent(GhostEntity):
    # AGENT: A subclass of GhostEntity that characterizes identifiable and 
    # interactive game objects.  Key components are a robust positioning and 
    # movement system & localized image with pygame Sprite functionality -- 
    # inherited from the GhostEntity -- and teams and collision control.
    def __init__(agent, gm, team):
        GhostEntity.__init__(agent, gm)
        agent.team = team
        agent.coll = None
        agent.coll_check_range = (None, -1)
            # How many blocks to check around my pos?  2tuple: (mode, value)
            #   'manh', (ceiling) manhattan distance, x+y>0, in tile-ids.
            #   'eucl', (ceiling) euclidean distance, sqrt(xx+yy)>0, in tile-ids.
            #   'list', a list of tile_id pairs to check relative to agent collider.
            # Implement this utility if efficiency becomes an issue - Decrease the 
            #   number of queries by moving the agents by O(map_num_tiles) by only
            #   checking nearby tiles for collision.
        agent.img_id = None
        agent.string_sub_class = 'None Stub you must override!! : Agent'

    ''' Agent movement methods: thin wrappers over GhostEntity movement '''
    def set_tpos(agent, abs_tpos):
        res = agent._set_tpos(abs_tpos)
        if res=='success': agent._update_coll()
        return res
    def move_tpos(agent, move_tid, no_log=False): 
        res = agent._move_tpos(move_tid, no_log)
        if res=='success': agent._update_coll()
        return res
    def set_ppos(agent, abs_ppos):
        res = agent._set_ppos(abs_ppos)
        if res=='success': agent._update_coll()
        return res
    def move_ppos(agent, move_pix):
        res = agent._move_ppos(move_pix)
        if res=='success':
            agent._update_coll()
        return res

    @abc.abstractmethod 
    def _update_coll(ego): raise Exception("ABC")
    @abc.abstractmethod 
    def moveparams_to_steps(ego,dirs): raise Exception("ABC")

    ''' Move validation for collision, by querying blockers in gm.db '''
    # utility: validate many possible move-indicators. (#function programming?)
    def _validate_multi_move(agent, parameter, debug=False, c='red'):
        results = []
        for vi,v in enumerate(parameter):
            p_tmp = [0]*len(parameter)
            p_tmp[vi]=v
            single_res = agent.validate_move(p_tmp, debug, c)
            results .append( single_res[vi] )
        return results
            
     #  Validate_move: given an move attempt by this agent, 'fix' move. 
     #- Parameter should be a binary vector of possible moves.
     #- What <parameter> represents depends on the subclass's definition
     #  of method moveparams_to_steps. 
    def validate_move(agent, parameter, debug=False, c='red'):
        if not any(parameter): return parameter # an easy optimization
        params = list(parameter[:])
        if sum(params)>1:
            return agent._validate_multi_move(params,debug,c)
        attmpt_step = agent.coll.move(agent.moveparams_to_steps(params))
        for block_r in agent.gm.get_agent_blocks(agent):
            if debug: agent.gm._Debug_Draw_Rect_border(block_r, render=False)
            if not block_r.colliderect(attmpt_step): continue
            if block_r.x < agent.ppos_rect.x:    params[LDIR] = False
            if block_r.x > agent.ppos_rect.x:    params[RDIR] = False
            if block_r.y < agent.ppos_rect.y:    params[UDIR] = False
            if block_r.y > agent.ppos_rect.y:    params[DDIR] = False
        if debug: agent.gm._Debug_Draw_Rect_border(attmpt_step,c=c)
        if not any(params) and any(parameter) and \
                    agent.string_sub_class=='plyr': # What does this do?
            agent.gm.prev_e=parameter
        return params




DEFAULT_MOVE_SCALE = 0.15 # ...tiles wide/high
class Move(GhostEntity):
    def __init__(mv, gm, parent, move_rect_size):
        GhostEntity.__init__(mv, gm, diff_ppos_rect_size = \
                                     move_rect_size)
        mv.parent = parent
    
    ''' Update move method: for being called by Game Manager. '''
    @abc.abstractmethod
    def update_move(mv, **kwargs): raise Exception("ABC")
    @abc.abstractmethod
    def kill_self(mv): raise Exception("ABC")
