from utilities import *
from abstractEntities import *
from abstractActions import *
from sensors import *
from playerActions import *
from pokemonActions import *
from motionActions import *
from attackActions import *
import agents as agents_module


'''             Belt               '''
        
''' Belt: Actions and Sensors are lists of available functions for Action
    Pickers to utilitize.   Core Attributes that all Belts have:
    --Actions: the available actions that the Agent can decide amongst. The
        decision process or what the actions represent are not relevant.
    --Sensors: the various tool this entity has to understand its environment.
        Encapsulates both trivial behavior handling as well as a behavior-
        -altering effect: with more Senses, different things can be done
        with its knowledge!
    --Dependent (graphical) objects: entities that ought to be updated with
        parameters decided with logic.Update calls.
    Auxiliarry Attributes that only some Belts have:
    --Items: The user-facing multiset of consumable items.
    --Pkmn: The list of pokemon this character or object 'owns'.

    future: add AnimationScript? Versioning? Geomapping? Zoning? '''



#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

class Belt(Entity):
    def __init__(belt, gm, agent, **options): 
        Entity.__init__(belt, gm)
        if not isinstance(agent, VisualStepAgent): 
            raise Exception(type(agent))
        belt.agent = agent
        belt.gm = gm

        for container_init in ['Dependents', 'Actions', 'Pkmn', 'Items', 'Sensors']:
            setattr(belt, container_init, {})

        belt.Sensors.update({True: { 'ppos':GetPPosSensor, 'tpos':GetTPosSensor, \
                                'smoothing':GetFrameSmoothingSensor ,\
                                'next reserved':GetFrameSmoothingSensor ,\
                                'tile obstr':TileObstrSensor, \
                                'unit step':GetCurUnitStepSensor }, \
                            False: {} }[options.get('std_sensors',True)] )
        belt.Actions.update({True: {'u':MotionUp,       'd':MotionDown,   \
                                    'l':MotionLeft,     'r':MotionRight,  \
                                    '-':MotionStatic }, False:{}  \
                            } [options.get('std_motions',True)])
        print 'test'
        which_init = options.get('sp_init', agent.team+' '+agent.species)
        if   which_init=='--plyr-- plyr': belt._init_basic_player()
        elif which_init=='target': pass
        elif which_init=='--wild-- pkmn': belt._init_pkmn(options);
        elif which_init=='--plyr-- pkmn': belt._init_pkmn(options);
        else: raise Exception("an easy, nbd exception but please implement.",options)
        belt.which_init=which_init

    def _init_basic_player(belt):
        belt.Items.update({i:'pokeball-lvl-1' for i in range(4)})

    def setup_belt(belt, class_type, **options):
        if class_type==agents_module.Player:        \
            belt.Dependents.update(                 \
                    {'highlighter': agents_module.PlayerHighlighter(belt.gm)} )
#        elif class_type==agents_module.AIAgent:     \
#            belt.Dependents.update(                 \
#                    {'health': agents_module.StatusBar(belt.gm, belt.agent, \
#                    metric='health', **options)} )

#    elif options.get('sp_init')=='pokeball catch':
#        belt.Actions = {'anim':AnimLinear, 'c':TryToCatch, 'add':AddPkmn}
#        belt.Sensors = [WildEntSensor]
    def _init_pkmn(belt, options):
        belt.Actions.update({'A':DoAttack})
        hb = agents_module.StatusBar(belt.gm, belt.agent, metric='health', **options)
        belt.Dependents.update({ 'health':hb })
        belt.gm.Effects.update({ str(belt.agent.uniq_id)+'_health':hb })

#        hb = agents_module.StatusBar(
#        belt.Dependents.update({ 'health':hb })
#        belt.gm.Effects.update({ str(agent.uniq_id)+'_health':hb })
#
    def _init_plyr_pkmn(belt): pass 
    def _init_wild_pkmn(belt): pass
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


           
