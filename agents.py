import pygame, random, sys
import abc
import numpy as np


''' Map Options '''
X = 0;  Y = 1

UDIR = 0;       LDIR = 1;       DDIR = 2;       RDIR = 3
UVEC=[1,0,0,0]; LVEC=[0,1,0,0]; DVEC=[0,0,1,0]; RVEC=[0,0,0,1]
DIRECTIONS = EVENTS = [UDIR, LDIR, DDIR, RDIR]
DIRNAMES = ['u','l','d','r']
NULL_POSITION = (-1,-1)

PLYR_COLL_WIDTH, PLYR_COLL_SHIFT = 0.4, 0.2
PLYR_IMG_SHIFT_INIT = 0.125
DEFAULT_STEPSIZE = 0.20

# Latencies for actions:
#PKMN_WANDER_LOW, PKMN_WANDER_HIGH = 0.4, 0.5
#PKMN_MOVE_LOW, PKMN_MOVE_HIGH = 0.8, 1.1
PKMN_WANDER_LOW, PKMN_WANDER_HIGH = 1.0,3.0
PKMN_MOVE_LOW, PKMN_MOVE_HIGH = 0.4,0.9

MOUSE_CURSOR_DISPL = 3
MOUSE_GRAD = (180,160,60)


def _dist(p1,p2,Q): 
    if Q in [1,'manh']: 
        return abs(p1[X]-p2[X])+abs(p1[Y]-p2[Y])
    if Q in [2,'eucl']: 
        return np.sqrt(np.square(p1[X]-p2[X])+np.square(p1[Y]-p2[Y]))
def _sub_aFb(a,b): return b[X]-a[X], b[Y]-a[Y]




class Entity(object):
    # Master class for any object that interacts non-trivially with the broader
    # system. Key components: game manager reference and interaction, sql-ready
    # IDs. Attributes of Sprites are specifically excluded.
    def __init__(ent, gm):
        gm.uniq_id_counter = gm.uniq_id_counter + 1
        ent.uniq_id = gm.uniq_id_counter
        ent.gm = gm
        ent.string_sub_class = 'None Stub you must override!! : Entity'

class GhostEntity(Entity):
    # 'half-subclass' that is an entity augmented with Sprite essentials like
    # movement and localized imagery, but doesn't experience any interaction 
    # with other visual object, receptively or affectively, eg via collisions.
    def __init__(gent, gm):
        Entity.__init__(gent, gm)
        gent.img_size = gm.tile_size
        gent.ppos_rect = pygame.Rect((0,0),gm.tile_size)
        gent.spr = pygame.sprite.DirtySprite()
        gent.spr.rect = gent.ppos_rect # tie these two
        gent.stepsize_x, gent.stepsize_y = 0,0
        gent.init_shift = (0,0)
        gent.img_id = None
        gent.string_sub_class = 'None Stub you must override!! : GhostEntity'

    ''' GameManager: database update '''
    # Tells the Game Manager to update my logged position in the database.
    def _notify_gm_move(agent, prev_tu=NULL_POSITION):
        next_tu = agent.get_tile_under()
        if prev_tu==next_tu: return
        # Otherwise, update the database to reflect the change:
        agent.gm._notify_move(prev_tu, next_tu, agent.uniq_id, \
                              agent.team, agent.string_sub_class)

    ''' Core GhostEntity movement methods '''
    # Movement method:  Set position according to tile(x,y) id 
    def _set_tpos(gent, abs_tpos):
        return gent._set_ppos(gent._tpos_to_ppos(abs_tpos))
    # Movement method:  Move position relatvely according to tile(x,y) id 
    def _move_tpos(gent, move_tid): 
        return gent._move_ppos(gent._tpos_to_ppos(move_tid))
    # Movement method:  Set position according to top-left pixel 
    def _set_ppos(gent, abs_ppos):
        return gent._move_ppos((abs_ppos[X]-gent.ppos_rect.x, \
                                abs_ppos[Y]-gent.ppos_rect.y  ))
    # Movement method:  Move position according to top-left pixel
    #                   This is the <base> method. Updates gm. 
    #                   Return value: check OOB. 
    def _move_ppos(gent, move_pix):
        prev_tile = gent.get_tile_under()
        targ_x, targ_y = gent.ppos_rect.x+move_pix[X], \
                         gent.ppos_rect.y+move_pix[Y]
        if targ_x<0 or targ_x>gent.gm.map_x or \
                            targ_y<0 or targ_y>gent.gm.map_y:
            return 'out of bounds'
        mov_tid = gent._ppos_to_tpos((targ_x, targ_y))
        gent.ppos_rect.move_ip(move_pix)
        gent.spr.dirty=1
        gent._notify_gm_move(prev_tile)
        return 'success'

    
    ''' Arithmetic conversion utilities '''
    # Conversion method: take pixel coords to (proper) tile coords
    def _ppos_to_tpos(gent, ppos):
        return (int(ppos[X]//gent.gm.tile_x_size), \
                int(ppos[Y]//gent.gm.tile_y_size))
    # Conversion method: take tile coords to pixel coords
    def _tpos_to_ppos(gent, tpos):
        return (int(tpos[X]*gent.gm.tile_x_size), \
                int(tpos[Y]*gent.gm.tile_y_size))

    ''' GET field access '''
    # Get methods: get my coords as Tile Rect
    def get_tpos_rect(gent): return gent._ppos_to_tpos(gent.ppos_rect)
    def get_ppos_rect(gent): return gent.ppos_rect
    # Get utility: get the tile under (me, target pixel position)
    def get_tile_under(gent, targ=None):
        if targ==None: return gent.__get_tile_under()
        return gent._ppos_to_tpos(targ)
    def __get_tile_under(gent): 
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
    def move_tpos(agent, move_tid): 
        res = agent._move_tpos(move_tid)
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


class Player(Agent):
    ''' PLAYER class: a type of Agent that is suited to represent (the single)
        player object. Attempt is to keep all relevant fields here, out of 
        the game manager's burden. Core unique attribute(s): tailored 
        animation dependent on user input. 
        '''
    def __init__(ego, gm):
        Agent.__init__(ego, gm, 'plyr')
        ego.string_sub_class = 'plyr'
        ego.coll_check_range = ('eucl',1.5) # check 8 tiles surrounding
        ego.spr = pygame.sprite.DirtySprite()
        ego.gm.agent_entities.append(ego)
        ego.spr.add( gm.plyr_team )
        ego.plyr_step_cycler = 0     # animation counter for player sprite
        ego.n_plyr_anim = gm.n_plyr_anim
        ego.n_plyr_dirs = gm.n_plyr_dirs
        ego.dirs_to_steps = ego.moveparams_to_steps
        ego.stepsize_x = DEFAULT_STEPSIZE * ego.gm.tile_x_size
        ego.stepsize_y = DEFAULT_STEPSIZE * ego.gm.tile_y_size
        ego._notify_gm_move(NULL_POSITION)

        ego.set_plyr_img(DVEC, 'init-shift')
        ego.set_ppos(ego.gm.world_pcenter)
        ego.init_shift = (0,-int(PLYR_IMG_SHIFT_INIT*ego.gm.tile_y_size//1))
        ego.move_ppos(ego.init_shift)

    def _update_coll(ego):
        ego.coll = ego.gm.deflate(ego.ppos_rect, PLYR_COLL_WIDTH, PLYR_COLL_SHIFT)

    def set_plyr_img(ego, dirs, mode=None, init_ppos=None):
        if not any(dirs): dirs[DDIR] = True # default, face down.
        ego.plyr_step_cycler = {'moving': ego.plyr_step_cycler+1, 'stopped':0,\
                'init-shift':0, 'init-noshift':0}[mode] % ego.gm.n_plyr_anim
        new_img_id = dirs.index(True)*ego.gm.n_plyr_anim+1+ego.plyr_step_cycler
        if ego.img_id==new_img_id: return
        ego.img_id = new_img_id 

        if mode[:4]=='init':
            ego.spr.image = ego.gm.imgs['player sprite 7']
        else:
            ego.spr.image = ego.gm.imgs['player sprite ' + str(ego.img_id)]
        ego.spr.rect = ego.spr.image.get_rect()
        ego.spr.rect = ego.get_ppos_rect()

    def moveparams_to_steps(ego,dirs):
        dx = (dirs[RDIR]-dirs[LDIR]) * ego.gm.smoothing * ego.stepsize_x
        dy = (dirs[DDIR]-dirs[UDIR]) * ego.gm.smoothing * ego.stepsize_y
        return (dx,dy)

    def _pick_rndm_action(ego, dirs): # subCASE: pick one of the options
        optns = [i for i in range(len(dirs)) if next_e[i]==1]
        next_e = [False]*len(dirs)
        next_e[random.choice(optns)] = True #...randomly
        return next_e

    def plyr_move(ego):
        prev_e = ego.gm.prev_e
        #next_e = ego.validate_move(ego.gm.events, debug=True) # restrict if invalid
        next_e = ego.validate_move(ego.gm.events) # restrict if invalid

        if not any(prev_e) and any(next_e): # CASE started walking
            if sum(next_e)>1:
                next_e = ego._pick_rndm_action(next_e)
            ego.move_ppos(ego.dirs_to_steps(next_e))
            ego.set_plyr_img(next_e, 'moving')
            ego.gm.prev_e = next_e
            return True
        if any(prev_e) and any(next_e) and not prev_e==next_e: # CASE walking & turning
            if sum(next_e)>1: # subCASE try: get the new option
                new = [a and not b for a,b in zip(next_e, prev_e)]
                if sum(new)>1: # subCASE except: pick one of the new options
                    optns = [i for i in range(ego.n_plyr_dirs) if new[i]==1]
                    new = [False]*ego.n_plyr_dirs
                    new[random.choice(optns)] = True
                ego.move_ppos(ego.dirs_to_steps(new))
                ego.set_plyr_img(new, 'moving')
                return True
            ego.move_ppos(ego.dirs_to_steps(next_e))
            ego.set_plyr_img(next_e, 'moving')
            ego.gm.prev_e = next_e
            return True
        if any(prev_e) and prev_e==next_e: # CASE continue walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            ego.move_ppos(ego.dirs_to_steps(next_e))
            ego.set_plyr_img(next_e, 'moving')
            return True
        if any(prev_e) and not any(next_e): # CASE stop walking
            if sum(prev_e)>1: 
                next_e = ego._pick_rndm_action(prev_e)
                raise Exception("Internal: prev dir")
            ego.set_plyr_img(prev_e, 'stopped')
            ego.spr.dirty=1
            return True # last update
        if not any(prev_e) and not any(next_e): # CASE continue stopped
            ego.set_plyr_img(prev_e, 'stopped')
            return False
        raise Exception("Internal error: plyr move")





class AIAgent(Agent):
    ''' AI class: a type of Agent that represents any(?) AI NPC with 
        dynamic behavior. Currently this is intended to be specifically & only
        for PKMN, either friendly or not, with extension to NPC 'players'
        pending necessity, at which point hopefully the design options 
        will be more clear. '''
    def __init__(ai, gm, team, options): 
        Agent.__init__(ai, gm, team)

        which_pkmn    = options['which_pkmn']
        init_pos      = options['pos']
        ai.stepsize_x = options['stepsize_x']
        ai.stepsize_y = options['stepsize_y']
        ai.mv_range   = options['move_range'].split('_')
        ai.move_speed = options['move_speed']
        ai.init_shift = options['init_shift']

        ai.string_sub_class = 'pkmn'
        ai.pkmn_id = -1
        ai.snooze=0.0
        ai.pkmn_id = int(which_pkmn)
        ai.coll_check_range = (ai.mv_range[0], float(ai.mv_range[1]))
        ai.set_pkmn_img('d')
        ai.set_tpos(init_pos)
        ai.move_ppos(ai.init_shift)

    def set_pkmn_img(ai, _dir):
        # assume pkmn...
        if ai.pkmn_id<0: raise Exception('internal: id not set')
        if type(_dir)==list: _dir = _dir.index(1)
        if type(_dir)==int:
            _dir = {UDIR:'u', LDIR:'l', DDIR:'d', RDIR:'r'}[_dir]
        if ai.img_id==_dir: return
        ai.spr.image = ai.gm.imgs['pkmn sprite '+str(ai.pkmn_id)+_dir]
        ai.img_id = _dir
        ai.spr.dirty=1

    ''' _choose_action: a core element of the AI system. Chooses which action to
        take based on any factors. '''
    def _choose_action(ai):
        if ai.team == ai.gm.Plyr.team and \
            _dist(ai.gm.Plyr.get_tile_under(), ai.get_tile_under(),2)>2.5:
            return 'move_towards_player'
        else:
            return 'wander'



    ''' act: Interface. Call this to cause the entity to perform actions. '''
    def act(ai): 
        # Update state based on 
        if ai.snooze>=0: 
            ai.snooze -= 1
            return
        ai.snooze=0.0 # normalize 
        # Take baseline mov
        decision = ai._choose_action()
        if decision=='wander': return ai._take_action_Wander()
        if decision=='move_towards_player': 
            return ai._take_action_Movetowards(ai.gm.Plyr)

    def _take_action_Movetowards(ai, target_Agent):
        goal_vec = _sub_aFb(ai.get_tile_under(), ai.gm.Plyr.get_tile_under())
        ideal = []; not_ideal = []
        if goal_vec[X]>=0: ideal.append(RDIR)
        if goal_vec[X]<=0: ideal.append(LDIR)
        if goal_vec[Y]<=0: ideal.append(UDIR)
        if goal_vec[Y]>=0: ideal.append(DDIR)
        random.shuffle(ideal); random.shuffle(not_ideal);
        moved_yet = False
        for vid in ideal:
            vec = [0]*len(DIRECTIONS); vec[vid]=1
            if (not moved_yet) and sum(ai.validate_move(vec))>0:
                ai.move_tpos(ai.moveparams_to_steps(vec))
                ai.set_pkmn_img(vec)
                moved_yet = True

        random_snooze = np.random.uniform(PKMN_MOVE_LOW, PKMN_MOVE_HIGH)
        ai.snooze = ai.snooze + ai.move_speed*random_snooze
        return moved_yet
        # For now, if not ideal, don't move at all.

    def _take_action_Wander(ai):
        poss_actions = [1,1,1,1]
        valid_actions =ai.validate_move(poss_actions) # restrict if invalid
        optns = list(range(len(poss_actions)))
        random.shuffle(optns)
        did_i_move = False
        for i in optns:
            if valid_actions[i]==0: continue
            vec = [0]*len(valid_actions)
            vec[i]=1
            ai.move_tpos(ai.moveparams_to_steps(vec))
            ai.set_pkmn_img(vec)
            did_i_move=True
            break
        random_snooze = np.random.uniform(PKMN_WANDER_LOW, PKMN_WANDER_HIGH)
        ai.snooze = ai.snooze + ai.move_speed*random_snooze
        return did_i_move

    def _update_coll(ai): ai.coll = ai.ppos_rect.copy()

    def moveparams_to_steps(ai, dirs): 
        dx = (dirs[RDIR]-dirs[LDIR]) * ai.gm.smoothing * ai.stepsize_x
        dy = (dirs[DDIR]-dirs[UDIR]) * ai.gm.smoothing * ai.stepsize_y
        return (dx,dy)



class MouseAgent(GhostEntity):
    ''' Mouse: a GhostEntity full with position and image but that should
        not interact directly with any other Agents.
        While still under design, the initial idea is that the mouse will
        indirectly signal other entities by updating the game manager's 
        databases and queues.    '''
    def __init__(mouse, gm):
        GhostEntity.__init__(mouse, gm)
        mouse.string_sub_class = 'mouse'
        mouse.gm.agent_entities.append(mouse)
        mouse.team = '--mouse--'
        mouse._set_ppos(mouse.gm.world_pcenter)
        mouse.spr.image = pygame.Surface(gm.tile_size).convert_alpha()
               

    def update_position(mouse, targ_ppos, cursor='default'):
        prev_pos = mouse.get_tile_under()
        targ_pos = mouse.get_tile_under(targ_ppos)
#        if targ_pos==prev_pos:
#            return
        mouse._set_tpos(targ_pos)
        mouse._notify_gm_move()
        mouse.set_cursor(cursor)

    def set_cursor(mouse, mode):
        # puts the desired cursor mode sprite at the current pos
        if mode=='default':
#            mouse.spr.image.fill((140,100,240,180))
            mouse.draw_target( (140,40,240) )
#            mouse.spr.image = pygame.image.load('./resources/cursor1.png')
            mouse.spr.image.convert_alpha()
            mouse.spr.dirty=1
        else: print "Mouse mode not recognized:", mode

    def draw_target(mouse, (r,g,b) ):
        mouse.spr.image.fill((0,0,0,0))
        tx,ty = mouse.gm.tile_size
        M = MOUSE_CURSOR_DISPL
#        for i in [1,2,3]:
        for i in [1,3,4,5]:
            for d in DIRECTIONS:
                rect_size = { UDIR: (tx-2*(i+1)*M, M),   DDIR: (tx-2*(i+1)*M, M),
                              LDIR: (M, ty-2*(i+1)*M),   RDIR: (M, ty-2*(i+1)*M) }[d]
                location = {
                    UDIR: ((i+1)*M, i*M),        DDIR: ((i+1)*M, ty-(i+1)*M), 
                    LDIR: (i*M, (i+1)*M),    RDIR: (tx-(i+1)*M, (i+1)*M), }[d]
#                print i, DIRNAMES[d], 'size/loc:',rect_size, location
                s = pygame.Surface( rect_size ).convert_alpha()
                try:
                    s.fill( (r,g,b, MOUSE_GRAD[i-1]) )
                except:
                    s.fill( (r,g,b, MOUSE_GRAD[-1]) )
                mouse.spr.image.blit(s, location)
        s = pygame.Surface( (4,4) ).convert_alpha()
        s.fill( (r,g,b, 255) )
        mouse.spr.image.blit(s, (tx/2-2,tx/2-2) )
