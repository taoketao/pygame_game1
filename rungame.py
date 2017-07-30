import pygame, sys
import sqlite3 as sql
import ConfigParser
import numpy as np

#from agents import Agent, AIAgent, Player
from agents import *
                    
''' Map Options '''
MAP_LEVEL_CONFIG = './config2.ini'
TILE_SIZE = (50,50);
X = 0;  Y = 1

UDIR = 0;       LDIR = 1;       DDIR = 2;       RDIR = 3
UVEC=[1,0,0,0]; LVEC=[0,1,0,0]; DVEC=[0,0,1,0]; RVEC=[0,0,0,1]
DIRECTIONS = EVENTS = [UDIR, LDIR, DDIR, RDIR]
NULL_POSITION = (-1,-1)

OBJBLOCK_COLL_WIDTH, OBJBLOCK_COLL_SHIFT = 0.35,-0.34
if OBJBLOCK_COLL_WIDTH + OBJBLOCK_COLL_SHIFT<=0: raise Exception()

DEFAULT_FPS = 24






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
        _db.execute(''' CREATE TABLE tile_occupants (  
                        uniq_id INT NOT NULL ,
                        tx INT,         ty INT,     agent_type TEXT, 
                        team TEXT       );''')
        
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
        gm.uniq_id_counter = 100
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
        gm.agent_entities = []
        gm.plyr_team = pygame.sprite.LayeredDirty([])
        gm.enemy_team_1 = pygame.sprite.LayeredDirty([])
        gm.ai_entities = []
        gm.environmental_sprites = pygame.sprite.Group([])
        gm.move_effect_sprites = pygame.sprite.LayeredDirty([])
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
        # Currently only renders agent sprites...
        # Previous version. Unsure how much it's re-rendering.
        upd_spr = []
 #       upd_spr = pygame.sprite.LayeredDirty([])
        for agent in gm.agent_entities:
            if agent.spr.dirty==1: 
                try:
                    upd_spr.append((agent.spr, agent.spr.rect))
 #                   upd_spr.add(agent.spr)
                except:
                    upd_spr.append(None)
        for spr in gm.environmental_sprites:
            if spr.dirty==1: 
                try:
                    upd_spr.append((spr, spr.image.get_rect()))
#                    upd_spr.add(spr)
                except:
                    upd_spr.append(None)
        for spr in gm.move_effect_sprites:
            if spr.dirty==1: 
                try:
                    upd_spr.append(spr) # todo
#                    upd_spr.add(spr)
                except:
                    upd_spr.append(None)

        for spr, dest_pos in upd_spr:
            gm.screen.blit(spr.image, dest_pos)
        pygame.display.update( [s.image.get_rect() for s,_ in upd_spr] )

        # if self.cur_mouse_pos on apricot tile: redraw apricot
#        gm.mouse_pos
#        pygame.display.update( upd_spr.draw(gm.screen) )
        


#        pygame.display.update( gm.environmental_sprites.draw(gm.screen))
#        pygame.display.update(d.draw(gm.screen))
#        pygame.display.update(gm.move_effect_sprites.draw(gm.screen))
        del upd_spr

    def _ordered_render(gm):
        gm.agent_entities.sort(key=lambda x: x.spr.rect.bottom)
        gm.Mouse.update_position(pygame.mouse.get_pos())
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

        to_update = [gm.Mouse.spr]
        to_update = []
        for agent in gm.ai_entities:
            did_agent_move = agent.act()
            if did_agent_move or any([agent.spr.rect.colliderect(u.rect) \
                                      for u in to_update]):
                to_update.append(agent.spr)
        if gm.Plyr.plyr_move() or \
                        any([gm.Plyr.spr.rect.colliderect(u.rect)\
                        for u in to_update]):
            to_update.append(gm.Plyr.spr)

        for ent in to_update: ent.dirty=1



        gm.clear_screen()
        gm._ordered_render()


    def create_new_ai(gm, team, entity, optns):
        if entity=='pkmn':
            # create ai entity
            pkmn_ai = AIAgent(gm, team, options=optns)
            # update game manager's structures:
            gm.ai_entities.append(pkmn_ai)
            gm.agent_entities.append(pkmn_ai)
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
    def _init_game(gm, fps=DEFAULT_FPS):
        gm.fps = float(fps)     # frames per second
        gm.fpms = fps/1000.0    # frames per millisecond
        gm.fps_itr = 0
        gm.clock = pygame.time.Clock()  # clock object for frame smoothness
        gm.last_tick = 0            # clock counter field
        gm.smoothing = 1.0          # animation smoothing factor

        gm.active_agents = {}

        gm._reset_events()
        gm.prev_e = gm.events[:]
        gm.Plyr.set_plyr_img(DVEC, 'init-shift', gm.world_pcenter)

        gm.map_dirty_where = [] # Where has the map been altered?
        gm.map_blocks = {} # validate type -> list of rects that block

        # Initialize some enemies, debug:
        pkmn_id = '1' # stub
        for team, pos in [ ('enemy1', (1,2)), ('plyr',(6,6)) ]:
            optns = {'which_pkmn':pkmn_id, 'pos':pos}
            optns['init_shift'] = (0, -int( (gm.tile_y_size * float(\
                        gm.cp.get('pkmn'+pkmn_id, 'img_shift')))//1))
            attrs = ['stepsize_x', 'stepsize_y', 'move_range', 'move_speed'] 
            for a in attrs:
                optns[a] = gm.db.execute( ' SELECT '+a+\
                        ' FROM pkmn_prefabs WHERE pkmn_id=?;', \
                        (pkmn_id,)).fetchone()[0]
            gm.create_new_ai(team,'pkmn', optns)

        # Init mouse interface...
        gm.Mouse = MouseAgent(gm)
    
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
                

    def _notify_move(gm, prev_tu, next_tu, uniq_id, team, atype):
        gm.db.execute('INSERT INTO tile_occupants VALUES (?,?,?,?,?);',
                    (uniq_id, next_tu[X], next_tu[Y], atype, team));
        if not prev_tu==NULL_POSITION:
            gm.db.execute('''DELETE FROM tile_occupants WHERE uniq_id=?
                    AND tx=? AND ty=?;''', (uniq_id, prev_tu[X], prev_tu[Y]))

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
