'''
AI Logic module for handling interactive behavior.

'''
import numpy as np
import pygame, random, sys

from utilities import *
from abstractEntities import *
from belt import *
from sensors import *
from state import *
from playerActions import *
from pokemonActions import *
from otherActions import *
from compositeActions import *


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

        # Read and process messages:
        while len(logic.message_queue)>0:
            print "processing message..."
            msg = logic.message_queue.pop(0)
            logic._state.update_ext(msg[0],msg[1])

        # Notify actions and ActionPickers that they can reset for next frame:
        logic.root_ap.reset()
        put = logic._state.update_env
        if logic.agent.species=='plyr': 
            # Update _state for new frame for PLAYER:
            # (ideally, sensors would offload most of this)

            put('prev move vec', logic.view('curr move vec'))   # do both these lines
            put('curr move vec', logic.gm.events[:4])           # with a Sensor
            put('triggered actions', logic.gm.events[4:])
#            print '---'

#        prev_inds = ap.logic.view('prev move vec')

        for snm,sensor in logic.belt.Sensors.items():
            sensor.rescan()


#-- Interface method        __ Decide __        Call for ALL before implementing
    def Decide(logic):      logic.root_ap.find_viability()
#-- Interface method        __ Implement __        Call after Deciding, for all
    def Implement(logic):   logic.root_ap.implement()

    # Notify: primary inbox method!
    def notify(logic, whatCol, whatVal):
        logic.message_queue.append( (whatCol, whatVal) )


    ''' ----------  Private methods  ---------- '''

    def __init__(logic, gm, agent, belt=None, init_belt=None, init_ppos=None):
        Entity.__init__(logic, gm)
        logic._state = State(gm, belt)
        logic.agent = agent
        if belt: 
            logic.belt = belt
            for action in belt.Actions.values(): action.logic=logic
        logic.message_queue = []
        logic._state.setup_fields(agent.species, logic, ppos=init_ppos)
        if agent.species=='plyr': 
            logic.root_ap = BasicPlayerActionPicker(logic)
        elif agent.species=='target':
            logic.root_ap = MouseActionPicker(logic)
        else:
            raise Exception('not impl yet')
        
        logic.root_ap.reset()

    def get_sensor(logic, name): return logic.belt.Sensors.get(name, False)

    def view_my(logic, what, who): return logic._state.view_ap(what, who)
    def view(logic, what):  return logic._state.view_env(what)
    def view_sensor(logic, what_sensor, **args): # Sensors can elect to prime also
        return logic.get_sensor(what_sensor).sense(**args)

    def get_resource(logic, database, which_resource):
        if database=='plyr img':
            return logic.gm.imgs['player sprite '+str(which_resource)]
    def has_sensor(logic, what_sensor):
        return not logic.get_sensor(what_sensor)==False
#
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

#    def detect(logic, what_sensor, agent_id=None): 
#        # specialty method that both primes and accesses
#        s=logic.get_sensor(what_sensor)
#        u=s.sense(agent_id)
#        t=s.access()
#        return t
#
#    def downgrade_PDA(logic, index):
#        if not type(index)==int: index = index.index # hack city
#        a = logic.belt.Actions[index_to_ltr(index)]
#        if a in logic._state.s_env['PDA']:
#            logic._state.s_env['PDA'].pop(a)
#            logic._state.s_env['PDA'].append(a)
#        else:
##            logic._state.s_env['PDA'].remove(a)
##            logic._state.s_env['PDA'].append(a)
##            print " ->> downgrading:", a
#            pass#logic._state.s_env['PDA'].append(a)
#
#    def clear_PDA(logic):
#        logic._state.s_env['PDA'] = [logic.belt.Actions['-']]
    def get_PDA(logic):
        try: 
            return logic._state.s_env['PDA'][0]
        except: 
#            print 'Exception',logic._state.s_env['PDA']
            logic.push_PDA(-1)
            return logic.belt.Actions['-']
#    def append_PDA(logic, which_pda, element):
#        if not element in logic._state.s_env[which_pda]:
#            logic._state.s_env[which_pda].append(element)
#
    def do_default(logic): return EVAL_T # semi-stub


    def tTOp(logic, X): 
        try: return multvec(X, logic.gm.tile_size, int)
        except: raise Exception(X)
    def pTOt(logic, X): 
        try: return divvec(X, logic.gm.tile_size, '//')
        except: raise Exception(X)
    
    def update_ap(logic, key, value, who):
        logic._state.update_ap(key, value, who)
    def update_global(logic, key, value): # for internal use only!
        logic._state.update_env(key, value)






