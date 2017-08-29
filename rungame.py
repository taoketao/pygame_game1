''' Game Options '''
DEFAULT_FPS = 15 # should be a cap: lower than expected max FPS
MAP_LEVEL_CONFIG = './config_collision.ini'#'./config7.ini'
TILE_SIZE = (40,35);

''' ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
'''#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
''' ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
'''#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
''' ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'''

# 8/13: for the current rewrite, a (*) marks objects that have been checked
# and passed for the next iteration.

import pygame, sys, operator
import sqlite3 as sql
import ConfigParser
import numpy as np
from PIL import Image, ImageOps

from utilities import *
from agents import *
from display import Display
                    
HUD_SIZE = TILE_SIZE[Y] # one tile
X = 0;  Y = 1

SP_ACTION = 4;
ACTIONS = [SP_ACTION]



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

#        _db.execute(''' CREATE TABLE tile_occupants (uniq_id INT NOT NULL,  
#                                tx INT, ty INT, agent_type TEXT, team TEXT);''')

        _db.execute(''' CREATE TABLE agent_status (
                        uniq_id INT NOT NULL,   img_str TEXT,
                        tx INT NOT NULL,        ty INT NOT NULL,
                        px INT NOT NULL,        py INT NOT NULL,
                        agent_type TEXT,        team TEXT           ); ''') 

        
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
        gm.reserved_tiles = {}
        gm.frame_iter = 0
        gm._smoothing = 1.0      # animation smoothing factor
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = \
                            multpos(gm.map_num_tiles, gm.tile_size)
        _for_reference=''' gm.tile_size = (gm.tile_x_size, gm.tile_y_size) '''

    def ts(gm): return gm.tile_size # *
    def smoothing(gm): return gm._smoothing

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
        gm.TEMPORARY_VARIABLE_DEBUG = True
        gm._init_game()
        FRAME_COUNTER = 0
        for _ in range(max_num_epochs_test):
            print '\n\nFRAME_COUNTER', FRAME_COUNTER; 
            FRAME_COUNTER+=1
            gm._run_frame()
#            print "\t Status:", gm.db.execute(sql_tile_locs).fetchall(), gm.reserved_tiles
            print 'reservations:'
            for k,v in sorted(gm.reserved_tiles.items()): print k,v
            gm._pretty_print_sql(sql_tile_locs)
    
    def _pretty_print_sql(gm, sql_str):
        print '**************************'
        res = gm.db.execute(sql_str).fetchall()
        if len(res)==0: print '\t[None]'; return
#        l = [0]*len(res[0])
        res.insert(0,sql_str.split(','))
        l = [max([len(str(v[i])) for v in res]) for i in range(len(res[0]))]
#        for vi,v in enumerate(sql_str.split(',')): 
#            s='  {:>'+str(l[vi])+'}'
#            print s.format(v),
        for item in res:
            print '\t',
            for vi,v in enumerate(item): 
                s='  {:'+str(l[vi])+'}'
                print s.format(v),
            print '\n',
        print ''

    def _init_game(gm, fps=DEFAULT_FPS):
        gm.fps = float(fps)     # frames per second
        gm.fpms = fps/1000.0    # frames per millisecond
        gm.fps_itr = 0
        gm.clock = pygame.time.Clock()  # clock object for frame smoothness
        gm.last_tick = 0            # clock counter field
        gm.update_queue = []
        gm.prev_agent_information = []

        gm.Agents, gm.Effects = {},{}

        gm.addNew('Agents', 'Player', Player )
        gm.addNew('Effects', 'mouse highlighter', MouseTarget )
        for (i,j) in [(1,1),(1,2),(2,1),(2,2),(3,2),(3,3)]:
            s=str(i)+','+str(j)
#            if gm.TEMPORARY_VARIABLE_DEBUG:
            if np.random.rand()<0.5:
                gm.addNew('Agents', 'PkmnPlyr'+s, AIAgent, init_tloc=(i,j),\
                        uniq_name='PkmnPlyr'+s, hbcolor='b', team='plyr', \
                        pokedex=1, health=20, orientation='vertic')
                gm.TEMPORARY_VARIABLE_DEBUG=False
            else:
                gm.addNew('Agents', 'PkmnWild'+s, AIAgent, init_tloc=(i,j),\
                        uniq_name=\
                        'PkmnWild'+s, hbcolor='r', team='wild', pokedex=1, 
                        health=5*i+10*j)
#                        health=np.random.choice(5*i+15*j))
        for g,v in gm.entities.items():
            if isinstance(v,StatusBar): 
                print '\t',g,':',v, v.metric, v.cur_metric,v.init_metric
#        import sys
#        sys.exit()

        gm.process_update_queue() # after entities have been initialized...
        gm._reset_events()
        gm.prev_e = gm.events[:]
        gm.buttonUp = { SP_ACTION: True }
        gm.display.std_render()

    def addNew(gm, store_where, key, class_val, **options):
        init = class_val(gm, **options)
        d={key: init}
        {'Agents': gm.Agents, 'Effects':gm.Effects}[store_where].update(d)
        if store_where=='Agents': init._belt.setup_belt(class_val, **options)


    def active_entities(gm): return gm.Agents.values() + gm.Effects.values()
    def primary_entities(gm): return [x for x in gm.active_entities() if x.master==True]
# def secondary_entities(gm): return [x for x in gm.active_entities() if x.master==False]
    def BroadcastAll(gm, fn_name): 
        return map(operator.methodcaller(fn_name), gm.primary_entities())

    def _run_frame(gm):
#        print 'current agent_status db:', [x for x in gm.db.execute('SELECT * FROM agent_status').fetchall() if not x[-1]==u'--targets--']
        gm.frame_iter += 1
        gm._prepare_new_frame()
        gm._punch_clock()
        gm._get_events()
        gm.BroadcastAll('Reset')
        gm.BroadcastAll('PrepareAction')
        gm.BroadcastAll('DoAction')
        gm.process_update_queue()
        gm.display.std_render()

    def _prepare_new_frame(gm):
        gm.reserved_tiles = {} # bidirectional map
        for tx,ty,_,aid in gm.db.execute(sql_tile_locs):
            if gm.entities[aid].species in BLOCKING_SPECIES:
                gm.reserved_tiles.update({aid:(tx,ty), (tx,ty):aid})
        sql_get_tocc = 'SELECT tx,ty,agent_type FROM agent_status;'
        gm.prev_agent_information = gm.db.execute(sql_get_tocc).fetchall()

    ''' Using the clock, determine the time that passed since last frame
        and calculate a multiplicative factor to smooth animation. '''
    def _punch_clock(gm):
#        print '$$$$ PUNCH CLOCK'
        gm.clock.tick(gm.fps)
        this_tick = pygame.time.get_ticks()
        dt = (this_tick - gm.last_tick)
        gm.dt = dt
        cur_true_fps = gm.clock.get_fps()
        if cur_true_fps<gm.fps-1 and gm.fps_itr==0:
            print 'fps:', cur_true_fps
        gm._smoothing = {True:dt * cur_true_fps / 1000.0, False:1}[gm.last_tick>0 and cur_true_fps>0]
#        print dt, gm.fpms, cur_true_fps, cur_true_fps*dt
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
        if down[pygame.K_p]:     raw_input()
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

    def process_update_queue(gm):
        #print 'gm.process_update_queue: print whole db.', gm.db.execute('SELECT img_str,tx,ty FROM agent_status;').fetchall()
#        print gm.prev_agent_information
        old_tposes = set(gm.prev_agent_information)
        while(len(gm.update_queue)>0):
#            for x in gm.update_queue[0]:
#                print '----',x
            cmd, values, what_kind = gm.update_queue.pop(0)
#            print '\texecuting command:',cmd,values
            gm.db.execute(cmd, values)
        new_tposes = set(gm.db.execute(sql_get_tocc).fetchall());
#        if gm.frame_iter<=1: 
#            for x in range(gm.num_x_tiles):
#                for y in range(gm.num_y_tiles):
#                    gm.display.queue_reset_tile((x,y), 'tpos') # hack
#        gm.display.queue_reset_tile((0,0), 'tpos') # hack
        for tx,ty,ent_type in old_tposes.union(new_tposes):
            gm.display.queue_reset_tile((tx,ty), 'tpos')
        img_pposes = set(gm.db.execute(sql_get_pposes).fetchall());
        for tx,ty,px,py,ent_type,img_str,uniq_id in img_pposes:
            if not ent_type in BLOCKING_SPECIES: #[u'target',u'bar']:
                gm.display.queue_E_img(img_str, (px,py))
            elif ent_type in BLOCKING_SPECIES:
                offset = gm.entities[uniq_id].image_offset
                gm.display.queue_A_img(img_str, sub_aFb(offset, (px,py)))
            else: raise Exception()

            if ent_type ==u'plyr':
                for i in [-1,0,1]: 
                    for j in [-2,-1,0,1]: 
                        gm.display.queue_reset_tile((tx+i,ty+j), 'tpos')

    def notify_image_update(gm, agent_ref, img_str, new_image=None):
        if not new_image==None: gm.display.imgs[img_str]=new_image
        upd = 'UPDATE OR FAIL agent_status SET img_str=? WHERE uniq_id=?;'
        gm.update_queue.append([upd, (img_str,agent_ref.uniq_id), 'img update'])
    
    def notify_update_agent(gm, agent_ref, **args):
        sql_upd = 'UPDATE agent_status SET '
        Vals = []
        for ak,av in args.items():
            Vals.append( av )
            sql_upd += ak+'=?,'
        if 'tx' in args.keys() and not 'px' in args.keys():
            Vals.append( args['tx']*gm.tile_x_size ); sql_upd += 'px=?,'
        if 'ty' in args.keys() and not 'py' in args.keys():
            Vals.append( args['ty']*gm.tile_y_size ); sql_upd += 'py=?,'
        if 'px' in args.keys() and not 'tx' in args.keys():
            Vals.append( args['px']//gm.tile_x_size ); sql_upd += 'tx=?,'
        if 'py' in args.keys() and not 'ty' in args.keys():
            Vals.append( args['py']//gm.tile_y_size ); sql_upd += 'ty=?,'
        sql_upd = sql_upd[:-1]+' '
        Vals.append(agent_ref.uniq_id)
        sql_upd += 'WHERE uniq_id=?;'
        gm.update_queue.append( [sql_upd, tuple(Vals), 'agent status update'] )
        
    def notify_new_agent(gm, agent_ref, **args):
        init_tpos = args['tpos']
        init_ppos = multvec(args['tpos'], gm.tile_size)
        if not divvec(init_ppos, gm.tile_size)==init_tpos: \
                raise Exception(divvec(init_ppos, gm.tile_size),init_tpos)
        sql_ins = 'INSERT INTO agent_status VALUES (?,?,?,?,?,?,?,?);'
        Vals = [agent_ref.uniq_id, args.get('img', '--no-img--'), \
                init_tpos[X], init_tpos[Y], init_ppos[X], init_ppos[Y],\
                args.get('agent_type', agent_ref.species), \
                args.get('team','--no-team--') ]
        gm.update_queue.append( [sql_ins, Vals, 'new agent'] ) 

    def notify_tmove(gm, a_id, tloc): gm.notify_pmove(a_id, gm._t_to_p(tloc))
    # Notify pmove: returns whether the move was successful @ making reservation:
    def notify_pmove(gm, agent_id, ploc):
        if not type(agent_id)==int: agent_id = agent_id.uniq_id
        tx, ty = tpos = divvec(ploc, gm.ts())
        if (gm.entities[agent_id].species in RESERVABLE_SPECIES)        \
                and (tpos in gm.reserved_tiles.keys())                  \
                and (not tpos in [(0,0),(-1,-1)])                       \
                and (not gm.reserved_tiles[tpos]==agent_id)             \
                and (not gm.reserved_tiles[tpos]==NULL_RESERVATION):
            X1,X2 = gm.entities[gm.reserved_tiles[tpos]], gm.entities[agent_id]
#            print "---------notify_pmove: tpos already reserved:",tpos, (tx,ty), \
#                    X1,X1.uniq_id,gm.reserved_tiles[X1.uniq_id],X1.view_field('tpos'),\
#                    X2,X2.uniq_id,gm.reserved_tiles[X2.uniq_id],X2.view_field('tpos')
#                    , gm.reserved_tiles, gm.revreserved_tiles
#            ag = gm.entities[agent_id]
#            old_tx,old_ty = ag.view_field('tpos')
#            old_px,old_py = ag.view_field('ppos')
#            gm.db.execute(sql_update_pos, (old_tx, old_ty, old_px, old_py, agent_id))
            return False
#        elif not (gm.entities[agent_id].species in RESERVABLE_SPECIES):
#        print '- pmove notify: by',agent_id,'frame',gm.frame_iter, gm.reserved_tiles, gm.revreserved_tiles,tx,ty
#        gm.db.execute(sql_update_pos, (tx, ty, ploc[X], ploc[Y], agent_id))
        if gm.entities[agent_id].species in BLOCKING_SPECIES:
            gm.reserved_tiles[tpos] = agent_id
            gm.reserved_tiles[agent_id] = tpos
        gm.update_queue.append([sql_update_pos, (tx, ty, ploc[X], ploc[Y], agent_id), 'new pos'])
        return True

#    def notify_imgChange(gm, ref_who, img_name, where='not provided', prior=None):
#        if where=='not provided':
#            where = gm.request_ppos(ref_who.uniq_id)
#        if not prior==None:
#            prev_where = {'ppos':prior[0], 'tpos':multvec(prior[0],gm.ts())}[prior[1]]
#            if where==prev_where:
#                pass
#
#
#        { True: gm.display.queue_A_img, False: gm.display.queue_E_img}[\
#                isinstance(ref_who, VisualStepAgent)](ref_who.uniq_id, img_name, where)
#        if prior: gm.display.queue_reset_tile(prior[0], prior[1])

    def request_tpos(gm, agent_id):
        if not type(agent_id)==int:
            agent_id = gm.Agents[agent_id].uniq_id
        q = 'SELECT tx,ty FROM agent_status WHERE uniq_id=?;'
        return gm.db.execute(q, (agent_id,)).fetchall()[0]

    def request_ppos(gm, agent_id): # return if possible, else NULL_POSITION.
        q = 'SELECT px,py FROM agent_status WHERE uniq_id=?;'
        return gm.db.execute(q, (agent_id,)).fetchall()[0]

    def request_mousepos(gm, mode):
        if mode=='tpos': return divvec(pygame.mouse.get_pos(), gm.ts())
        if mode=='ppos': return pygame.mouse.get_pos()
    def request_what_at(gm, what, tpos): pass  # perhaps break this up....

    def send_message(gm, **arglist):
        return
    '''
        print "message to be routed:", arglist,
        if arglist['message']=='redraw':
            tid = arglist['tpos']

            gm.db.execute("SELECT uniq_id FROM agent_status;").fetchall()
            for _,ent_id,__ in gm.get_tile_occupants(tid):
                ent = gm.entities[ent_id]
                print '(sent to',ent.species,')',
                if ent.has_logic:
                    ent.logic.notify('redraw', tid)
        print ''
        '''

            
#    def _make_db_consistent_ppos_tpos(gm, cmd, values, what_kind):
#        def _substrs_in_str(X): return all(map(lambda x: x in cmd, X))
#        if what_kind=='img update': # situation: no update needed.
#            return
#        elif what_kind=='agent status update':
#        try:
#            set_what = cmd[cmd.index('SET')+4 : cmd.index('WHERE')]
#            if not 'tx' in set_what: return
##            print cmd, values, '>>',set_what
#        except:
#            pass#print cmd,'!!!!!!!!!!!!!!'
#        gm._make_db_consistent(aus='ppos',at='tpos',where=None)
#    def _make_db_consistent(gm, aus='ppos',at='tpos',where=None): pass

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
#    def notify move(gm, agent, ppos):
#        if not next_tid: next_tid = agent.get_tpos();
#        tx,ty = divvec(ppos, gm.tile_size)
#        gm.db.execute('''UPDATE OR FAIL tile_occupants SET tx=?, ty=? \
#                WHERE uniq_id=?''', (tx, ty, agent.uniq_id))
#        gm.db.execute('''UPDATE OR FAIL agent_locations SET tx=?, ty=? \
#                WHERE uniq_id=?''', (next_tid[X], next_tid[Y], agent.uniq_id))
#        
#    def notify_kill(gm, agent):
#        gm.db.execute('DELETE FROM tile_occupants WHERE uniq_id=?;', \
#                (agent.uniq_id, ))
#
#    def foo(gm):
#        if not next_tid==NULL_POSITION:
#            gm.db.execute('INSERT INTO tile_occupants VALUES (?,?,?,?,?);',
#                    (uniq_id, next_tid[X], next_tid[Y], atype, team));
#        if not prev_tid==NULL_POSITION:
#            gm.db.execute('''DELETE FROM tile_occupants WHERE uniq_id=?
#                    AND tx=? AND ty=?;''', (uniq_id, prev_tid[X], prev_tid[Y]))
#
    ''' Query a specific tile for occupants and tile info. Supply WHAT columns.'''
    def query_tile(gm, tid, what='*'): 
        if type(what)==list: what = ','.join(what)
        ret = gm.db.execute( "SELECT "+what+\
                " FROM tilemap WHERE tx=? AND ty=?;", tid).fetchall()
        return gm.get_tile_occupants(tid), ret

    # returns BLOCK=T, FREE=F
    def query_tile_for_blck(gm, tid, what='*'): 
        if type(what)==list: what = ','.join(what)
#        print '---------',gm.db.execute( "SELECT "+what+" FROM tilemap WHERE tx=? AND ty=?;",tid).fetchall()
        if gm.db.execute( "SELECT "+what+" FROM tilemap WHERE tx=? AND ty=?;", \
                tid).fetchone() == (u'true',):
            return True
        n_agents = gm.db.execute("""SELECT count(*) FROM agent_status 
            WHERE tx=? AND ty=? AND NOT agent_type=?;""",\
                    (tid[X],tid[Y], u'target') ).fetchone()[0]
        if n_agents==0: return False


    # Returns: select or full list of tuples [agent_type, uniq_id, team].
    def get_tile_occupants(gm, tid=None):
        if tid==None:
            return gm.db.execute(\
                    """SELECT tx,ty,agent_type FROM agent_status;""")\
                    .fetchall()
        return gm.db.execute(\
                """SELECT agent_type,uniq_id,team FROM agent_status 
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
