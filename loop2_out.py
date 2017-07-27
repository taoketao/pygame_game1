# IPython log file
import pygame, random, sys
import sqlite3 as sql
import ConfigParser
import abc


''' Options '''
MAP_LEVEL_CONFIG = './config2.ini'
TILE_SIZE = (64,64);
X = 0;  Y = 1

UDIR = 0;       LDIR = 1;       DDIR = 2;       RDIR = 3
UVEC=[1,0,0,0]; LVEC=[0,1,0,0]; DVEC=[0,0,1,0]; RVEC=[0,0,0,1]
EVENTS = [UDIR, LDIR, DDIR, RDIR]

PLYR_COLL_WIDTH, PLYR_COLL_SHIFT = 0.4, 0.2
PLYR_IMG_SHIFT_INIT = 0.125
BLOCK_COLL_WIDTH, BLOCK_COLL_SHIFT = 0.3, -0.3
DEFAULT_STEPSIZE = 0.15
DEFAULT_FPS = 20


class Agent(object):
    def __init__(agent, gm, team, size=TILE_SIZE):
        agent.gm = gm
        agent.team = team
        agent.img_size = size
        agent._rect_init=False # ie, not starting at (0,0)
        agent.ppos_rect = pygame.Rect((-1,-1),size)
        agent.tpos_rect = pygame.Rect(-1,-1,1,1)
#        agent.rect = agent.spr.rect = agent.spr.image.get_rect()
        agent.spr = pygame.sprite.DirtySprite()
        agent.spr.rect = agent.ppos_rect # tie these two

        agent.coll = None

#        agent.pos_px, agent.pos_py, agent.pos_tx, agent.pos_ty = 0,0,0,0
#        agent.pos_pix = (agent.pos_px, agent.pos_py)
#        agent.pos_tid = (agent.pos_tx, agent.pos_ty)
        agent.img_id = None

        agent.string_sub_class = 'None Stub you must override!!'

    def set_tpos(agent, abs_tpos):
        agent._rect_init=True # The first positioning must be a set
        return agent.set_ppos(agent._tpos_to_ppos(abs_tpos))
    def move_tpos(agent, move_tid): 
        return agent.move_ppos(agent._tpos_to_ppos(move_tid))
    def set_ppos(agent, abs_ppos):
        agent._rect_init=True # The first positioning must be a set
        return agent.move_ppos((abs_ppos[X]-agent.ppos_rect.x, \
                                abs_ppos[Y]-agent.ppos_rect.y  ))
    def move_ppos(agent, move_pix):
        if not agent._rect_init: return 'not initialized'
        targ_x, targ_y = agent.ppos_rect.x+move_pix[X], agent.ppos_rect.y+move_pix[Y]
#        print 'to',targ_x,targ_y
        if targ_x<0 or targ_x>agent.gm.map_x or targ_y<0 or targ_y>agent.gm.map_y:
            return 'out of bounds'
        mov_tid = agent._ppos_to_tpos((targ_x, targ_y))
#        agent.rect = agent.spr.rect = agent.spr.image.get_rect()
#        agent.pos_px = targ_x;       agent.pos_py += targ_y 
#        agent.pos_tx = mov_tid[X]
#        agent.pos_ty = mov_tid[Y]
#        agent.pos_pix = (agent.pos_px, agent.pos_py)
#        agent.pos_tid = (agent.pos_tx, agent.pos_ty)
#        print '===', agent.spr.rect, agent.spr.image.get_rect(), agent.pos_pix, move_pix
        #agent.rect.move_ip(move_pix)
#     agent.spr.rect = pygame.Rect( agent.img_size...agent.spr.image.get_rect().move(move_pix)
        agent.ppos_rect.move_ip(move_pix)
        agent.tpos_rect.move_ip(agent._ppos_to_tpos(move_pix))
        agent.spr.rect.move_ip(move_pix) #<- should be unnecessary... '''
        #agent.spr.rect = agent.rect
#        agent.rect = agent.spr.rect

#        print '===',agent.spr.rect, agent.spr.image.get_rect(), agent.pos_pix
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

    def get_tpos_rect(agent): return agent.ppos_rect
    def get_ppos_Rect(agent): return agent.tpos_rect

class Player(Agent):
    def __init__(ego, gm):
        Agent.__init__(ego, gm, 'plyr')
        ego.string_sub_class = 'plyr'
        ego.spr = pygame.sprite.DirtySprite()
        ego.spr.image = gm.imgs['player sprite 1']
        ego.spr.rect = ego.spr.image.get_rect()
        ego.gm.sprites.append(ego.spr)

#        print (ego.gm.world_pcenter)
#        print 'a',ego.set_ppos(ego.gm.world_pcenter)#.\
#                    #move((0,-int(PLYR_IMG_SHIFT_INIT*gm.tile_y_size//1)))
#        print 'b',ego.move_ppos((0,-int(PLYR_IMG_SHIFT_INIT*gm.tile_y_size//1)))
#        ego.rect = ego.spr.rect = ego.spr.image.get_rect()
#        print ego.pos_pix, ego.pos_tid, ego.rect, ego.spr.rect, ego.spr.image.get_rect()
        ego.spr.dirty=1
        ego.spr.add( gm.plyr_team )
        ego.plyr_step_cycler = 0     # animation counter for player sprite
        ego.n_plyr_anim = gm.n_plyr_anim
        ego.n_plyr_dirs = gm.n_plyr_dirs
        ego.dirs_to_steps = ego.moveparams_to_steps

    def _update_coll(ego):
        ego.coll = ego.gm.deflate(ego.ppos_rect, PLYR_COLL_WIDTH, PLYR_COLL_SHIFT)

    def Spr(ego): return ego.spr

    def set_plyr_img(ego, dirs, mode=None, init_ppos=None):
        if mode==None: raise Exception("[mode] is restricted to not be <None>")
        if not init_ppos==None:
            ego.set_ppos(init_ppos)
            if mode=='init-shift':
                ego.move_ppos((0,-int(PLYR_IMG_SHIFT_INIT*ego.gm.tile_y_size//1)))
            elif mode=='init-noshift': pass
            else: print "Unrecognized init mode"
        if not ego._rect_init: raise Exception('Internal: not initialized')
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

    def moveparams_to_steps(ego,dirs):
        dx = (dirs[RDIR]-dirs[LDIR]) * ego.gm.smoothing * ego.gm.stepsize_x
        dy = (dirs[DDIR]-dirs[UDIR]) * ego.gm.smoothing * ego.gm.stepsize_y
        return (dx,dy)





class AIAgent(Agent):
    def __init__(ai, gm, team): 
        Agent.__init__(ai, gm, team)
        ai.string_sub_class = 'pkmn'
        ai.pkmn_id = -1

    def set_pkmn_img(ai, _dir):
        # assume pkmn...
        if ai.pkmn_id<0: raise Exception('internal: id not set')
        if type(_dir)==int:
            _dir = {UDIR:'u', LDIR:'l', DDIR:'d', RDIR:'r'}[_dir]
        if ai.img_id==_dir: return
        ai.spr.image = ai.gm.imgs['pkmn sprite '+str(ai.pkmn_id)+_dir]
        ai.rect = ai.spr.rect = ai.spr.image.get_rect() # reference or copy?
        if not ai._rect_init: ai.gm.sprites.append(ai.spr)
        ai._rect_init = True
        ai.img_id = _dir
        ai.spr.dirty=1

    def act(ai): pass

    def _update_coll(ai): pass
    def moveparams_to_steps(ai, params): pass
    def set_which_pkmn(ai, s): ai.pkmn_id = int(s)



''' GameManager: Whole wrapper class for a organizing a game level. '''
class GameManager(object):
    def __init__(gm, which_map_file=None): 
        if not which_map_file:  gm.which_map_file = MAP_LEVEL_CONFIG 
        else:                   gm.which_map_file = which_map_file 

    def initialize_internal_structures(gm):
        gm._init_create_database()
        gm._init_global_fields()
        gm._init_pygame()
        gm._init_load_imgs()
        gm._init_sprite_macros()
        gm._init_plyr_object()
        gm._init_start_map()

    """ ---------------------------------------------------------------------- """
    """    Initialization Procedures, called once prior to a new game level.   """
    """ ---------------------------------------------------------------------- """

    ''' Create databases '''
    def _init_create_database(gm):
        gm.tile_size = (gm.tile_x_size, gm.tile_y_size) = TILE_SIZE
        cxn = sql.connect(':memory:')
        _db = cxn.cursor()
        _db.execute(''' CREATE TABLE tilemap ( 
            tx INT, ty INT,                 px INT, py INT, 
            base_tid TEXT NOT NULL,         ent_tid TEXT,   
            block_plyr BOOL,                block_pkmn BOOL      ); ''')
        cp = ConfigParser.ConfigParser()
        cp.read(gm.which_map_file)
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
        gm.map_db = _db
        gm.map_num_tiles = (curR, curC+1)
        gm.cp = cp

    ''' Important global fields '''
    def _init_global_fields(gm):
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = tuple( \
                [gm.map_num_tiles[i] * gm.tile_size[i] for i in (X,Y)])
        gm.world_pcenter = ( gm.map_x // 2 - gm.tile_x_size // 2, \
                            gm.map_y // 2 - gm.tile_y_size // 2   )
        gm.n_plyr_anim = 3
        gm.n_plyr_dirs = len(EVENTS)

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
        gm.sprites = []
        gm.plyr_team = pygame.sprite.LayeredDirty([])
        gm.enemy_team_1 = pygame.sprite.LayeredDirty([])
        gm.ai_entities = []
        
    def _init_plyr_object(gm): 
        gm.Plyr = Player(gm)
        #print gm.Plyr.pos_tid

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
        for px, py, base, ent in gm.map_db.execute(query).fetchall():
            '''  Base layer: '''
            targ_surface.blit(gm.imgs[base], (px,py))
            '''  Entity layer: '''
            if not ent=='-':
                targ_surface.blit(gm.imgs[ent], (px,py))
        if update_me: pygame.display.update()

    def clear_screen(gm): 
        gm.screen.blit(gm.background,(0,0))

    def _basic_render(gm):
        d = pygame.sprite.LayeredDirty(gm.sprites)
        pygame.display.update(d.draw(gm.screen))
        del d

    def _ordered_render(gm):
        gm.sprites.sort(key=lambda x: x.rect.bottom)
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

        #if len(gm.ai_entities.sprites())==0:
        if len(gm.ai_entities)==0:
            gm.create_new_ai('enemy1','pkmn', (1,1), {'which_pkmn':'1'})
            gm.create_new_ai('enemy1','pkmn', (1,2), {'which_pkmn':'1'})

        to_update = []
        for agent in gm.ai_entities:
            did_agent_move = agent.act()
            if did_agent_move or any([agent.spr.rect.colliderect(u.rect) \
                                      for u in to_update]):
                to_update.append(agent.spr)
        if gm._handle_plyr_movement() or \
                        any([gm.Plyr.Spr().rect.colliderect(u.rect)\
                        for u in to_update]):
            to_update.append(gm.Plyr.Spr())

        for ent in to_update: ent.dirty=1
        gm.clear_screen()
        gm._ordered_render()


    def create_new_ai(gm, team, entity, init_pos, optns):
        agent = AIAgent(gm, team)
        #agent.spr.add(gm.ai_entities)
        gm.ai_entities.append(agent)
        gm.sprites.append(agent.spr)
        if team=='enemy1': agent.spr.add(gm.enemy_team_1)
        elif team=='plyr': agent.spr.add(gm.plyr_team)
        else: raise Exception("invalid team")

        # init_enemy_object
        if entity=='pkmn':
            agent.set_which_pkmn(optns['which_pkmn'])
            agent.set_pkmn_img('d')
            s1=agent.set_tpos(init_pos)
            s2=agent.move_ppos((0,-int((gm.tile_y_size * float(gm.cp.get(\
                    'pkmn'+optns['which_pkmn'], 'img_shift')))//1)))
            agent.move_tpos((-1,1))
            agent.move_tpos((1,1))
            if not s1=='success' and s2=='success':
                raise Exception("Initialization error: out of bounds")
        return agent

    ''' --------- PRIVATE UTILITIES for internals --------- '''

    ''' _init_game: setup core fields for running game frames. '''
    def _init_game(gm, fps=DEFAULT_FPS, stepsize_factor=DEFAULT_STEPSIZE):
        gm.fps = float(fps)     # frames per second
        gm.fpms = fps/1000.0    # frames per millisecond
        gm.stepsize_x = stepsize_factor * gm.tile_x_size
        gm.stepsize_y = stepsize_factor * gm.tile_y_size
        gm.clock = pygame.time.Clock()  # clock object for frame smoothness
        gm.last_tick = 0            # clock counter field
        gm.smoothing = 1.0          # animation smoothing factor
        gm._reset_events()
        gm.prev_e = gm.events[:]
        gm.Plyr.set_plyr_img(DVEC, 'init-shift', gm.world_pcenter)
        gm.map_dirty_where = [] # Where has the map been altered?
        gm.map_blocks = {} # validate type -> list of rects that block


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
        print 'fps:', gm.clock.get_fps()
        gm.smoothing = dt * gm.fpms if gm.last_tick>0 else 1
        gm.last_tick = this_tick

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

    def _debugutility_print_dir(gm, d, prefix='', end=False):
        print prefix,
        print 'U' if d[UDIR] else '_',
        print 'R' if d[RDIR] else '_',
        print 'D' if d[DDIR] else '_',
        print 'L' if d[LDIR] else '_',
        print '  ',
        if end: print ''

    ''' _handle_plyr_movement: using known prev_e events and current 
        gm.events, calculate '''
    def _handle_plyr_movement(gm):
        prev_e = gm.prev_e
        next_e = gm.validate_move(gm.Plyr, gm.events) # restrict if invalid
#        gm._debugutility_print_dir(prev_e, 'prev')
#        gm._debugutility_print_dir(next_e, '  ->  next')
#        gm._debugutility_print_dir(gm.events, '  from  event')
        if not any(prev_e) and any(next_e): # started walking
            if sum(next_e)>1: # pick one of the options
                optns = [i for i in range(gm.n_plyr_dirs) if next_e[i]==1]
                next_e = [False]*gm.n_plyr_dirs
                next_e[random.choice(optns)] = True

            gm.Plyr.move_ppos(gm.Plyr.dirs_to_steps(next_e))
            gm.Plyr.set_plyr_img(next_e, 'moving')
            gm.prev_e = next_e
            return True
        if any(prev_e) and any(next_e) and not prev_e==next_e: # walking & turning
            if sum(next_e)>1: # try: get the new option
                new = [a and not b for a,b in zip(next_e, prev_e)]
#                gm._debugutility_print_dir(new, '  new')
                if sum(new)>1: # except: pick one of the new options
                    optns = [i for i in range(gm.n_plyr_dirs) if new[i]==1]
                    new = [False]*gm.n_plyr_dirs
                    new[random.choice(optns)] = True
                gm.Plyr.move_ppos(gm.Plyr.dirs_to_steps(new))
                gm.Plyr.set_plyr_img(new, 'moving')
                return True
            gm.Plyr.move_ppos(gm.Plyr.dirs_to_steps(next_e))
            gm.Plyr.set_plyr_img(next_e, 'moving')
            gm.prev_e = next_e
            return True
        if any(prev_e) and prev_e==next_e: # continue walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            gm.Plyr.move_ppos(gm.Plyr.dirs_to_steps(next_e))
            gm.Plyr.set_plyr_img(next_e, 'moving')
            return True
        if any(prev_e) and not any(next_e): # stop walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            gm.Plyr.set_plyr_img(prev_e, 'stopped')
            gm.Plyr.Spr().dirty=1
            return True # last update
        if not any(prev_e) and not any(next_e): # continue stopped
            gm.Plyr.set_plyr_img(prev_e, 'stopped')
            return False


    """ validate_move: given an move attempt by an agent, update move. """
    def validate_move(gm, agent, parameter):
        if agent.string_sub_class=='plyr':
            if not any(parameter): return parameter
            dirs = parameter[:]
            query = "SELECT px, py, ent_tid FROM tilemap WHERE block_plyr==?"
            under_tiles = []
            agent_coll = agent.coll.move(agent.moveparams_to_steps(dirs))
#

            blocks = []
#            agent.move_ip(gm._new_pos_plyrstep(dirs)) # Would step result in coll?
            #boundaries = gm._get_block_impasses(agent) TODO
            for px, py, ent in gm.map_db.execute(query, ('true',)).fetchall():
                block_r = gm.deflate(pygame.Rect((px,py), TILE_SIZE), \
                        BLOCK_COLL_WIDTH, BLOCK_COLL_SHIFT)
                if block_r.colliderect(agent_coll):
                    under_tiles.append((px,py))
                blocks += [block_r] 

            for block_r in blocks :
                gm._Debug_Draw_Rect_border(block_r, render=False)
            gm._Debug_Draw_Rect_border(agent_coll)

            for px,py in under_tiles:
                if px < gm.Plyr.ppos_rect.x:    dirs[LDIR] = False
                if px > gm.Plyr.ppos_rect.x:    dirs[RDIR] = False
                if py < gm.Plyr.ppos_rect.y:    dirs[UDIR] = False
                if py > gm.Plyr.ppos_rect.y:    dirs[DDIR] = False
            return dirs
        else: raise Exception("Not implemented yet: "+agent.string_sub_class)

    def _get_block_impasses(gm, agent):
        if len(gm.map_dirty_where)>0 or \
                    not gm.map_blocks.has_key(agent.string_sub_class):
            gm._recompute_blocks(agent)
        return gm.map_blocks[agent]

    def _recompute_blocks(gm, agent): 
        pass
        # 1 acquire map & identify blocking blocks, 2 sequentially compute  blocking rects,
        # 3 condolidate blocking rects (4: optimize: only update where map was dirty)
        # 5 store them im a way that is accessible to the agent
        query = "SELECT block_"+agent.string_sub_class+' '+\
                "FROM tilemap WHERE tx=? AND ty=?;"
        if gm.map_db.execute(query, mov_tid).fetchone()[0] == 'true':
            return 'space is blocked for this '+agent.string_sub_class
    

    def _Debug_Draw_Rect_border(gm, rect, thickness=2, render=True):
        t=thickness
        rs = []
        def _draw(R, rs):
            rs += [pygame.draw.rect(gm.screen, pygame.Color('red'), R)]

        _draw(pygame.Rect(rect.topleft, (t,rect.h)), rs)
        _draw(pygame.Rect(rect.topright, (t,rect.h)), rs)
        _draw(pygame.Rect(rect.topleft, (rect.w,t)), rs)
        _draw(pygame.Rect(rect.bottomleft, (rect.w,t)), rs)

#        for x in range(rect.w//t+1): 
#            _draw(rect.left + x*t, rect.top, rs)
#            _draw(rect.left + x*t, rect.bottom, rs)
#        for y in range(rect.h//t+1): 
#            _draw(rect.left, rect.top + t*y, rs)
#            _draw(rect.right, rect.top +t*y, rs)
        if render:
            pygame.display.update(rs)
'''        query = "SELECT block_"+agent.string_sub_class+' '+\
                "FROM tilemap WHERE tx=? AND ty=?;"
        if agent.gm.map_db.execute(query, mov_tid).fetchone()[0] == 'true':
            return 'space is blocked for this '+agent.string_sub_class
'''

GM = GameManager()
GM.initialize_internal_structures()
GM.run_game()
