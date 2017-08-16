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

    def set_state(sensor, state): # Init function
        if not sensor.state == None: 
            raise Exception("State has already been set.")
        if state=='stateless':
            sensor._storage = {}
        else:
            sensor._storage = state.s_ssr[sensor.access_name] = {}

    def _store(sensor, value): # ret: was the store successful?
        if type(value)==dict:
            sensor._storage.update(value)
            for k in value.keys():
                sensor._storage[k]=value[k]
        else:
            sensor._storage = value

    def get_priming(sensor): return sensor.priming
    def prime(sensor): 
        sensor._sensor_check('sense')
        return PRIMED(sensor)
    def _retrieve(sensor, *keys):
        if len(keys)==0: return sensor._storage
        elif len(keys)==1: return sensor._storage[keys[0]]
        else: 
            print "console log: should probably be using a MultiSensor."
            return sensor._storage[keys]
    
    def rescan(sensor): NOTPRIMED(sensor)
    @abc.abstractmethod
    def sense(sensor, *what): raise Exception("Implement me please")


''' TPOS tile position of a target entity '''
class GetTPosSensor(Sensor):
    def __init__(sensor, gm, agent_id=None):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'tpos'
        if agent_id: sensor.agent_id = agent_id
    def sense(sensor, agent_id=None):
        if agent_id==None: agent_id = sensor.agent_id
        if sensor.get_priming()==EVAL_T:
            return sensor._retrieve(agent_id)
        sensor.prime()
        querystr = 'SELECT tx,ty FROM agent_locations WHERE uniq_id==?;'
        sensor._store({agent_id: sensor.gm.db.execute(querystr, (agent_id,)).fetchone()})
        return sensor.sense(agent_id)

''' PPOS pixel position of a target entity '''
class GetPPosSensor(Sensor):
    def __init__(sensor, gm, agent_id=None):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'ppos'
        if agent_id: sensor.agent_id = agent_id
    def sense(sensor, agent_id=None):
        if agent_id==None: agent_id = sensor.agent_id
        if sensor.get_priming()==EVAL_T:
            return sensor._retrieve(agent_id)
        sensor.prime()
        querystr = 'SELECT px,py FROM agent_locations WHERE uniq_id==?;'
        sensor._store({agent_id: sensor.gm.db.execute(querystr, (agent_id,)).fetchone()})
        return sensor.sense(agent_id)

''' Mouse position '''
class GetMouseTIDSensor(Sensor):
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'mousepos'
    def sense(sensor):
        if sensor.get_priming()==EVAL_T:
            return sensor._retrieve()
        sensor.prime()
        sensor._store(sensor.gm.request_mousepos('tpos'))
        return sensor._retrieve()

#''' User input indicating position '''
#class GetMoveInputSensor(Sensor):
#    def __init__(sensor, gm):
#        Sensor.__init__(sensor, gm)
#        sensor.access_name = 'curr move vec'
#    def sense(sensor):
#        if sensor.get_priming()==EVAL_T:
#            sensor._store(sensor.gm.request_mousepos('tpos')) # Add any more queued
#            return sensor._retrieve()
#        sensor.prime()


class GetFrameSmoothingSensor(Sensor):
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'tpos'
    def sense(sensor): 
        if sensor.get_priming()==EVAL_T:
            return sensor._retrieve()
#            return sensor._storage[sensor.access_name]
        sensor.prime()
        sensor._store(sensor.gm.smoothing())
        return sensor.sense()

class GetCurUnitStepSensor(Sensor):
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)
        sensor.access_name = 'unit step'
    def sense(sensor, vsa_id): 
        if sensor.get_priming()==EVAL_T:
            return sensor._retrieve(vsa_id)
#            return sensor._storage[sensor.access_name][vsa_id]
        sensor.prime()
        sensor._store({vsa_id:sensor.gm.entities[vsa_id].get_pstep()})
        return sensor.sense(vsa_id)

class WildEntSensor(Sensor): # TODO totally out of date!
    # Query: at the specific tile, get all the wild pokemon here.
    # Use case: estimated, for pokeball_throw move.
    def __init__(sensor, gm): Sensor.__init__(sensor, gm)
    def query_get_wild_at_tile(sensor, tid):
        return [x[1] for x in sensor._abstract_query(\
                sensor.gm.get_tile_occupants, (lambda x: x[2]==u'wild'), tid)]
    def sense(sensor, tid): return sensor.query_get_wild_at_tile(tid)

class MultiSensor(Sensor):
# A sensor whose 'primeness' is multifaceted. EVAL returned depends on input.
    def __init__(sensor, gm):
        Sensor.__init__(sensor, gm)

    def set_state(sensor, state): # Init function.
        if not sensor.state == None: raise Exception("State has already been set.")
        sensor._storage = state.s_ssr[sensor.access_name] = {}
        sensor._primings = {}; sensor.priming=EVAL_U

    def _sensor_check(sensor, stage=None, what=None): 
        assert(sensor.priming==EVAL_U)
        if what: 
            assert(type(what))==dict
            for k in what.keys(): assert(sensor._primings[k]==EVAL_F)

    def query_priming(sensor, *keys): 
        try: return sensor._primings[keys]
        except: return EVAL_F
    def get_primings(sensor): return sensor._primings
    def _store(sensor, value):
        sensor._sensor_check()
        for k in value.keys():
            sensor._primings[k]=EVAL_T
            sensor._storage[k]=value[k]

    def _retrieve(sensor, *keys):
        sensor._sensor_check()
        return sensor._storage[keys]
    
    def rescan(sensor):  # Prune memory here.
        sensor._sensor_check()
        for k in sensor._primings.keys(): sensor._primings[k]=EVAL_F
    @abc.abstractmethod
    def sense(sensor, *what): raise Exception("Implement me please")

class TileObstrSensor(MultiSensor):
    # Query: at the specific tile, get blocking (T:obstr/F:free) info here.
    # Use case: moving. Uses agent component block_[plyr,pkmn,flying,water].
    def __init__(sensor, gm): 
        MultiSensor.__init__(sensor, gm)
        sensor.access_name = "tile obstr"

    def sense(sensor, tid, blck): 
#        print "sensing tile",tid,'. Primings:', sensor.get_primings()
        try: assert(blck[:6]=='block_')
        except: blck = 'block_'+blck
        if sensor.query_priming(tid, blck)==EVAL_T:
            return sensor._retrieve(tid, blck)
        occups, tileinfo = sensor.gm.query_tile(tid, blck)
        if len([o for o in occups if o[0]==u'pkmn'])>0: 
            sensor._store({(tid, blck): False})
            return sensor.sense(tid, blck)
        if not len(tileinfo)==1: 
            raise Exception((tileinfo, tid))
        blocked_res = [(u'true',)]==tileinfo
        sensor._store({(tid,blck): blocked_res})
        return blocked_res

# Query a tile for the teams of its occupants 
class TeamDetector(MultiSensor): 
    def __init__(sensor, gm, radius=-1): 
        MultiSensor.__init__(sensor, gm)
        sensor.access_name = "team detector"

    def sense(sensor, tid, pos=None):
        if pos and dist(pos, tid)>radius: # for later.
            sensor._store({tid: set()})
            return []
        if sensor.query_priming(tid)==EVAL_T:
            return sensor._retrieve(tid)
        occups = sensor.gm.get_tile_occupants(tid) # list of a_type,id,team
        sensor._store({tid: set(o[2] for o in occups)})
        return sensor._retrieve(tid)

    def _retrieve(sensor, tid):
        sensor._sensor_check()
        return sorted(list(sensor._storage[tid]))
