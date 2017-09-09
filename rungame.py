''' Game Options '''
DEFAULT_FPS = 10 # should be a cap: lower than expected max FPS
MAP_LEVEL_CONFIG = './config_collision.ini'
MAP_LEVEL_CONFIG = './config7.ini'
TILE_SIZE = (40,36);

''' ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
'''#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
''' ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
'''#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
''' ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'''

import sys
sys.path.append(\
        '/Users/morganbryant/Desktop/Codes/miniconda2/lib/python2.7/site-packages')
import pygame, operator
import sqlite3 as sql
import ConfigParser
import numpy as np
from PIL import Image, ImageOps

from config_py1 import *
from utilities import *
import leaves as leaves_module
import agents as agents_module
import belt as belt_module
from display import Display
                    
HUD_SIZE = TILE_SIZE[Y] # one tile
X = 0;  Y = 1



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

    """ ---------------------------------------------------------------------- """
    """    Initialization Procedures, called once prior to a new game level.   """
    """ ---------------------------------------------------------------------- """

    ''' Create databases '''
    def _init_database(gm): # *
        gm.tile_size = (gm.tile_x_size, gm.tile_y_size) = TILE_SIZE
        # Initialize databases
        _db = sql.connect(':memory:').cursor() # formerly broken up with cxn
        """
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

        _db.execute(''' CREATE TABLE agent_status (
                        uniq_id INT NOT NULL,   img_str TEXT,
                        tx INT NOT NULL,        ty INT NOT NULL,
                        px INT NOT NULL,        py INT NOT NULL,
                        species TEXT,        team TEXT           ); ''') 
        """














        '''     Database guide      '''
#        entities: houses dynamic information and properties about an entity.
#        map_info: stores static, RO info about the tile-map.
#        map_occs: aggregates knowledge of who is where and who reserves what.
        
        _db.execute(''' CREATE TABLE entities (
                        uniq_id INT NOT NULL, 
                        img_str TEXT, 
                        px INT,               
                        py INT,
                        species TEXT,         
                        team TEXT,
                        tile_occupying INT ); ''' )
        
        _db.execute(''' CREATE TABLE map_info (
                        tx INT, ty INT, 
                        tile_key TEXT, 
                    base_tile_img TEXT NOT NULL,
                        obst_tile_img TEXT,   
                        blocks_walking INT,
                        lane_path INT ); ''' )

        _db.execute(''' CREATE TABLE map_occs (
                        tx INT, ty INT, 
                        standing_occupant INT,
                        movingfrom_occupant INT,
                        movingto_occupant INT);''')




















        for y in range(len(LEVEL_MAP[0])):
            for x in range(len(LEVEL_MAP)):
                t_key = LEVEL_MAP[x][y]
                _db.execute(''' INSERT INTO map_info (tx,ty, tile_key, \
                        base_tile_img, obst_tile_img, blocks_walking) \
                        VALUES (?,?,?,?,?,?);''', \
                        (x, y, t_key, \
                        TILE_INFO[t_key]['base_image'], \
                        TILE_INFO[t_key].get('obst_image', '-'),\
                        int(TILE_INFO[t_key]['blocks_walking'])))
        gm.map_num_tiles = (len(LEVEL_MAP[0]), len(LEVEL_MAP))
        gm.db=_db

        
        """
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
#        gm.db = _db
#        gm.map_num_tiles = (curR, curC+1)
        gm.cp = cp
"""


    ''' Important global fields '''
    def _init_global_fields(gm): # *
        gm.uniq_id_counter = 100
        gm.entities = {}
        gm.new_spawns_queue=[]
        gm.reserved_tiles = {}
        gm.frame_iter = 0
        gm._smoothing = 1.0      # animation smoothing factor
        (gm.num_x_tiles, gm.num_y_tiles) = gm.map_num_tiles
        gm.map_pix_size = (gm.map_x, gm.map_y) = \
                            multpos(gm.map_num_tiles, gm.tile_size)
        _for_reference=''' gm.tile_size = (gm.tile_x_size, gm.tile_y_size) '''

    def ts(gm): return gm.tile_size 
    def smoothing(gm): return gm._smoothing

    ''' _init_display:  set up the Display.'''
    def _init_display(gm): 
        gm.hud_size = (gm.map_x, HUD_SIZE)
        gm.screen_size = (gm.map_x, gm.map_y+HUD_SIZE)
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
            #print '\n\nFRAME_COUNTER', FRAME_COUNTER; 
            FRAME_COUNTER+=1
            gm._run_frame()

    def _pretty_print_sql(gm, sql_str):
        print '**************************'
        res = gm.db.execute(sql_str).fetchall()
        if len(res)==0: print '\t[None]'; return
        if not '*' in sql_str:
            res.insert(0,sql_str.split(','))
        l = [max([len(str(v[i])) for v in res]) for i in range(len(res[0]))]
        for item in res:
            print '\t',
            for vi,v in enumerate(item): 
                try: 
                    s='  {:'+str(l[vi])+'}'
                    print s.format(v),
                except: pass
            print '\n',
        print ''

    def _init_game(gm, fps=DEFAULT_FPS):
        gm.fps = float(fps)     # frames per second
        gm.fpms = fps/1000.0    # frames per millisecond
        gm.fps_itr = 0
        gm.clock = pygame.time.Clock()  # clock object for frame smoothness
        gm.last_tick = 0            # clock counter field
        gm.update_queue = []
        gm.pkmn_damage_teams = []
        gm.prev_agent_information = []

        gm.Agents, gm.Effects, gm.AfterEffects = {},{},{}

#       Stub code:  <stub>



        gm.addNew('Agents', 'Player', agents_module.Player, team='plyr' )
        locs = list(set([(np.random.choice(range(gm.tile_x_size)), np.random.choice(\
                range(gm.tile_y_size))) for _ in range(20) ]))
        locs= [(1,1),(1,3),(3,1),(3,3),(5,3),(5,1)]
        locs = []
        for x in [1,3,5,7]:
            for y in [1,3,5,7]:
                locs.append((x,y))
        locs=[]
        for x in [1,3]:
            for y in [3]:
                locs.append((x,y))

        for l in locs:
            s=str(l[0])+','+str(l[1])
            if np.random.rand()<0.5:
                gm.addNew('Agents', 'PkmnWild'+s, agents_module.AIAgent, \
                init_tloc=l, hbcolor='r', team='wild', vizscale=1, \
                pokedex=1, health=np.random.choice(range(40,50)))
            else:
                gm.addNew('Agents', 'PkmnPlyr'+s, agents_module.AIAgent, \
                init_tloc=l, hbcolor='b', team='plyr', vizscale=1, \
                health=np.random.choice(range(40,50)), pokedex=1)
        '''
        for (i,j) in [(1,1),(1,2),(2,1),(2,2),(3,2),(3,3)]:
            s=str(i)+','+str(j)
            if np.random.rand()<0.5:
                gm.addNew('Agents', 'PkmnPlyr'+s, agents_module.AIAgent, \
                        init_tloc=(i,j), uniq_name='PkmnPlyr'+s, \
                        hbcolor='b', team='plyr', \
                        pokedex=1, health=20, \
                        orientation='vertic')
                gm.TEMPORARY_VARIABLE_DEBUG=False
            else:
                gm.addNew('Agents', 'PkmnWild'+s, agents_module.AIAgent, \
                        init_tloc=(i,j), uniq_name= 'PkmnWild'+s, \
                        hbcolor='r', team='wild', \
                        pokedex=1, health=12+2*i+4*j)
#       </stub>'''
        gm.addNew('AfterEffects', 'mouse highlighter', leaves_module.MouseTarget,\
                    pkmn_damaging_team=False  )

        gm.process_update_queue() # after entities have been initialized...
        gm._reset_events()
        gm.prev_e = gm.events[:]
        gm.buttonUp = { SP_ACTION: True }
        gm.display.std_render()

    def addNew(gm, store_where, key, class_val, **options):
        options['uniq_name'] = key
        init = class_val(gm, **options)
        d={key: init}
        {'Agents': gm.Agents, 'Effects':gm.Effects, 'AfterEffects':\
                    gm.AfterEffects}[store_where].update(d)
        if options.get('pkmn_damaging_team',True):
            _team = '--'+options['team']+'--'
            tmp = set(gm.pkmn_damage_teams)
            tmp |= { _team }
            gm.pkmn_damage_teams = list(tmp)

        return init

    def active_entities(gm): return gm.Agents.values() + gm.Effects.values() \
                + gm.AfterEffects.values()

    def BroadcastAll(gm, fn_name): 
#        print 3*fn_name+' ', gm.Agents.keys() + gm.Effects.keys() \
#                + gm.AfterEffects.keys()
        map(operator.methodcaller(fn_name), gm.active_entities())

    def _run_frame(gm):
#        print 'Active Entities:', gm.active_entities()
        gm.frame_iter += 1
        print 'DATABASES at frame ', gm.frame_iter,':\n\t',\
                gm.db.execute('SELECT * FROM map_occs').fetchall(), '\n'
#                gm.db.execute('SELECT * FROM entities').fetchall(), '\n\t',\
#                gm.db.execute('SELECT * FROM map_info').fetchall(), '\n\t',\
        gm._prepare_new_frame()
        gm._punch_clock()
        gm._get_events()
        gm.BroadcastAll('Reset')
        gm.BroadcastAll('PrepareAction')
        gm.BroadcastAll('DoAction')
        gm.process_update_queue()
        gm.display.std_render()

    def _prepare_new_frame(gm):
        while len(gm.new_spawns_queue)>0:
            tmp = gm.new_spawns_queue.pop(0)
            gm.addNew(tmp[0], tmp[1], tmp[2], **tmp[3])
#            print 'Success! added a new'

#        gm.reserved_tiles = {} # bidirectional map
#        for tx,ty,_,aid in gm.db.execute(sql_tile_locs):
##            print tx,ty,aid,'\t\t9999'
#            if gm.entities[aid].species in BLOCKING_SPECIES:
#                gm.reserved_tiles.update({aid:(tx,ty), (tx,ty):aid})
        gm.prev_agent_information=gm.db.execute(SQL_get_all_occs).fetchall()

    ''' Using the clock, determine the time that passed since last frame
        and calculate a multiplicative factor to smooth animation. '''
    def _punch_clock(gm):
        gm.clock.tick(gm.fps)
        this_tick = pygame.time.get_ticks()
        dt = (this_tick - gm.last_tick)
        gm.dt = dt
        cur_true_fps = gm.clock.get_fps()
        if cur_true_fps<gm.fps-1 and gm.fps_itr==0:
            print 'fps:', cur_true_fps
        gm._smoothing = {True:dt * cur_true_fps / 1000.0, False:1}\
                [gm.last_tick>0 and cur_true_fps>0]
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
        if down[pygame.K_q]:     
#            print 'player belt pkmn:',gm.Agents['Player']._logic.belt.Pkmn
            
#            for a in sorted(gm.entities.keys()):
#                print a,'\t',gm.entities[a]
            print 'Exiting.'
            sys.exit()
        if down[pygame.K_p]:     raw_input()
        if (not gm.buttonUp[SP_ACTION]) and (not down[pygame.K_SPACE]):
            gm.buttonUp[SP_ACTION] = True 
        pygame.event.clear()
    
    def input_actions_map(gm):  # actions, specifically
        return { gi:gm.events[gi] for gi in range(4,len(gm.events)) }

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
        old_tposes = set(gm.prev_agent_information)
        _debug_store = gm.update_queue[:]
        while(len(gm.update_queue)>0):
            cmd, values, what_kind = gm.update_queue.pop(0)
#            print '----processing update:<',cmd, '>,\n\t\t', values, ',\n\t\t', what_kind
                    
            #print '\n',cmd,values,what_kind; 
            #print '\n',cmd,values,what_kind; import sys; sys.exit()
            if len(values)>0:
                gm.db.execute(cmd, values)
            else:
                gm.db.execute(cmd)
        new_tposes = set(gm.db.execute(SQL_get_all_occs).fetchall());
        for tx,ty in old_tposes.union(new_tposes):
            gm.display.queue_reset_tile((tx,ty), 'tpos')
        img_pposes = set(gm.db.execute(SQL_get_pposes).fetchall());
        for px,py,ent_type,img_str,uniq_id in img_pposes:
            if ent_type in AFTEREFFECT_SPECIES:
                gm.display.queue_AE_img(img_str, (px,py))
            elif ent_type in BLOCKING_SPECIES:
                offset = gm.entities[uniq_id].image_offset
                gm.display.queue_A_img(img_str, sub_aFb(offset, (px,py)))
            elif ent_type in EFFECT_SPECIES:
                gm.display.queue_E_img(img_str, (px,py))
            else: raise Exception(ent_type, AFTEREFFECT_SPECIES, BLOCKING_SPECIES,\
                    EFFECT_SPECIES, uniq_id, gm.entities[uniq_id], _debug_store)

            # Todo: has this incidentally become redundant?
            tx,ty = divvec( (px,py), gm.ts() )
            if ent_type ==u'plyr':
                for i in [-1,0,1]: 
                    for j in [-2,-1,0,1]: 
                        gm.display.queue_reset_tile((tx+i,ty+j), 'tpos')

    def notify_image_update(gm, agent_ref, img_str, new_image=None):
        # TAG CHECKED FOR DATABASE UPDATE
        if not new_image==None: gm.display.imgs[img_str]=new_image
#        gm.update_queue.append(\
#                [sql_img_update, (img_str,agent_ref.uniq_id), 'img update'])
        gm.update_queue.append(\
                [SQL_img_update, (img_str,agent_ref.uniq_id), 'img update'])

    def notify_new_spawn(gm, a,b,c,**o):
        gm.new_spawns_queue.append( (a,b,c, o.copy()) )
    
#    def notify_update_agent(gm, agent_ref, **args):
#        sql_upd = 'UPDATE agent_status SET '
#        Vals = []
#        for ak,av in args.items():
#            Vals.append( av )
#            sql_upd += ak+'=?,'
#        if 'tx' in args.keys() and not 'px' in args.keys():
#            Vals.append( args['tx']*gm.tile_x_size ); sql_upd += 'px=?,'
#        if 'ty' in args.keys() and not 'py' in args.keys():
#            Vals.append( args['ty']*gm.tile_y_size ); sql_upd += 'py=?,'
#        if 'px' in args.keys() and not 'tx' in args.keys():
#            Vals.append( args['px']//gm.tile_x_size ); sql_upd += 'tx=?,'
#        if 'py' in args.keys() and not 'ty' in args.keys():
#            Vals.append( args['py']//gm.tile_y_size ); sql_upd += 'ty=?,'
#        sql_upd = sql_upd[:-1]+' '
#        Vals.append(agent_ref.uniq_id)
#        sql_upd += 'WHERE uniq_id=?;'

#%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*%--*
    def notify_update_ent(gm, entity_ref, **args): 
        gm.notify_update(entity_ref, 'entities', **args)
    def notify_update(gm, entity_ref, database_vers, **args):
        # TAG CHECKED FOR DATABASE UPDATE
        if database_vers in ['entities', 'map_occs']:
            _sql_upd = 'UPDATE '+database_vers+' SET '
        elif database_vers=='map_info':
            raise Exception("Map_info database is currently Read-only.")
        else: raise Exception('notify update failed:database_vers:',\
                                database_vers, entity_ref, args)
        Vals = []
        for ak,av in args.items():
#            if ak=='tx' and database_vers=='entities':
#                Vals.append( av*gm.ts()[X] )
#                _sql_upd += 'px=?,'
#            elif ak=='ty' and database_vers=='entities':
#                Vals.append( av*gm.ts()[Y] )
#                _sql_upd += 'py=?,'
            if ak in ['tx','ty'] and database_vers=='entities':
                Vals.append( av*gm.ts()[{'tx':X, 'ty':Y}[ak]] )
                _sql_upd += 'p'+ak[1]+'=?,'
            else:
                Vals.append( av )
                _sql_upd += ak+'=?,'

        _sql_upd = _sql_upd[:-1]+' WHERE uniq_id=?;'
        Vals.append(entity_ref.uniq_id)
        gm.update_queue.append( [_sql_upd, tuple(Vals), 'update: '+database_vers] )
        
#    def notify_new_agent(gm, agent_ref, **args):
#        init_tpos = args['tpos']
#        init_ppos = multvec(args['tpos'], gm.tile_size)
#        if not divvec(init_ppos, gm.tile_size)==init_tpos: \
#                raise Exception(divvec(init_ppos, gm.tile_size),init_tpos)
#        Vals = [agent_ref.uniq_id, args.get('img', '--no-img--'), \
#                init_tpos[X], init_tpos[Y], init_ppos[X], init_ppos[Y],\
#                args.get('species', agent_ref.species), \
#                args.get('team','--no-team--') ]
#        gm.update_queue.append( [sql_ins, Vals, 'new agent'] ) 

    def notify_new_entity(gm, ent_ref):
        # TAG CHECKED FOR DATABASE UPDATE
        gm.update_queue.append([ 'INSERT INTO entities (uniq_id) VALUES ('+\
                str(ent_ref.uniq_id)+');', [], 'new agent entities'])

#    def notify_new_effect(gm, effect_ref, **args):
#        if 'tpos' in args.keys(): init_tpos = args['tpos']
#        else: init_tpos = divvec(args['ppos'], gm.tile_size, '//')
#        if 'ppos' in args.keys(): init_ppos = args['ppos']
#        else: init_ppos = multvec(args['tpos'], gm.tile_size)
#
##        init_tpos = args.get('tpos',  divvec(args['ppos'], gm.tile_size, '//'))
##        init_ppos = args.get('ppos', multvec(args['tpos'], gm.tile_size))
#        Vals = [effect_ref.uniq_id, args.get('img', '--no-img--'), \
#                init_tpos[X], init_tpos[Y], init_ppos[X], init_ppos[Y],\
#                args.get('species', effect_ref.species), \
#                args.get('team','--no-team--') ]
#        gm.update_queue.append( [sql_ins, Vals, 'new effect'] ) 

    
    def notify_tmove(gm, a_id, tloc): 
#        print gm.entities[a_id], tloc
        gm.notify_pmove(a_id, multvec(gm.ts(), tloc))
    # Notify pmove: returns whether the move was successful @ making reservation:


    # Note: new function does not handle *releasing* previous tiles 
    # or tile motions: this works by changing TX and TY given an ID
    def _notify_change_ppos(gm, u_id, ppos, put_or_drop='put', mode='stand'):
        # internal method for changing the map occupancy & entity tiletag
        if not type(u_id)==int: u_id = u_id.uniq_id
        if ppos==NULL_POSITION: return
        blocking_flag = gm.db.execute(SQL_is_blocking,(u_id,)).fetchone()
        gm.update_queue.append([SQL_set_ent_ppos, \
                    [ppos[X],ppos[Y],u_id], 'set ent ppos'])
        if blocking_flag:
            tx, ty = tpos = divvec(ppos, gm.ts())
            if put_or_drop=='put':
                gm.update_queue.append([ \
                       {'stand':SQL_map_set_occ_standing_loc,\
                        'moveto':SQL_map_set_occ_moveto_loc,\
                        'movefrom':SQL_map_set_occ_movefrom_loc}[mode], \
                        [u_id, tx, ty], 'put map occ' ])
            elif put_or_drop=='drop':
                gm.update_queue.append([ \
                       {'stand':SQL_map_set_occ_standing_loc,\
                        'moveto':SQL_map_set_occ_moveto_loc,\
                        'movefrom':SQL_map_set_occ_movefrom_loc}[mode], \
                        [u_id, tx, ty], 'drop map occ' ])
            else: raise Exception('!')

    # Helpers for setting and releasing tiles
    def notify_put_ppos(gm, u_id, ppos, mode='stand'): 
        gm._notify_change_ppos(u_id, ppos, 'put', mode)
    def notify_drop_ppos(gm, u_id, ppos, mode='stand'): 
        if ppos==NULL_POSITION: return
        gm._notify_change_ppos(u_id, ppos, 'drop', mode)
    def notify_put_tpos(gm, u_id, tpos, mode='stand'): 
        gm._notify_change_ppos(u_id, multvec(tpos, gm.ts()), 'put', mode)
    def notify_drop_tpos(gm, u_id, tpos, mode='stand'): 
        if tpos==NULL_POSITION: return
        gm._notify_change_ppos(u_id, multvec(tpos, gm.ts()), 'drop', mode)


    # Convenience functions
    def notify_ppos(gm, u_id, new, prev, mode='stand'):
        if mode=='stand':
            gm.notify_drop_ppos(u_id, prev, 'stand')
            gm.notify_put_ppos(u_id, new, 'stand')
        else: raise Exception('implemented not yet notify_tpos')
    def notify_tpos(gm, u_id, new, prev, mode='stand'):
        gm.notify_ppos(u_id, multvec(new,gm.ts()), \
                             multvec(prev,gm.ts()), mode)

    # These methods do not error check:
    def notify_new_motion(gm, uid, prev, new):
        gm.notify_drop_tpos(uid, prev, 'stand')
        gm.notify_put_tpos(uid, prev, 'movefrom')
        gm.notify_put_tpos(uid, new, 'moveto')

    def notify_stopping(gm, uid, prev, new):
        gm.notify_drop_tpos(uid, prev, 'movefrom')
        gm.notify_drop_tpos(uid, new, 'moveto')
        gm.notify_put_tpos(uid, new, 'stand')


    def query_ent_ppos(gm, uid):
        return gm.db.execute(SQL_get_ent_ppos,(uid,)).fetchone()
    def query_ent_tpos(gm, uid):
        return divvec(gm.query_ent_ppos(uid), gm.ts())



#    def notify_pmove(gm, agent_id, ploc):
#        if not type(agent_id)==int: agent_id = agent_id.uniq_id
#        tx, ty = tpos = divvec(ploc, gm.ts())
#        if (gm.entities[agent_id].species in RESERVABLE_SPECIES)        \
#                and (tpos in gm.reserved_tiles.keys())                  \
#                and (not tpos in [(0,0),(-1,-1)])                       \
#                and (not gm.reserved_tiles[tpos]==agent_id)             \
#                and (not gm.reserved_tiles[tpos]==NULL_RESERVATION):
#            X1,X2 = gm.entities[gm.reserved_tiles[tpos]], gm.entities[agent_id]
#            return False
#        if gm.entities[agent_id].species in BLOCKING_SPECIES:
#            gm.reserved_tiles[tpos] = agent_id
#            gm.reserved_tiles[agent_id] = tpos
#        gm.update_queue.append([sql_update_pos, (tx, ty, ploc[X], \
#                                ploc[Y], agent_id), 'new pos'])
#        return True

    ''' the following code has not been analysed at all for refactor: '''
#    def notify_reset_previous_image(gm, ppos=None, tpos=None):
#        if tpos: gm.display.queue_reset_tile(tpos, 'tpos')
#        if ppos: gm.display.queue_reset_tile(ppos, 'ppos')
#
#    def request_tpos(gm, agent_id):
#        if not type(agent_id)==int:
#            agent_id = gm.Agents[agent_id].uniq_id
#        return gm.db.execute(sql_get_tpos_of_who, (agent_id,)).fetchone()
#
#    def request_ppos(gm, agent_id): # return if possible, else NULL_POSITION.
#        q = 'SELECT px,py FROM agent_status WHERE uniq_id=?;'
#        return gm.db.execute(q, (agent_id,)).fetchall()[0]
#
    def request_mousepos(gm, mode):
        if mode=='tpos': return divvec(pygame.mouse.get_pos(), gm.ts())
        if mode=='ppos': return pygame.mouse.get_pos()
#    def request_what_at(gm, what, tpos): pass  # perhaps break this up....

    def send_message(gm, **arglist):
#        print "GM delivering message", arglist
#        if 'msg' in arglist.keys(): raise Exception(' <msg> field is reserved '+\
#                'by the gm.send_message function.')
        if arglist.get('msg') in ['catching', 'throwing']:
            if arglist.get('at',False):
                ents = gm.db.execute(sql_query_tile, arglist['at']).fetchall()
                for ent in ents:
                    e_species, e_id, e_team = ent
                    if (not arglist['sender_team']==e_team) and e_species=='pkmn':
                        gm.entities[e_id].deliver_message(**arglist)
        elif arglist.get('msg')=='you caught me':
            gm.entities[arglist['recipient_id']].deliver_message(**arglist)
        else: raise Exception(arglist)

        return


    def query_db(gm, what): # general database query
        return gm.db.execute(what).fetchall()




    def query_tile_for_team(gm, tid, team):
        if not type(team)==str:
            try:        team[0]=='not_my_team'
            except:     raise Exception(tid, team)
            teams = [t for t in gm.pkmn_damage_teams[:] if not t==team[1]]
            ''' ^ Get not-team, restricted to client-side 'Game teams'. '''
            ret = []
            for Team in teams:
                ret += gm.db.execute(sql_query_tile_for_team, \
                        (tid[0], tid[1], Team)).fetchall()
            return ret
        else:
            return gm.db.execute(sql_query_tile_for_team, (tid[0], tid[1], \
                            team)).fetchall()

    ''' Query a specific tile for occupants and tile info. Supply WHAT columns.'''
    def query_tile(gm, tid, what='*'): 
        if type(what)==list: what = ','.join(what)
        ret = gm.db.execute( "SELECT "+what+\
                " FROM tilemap WHERE tx=? AND ty=?;", tid).fetchall()
        return gm.get_tile_occupants(tid), ret


    def query_tile_held_as(gm, tid, what, fetch='fetchall'):
#        if not what in ['standing_occupant', 'movingfrom_occupant', \
#                'movingto_occupant', 'COUNT(*)']:
#            raise Exception("Query not accepted:",tid,what)
        query = 'SELECT '+what+' FROM map_occs WHERE tx=? AND ty=?;'
        if fetch=='fetchall':
            result= gm.db.execute(query, tid).fetchall()
        elif fetch=='fetchone':
            result= gm.db.execute(query, tid).fetchone()
        else: raise Exception(tid,what,fetch)
#        print 'query_tile_held_as result:',result, what, tid
        if len(result)==0: return None
        else: return result

    def query_all_tile_occs(gm, tid):
        return gm.query_tile_held_as(tid, 'standing_occupant, '+\
                    'movingfrom_occupant, movingto_occupant')

    def query_tile_occupied(gm, tid):
        # Facilitates Bug-Type: returns count!
        return gm.query_tile_held_as(tid, 'COUNT(*)', 'fetchone')[0]

    def query_occupancy_status(gm, ent_id):
        tx, ty = divvec(gm.db.execute(SQL_get_ent_ppos, (ent_id,)), gm.ts())
        tmp= gm.query_all_tile_occs( (tx,ty) )
        print 'query_occupancy_status:', tmp
        st, frm, to = tmp
        if ent_id==st and ent_id==frm: raise Exception('consistency')
        if ent_id==to and ent_id==frm: raise Exception('consistency')
        if ent_id==st and ent_id==to: raise Exception('consistency')
        if ent_id==st: return 'static', tx,ty
        if ent_id==frm: return 'movefrom', tx,ty
        if ent_id==to: return 'moveto', tx,ty
        return None, tx, ty


    def query_tpos_for_ent(gm, tpos):
        return 



    def query_tile_for_blck(gm, tid, what='*'): 
        if type(what)==list: what = ','.join(what)
        res = gm.db.execute( "SELECT "+what+" FROM \
                tilemap WHERE tx=? AND ty=?;", tid).fetchone()
        if all(x==u'true' for x in res):
            return True
        elif all(x==u'false' for x in res):
            return False
        else: raise Exception("impl")

        n_agents = sum([gm.db.execute("""SELECT count(*) FROM agent_status 
            WHERE tx=? AND ty=? AND species=?;""",\
                    (tid[X],tid[Y], SPECIES) ).fetchone()[0] \
                    for SPECIES in BLOCKING_SPECIES])
        if n_agents==0: return False


    # Returns: select or full list of tuples [species, uniq_id, team].
    def get_tile_occupants(gm, tid=None):
        if tid==None:
            return gm.db.execute(sql_get_tocc).fetchall()
        return gm.db.execute(sql_query_tile, tid).fetchall()




GM = GameManager()
GM.load() 
GM.run_game()
