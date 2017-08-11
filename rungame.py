import pygame, sys
from os.path import join
import sqlite3 as sql
import ConfigParser
import numpy as np
from PIL import Image, ImageOps

from utilities import *
from agents2 import *
from moves import *
                    
''' Map Options '''
MAP_LEVEL_CONFIG = './config7.ini'
IMGS_LOC = './resources/images/'
TILE_SIZE = (64,56);
TILE_SIZE = (32,28);
TILE_SIZE = (25,25);
HUD_SIZE = TILE_SIZE[Y]
X = 0;  Y = 1

SP_ACTION = 4;
ACTIONS = [SP_ACTION]

DEFAULT_FPS = 20


''' GameManager: Whole wrapper class for a organizing a game level. '''
class GameManager(object):
    def __init__(gm, which_config_file=None): 
        if not which_config_file:  gm.which_config_file = MAP_LEVEL_CONFIG 
        else:                      gm.which_config_file = which_config_file 

    def load(gm):
        gm._init_create_database()
        gm._init_global_fields() # requires loaded maps
        gm._init_pygame()
        gm._init_load_imgs() # requires pygame
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
                                pkmn_id INT,            img_shift FLOAT, 
                                stepsize_x FLOAT,       stepsize_y FLOAT,
                                move_speed FLOAT,       move_range TEXT,
                                base_health INT,        base_move_1 TEXT, 
                                base_move_2 TEXT,       base_move_3 TEXT,
                                catch_threshold INT
                                );''')
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
            nvals = ','.join(['?']*len(vals))
            _db.execute('INSERT INTO pkmn_prefabs VALUES ('+nvals+')',vals);
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
        gm.entities = {}

        gm.n_plyr_anim = 3
        gm.smoothing = 1.0          # animation smoothing factor
        gm.n_plyr_dirs = len(DIRECTIONS)
        gm.n_plyr_actions = len(ACTIONS)
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = \
                            multpos(gm.map_num_tiles, gm.tile_size)
        gm.hud_size = (gm.map_x, HUD_SIZE)
        gm.screen_size = (gm.map_x, gm.map_y+HUD_SIZE)
        gm.world_pcenter = subvec(multvec(gm.tile_size,2,'//'),\
                                  multvec(gm.map_pix_size,2,'//'))

#        gm.world_pcenter = ( gm.map_x // 2 - gm.tile_x_size // 2, \
#                            gm.map_y // 2 - gm.tile_y_size // 2   )

    ''' Spin up pygame '''
    def _init_pygame(gm):
        pygame.init()
        gm.screen = pygame.display.set_mode(gm.screen_size)
        gm.screen.convert()
        gm.screen.fill( (220,220,20), rect = \
                    pygame.Rect((0,gm.map_y), gm.hud_size))

    ''' Load and store tile-sized sprite images '''
    def _init_load_imgs(gm):
        gm.imgs = {}
        ''' >>> Tiles:  '''
        gm.imgs['a'] = pygame.image.load(join(IMGS_LOC, 'environment',\
                            'apricorn_img.png')).convert_alpha()
        gm.imgs['g'] = pygame.image.load(join(IMGS_LOC, 'environment',\
                            'grass_tile_img.png')).convert_alpha()
        gm.imgs['d'] = pygame.image.load(join(IMGS_LOC, 'environment',\
                            'dirt_tile_img.png')).convert_alpha()
        ''' >>> Plyr:  '''
        for i in range(gm.n_plyr_dirs * gm.n_plyr_anim):
            save_spnm = 'player sprite '+str(i+1)
            load_spnm = join(IMGS_LOC, 'player', str(i+1)+'.png')
            gm.imgs[save_spnm] = pygame.image.load(load_spnm).convert_alpha()

        ''' >>> PKMN:  '''
        for i in range(1):
            for d in ['u','d','r','l']:
                save_spnm = 'pkmn sprite '+str(i+1)+d
                load_spnm = join(IMGS_LOC, 'pkmn', str(i+1)+d+'.png')
                gm.imgs[save_spnm] = pygame.image.load(load_spnm).convert_alpha()
                gm.imgs[save_spnm+' half whitened'] = gm.imgs[save_spnm].copy()
                gm.imgs[save_spnm+' half whitened'].blit(gm._get_whitened_img(\
                        gm.imgs[save_spnm].copy(), 0.5), (0,0))
                gm.imgs[save_spnm+' full whitened'] = gm.imgs[save_spnm].copy()
                gm.imgs[save_spnm+' full whitened'].blit(gm._get_whitened_img(\
                        gm.imgs[save_spnm].copy(), 0.85), (0,0))

        ''' >>> [processing tile-sized]:  '''
        for tnm, t in gm.imgs.items():
            tmp = pygame.Surface(gm.tile_size).convert_alpha()
            pygame.transform.scale(t, gm.tile_size, tmp)
            t.fill((255,255,255,255), None, pygame.BLEND_RGBA_MULT)
            gm.imgs[tnm]=tmp.convert_alpha()

        ''' >>> Misc:  '''
        # Pokeball sizes: see moves.py.
        pball = pygame.image.load(join(IMGS_LOC, 'moves',\
                            'pokeball.png')).convert_alpha()
        pball_size = multvec(gm.tile_size, 2*POKEBALL_SCALE, 'int')
        pbimg = pygame.transform.scale(pball, pball_size)
        gm.imgs['pokeball'] = pbimg
        for i in range(int(PB_OPENFRAMES)): # see moves.py
            pb_i = gm._get_whitened_img(pbimg, i/PB_OPENFRAMES, pball_size)
            gm.imgs['pokeball-fade-'+str(i)] = pb_i

    def _get_whitened_img(gm, base_pygame_img, frac, size=None): 
        mode = 'RGBA'
        if not size:
            size = base_pygame_img.get_rect().size
        base = Image.frombytes(mode, size, \
                    pygame.image.tostring(base_pygame_img, mode, False))
        arr_base = np.array(base)
        arr_targ = np.copy(arr_base)
        for i in range(arr_targ.shape[0]):
            for j in range(arr_targ.shape[1]):
                    arr_targ[i,j,1] = 255
                    arr_targ[i,j,2] = 255
                    arr_targ[i,j,0] = 255
        blended = Image.blend(base, Image.fromarray(arr_targ, mode), frac)
        return pygame.image.fromstring(blended.tobytes(), size, mode)

    
    def _init_sprite_macros(gm): 
        gm.agent_entities = []
#        gm.plyr_team = pygame.sprite.LayeredDirty([])
#        gm.enemy_team_1 = pygame.sprite.LayeredDirty([])
#        gm.wild_team = pygame.sprite.LayeredDirty([])
        gm.ai_entities = []
        gm.move_effects = []
        
    def _init_plyr_object(gm): 
        gm.Plyr = Player(gm)

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
    def update_hud(gm): # stub...
        gm.screen.fill( (220,220,20), rect = \
                    pygame.Rect((0,gm.map_y), gm.hud_size))


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
        for effect in gm.move_effects:
            if True:#effect.spr.dirty==1: 
                try:
                    upd_spr.insert(0,(effect.spr, effect.spr.rect))
#                    upd_spr.add(spr)
                except:
                    upd_spr.append(None)


        for spr, dest_pos in upd_spr:
            gm.screen.blit(spr.image, dest_pos)
        pygame.display.update( [s.image.get_rect() for s,_ in upd_spr] )

        # if self.cur_mouse_pos on apricot tile: redraw apricot
#        gm.mouse_pos
#        pygame.display.update( upd_spr.draw(gm.screen) )

#        pygame.display.update(d.draw(gm.screen))
#        pygame.display.update(gm.move_effect_sprites.draw(gm.screen))
        del upd_spr

    def _ordered_render(gm):
        gm.agent_entities.sort(key=lambda x: x.spr.rect.bottom)
        gm._basic_render()

    """ ---------------------------------------------------------------------- """
    """ core function run_game handles the mechanics of running a level.       """
    """    Specifically, it manages all the sprites and interactions between   """
    """    them as the master over sequentially-sensitive events.              """
    """ ---------------------------------------------------------------------- """

    """ PUBLIC FUNCTION run_game: launch a game and loop it  """
    def run_game(gm, max_num_epochs_test=10000):
        gm._init_game()
        FRAME_COUNTER = 0
        for _ in range(max_num_epochs_test):
            print '\n\nFRAME_COUNTER', FRAME_COUNTER; 
            FRAME_COUNTER+=1
            gm._run_frame()

    """ CORE FUNCTION run_frame: launch a single loop iteration.
        Paradigm: (1) update UI and global fields to be current, 
            (2) sequentially update entities and interactions,
            (3) render. """
    def _run_frame(gm):
        gm._standardize_new_frame()
        print gm.Plyr.get_center()

#        to_update = [gm.Mouse.spr]
        to_update = []
        # Update agents:
        for agent in gm.ai_entities:
            agent.update_state()
            did_agent_move = agent.act()
            to_update.append(agent.spr)
#            if did_agent_move:
#                to_update.append(agent.spr)
#            if did_agent_move or any([agent.spr.rect.colliderect(u.rect) \
#                                      for u in to_update]):
#                to_update.append(agent.spr)

        # Update effects:
        gm.PlyrHighlighter.update_position_and_image()
        gm.MouseTarget.update_position_and_image()
        for effect in gm.move_effects:
            effect.update_move()

        # Update player:
#        if gm.Plyr.plyr_move() or \
#                        any([gm.Plyr.spr.rect.colliderect(u.rect)\
#                        for u in to_update]):
#            to_update.append(gm.Plyr.spr)
#        if gm.events[SP_ACTION] and gm.buttonUp[SP_ACTION]:
#            gm.agent_main_action()
#        else:
#            gm.Mouse.update_position(pygame.mouse.get_pos(), 'default')
            
        gm.Plyr.TMP_reset()
#        gm.Mouse._logic.update()
        gm.Plyr.TMP_think()
#        gm.Mouse._logic.decide()
        gm.Plyr.TMP_enact()
#        #gm.Mouse._logic.enact()

        for ent in to_update: ent.dirty=1
#        print gm.get_tile_occupants()
        gm.clear_screen()
        gm._ordered_render()

    def agent_main_action(gm):
        # The player has triggered the agent's main action
        # which for now as a stub is just to throw next pokeball.
        return # for now



        if not gm.Plyr.is_plyr_actionable(): return
#        plyr_tpos = gm.Plyr.get_tile_under()
#        mouse_tpos = gm.Mouse.get_tile_under()
        plyr_tpos = gm._p_to_t(gm.Plyr.get_center())
        mouse_tpos = gm._p_to_t(gm.Mouse.get_center())
        query_res = gm.db.execute('''
            SELECT block_pkmn FROM tilemap WHERE 
            tx=? AND ty=?;''', mouse_tpos).fetchall()
        d=dist(plyr_tpos, mouse_tpos,1) 
        if len(query_res)==0:
            pass#gm.Mouse.update_position(pygame.mouse.get_pos(), 'hud action')
        elif d<=3 and not u'true'==query_res[0][0]: # and d>0
            pos = pygame.mouse.get_pos()
            pass#gm.Mouse.update_position(pos, 'good action')
            gm.Plyr.do_primary_action(pos)
#            gm.Plyr.set_plyr_actionable(False)
            pball = Pokeball(gm, 1, gm.Plyr.get_center(), \
                            addvec( pos, \
                                    divvec(gm.tile_size, 2)))
#            pball = Pokeball(gm, 1, gm.Plyr.get_ppos_rect().center, \
#                                addvec(pos, (-int(gm.tile_x_size*POKEBALL_SCALE),0)) )
            gm.move_effects.append(pball)
            gm.buttonUp[SP_ACTION] = False # Require button_up for next action
        else:
            pass#gm.Mouse.update_position(pygame.mouse.get_pos(), 'bad action')
        X = gm.db.execute('''
            SELECT tx, ty, block_plyr, block_pkmn FROM tilemap;''').fetchall()
        x = np.zeros(gm.map_num_tiles)
        for tile in X:
            if tile[2]=='true': x[tile[0],tile[1]]=1
            if tile[2]=='false': x[tile[0],tile[1]]=-1
        y = np.zeros(gm.map_num_tiles)

    def create_new_ai(gm, team, entity, optns):
        if entity=='pkmn':
            # create ai entity
            pkmn_ai = AIAgent(gm, team, options=optns)
            # update game manager's structures:
            gm.ai_entities.append(pkmn_ai)
            gm.agent_entities.append(pkmn_ai)
#            if team=='enemy1': pkmn_ai.spr.add(gm.enemy_1_team)
#            elif team=='plyr': pkmn_ai.spr.add(gm.plyr_team)
#            elif team=='wild': pkmn_ai.spr.add(gm.wild_team)
#            else: raise Exception("invalid team")
            # initialize as:
#            if not s1=='success' and s2=='success':
#                raise Exception("Initialization error: out of bounds")
            pkmn_ai.send_message('initialized as free')
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

        gm.active_agents = {}

        gm._reset_events()
        gm.prev_e = gm.events[:]
        gm.Plyr.set_plyr_img(DVEC, 'init-shift', gm.world_pcenter)
        gm.buttonUp = { SP_ACTION: True }

        gm.map_dirty_where = [] # Where has the map been altered?
        gm.map_blocks = {} # validate type -> list of rects that block

        # Initialize some enemies, debug:
        pkmn_id = '1' # stub
#        for team, pos in [ ('enemy1', (1,2)), ('plyr',(6,6)) ]:
#        for team, pos in [ ('wild', (1,2)),  ('wild', (8,7)),
#                    ('wild', (5,2)), ('wild', (5,9)), ('wild', (12,2)),
#                    ('wild', (1,8)), ('wild', (11,2)), ('wild', (11,12))]:
        #for team, pos in [ ('wild', (1,2)),  ('wild', (3,3))]:
        for team, pos in [ ('wild', (1,2))]:
            optns = {'which_pkmn':pkmn_id, 'pos':pos}
            optns['init_shift'] = (0, -int( (gm.tile_y_size * float(\
                        gm.cp.get('pkmn'+pkmn_id, 'img_shift')))//1))
            attrs = ['stepsize_x', 'stepsize_y', 'move_range', 'move_speed',\
                    'base_health', 'catch_threshold'] 
            for a in attrs:
                optns[a] = gm.db.execute( ' SELECT '+a+\
                        ' FROM pkmn_prefabs WHERE pkmn_id=?;', \
                        (pkmn_id,)).fetchone()[0]
            gm.create_new_ai(team,'pkmn', optns)

        # Init mouse interface...
        #gm.Mouse = MouseAgent(gm)
        gm.MouseTarget = MouseTarget(gm)
        gm.PlyrHighlighter = Highlighter(gm)
    
    ''' _reset_events: clear the active stored events '''
    def _reset_events(gm):
        gm.events = [False] * (gm.n_plyr_dirs + gm.n_plyr_actions)

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
        if down[pygame.K_SPACE]: gm.events[SP_ACTION]=True
        if down[pygame.K_q]:     sys.exit()
        if (not gm.buttonUp[SP_ACTION]) and (not down[pygame.K_SPACE]):
            gm.buttonUp[SP_ACTION] = True 
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
                
    def notify_new(gm, agent):
        tidx, tidy = agent.get_tpos()
        gm.db.execute('INSERT INTO tile_occupants VALUES (?,?,?,?,?);',
               (agent.uniq_id, tidx, tidy, agent.string_sub_class, agent.team));

#    def notify_move(gm, prev_tid, next_tid, uniq_id, team=None, atype=None):
#        if next_tid==NULL_POSITION or prev_tid==NULL_POSITION:
#            raise Exception()
#        gm.db.execute('''UPDATE OR FAIL tile_occupants SET tx=?, ty=? \
#                WHERE uniq_id=?''', (next_tid[X], next_tid[Y], uniq_id))
#        
    def notify_move(gm, agent, next_tid=None):
        if not next_tid: next_tid = agent.get_tpos();
        gm.db.execute('''UPDATE OR FAIL tile_occupants SET tx=?, ty=? \
                WHERE uniq_id=?''', (next_tid[X], next_tid[Y], agent.uniq_id))
        
    def notify_kill(gm, agent):
        gm.db.execute('DELETE FROM tile_occupants WHERE uniq_id=?;', \
                (agent.uniq_id, ))

    def foo(gm):
        if not next_tid==NULL_POSITION:
            gm.db.execute('INSERT INTO tile_occupants VALUES (?,?,?,?,?);',
                    (uniq_id, next_tid[X], next_tid[Y], atype, team));
        if not prev_tid==NULL_POSITION:
            gm.db.execute('''DELETE FROM tile_occupants WHERE uniq_id=?
                    AND tx=? AND ty=?;''', (uniq_id, prev_tid[X], prev_tid[Y]))

    ''' Query a specific tile for occupants and tile info. Supply WHAT columns.'''
    def query_tile(gm, tid, what='*'): 
        if type(what)==list: what = ','.join(what)
        ret = gm.db.execute( "SELECT "+what+\
                " FROM tilemap WHERE tx=? AND ty=?;", tid).fetchall()
        return gm.get_tile_occupants(tid), ret

    # Returns: select or full list of tuples [agent_type, uniq_id, team].
    def get_tile_occupants(gm, tid=None):
        if tid==None:
            return gm.db.execute(\
                    """SELECT tx,ty,agent_type FROM tile_occupants;""")\
                    .fetchall()
        return gm.db.execute(\
                """SELECT agent_type,uniq_id,team FROM tile_occupants 
                    WHERE tx=? AND ty=?;""", tid).fetchall()

    



    def get_multitiles(gm, tiles, what):
#        print tiles
        if what in ('block_plyr', 'block_pkmn'):
            l1 = []
            l1 =  gm.db.execute( \
                """SELECT tx,ty FROM tile_occupants;""").fetchall()
            l2 =  gm.db.execute( "SELECT tx,ty FROM tilemap WHERE "+\
                    what+"=?;", (u'false',)).fetchall()
            return [t for t in tiles if (t not in l1 and t in l2)] # valids

#            return l1, l2




    def notify_catching(gm, tid, what_pokeball, catches):
        for agent in gm.ai_entities:
#            print agent.uniq_id, catches, agent.uniq_id in catches
#            print gm.Plyr.did_catch(agent.get_center(), 
            if agent.uniq_id in catches:
                if gm._p_to_t(agent.get_center())==tid: 
                    agent.send_message('getting caught', what_pokeball)
                else:
                    print "Argh, almost caught:", agent.get_center(), tid





GM = GameManager()
GM.load() 
GM.run_game()
