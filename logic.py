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
        logic.viability = EVAL_F
        # Read and process messages:
        while len(logic.message_queue)>0:
            print "processing message...",logic.message_queue[0]
            msg = logic.message_queue.pop(0)
            logic._state.update_global(msg[0],msg[1])

        # Rescan sensors:
        for snm,sensor in logic.belt.Sensors.items():
            sensor.rescan()
            if snm in ['tpos','ppos']: # Self-reference these.
                logic.get_sensor(snm).agent_id = logic.agent.uniq_id
            if logic.agent.species=='plyr' and snm=='tpos':
                print "Rescanned tpos sensor.", logic.view_sensor('tpos')

        # Reset Actions and ActionPickers:
        logic.root_ap.reset()

        # Update interlocking global fields:
        put = logic._state.update_env
        put('next reserved', logic.view_sensor('tpos'))
        #put('delay',logic.view('delay')-logic.gm.dt**-1)
        put('delay',logic.view('delay')-logic.gm.dt) # check...
        #print logic.agent.uniq_id,logic.view('delay'), logic.view('root delay'), logic.gm.dt
#        print "Decrease delay :", logic.gm.dt/1000.0, logic.gm.fps, logic.gm.dt**-1
#        print logic.gm.dt, logic.gm.fpms, logic.gm.dt*logic.gm.fpms
        if logic.agent.species=='plyr': 
            pass
#            put('prev move vec', logic.view('curr move vec'))   # do both these lines
#            put('curr move vec', logic.gm.events[:4])           # with a Sensor
#            put('triggered actions', logic.gm.events[4:])
        if logic.agent.species=='pkmn':
#            put('prevtid', logic.view('curtid'))
            pass#put('curtid', logic.view_sensor('tpos'))

        for dep in logic.belt.Dependents.values(): dep.Reset()

#-- Interface method        __ Decide __        Call for ALL before implementing
    def Decide(logic):      
        logic.viability = logic.root_ap.find_viability()
        removes = []
        for dep_key, dep in logic.belt.Dependents.items(): 
            ret = dep.PrepareAction()
            if ret in EVALS and not ret==EVAL_T: 
                removes.append(dep_key)
                print 'removing:', dep_key, dep, WHICH_EVAL[ret]
        map(logic.belt.Dependents.pop, removes)
#-- Interface method        __ Implement __        Call after Deciding, for all
    def Implement(logic):   
        if logic.gm.frame_iter>1: logic.root_ap.implement()
        for dep in logic.belt.Dependents.values():  dep.DoAction()

    # Notify: primary inbox method!
    def notify(logic, whatCol, whatVal):
        logic.message_queue.append( (whatCol, whatVal) )


    ''' ----------  Private methods  ---------- '''

    def __init__(logic, gm, agent, **options):
        Entity.__init__(logic, gm)
        agent.has_logic=True
        logic.agent = agent
        logic.belt = belt_module.Belt(gm, agent, **options)
        logic._state = state_module.State(gm, logic.belt)
        logic._state.setup_fields(agent.species, logic=logic, 
                            ppos=options['init_ppos'])
        logic.message_queue = []
        if agent.species=='plyr': 
            logic.root_ap = BasicPlayerActionPicker(logic)
        elif agent.species=='target':
            logic.root_ap = MouseActionPicker(logic)
        elif agent.species=='pkmn':
            logic.root_ap = WildPkmnBehavior(logic)
#            for dk,dv in logic.belt.Dependents.items():
#                if dk=='health' and logic.agent.team=='--plyr--': 
#                    dv = dv(logic.gm, team=logic.agent.team, agent=logic.agent, metric=dk, color='b', init_value=)
#                if dk=='health' and logic.agent.team=='--plyr--': 
#                    dv = dv(logic.gm, team=logic.agent.team, agent=logic.agent, metric=dk, color='r')
        else:
            raise Exception('not impl yet')
        
        logic.root_ap.reset()

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


    def tTOp(logic, X): 
        try: return multvec(X, logic.gm.tile_size, int)
        except: raise Exception(X)
    def pTOt(logic, X): 
        try: return divvec(X, logic.gm.tile_size, '//')
        except: raise Exception(X)

    def spawn_dep(logic, what_to_spawn, kind, **options):
        # spawn a dependant by keystr. kind: Move, Agent, StatusBar, ...
        options['logic'] = logic#._state
        new_ent = logic.belt.spawn_new(what_to_spawn, kind, **options)




