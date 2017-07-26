# IPython log file
import pygame, random, sys
import sqlite3 as sql
import ConfigParser


''' Options '''
MAP_LEVEL_CONFIG = './config2.ini'
TILE_SIZE = (64,64)

UDIR = 0;       LDIR = 1;       DDIR = 2;       RDIR = 3
EVENTS = [UDIR, LDIR, DDIR, RDIR]

class GameManager(object):
    ''' Whole wrapper class for a organizing a game level. '''
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

    ''' Important global fields '''
    def _init_global_fields(gm):
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = tuple( \
                [gm.map_num_tiles[i] * gm.tile_size[i] for i in (0,1)])
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
        ''' >>> [processing]:  '''
        for tnm, t in gm.imgs.items():
            tmp = pygame.Surface(gm.tile_size).convert_alpha()
            pygame.transform.scale(t, gm.tile_size, tmp)
            t.fill((255,255,255,255), None, pygame.BLEND_RGBA_MULT)
            gm.imgs[tnm]=tmp.convert_alpha()
    
    def _init_sprite_macros(gm): 
        gm.sprites = pygame.sprite.LayeredDirty([])
        gm.plyr_team = pygame.sprite.LayeredDirty([])
        
    def _init_plyr_object(gm): 
        gm.plyr = pygame.sprite.DirtySprite()
        gm.plyr.image = gm.imgs['player sprite 1']
        gm.plyr.rect = gm.plyr.image.get_rect().move(gm.world_center).\
                            move((0,-gm.tile_y_size//8))
        gm.plyr.dirty=1
        gm.plyr.add(gm.sprites, gm.plyr_team)
#    def plyr_collider(gm, amt=0.8): return gm.plyr.rect.inflate(\
#            (gm.tile_x_size * -amt, gm.tile_y_size * -amt) )
    def deflate(gm, targ, pct):
        return targ.inflate((gm.tile_x_size * -pct, gm.tile_y_size * -pct))
    def _init_start_map(gm):
        gm.draw_background()
        gm.background = pygame.Surface(gm.map_pix_size)
        gm.draw_background(gm.background)
        pygame.display.update(gm.sprites.draw(gm.screen))




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



    """ run_game: launch a game and loop it  """
    def run_game(gm, max_num_epochs_test):
        _rg = RunGame(gm)
        for _ in range(max_num_epochs_test):
            _rg.run_frame()

    """ validate_action: given an action by an agent, affect it if needed. """
    def validate_action(gm, agent, action, parameter):
#        print gm.map_db.execute("SELECT DISTINCT block_plyr FROM tilemap").fetchall()
#        sys.exit()
        if agent=='plyr' and action=='move':
            new_param = parameter[:]
            query = "SELECT px, py, ent_tid FROM tilemap WHERE block_plyr==?"
            under_tiles = []
            for px, py, ent in gm.map_db.execute(query, ('true',)).fetchall():
                r = gm.deflate(pygame.Rect( (px,py), TILE_SIZE), 0.5)
                r.move(
                if r.colliderect(gm.deflate(gm.plyr.rect, 0.5)):
                    under_tiles.append(r)
            print under_tiles
            for r in under_tiles:
                if r.x < gm.plyr.rect.x:    new_param[LDIR] = False
                if r.x > gm.plyr.rect.x:    new_param[RDIR] = False
                if r.y < gm.plyr.rect.y:    new_param[UDIR] = False
                if r.y > gm.plyr.rect.y:    new_param[DDIR] = False
            return new_param
        else: raise Exception("Not implemented yet")

""" ---------------------------------------------------------------------- """
""" Class RunGame handles the mechanics of running a level. Specifically,  """
"""    it manages all the sprites and interactions between them as the     """
"""    master over sequentially-sensitive events.                          """
""" ---------------------------------------------------------------------- """
class RunGame(object):

    def __init__(rg, gm, fps=30, stepsize_factor=0.15):
        rg.gm = gm
        rg.fps = float(fps)
        rg.fpms = fps/1000.0
        rg.stepsize_x = stepsize_factor * rg.gm.tile_x_size
        rg.stepsize_y = stepsize_factor * rg.gm.tile_y_size
        rg._init_counters()

    def _init_counters(rg):
        rg.clock = pygame.time.Clock()
        rg.last_tick = 0
        rg.step_cycler = 0
        rg._reset_events()

    def _reset_events(rg): rg.events = [False] * rg.gm.n_plyr_dirs

    def _punch_clock(rg):
        rg.clock.tick(rg.fps)
        this_tick = pygame.time.get_ticks()
        dt = (this_tick - rg.last_tick)
        sm = dt * rg.fpms if rg.last_tick>0 else 1
        rg.last_tick = this_tick
        return sm, dt

    ''' Events Schema: each numbered RunGame event maps to a bool
        array of whether the event happened. '''
    def _update_events(rg):
        rg._reset_events()
        pygame.event.pump()
        down = pygame.key.get_pressed()
        if down[pygame.K_UP]:    rg.events[UDIR]=True
        if down[pygame.K_DOWN]:  rg.events[DDIR]=True
        if down[pygame.K_LEFT]:  rg.events[LDIR]=True
        if down[pygame.K_RIGHT]: rg.events[RDIR]=True
        if down[pygame.K_w]:     rg.events[UDIR]=True
        if down[pygame.K_s]:     rg.events[DDIR]=True
        if down[pygame.K_a]:     rg.events[LDIR]=True
        if down[pygame.K_d]:     rg.events[RDIR]=True
        if down[pygame.K_q]:     sys.exit()
        pygame.event.clear()

    def _handle_plyr_movement(rg, smoothing):
        prev_e = rg.events[:]
        rg._update_events()

        if sum(rg.events)>1: 
            rg.events=prev_e
        next_e = rg.gm.validate_action('plyr', 'move', rg.events)
        
        if not any(prev_e) and any(next_e): # started walking
            rg.gm.plyr.rect = rg._update_plyr_pos(next_e, smoothing)
            rg._update_plyr_img(next_e, 'moving')
            return True
        if any(prev_e) and prev_e==next_e: # continue walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            rg._update_plyr_img(next_e, 'moving')
            rg._update_plyr_pos(next_e, smoothing)
            return True
        if any(prev_e) and not any(next_e): # stop walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            rg._update_plyr_img(prev_e, 'stopped')
            rg.gm.plyr.dirty=1
            return True # last update
        if not any(prev_e) and not any(next_e): # continue stopped
            rg._update_plyr_img(prev_e, 'stopped')
            return False

    ''' _update_plyr_pos: return a pos tuple that indicates how much to 
        move an agent, according to the player's step sizes. '''
    def _update_plyr_pos(rg, dirs, smoothing):
        dx = (dirs[RDIR]-dirs[LDIR]) * smoothing * rg.stepsize_x
        dy = (dirs[DDIR]-dirs[UDIR]) * smoothing * rg.stepsize_y
        rg.gm.plyr.rect = rg.gm.plyr.rect.move((dx,dy))
        #  gm.plyr.rect.move_ip((dx,dy))
        rg.gm.plyr.dirty=1
        return True

    def _update_plyr_img(rg, dirs, mode):
        if not any(dirs): dirs[DDIR] = True
        rg.step_cycler = {'moving': rg.step_cycler+1, 'stopped':0}[mode]
        rg.gm.plyr.image = rg.gm.imgs['player sprite ' + str(\
                dirs.index(True) * rg.gm.n_plyr_anim + 1 + \
                {'moving':(rg.step_cycler % rg.gm.n_plyr_anim), \
                 'stopped':0}[mode])]

    def run_frame(rg):
        smoothing, paused_t = rg._punch_clock()
        movement = rg._handle_plyr_movement(smoothing)
        #rg.gm.sprites.clear(rg.gm.screen, background)
        if movement: rg.gm.clear_screen()
        pygame.display.update(rg.gm.sprites.draw(rg.gm.screen))
        #self.wander_player_testfn(smoothing=smoothing_multiplier)
#            self.move_player_testfn(smoothing=smoothing_multiplier)




        '''
        def move_player_testfn(self, smoothing=1.0, stepsize=0.1, events=None):
            direction = random.randint(0,4) # uldr
            if direction>=4: 
                self.step_cycler = 0
                return
            plyr.image = imgs['player sprite '+str(direction*n_anim+1+self.step_cycler%n_anim)]
            mx, my = 0,0
            if direction==0: my -= smoothing*stepsize*tile_y_size
            if direction==1: mx -= smoothing*stepsize*tile_x_size
            if direction==2: my += smoothing*stepsize*tile_y_size
            if direction==3: mx += smoothing*stepsize*tile_x_size
            plyr_pos = (plyr.rect.centerx, plyr.rect.bottom)
            plyr.rect = plyr.rect.move((mx,my))
            plyr.dirty=1
            all_sprites.clear(screen, background)
            pygame.display.update(all_sprites.draw(screen))
            self.step_cycler += 1

        def wander_player_testfn(self, smoothing=1.0, stepsize=0.1):
            n_anim = 3
            direction = random.randint(0,4) # uldr
            if direction>=4: 
                self.step_cycler = 0
                return
            plyr.image = imgs['player sprite '+str(direction*n_anim+1+self.step_cycler%n_anim)]
            mx, my = 0,0
            if direction==0: my -= smoothing*stepsize*tile_y_size
            if direction==1: mx -= smoothing*stepsize*tile_x_size
            if direction==2: my += smoothing*stepsize*tile_y_size
            if direction==3: mx += smoothing*stepsize*tile_x_size
            plyr_pos = (plyr.rect.centerx, plyr.rect.bottom)
            plyr.rect = plyr.rect.move((mx,my))
            plyr.dirty=1
            all_sprites.clear(screen, background)
            pygame.display.update(all_sprites.draw(screen))
            self.step_cycler += 1
            '''







GM = GameManager()
GM.initialize_internal_structures()
GM.run_game(10000)
