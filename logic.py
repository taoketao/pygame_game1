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
        print '\t',occups, tileinfo, blck, tid
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
class Action(object):
    def __init__(action):
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

class MotionAction(Action):
    def __init__(action):
        Action.__init__(action)
        action.gent = None
        action.unit_move = None
    def find_viability(action):
        cur_tpos = action.logic.view('tpos')
        querypos = addvec(action.posvec, cur_tpos)
        if action.logic.agent.string_sub_class=='plyr':
            if action.logic.access_sensor('tile obstr info', querypos)==True:
                action.viability = EVAL_F
            else:
                action.viability = EVAL_T

    def link_to_gent(action, gent, unit_move=None): action.gent = gent

    def implement(action):
        if action.index<0: return
        if action.gent: action.gent.move_tpos(action.posvec)
    def same(action, targ): return action.index==targ.index # etc

class MotionUp(MotionAction):
    def __init__(action):
        MotionAction.__init__(action)
        action.dvec = [1,0,0,0];      action.posvec = (0,-1);
        action.name = 'u';            action.index = 0
        action.null=False
class MotionLeft(MotionAction):
    def __init__(action):
        MotionAction.__init__(action)
        action.dvec = [0,1,0,0];      action.posvec = (-1,0);
        action.name = 'l';            action.index = 1
        action.null=False
class MotionDown(MotionAction):
    def __init__(action):
        MotionAction.__init__(action)
        action.dvec = [0,0,1,0];      action.posvec = (0,1);
        action.name = 'd';            action.index = 2
        action.null=False
class MotionRight(MotionAction):
    def __init__(action):
        MotionAction.__init__(action)
        action.dvec = [0,0,0,1];      action.posvec = (1,0);
        action.name = 'r';            action.index = 3
        action.null=False
class MotionStatic(MotionAction):
    def __init__(action):
        MotionAction.__init__(action)
        action.dvec = [0,0,0,0];      action.posvec = (0,0);
        action.name = '-';            action.index = -1
        action.null=True
class MotionNull(MotionAction):
    def __init__(action):
        MotionAction.__init__(action)
        action.dvec = None;         action.posvec = NULL_POSITION;
        action.name = '__x__';      action.index = -2
        action.null=True


class SetCycleImage(Action):
    def __init__(action):
        Action.__init__(action) # TODO
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
    def __init__(ap, logic):
        Action.__init__(ap)
        ap.logic=logic
        ap.constituent_APs = []


class BasicPlayerActionPicker(ActionPicker, Entity): 
    # directly-used subclasses inherit from Entity.
    def __init__(ap, gm, logic):
        ActionPicker.__init__(ap, logic)
        Entity.__init__(ap, gm)

        ap.has_state = True
#        ap.active_actions = {}
#        for k in ['u','l','r','d','-']: 
#            ap.active_actions[k]=belt.Actions[k]
        ap.active_actions = logic.view('available motions')
        ap.image_cycler=0
        ap.choice=MotionNull()
                                 
    def find_viability(ap): 
        if not ap.viability == EVAL_U: raise Exception("Please call reset!")
        choice = ap._get_valid_input_motions()
        prev_choice = ap.logic.view('last move')
        print choice.name, prev_choice.name
#        if not (choice.null and prev_choice.null):
        ap.logic.notify('curr move', choice)

        if choice.null and prev_choice.null: # Continue stopped.
            ap.image_cycler = 0
            ap.choice = prev_choice
        elif choice.null and not prev_choice.null: # Just stopped.
            ap.image_cycler = 0
            ap.choice = choice
        elif not choice.null and prev_choice.null: 
            ap.image_cycler += 0; ap.image_cycler = ap.image_cycler % 3
            ap.choice = choice
        elif not choice.null and choice.same(prev_choice):
            ap.image_cycler += 0; ap.image_cycler = ap.image_cycler % 3
            ap.choice = choice
        elif not choice.null and not choice.same(prev_choice):
            ap.image_cycler = 0
            ap.choice = choice
        if ap.choice.same(MotionNull()): return ap.INVIABLE()
        return ap.VIABLE()

    def _get_valid_input_motions(ap):
        moves = ap.logic.view('curr move')
        if sum(moves)==0: return MotionStatic()
        curpos = ap.gm._t_to_p(ap.logic.view('tpos'))
        valid_attempts = []
        if not ap.logic.has_sensor('tile obstr'):  return ap.INVIABLE()
        for act in ap.active_actions:
            if act.index<0:  continue
            qpos = floorvec(divvec(addvec(curpos, ap.logic.plyr_steps(act.dvec)), \
                    ap.gm.tile_size))
            print act.name, ap.gm._p_to_t(curpos), qpos, ap.logic.plyr_steps(\
                    act.dvec), act.dvec, qpos
            if moves[act.index]==1 and (ap.gm._p_to_t(curpos)==qpos or \
                    not ap.logic.access_sensor('tile obstr').sense(qpos, 'plyr')):
                valid_attempts.append(act)
        if len(valid_attempts)==0:  return MotionStatic()
        if len(valid_attempts)==1:  return valid_attempts[0]
        return random.choice(valid_attempts)

    def implement(ap): 
        if not ap.viability==EVAL_T: raise Exception("implement is not trusted.")
        motion = ap.choice
        which_img = 3 * ap.choice.index + ap.image_cycler
        motion.link_to_gent(ap.logic.agent)
        motion.unit_move = ap.logic.plyr_steps((1,1,0,0))
        motion.implement()
#        ap.logic.entity.image = ap.logic.get_resource('plyr img', which_img)
#        ap.entity.move_ppos(ap.logic.plyr_steps(ap.choice.dvec))
        ap.logic.notify('prev move', ap.choice)
        ap.logic.notify('curr move', ap.choice)
        ap.logic.notify('image', which_img)

    def get_which_action_chosen(ap): return ap.choice

    def reset(ap):
        if not ap.viability in [EVAL_T, EVAL_F, EVAL_INIT]: 
            raise Exception("I've already been reset!", WHICH_EVAL[ap.viability])
        ap.viability = EVAL_U
#        ap.valid_attempts=None
        ap.choice = MotionNull()
        for sub_ap in ap.constituent_APs: sub_ap.reset()



class State(Entity): # i do not write, so no need to have logic
    def __init__(st, gm, belt=None):
        Entity.__init__(st, gm)
        st.gm = gm
        st._s = {}
        if belt: st.init_belt(belt)

#    def init_belt(st, init_belt): st._s['belt'] = init_belt
    def update(st, a, b=None): 
        if b==None: 
            assert(len(a)==2);
            st._st[a[0]]=a[1]
        else:
            st._s[a] = b
    def copy_aFb(st, a, b): st._s[a] = st._s[b]
    def view(st, k): return st._s[k]
    def setup_fields(st, what):
        if what=='plyr': st.setup_plyr_fields()

    def setup_plyr_fields(st):
        st._s['last move']  = MotionNull()
        st._s['curr move']  = MotionDown()#MotionStatic()
        st._s['image']      = -1
        st._s['available']  = True
        st._s['tpos']       = NULL_POSITION
        st._s['num moves']  = 4
        st._s['available motions'] = [MotionUp(), MotionDown(), \
                MotionLeft(), MotionRight(), MotionStatic() ]


class Logic(Entity):
    ''' Logic: the unique logic root of an agent that maintains an active
        internal state and belts for the agent. Simple entities like most Moves 
        should lack an explicit Logic. 
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

    def view(logic, what): return logic._state.view(what)
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
    

    def update_self(logic):
        # Read and process messages:
        while len(logic.message_queue)>0:
            msg = logic.message_queue.pop(0)
            logic._state.update(msg[0],msg[1])
        # Notify actions and ActionPickers that they can reset for next frame:
        logic.root_ap.reset()
        if logic.agent.string_sub_class=='plyr': 
            # update _state for new frame for PLAYER:
            logic._state.copy_aFb('last move', 'curr move')
            logic._state.update('curr move', logic.gm.events[:4])
            logic._state.update('tpos', logic.agent.get_position())
            logic._state.update('triggered actions', logic.gm.events[4:])

    def decide(logic):
        # Player workflow. Query triggers, then move regardless.
        if any(logic._state.view('triggered actions')):
            pass
        attmptMove = logic.root_ap.find_viability()
        if attmptMove==EVAL_T:
            #logic.chosen_action = logic.root_ap.get_which_action_chosen()
            logic.chosen_action = logic.root_ap
        
   # def enact(logic): logic.chosen_action.implement() 
    def enact(logic): logic.chosen_action.implement() 




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
#                            's':PBallSend, 'c':PballCatch\
                            }
            belt.Actions = {k:v() for k,v in tmp__actions.items()}
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
            
