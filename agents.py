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
from abstractEntities import VisualStepAgent, TileAgent
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
#PLYR_STEP_DELAY = 0.03+np.random.uniform(0.0,0.01)
PLYR_STEP_DELAY = 81

# Latencies for Pkmn:
PKMN_WANDER_LOW, PKMN_WANDER_HIGH = 1.0,3.0
PKMN_MOVE_LOW, PKMN_MOVE_HIGH = 0.4,0.9
PKMN_WANDER_DELAY = 000
DIRVECS_TO_STR = {(0,1):'u',(1,0):'l',(-1,0):'r',(0,-1):'d'} 

# (color) options for Mouse:
MOUSE_CURSOR_DISPL = 3
MOUSE_GRAD = (180,160,60)
#INIT_POS = (100,100)
# Health bar: 
BAR_WIDTH = 3


class Player(VisualStepAgent):
    ''' Player class: the human player representation as an agent (step, img) '''
    def __init__(ego, gm):
        init_tpos = divvec(gm.map_num_tiles,1.5) 
        init_ppos = addvec(multvec(init_tpos,gm.ts()), list(np.random.choice(\
                range(1, min(gm.ts())), 2)))
        VisualStepAgent.__init__(ego, gm, init_tpos=init_tpos)
        ego.species='plyr'
        ego.team = '--plyr--'
        ego.primary_delay = PLYR_STEP_DELAY #* gm.fps # ie, without smoothing
        print 'ego.primary_delay', ego.primary_delay
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
    #def get_pstep(ego): return divvec(ego.stepsize, ego.gm.smoothing())
    #def get_pstep(ego): return ego.stepsize

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


class AIAgent(TileAgent):
    ''' AIAgent class: basic pokemon unit.'''
    def __init__(ai, gm, **options):
        TileAgent.__init__(ai, gm, options['init_tloc'])
        init_tloc = options['init_tloc']
        ai.primary_delay = PKMN_WANDER_DELAY #* gm.fps # ie, without smoothing
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
        ai.gm.notify_update_agent(ai, img_str='pkmn sprite '+str(ai.pokedex)+'d',
                    team=ai.team, agent_type=ai.species)
        ai.gm.notify_update_agent(ai, tx=init_tloc[X], ty=init_tloc[Y], px=px, py=py)

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



class Highlighter(TileAgent):
    ''' An abstract highlighter class. Provide the <targeter> a sensor that
        returns a TPOS to put this highlighter on. TODO: move this to abstractEntities.'''
    def __init__(h, gm):
        TileAgent.__init__(h, gm, (0,0))
        h.default_color = (0,0,0,255)
        h.species='target'
        h.team = '--targets--'
        h.prev_position = (0,0)
        h.targeter = None;
        h.image_offset = (-2,-2)
        h.gm.notify_update_agent(h, tx=0,ty=0,px=0,py=0,\
                    team=h.team, agent_type=h.species)
        h.gm.reserved_tiles[(0,0)] = NULL_RESERVATION

    def update_position_and_image(h): 
        ''' update_position_and_image: call every frame to update. '''
        prev_tpos = h.prev_position
        new_tpos = h.targeter.sense()
        px,py=multvec(h.gm.ts(), new_tpos)
        h.gm.notify_pmove(h.uniq_id, multvec(h.gm.ts(), new_tpos))
        h.prev_position = new_tpos

    def draw_highlight(h, tile_location):
        '''  Draw a target on specified tile. '''
        try:
            r,g,b,a = h.color
        except:
            r,g,b,a = h.default_color
        image = pygame.Surface(h.gm.ts()).convert_alpha()
        image.fill((0,0,0,0))
        tx,ty = h.gm.tile_size
        tx = tx-2; ty=ty-2
        M = MOUSE_CURSOR_DISPL = 1; # stub!
        for i in [1,3,4,5]:
            for d in DIRECTIONS:
                rect_size = { UDIR: (tx-2*(i+1)*M, M),  
                              DDIR: (tx-2*(i+1)*M, M),
                              LDIR: (M, ty-2*(i+1)*M), 
                              RDIR: (M, ty-2*(i+1)*M) }[d]
                location = {
                    UDIR: ((i+1)*M, i*M),    DDIR: ((i+1)*M, ty-(i+1)*M), 
                    LDIR: (i*M, (i+1)*M),    RDIR: (tx-(i+1)*M, (i+1)*M), }[d]
                if rect_size[X]<=0 or rect_size[Y]<=0: continue


                s = pygame.Surface( rect_size ).convert_alpha()
                try:
                    s.fill( (r,g,b, MOUSE_GRAD[i-1]) )
                except:
                    s.fill( (r,g,b, MOUSE_GRAD[-1]) )
                image.blit( s, location )
        h.display_parameters = (-1, image, addvec((1,1),multvec(tile_location,h.gm.ts())))
        return image

    def Reset(h): pass
    def PrepareAction(h): h.targeter.rescan()
    def DoAction(h): h.update_position_and_image()


class PlayerHighlighter(Highlighter):
    ''' Follow the player & indicate current tile. '''
    def __init__(h, gm, who='Player'): 
        Highlighter.__init__(h, gm)
#        plyr = h.gm.Agents['Player']
#        h.targeter = plyr.alias_sensor('tpos')
#        h.targeter = sensor
        h.targeter = sensors_module.GetNextReservation(gm, gm.Agents[who].uniq_id)
        h.targeter.set_state('stateless')
        #h.targeter = h.gm.Agents['Player'].view_field('most recently reserved')
        h.color = (60,120,180,60)
        h.gm.notify_image_update(h, 'targ '+str(h.color), h.draw_highlight((0,0)))
        h.gm.notify_update_agent(h, img_str = 'targ '+str(h.color))



class MouseTarget(Highlighter):
    ''' Follow the mouse & indicate current tile. '''
    def __init__(h, gm): 
        Highlighter.__init__(h, gm)
        h.targeter = sensors_module.GetMouseTIDSensor(gm)
        h.color=h.default_color
        h.gm.notify_image_update(h, 'targ '+str(h.color), h.draw_highlight((0,0)))
        h.gm.notify_update_agent(h, img_str = 'targ '+str(h.color))

class StatusBar(TileAgent):
    ''' An abstract status bar class that pokemon can take on.
        TODO: move this to abstractEntities once completed'''
    def __init__(sb, gm, owner, **options):
        TileAgent.__init__(sb, gm, (0,0))
        sb.species='bar'
        sb.team = owner.team
        sb.owner = owner
        sb.color = { 'b': (0,0,255,255), 'r': (255,0,0,255) }[options.get('hbcolor','r')]
        sb.metric = options['metric']
        sb.bg_color = (0,0,0,255)
        sb.prev_position = (0,0)
        sb.offset = 0.1 # move the bar away from edge (ie, if have numerous bars)
        sb.shift = 0.15 # shape the bar ( adjust width for aesthetics ). 0.2-0.1 solid.

        sb.cur_metric = sb.init_metric = -1
        sb.orientation = options.get('orientation', 'horiz') # vs vertic
        sb.bar_shape = { 'horiz': (int(sb.gm.ts()[X]*(1-2*sb.shift)), BAR_WIDTH), \
                 'vertic': (BAR_WIDTH, int(sb.gm.ts()[X]*(1-2*sb.shift)))}[sb.orientation]
        sb.gm.notify_update_agent(sb, tx=0,ty=0,px=0,py=0, team=sb.team, \
                agent_type=sb.species, img_str = 'bar '+str(sb.color))
        sb.gm.notify_image_update(sb, 'bar '+str(sb.color), sb.draw_statusbar((0,0)))

    def update_position_and_image(sb): 
        prev_tpos = sb.prev_position
        if sb.cur_metric<0: sb.cur_metric = sb.init_metric = \
                            sb.owner.view_field('max health')
        new_tpos = sb.owner.view_field('most recently reserved')
        px,py=multvec(sb.gm.ts(), new_tpos)
        sb.draw_statusbar(new_tpos)
        sb.gm.notify_pmove(sb.uniq_id, (px,py))
        sb.prev_position = new_tpos

    def update_metric(sb, amount, delta_or_flat='delta'):
        if delta_or_flat=='delta': amount = sb.cur_metric+amount
        elif not delta_or_flat=='flat': raise Exception()
        sb.cur_metric = min(sb.init_metric, max(0, amount))

    def draw_statusbar(sb, new_tpos):
        if sb.orientation=='horiz':
            scaling = (float(sb.cur_metric)/sb.init_metric, 1)
            loc = multvec(sb.gm.ts(), (sb.shift, sb.offset))
        elif sb.orientation=='vertic':
            scaling = (1, float(sb.cur_metric)/sb.init_metric)
            loc = multvec(sb.gm.ts(), (sb.offset, sb.shift))
        image = pygame.Surface(sb.gm.ts()).convert_alpha()
        image.fill((0,0,0,0))
        s_full = pygame.Surface( addvec(sb.bar_shape,2) ).convert_alpha()
        s_curr = pygame.Surface( sb.bar_shape ).convert_alpha()
        s_full.fill(sb.bg_color)
        s_curr.fill(sb.color)
        ppos = multvec(sb.gm.ts(), new_tpos)
        image.blit(s_full, addvec(ppos,loc))
        image.blit(s_curr, addvec(ppos, addvec(loc, 1)))
        return image


    def Reset(sb): pass # All StatusBar fields are reset by the logic.
    def PrepareAction(sb): pass # StatusBar should not reset anything.
    def DoAction(sb): sb.update_position_and_image()



