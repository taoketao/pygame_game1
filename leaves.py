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
import abstractEntities as ae_module

''' Magic Numbers '''
# (color) options for Mouse:
MOUSE_GRAD = (180,180,180,255)
MOUSE_GRAD = (60,180,255,230)


class Highlighter(ae_module.TileAgent):
    ''' An abstract highlighter class. Provide the <targeter> a sensor that
        returns a TPOS to put this highlighter on. '''
    def __init__(h, gm):
        TileAgent.__init__(h, gm, (0,0))
        h.default_color = (0,0,0,255)
        h.species='target'
        h.team = '--targets--'
        h.prev_position = (0,0)
        h.targeter = None;
        h.image_offset = (-2,-2)
        h.gm.notify_update_agent(h, tx=0,ty=0,px=0,py=0,\
                    team=h.team, species=h.species)

    def update_position(h): 
        ''' update_position: call every frame to update. '''
        #print 'Sense my tpos by highlighter',h,':',h.targeter.sense()
        h.gm.notify_tmove(h.uniq_id, h.targeter.sense())

    def draw_highlight(h, tile_location):
        '''  Draw a target on specified tile. '''
        try:      r,g,b,a = h.color
        except:   r,g,b,a = h.default_color
        image = pygame.Surface(h.gm.ts()).convert_alpha()
        image.fill((0,0,0,0))
        tx,ty = h.gm.tile_size
        tx = tx-2; ty=ty-2
        M = MOUSE_CURSOR_DISPL = 2; # stub!
        for i in [1,3,6,5]:
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
                s.fill( h.color )
                image.blit( s, addvec(location,1) )
        h.display_parameters = (-1, image, addvec((1,1),\
                        multvec(tile_location,h.gm.ts())))
        return image

    def Reset(h): pass
    def PrepareAction(h): h.targeter.rescan(); return EVAL_T
    def DoAction(h): h.update_position()

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
    def __init__(h, gm, **_unused_args_): 
        ae_module.Highlighter.__init__(h, gm)
        h.targeter = sensors_module.GetMouseTIDSensor(gm)
        h.color= MOUSE_GRAD
        h.gm.notify_image_update(h, 'targ '+str(h.color), h.draw_highlight((0,0)))
        h.gm.notify_update_agent(h, img_str = 'targ '+str(h.color))
        h.past_position=NULL_POSITION
    def update_position(h): # updated to reset HUD tiles
        if not h.past_position == h.targeter.sense():
            h.gm.display.queue_reset_tile(h.past_position, 'tpos')
#            print 'Reset mouseover tile:', h.targeter.sense(), h.past_position
        h.gm.notify_tmove(h.uniq_id, h.past_position)
        h.past_position = h.targeter.sense()

class StatusBar(ae_module.TileAgent):
    ''' An abstract status bar class that pokemon can take on.
        TODO: move this to abstractEntities once completed'''
    def __init__(sb, gm, owner, **options):
        ae_module.TileAgent.__init__(sb, gm, options.get('init_tloc',(0,0)))
        sb.species='bar'
        sb.owner = owner

        # Set fields
        sb.color = { 'b': (110,120,255,255), 'r': (255,0,0,255),\
                'y': (255,255,0,255), 'w':(255,255,255,255)}[\
                options.get('hbcolor','r')]
        sb.metric = options['metric']
        sb.bg_color = (0,0,0,255)
        sb.prev_position = (0,0)
        sb.offset = 2+(BAR_WIDTH+1)*options.get('offset',0) # stack distance 
        sb.shift = 2+(BAR_WIDTH+1)*options.get('shift', 0) # buffer dist from edge
        sb.orientation = options.get('orientation', 'horiz') # vs vertic
        try: 
            sb.init_metric = options['max_'+sb.metric]
            sb.cur_metric = options['cur_'+sb.metric]
        except:
            sb.cur_metric = sb.init_metric = options[sb.metric]
        sb.bar_shape = [BAR_WIDTH];
        sb.bar_shape.insert({'horiz':0, 'vertic':1}[sb.orientation], \
                    sb.init_metric/options.get('vizscale',1))

        # conduct essential initial interactions
        sb.gm.notify_update_agent(sb, team=sb.owner.team,   \
                tx=options.get('init_tloc',(0,0))[X], \
                ty=options.get('init_tloc',(0,0))[Y], \
                species=sb.species, img_str='bar '+str(sb.color))
        sb.gm.notify_image_update(sb, 'bar '+str(sb.color)+str(sb.uniq_id), \
                                      sb.draw_statusbar())
        sb.targeter = sensors_module.GetNextReservation(gm, owner.uniq_id)
        sb.targeter.set_state('stateless')
        sb.targeter.rescan()

        sb.relative_scaling = gm.tile_size[{'horiz':0,'vertic':1}[sb.orientation]]

    def update_position(sb): 
        sb.gm.notify_tmove(sb.uniq_id, sb.targeter.sense())

    def update_metric(sb, amount, delta_or_absolute='delta'):
        if delta_or_absolute=='delta' or amt<0: amount = sb.cur_metric+amount
        elif not delta_or_absolute=='absolute': raise Exception()
        sb.cur_metric = min(sb.init_metric, max(0, amount)) # CAPPED!
        sb.gm.notify_image_update(sb, 'bar '+str(sb.color)+str(sb.uniq_id), \
                                          sb.draw_statusbar())

    def view_metric(sb): return (sb.cur_metric, sb.init_metric)
    def view_pct(sb): return float(sb.cur_metric) / sb.init_metric


    def draw_statusbar(sb):
        scaling_amount = float(0.5*sb.cur_metric)/sb.init_metric # for debugging
#        scaling_amount = float(sb.cur_metric)/sb.init_metric # for debugging
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
    def PrepareAction(sb): 
        sb.targeter.rescan() 
#        print 'STATUS BAR RESET', sb.uniq_id; sb.targeter.sense()
    # ^ Careful! Rescans can be easily forgotten and omitted for fiendish bugs.
    # Consider instead making the targeter reference the agent's sensor, whose
    # updating is already in place.
    def DoAction(sb): sb.update_position()



