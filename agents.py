'''
agents.py:
Implementations of various kinds of agents:
- Player represents a human controllable player
- AIAgent represents a pokemon AI whose actions are independently, 
    internally motivated.
- MouseAgent defines aspects that enable interactive mouse control
'''


import pygame, random
import numpy as np

from utilities import *
from logic import *
from abstractEntities import VisualStepAgent
from sensors import GetTPosSensor

''' Magic Numbers '''
# latencies for Player:
PLYR_COLL_WIDTH, PLYR_COLL_SHIFT = 0.4, 0.2
PLYR_IMG_SHIFT_INIT = 0.125
DEFAULT_STEPSIZE = 0.20
PLYR_CATCH_DIST = 0.5
PLYR_COLL_BUF = 1+PLYR_COLL_WIDTH

# Latencies for Pkmn:
PKMN_WANDER_LOW, PKMN_WANDER_HIGH = 1.0,3.0
PKMN_MOVE_LOW, PKMN_MOVE_HIGH = 0.4,0.9

DIRVECS_TO_STR = {(0,1):'u',(1,0):'l',(-1,0):'r',(0,-1):'d'} 

# (color) options for Mouse:
MOUSE_CURSOR_DISPL = 3
MOUSE_GRAD = (180,160,60)
#INIT_POS = (100,100)



class Player(VisualStepAgent):
    def __init__(ego, gm, belt):
        init_tpos = divvec(gm.map_num_tiles,3) 
        init_ppos=multvec(init_tpos,gm.ts())
        VisualStepAgent.__init__(ego, gm, belt_init = belt, init_tpos=init_tpos)
        ego.species='plyr'
        ego.team = '--plyr--'
        ego.stepsize_x, ego.stepsize_y = \
                ego.stepsize = multvec(gm.ts(), DEFAULT_STEPSIZE,int)
        ego._belt = (Belt(gm, ego, 'basic player') if belt=='init' else belt)
        ego._logic = Logic(gm, ego, ego._belt)
        ego.gm.notify_update_agent(ego, img_str='player sprite 7', team=ego.team,\
                            agent_type=ego.species)
        ego.gm.notify_update_agent(ego, tx=init_tpos[X], ty=init_tpos[Y],\
                            px=init_ppos[X], py=init_ppos[Y])
        ego.initialized = True

    ''' Methods: Game Manager to PlayerAgent '''
    def Reset(ego):         ego._logic.Update()
    def PrepareAction(ego): ego._logic.Decide()
    def DoAction(ego):      ego._logic.Implement()

    ''' Method: other Agents to PlayerAgent '''
    def message(ego, header, msg):
        if header=="Someone has caught me":
            ego._belt.add_pkmn(msg)
        etc
        ego.logic.notify('isPlayerActionable', True)
        ego.logic.notify(header, msg)

    ''' Methods: fulfill inheritance. '''
    def set_img(ego, which_img): 
#        print '\tego setting img',which_img
        if (not type(which_img)==int) or not which_img in range(12): \
                raise Exception(which_img, type(which_img))
        ego.gm.notify_image_update(ego, 'player sprite '+str(which_img+1))
    def get_pstep(ego): return multvec(ego.stepsize, ego.gm.smoothing())

    ''' Methods: available to many for read.  ( No need to overwrite 
            move_in_direction for Player(VisualStepAgent)  ) '''
    def moveparams_to_steps(ego,dirs):
        dx = (dirs[RDIR]-dirs[LDIR]) * ego.gm.smoothing() * ego.stepsize[X]
        dy = (dirs[DDIR]-dirs[UDIR]) * ego.gm.smoothing() * ego.stepsize[Y]
        return (dx,dy)
    def get_num_actions(ego): return len(ego._belt.Actions)


class AIAgent(TileAgent):
    def __init__(ai, gm, initloc, **options):
        TileAgent.__init__(ai, gm, initloc)
        ai.primary_delay = 0.3
        ai.species = 'pkmn'
        ai.team = '--wild--'
        ai.stepsize_x, ai.stepsize_y = ai.stepsize = gm.ts()
        ai._belt = Belt(gm, ai, 'wild pokemon', options=options)
        ai._logic = Logic(gm, ai, ai._belt, options)
        ai._logic.update_global('curtid',initloc)
        ai.initialized = True
        ai.pokedex = options['pokedex']
        ai.default_img_offset = multvec(gm.ts(), (0.0,0.3))
        ai.gm.notify_update_agent(ai, img_str='pkmn sprite '+str(ai.pokedex)+'d',
                    team=ai.team, agent_type=ai.species)
#        ai.gm.notify_update_agent(ai, tx=init_tpos[X], ty=init_tpos[Y],\
#                            px=init_ppos[X], py=init_ppos[Y])


    def Reset(ai):         ai._logic.Update()
    def PrepareAction(ai): ai._logic.Decide()
    def DoAction(ai):      ai._logic.Implement()

    def set_img(ai, which_img, reset=None): 
#        print '\tai setting img',which_img
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

        #h.redraw(prev_tpos)
    def get_pstep(ai): return ai.gm.ts()




class Highlighter(TileAgent):
    ''' An abstract highlighter class. Provide the <targeter> a sensor that
        returns a TPOS to put this highlighter on. '''
    def __init__(h, gm):
        TileAgent.__init__(h, gm, (0,0))
        h.default_color = (0,0,0,255)
        h.species='target'
        h.team = '--targets--'
        h.image = pygame.Surface(gm.tile_size).convert_alpha()
        h.prev_position = (0,0)
        h.targeter = None;
        h.gm.notify_update_agent(h, tx=0,ty=0,px=0,py=0,\
                    team=h.team, agent_type=h.species)

    def update_position_and_image(h): 
        prev_tpos = h.prev_position
        new_tpos = h.targeter.sense()
        h.draw_highlight(new_tpos)
#        h.redraw(prev_tpos)
        h.prev_position = new_tpos

    def draw_highlight(h, tile_location):
        try:
            r,g,b,a = h.color
        except:
            r,g,b,a = h.default_color
        image = pygame.Surface(h.gm.ts()).convert_alpha()
        image.fill((0,0,0,0))
        tx,ty = h.gm.tile_size
        tx = tx-2; ty=ty-2
        M = MOUSE_CURSOR_DISPL = 1; # stub!
#        for i in [1,2,3]:
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

#    def redraw(h, former): 
#        h.gm.display.queue_E_img( *h.display_parameters )
#        h.gm.display.queue_reset_tile(former)

    def Reset(h): pass
    def PrepareAction(h): h.targeter.rescan()
    def DoAction(h): h.update_position_and_image()


class PlayerHighlighter(Highlighter):
    def __init__(h, gm): 
        Highlighter.__init__(h, gm)
        h.targeter = GetTPosSensor(gm, agent_id = h.gm.Agents['Player'].uniq_id)
        h.targeter.set_state('stateless')
        h.color = (60,120,180,60)
        h.gm.notify_image_update(h, 'targ '+str(h.color), h.draw_highlight((0,0)))
        h.gm.notify_update_agent(h, img_str = 'targ '+str(h.color))


class MouseTarget(Highlighter):
    def __init__(h, gm): 
        Highlighter.__init__(h, gm)
        h.targeter = GetMouseTIDSensor(gm)
        h.targeter.set_state('stateless')
        h.color=h.default_color
        h.gm.notify_image_update(h, 'targ '+str(h.color), h.draw_highlight((0,0)))
        h.gm.notify_update_agent(h, img_str = 'targ '+str(h.color))



#
#
#
#
#
#
#
#class AIAgent(Agent):
#    ''' AI class: a type of Agent that represents any(?) AI NPC with 
#        dynamic behavior. Currently this is intended to be specifically & only
#        for PKMN, either friendly or not, with extension to NPC 'players'
#        pending necessity, at which point hopefully the design options 
#        will be more clear. '''
#    def __init__(ai, gm, team, options): 
#        Agent.__init__(ai, gm, team)
#
#        which_pkmn    = options['which_pkmn']
#        init_pos      = options['pos']
#        ai.stepsize_x = options['stepsize_x']
#        ai.stepsize_y = options['stepsize_y']
#        ai.mv_range   = options['move_range'].split('_')
#        ai.move_speed = options['move_speed']
#        ai.init_shift = options['init_shift']
#        ai.catch_threshold = options['catch_threshold']
#        ai.max_health = int(options['base_health'] * (1 if team=='plyr' else 0.8))
#        ai.cur_health = ai.max_health
#
#        ai.string_sub_class = 'pkmn'
#        ai.pkmn_id = -1
#        ai.snooze=0.0
#        ai.pkmn_id = int(which_pkmn)
#        ai.coll_check_range = (ai.mv_range[0], float(ai.mv_range[1]))
#        ai.set_pkmn_img('d')
#        ai.set_tpos(init_pos)
#        ai.move_ppos(ai.init_shift)
#
#        ai.gm.notify_new(ai)
#        ai.gm.notify_move(ai, ai.get_position())
#
#        ai.catch_counter = 0
#        ai.is_being_caught = False
#        ai.was_caught = False
#        ai.needs_updating = False
#        ai.free_to_act = False
#        ai.avoided_catch = False
#        ai.flags = [ai.catch_counter, ai.is_being_caught, ai.was_caught,  ai.needs_updating,\
#                ai.free_to_act, ai.avoided_catch]
#
#
#    def set_pkmn_img(ai, _dir, whitened=None):
#        if ai.pkmn_id<0: raise Exception('internal: id not set')
#        if type(_dir)==list: _dir = _dir.index(1)
#        if type(_dir)==int:
#            _dir = {UDIR:'u', LDIR:'l', DDIR:'d', RDIR:'r'}[_dir]
#        if ai.img_id==_dir and whitened==None: return
#        basename = 'pkmn sprite '+str(ai.pkmn_id)+_dir
#        if whitened == None:
#            ai.spr.image = ai.gm.imgs[basename]
#        if whitened == 'half whitened':
#            ai.spr.image = ai.gm.imgs[basename+' half whitened']
#        if whitened == 'full whitened':
#            ai.spr.image = ai.gm.imgs[basename+' full whitened']
#        ai.img_id = _dir
#        ai.spr.dirty=1
#        ai.last_taken_action = _dir
#
#
#    ''' _choose_action: a core element of the AI system. Chooses which action to
#        take based on any factors. '''
#    def _choose_action(ai):
#        return 'wander2'
#        if ai.team == ai.gm.Plyr.team and \
#            dist(ai.gm.Plyr.get_tile_under(), ai.get_tile_under(),2)>2.5:
#            return 'move_towards_player'
#        else:
#            return 'wander'
#
#    ''' Agent workflow: After an act, and the frame finishes, other entities may
#        need to do something to/with this agent. So, a messaging service is 
#        implemented to facilitate that. Then, before this agent is free to alter
#        the world in any way with act, it must go though all its messsages. This 
#        system is maintained by flags. '''
#
#    ''' Interface: Public method for changing this pkmn's state and behavior. '''
#    def send_message(ai, msg, from_who=None):
#        ai.needs_updating = True
#        print '<>',msg
#        if msg=='getting caught':
#            if ai.avoided_catch:
#                ai.is_being_caught = False
#                ai.free_to_act=True
#                ai.caught_by_what = None
#            elif ai.catch_counter==0:
#                ai.is_being_caught = True
#                ai.free_to_act=False
#                ai.caught_by_what = from_who
#                ai.avoided_catch = False
#        else: 
#            ai.is_being_caught = False
#        if msg=='initialized as free':
#            ai.free_to_act=True
#
#    ''' Interface: Call update_state before acting, else failure. '''
#    def update_state(ai):
#        if ai.was_caught: # This pkmn is no longer interactive
#            pass
#        elif ai.avoided_catch:
#            ai.set_pkmn_img(ai.last_taken_action, whitened='Not whitened')
#            ai.is_being_caught = False
#            ai.avoided_catch = False  
#        elif ai.is_being_caught:
#            #print ai.catch_counter, ai.catch_threshold
#            if ai.caught_by_what.how_open() > 1 or (ai.free_to_act and \
#                            not ai.needs_updating):
#                ai.avoided_catch = True  
#                ai.is_being_caught = False  
#                ai.catch_counter = 0
#            else:
#                ai.catch_counter += 1
#                ai.set_pkmn_img(ai.last_taken_action, 'half whitened')
#            # Set up getting-caught system.
#    
#    def _act_accordingly(ai):
#        if ai.is_being_caught and not ai.avoided_catch \
#                    and ai.catch_counter >= ai.catch_threshold:
#            print '\t\tfoo'
#            ai.is_being_caught = False
#            ai.was_caught = True
#            ai.set_pkmn_img(ai.last_taken_action, 'full whitened')
#            ai.snooze = ai.move_speed
#        elif ai.was_caught: # pause while getting stored 
#            ai.gm.Plyr.send_message("Someone has caught me", ai)
#            ai.kill_this_pkmn()
#        else:
#            ai.free_to_act=True
#
#
#    ''' Interface: Call this when the entity is presumably ready to perform. '''
#    def act(ai, debug=False): 
#        if debug: 
#            ai.flags = [ai.catch_counter, ai.is_being_caught, ai.was_caught,\
#                        ai.needs_updating, ai.free_to_act, ai.avoided_catch]
#            if np.random.rand()<0.1:
#                print 'catch_counter // is_being_caught // was_caught // ',
#                print 'needs_updating // free_to_act // avoided_catch'
#            print ai.flags
#
#        # First, check if updating is needed.
#        if not ai.needs_updating: ai.update_state()
#        ai.needs_updating = False
#
#        # Next, if the AI has its agency, first pause for sake of frames/etc.
#        if ai.snooze>=0: 
#            ai.snooze -= 1
#            return False
#        ai.snooze=0.0 # normalize 
#
#        # Next, if this AI's agency is restricted, do as such:
#        ai._act_accordingly()
#        if not ai.free_to_act: return False
#
#        # Finally, nothing is in the way of letting this agent act freely:
#        decision = ai._choose_action()
#        if decision=='wander': return ai._take_action_Wander()
#        if decision=='wander2': return ai._take_action_Wander_2()
#        if decision=='move_towards_player': 
#            return ai._take_action_Movetowards(ai.gm.Plyr)
#
#    def _take_action_Movetowards(ai, target_Agent):
#        goal_vec = _sub_aFb(ai.get_tile_under(), ai.gm.Plyr.get_tile_under())
#        ideal = []; not_ideal = []
#        if goal_vec[X]>=0: ideal.append(RDIR)
#        if goal_vec[X]<=0: ideal.append(LDIR)
#        if goal_vec[Y]<=0: ideal.append(UDIR)
#        if goal_vec[Y]>=0: ideal.append(DDIR)
#        random.shuffle(ideal); random.shuffle(not_ideal);
#        moved_yet = False
#        for vid in ideal:
#            vec = [0]*len(DIRECTIONS); vec[vid]=1
#            if (not moved_yet) and sum(ai.validate_move(vec))>0:
#                ai.move_tpos(ai.moveparams_to_steps(vec))
#                raise Exception('section todo')
#                ai.set_pkmn_img(vec)
#                ai.last_taken_action = vec
#                moved_yet = True
#
#        random_snooze = np.random.uniform(PKMN_MOVE_LOW, PKMN_MOVE_HIGH)
#        ai.snooze = ai.snooze + ai.move_speed*random_snooze
#        return moved_yet
#        # For now, if not ideal, don't move at all.
#
#    def _take_action_Wander_2(ai):
#        poss_actions = [addvec(ai.get_position(), d) for d in DIR_TILE_VECS]
#        valid_pos = ai.gm.get_multitiles(poss_actions, 'block_pkmn')
#        if len(valid_pos)==0: return False
#        choice = random.choice(valid_pos)
#        #ai.set_pkmn_img(DIRVECS_TO_STR[sub_aFb(choice, tpos)])
#        ai.set_pkmn_img(DIRVECS_TO_STR[sub_aFb(choice, ai.get_position())])
#        ai.set_ppos( addvec(multvec(choice, ai.gm.tile_size), ai.init_shift))
#        ai.gm.notify_move(ai, ai.get_position())
#        ai.snooze += ai.move_speed*np.random.uniform(PKMN_WANDER_LOW, PKMN_WANDER_HIGH)
#        return True
#        
#
#    def _take_action_Wander(ai):
#        poss_actions = [1,1,1,1]
#        valid_actions =ai.validate_move(poss_actions) # restrict if invalid
#        optns = list(range(len(poss_actions)))
#        random.shuffle(optns)
#        did_i_move = False
#        for i in optns:
#            if valid_actions[i]==0: continue
#            vec = [0]*len(valid_actions)
#            vec[i]=1
#            ai.move_tpos(ai.moveparams_to_steps(vec), no_log=True)
#            ai.gm.notify_move(ai, ai._ppos_to_tpos(ai.get_ppos_rect().midbottom))
#            #ai.set_pkmn_img(vec, 'whitened')
#            ai.set_pkmn_img(vec)
#            did_i_move=True
#            ai.last_taken_action=vec
##            print "Pkmn's tile under:", ai.get_tpos()
#                        
#            break
#        random_snooze = np.random.uniform(PKMN_WANDER_LOW, PKMN_WANDER_HIGH)
#        ai.snooze = ai.snooze + ai.move_speed*random_snooze
#        return did_i_move
#
#    def moveparams_to_steps(ai, dirs): 
#        dx = (dirs[RDIR]-dirs[LDIR]) * ai.gm.smoothing * ai.stepsize_x
#        dy = (dirs[DDIR]-dirs[UDIR]) * ai.gm.smoothing * ai.stepsize_y
#        return (dx,dy)
#
#    def kill_this_pkmn(ai):
#        ai.gm.ai_entities.remove(ai)
#        ai.gm.agent_entities.remove(ai)
#        if ai.team=='enemy1':
#            ai.gm.enemy_team_1.remove(ai)
#        #ai.gm.notify_move(ai.get_tpos(), NULL_POSITION, ai.uniq_id)
#        ai.gm.notify_kill(ai)
#
#        # TODO: If I am on a team, remove me from that team's master agent...
#        del ai
#
#class MouseAgent(GhostEntity):
#    ''' Mouse: a GhostEntity full with position and image but that should
#        not interact directly with any other Agents.
#        While still under design, the initial idea is that the mouse will
#        indirectly signal other entities by updating the game manager's 
#        databases and queues.    '''
#    def __init__(mouse, gm):
#        GhostEntity.__init__(mouse, gm)
#        mouse.string_sub_class = 'mouse target'
#        mouse.gm.agent_entities.append(mouse)
#        mouse.team = '--mouse--'
#        mouse.spr.image = pygame.Surface(gm.tile_size).convert_alpha()
#        mouse.update_position(mouse.gm.world_pcenter)
#        mouse.gm.notify_new(mouse)
#        mouse.gm.move_effects.append(mouse)
#
#        mouse._logic = Logic(gm, mouse)
#
#
#               
#    def update_position(mouse, targ_ppos, cursor='default'):
#        #targ_pos = mouse.get_tile_under((targ_ppos[X]+1,targ_ppos[Y]+1))
#        #mouse._notify_gm_move(prev_pos)
##        mouse.gm.notify_move(mouse.get_ppos(), targ_ppos, mouse.uniq_id, mouse.team, \
##                mouse.string_sub_class)
#        prev_pos = mouse.get_tpos()
#        targ_pos = mouse.get_tpos((targ_ppos[X]+1,targ_ppos[Y]+1))
#        mouse._set_tpos(targ_pos)
#        mouse.set_cursor(cursor)
#        if not prev_pos==targ_pos:
#            mouse.gm.update_hud()
#    def update_move(mouse): mouse._logic.root_ap.implement()
#
#    def set_cursor(mouse, mode):
#        # puts the desired cursor mode sprite at the current pos
#        try:
#            targ_color = {
#                    'default':      (140,40,240), 
#                    'hud action':   (200,200,255), \
#                    'bad action':   (255,60,0), \
#                    'good action':  (60,155,0) }[mode]
#        except: print "Mouse mode not recognized:", mode
#
##       mouse.spr.image.fill((140,100,240,180))
#        mouse.draw_target( targ_color )
##       mouse.spr.image = pygame.image.load('./resources/cursor1.png')
#        mouse.spr.image.convert_alpha()
#        mouse.spr.dirty=1
#
#    def draw_target(mouse, (r,g,b) ):
#        mouse.spr.image.fill((0,0,0,0))
#        tx,ty = mouse.gm.tile_size
#        tx = tx-2; ty=ty-2
#        M = MOUSE_CURSOR_DISPL
##        for i in [1,2,3]:
#        for i in [1,3,4,5]:
#            for d in DIRECTIONS:
#                rect_size = { UDIR: (tx-2*(i+1)*M, M),   DDIR: (tx-2*(i+1)*M, M),
#                              LDIR: (M, ty-2*(i+1)*M),   RDIR: (M, ty-2*(i+1)*M) }[d]
#                location = {
#                    UDIR: ((i+1)*M, i*M),        DDIR: ((i+1)*M, ty-(i+1)*M), 
#                    LDIR: (i*M, (i+1)*M),    RDIR: (tx-(i+1)*M, (i+1)*M), }[d]
##                print i, DIRNAMES[d], 'size/loc:',rect_size, location
#                if rect_size[X]<=0 or rect_size[Y]<=0: continue
#                s = pygame.Surface( rect_size ).convert_alpha()
#                try:
#                    s.fill( (r,g,b, MOUSE_GRAD[i-1]) )
#                except:
#                    s.fill( (r,g,b, MOUSE_GRAD[-1]) )
#                mouse.spr.image.blit(s, location)
#        s = pygame.Surface( (4,4) ).convert_alpha()
#        s.fill( (r,g,b, 255) )
#        mouse.spr.image.blit(s, (tx/2-2,ty/2-2) )
#
#
#
#
#
#
#
#


################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################


# 8/13: everthing below the WALL has been checked and verified for new paradigm.



