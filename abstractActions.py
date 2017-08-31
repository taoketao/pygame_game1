import abc
import abstractEntities as AE
from utilities import *



'''        Action and ActionPicker: base classes and exemplars             '''

''' Abstract Action that encodes an action made by a pokemon, attack, npc, etc.
    Actions have one of several values that can be returned on query, which
    tell if an action is viable, for an action picker: 
        T: this action is viable and ready     F: this action is not viable
        U: this action has insufficient information to decide viability.
        E/I: Runtime error and Init error.

    Paradigm:
 1. RESET: Reset the Action. These can be done concurrently for all actions.
        Do this when doing a new frame. Usually, this amounts to resetting all
        evaluations to U for unevaluated.
 2. FIND_VIABILITY: using the maintained internal state (with either a dedicated
        State objet or simple class attributes) and sensors that query the world 
        environment, determine an action to take. This can be thought of as an
        abstract input handler and behavior module. Each action is evaluated
        to T, F, or U for unreached; T actions are implemented; and if none 
        evaluate to T, then there are no Us and F is determined, indicating a
        failure for the action.
 3. IMPLEMENT: this actually does the chosen T actions. If no actions are eval-
        -uated as T, a system failure is raised.


    This module: this implements the very simplest actions and core class supers.

    '''

#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------


class Action(AE.Entity):
    ''' Action: the base object which all Actions should inherit. '''
    def __init__(action, gm):
        AE.Entity.__init__(action, gm)
        action.species = 'action'
        # action.viability: the core reason for this implementation
        action.viability = EVAL_INIT

    # Query the action's viability.
    def get_viability(action): return action.viability
    # find viability: STUB!
    @abc.abstractmethod
    def find_viability(action): raise Exception("Must implement me!",action)
    # find viability: STUB!
    @abc.abstractmethod
    def implement(action): raise Exception("Must implement me!",action)
    # find viability: STUB!
    @abc.abstractmethod
    def reset(action): raise Exception("Must implement me!",action)

    # helpers:
    def INVIABLE(action): 
        ''' INVIABLE: Determine this action as EVAL_F and return EVAL_F. '''
        action.viability=EVAL_F; return EVAL_F
    def VIABLE(action): 
        ''' VIABLE: Determine this action as EVAL_T and return EVAL_T. '''
        action.viability=EVAL_T; return EVAL_T
    def GETTRUTH(action, query): 
        ''' GETTRUTH(query): Determine EVAL_T and return EVAL_T only if
            query==true. '''
        return (action.VIABLE() if query==True else action.INVIABLE())
    def GETVIA(action, query): 
        ''' GETVIA(query): Determine EVAL_T and return EVAL_T only if 
            query.find_viability()==EVAL_T. '''
        return (action.VIABLE() if query.find_viability()==EVAL_T \
                else action.INVIABLE())
    def Verify(action, query): 
        ''' Verify(query): if not query.viability==EVAL_T, raise system error.'''
        if not action.GETVIA(query)==EVAL_T:
            raise Exception(query, WHICH_EVAL[query.viability])
        return action.viability
    def VIABILITY_ERROR(action):
        ''' VIABILITY_ERROR: Determine this action as & return EVAL_ERR.  '''
        action.viability = EVAL_ERR; return EVAL_ERR
    def COPYEVAL(action, query): 
        ''' COPYEVAL(query): Copy value irrespectively and pass it up.  '''
        action.viability=query; return query

class ActionPicker(Action):
    ''' ActionPicker: a more practical version of Action that takes Logic 
        and everything that that implies. '''
    def __init__(ap, logic):
        Action.__init__(ap, logic.gm)
        ap.logic=logic
        ap.components = []
        ap.key = 'stub key'
        ap.write_state_access = False # by default
    def easy_init(ap, k): 
        ''' easy_init is suggested when the ActionPicker's determination can
        be encapsulated with a single field that is not needed elsewhere. '''
        ap.write_state_access = True
        ap.key = k
        ap.logic.update_ap(ap.key, EVAL_INIT, ap.uniq_id)
    def reset(ap): 
        ''' reset, by default, just resets this viability. '''
        ap.viability = EVAL_U
        for c in ap.components: c.reset()

# simple actions: 
class View(ActionPicker):
    ''' View(X): a simple action that responds to the logic's field X. '''
    def __init__(ap, logic, X):
        ActionPicker.__init__(ap, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): return ap.GETTRUTH(ap.logic.view(ap.X))
    def reset(ap):  ap.viability = EVAL_U;

class isTrue(ActionPicker): # Only changes if X changes via reference!
    ''' deprecated?'''
    def __init__(ap, logic, X):
        ActionPicker.__init__(ap, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): return ap.GETTRUTH(ap.X)
    def reset(ap):  ap.viability = EVAL_U

class nonEmpty(ActionPicker): # Query an element in the State..
    ''' deprecated?'''
    def __init__(ap, logic, X):
        ActionPicker.__init__(ap, logic)
        ap.X, ap.write_state_access = X, False
    def find_viability(ap): 
        return ap.GETVIA(sum(ap.logic.view(X))>0)
    def reset(ap): ap.viability = EVAL_U
           
class Delay(ActionPicker): 
    # As used in Priority, returns EVAL_T to block if delay has not finished.
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
    def find_viability(ap):
        return (ap.VIABLE() if ap.logic.view('delay')>=0 else ap.INVIABLE())
    def implement(ap): assert(ap.viability==EVAL_T)
    def reset(ap): ap.viability=EVAL_U
