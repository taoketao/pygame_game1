from utilities import *
from abstractEntities import *
from abstractActions import *
from sensors import *
from playerActions import *
from pokemonActions import *
from motionActions import *
from attackActions import *


'''             Belt               '''
        
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



#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

class Belt(Entity):
    def __init__(belt, gm, whose_belt, sp_init=None, std_sensor_suite=True, options=None): 
        Entity.__init__(belt, gm)
        if not isinstance(whose_belt, VisualStepAgent): 
            raise Exception(type(whose_belt))
        belt.whose_belt = whose_belt
        belt.gm = gm

        belt.Sensors = {True: { 'ppos':GetPPosSensor, 'tpos':GetTPosSensor, \
                                'smoothing':GetFrameSmoothingSensor ,\
                                'tile obstr':TileObstrSensor, \
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
            belt.Sensors.update({ })
        elif sp_init=='pokeball catch':
            belt.Actions = {'anim':AnimLinear, 'c':TryToCatch, 'add':AddPkmn}
            belt.Sensors = [WildEntSensor]
        elif sp_init=='target':
            belt.Actions = {}
            belt.Sensors, belt.Pkmn, belt.Items = None, None, None
        elif sp_init=='wild pokemon':
            belt.Actions ={ 'u':MotionUp,     \
                            'd':MotionDown,   \
                            'l':MotionLeft,   \
                            'r':MotionRight,  \
                            '-':MotionStatic,  \
                            'A':DoAttack\
                            }
            belt.Sensors.update({ })
            belt.Pkmn, belt.Items = None, None
        else: raise Exception("an easy, nbd exception but please implement.")

    def add_pkmn(belt, pkmn):
        belt.Pkmn.append(stored_pkmn(belt.gm, pkmn))

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


           
