from abstractEntities import Entity

'''             State               '''

''' State: Always associated with a Logic and required by any Actions
that are ActionPicker, the State maintains various information fields.'''



#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------


class State(Entity): # i do not write, so no need to have logic
    def __init__(st, gm, belt=None):
        Entity.__init__(st, gm)
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
    def view_ap(st, what, who):  return st.s_ap[who][what]

    def update_env(st, key, val): 
#        if not key in st.s_env.keys(): raise Exception(key, val, \
#                "Global field was not initialized; please specify in setup or use Sensor.")
        st.s_env[key] = val
    def view_env(st, what):
        return st.s_env[what]

    # Initialize and define global fields. All globals must start here.
    def setup_fields(st, genus, parent_logic, ppos=None):
        st._init_sensors(parent_logic)
        st._init_actions(parent_logic)

        st.s_env['tilesize'] = st.gm.tile_size
        if genus=='plyr':   st.setup_plyr_fields(parent_logic)
        if genus=='pkmn':   st.setup_basic_pkmn_fields(parent_logic)
        if genus=='target': st.setup_mouse(parent_logic) 
        if ppos:
            st.s_env['tpos'] = divvec(ppos, st.gm.ts())
            st.s_env['ppos'] = ppos


    def _init_sensors(st, parent_logic):
        st.belt.Sensors = {k:v(st.gm) for k,v in st.belt.Sensors.items()}
        for sensor in st.belt.Sensors.values():
            sensor.set_state(st)

    def _init_actions(st, parent_logic):
        st.belt.Actions = {k:v(parent_logic) for k,v in st.belt.Actions.items()}
        st.s_env['available motions'] = st.belt.Actions # todo! For now.

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

        st.s_env['PDA']             = [st.belt.Actions['d']]
        # Dynamic fields:
        st.s_env['player motion rand pda'] = [st.s_env['available motions']['-']]
        st.s_env['player motion newest pda']=[st.s_env['available motions']['-']]
        st.s_env['global movedir choice'] = 2 # down
  


    def setup_mouse(st, logic):
        st.s_env['mouse ppos'] = NULL_POSITION

    def setup_basic_pkmn_fields(st):
        st.s_env['is being caught'] = False
        st.s_env['available motions'] = [MotionUp(st.gm), MotionDown(st.gm), \
                MotionLeft(st.gm), MotionRight(st.gm), MotionStatic(st.gm) ]
