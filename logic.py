'''
Logic module for managing and handling interactive behavior of (AI) agents.

'''
import numpy as np
import pygame, random, sys

from utilities import *
from abstractEntities import *
from sensors import *
from playerActions import *
from pokemonActions import *
from otherActions import *
from compositeActions import *
import belt as belt_module
import state as state_module
import agents as agents_module
import messagehandler as messagehandler_module


#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''             Logic               '''

class Logic(Entity):
    ''' Logic: the unique logic root of an agent that maintains an active
        internal state and belts for the agent. Simple entities like most Moves 
        I organize ActionPickers and field messages to update State. 
        Belt should be fully initialized; changes now must be fielded through me.
    '''

    def __init__(logic, gm, agent, **options):
        ''' Initializer '''
        Entity.__init__(logic, gm)

#        print 'Logic init OPTIONS:', options
        agent.has_logic=True
        logic.IS_DEAD = False
        logic.agent = agent
        logic.belt = belt_module.Belt(gm, agent, **options)
        logic._state = state_module.State(gm, logic.belt)
        logic._state.setup_fields(agent.species, logic=logic, 
                            ppos=options['init_ppos'])
        logic.__action_lock = -1 # Not state: lock mechanism.

        logic.message_handler = messagehandler_module.MessageHandler(logic)
        
        if agent.species=='plyr': 
            logic.root_ap = BasicPlayerActionPicker(logic)
        elif agent.species=='target':
            logic.root_ap = MouseActionPicker(logic)
        elif agent.species=='pkmn':
            logic.root_ap = WildPkmnBehavior(logic)
        else: raise Exception('not impl yet')
        
        logic.root_ap.reset()

    '''
        Public Methods: 
        (cp Update/Decide/Implement with reset/find_viability/implement)   '''

#-- Interface method        __ Update __        Call before choosing actions 
    def Update(logic):
        if logic.IS_DEAD: 
            print 'I am dead!'
            logic._kill(); return

        logic.message_handler.handle_messages()

        # Wipe sensors and prime them
        logic.viability = EVAL_F

        # Rescan sensors:
        for snm,sensor in logic.belt.Sensors.items():
            sensor.rescan()
            if snm in ['tpos','ppos']: # Self-reference these.
                logic.get_sensor(snm).agent_id = logic.agent.uniq_id

        # Update interlocking global fields:
        put = logic._state.update_env
        put('next reserved', logic.view_sensor('tpos'))
        if logic.ViewActionLock()<0: # don't internally delay while animating
            put('delay',logic.view('delay')-logic.gm.dt*np.random.uniform(0.7,1.3))

        # Reset Actions and ActionPickers:
        for dep in logic.belt.Dependents.values(): dep.Reset()
        for move in logic.belt.Spawns.values():  move.reset()
        logic.root_ap.reset()

#-- Interface method        __ Decide __        Call for ALL before implementing
    def Decide(logic):      
        logic.viability = logic.root_ap.find_viability()
        
        removes = []
        for mv_keyname, move in logic.belt.Spawns.items(): 
            ret = move.find_viability()
            if ret in EVALS and not ret==EVAL_T: 
                removes.append(mv_keyname)
#                print 'removing:', mv_keyname, move, WHICH_EVAL[ret]
        for r in removes: 
            logic.belt.Spawns[r].kill()
            logic.belt.Spawns.pop(r)

        for d in logic.belt.Dependents.values(): d.PrepareAction()


#-- Interface method        __ Implement __        Call after Deciding, for all
    def Implement(logic):   
        if logic.gm.frame_iter>1: logic.root_ap.implement()
        for dep in logic.belt.Dependents.values():  
            dep.DoAction() # broad
        for move in logic.belt.Spawns.values():  
            move.implement() # specific

    #Deliver and receive message: these simply hide message handler systems.
    def deliver_message(logic, msg, **args):
        ''' deliver_message: primary outbox method. Only I should call this, 
            in order to compose outgoing messages.  '''
        logic.message_handler._deliver_message( msg, **args )

    def receive_message(logic, msg, **args):
        ''' receive_message: primary inbox method. Let others call this to 
            communicate something to This. '''
        logic.message_handler._receive_message( msg, **args )


    ''' ----------  Private methods  ---------- '''

    # view/update_global//env: interface with high-level, oft-accessed state
    # variables. Specifically, these ought to be dominated by: (1) computed, 
    # parameterized globals and (2) forcible changes via messages, as the only
    # way an external entity should be able to effect this.
    def view(logic, what):  
        if not what in logic._state.s_env.keys() and \
                what in logic._state.s_ssr.keys() :
                    raise Exception("This information is accessed via sensor",what)
        return logic._state.view_env(what)
    def update_global(logic, key, value, field_type=None):
        logic._state.update_env(key, value, field_type)

    # view/update_ap//my: ActionPickers interface with private reserved space
    def view_my(logic, what, who): 
        if not type(who)==int: who=who.uniq_id
        return logic._state.view_ap(what, who)
    def update_ap(logic, key, value, who):
        logic._state.update_ap(key, value, who)
    
    # view/update_dep: dependent objects piggyback, storing and writing 
    # their data accessibly but also providing reads to parent's components.
    def view_dep(logic, what, who): return logic._state.view_dep(what, who)
    def update_dep(logic, key, value, who):
        logic._state.update_dep(key, value, who)

    # get_resource: ad hoc implementation for reading from the Game Manager 
    def get_resource(logic, database, which_resource):
        if database=='plyr img':
            return logic.gm.imgs['player sprite '+str(which_resource)]

    # get/view/has_sensor: read/query this logic-holder's sensors, from anywhere.
    def view_sensor(logic, what_sensor, **args): # Sensors can elect to prime also
        return logic.get_sensor(what_sensor).sense(**args)
    def get_sensor(logic, name): return logic.belt.Sensors.get(name, False)
    def has_sensor(logic, what_sensor):
        return not logic.get_sensor(what_sensor)==False

    def plyr_steps(logic, dvec): 
        if not logic.agent.species=='plyr': 
            raise Exception('notice: not plyr object')
        return ( int(dvec[X] * logic.gm.smoothing() * logic.agent.stepsize_x), \
                 int(dvec[Y] * logic.gm.smoothing() * logic.agent.stepsize_y))
    def pop_PDA(logic, index):
        if not type(index)==int: index = index.index # hack city
        s = []
        for i in logic._state.s_env['PDA']:
            if not i.index==index: 
                s.append(i)
        logic._state.s_env['PDA'] = s

    def push_PDA(logic, index): # CHECK
        if not type(index)==int: index = index.index # hack city
        a = logic.belt.Actions[index_to_ltr[index]]
        logic.pop_PDA(a)
        if not a in logic._state.s_env['PDA']:
            logic._state.s_env['PDA'].insert(0, a)

    def get_PDA(logic):
        try: 
            return logic._state.s_env['PDA'][0]
        except: 
            logic.push_PDA(-1)
            return logic.belt.Actions['-']
#
    def do_default(logic): return EVAL_T # semi-stub

    def UnlockAction(logic, uid): # try to lock
        if logic.__action_lock==uid: logic.__action_lock=-1
        else: raise Exception('uid does not have lock:',uid,logic.__action_lock)
    def ViewActionLock(logic): return logic.__action_lock
    def LockAction(logic, uid): # try to lock
        if logic.__action_lock<0: 
            logic.__action_lock = uid
            return True
        return False

    def tTOp(logic, X): 
        try: return multvec(X, logic.gm.tile_size, int)
        except: raise Exception(X)
    def pTOt(logic, X): 
        try: return divvec(X, logic.gm.tile_size, '//')
        except: raise Exception(X)

    def spawn_new(logic, what_to_spawn, kind, **options):
        optn = options.copy()
        if what_to_spawn in ['cast pokeball', 'throw pokeball', 'tackle',\
#                            'pokemon animation u', 'pokemon animation r', 
#                            'pokemon animation d',
                            'pokemon animation']:
            optn['logic'] = logic
            new_ent = logic.belt.spawn_new(what_to_spawn, kind, **optn)
            try:    new_ent.reset()
            except: new_ent.Reset()
            return new_ent
        elif what_to_spawn in ['create pokemon']:
            if not optn.get('which_slot',False): return 'signal XASDFUEN'
            if len(optn.keys())==0: return None
#            print 'pkmn in belt before',logic.belt.Pkmn, optn
            cur_pkmn = logic.belt.Pkmn.copy()
            logic.belt.Pkmn.pop(optn['which_slot'])
            for k in optn.keys(): 
                if k in cur_pkmn.keys(): cur_pkmn[k]=optn[k]
            optn.update(cur_pkmn[optn['which_slot']]) # Add data from belt
#            print 'pkmn in belt after',logic.belt.Pkmn , optn
            optn['name'] = name = 'PkmnPlyr_'+str(logic.belt.pkmn_counter)
            optn['team'] = logic.agent.team
            cur_pkmn['init_tloc'] = optn['init_tloc']
            logic.belt.pkmn_counter += 1
            try:
                cur_health, max_health = optn['cur_health'], optn['max_health']
            except:
                cur_health, max_health = optn['health_cur'], optn['health_max']
            logic.gm.addNew('Agents', name, agents_module.AIAgent, \
                                 sp_init='pkmn_basic_init', 
                                 init_tloc=optn['init_tloc'],
                                 tloc=optn['init_tloc'],
                                 pokedex=optn['pokedex'], 
                                 team=optn['team'], 
                                 cur_health=cur_health, 
                                 max_health=max_health, 
                                 hbcolor='b', 
                                 )
        else:
            raise Exception('logic spawn_new', what_to_spawn, kind, optn)

    def kill(logic): logic.IS_DEAD = True
    def _kill(logic):
        print "I am dying:", logic.agent
        logic.gm.display.queue_reset_tile(logic.view_sensor('tpos'), 'tpos')
        logic.agent.delete_all()
        logic.gm.db.execute(sql_del_partial+'uniq_id=?;', (logic.agent.uniq_id,))

#        print logic.belt.Spawns
        for r in logic.belt.Spawns.keys(): 
            logic.belt.Spawns[r].kill()
            logic.belt.Spawns.pop(r)
        for entity in logic.belt.Sensors.values() + \
                logic.belt.Dependents.values() +[ logic.agent, logic]:
            for coll in (logic.gm.Agents, logic.gm.Effects, logic.gm.AfterEffects):
                print '--',coll
                for k,v in coll.items():
                    if  v.uniq_id==entity.uniq_id:
                        coll.pop(k)
                coll = {k:v for k,v in coll.items() if not \
                                v.uniq_id==logic.agent.uniq_id}
            logic.gm.db.execute(sql_del_partial+'uniq_id=?;', (entity.uniq_id,))
            logic.gm.entities.pop(entity.uniq_id)
            del entity
#            try:
#                logic.gm.db.execute(sql_del_partial+'uniq_id=?;', (entity.uniq_id,))
#                logic.gm.entities.pop(entity.uniq_id)
#            except:
#                print entity, 'was unable to remove standardly.'
#                del entity
            
