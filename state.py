import  sys
import  numpy as np
from abstractEntities import Entity
from motionActions import *
from attackActions import *
import random

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
        st.s_ssr = {} # space reserved for sensors to hold intermediate values
        st.s_dep = {} # space reserved for simple Dependent object entities
        st.belt = (belt if belt else None)

    def update_env(st, key, val, field_type=None):   
        if field_type==None:    st.s_env[key] = val
        elif field_type==list:    
            try:                st.s_env[key].append(val)
            except:             st.s_env[key] = [val]
        else: raise Exception(key, val, st, field_type, st.init_options)
    def view_env(st, what):         return st.s_env[what]

    def update_ap(st, key, val, who_id): 
        if not st.gm.entities[who_id].write_state_access==True: 
            raise Exception('State writing access not permitted: ActionPicker')
        if not st.s_ap.has_key(who_id):
            st.s_ap[who_id] = {}
        st.s_ap[who_id][key] = val
    def view_ap(st, what, who_id):     return st.s_ap[who_id][what]

    # This is deprecated?:
    def update_dep(st, key, val, who): # who: pass Object Reference
        if type(who) in [str, int]:
            raise Exception('provide object reference, not key or id.')
        if not who.write_state_access:
            raise Exception('State writing access not permitted: Dependent')
        if not st.s_dep.has_key(who.uniq_id):
            st.s_dep[who.uniq_id] = {}
        st.s_dep[who.uniq_id][key] = val
    def view_dep(st, what, who_id): # by object reference
        if not type(who_id)==int: 
            who_id = who_id.uniq_id # Ref to actual object
        return st.s_dep[who_id][what]
    

    # Initialize and define global fields. All globals must start here.
    def setup_fields(st, genus, logic, ppos=None, tpos=None):
        st._init_sensors(logic)
        st._init_actions(logic, genus)

        if genus in RESERVABLE_SPECIES:
            st.s_env['root delay'] = logic.agent.primary_delay
        if genus=='plyr':   st.setup_plyr_fields(logic)
        if genus=='pkmn':   st.setup_basic_pkmn_fields(logic)
        if genus=='target': st.setup_target(logic) 

        st.s_env['tilesize'] = st.gm.tile_size
        if ppos:
            st.s_env['initial tpos'] = divvec(ppos, st.gm.ts())
            st.s_env['initial ppos'] = ppos
        elif tpos:
            st.s_env['initial tpos'] = multvec(tpos, st.gm.ts())
            st.s_env['initial ppos'] = tpos


    def _init_sensors(st, logic):
        st.belt.Sensors = {k:v(st.gm) for k,v in st.belt.Sensors.items()}
        for sensor in st.belt.Sensors.values():
            sensor.set_state(st)

    def _init_actions(st, logic, genus):
        st.belt.Actions = {k:v(logic) for k,v in st.belt.Actions.items()}

    def setup_plyr_fields(st, logic):
        st.s_env['delay'] = 0.001
        # Simple status fields, eg primitives or fixed-structure collections:
        st.s_env['most recently reserved'] = NULL_POSITION # for all blocking agents
        st.s_env['available']       = True
        st.s_env['unit step']       = logic.plyr_steps((1,1))
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
        try:
            # function:
            st.s_env['caught_counter'] = logic.belt.Dependents['caughtbar'].view_metric
        except:
            st.s_env['caught_counter'] = 'not catchable'

        st.s_env['delay'] = np.random.uniform(1.0,2.0)*logic.agent.primary_delay
        st.s_env['most recently reserved'] = NULL_POSITION # for all blocking agents
        st.s_env['unit step'] = logic.gm.ts()
        st.s_env['is being caught'] = False
        st.s_env['motions'] = {k:v for k,v in st.belt.Actions.items()\
                if k in ['r','l','u','d','-']}
        st.s_env['attacks'] = {k:v for k,v in st.belt.Actions.items()\
                if k in ['A']}
