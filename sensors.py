from utilities import *
from abstractEntities import Entity
import abc 



#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''             Sensor               '''

def NOTPRIMED(sensor): sensor.priming=EVAL_F; return EVAL_F
def PRIMED(sensor): sensor.priming=EVAL_T; return EVAL_T
def GET_PRIMED(sensor,p): sensor.priming=p; return p
class Sensor(Entity):
    ''' Sensor class: this is an object that can answer questions, engaging
        various game resources if necessary.  '''
    def __init__(sensor, gm):
        Entity.__init__(sensor, gm)
        sensor.gm = gm
        sensor.priming = EVAL_INIT # Like Actions below, must compute before use.
        sensor.write_state_access = True # Sensors inherently write!
        sensor.state = None

    def _sensor_check(sensor, what):
        assert(sensor.priming in [EVAL_T,EVAL_F])
        if what=='access':
            if sensor.priming == EVAL_F: 
                return EVAL_F
        return EVAL_T

    def _abstract_query(sensor, acquisition_method, condition, am_params=None):
        try: options = acquisition_method(am_params)
        except: options = acquisition_method()
        return [o for o in options if condition(o)]

    def set_state(sensor, state): # Init function.
        if not sensor.state == None: raise Exception("State has already been set.")
        #state.s_ssr[sensor.uniq_id] = {}
        #sensor._storage = state.s_ssr[sensor.uniq_id]
        state.s_ssr = {}
        sensor._storage = state.s_ssr

    def _store(sensor, value): # ret: was the store successful?
        sensor._storage[sensor.access_name] = value

    def get_priming(sensor): return sensor.priming

    def access(sensor, *what): # ret: was the store successful?
        if sensor._sensor_check('access')==EVAL_F:
            if not sensor.sense(what)==EVAL_T:
                return EVAL_F;
        return sensor._storage[sensor.access_name]

    def rescan(sensor):
        NOTPRIMED(sensor)

    @abc.abstractmethod
    def sense(sensor, *what): raise Exception("Implement me please")


class GetTPosSensor(Sensor):
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'tpos'
    def sense(sensor, args):
        sensor._sensor_check('sense')
        agent_id = args['agent id']
        querystr = 'SELECT tx,ty FROM agent_locations WHERE uniq_id==?;'
        try:
            sensor._store(sensor.gm.db.execute(querystr, (agent_id,)).fetchone())
            return PRIMED(sensor)
        except: return NOTPRIMED(sensor)

class GetPPosSensor(Sensor):
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'ppos'

    def sense(sensor, agent_id):
        if sensor.priming==EVAL_T: # a positive result has already been found:
            return sensor._storage[sensor.access_name]
        sensor._sensor_check('sense')
        querystr = 'SELECT px,py FROM agent_locations WHERE uniq_id==?;'
        sensor._store([agent_id, sensor.gm.db.execute(querystr, (agent_id,)).fetchone()])
        return PRIMED(sensor) # todo: error hangle this a little better.

    def access(sensor): 
        #print 'sensor priming', sensor.priming
        agent_id=sensor._storage[sensor.access_name][0]
        if sensor.priming==EVAL_F: 
            sensor.sense(agent_id)
        if sensor.priming==EVAL_F:  # still:
            raise Exception(sensor.priming)
            return sensor.access(agent_id)
        return sensor._storage[sensor.access_name][1]


class GetFrameSmoothingSensor(Sensor):
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'tpos'
    def sense(sensor): 
        sensor._store(sensor.gm.smoothing())
        return PRIMED(sensor)

class GetCurUnitStepSensor(Sensor):
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'unit step'
    def sense(sensor, vsa_id): 
        sensor._store(sensor.gm.entities[vsa_id].get_pstep())
        return PRIMED(sensor)

class WildEntSensor(Sensor): # TODO totally out of date!
    # Query: at the specific tile, get all the wild pokemon here.
    # Use case: estimated, for pokeball_throw move.
    def __init__(sensor, gm): Sensor.__init__(sensor, gm)
    def query_get_wild_at_tile(sensor, tid):
        return [x[1] for x in sensor._abstract_query(\
                sensor.gm.get_tile_occupants, (lambda x: x[2]==u'wild'), tid)]
    def sense(sensor, tid): return sensor.query_get_wild_at_tile(tid)

class TileObstrSensor(Sensor):
    # Query: at the specific tile, get blocking (T:obstr/F:free) info here.
    # Use case: moving. Uses agent component block_[plyr,pkmn,flying,water].
    def __init__(sensor, gm): 
        Sensor.__init__(sensor, gm)
        sensor.access_name = "tile obstr"

    def sense(sensor, tid, blck): 
        sensor._sensor_check('sense')
        try: assert(blck[:6]=='block_')
        except: blck = 'block_'+blck
        occups, tileinfo = sensor.gm.query_tile(tid, blck)
#        print '\ttile obstr sensor occs,info,blck?,tid','\n\t',occups, '\n\t'\
#                ,tileinfo, '\n\t',blck, '\n\t',tid
        if len([o for o in occups if o[0]==u'pkmn'])>0: 
##            print "Getting primed: pokemon"
            return GET_PRIMED(sensor, sensor._store([ False, tid, blck]))
        if not len(tileinfo)==1: 
            raise Exception((tileinfo, tid))
        blocked_res = [(u'true',)]==tileinfo
        sensor._store([ blocked_res, tid, blck])
#        print "blocked result: ", blocked_res, tid, WHICH_EVAL[{True: NOTPRIMED, \
#                False: PRIMED}[blocked_res](sensor)], sensor._storage
        return {True: NOTPRIMED, False: PRIMED}[blocked_res](sensor)

    def access(sensor):
        sensor._sensor_check('access')
#        print "TileObstr access returns:", sensor._storage[sensor.access_name][0]
        return sensor._storage[sensor.access_name][0]
        
    # Two more sensors to make:
#            put('curr move vec', logic.gm.events[:4])
#            put('triggered actions', logic.gm.events[4:])
