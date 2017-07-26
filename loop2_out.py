# IPython log file
import pygame, random, sys
import sqlite3 as sql
import ConfigParser


''' Options '''
MAP_LEVEL_CONFIG = './config2.ini'
TILE_SIZE = (64,64);
X = 0;  Y = 1

UDIR = 0;       LDIR = 1;       DDIR = 2;       RDIR = 3
EVENTS = [UDIR, LDIR, DDIR, RDIR]

PLYR_COLL_WIDTH, PLYR_COLL_SHIFT = 0.4, 0.2
PLYR_IMG_SHIFT_INIT = 0.125
BLOCK_COLL_WIDTH, BLOCK_COLL_SHIFT = 0.3, -0.3
DEFAULT_STEPSIZE = 0.15
DEFAULT_FPS = 30


class AIAgent(object):
    def __init__(ai, gm, team): 
        ai.gm = gm
        ai.spr = pygame.sprite.DirtySprite()
        ai.pkmn_id = -1
        ai.img_id = None
        ai.team = team
        ai._rect_init=False

    def set_img(ai, _dir):
        # assume pkmn...
        if ai.pkmn_id<0: raise Exception('internal: id not set')
        if type(_dir)==int:
            _dir = {UDIR:'u', LDIR:'l', DDIR:'d', RDIR:'r'}[_dir]
        if ai.img_id==_dir: return
        ai.spr.image = ai.gm.imgs['pkmn sprite '+str(ai.pkmn_id)+_dir]
        ai._rect_init = True
        ai.img_id = _dir
        ai.spr.dirty=1

    def act(ai): pass
    def set_tpos(ai, pos_tid): 
        try: assert(len(pos_tid)==2 and type(pos_tid[X])==int and \
                    type(pos_tid[Y])==int)
        except: raise Exception('Bad tile coords')
        ai.pos_tid = (ai.pos_tx, ai.pos_ty) = pos_tid
        ai.pos_pix = (ai.pos_px, ai.pos_py) = ai.gm.map_db.execute(\
                "SELECT px, py FROM tilemap WHERE tx=? AND ty=?;", \
                (ai.pos_tx, ai.pos_ty)).fetchone()
        if not ai._rect_init: 
            ai.spr.rect = ai.spr.image.get_rect()
            ai._rect_init = True
        ai.spr.rect.move_ip(ai.pos_pix)
        print(ai.pos_tid, ai.pos_pix, ai.spr.rect)
        ai.spr.dirty=1

    def set_ppos(ai, ppix): 
#        ai.spr.rect.move_ip(ppix)
        ai.pos_pix = (ai.pos_px, ai.pos_py) = ppix
        ai._update_tpos_from_ppos(ai.pos_pix)

    def move_ppos(ai, move_pix):
        print '<',ai.spr.rect
        print '-',ai.pos_pix, ai.pos_tid, ai.pos_px, ai.pos_py,';',move_pix
        ai.set_ppos((ai.pos_px + move_pix[X], ai.pos_px + move_pix[X] ))
        print '>',ai.spr.rect

    def _update_tpos_from_ppos(ai, ppos):
        ai.pos_tid = (ai.pos_tx, ai.pos_ty) = \
            (int(ppos[X]//ai.gm.tile_x_size), int(ppos[Y]//ai.gm.tile_y_size))

    def get_tpos(ai): return ai.pos_tid
    def get_ppos(ai): return ai.pos_pix

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
            block_plyr BOOL,                altered BOOL          ); ''')
        # what does altered mean...?
        cp = ConfigParser.ConfigParser()
        cp.read(gm.which_map_file)
        curR, curC = 0,0
        for char in cp.get('map','map'):
            if char== '\n':
                curC += 1; curR = 0; continue;
            base_tid = char if char in ['d','g'] else ['g']
            _db.execute(''' INSERT INTO tilemap 
                (tx, ty, px, py, base_tid, ent_tid, block_plyr, altered)
                VALUES (?,?,?,?,?,?,?,?); ''', \
                        (curR, curC, gm.tile_x_size*curR, gm.tile_y_size*curC, 
                        cp.get(char, 'base_tid'),   cp.get(char, 'ent_tid'), 
                        cp.get(char, 'block'),      True))
            curR += 1
        gm.map_db = _db
        gm.map_num_tiles = (curR, curC+1)
        gm.cp = cp

    ''' Important global fields '''
    def _init_global_fields(gm):
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = tuple( \
                [gm.map_num_tiles[i] * gm.tile_size[i] for i in (X,Y)])
        gm.world_center = ( gm.map_x // 2 - gm.tile_x_size // 2, \
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
        #gm.sprites = pygame.sprite.LayeredDirty([])
        gm.sprites = []
        gm.plyr_team = pygame.sprite.LayeredDirty([])
        gm.enemy_team_1 = pygame.sprite.LayeredDirty([])
        #gm.ai_entities = pygame.sprite.LayeredDirty([])
        gm.ai_entities = []
        
    def _init_plyr_object(gm): 
        gm.plyr = pygame.sprite.DirtySprite()
        gm.plyr.image = gm.imgs['player sprite 1']
        gm.plyr.rect = gm.plyr.image.get_rect().move(gm.world_center).\
                    move((0,-int(PLYR_IMG_SHIFT_INIT*gm.tile_y_size//1)))
        gm.plyr.dirty=1
        gm.plyr.add( gm.plyr_team)
        gm.sprites.append(gm.plyr)
#    def plyr_collider(gm, amt=0.8): return gm.plyr.rect.inflate(\
#            (gm.tile_x_size * -amt, gm.tile_y_size * -amt) )
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

    def clear_screen(gm): gm.screen.blit(gm.background,(0,0))

    def _basic_render(gm):
        pygame.display.update(pygame.sprite.LayeredDirty(gm.sprites).\
                        draw(gm.screen))
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
            gm.create_new_ai('enemy1','pkmn', (1,3), {'which_pkmn':'1'})
            gm.create_new_ai('enemy1','pkmn', (2,2), {'which_pkmn':'1'})
            gm.create_new_ai('enemy1','pkmn', (2,3), {'which_pkmn':'1'})
            gm.create_new_ai('enemy1','pkmn', (3,3), {'which_pkmn':'1'})

        to_update = []
        for agent in gm.ai_entities:
            did_agent_move = agent.act()
            if did_agent_move or any([agent.spr.rect.colliderect(u.rect) \
                                      for u in to_update]):
                to_update.append(agent.spr)
        if gm._handle_plyr_movement() or any([gm.plyr.rect.colliderect(u.rect)\
                                              for u in to_update]):
            to_update.append(gm.plyr)

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
            agent.set_img('d')
            agent.set_tpos(init_pos)
            agent.move_ppos((0,-int((gm.tile_y_size * float(gm.cp.get(\
                    'pkmn'+optns['which_pkmn'], 'img_shift')))//1)))
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
        gm.plyr_step_cycler = 0     # animation counter for player sprite
        gm.smoothing = 1.0          # animation smoothing factor
        gm._reset_events()
        gm.prev_e = gm.events[:]

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
        next_e = gm.validate_move('plyr', gm.events) # restrict if invalid
#        gm._debugutility_print_dir(prev_e, 'prev')
#        gm._debugutility_print_dir(next_e, '  ->  next')
#        gm._debugutility_print_dir(gm.events, '  from  event')
        if not any(prev_e) and any(next_e): # started walking
            if sum(next_e)>1: # pick one of the options
                optns = [i for i in range(gm.n_plyr_dirs) if next_e[i]==1]
                next_e = [False]*gm.n_plyr_dirs
                next_e[random.choice(optns)] = True
            gm._update_plyr_pos(next_e)
            gm._update_plyr_img(next_e, 'moving')
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
                gm._update_plyr_pos(new)
                gm._update_plyr_img(new, 'moving')
                return True
            gm._update_plyr_pos(next_e)
            gm._update_plyr_img(next_e, 'moving')
            gm.prev_e = next_e
            return True
        if any(prev_e) and prev_e==next_e: # continue walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            gm._update_plyr_pos(next_e)
            gm._update_plyr_img(next_e, 'moving')
            return True
        if any(prev_e) and not any(next_e): # stop walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            gm._update_plyr_img(prev_e, 'stopped')
            gm.plyr.dirty=1
            return True # last update
        if not any(prev_e) and not any(next_e): # continue stopped
            gm._update_plyr_img(prev_e, 'stopped')
            return False


    """ validate_move: given an move attempt by an agent, update move. """
    def validate_move(gm, agent, parameter):
        if agent=='plyr':
            if not any(parameter): return parameter
            new_param = parameter[:]
            query = "SELECT px, py, ent_tid FROM tilemap WHERE block_plyr==?"
            under_tiles = []
            plyr_r = gm.deflate(gm.plyr.rect, PLYR_COLL_WIDTH, PLYR_COLL_SHIFT)
            plyr_r.move_ip(gm._new_pos_plyrstep(new_param)) # Would step result in coll?
            for px, py, ent in gm.map_db.execute(query, ('true',)).fetchall():
                block_r = gm.deflate(pygame.Rect((px,py), TILE_SIZE), \
                        BLOCK_COLL_WIDTH, BLOCK_COLL_SHIFT)
                if block_r.colliderect(plyr_r):
                    under_tiles.append((px,py))
            for px,py in under_tiles:
                if px < gm.plyr.rect.x:    new_param[LDIR] = False
                if px > gm.plyr.rect.x:    new_param[RDIR] = False
                if py < gm.plyr.rect.y:    new_param[UDIR] = False
                if py > gm.plyr.rect.y:    new_param[DDIR] = False
            return new_param
        else: raise Exception("Not implemented yet")


    ''' _update_plyr_pos: return a pos tuple that indicates how much to 
        move an agent, according to the player's step sizes. '''
    def _update_plyr_pos(gm, dirs):
        gm.plyr.rect.move_ip(gm._new_pos_plyrstep(dirs))
        gm.plyr.dirty=1
        return True

    def _new_pos_plyrstep(gm, dirs):
        dx = (dirs[RDIR]-dirs[LDIR]) * gm.smoothing * gm.stepsize_x
        dy = (dirs[DDIR]-dirs[UDIR]) * gm.smoothing * gm.stepsize_y
        return (dx,dy)

    def _update_plyr_img(gm, dirs, mode):
        if not any(dirs): dirs[DDIR] = True # default, face down.
        gm.plyr_step_cycler = {'moving': gm.plyr_step_cycler+1, 'stopped':0}[mode]
        gm.plyr.image = gm.imgs['player sprite ' + str(\
                dirs.index(True) * gm.n_plyr_anim + 1 + \
                {'moving':(gm.plyr_step_cycler % gm.n_plyr_anim), \
                 'stopped':0}[mode])]



GM = GameManager()
GM.initialize_internal_structures()
GM.run_game()
