# IPython log file
import pygame, random, sys
import sqlite3 as sql
import ConfigParser
import abc
import numpy as np


''' Options '''
MAP_LEVEL_CONFIG = './config2.ini'
TILE_SIZE = (64,50);
TILE_SIZE = (50,50);
X = 0;  Y = 1

UDIR = 0;       LDIR = 1;       DDIR = 2;       RDIR = 3
UVEC=[1,0,0,0]; LVEC=[0,1,0,0]; DVEC=[0,0,1,0]; RVEC=[0,0,0,1]
DIRECTIONS = EVENTS = [UDIR, LDIR, DDIR, RDIR]

PLYR_COLL_WIDTH, PLYR_COLL_SHIFT = 0.4, 0.2
PLYR_IMG_SHIFT_INIT = 0.125
OBJBLOCK_COLL_WIDTH, OBJBLOCK_COLL_SHIFT = 0.3, -0.3
OBJBLOCK_COLL_WIDTH, OBJBLOCK_COLL_SHIFT = 0.35, -0.35
if OBJBLOCK_COLL_WIDTH+OBJBLOCK_COLL_SHIFT<0: raise Exception()
DEFAULT_STEPSIZE = 0.20
DEFAULT_FPS = 24

# Latencies for actions:
#PKMN_WANDER_LOW, PKMN_WANDER_HIGH = 0.4, 0.5
#PKMN_MOVE_LOW, PKMN_MOVE_HIGH = 0.8, 1.1
PKMN_WANDER_LOW, PKMN_WANDER_HIGH = 1.0,3.0
PKMN_MOVE_LOW, PKMN_MOVE_HIGH = 0.4,0.9





def _dist(p1,p2,Q): 
    if Q in [1,'manh']: return abs(p1[X]-p2[X])+abs(p1[Y]-p2[Y])
    if Q in [2,'eucl']: 
        return np.sqrt(np.square(p1[X]-p2[X])+np.square(p1[Y]-p2[Y]))
def _sub_aFb(a,b): return b[X]-a[X], b[Y]-a[Y]

class Agent(object):
    def __init__(agent, gm, team, size=TILE_SIZE):
        agent.gm = gm
        agent.team = team
        agent.img_size = size
#        agent._rect_init=False # ie, not starting at (0,0)
        agent.ppos_rect = pygame.Rect((0,0),size)
        agent.spr = pygame.sprite.DirtySprite()
        agent.spr.rect = agent.ppos_rect # tie these two
        agent.stepsize_x, agent.stepsize_y = 0,0
        agent.init_shift = (0,0)

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

        agent.string_sub_class = 'None Stub you must override!!'

    def Spr(agent): return agent.spr

    def set_tpos(agent, abs_tpos):
#        agent._rect_init=True # The first positioning must be a set
        return agent.set_ppos(agent._tpos_to_ppos(abs_tpos))
    def move_tpos(agent, move_tid): 
        return agent.move_ppos(agent._tpos_to_ppos(move_tid))
    def set_ppos(agent, abs_ppos):
#        agent._rect_init=True # The first positioning must be a set
        return agent.move_ppos((abs_ppos[X]-agent.ppos_rect.x, \
                                abs_ppos[Y]-agent.ppos_rect.y  ))
    def move_ppos(agent, move_pix):
#        if not agent._rect_init: return 'not initialized'
        targ_x, targ_y = agent.ppos_rect.x+move_pix[X], agent.ppos_rect.y+move_pix[Y]
        if targ_x<0 or targ_x>agent.gm.map_x or targ_y<0 or targ_y>agent.gm.map_y:
            return 'out of bounds'
        mov_tid = agent._ppos_to_tpos((targ_x, targ_y))
        agent.ppos_rect.move_ip(move_pix)
        #agent.spr.rect.move_ip(move_pix) #<- should be unnecessary... '''
        agent.spr.dirty=1
        agent._update_coll()
        return 'success'

    @abc.abstractmethod 
    def _update_coll(ego): raise Exception("ABC")
    @abc.abstractmethod 
    def moveparams_to_steps(ego,dirs): raise Exception("ABC")

    def _update_tpos_from_ppos(agent, ppos):
        agent.pos_tid = (agent.pos_tx, agent.pos_ty) = agent._ppos_to_tpos(ppos)
    def _ppos_to_tpos(agent, ppos):
        return (int(ppos[X]//agent.gm.tile_x_size), int(ppos[Y]//agent.gm.tile_y_size))
    def _tpos_to_ppos(agent, tpos):
        return (int(tpos[X]*agent.gm.tile_x_size), int(tpos[Y]*agent.gm.tile_y_size))

    def get_tpos_rect(agent): return agent._ppos_to_tpos(agent.ppos_rect)
    def get_tile_under(agent): 
        t = agent._ppos_to_tpos(pygame.Rect(agent.ppos_rect.midbottom, \
                TILE_SIZE).move(agent.init_shift))
        return (t[X],t[Y])
    def get_ppos_rect(agent): return agent.ppos_rect

    def _split_binary_vec(agent, vec):
        if sum(vec)<=1: raise Exception("internal: dev err")
        v1 = [False]*len(vec);  v1[vec.index(True)]=True
        v2 = vec[:];            v2[vec.index(True)]=False
        return v1, v2
    def _combine_moves(agent, v1, v2): 
        return [bool(i * j) for i,j in zip(v1,v2)]
    """ validate_move: given an move attempt by this agent, 'fix' move. 
        parameter should be a binary vector of possible moves.
        What each action means is dependent on the subclass's definition
        of method moveparams_to_steps
    """ 

    def _validate_multi_move(agent, parameter, debug=False, c='red'):
        results = []
        for vi,v in enumerate(parameter):
            p_tmp = [0]*len(parameter)
            p_tmp[vi]=v
            single_res = agent.validate_move(p_tmp, debug, c)
            results .append( single_res[vi] )
        return results
            

    def validate_move(agent, parameter, debug=False, c='red'):
        if not any(parameter): return parameter # an easy optimization
        params = list(parameter[:])
        if sum(params)>1:
            return agent._validate_multi_move(params,debug,c)
        attmpt_step = agent.coll.move(agent.moveparams_to_steps(params))
        for block_r in agent.gm.get_agent_blocks(agent):
            if debug: agent.gm._Debug_Draw_Rect_border(block_r, render=False,c=c)
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
    def __init__(ego, gm):
        Agent.__init__(ego, gm, 'plyr')
        ego.string_sub_class = 'plyr'
        ego.coll_check_range = ('eucl',1.5) # check 8 tiles surrounding
        ego.spr = pygame.sprite.DirtySprite()
        ego.gm.agent_sprites.append(ego)
        ego.spr.add( gm.plyr_team )
        ego.plyr_step_cycler = 0     # animation counter for player sprite
        ego.n_plyr_anim = gm.n_plyr_anim
        ego.n_plyr_dirs = gm.n_plyr_dirs
        ego.dirs_to_steps = ego.moveparams_to_steps

        ego.set_plyr_img(DVEC, 'init-shift')
        ego.set_ppos(ego.gm.world_pcenter)
        ego.init_shift = (0,-int(PLYR_IMG_SHIFT_INIT*ego.gm.tile_y_size//1))
        ego.move_ppos(ego.init_shift)

    def _update_coll(ego):
        ego.coll = ego.gm.deflate(ego.ppos_rect, PLYR_COLL_WIDTH, PLYR_COLL_SHIFT)

    def Spr(ego): return ego.spr

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
    def __init__(ai, gm, team, options): 
        which_pkmn = options['which_pkmn']
        init_pos = options['pos']
        Agent.__init__(ai, gm, team)
        ai.string_sub_class = 'pkmn'
        ai.pkmn_id = -1
        ai.snooze=0.0
        ai.pkmn_id = int(which_pkmn)
        ai.stepsize_x, ai.stepsize_y, mv_range, ai.move_speed = ai.gm.db.execute(
        '''  SELECT     stepsize_x, stepsize_y, move_range, move_speed 
             FROM       pkmn_prefabs 
             WHERE      pkmn_id=?''' , (ai.pkmn_id,)).fetchone()
        mv_r = mv_range.split('_')
        ai.coll_check_range = (mv_r[0], float(mv_r[1]))
        ai.set_pkmn_img('d')
        ai.set_tpos(init_pos)
        ai.init_shift = (0, -int((ai.gm.tile_y_size * float(ai.gm.cp.get(\
                             'pkmn'+which_pkmn, 'img_shift')))//1))
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
            return 'wander' # STUB



    ''' act: Interface. Call this method to cause the entity to perform an action. '''
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




''' GameManager: Whole wrapper class for a organizing a game level. '''
class GameManager(object):
    def __init__(gm, which_config_file=None): 
        if not which_config_file:  gm.which_config_file = MAP_LEVEL_CONFIG 
        else:                      gm.which_config_file = which_config_file 

    def initialize_internal_structures(gm):
        gm._init_create_database()
        gm._init_global_fields()
        gm._init_pygame()
        gm._init_load_imgs()
        gm._init_sprite_macros()
        gm._init_start_map()
        gm._init_plyr_object()

    """ ---------------------------------------------------------------------- """
    """    Initialization Procedures, called once prior to a new game level.   """
    """ ---------------------------------------------------------------------- """

    ''' Create databases '''
    def _init_create_database(gm):
        gm.tile_size = (gm.tile_x_size, gm.tile_y_size) = TILE_SIZE
        # Initialize databases
        _db = sql.connect(':memory:').cursor() # formerly broken up with cxn
        _db.execute(''' CREATE TABLE tilemap ( 
            tx INT, ty INT,                 px INT, py INT, 
            base_tid TEXT NOT NULL,         ent_tid TEXT,   
            block_plyr BOOL,                block_pkmn BOOL,
            coll_present BOOL,
            coll_px INT,    coll_py INT,    coll_pw INT,    coll_ph INT ); ''')

        _db.execute(''' CREATE TABLE pkmn_prefabs (     name TEXT, 
                                                        pkmn_id INT, 
                                                        img_shift FLOAT, 
                                                        stepsize_x FLOAT, 
                                                        stepsize_y FLOAT,
                                                        move_speed FLOAT,
                                                        move_range TEXT);''')
        cp = ConfigParser.ConfigParser()
        cp.read(gm.which_config_file)
        # Populate databases
        for pkmn_id in cp.get('list_of_pkmn_prefabs','ids').split(','):
            if pkmn_id=='0': continue
            vals = [i for _,i in cp.items('pkmn'+pkmn_id)] 
            # ^^ Must be in order as specified above! ^^
            _db.execute('INSERT INTO pkmn_prefabs VALUES (?,?,?,?,?,?,?)',vals);
#        
        curR, curC = 0,0
        for char in cp.get('map','map'):
            if char== '\n':
                curC += 1; curR = 0; continue;
            base_tid = char if char in ['d','g'] else ['g']
            _db.execute(''' INSERT INTO tilemap 
                (tx, ty, px, py, base_tid, ent_tid, block_plyr, block_pkmn)
                VALUES (?,?,?,?,?,?,?,?); ''', \
                        (curR, curC, gm.tile_x_size*curR, gm.tile_y_size*curC, 
                        cp.get(char, 'base_tid'),   cp.get(char, 'ent_tid'), 
                        cp.get(char, 'block_plyr'), cp.get(char, 'block_pkmn')))
            curR += 1
        gm.db = _db
        gm.map_num_tiles = (curR, curC+1)
        gm.cp = cp

    ''' Important global fields '''
    def _init_global_fields(gm):
        gm.n_plyr_anim = 3
        gm.n_plyr_dirs = len(EVENTS)
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = tuple( \
                [gm.map_num_tiles[i] * gm.tile_size[i] for i in (X,Y)])
        gm.world_pcenter = ( gm.map_x // 2 - gm.tile_x_size // 2, \
                            gm.map_y // 2 - gm.tile_y_size // 2   )

    ''' Spin up pygame '''
    def _init_pygame(gm):
        pygame.init()
        gm.screen = pygame.display.set_mode(gm.map_pix_size)

    ''' Load and store tile-sized sprite images '''
    def _init_load_imgs(gm):
        gm.imgs = {}
        ''' >>> Tiles:  '''
        gm.imgs['a'] = pygame.image.load('./apricorn_img.png').convert_alpha()
        gm.imgs['g'] = pygame.image.load('./grass_tile_img.png').convert_alpha()
        gm.imgs['d'] = pygame.image.load('./dirt_tile_img.png').convert_alpha()
        ''' >>> Plyr:  '''
        for i in range(gm.n_plyr_dirs * gm.n_plyr_anim):
            save_spnm = 'player sprite '+str(i+1)
            load_spnm = './player/'+str(i+1)+'.png'
            gm.imgs[save_spnm] = pygame.image.load(load_spnm).convert_alpha()
        ''' >>> PKMN:  '''
        for i in range(1):
            for d in ['u','d','r','l']:
                save_spnm = 'pkmn sprite '+str(i+1)+d
                load_spnm = './pkmn/'+str(i+1)+d+'.png'
                gm.imgs[save_spnm] = pygame.image.load(load_spnm).convert_alpha()
        ''' >>> [processing]:  '''
        for tnm, t in gm.imgs.items():
            tmp = pygame.Surface(gm.tile_size).convert_alpha()
            pygame.transform.scale(t, gm.tile_size, tmp)
            t.fill((255,255,255,255), None, pygame.BLEND_RGBA_MULT)
            gm.imgs[tnm]=tmp.convert_alpha()
    
    def _init_sprite_macros(gm): 
        gm.agent_sprites = []
        gm.plyr_team = pygame.sprite.LayeredDirty([])
        gm.enemy_team_1 = pygame.sprite.LayeredDirty([])
        gm.ai_entities = []
#        gm.sprites = []
        
    def _init_plyr_object(gm): 
        gm.Plyr = Player(gm)

    def deflate(gm, targ, pct, shift_down=0.0):
        r = targ.inflate((gm.tile_x_size * -pct, gm.tile_y_size * -pct))
        return r.move((0, gm.tile_y_size * shift_down/2))
    def _init_start_map(gm):
        gm.draw_background()
        gm.background = pygame.Surface(gm.map_pix_size)
        gm.draw_background(gm.background)
        gm._basic_render()


    """ ---------------------------------------------------------------------- """
    """  Rendering functions on the map-global scale. Unsure if keeping these. """
    """ ---------------------------------------------------------------------- """
    def draw_background(gm, targ_surface=None, update_me=True):
        ''' Naively redraw entire background. '''
        if not targ_surface: targ_surface = gm.screen
        query = "SELECT px, py, base_tid, ent_tid FROM tilemap"
        for px, py, base, ent in gm.db.execute(query).fetchall():
            '''  Base layer: '''
            targ_surface.blit(gm.imgs[base], (px,py))
            '''  Entity layer: '''
            if not ent=='-':
                targ_surface.blit(gm.imgs[ent], (px,py))
        if update_me: pygame.display.update()

    def clear_screen(gm): 
        gm.screen.blit(gm.background,(0,0))

    def _basic_render(gm):
        # Previous version. Unsure how much it's re-rendering.
        d = pygame.sprite.LayeredDirty([a.Spr() for a in gm.agent_sprites])
#        print len(gm.agent_sprites)
#        for spr in gm.agent_sprites:
#            print '\t',spr.image.get_rect()
#            gm._Debug_Draw_Rect_border(spr.image.get_rect(), c='yellow')
#        gm._Debug_Draw_Rect_border(spr.image.get_rect(), c='yellow')
        pygame.display.update(d.draw(gm.screen))
        del d

    def _ordered_render(gm):
        gm.agent_sprites.sort(key=lambda x: x.spr.rect.bottom)
        gm._basic_render()

    """ ---------------------------------------------------------------------- """
    """ core function run_game handles the mechanics of running a level.       """
    """    Specifically, it manages all the sprites and interactions between   """
    """    them as the master over sequentially-sensitive events.              """
    """ ---------------------------------------------------------------------- """

    """ PUBLIC FUNCTION run_game: launch a game and loop it  """
    def run_game(gm, max_num_epochs_test=10000):
        gm._init_game()
        for _ in range(max_num_epochs_test):
            gm._run_frame()

    """ CORE FUNCTION run_frame: launch a single loop iteration.
        Paradigm: (1) update UI and global fields to be current, 
            (2) sequentially update entities and interactions,
            (3) render. """
    def _run_frame(gm):
        gm._standardize_new_frame()

        to_update = []
        for agent in gm.ai_entities:
            did_agent_move = agent.act()
            if did_agent_move or any([agent.spr.rect.colliderect(u.rect) \
                                      for u in to_update]):
                to_update.append(agent.spr)
        if gm.Plyr.plyr_move() or \
                        any([gm.Plyr.Spr().rect.colliderect(u.rect)\
                        for u in to_update]):
            to_update.append(gm.Plyr.Spr())

        for ent in to_update: ent.dirty=1
        gm.clear_screen()
        gm._ordered_render()


    def create_new_ai(gm, team, entity, optns):
        if entity=='pkmn':
            # create ai entity
            pkmn_ai = AIAgent(gm,  team,  options=optns)
            # update game manager's structures:
            gm.ai_entities.append(pkmn_ai)
            gm.agent_sprites.append(pkmn_ai)
            if team=='enemy1': pkmn_ai.spr.add(gm.enemy_team_1)
            elif team=='plyr': pkmn_ai.spr.add(gm.plyr_team)
            else: raise Exception("invalid team")
            # initialize as:
#            if not s1=='success' and s2=='success':
#                raise Exception("Initialization error: out of bounds")
            return pkmn_ai
        raise Exception("Internal error: AI type not recognized.")

    ''' --------- PRIVATE UTILITIES for internals --------- '''

    ''' _init_game: setup core fields for running game frames. '''
    def _init_game(gm, fps=DEFAULT_FPS, plyr_stepsize_factor=DEFAULT_STEPSIZE):
        gm.fps = float(fps)     # frames per second
        gm.fpms = fps/1000.0    # frames per millisecond
        gm.fps_itr = 0
        gm.clock = pygame.time.Clock()  # clock object for frame smoothness
        gm.last_tick = 0            # clock counter field
        gm.smoothing = 1.0          # animation smoothing factor

        gm._reset_events()
        gm.prev_e = gm.events[:]
        gm.Plyr.set_plyr_img(DVEC, 'init-shift', gm.world_pcenter)
        gm.Plyr.stepsize_x = plyr_stepsize_factor * gm.tile_x_size
        gm.Plyr.stepsize_y = plyr_stepsize_factor * gm.tile_y_size

        gm.map_dirty_where = [] # Where has the map been altered?
        gm.map_blocks = {} # validate type -> list of rects that block

        # Initialize some enemies, debug:
        gm.create_new_ai('enemy1','pkmn', {'pos':(1,2), 'which_pkmn':'1'})
        gm.create_new_ai('plyr','pkmn', {'pos':(6,6), 'which_pkmn':'1'})



    ''' _reset_events: clear the active stored events '''
    def _reset_events(gm): gm.events = [False] * gm.n_plyr_dirs

    def _standardize_new_frame(gm):
        gm._punch_clock()
        gm._update_events()

    ''' Using the clock, determine the time that passed since last frame
        and calculate a multiplicative factor to smooth animation. '''
    def _punch_clock(gm):
        gm.clock.tick(gm.fps)
        this_tick = pygame.time.get_ticks()
        dt = (this_tick - gm.last_tick)
        cur_true_fps = gm.clock.get_fps()
        if cur_true_fps<gm.fps-1 and gm.fps_itr==0:
            print 'fps:', cur_true_fps
        gm.smoothing = dt * gm.fpms if gm.last_tick>0 else 1
        gm.last_tick = this_tick
        gm.fps_itr = (gm.fps_itr+1)%10

    ''' Events Schema: each numbered RunGame event maps to a bool
        array of whether the event happened. '''
    def _update_events(gm):
        gm._reset_events()
        pygame.event.pump()
        down = pygame.key.get_pressed()
        if down[pygame.K_UP]:    gm.events[UDIR]=True
        if down[pygame.K_DOWN]:  gm.events[DDIR]=True
        if down[pygame.K_LEFT]:  gm.events[LDIR]=True
        if down[pygame.K_RIGHT]: gm.events[RDIR]=True
        if down[pygame.K_w]:     gm.events[UDIR]=True
        if down[pygame.K_s]:     gm.events[DDIR]=True
        if down[pygame.K_a]:     gm.events[LDIR]=True
        if down[pygame.K_d]:     gm.events[RDIR]=True
        if down[pygame.K_q]:     sys.exit()
        pygame.event.clear()

    def _tx_to_px(gm, v): return TILE_SIZE[X]*v
    def _ty_to_py(gm, v): return TILE_SIZE[Y]*v
    def _t_to_p(gm, v1, v2=None): 
        if not v2==None:
            return (v1*TILE_SIZE[X], v2*TILE_SIZE[Y])
        return (v1[X]*TILE_SIZE[X], v1[Y]*TILE_SIZE[Y])
    def _px_to_tx(gm, v): return int(v//TILE_SIZE[X])
    def _py_to_ty(gm, v): return int(v//TILE_SIZE[Y])
    def _p_to_t(gm, v1, v2=None): 
        if not v2==None:
            return (int(v1//TILE_SIZE[X]), int(v2//TILE_SIZE[Y]))
        return (int(v1[X]//TILE_SIZE[X]), int(v1[Y]//TILE_SIZE[Y]))
                
            

    def _debugutility_print_dir(gm, d, prefix='', end=False):
        print prefix,
        print 'U' if d[UDIR] else '_',
        print 'R' if d[RDIR] else '_',
        print 'D' if d[DDIR] else '_',
        print 'L' if d[LDIR] else '_',
        print '  ',
        if end: print ''

    ''' This mode is inefficient... but not to be optimized now. '''
    def get_agent_blocks(gm, agent):
        #print 'Loaded blocks:', gm.map_blocks.keys()
        if len(gm.map_dirty_where)>0 or \
                    not gm.map_blocks.has_key(agent.string_sub_class):
            gm._recompute_blocks(agent)
        gm._recompute_blocks(agent)
        return gm.map_blocks[agent.string_sub_class]

    def _recompute_blocks(gm, agent, debug=False): 
        blocks = []
        # 1 acquire map & identify blocking blocks, 2 sequentially compute  blocking rects,
        # 3 condolidate blocking rects (4: optimize: only update where map was dirty)
        # 5 store them im a way that is accessible to the agent
        # Assume uniform blocks!
        arr = np.zeros(gm.map_num_tiles)
        query = "SELECT tx,ty,px,py FROM tilemap WHERE block_"+\
                    agent.string_sub_class+"=?;"
        res = gm.db.execute(query, ('true',)).fetchall()
        for tx,ty,px,py in res: 
            arr[tx,ty] = 1
        for tx,ty,px,py in res: 
            blocks.append( gm.deflate(pygame.Rect((px,py), TILE_SIZE), \
                        OBJBLOCK_COLL_WIDTH, OBJBLOCK_COLL_SHIFT) )
            if debug: gm._Debug_Draw_Rect_border(blocks[-1], render=False, c='red')
            for conn in [(0,1),(1,0)]:
                targ = (gm._px_to_tx(px)+conn[X], gm._py_to_ty(py)+conn[Y])
                if gm.num_x_tiles<=targ[X] or gm.num_y_tiles<=targ[Y] or \
                        0>targ[X] or 0>targ[Y]:  continue
                if arr[targ]==1:
                    blocks += gm._make_conn(conn, (px,py))
                    if debug: gm._Debug_Draw_Rect_border(blocks[-1], render=False, c='blue')
        gm.map_blocks[agent.string_sub_class] = blocks
        
    def _make_conn(gm, direction, p_src):
        if direction[X]<0: return [] # internal error!
        if direction[Y]<0: return [] # internal inconsistency!
        w = OBJBLOCK_COLL_WIDTH*gm.tile_x_size
        h = OBJBLOCK_COLL_WIDTH*gm.tile_y_size
        h_shift = OBJBLOCK_COLL_SHIFT * gm.tile_y_size
        _w = (1-OBJBLOCK_COLL_WIDTH)*gm.tile_x_size
        _h = (1-OBJBLOCK_COLL_WIDTH)*gm.tile_y_size
        _h_shift = (1-OBJBLOCK_COLL_WIDTH)*gm.tile_y_size+h_shift
        td= (p_src[X]+w/2, p_src[Y]+_h, _w, h)
        tr= (p_src[X]+w/2+_w, p_src[Y]+h+h_shift, w, _h)
        return [pygame.Rect( { (0,1): td, (1,0): tr }[direction])]

    def _Debug_Draw_Rect_border(gm, rect, thickness=2, render=True, c='red'):
        t=thickness
        rs = []
        def _draw(R, rs):
            rs += [pygame.draw.rect(gm.screen, pygame.Color(c), R)]
        _draw(pygame.Rect(rect.topleft, (t,rect.h)), rs)
        _draw(pygame.Rect(rect.topright, (t,rect.h)), rs)
        _draw(pygame.Rect(rect.topleft, (rect.w,t)), rs)
        _draw(pygame.Rect(rect.bottomleft, (rect.w,t)), rs)
        if render:
            pygame.display.update(rs)






GM = GameManager()
GM.initialize_internal_structures()
GM.run_game()
