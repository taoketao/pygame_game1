from utilities import *
from abstractEntities import *
from abstractActions import *
from sensors import *
from playerActions import *
from pokemonActions import *
from motionActions import *
from attackActions import *
import agents as agents_module
import leaves as leaves_module
import moves as moves_module


'''             Belt               '''
        
''' Belt: Actions and Sensors are lists of available functions for Action
    Pickers to utilitize.   Core Attributes that all Belts have:
    --Actions: the available actions that the Agent can decide amongst. The
        decision process or what the actions represent are not relevant.
    --Moves: 'scripts' (that are actually Actions) of various fixed action
        patterns. Unlike Action prefabs, Move prefabs often take variable 
        arguments and require a kill function.
    --Sensors: the various tool this entity has to understand its environment.
        Encapsulates both trivial behavior handling as well as a behavior-
        -altering effect: with more Senses, different things can be done
        with its knowledge!
    --Dependent (graphical) objects: otherwise independent entities that
        require 
    --Spawns: short-lived instantiations of Move scripts. These are the 
        closest to fully breaking a connection to this belt's associated
        logic, but are kept mainly for organization purposes. 


    Auxiliary Attributes that only some Belts have:
    --Items: The user-facing multiset of consumable items.
    --Pkmn: The list of pokemon this character or object 'owns'.

    future: add AnimationScript? Versioning? Geomapping? Zoning? '''



#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

class Belt(Entity):
    ''' Belt: a fancy dynamic container for an agent. Belts are designed to
        interact closely with a Logic, a State, an Agent, and the Game Manager
        to implement and house user-facing objects. cp State, houses data '''
    def __init__(belt, gm, agent, **options): 
        Entity.__init__(belt, gm)
        if not isinstance(agent, VisualStepAgent): 
            raise Exception(type(agent))
        belt.agent = agent
        belt.gm = gm

        for container_init in ['Dependents', 'Actions', 'Pkmn', 'Items', \
                'Sensors', 'Spawns', 'Moves']:
            setattr(belt, container_init, {}) # init as empty

        belt.Sensors.update({True: { 'ppos':GetPPosSensor, 'tpos':GetTPosSensor, \
                                'smoothing':GetFrameSmoothingSensor ,\
                                'next reserved':GetFrameSmoothingSensor ,\
                                'tile obstr':TileObstrSensor, \
                                'get who at tile':GetWhoAtTIDSensor ,\
                                'unit step':GetCurUnitStepSensor }, \
                            False: {} }[options.get('std_sensors',True)] )
        belt.Actions.update({True: {'u':MotionUp,       'd':MotionDown,   \
                                    'l':MotionLeft,     'r':MotionRight,  \
                                    '-':MotionStatic }, False:{}  \
                            } [options.get('std_motions',True)])
        which_init = options.get('sp_init', agent.team+' '+agent.species)
        if   which_init=='--plyr-- plyr': belt._init_basic_player()
        elif which_init=='target': pass
        elif which_init=='--wild-- pkmn': belt._init_pkmn(options);
        elif which_init=='--plyr-- pkmn': belt._init_pkmn(options);
        else: raise Exception("an easy, nbd exception but please implement.",options)
        belt.which_init=which_init

    def _init_basic_player(belt):
        belt.Items.update({i:'pokeball-lvl-1' for i in range(4)})
        belt.Sensors.update({'mousepos':GetMouseTIDSensor})
        belt.Moves.update({'cast pokeball': moves_module.ThrowPokeballMove})
        belt.Dependents.update({'highlighter': \
                leaves_module.PlayerHighlighter(belt.gm, belt.agent.uniq_id)} )

    def _init_pkmn(belt, options):
        belt.Actions.update({'A':DoAttack})
        tmp=options['hbcolor']
        for i,c in enumerate([tmp,'y']): # hacky sanity checks:
            options['hbcolor']=c
            options['offset']=i
            hb = leaves_module.StatusBar(belt.gm, belt.agent, metric='health', 
                    **options)
            if i==1: hb.update_metric(random.choice(range(-10,35)), 'absolute')
            hb.master=False
            belt.Dependents.update({ 'healthbar_'+c:hb })


    def spawn_new(belt, what_to_spawn, kind, **options):
        # Take a prefab from Moves and initialize it into Spawns.
        assert(kind=='move') # stub
        prefab = belt.Moves[what_to_spawn] # typically an action...
        new_ent = prefab(belt.gm, **options)
        belt.Spawns.update({what_to_spawn: new_ent})

        return new_ent
