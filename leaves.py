'''
leaves.py:
Implementations of various kinds of 'leaf' objects that ONLY READ other agents.
- StatusBar is a generic bar that indicates some metric for another agent.
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
# (color) options for Mouse:
MOUSE_GRAD = (180,180,180,255)
MOUSE_GRAD = (60,180,255,230)


class PlayerHighlighter(ae_module.Highlighter):
    ''' Follow the player & indicate current tile. '''
    def __init__(h, gm, player_id): 
        ae_module.Highlighter.__init__(h, gm)
        h.targeter = sensors_module.GetNextReservation(gm, player_id)
        h.targeter.set_state('stateless')
        h.color = (255,255,255,130)
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
                species=sb.species, img_str='bar '+str(sb.color))
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

    def Reset(sb): pass 
    def PrepareAction(sb): sb.targeter.rescan() 
    # ^ Careful! Rescans can be easily forgotten and omitted for fiendish bugs.
    # Consider instead making the targeter reference the agent's sensor, whose
    # updating is already in place.
    def DoAction(sb): sb.update_position()



