'''
Belt: inventory class and management methods for an Agent.
'''
import pygame

from utilities import *
from abstractEntities import Entity, Agent

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
    def __init__(belt, gm, whose_belt): 
        Entity.__init__(belt, gm)
        if not isinstance(whose_belt, Agent): 
            raise Exception(type(whose_belt))
        belt.whose_belt = whose_belt
        belt.gm = gm
        belt.pkmn = []
        belt.items = ['pokeball-lvl-1']*4
        belt.avail_actions = {'throw':True, 'catch':True}

    def add_pkmn(belt, pkmn):
        belt.pkmn.append(stored_pkmn(belt.gm, pkmn))
            
