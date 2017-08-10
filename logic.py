'''
AI Logic module for handling interactive behavior.

'''
import numpy as np
import abc, pygame, random

from utilities import *
from abstractEntities import *

# EVAL Key: T/F means the Action[Picker] has evaluated the world and decided
# definitively whether it ought to be called (#decidability!). U indicates 
# an unevaluated or undecided, meaning perception and 'thinking' process is
# awaiting, and should appear iff the entity has called implement() as its most
# recent command.  ERR and INIT are convenience error flags.
# R means running in behavior-tree language.
EVAL_T, EVAL_F, EVAL_U, EVAL_R, EVAL_ERR, EVAL_INIT =  44,55,66,77,88,99
WHICH_EVAL = {EVAL_T:'T', EVAL_F:'F', EVAL_U:'U', EVAL_R:'R', \
                EVAL_ERR:'ERR', EVAL_INIT:'INIT'}




class Sensor(Entity):
    ''' Sensor class: this is an object that can answer questions, engaging
        various game resources if necessary.  '''
    def __init__(sensor, gm):
        Entity.__init__(sensor, gm)
        sensor.gm = gm
#        sensor.belt = belt
        #sensor.parent = parent_action_picker
        pass
    def _abstract_query(sensor, acquisition_method, condition, am_params=None):
        try: options = acquisition_method(am_params)
        except: options = acquisition_method()
        return [o for o in options if condition(o)]

    @abc.abstractmethod
    def sense(sensor, params): raise Exception("Implement me please")


class WildEntSensor(Sensor):
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
    def __init__(sensor, gm): Sensor.__init__(sensor, gm)
    def sense(sensor, tid, blck): 
        #blck = 'block_'+sensor.logic.agent.string_sub_class
        try: assert(blck[:6]=='block_')
        except: blck = 'block_'+blck
        occups, tileinfo = sensor.gm.query_tile(tid, blck)
        print '\ttile obstr sensor occs,info,blck?,tid',occups, tileinfo, blck, tid
        if len(occups)>0: return True
        if not len(tileinfo)==1: raise Exception((tileinfo, tid))
        return True if u'true' in tileinfo else False
        








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
        action.string_sub_class = 'action'
        action.viability = EVAL_INIT

    # Methods: get_viability(): T/F/U/..., find_viability() T/F, implement()
    def get_viability(action): return action.viability
    @abc.abstractmethod
    def find_viability(action): raise Exception("Must implement me!")
    @abc.abstractmethod
    def implement(action): raise Exception("Must implement me!")
    @abc.abstractmethod
    def reset(action): raise Exception("Must implement me!") # Call before viable!

    # helpers:
    def INVIABLE(action): action.viability=EVAL_F; return EVAL_F
    def VIABLE(action): action.viability=EVAL_T; return EVAL_T
    def GETTRUTH(action, query): return (action.VIABLE() if query==True \
            else action.INVIABLE())
    def GETVIA(action, query): return (action.VIABLE() if \
            query.find_viability()==EVAL_T else action.INVIABLE())

class MotionAction(Action):
    def __init__(action, gm):
        Action.__init__(action, gm)
        action.gent = None
        action.unit_move = None
    def find_viability(action):
        cur_tpos = action.logic.view('tpos')
        querypos = addvec(action.posvec, cur_tpos)
        if action.logic.agent.string_sub_class=='plyr':
            print action.logic.access_sensor('tile obstr info', querypos)
            if action.logic.access_sensor('tile obstr info', querypos)==True:
                return INVIABLE()
            else:
                return VIABLE()

    def link_to_gent(action, gent, unit_move=None): action.gent = gent

    def implement(action):
        if action.index<0: return
        if action.gent: action.gent.move_tpos(action.posvec)
    def same(action, targ): return action.index==targ.index # etc

class MotionUp(MotionAction):
    def __init__(action, gm):
        MotionAction.__init__(action, gm)
        action.dvec = [1,0,0,0];      action.posvec = (0,-1);
        action.name = 'u';            action.index = 0
        action.null=False
class MotionLeft(MotionAction):
    def __init__(action, gm):
        MotionAction.__init__(action, gm)
        action.dvec = [0,1,0,0];      action.posvec = (-1,0);
        action.name = 'l';            action.index = 1
        action.null=False
class MotionDown(MotionAction):
    def __init__(action, gm):
        MotionAction.__init__(action, gm)
        action.dvec = [0,0,1,0];      action.posvec = (0,1);
        action.name = 'd';            action.index = 2
        action.null=False
class MotionRight(MotionAction):
    def __init__(action, gm):
        MotionAction.__init__(action, gm)
        action.dvec = [0,0,0,1];      action.posvec = (1,0);
        action.name = 'r';            action.index = 3
        action.null=False
class MotionStatic(MotionAction):
    def __init__(action, gm):
        MotionAction.__init__(action, gm)
        action.dvec = [0,0,0,0];      action.posvec = (0,0);
        action.name = '-';            action.index = -1
        action.null=True
class MotionNull(MotionAction):
    def __init__(action, gm):
        MotionAction.__init__(action, gm)
        action.dvec = None;         action.posvec = NULL_POSITION;
        action.name = '__x__';      action.index = -2
        action.null=True


class SetCycleImage(Action):
    def __init__(action, gm):
        Action.__init__(action, gm) # TODO
        action.curpos = curpos
        action.logic.require('tile obstr info')
    # Methods: get_viability(): T/F/U/..., find_viability() T/F, implement()
    def get_viability(action): return EVAL_T
    @abc.abstractmethod
    def implement(action): raise Exception("Must implement me!")

    def find_viability(action):
        cur_tpos = action.logic.get_tpos()
        querypos = addvec(action.posvec, cur_tpos)
        if action.logic.agent.string_sub_class=='plyr':
            if action.logic.access_sensor('tile obstr info', querypos)==True:
                action.viability = EVAL_F
            else:
                action.viability = EVAL_T







class ActionPicker(Action):
    ''' ActionPicker: a level-wise logical decision tree for a given agent.
        Has fields Belt, associated behavior tree that maps to Belt elements, 
        Sensor suite that constituent Belt elements can engage, and a reference
        to the root Logic object that maintains the agent's state.  Note that 
        the ActionPicker is the one that organizes *all* hierarchy: the Belt's
        collection of sensors and actions are in a plain unleveled set.
        
        Update: this is now a special kind of Action subclass, where instead
        of directly executing actions, this enacts other ones with the assistance
        of access to the State that is maintained by a Logic.

        Methods: a read-only find_viability() which couples perception with 
            decision making, implement() which executes a command, meaning 
            a higher-up logic, entity, or actionPicker has approved this act;
            and reset() which needs to be called 
        '''
    def __init__(ap, gm, logic):
        Action.__init__(ap, gm)
        ap.logic=logic
        ap.components = []
        ap.key = 'stub key'
        ap.write_state_access = False # by default
    def easy_init(ap, k): 
        ap.write_state_access = True
        ap.key = k
        ap.logic.update_ap(ap.key, EVAL_INIT, ap.uniq_id)
    def reset(ap): 
        action.viability = EVAL_U

# SEQUENTIAL: does all the actions (in order), and returns EVAL_T iff each
#  returns EVAL_T. cp DoAllRetAny, DoNRetM.
class Sequential(ActionPicker): # in order
    def __init__(ap, gm, logic, components):
        ActionPicker.__init__(ap, gm, logic)
        ap.components = components
        ap.write_state_access = True
    def find_viability(ap): # unpythonic for loop to verify short circuit
        for a in ap.components:
            if not EVAL_T==a.find_viability(): return ap.INVIABLE()
        return ap.VIABLE()
    def implement(ap):
        for a in a.components: a.implement()
    def reset(ap):  action.viability = EVAL_U
def All(g,l,c): return Sequential(g,l,c)
def Both(g,l,c): return All(g,l,c) if len(c)==2 else EVAL_ERR

# PRIORITY: Given a list, picks the first success in the list (if not any: EVAL_F)
class Priority(ActionPicker): # AKA, DoOneRetOne in order
    def __init__(ap, gm, logic, components):
        ActionPicker.__init__(ap, gm, logic)
        ap.components = components
        ap.easy_init('choice')
    def find_viability(ap):
        for ci, c in enumerate(ap.components):
            if EVAL_T==c.find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABILE()
        return ap.INVIABLE()
    def implement(ap):
        ap.components[ap.logic.view(ap.key, ap.uniq_id)].implement()
    def reset(ap):
        action.viability = EVAL_U
        for a in ap.components[:ap.logic.view(ap.key, ap.uniq_id)]: a.reset()

# PickRand a.k.a. Random Priority: pick a viable element at random, if possible.
class PickRand(ActionPicker): # AKA, DoOneRetOne in no order
    def __init__(ap, gm, logic, components):
        ActionPicker.__init__(ap, gm, logic)
        ap.easy_init('choice')
    def find_viability(ap):
        indices = list(range(len(ap.components)))
        random.shuffle(indices)
        for ci in indices:
            if EVAL_T==ap.components[ci].find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABILE()
        return ap.INVIABLE()
    def implement(ap):
        ap.components[ap.logic.view(ap.key, ap.uniq_id)].implement()

# COND: basic conditional. Returns what <do> returns only when <cond>, else EVAL_T
class Cond(ActionPicker):
    def __init__(ap, gm, logic, cond, do):
        ActionPicker.__init__(ap, gm, logic)
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
        if ap.logic.view(ap.key, ap.uniq_id)==EVAL_T: ap.do.implement()

class TryCatch(ActionPicker):
    def __init__(ap, gm, logic, tr, ca):
        ActionPicker.__init__(ap, gm, logic)
        ap.tr, ap.ca = tr, ca
        ap.easy_init('valuation')

    def find_viability(ap):
        try_via = ap.tr.find_viability()
        ap.logic.update_ap(ap.key, try_via, ap.uniq_id)
        if cond_via==EVAL_F:
            return ap.GETVIA( ap.ca.find_viability() )
        return ap.VIABLE()
    def implement(ap):
        if ap.logic.view(ap.key, ap.uniq_id)==EVAL_T: ap.tr.implement()
        else: ap.ca.implement() # if implemented, one of the two succeeded.

# Tautologies. Useful for representing variables. Provide str X: state key.
# View() is a shortcut for isTrue(), which simply evaluates the expression
# at runtime; Note that View also needs its structure in order to stay dynamic.
class View(ActionPicker):
    def __init__(ap, gm, logic, X):
        ActionPicker.__init__(ap, gm, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): return ap.GETTRUTH(ap.logic.view(ap.X))
    def reset(ap):  action.viability = EVAL_U
class isTrue(ActionPicker): # Is only evaulated once!
    def __init__(ap, gm, logic, X):
        ActionPicker.__init__(ap, gm, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): return ap.GETTRUTH(ap.X)
    def reset(ap):  action.viability = EVAL_U
class nonempty(ActionPicker): # True is list is not all 0/False/EVAL_F
    def __init__(ap, gm, logic, X):
        ActionPicker.__init__(ap, gm, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): 
        return ap.GETVIA(sum(ap.logic.view(X))>0)
    def reset(ap): action.viability = EVAL_U


'''     Pokemon logic APs               '''
# wasCaught: query if the pokemon was caught; execute pkmn removal from scene.
class wasCaughtProcessing(ActionPicker):
    def __init__(ap, gm, logic):
        ActionPicker.__init__(ap, gm, logic)
        ap.write_state_access = False # no update; read-only @ State 
        ap.key = 'was catch completed'
    def find_viability(ap): 
        return { True: ap.VIABLE(), False: ap.INVIABLE() }\
                    [ap.logic.view(ap.key)]
    def implement(ap): 
        pass # set image to white and kill self
    def reset(ap):  action.viability = EVAL_U

# wander: pick a random valid direction and move there.
class wander(ActionPicker):
    def __init__(ap, gm, logic):
        ActionPicker.__init__(ap, gm, logic)
        ap.card_dirs = logic.view('available motions')
        ap.chooser = PickRand(ap.card_dirs)
    def find_viability(ap): return ap.GETVIA(ap.chooser) 
    def implement(ap): ap.chooser.implement()
    def reset(ap):  action.viability = EVAL_U


class BasicPkmnActionPicker(ActionPicker):
    def __init__(ap, gm, logic):
        ActionPicker.__init__(ap, gm, logic)
        ap.write_state_access = True
        ap.root = Priority(ap.gm, ap.logic [ \
                wasCaughtProcessing(ap.gm, ap.logic) ,\
                # is being caught,
                # use attack move (a big AP itself),
                wander(ap.gm, ap.logic)
                ] )
    def find_viability(ap): return ap.GETVIA(ap.root)
    def implement(ap): ap.root.implement()
    def reset(ap): action.viability = EVAL_U





#--------------


class PushDown(ActionPicker):
    def __init__(ap, gm, logic, dname):
        ap.write_state_access = True
        ap.motion = logic.view('available motions')[dname]
    def find_viability(ap):
        motion_reqs = ap.logic.view('curr move vec')
        if not motion_reqs[ap.motion.index]==1:
            logic.pop_PDA('player motion pda', ap.motion.index)
            return ap.INVIABLE() # not requested
        cur_ppos = ap.logic.view('ppos')
        req_ppos = addvec(cur_ppos, logic.plyr_steps(ap.motion.posvec) )
        req_tpos = logic.pTOt(req_ppos)
        if ap.logic.view('tpos')==req_ppos:
            return ap.VIABLE() # Same tile: viable.
        print ap.logic.access_sensor('tile obstr').sense(qpos, 'plyr')
        return




class PlayerMotion(ActionPicker):
    def __init__(ap, gm, logic):
        ActionPicker.__init__(ap, gm, logic)
        g,l = gm,logic
        ap.root = Sequential(g,l, [PushDown(g,l,'u')])
#        ap.root = \
#           Sequential(g,l, \
#             TryCatch(g,l, \
#                Both([PickRand( 
#                        [PushDown(g,l,'u'), PushDown(g,l,'r'),\
#                         PushDown(g,l,'d'), PushDown(g,l,'l')]), 
#                        ]))
#                      CycleUp(g,l)]),\
#                Stand(g,l)),\
#             orderAction(g,l),\
#             setNextPlayerImage(g,l) )
#            
    def find_viability(ap): return ap.GETVIA(ap.root)
    def implement(ap): ap.root.implement()
    def reset(ap): action.viability = EVAL_U

def ThrowPokeball(x,y): pass            


class BasicPlayerActionPicker(ActionPicker): 
    # directly-used subclasses inherit from Entity.
    def __init__(ap, gm, logic):
        ActionPicker.__init__(ap, gm, logic)
        ap.write_state_access = True
        ap.logic.update_ap('last move', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('heading', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('cycle', EVAL_INIT, ap.uniq_id)

        l,g = ap.logic,ap.gm
#        ap.root = Sequential(g,l, \
#            Cond(g,l, All(g,l,[View(g,l,'isPlayerActionable'), 
#                               nonempty('triggered actions')],\
#                          ThrowPokeball(g,l)),\
#            PlayerMotion(g,l)))
        ap.root = Sequential(g,l, [View(g,l,'isPlayerActionable')])

    def reset(ap): 
        ap.viability = EVAL_U

    def find_viability(ap): 
        if not ap.viability == EVAL_U: raise Exception("Please call reset!")
        return ap.root.find_viability()


#        ap.logic.notify('curr move', choice)
#
#        if choice.null and prev_choice.null: # Continue stopped.
#            ap.image_cycler = 0
#            ap.choice = prev_choice
#        elif choice.null and not prev_choice.null: # Just stopped.
#            ap.image_cycler = 0
#            ap.choice = choice
#        elif not choice.null and prev_choice.null: 
#            ap.image_cycler += 0; ap.image_cycler = ap.image_cycler % 3
#            ap.choice = choice
#        elif not choice.null and choice.same(prev_choice):
#            ap.image_cycler += 0; ap.image_cycler = ap.image_cycler % 3
#            ap.choice = choice
#        elif not choice.null and not choice.same(prev_choice):
#            ap.image_cycler = 0
#            ap.choice = choice
#        if ap.choice.same(MotionNull()): return ap.INVIABLE()
#        return ap.VIABLE()
#
#    def _get_valid_input_motions(ap):
#        moves = ap.logic.view('curr move')
#        if sum(moves)==0: return MotionStatic()
#        curpos = ap.gm._t_to_p(ap.logic.view('tpos'))
#        valid_attempts = []
#        if not ap.logic.has_sensor('tile obstr'):  return ap.INVIABLE()
#        for act in ap.active_actions:
#            if act.index<0:  continue
#            qpos = floorvec(divvec(addvec(curpos, ap.logic.plyr_steps(act.dvec)), \
#                    ap.gm.tile_size))
#            print act.name, ap.gm._p_to_t(curpos), qpos, ap.logic.plyr_steps(\
#                    act.dvec), act.dvec, qpos
#            if moves[act.index]==1 and (ap.gm._p_to_t(curpos)==qpos or \
#                    not ap.logic.access_sensor('tile obstr').sense(qpos, 'plyr')):
#                valid_attempts.append(act)
#        if len(valid_attempts)==0:  return MotionStatic()
#        if len(valid_attempts)==1:  return valid_attempts[0]
#        return random.choice(valid_attempts)
#
#    def implement(ap): 
#        if not ap.viability==EVAL_T: raise Exception("implement is not trusted.")
#        motion = ap.choice
#        which_img = 3 * ap.choice.index + ap.image_cycler
#        motion.link_to_gent(ap.logic.agent)
#        motion.unit_move = ap.logic.plyr_steps((1,1,0,0))
#        motion.implement()
#        ap.logic.notify('prev move', ap.choice)
#        ap.logic.notify('curr move', ap.choice)
#        ap.logic.notify('image', which_img)
#
#    def get_which_action_chosen(ap): return ap.choice
#
#    def reset(ap):
#        if not ap.viability in [EVAL_T, EVAL_F, EVAL_INIT]: 
#            raise Exception("I've already been reset!", WHICH_EVAL[ap.viability])
#        ap.viability = EVAL_U
##        ap.valid_attempts=None
#        ap.choice = MotionNull()
#        for sub_ap in ap.constituent_APs: sub_ap.reset()
#
#
#





class State(Entity): # i do not write, so no need to have logic
    def __init__(st, gm, belt=None):
        Entity.__init__(st, gm)
        st.gm = gm
        st.s_env, st.s_ap = {}, {} # environment/internal state, ActionPickers'
        if belt: st.init_belt(belt)

#    def init_belt(st, init_belt): st._s['belt'] = init_belt
    def _update(st, k, v=None, who=None): 
        if who==None: 
            d = st.s_env
        else:           
            if not who in st.s_ap: 
                st.s_ap[who] = {}
            d = st.s_ap[who]
        if len(k)==2 and v==None:   d[k[0]]=k[1]
        else:                       d[k] = v
    def update_ap(st, key, val=None, who=None):
        if who==None: raise Exception()
        st._update(key, val, who)
    def update_env(st, a, b=None):
        st._update(a, b)
    def view_env(st, what): return st.s_env[what]
    def view_ap(st, what, who): 
        if not who.write_state_access==True: 
            raise Exception('State writing access not permitted.')
        return st.s_ap[who][what]

    def setup_fields(st, what):
        st.s_env['tilesize'] = st.gm.tile_size
        if what=='plyr': st.setup_plyr_fields()
        if what=='pkmn': st.setup_basic_pkmn_fields()

    def setup_plyr_fields(st):
        st.s_env['image']      = -1
        st.s_env['available']  = True
        st.s_env['tpos']       = NULL_POSITION
        st.s_env['ppos']       = NULL_POSITION
        st.s_env['num moves']  = 4
        st.s_env['isPlayerActionable'] = None
        st.s_env['available motions'] = { 'u':MotionUp(st.gm),\
                    'd':MotionDown(st.gm), 'l':MotionLeft(st.gm), \
                    'r':MotionRight(st.gm), '-':MotionStatic(st.gm) }
        st.s_env['player motion pda'] = [ MotionStatic(st.gm) ]

    def setup_basic_pkmn_fields(st):
        st.s_env['is being caught'] = False
        st.s_env['available motions'] = [MotionUp(st.gm), MotionDown(st.gm), \
                MotionLeft(st.gm), MotionRight(st.gm), MotionStatic(st.gm) ]


class Logic(Entity):
    ''' Logic: the unique logic root of an agent that maintains an active
        internal state and belts for the agent. Simple entities like most Moves 
        I organize ActionPickers and field messages to update State. 
        Belt should be fully initialized; changes now must be fielded through me.
        '''
    def __init__(logic, gm, agent, belt, init_belt=None):
        Entity.__init__(logic, gm)
        logic._state = State(gm)
        logic.agent = agent
        logic.belt = belt
        logic.message_queue = []
        if agent.string_sub_class=='plyr': 
            logic._state.setup_fields('plyr')
            logic.root_ap = BasicPlayerActionPicker(gm, logic)
        else:
            raise Exception('not impl yet')
        
        logic.reload()

    def view(logic, what, who=None): 
        return logic._state.view_ap(what, who) if who \
                        else logic._state.view_env(what)
    # Notify: primary inbox method!
    def notify(logic, whatCol, whatVal):
        logic.message_queue.append( (whatCol, whatVal) )
    def get_resource(logic, database, resourceName):
        if database=='plyr img':
            return logic.gm.imgs['player sprite '+str(resourceName)]
    def has_sensor(logic, what_sensor):
        return logic.belt.Sensors.has_key(what_sensor)
    def access_sensor(logic, what_sensor):
        return logic.belt.Sensors[what_sensor]
    def plyr_steps(logic, dvec): 
        if not logic.agent.string_sub_class=='plyr': 
            raise Exception('notice: not plyr object')
        return ( dvec[X] * logic.gm.smoothing * logic.agent.stepsize_x, \
                 dvec[Y] * logic.gm.smoothing * logic.agent.stepsize_y)
    def pop_PDA(logic, which_pda, element):
        try:
            tmp = [s for s in st.s_env if not s.index==element]
        except: raise Exception()
        st.s_env[which_pda] = tmp
    def tTOp(logic, X): 
        try: return multvec(X, logic.gm.tile_size, int)
        except: raise Exception(X)
    def pTOt(logic, X): 
        try: return multvec(X, logic.gm.tile_size, '//')
        except: raise Exception(X)
    
    def update_ap(logic, key, value, who):
        logic._state.update_ap(key, value, who)

    def update(logic):
        # Read and process messages:
        while len(logic.message_queue)>0:
            msg = logic.message_queue.pop(0)
            logic._state.update_ext(msg[0],msg[1])

        # Notify actions and ActionPickers that they can reset for next frame:
        logic.root_ap.reset()

        if logic.agent.string_sub_class=='plyr': 
            # update _state for new frame for PLAYER:
#            logic._state.update_env('last move', logic._state.view_env('curr move'))
            put = logic._state.update_env
            put('ppos', logic.agent.get_center())
            put('tpos', logic.agent.get_position())
            put('curr move vec', logic.gm.events[:4])
            put('triggered actions', logic.gm.events[4:])
            put('isPlayerActionable', logic.agent.is_plyr_actionable())


    def decide(logic):
        # Player workflow. Query triggers, then move regardless.

        logic.root_ap.find_viability()
#        if any(logic._state.view_ap('triggered actions')):
#            pass
#        attmptMove = logic.root_ap.find_viability()
#        if attmptMove==EVAL_T:
#            #logic.chosen_action = logic.root_ap.get_which_action_chosen()
#            logic.chosen_action = logic.root_ap
        
   # def enact(logic): logic.chosen_action.implement() 
    def enact(logic): pass#logic.chosen_action.implement() 

    def reload(logic): # Call this after action(s) is complete to prepare for next frame.
        # This is not normally called directly. ?
        logic.root_ap.reset()



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
        Pickers to utilitize. '''
    def __init__(belt, gm, whose_belt, sp_init=None): 
        Entity.__init__(belt, gm)
        if not isinstance(whose_belt, Agent): 
            raise Exception(type(whose_belt))
        belt.whose_belt = whose_belt
        belt.gm = gm
        if sp_init=='basic player':
            tmp__actions = {'u':MotionUp, 'l':MotionLeft, \
                            'd':MotionDown, 'r':MotionRight, \
                            '-':MotionStatic, \
                            }
            belt.Actions = {k:v(gm) for k,v in tmp__actions.items()}
            belt.Items = ['pokeball-lvl-1']*4
            belt.Pkmn = []
            tmp__sensors = {'tile obstr':TileObstrSensor}
            belt.Sensors =  {k:v(gm) for k,v in tmp__sensors.items()}
        elif sp_init=='pokeball catch':
            belt.Actions = {'anim':AnimLinear, 'c':TryToCatch, 'add':AddPkmn}
            belt.Pkmn, belt.Items = None, None
            belt.Sensors = [WildEntSensor]
        else: raise Exception("an easy, nbd exception but please implement.")


    def add_pkmn(belt, pkmn):
        belt.pkmn.append(stored_pkmn(belt.gm, pkmn))
            
