import  sys
import  numpy as np
from abstractEntities import Entity
from motionActions import *
from attackActions import *

'''             State               '''

''' State: Always associated with a Logic and required by any Actions
that are ActionPicker, the State maintains various information fields.'''



#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------


class State(Entity): # i do not write, so no need to have logic
    def __init__(st, gm, belt=None, options=None):
        Entity.__init__(st, gm)
        st.init_options=options
        st.gm = gm
        st.s_env = {} # environment info and holistic internal state
        st.s_ap = {} # space reserved for ActionPickers to store exec data
#        st.running = {} # a log of fields specifically indicating Running actions.
        st.s_ssr = {} # space reserved for sensors to hold intermediate values
        st.belt = (belt if belt else None)

    def update_ap(st, key, val, who):
        if not st.gm.entities[who].write_state_access==True: 
            raise Exception('State writing access not permitted.')
        if not st.s_ap.has_key(who):
            st.s_ap[who] = {}
        st.s_ap[who][key] = val
    def view_ap(st, what, who):     return st.s_ap[who][what]
    def update_env(st, key, val):   st.s_env[key] = val
    def view_env(st, what):         return st.s_env[what]

    # Initialize and define global fields. All globals must start here.
    def setup_fields(st, genus, parent_logic, ppos=None, tpos=None):
        st._init_sensors(parent_logic)
        st._init_actions(parent_logic, genus)

        st.s_env['tilesize'] = st.gm.tile_size
        st.s_env['redraw'] = EVAL_F
        if genus=='plyr':   st.setup_plyr_fields(parent_logic)
        if genus=='pkmn':   st.setup_basic_pkmn_fields(parent_logic)
        if genus=='target': st.setup_target(parent_logic) 
        if ppos:
            st.s_env['tpos'] = divvec(ppos, st.gm.ts())
            st.s_env['ppos'] = ppos
        elif tpos:
            st.s_env['tpos'] = multvec(tpos, st.gm.ts())
            st.s_env['ppos'] = tpos


    def _init_sensors(st, parent_logic):
        st.belt.Sensors = {k:v(st.gm) for k,v in st.belt.Sensors.items()}
        for sensor in st.belt.Sensors.values():
            sensor.set_state(st)

    def _init_actions(st, parent_logic, genus):
#        if genus=='pkmn': return
#            print '\t',st.belt.Actions, parent_logic
#            for k in ['l','r','u','d','-']:
#                print '--',k
#                st.belt.Actions[k]=st.belt.Actions[k]( parent_logic)
#            for k in ['l','r','u','d','-']:
#                print '--',k
#                st.belt.Actions[k]=st.belt.Actions[k](parent_logic)
#            sys.exit()
#        print ''
#        if not genus=='pkmn':
#            tmp = {k:v(parent_logic) for k,v in st.belt.Actions.items()}
        st.belt.Actions = {k:v(parent_logic) for k,v in st.belt.Actions.items()}

    def setup_plyr_fields(st, parent_logic):
        # Simple status fields, eg primitives or fixed-structure collections:
        st.s_env['available']       = True
        st.s_env['unit step']       = parent_logic.plyr_steps((1,1))
#        st.s_env['prev move vec']   = [0,0,0,0]
        st.s_env['curr move vec']   = [0,0,0,0]
        st.s_env['num moves']       = 4
        st.s_env['Image']           = 'player sprite 7' # down
        st.s_env['motion ap key'] = None 
        st.s_env['isPlayerActionable'] = True
        if not st.belt: raise Exception('Need at least an empty belt.')

        st.s_env['available motions'] = st.belt.Actions # todo! For now.
        st.s_env['PDA']             = [st.belt.Actions['d']]
        # Dynamic fields:
        st.s_env['player motion rand pda'] = [st.s_env['available motions']['-']]
        st.s_env['player motion newest pda']=[st.s_env['available motions']['-']]
        st.s_env['global movedir choice'] = 2 # down
  


    def setup_target(st, logic): pass

    def setup_basic_pkmn_fields(st, logic):
        st.s_env['unit step'] = logic.gm.ts()
        st.s_env['root delay'] = logic.agent.primary_delay
        st.s_env['delay'] = np.random.uniform(0.0, st.s_env['root delay'])
        st.s_env['is being caught'] = False
        st.s_env['motions'] = {k:v for k,v in st.belt.Actions.items()\
                if k in ['r','l','u','d','-']}
        st.s_env['attacks'] = {k:v for k,v in st.belt.Actions.items()\
                if k in ['A']}

#        st.s_env['attacks'] = {'tackle':Tackle(logic)}
#        st.s_env['motions']=[]
#        for m in [MotionUp, MotionRight, MotionDown, MotionLeft, MotionStatic]:
#            st.s_env['motions'].append(m)
#            if isinstance(v, MotionAction): st.s_env['motions'].append(v)
#            if k=='tackle': st.s_env['attacks'].append(v)
