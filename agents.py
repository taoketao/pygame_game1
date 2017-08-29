'''
agents.py:
Implementations of various kinds of agents:
    Core Agents:
- Player represents a human controllable player.
- AIAgent is a pokemon AI whose actions are independently, internally motivated.
    Supers:
- Highlighter is a TileAgent that draws generic targets over tiles.
- StatusBar is a generic bar that indicates some metric for another agent.
    Dependent Agents:
- PlayerHighlighter is a Highlighter that highlights the player's current tile.
- MouseTarget is a Highlighter that makes mouse indications.
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
PLYR_COLL_WIDTH, PLYR_COLL_SHIFT = 0.4, 0.2
PLYR_IMG_SHIFT_INIT = 0.125
DEFAULT_STEPSIZE = 3.7 # a prime?
PLYR_CATCH_DIST = 0.5
PLYR_COLL_BUF = 1+PLYR_COLL_WIDTH
PLYR_STEP_DELAY = 51

# Latencies for Pkmn:
PKMN_WANDER_LOW, PKMN_WANDER_HIGH = 1.0,3.0
PKMN_MOVE_LOW, PKMN_MOVE_HIGH = 0.4,0.9
PKMN_WANDER_DELAY = 1600
DIRVECS_TO_STR = {(0,1):'u',(1,0):'l',(-1,0):'r',(0,-1):'d'} 

# (color) options for Mouse:
MOUSE_CURSOR_DISPL = 3
MOUSE_GRAD = (180,160,60,160)
                     
# Health bar: 
#BAR_WIDTH = 3


class Player(ae_module.VisualStepAgent):
    ''' Player class: the human player representation as an agent (step, img) '''
    def __init__(ego, gm):
        init_tpos = divvec(gm.map_num_tiles,1.5) 
        init_ppos = addvec(multvec(init_tpos,gm.ts()), list(np.random.choice(\
                range(1, min(gm.ts())), 2)))
        ae_module.VisualStepAgent.__init__(ego, gm, init_tpos=init_tpos)
        ego.species='plyr'
        ego.team = '--plyr--'
        ego.primary_delay = PLYR_STEP_DELAY
        ego.store_reservations=True
        ego.image_offset = multvec(gm.ts(), (0.4,0.9))
        ego.stepsize_x, ego.stepsize_y = \
                ego.stepsize = multvec(gm.ts(), DEFAULT_STEPSIZE/(10+gm.fps**0.5),int)
        ego._logic = logic_module.Logic(gm, ego, init_ppos=init_ppos)
        ego._belt = ego._logic.belt
        ego.gm.notify_update_agent(ego, img_str='player sprite 7', team=ego.team,\
                            agent_type=ego.species)
        ego.gm.notify_update_agent(ego, tx=init_tpos[X], ty=init_tpos[Y],\
                            px=init_ppos[X], py=init_ppos[Y])
        ego.initialized = True

    ''' Methods: Game Manager to PlayerAgent '''
    def Reset(ego):         ego._logic.Update()
    def PrepareAction(ego): ego._logic.Decide()
    def DoAction(ego):      ego._logic.Implement()

    def message(ego, header, msg):
        ''' Method: other Agents to PlayerAgent '''
        if header=="Someone has caught me":
            ego._belt.add_pkmn(msg)
        etc
        ego.logic.notify('isPlayerActionable', True)
        ego.logic.notify(header, msg)

    def set_img(ego, which_img): 
        ''' Methods: fulfill inheritance. '''
        if (not type(which_img)==int) or not which_img in range(12): \
                raise Exception(which_img, type(which_img))
        ego.gm.notify_image_update(ego, 'player sprite '+str(which_img+1))
    def get_pstep(ego): return divvec(ego.stepsize, ego.gm.smoothing())

    ''' Methods: available to many for read.  ( No need to overwrite 
            move_in_direction for Player(VisualStepAgent)  ) '''
    def moveparams_to_steps(ego,dirs):
        dx = (dirs[RDIR]-dirs[LDIR]) * ego.gm.smoothing() * ego.stepsize[X]
        dy = (dirs[DDIR]-dirs[UDIR]) * ego.gm.smoothing() * ego.stepsize[Y]
        return (dx,dy)
        return multvec((dx,dy), ego.gm.fps)
    def get_num_actions(ego): return len(ego._belt.Actions)
    def alias_sensor(ego, what_sensor): return ego._logic.get_sensor(what_sensor)
    def view_field(ego, what_field): return ego._logic.view(what_field)


class AIAgent(ae_module.TileAgent):
    ''' AIAgent class: basic pokemon unit.'''
    def __init__(ai, gm, **options):
        ae_module.TileAgent.__init__(ai, gm, options['init_tloc'])
        init_tloc = options['init_tloc']
        ai.primary_delay = PKMN_WANDER_DELAY 
        ai.species = 'pkmn'
        ai.team = '--'+options.get('team')+'--'
        ai.store_reservations=True
        ai.stepsize_x, ai.stepsize_y = ai.stepsize = gm.ts()
        px,py = gm._t_to_p(init_tloc)
        ai._logic = logic_module.Logic(gm, ai, init_ppos=(px,py), **options)
        ai._logic.update_global('curtid',init_tloc)
        ai._logic.update_global('max health',options['health'])
        ai._logic.update_global('cur health',options['health']) # default
        ai._logic.update_global('uniq_name',options['uniq_name'])
        ai._belt = ai._logic.belt
        ai.initialized = True
        ai.pokedex = options['pokedex']
        ai.gm.notify_update_agent(ai, team=ai.team, agent_type=ai.species, \
                img_str='pkmn sprite '+str(ai.pokedex)+'d',\
                tx=init_tloc[X], ty=init_tloc[Y], px=px, py=py)
        ai.set_img('d')

    def Reset(ai):         ai._logic.Update()
    def PrepareAction(ai): ai._logic.Decide()
    def DoAction(ai):      ai._logic.Implement()

    def set_img(ai, which_img, reset=None): 
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



class PlayerHighlighter(ae_module.Highlighter):
    ''' Follow the player & indicate current tile. '''
    def __init__(h, gm, who='Player'): 
        ae_module.Highlighter.__init__(h, gm)
        h.targeter = sensors_module.GetNextReservation(gm, gm.Agents[who].uniq_id)
        h.targeter.set_state('stateless')
        h.color = (60,120,180,160)
        h.gm.notify_image_update(h, 'targ '+str(h.color), h.draw_highlight((0,0)))
        h.gm.notify_update_agent(h, img_str = 'targ '+str(h.color))


class MouseTarget(ae_module.Highlighter):
    ''' Follow the mouse & indicate current tile. '''
    def __init__(h, gm): 
        ae_module.Highlighter.__init__(h, gm)
        h.targeter = sensors_module.GetMouseTIDSensor(gm)
        h.color= MOUSE_GRAD
        h.gm.notify_image_update(h, 'targ '+str(h.color), h.draw_highlight((0,0)))
        h.gm.notify_update_agent(h, img_str = 'targ '+str(h.color))

class StatusBar(ae_module.TileAgent):
    ''' An abstract status bar class that pokemon can take on.
        TODO: move this to abstractEntities once completed'''
    def __init__(sb, gm, owner, **options):
        ae_module.TileAgent.__init__(sb, gm, options.get('init_tloc',(0,0)))
        sb.species='bar'
        sb.team = owner.team
        sb.owner = owner

        # Set fields
        sb.color = { 'b': (110,120,255,255), 'r': (255,0,0,255),\
                     'y': (255,255,0,255)}[\
                options.get('hbcolor','r')]
        sb.metric = options['metric']
        sb.bg_color = (0,0,0,255)
        sb.prev_position = (0,0)
        sb.offset = 2+(BAR_WIDTH+1)*options.get('offset',0) # stack distance 
        sb.shift = 2+(BAR_WIDTH+1)*options.get('shift', 0) # buffer dist from edge
        sb.orientation = options.get('orientation', 'horiz') # vs vertic
        sb.cur_metric = sb.init_metric = options['health']
        if sb.orientation=='vertic':
            sb.bar_shape = (BAR_WIDTH, options[sb.metric])
        elif sb.orientation=='horiz':
            sb.bar_shape = (options[sb.metric], BAR_WIDTH)
        else: raise Exception("Other statusbar format not implemented")

        # conduct essential initial interactions
        sb.gm.notify_update_agent(sb, team=sb.team,   \
                tx=options.get('init_tloc',(0,0))[X], \
                ty=options.get('init_tloc',(0,0))[Y], \
                agent_type=sb.species, img_str='bar '+str(sb.color))
        sb.gm.notify_image_update(sb, 'bar '+str(sb.color)+str(sb.uniq_id), \
                                      sb.draw_statusbar())
        sb.targeter = sensors_module.GetNextReservation(gm, owner.uniq_id)
        sb.targeter.set_state('stateless')

    def update_position(sb): 
        sb.gm.notify_tmove(sb.uniq_id, sb.targeter.sense())

    # Public access method: TODO: turn this into a sensor/etc
    def update_metric(sb, amount, delta_or_absolute='delta'):
        if delta_or_absolute=='delta': amount = sb.cur_metric+amount
        elif not delta_or_absolute=='absolute': raise Exception()
        sb.cur_metric = min(sb.init_metric, max(0, amount)) # CAPPED!
        sb.gm.notify_image_update(sb, 'bar '+str(sb.color)+str(sb.uniq_id), \
                                          sb.draw_statusbar())

    def draw_statusbar(sb):
        scaling_amount = float(0.5*sb.cur_metric)/sb.init_metric # for debugging
        scaling_amount = float(sb.cur_metric)/sb.init_metric # for debugging
        if sb.orientation=='horiz':
            scaling = (scaling_amount, 1)
            loc = (sb.shift, sb.offset)
            maxsize = (sb.gm.ts()[X]-2*sb.shift, BAR_WIDTH)
            full_size = minvec(addvec(sb.bar_shape,2), \
                            (sb.gm.ts()[X]-2*sb.shift, BAR_WIDTH+2))
            cur_size = minvec(multvec(sb.bar_shape,scaling), \
                            (sb.gm.ts()[X]-2*sb.shift, BAR_WIDTH))
        elif sb.orientation=='vertic':
            scaling = (1, scaling_amount)
            maxsize = (BAR_WIDTH, sb.gm.ts()[Y]-2*sb.shift)
            full_size = minvec(addvec(sb.bar_shape,2), \
                            (BAR_WIDTH+2, sb.gm.ts()[X]-2*sb.shift))
            cur_size = minvec(multvec(sb.bar_shape,scaling), \
                            (BAR_WIDTH, sb.gm.ts()[X]-2*sb.shift))
            loc = (sb.offset, sb.shift+sb.gm.ts()[Y]-sb.bar_shape[Y])
            loc = (sb.offset, -2*sb.shift+sb.gm.ts()[Y]-sb.bar_shape[Y])
        image = pygame.Surface(sb.gm.ts()).convert_alpha()
        image.fill((0,0,0,0))

        delt = sub_aFb(cur_size,full_size) 
        s_full = pygame.Surface( full_size ).convert_alpha()
        s_curr = pygame.Surface( cur_size ).convert_alpha()
        s_full.fill(sb.bg_color)
        s_curr.fill(sb.color)
        image.blit(s_full, loc)
        image.blit(s_curr, addvec(loc,{'horiz':1, \
                'vertic':sub_aFb((1,1),delt)}\
                [sb.orientation]))
        return image


    def Reset(sb): pass # All StatusBar fields are reset by the logic.
    def PrepareAction(sb): sb.targeter.rescan()
    def DoAction(sb): sb.update_position()



