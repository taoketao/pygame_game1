
# 8/13: for the current rewrite, a (*) marks objects that have been checked
# and passed for the next iteration.

import pygame, sys, operator
import sqlite3 as sql
import ConfigParser
import numpy as np
from PIL import Image, ImageOps

from utilities import *
from agents2 import *
from display import Display
                    
''' Map Options '''
MAP_LEVEL_CONFIG = './config7.ini'
TILE_SIZE = (64,56);
TILE_SIZE = (32,28);
TILE_SIZE = (25,25);
HUD_SIZE = TILE_SIZE[Y] # one tile
X = 0;  Y = 1

SP_ACTION = 4;
ACTIONS = [SP_ACTION]

DEFAULT_FPS = 10


''' GameManager: Whole wrapper class for a organizing a game level. '''
class GameManager(object): # *
    def __init__(gm, which_config_file=None): 
        if not which_config_file:  gm.which_config_file = MAP_LEVEL_CONFIG 
        else:                      gm.which_config_file = which_config_file 

    def load(gm): # *
        gm._init_database()
        gm._init_global_fields() # requires loaded maps from _init_database
        pygame.init()
        gm._init_display()
        #gm.display.std_render()

    """ ---------------------------------------------------------------------- """
    """    Initialization Procedures, called once prior to a new game level.   """
    """ ---------------------------------------------------------------------- """

    ''' Create databases '''
    def _init_database(gm): # *
        gm.tile_size = (gm.tile_x_size, gm.tile_y_size) = TILE_SIZE
        # Initialize databases
        _db = sql.connect(':memory:').cursor() # formerly broken up with cxn
        _db.execute(''' CREATE TABLE tilemap ( 
                                tx INT, ty INT,             px INT, py INT, 
                                base_tid TEXT NOT NULL,     ent_tid TEXT,   
                                block_plyr BOOL,            block_pkmn BOOL,
                                coll_present BOOL,
                                coll_px INT,    coll_py INT,    
                                coll_pw INT,    coll_ph INT ); ''')

        _db.execute(''' CREATE TABLE pkmn_prefabs (     name TEXT, 
                                pkmn_id INT,            img_shift FLOAT, 
                                stepsize_x FLOAT,       stepsize_y FLOAT,
                                move_speed FLOAT,       move_range TEXT,
                                base_health INT,        base_move_1 TEXT, 
                                base_move_2 TEXT,       base_move_3 TEXT,
                                catch_threshold INT  );''')

        _db.execute(''' CREATE TABLE tile_occupants (uniq_id INT NOT NULL,  
                                tx INT, ty INT, agent_type TEXT, team TEXT);''')

        _db.execute(''' CREATE TABLE agent_locations (
                        uniq_id INT NOT NULL, 
                        tx INT NOT NULL,    ty INT NOT NULL,
                        px INT NOT NULL,    py INT NOT NULL   ); ''') 

        
        cp = ConfigParser.ConfigParser()
        cp.read(gm.which_config_file)
        # Populate databases using configuration data
        for pkmn_id in cp.get('list_of_pkmn_prefabs','ids').split(','):
            if pkmn_id=='0': continue
            vals = [i for _,i in cp.items('pkmn'+pkmn_id)] 
            # ^^ Must be in order as specified above! ^^
            nvals = ','.join(['?']*len(vals))
            _db.execute('INSERT INTO pkmn_prefabs VALUES ('+nvals+')',vals);
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
    def _init_global_fields(gm): # *
        gm.uniq_id_counter = 100
        gm.entities = {}
        gm._smoothing = 1.0          # animation smoothing factor
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = \
                            multpos(gm.map_num_tiles, gm.tile_size)

    def ts(gm): return gm.tile_size # *
    def smoothing(gm): return gm._smoothing # *

    ''' _init_display:  set up the Display.'''
    def _init_display(gm): # *
        gm.hud_size = (gm.map_x, HUD_SIZE)
        gm.screen_size = (gm.map_x, gm.map_y+HUD_SIZE) # For now
        gm.display = Display(gm)


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

    def active_entities(gm): return gm.Agents.values()
    def BroadcastAll(gm, fn_name): 
        return map(operator.methodcaller(fn_name), gm.active_entities())

    def _run_frame(gm):
#        raw_input("Launch Next frame:")
        gm._punch_clock()
        gm._get_events()
        gm.BroadcastAll('Reset')
        gm.BroadcastAll('PrepareAction')
        gm.BroadcastAll('DoAction')
#        for ae in gm.active_entities():   ae.Reset()
#        for ae in gm.active_entities():   ae.PrepareAction()
#        for ae in gm.active_entities():   ae.DoAction()
#        map(PrepareAction,  gm.active_entities)
#        map(DoAction,       gm.active_entities)
        gm.display.std_render()


    ''' Using the clock, determine the time that passed since last frame
        and calculate a multiplicative factor to smooth animation. '''
    def _punch_clock(gm):
        gm.clock.tick(gm.fps)
        this_tick = pygame.time.get_ticks()
        dt = (this_tick - gm.last_tick)
        cur_true_fps = gm.clock.get_fps()
        if cur_true_fps<gm.fps-1 and gm.fps_itr==0:
            print 'fps:', cur_true_fps
        gm._smoothing = dt * (gm.fpms if gm.last_tick>0 else 1)
        gm.last_tick = this_tick
        gm.fps_itr = (gm.fps_itr+1)%10

    ''' Events Schema: each numbered RunGame event maps to a bool
        array of whether the event happened. '''
    # todo: redo this all. Want event queue, not instantaneous events.
    def _get_events(gm):
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

    def create_new_ai(gm, team, entity, optns):
        if entity=='pkmn':
            pkmn_ai = AIAgent(gm, team, options=optns)
            gm.ai_entities.append(pkmn_ai)
            gm.agent_entities.append(pkmn_ai)
            pkmn_ai.send_message('initialized as free')
            return pkmn_ai
        raise Exception("Internal error: AI type not recognized.")





    def _init_game(gm, fps=DEFAULT_FPS):
        gm.fps = float(fps)     # frames per second
        gm.fpms = fps/1000.0    # frames per millisecond
        gm.fps_itr = 0
        gm.clock = pygame.time.Clock()  # clock object for frame smoothness
        gm.last_tick = 0            # clock counter field

        gm.Agents = { \
                'Player': Player(gm, 'init'),\
#                'Mouse': MouseTarget(gm), \
#                'player highlighter': Highlighter(gm)   \
                }

        gm._reset_events()
        gm.prev_e = gm.events[:]
        gm.buttonUp = { SP_ACTION: True }

        if 'false'=='Pass this now via comment':
            pkmn_id = '1' # stub
            for team, pos in [ ('wild', (1,2)),  ('wild', (3,3))]:
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

    
    ''' _reset_events: clear the active stored events '''
    def _reset_events(gm):
        gm.events = [False] * (gm.Agents['Player'].get_num_actions())


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

#----------#----------#----------#----------#----------#----------#----------
#       Access functions: use notify/request when talking to this GM,
#       and use query/message when talking to other agents. *
#----------#----------#----------#----------#----------#----------#----------

    def notify_new_agent(gm, agent_ref, init_tpos, init_ppos):
        if not divvec(init_ppos, gm.tile_size)==init_tpos: raise Exception()
        gm.db.execute('INSERT INTO agent_locations VALUES (?,?,?,?,?);',\
                      ( agent_ref.uniq_id, \
                        init_tpos[X], init_tpos[Y], \
                        init_ppos[X], init_ppos[Y] ))
        pass # Stub. This maintains a database that requires tpos 
        # (for others' access) and can take optional ppos or locpos as well;
        # ppos will always be inferred, and locpos can be used for other modes
        # of interaction that are better handled as converted back-and-forth.

    def notify_pmove(gm, agent_id, ploc, opt_dont_update_tpoc=False, img=None):
        tx, ty = divvec(ploc, gm.ts())
        gm.db.execute('''UPDATE OR FAIL agent_locations SET tx=?, ty=?, px=?, py=?
             WHERE uniq_id=?''', (tx, ty, ploc[X], ploc[Y], agent_id))

    def notify_imgChange(gm, ref_who, img_name, where='not provided'):
        if where=='not provided':
            where = gm.request_ppos(ref_who.uniq_id)
        where = sub_aFb(ref_who.default_img_offset, where)
        { True: gm.display.queue_A_img, False: gm.display.queue_E_img}[\
                isinstance(ref_who, VisualStepAgent)](ref_who.uniq_id, img_name, where)

    def request_tpos(gm, agent_id):
        if not type(agent_id)==int:
            agent_id = gm.Agents[agent_id].uniq_id
        q = 'SELECT tx,ty FROM agent_locations WHERE uniq_id=?;'
        return gm.db.execute(q, (agent_id,)).fetchall()[0]

    def request_ppos(gm, agent_id): # return if possible, else NULL_POSITION.
        q = 'SELECT px,py FROM agent_locations WHERE uniq_id=?;'
        return gm.db.execute(q, (agent_id,)).fetchall()[0]

    def request_what_at(gm, what, tpos): pass  # perhaps break this up....




#----------#----------#----------#----------#----------#----------#----------
#       End of fresh code * (stubs)
#----------#----------#----------#----------#----------#----------#----------
                
#    def notify_new(gm, agent):
#        tidx, tidy = agent.get_tpos()
#        gm.db.execute('INSERT INTO tile_occupants VALUES (?,?,?,?,?);',
#               (agent.uniq_id, tidx, tidy, agent.species, agent.team));
#
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
