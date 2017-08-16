import abc
from abstractEntities import *
from utilities import *



'''        Action and ActionPicker: base classes and exemplars             '''

''' Abstract Action that encodes an action made by a pokemon, attack, npc, etc.
    Actions have one of several values that can be returned on query, which
    tell if an action is viable, for an action picker: 
        T: this action is viable and ready     F: this action is not viable
        U: this action has insufficient information to decide viability.
    The find_viability method will return T or F based on available Sensors
    and the state. implement() performs the action and requires a T viability. '''

#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

class Action(Entity):
    def __init__(action, gm):
        Entity.__init__(action, gm)
        action.species = 'action'
        # action.viability: the core reason for this implementation
        action.viability = EVAL_INIT

    # Methods: get_viability(): T/F/U/..., find_viability() T/F, implement()
    def get_viability(action): return action.viability
    @abc.abstractmethod
    def find_viability(action): raise Exception("Must implement me!",action)
    @abc.abstractmethod
    def implement(action): raise Exception("Must implement me!",action)
    @abc.abstractmethod
    def reset(action): raise Exception("Must implement me!",action)

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
    def COPYEVAL(action, val): action.viability=val; return val

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

# simple actions: 
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

