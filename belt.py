from utilities import *
from abstractEntities import *
from abstractActions import *
from sensors import *
from playerActions import *
from pokemonActions import *
from motionActions import *
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
        belt.spawn_itr=0

        for container_init in [\
                'Actions',      #   Initialized Action(Picker) objects
                'Dependents',   #   Objects who depend completely on this
                'Items',        #   user-facing; currently ununsed
                'Moves',        #   Prefab init functions of various spawnables
                'Pkmn',         #   Player only so far: stored pokemon info
                'Sensors',      #   internal sensors for the environment
                'Spawns',       #   a container for any temp spawned instances
                ]:
            setattr(belt, container_init, {}) # init as empty

        belt.Sensors.update({True: { 'ppos':GetPPosSensor, 'tpos':GetTPosSensor, \
                                'smoothing':GetFrameSmoothingSensor ,\
                                'next reserved':GetFrameSmoothingSensor ,\
                                'tile obstr':TileObstrSensor, \
#                                'tile occ':TileOccupSensor, \
                                'tile occs':TileOccsSensor, \
#                                'get who at tile':GetWhoAtTIDSensor ,\
                                'get agents at tile':GetAgentsAtTileSensor ,\
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
        elif which_init=='pkmn_basic_init': belt._init_pkmn(options);
        else: raise Exception("an easy exception: please implement.",options)
        belt.which_init=which_init

    def _init_basic_player(belt):
        belt.Items.update({i:'pokeball-lvl-1' for i in range(4)})
        belt.Sensors.update({'mousepos':GetMouseTIDSensor})
        belt.Moves.update({'cast pokeball': moves_module.CatchPokeballMove})
        belt.Moves.update({'throw pokeball': moves_module.ThrowPokeballMove})
        belt.Dependents.update({'highlighter': \
                leaves_module.PlayerHighlighter(belt.gm, belt.agent.uniq_id)} )
        belt.pkmn_counter=0
        s='initialized_pkmn'
        belt.Pkmn.update({s:{ 'pokedex':1,\
                    'max_health':30, 'cur_health':25,\
                    'health_max':30, 'health_cur':25}})


    def _init_pkmn(belt, options):
        belt.Moves.update({'tackle':moves_module.Tackle})
        options['offset']=0
        hb = leaves_module.StatusBar(belt.gm, belt.agent, metric='health', 
                **options)
        belt.Dependents.update({ 'healthbar':hb })
        belt.health = belt.Dependents['healthbar']
        if belt.agent.team=='--wild--':
            hb.master=False
            options['caughtness']=150
            options['vizscale']=5
            options['hbcolor']='w'
            options['offset']=1
            belt.Dependents.update({ 'caughtbar': leaves_module.StatusBar(\
                    belt.gm, belt.agent, metric='caughtness', \
                    orientation='horiz', **options) })
        elif belt.agent.team=='--plyr--':
            pass
        else: raise Exception(belt.agent.team,'team for pkmn is not recognized/')


    def spawn_new(belt, what_to_spawn, kind, **options):
        # Take a prefab activity from Moves and initialize it into Spawns.
        assert(kind=='move') # stub
        if what_to_spawn in ['cast pokeball', 'throw pokeball', 'tackle']:
            prefab = belt.Moves[what_to_spawn]
            new_ent = prefab(belt.gm, **options)
            belt.Spawns.update({what_to_spawn+':'+str(belt.spawn_itr): new_ent})
            belt.spawn_itr+=1
            return new_ent
        # Take data from options and create a new Agent
        elif what_to_spawn in ['create pokemon']:
            raise Exception("This doesn't need the belt!")
            if not 'which_slot' in options.keys(): return None
            options.update(belt.Pkmn[options['which_slot']])
            name = 'PkmnPlyr_'+str(belt.pkmn_counter); belt.pkmn_counter+=1
            chealth, mhealth = options.get('health_cur_max', \
                    (options['health_cur'], options['health_max']) )
            if 'init_ppos' in options.keys():
                options['init_tloc'] = divvec(options['init_ppos'], belt.gm.ts())
            belt.gm.notify_new_spawn('Agents', name, agents_module.AIAgent, \
                    uniq_name=name, team=belt.agent.team, \
                    init_tloc=options['init_tloc'], pokedex=options['pokedex'],\
                    max_health=mhealth, cur_health=chealth, sp_init=\
                    'pkmn_basic_init')
        else: raise Exception('unrecognozed', what_to_spawn)
 

