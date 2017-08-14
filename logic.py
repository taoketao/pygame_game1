'''
AI Logic module for handling interactive behavior.

'''
import numpy as np
import abc, pygame, random, sys

from utilities import *
from abstractEntities import *

'''   Constants  '''
# EVAL Key: T/F means the Action[Picker] has evaluated the world and decided
# definitively whether it ought to be called (#decidability!). U indicates 
# an unevaluated or undecided, meaning perception and 'thinking' process is
# awaiting, and should appear iff the entity has called implement() as its most
# recent command.  ERR and INIT are convenience error flags.
# R means running in behavior-tree language.
EVAL_T, EVAL_F, EVAL_U, EVAL_R, EVAL_ERR, EVAL_INIT =  44,55,66,77,88,99
WHICH_EVAL = {EVAL_T:'T', EVAL_F:'F', EVAL_U:'U', EVAL_R:'R', \
                EVAL_ERR:'ERR', EVAL_INIT:'INIT'}
def index_to_ltr(index): return {0:'u', 1:'l', 2:'d', 3:'r', -1:'-'}[index]
#   ^^^^^^^^^^^^ as according to Motions below


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
        sensor._store(sensor.gm.db.execute(querystr, (agent_id,)).fetchone())
        return PRIMED(sensor) # todo: error hangle this a little better.

    def access(sensor, agent_id): 
        if sensor.priming==EVAL_F: 
            return EVAL_F
        if sensor.priming==EVAL_U: 
            sensor.sense(agent_id)
            return sensor.access(agent_id)
        return sensor._storage[sensor.access_name]


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
        print '\ttile obstr sensor occs,info,blck?,tid','\n\t',occups, '\n\t'\
                ,tileinfo, '\n\t',blck, '\n\t',tid
        if len([o for o in occups if o[0]==u'pkmn'])>0: 
            return GET_PRIMED(sensor, sensor._store([ False, tid, blck]))
        if not len(tileinfo)==1: 
            raise Exception((tileinfo, tid))
        blocked_res = [(u'true',)]==tileinfo
        sensor._store([ blocked_res, tid, blck])
        return {True: NOTPRIMED, False: PRIMED}[blocked_res](sensor)

    def access(sensor):
        sensor._sensor_check('access')
        return sensor._storage[sensor.access_name][0]
        
    # Two more sensors to make:
#            put('curr move vec', logic.gm.events[:4])
#            put('triggered actions', logic.gm.events[4:])


#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''        Action and ActionPicker: base classes and exemplars             '''


''' Abstract Action that encodes an action made by a pokemon, attack, npc, etc.
    Actions have one of several values that can be returned on query, which
    tell if an action is viable, for an action picker: 
        T: this action is viable and ready     F: this action is not viable
        U: this action has insufficient information to decide viability.
    The find_viability method will return T or F based on available Sensors
    and the state. implement() performs the action and requires a T viability. '''

class Action(Entity):
    def __init__(action, gm):
        Entity.__init__(action, gm)
        action.species = 'action'
        # action.viability: the core reason for this implementation
        action.viability = EVAL_INIT

    # Methods: get_viability(): T/F/U/..., find_viability() T/F, implement()
    def get_viability(action): return action.viability
    @abc.abstractmethod
    def find_viability(action): raise Exception("Must implement me!")
    @abc.abstractmethod
    def implement(action): raise Exception("Must implement me!")
    @abc.abstractmethod
    def reset(action): raise Exception("Must implement me!")

    # helpers:
    def INVIABLE(action): action.viability=EVAL_F; return EVAL_F
    def VIABLE(action): action.viability=EVAL_T; return EVAL_T
    def GETTRUTH(action, query): return (action.VIABLE() if query==True \
            else action.INVIABLE())
    def GETVIA(action, query): return (action.VIABLE() if \
            query.find_viability()==EVAL_T else action.INVIABLE())
    def Verify(action, query): 
        if not action.GETVIA(query)==EVAL_T:
            raise Exception(query, WHICH_EVAL[query.viability])
        return action.viability
    def VIABILITY_ERROR(action): action.viability = EVAL_ERR; return EVAL_ERR

class ActionPicker(Action):
    ''' ActionPicker: a more practical version of Action that takes Logic. '''
    def __init__(ap, logic):
        Action.__init__(ap, logic.gm)
        ap.logic=logic
        ap.components = []
        ap.key = 'stub key'
        ap.write_state_access = False # by default
    def easy_init(ap, k): 
        ap.write_state_access = True
        ap.key = k
        ap.logic.update_ap(ap.key, EVAL_INIT, ap.uniq_id)
    def reset(ap): 
        ap.viability = EVAL_U


#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''     Convenience, Baseline, and Exemplar Actions and APs            '''


''' MotionAction: a base Action variant that '''
class MotionAction(Action):
    def __init__(action, logic):
        Action.__init__(action, logic.gm)
        action.logic = logic
        action.agent = logic.agent

    def find_viability(action):
        if action.name=='-': return action.VIABLE()
        if action.viability in [EVAL_T, EVAL_F]: return action.viability
        cur_ppos = action.logic.detect('ppos', agent_id=action.logic.agent.uniq_id)
        unit_step = action.logic.view('unit step')
        if EVAL_F in [cur_ppos, unit_step]:
            print "ERR?: cur_ppos & unit_step", cur_ppos, unit_step
            return action.INVIABLE()
        query_ppos = addvec(multvec(action.posvec, unit_step), cur_ppos)
        if action.logic.agent.species=='plyr':
            query_tpos = action.logic.pTOt(query_ppos)
            if action.logic.view('tpos')==query_tpos: return action.VIABLE()
#            print 'curp,unit,queryp,queryt,curt',cur_ppos, unit_step, \
#                    query_ppos, query_tpos, action.logic.view('tpos')
            if not action.logic.prime_sensor('tile obstr', tid=query_tpos, \
                    blck='plyr'): return action.VIABILITY_ERROR()
            return action.GETTRUTH(action.logic.access_sensor('tile obstr'))
        raise Exception()

    def implement(action):
        assert(action.viability==EVAL_T)
        if action.index<0: return
        action.agent.move_in_direction(action.posvec)

    def same(action, targ): return action.index==targ.index # etc
    def reset(action): action.viability = EVAL_U # actually impt here


class MotionUp(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [1,0,0,0];      action.posvec = (0,-1);
        action.name = 'u';            action.index = 0
        action.null=False
class MotionLeft(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,1,0,0];      action.posvec = (-1,0);
        action.name = 'l';            action.index = 1
        action.null=False
class MotionDown(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,0,1,0];      action.posvec = (0,1);
        action.name = 'd';            action.index = 2
        action.null=False
class MotionRight(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,0,0,1];      action.posvec = (1,0);
        action.name = 'r';            action.index = 3
        action.null=False
class MotionStatic(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,0,0,0];      action.posvec = (0,0);
        action.name = '-';            action.index = -1
        action.null=True
class MotionNull(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = None;         action.posvec = NULL_POSITION;
        action.name = '__x__';      action.index = -2
        action.null=True

# Tautologies. Useful for representing variables. Provide str X: state key.
# View() is a shortcut for isTrue(), which simply evaluates the expression
# at runtime; Note that View also needs its structure in order to stay dynamic.

# Note: All of these are Leaf Actions and should not maintain propagation.
class View(ActionPicker):
    def __init__(ap, logic, X):
        ActionPicker.__init__(ap, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): return ap.GETTRUTH(ap.logic.view(ap.X))
    def reset(ap):  ap.viability = EVAL_U;
class isTrue(ActionPicker): # Only changes if X changes via reference!
    def __init__(ap, logic, X):
        ActionPicker.__init__(ap, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): return ap.GETTRUTH(ap.X)
    def reset(ap):  ap.viability = EVAL_U
class nonEmpty(ActionPicker): # Query an element in the State..
    def __init__(ap, logic, X):
        ActionPicker.__init__(ap, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): 
        return ap.GETVIA(sum(ap.logic.view(X))>0)
    def reset(ap): ap.viability = EVAL_U



#-------------#-------------#--------------#--------------#--------------

'''     Standard Composite AP Nodes               '''


# SEQUENTIAL: does all the actions (in order), and returns EVAL_T iff each
#  returns EVAL_T. cp DoAllRetAny, DoAllRetAll.
class Sequential(ActionPicker): # in order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.components = components
        ap.write_state_access = True
    def find_viability(ap): # unpythonic for loop: no short circuit
        for __ai, a in enumerate(ap.components):
            if not EVAL_T==a.find_viability(): 
                return ap.INVIABLE()
        return ap.VIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        for a in ap.components: a.implement()
    def reset(ap):  
        for a in ap.components: a.reset() # naive
        ap.viability = EVAL_U; 

def All(g,l,c): return Sequential(g,l,c)
def Both(g,l,c): return All(g,l,c) if len(c)==2 else EVAL_ERR

# PRIORITY: Given a list, picks the first success in the list (if not any: EVAL_F)
class Priority(ActionPicker): # AKA, DoOneRetOne in order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.components = components
        ap.easy_init('choice')
    def find_viability(ap):
        for ci, c in enumerate(ap.components):
            if EVAL_T==c.find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABILE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.components[ap.logic.view_my(ap.key, ap.uniq_id)].implement()
    def reset(ap):
        ap.viability = EVAL_U
        for a in ap.components[:ap.logic.view_my(ap.key, ap.uniq_id)]: a.reset()

# PickRand a.k.a. Random Priority: pick a viable element at random, if possible.
class PickRand(ActionPicker): # AKA, DoOneRetOne in no order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.logic.update_ap('choice', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('indices', EVAL_INIT, ap.uniq_id)
        ap.components = components

    def find_viability(ap):
        indices = list(range(len(ap.components)))
        random.shuffle(indices)
        ap.logic.update_ap('indices', indices, ap.uniq_id) # For other reference
        for ci in indices:
            if EVAL_T==ap.components[ci].find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABLE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.components[ap.logic.view_my('choice', ap.uniq_id)].implement()
    def reset(ap): 
        ap.viability = EVAL_U; 
        for c in ap.components: c.reset()
        ap.logic.update_ap('indices', EVAL_U, ap.uniq_id)
        ap.logic.update_ap('choice', EVAL_U, ap.uniq_id)


# COND: basic conditional. Returns what <do> returns only when <cond>, else EVAL_T
class Cond(ActionPicker):
    def __init__(ap, logic, cond, do):
        ActionPicker.__init__(ap, logic)
        ap.cond = cond
        ap.do = do
        ap.easy_init('valuation')

    def find_viability(ap):
        cond_via = ap.cond.find_viability()
        ap.logic.update_ap(ap.key, cond_via, ap.uniq_id)
        if cond_via==EVAL_T:
            ap.viability = ap.do.find_viability()
            return ap.viability
        return ap.VIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        if ap.logic.view_my(ap.key, ap.uniq_id)==EVAL_T: ap.do.implement()

    def reset(ap): 
        ap.viability = EVAL_U; ap.cond.reset(); ap.do.reset()
        ap.logic.update_ap(ap.key, EVAL_T, ap.uniq_id)

class TryCatch(ActionPicker):
    def __init__(ap, logic, tr, ca):
        ActionPicker.__init__(ap, logic)
        ap.tr, ap.ca = tr, ca
        ap.easy_init('valuation')

    def find_viability(ap):
        try_via = ap.tr.find_viability()
        ap.logic.update_ap(ap.key, try_via, ap.uniq_id)
        if try_via==EVAL_F:
            if ap.ca: return ap.GETVIA( ap.ca )
        return ap.VIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        if ap.logic.view_my(ap.key, ap.uniq_id)==EVAL_T: ap.tr.implement()
        elif ap.ca: ap.ca.implement() # if implemented, one of the two succeeded.
    def reset(ap):
        ap.viability = EVAL_U; 
        ap.tr.reset(); 
        if ap.ca: ap.ca.reset()
        ap.logic.update_ap(ap.key, EVAL_T, ap.uniq_id)
def Try(logic, tr): return TryCatch(logic, tr, None)


#-------------#-------------#--------------#--------------#--------------

'''     Pokemon logic APs               '''


# wasCaught: query if the pokemon was caught; execute pkmn removal from scene.
class wasCaughtProcessing(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = False # no update; read-only @ State 
        ap.key = 'was catch completed'
    def find_viability(ap): 
        return { True: ap.VIABLE(), False: ap.INVIABLE() }\
                    [ap.logic.view(ap.key)]
    def implement(ap):
        assert(ap.viability==EVAL_T)
        pass # set image to white and kill self
    def reset(ap): ap.viability = EVAL_U;

# wander: pick a random valid direction and move there.
class wander(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.card_dirs = logic.view('available motions')
        ap.chooser = PickRand(ap.card_dirs)
    def find_viability(ap): return ap.chooser.find_viability()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.chooser.implement()
    def reset(ap): ap.viability = EVAL_U; ap.chooser.reset()


class BasicPkmnActionPicker(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.root = Priority(ap.ap.logic [ \
                wasCaughtProcessing(ap.ap.logic) ,\
                # is being caught,
                # use attack move (a big AP itself),
                wander(ap.ap.logic)
                ] )
    def find_viability(ap): return ap.root.find_viability()
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()
    def reset(ap): ap.viability = EVAL_U; ap.root.reset()



#-------------#-------------#--------------#--------------#--------------

'''   Mouse follower, almost a stub. Most of this code has been left
      unotuched, opting to piggyback on previous agents2 work.          '''

class MouseActionPicker(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
    def reset(ap): ap.viability=EVAL_U
    def find_viability(ap):
        ap.logic.update_global('mouse ppos',pygame.mouse.get_pos())
        return ap.VIABLE()
    def implement(ap):
        ap.logic.agent.update_position(ap.logic.pTOt(\
                ap.logic.view('mouse ppos')))
        


#-------------#-------------#--------------#--------------#--------------

'''     Player-exclusive logic APs (as of now)   '''


# Pick Newest: using Pushdown automata, maintain newest. 
# This function is not general as-is, but can be cannibalized quite easily.
# Global state update: makes  
class PickNewest(ActionPicker): 
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.components = logic.view('available motions')#.copy()
        ap.key = 'player motion newest pda'
        ap.logic.update_global("motion ap key", ap.key)


    def find_viability(ap):
        # Messy messy, but so is lateral non-hierarchical variable passing
        ind_priorities = ap.logic.view('curr move vec')[:] 
#        prev_inds = ap.logic.view('prev move vec')
        results = []
        Rng = [d.index for d in ap.logic.view(ap.key) if d.index>=0]
        for i in range(len(ind_priorities)):
            if not i in Rng: Rng.append(i)

        cmpd = {}
        def process_each_case(f):
            for index in Rng:
                i_bool = ind_priorities[index]
                if index in cmpd.keys():
                    Cmp = cmpd[index]
                else:
                    Cmp = cmpd[index] = ap.components[index_to_ltr(index)] # inefficent!
                f(index, i_bool, Cmp)
        def case_new_down(index, i_bool, Cmp):
            if i_bool: 
                ap.logic.update_global('global movedir choice', index)
                if Cmp.find_viability()==EVAL_T:
                    ap.logic.push_PDA(ap.key, Cmp)
                    results.insert(0, index)
                else:
                    ap.logic.pop_PDA(ap.key, Cmp)
        def case_not_down(index, i_bool, Cmp):
            if Cmp.find_viability()==EVAL_T and not i_bool: 
                ap.logic.pop_PDA(ap.key, Cmp)

##        print '--- both down'
#        process_each_case(case_both_down) # in order!
#        print '--- new down'
        process_each_case(case_new_down) # in order!
#        print '--- not down'
        process_each_case(case_not_down) # in order!

        if len(results)==0: 
            ap.logic.push_PDA(ap.key, ap.components['-'])
        return ap.VIABLE()
           
    def implement(ap): assert(ap.viability==EVAL_T)

    def reset(ap): 
        ap.viability = EVAL_U; 
        for c in ap.components.values(): c.reset()

class PushDown(ActionPicker):
    def __init__(ap, logic, dname):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.motion = logic.view('available motions')[dname]

    def find_viability(ap):
        if ap.motion.name=='-': return ap.VIABLE()
        motion_reqs = [int(i) for i in ap.logic.view('curr move vec')]
        if not motion_reqs[ap.motion.index]==1:
            ap.logic.pop_PDA('player motion rand pda', ap.motion.index)
            return ap.INVIABLE() # not requested
        if not ap.motion.find_viability()==EVAL_T:
            ap.logic.pop_PDA('player motion rand pda', ap.motion.index)
            return ap.INVIABLE() # not valid
        ap.logic.push_PDA('player motion rand pda', ap.motion)
        return ap.VIABLE()
    def implement(ap): assert(ap.viability==EVAL_T)

class SetPlayerCycleImage(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic) 
        ap.write_state_access = True
        ap.logic.update_ap('cycler', 0, ap.uniq_id)

    def find_viability(ap): return ap.VIABLE()
    def reset(ap): ap.viability=EVAL_U
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        c = ap.logic.view_my('cycler', ap.uniq_id)
        if ap.logic.view(ap.logic.view("motion ap key"))[0].name=='-':
            c=0
        try:
            choose_img = ap.logic.view(ap.logic.view("motion ap key"))[0].index*3
            assert(choose_img>=0)
        except:
            choose_img = ap.logic.view('global movedir choice') * 3
            if choose_img<0:
                raise Exception()
#        choose_img = ap.logic.view('global movedir choice') * 3

        ap.logic.agent.set_img(choose_img + c )
        ap.logic.update_global("Image", 'player sprite '+\
                                str(choose_img + c ))
        if sum(ap.logic.view('curr move vec'))==0: return
        c += 1
        if c==3: c=0
        ap.logic.update_ap('cycler', c, ap.uniq_id)
        

# Actually carry out a picked action once ready:
class orderPDAAction(ActionPicker):
    def __init__(ap, logic, mode):
        ActionPicker.__init__(ap, logic)
        ap.VIABLE()
    def find_viability(ap): 
#        motion_key = ap.logic.view("motion ap key")
        return ap.GETVIA(ap.logic.view(ap.logic.view("motion ap key"))[0]) 
    def reset(ap): ap.viability = EVAL_U;
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        if not ap.viability==EVAL_T:
            return logic.do_default()
        motion_key = ap.logic.view("motion ap key")
        return ap.logic.view(motion_key)[0].implement()


class PlayerMotion(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.root = Sequential(logic, [\
                    PickNewest(logic),\
                    orderPDAAction(logic, 'newest'),\
                    SetPlayerCycleImage(logic), \
                  ])
    def find_viability(ap): return ap.Verify(ap.root)
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()
    def reset(ap): ap.viability = EVAL_U; ap.root.reset()

def ThrowPokeball(x,y): pass            


class BasicPlayerActionPicker(ActionPicker): 
    # directly-used subclasses inherit from Entity.
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.logic.update_ap('last move', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('heading', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('cycle', EVAL_INIT, ap.uniq_id)

#        ap.root = Sequential(g,l, \
#            Cond(g,l, All(g,l,[View(g,l,'isPlayerActionable'), 
#                               nonempty('triggered actions')],\
#                          ThrowPokeball(g,l)),\
#            PlayerMotion(g,l)))
#        ap.root = Sequential(g,l, [View(g,l,'isPlayerActionable')])
        ap.root = Try(logic, PlayerMotion(logic) )
        

    def reset(ap): 
        ap.viability = EVAL_U
        ap.root.reset()

    def find_viability(ap): 
        if not ap.viability == EVAL_U: raise Exception("Please call reset!")
        return ap.Verify(ap.root)

    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()



#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''             State               '''


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
        st.s_env['tpos']            = NULL_POSITION
        st.s_env['ppos']            = NULL_POSITION
        st.s_env['available']       = True
        st.s_env['unit step']       = parent_logic.plyr_steps((1,1))
#        st.s_env['prev move vec']   = [0,0,0,0]
        st.s_env['curr move vec']   = [0,0,0,0]
        st.s_env['num moves']       = 4
        st.s_env['Image']           = 'player sprite 7' # down
        st.s_env['motion ap key'] = None 
        st.s_env['isPlayerActionable'] = True
        if not st.belt: raise Exception('Need at least an empty belt.')

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


#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''             Logic               '''

class Logic(Entity):
    ''' Logic: the unique logic root of an agent that maintains an active
        internal state and belts for the agent. Simple entities like most Moves 
        I organize ActionPickers and field messages to update State. 
        Belt should be fully initialized; changes now must be fielded through me.

        Public Methods: 
        (cp Update/Decide/Implement with reset/find_viability/implement)   '''

#-- Interface method        __ Update __        Call before choosing actions 
    def Update(logic):
        # Wipe sensors and prime them

        # Read and process messages:
        while len(logic.message_queue)>0:
            print "processing message..."
            msg = logic.message_queue.pop(0)
            logic._state.update_ext(msg[0],msg[1])

        # Notify actions and ActionPickers that they can reset for next frame:
        logic.root_ap.reset()
        put = logic._state.update_env
        if logic.agent.species=='plyr': 
            # Update _state for new frame for PLAYER:
            # (ideally, sensors would offload most of this)
            put('curr move vec', logic.gm.events[:4])
            put('triggered actions', logic.gm.events[4:])
            print '---'

#        prev_inds = ap.logic.view('prev move vec')

        for snm,sensor in logic.belt.Sensors.items():
            sensor.rescan()


#-- Interface method        __ Decide __        Call for ALL before implementing
    def Decide(logic):      logic.root_ap.find_viability()
#-- Interface method        __ Implement __        Call after Deciding, for all
    def Implement(logic):   logic.root_ap.implement()

    # Notify: primary inbox method!
    def notify(logic, whatCol, whatVal):
        logic.message_queue.append( (whatCol, whatVal) )


    ''' ----------  Private methods  ---------- '''

    def __init__(logic, gm, agent, belt=None, init_belt=None, init_ppos=None):
        Entity.__init__(logic, gm)
        logic._state = State(gm, belt)
        logic.agent = agent
        if belt: 
            logic.belt = belt
            for action in belt.Actions.values(): action.logic=logic
        logic.message_queue = []
        logic._state.setup_fields(agent.species, logic, ppos=init_ppos)
        if agent.species=='plyr': 
            logic.root_ap = BasicPlayerActionPicker(logic)
        elif agent.species=='target':
            logic.root_ap = MouseActionPicker(logic)
        else:
            raise Exception('not impl yet')
        
        logic.root_ap.reset()

    def get_sensor(logic, name): return logic.belt.Sensors.get(name, False)

    def view_my(logic, what, who): return logic._state.view_ap(what, who)
    def view(logic, what):  # view environmental variables.
        return logic._state.view_env(what)
        pass; # THIS function is a good place to engage Sensors.
#        sensor_name = logic.sensor_map(what) 
#        sensor_status = logic._state.sensor_status.get(sensor_name, EVAL_U)
#        if sensor_status==EVAL_U: sensor_status = sensor.rescan()
#        if sensor_status==EVAL_F: return None
#        if sensor_status==EVAL_T:
#            return logic._state.view_env(what)

    def get_resource(logic, database, which_resource):
        if database=='plyr img':
            return logic.gm.imgs['player sprite '+str(which_resource)]
    def has_sensor(logic, what_sensor):
        return not logic.get_sensor(what_sensor)==False
    def detect(logic, what_sensor, **args): 
        # specialty method that both primes and accesses
        s = logic.get_sensor(what_sensor)
        #print '>>',WHICH_EVAL[s.sense(**args)]
        return s.access(**args)

    def prime_sensor(logic, what_sensor, **args):
        return logic.get_sensor(what_sensor).sense(**args)
    def access_sensor(logic, what_sensor, **args):
        return logic.get_sensor(what_sensor).access(**args)

    def plyr_steps(logic, dvec): 
        if not logic.agent.species=='plyr': 
            raise Exception('notice: not plyr object')
        print '^v^v^', dvec, logic.gm.smoothing(), logic.agent.stepsize
        return ( dvec[X] * logic.gm.smoothing() * logic.agent.stepsize_x, \
                 dvec[Y] * logic.gm.smoothing() * logic.agent.stepsize_y)
    def pop_PDA(logic, which_pda, new):
        if not which_pda in ['player motion rand pda', 'player motion newest pda']: 
            raise Exception("This pushdown Automata not impl")
        s=[w for w in logic._state.s_env[which_pda] if not w.index==new.index]
        logic._state.s_env[which_pda] = s
    def push_PDA(logic, which_pda, element):
        if not element in logic._state.s_env[which_pda]:
            logic._state.s_env[which_pda].insert(0, element)
    def append_PDA(logic, which_pda, element):
        if not element in logic._state.s_env[which_pda]:
            logic._state.s_env[which_pda].append(element)

    def do_default(logic): return EVAL_T # semi-stub


    def tTOp(logic, X): 
        try: return multvec(X, logic.gm.tile_size, int)
        except: raise Exception(X)
    def pTOt(logic, X): 
        try: return divvec(X, logic.gm.tile_size, '//')
        except: raise Exception(X)
    
    def update_ap(logic, key, value, who):
        logic._state.update_ap(key, value, who)
    def update_global(logic, key, value): # for internal use only!
        logic._state.update_env(key, value)



        
#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''             Belt               '''



''' stored_pkmn: a struct-class that stores sufficient information to
    totally recreate a pokemon. Has constructor, comparator, save methods.'''
class stored_pkmn(Entity):
    def __init__(sp, gm, pkmn_aiagent_obj=None, which_pkmn_id=-1, \
                    cur_health=-1): 
        Entity.__init__(sp, gm)
        sp.fields \
            = [sp.pkmn_id, sp.maxhealth, sp.curhealth, sp.moves, sp.afflictions] \
            = [None, None, None, None, None]
        if not pkmn_aiagent_obj==None:
            sp._ingest_as_ai_agent(pkmn_aiagent_obj)

    def _ingest_as_ai_agent(sp, pkmn_ai):
        sp.max_health = pkmn_ai.max_health
        sp.cur_health = pkmn_ai.cur_health
        sp.was_wild = True if pkmn_ai.team=='wild' else False



class Belt(Entity):
    ''' Belt: Actions and Sensors are lists of available functions for Action
        Pickers to utilitize.   Core Attributes that all Belts have:
        --Actions: the available actions that the Agent can decide amongst. The
            decision process or what the actions represent are not relevant.
        --Sensors: the various tool this entity has to understand its environment.
            Encapsulates both trivial behavior handling as well as a behavior-
            -altering effect: with more Senses, different things can be done
            with its knowledge!
        Auxiliarry Attributes that only some Belts have:
        --Items: The user-facing multiset of consumable items.
        --Pkmn: The list of pokemon this character or object 'owns'.

        future: add AnimationScript? Versioning? Geomapping? Zoning? '''
    def __init__(belt, gm, whose_belt, sp_init=None, std_sensor_suite=True): 
        Entity.__init__(belt, gm)
        if not isinstance(whose_belt, VisualStepAgent): 
            raise Exception(type(whose_belt))
        belt.whose_belt = whose_belt
        belt.gm = gm

        belt.Sensors = {True: { 'ppos':GetPPosSensor, 'tpos':GetTPosSensor, \
                                'smoothing':GetFrameSmoothingSensor ,\
                                'unit step':GetCurUnitStepSensor }, \
                        False: {} }[std_sensor_suite==True]
        
        if sp_init=='basic player':
            belt.Items = ['pokeball-lvl-1']*4
            belt.Pkmn = []
            belt.Actions ={ 'u':MotionUp,     \
                            'd':MotionDown,   \
                            'l':MotionLeft,   \
                            'r':MotionRight,  \
                            '-':MotionStatic  }
            belt.Sensors.update({'tile obstr':TileObstrSensor })
        elif sp_init=='pokeball catch':
            belt.Actions = {'anim':AnimLinear, 'c':TryToCatch, 'add':AddPkmn}
            belt.Sensors = [WildEntSensor]
        elif sp_init=='target':
            belt.Actions = {}
            belt.Sensors, belt.Pkmn, belt.Items = None, None, None
        else: raise Exception("an easy, nbd exception but please implement.")
        if not False: # situation
            belt.Sensors.update({}) # Todo: gm.smooth sensor, etc

    def add_pkmn(belt, pkmn):
        belt.Pkmn.append(stored_pkmn(belt.gm, pkmn))
            
