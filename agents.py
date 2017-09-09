'''
agents.py:
Implementations of various kinds of primary agents that (can) operate without
    a parent agent to be a dependent of.
- Player represents a human controllable player.
- AIAgent is a pokemon AI whose actions are independently, internally motivated.
'''


import pygame, random
import numpy as np

from utilities import *
import abstractEntities as ae_module
import sensors as sensors_module
import belt as belt_module
import logic as logic_module

''' Magic Numbers '''
# latencies for Player:
DEFAULT_STEPSIZE = 3.7 # a prime?
PLYR_CATCH_DIST = 0.5
PLYR_STEP_DELAY = 41



class Player(ae_module.VisualStepAgent):
    ''' Player class: the human player representation as an agent (step, img) '''
    def __init__(ego, gm, **__unused_arguments):
        init_tpos = divvec(gm.map_num_tiles,1.5) 
        init_ppos = addvec(multvec(init_tpos,gm.ts()), list(np.random.choice(\
                range(1, min(gm.ts())), 2)))
        ae_module.VisualStepAgent.__init__(ego, gm)

        ego.isMasterAgent = True
        ego.uniq_name = ego.species='plyr'
        ego.team = '--plyr--'
        ego.primary_delay = PLYR_STEP_DELAY
        ego.store_reservations=True
        ego.image_offset = multvec(gm.ts(), (0.4,0.9))
        ego.stepsize_x, ego.stepsize_y = ego.stepsize =  \
                multvec(gm.ts(), DEFAULT_STEPSIZE/(10+gm.fps**0.5),int)
        ego._logic = logic_module.Logic(gm, ego, init_ppos=init_ppos)
        ego._belt = ego._logic.belt
        ego.gm.notify_update_ent(ego, img_str='player sprite 7', \
                                team=ego.team, species=ego.species, \
                                px=init_ppos[X], py=init_ppos[Y])
        ego.gm.notify_put_ppos(ego.uniq_id, init_ppos)
        ego.initialized = True

    ''' Methods: Game Manager to PlayerAgent '''
    def Reset(ego):         ego._logic.Update()
    def PrepareAction(ego): ego._logic.Decide()
    def DoAction(ego):      ego._logic.Implement()

    def set_img(ego, which_img): 
        ''' Methods: fulfill inheritance. '''
        if (not type(which_img)==int) or not which_img in range(12): \
                raise Exception(which_img, type(which_img))
        ego.gm.notify_image_update(ego, 'player sprite '+str(which_img+1))
    def get_pstep(ego): return divvec(ego.stepsize, ego.gm.smoothing())

    ''' Methods: available to many for read.  ( No need to overwrite 
            move_in_direction for Player(VisualStepAgent)  ) '''
    def moveparams_to_steps(ego,dirs):
        ''' convert a given (dx,dy) vector into the appropriate scaling '''
        dx = (dirs[RDIR]-dirs[LDIR]) * ego.gm.smoothing() * ego.stepsize[X]
        dy = (dirs[DDIR]-dirs[UDIR]) * ego.gm.smoothing() * ego.stepsize[Y]
        return (dx,dy)
    def get_num_actions(ego): return len(ego._belt.Actions)
    def alias_sensor(ego, what_sensor): return ego._logic.get_sensor(what_sensor)
    def view_field(ego, what_field): return ego._logic.view(what_field)
    def view_in_belt(ego, category, what): 
        if what=='any' and category=='Pkmn': 
            return ego._belt.Pkmn[ego._belt.Pkmn.keys()[0]].copy()
        elif what=='all values' and category=='Pkmn': 
            return ego._belt.Pkmn.values()
        else: raise Exception(category, what)
    def receive_message(ego, m, **t): ego._logic.receive_message(m, **t)

class AIAgent(ae_module.TileAgent):
    ''' AIAgent class: basic pokemon unit.'''
    def __init__(ai, gm, **options):
        ae_module.TileAgent.__init__(ai, gm)#, options['init_tloc'])
        ai.isMasterAgent = True
        init_tloc = options['init_tloc']
        ai.primary_delay = PKMN_WANDER_DELAY 
        ai.species = 'pkmn'
        ai.team = options.get('team')
        if not '--' in ai.team: ai.team= '--'+ai.team+'--'
        ai.uniq_name = options.get('uniq_name', '-uniqname not provided-')
        ai.store_reservations=True
        ai.stepsize_x, ai.stepsize_y = ai.stepsize = gm.ts()
        px,py = gm._t_to_p(init_tloc)
        ai._logic = logic_module.Logic(gm, ai, init_ppos=(px,py), **options)
        ai._logic.update_global('curtid',init_tloc)
        ai._belt = ai._logic.belt
        ai.initialized = True
        ai.pokedex = options['pokedex']
        ai._logic.update_global('pkmn_id', ai.pokedex)
        ai.gm.notify_update_ent(ai, team=ai.team, species=ai.species, \
                img_str='pkmn sprite '+str(ai.pokedex)+'d',  px=px, py=py)
        ai.gm.notify_put_ppos(ai.uniq_id, (px,py))
        ai.set_img('d')

    def Reset(ai):         ai._logic.Update()
    def PrepareAction(ai): ai._logic.Decide()
    def DoAction(ai):      ai._logic.Implement()

    def set_img(ai, which_img, reset=None): 
        ''' Change image (frame-timed) according to the image signal which_img.'''
        ai.gm.notify_image_update(ai, 'pkmn sprite '+str(ai.pokedex)+which_img)
        return
        if (not type(which_img)==str) or not which_img in MTNKEYS: \
                raise Exception(which_img, type(which_img))
        s = 'pkmn sprite '+str(ai.pokedex)+which_img
        if ai._logic.view('prevtid')==ai._logic.view('curtid') and not reset:
            ai.gm.notify_imgChange(ai, s)
        elif not reset:
            ai.gm.notify_imgChange(ai, s, prior=(ai._logic.view("prevtid"), 'tpos'))
        else:
            ai.gm.notify_imgChange(ai, s, prior=(reset, 'tpos'))

    def get_pstep(ai): return ai.gm.ts()
    def alias_sensor(ai, what_sensor): return ai._logic.get_sensor(what_sensor)
    def view_field(ai, what_field): return ai._logic.view(what_field)
    def receive_message(ai, m, **t): ai._logic.receive_message(m, **t)
