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
from abstractEntities import Agent, GhostEntity
from belt import Belt

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


class Player(Agent):
    ''' PLAYER class: a type of Agent that is suited to represent (the single)
        player object. Attempt is to keep all relevant fields here, out of 
        the game manager's burden. Core unique attribute(s): tailored 
        animation dependent on user input. 
        '''
    def __init__(ego, gm):
        Agent.__init__(ego, gm, 'plyr')
        # Set up internal components:
        ego.string_sub_class = 'plyr'
        ego.coll_check_range = ('eucl',1.5) # check 8 tiles surrounding
        ego.spr = pygame.sprite.DirtySprite()
        ego.gm.agent_entities.append(ego)
        #ego.spr.add( gm.plyr_team )
        ego.plyr_step_cycler = 0     # animation counter for player sprite
        ego.n_plyr_anim = gm.n_plyr_anim
        ego.n_plyr_dirs = gm.n_plyr_dirs
        ego.dirs_to_steps = ego.moveparams_to_steps
        ego.stepsize_x = DEFAULT_STEPSIZE * ego.gm.tile_x_size
        ego.stepsize_y = DEFAULT_STEPSIZE * ego.gm.tile_y_size
        #ego.notify_gm_move(NULL_POSITION)

        # Set up game state components:
        ego._belt = Belt(gm, ego)

        ego.set_plyr_img(DVEC, 'init-shift')
        ego.set_ppos(ego.gm.world_pcenter)
        ego.init_shift = (0,-int(PLYR_IMG_SHIFT_INIT*ego.gm.tile_y_size//1))
        ego.move_ppos(ego.init_shift)
        ego.set_plyr_actionable('init')
        ego.gm.notify_new(ego)
        
        ego.catch_box = multvec(gm.tile_size, PLYR_CATCH_DIST)
        ego.catch_rect = pygame.Rect((0,0), ego.catch_box)

    def did_catch(ego, query_throw, query_catch):
        ego.catch_rect.center = query_throw
#        ego.catch_rect = pygame.Rect(addvec(ego.get_ppos(), \
#                                     divvec(ego.catch_box, 2)), ego.catch_box)
        return ego.catch_rect.collidepoint(query_catch)

    def _update_coll(ego):
        ego.coll = ego.gm.deflate(ego.ppos_rect, PLYR_COLL_WIDTH, PLYR_COLL_SHIFT)

    def set_plyr_img(ego, dirs, mode=None, init_ppos=None):
        if not any(dirs): dirs[DDIR] = True # default, face down.
        ego.plyr_step_cycler = {'moving': ego.plyr_step_cycler+1, 'stopped':0,\
                'init-shift':0, 'init-noshift':0}[mode] % ego.gm.n_plyr_anim
        new_img_id = dirs.index(True)*ego.gm.n_plyr_anim+1+ego.plyr_step_cycler
        if ego.img_id==new_img_id: return
        ego.img_id = new_img_id 

        if mode[:4]=='init':
            ego.spr.image = ego.gm.imgs['player sprite 7']
        else:
            ego.spr.image = ego.gm.imgs['player sprite ' + str(ego.img_id)]
        ego.spr.rect = ego.spr.image.get_rect()
        ego.spr.rect = ego.get_ppos_rect()

    def moveparams_to_steps(ego,dirs):
        dx = (dirs[RDIR]-dirs[LDIR]) * ego.gm.smoothing * ego.stepsize_x
        dy = (dirs[DDIR]-dirs[UDIR]) * ego.gm.smoothing * ego.stepsize_y
        return (dx,dy)

    def _pick_rndm_action(ego, dirs): # subCASE: pick one of the options
        optns = [i for i in range(len(dirs)) if next_e[i]==1]
        next_e = [False]*len(dirs)
        next_e[random.choice(optns)] = True #...randomly
        return next_e

    def plyr_move(ego):
        prev_e = ego.gm.prev_e[:4]
        all_poss_targs = [ego._ppos_to_tpos(addvec(ego.get_center(), \
              multvec(ego.dirs_to_steps(d),PLYR_COLL_BUF))) for d in DIR_LONG_VECS]
        next_e_try = ego.gm.events[:4]
        curr_occs = ego.gm.get_tile_occupants()
        for option in EVENTS:
            if all_poss_targs[option]==ego.get_position(): continue
            dvec = sub_aFb(all_poss_targs[option], ego.get_position())
            if not next_e_try[option]: 
                continue
            ents, map_t = ego.gm.query_tile(all_poss_targs[option], 'tx,ty,block_plyr')
            for e in ents:
                if e[0]==u'pkmn' and not e[2]==u'plyr':
                    next_e_try[option]=False
            if not len(map_t)==1:
                raise Exception('not impl: multiple tiles!')
            if map_t[0][2]==u'true':  # blocks
                next_e_try[option]=False

        next_poss = Events_To_Vec(ego.gm.events[:4])


        next_e = next_e_try
#        print np.logical_xor(ego.gm.events[:4],next_e), ego.get_position()
#        print prev_e, next_e 
#
#
#
#        print ego.get_position(), ego.gm.events[:4]
#        for dvec in next_poss:
#            poss_targs += [{'d':dvec, 'pos':addvec(ego.get_position(), dvec)}]
#        print next_poss, poss_actions
#        valid_actions = ego.gm.get_multitiles(poss_targs['pos'], 'block_plyr')
#        next_e = Vec_To_Event(valid_actions)
#        print prev_e, next_e

        #next_e = ego.validate_move(ego.gm.events, debug=True) # restrict if invalid
#        next_e = ego.validate_move(ego.gm.events[:4]) # restrict if invalid
#        #print prev_e, next_e, Events_To_Vec(next_e)
#        tpos = ego._ppos_to_tpos(ego.get_center())
#        poss_actions = [addvec(tpos, d) for d in Events_To_Vec(next_e)]
#        if len(poss_actions)==0: return False
#        valid_actions = ego.gm.get_multitiles(poss_actions, 'block_plyr')
#        if len(valid_actions)==0: return False
##        print poss_actions, valid_actions
#        print ego.gm.get_tile_occupants()
#        next_e 
##        if len(valid_pos)==0: return False

        move_to_pos = (0,0)
        new_img = None
        retval = 'SENTINEL'
        if not any(prev_e) and any(next_e): # CASE started walking
            if sum(next_e)>1:
                next_e = ego._pick_rndm_action(next_e)
            move_to_pos = ego.dirs_to_steps(next_e)
            new_img = (next_e, 'moving')
            ego.gm.prev_e = next_e
            retval = True
        elif any(prev_e) and any(next_e) and not prev_e==next_e: # CASE walking & turning
            if sum(next_e)>1: # subCASE try: get the new option
                new = [a and not b for a,b in zip(next_e, prev_e)]
                if sum(new)>1: # subCASE except: pick one of the new options
                    optns = [i for i in range(ego.n_plyr_dirs) if new[i]==1]
                    new = [False]*ego.n_plyr_dirs
                    new[random.choice(optns)] = True
#                ego.move_ppos(ego.dirs_to_steps(new))
                move_to_pos = ego.dirs_to_steps(new)
#                ego.set_plyr_img(new, 'moving')
                new_img = (new, 'moving')
                retval = True
            else:
                move_to_pos = ego.dirs_to_steps(next_e)
                new_img = (next_e, 'moving')
                ego.gm.prev_e = next_e
                retval = True
        elif any(prev_e) and prev_e==next_e: # CASE continue walking
            if sum(prev_e)>1: raise Exception("Internal: prev dir")
            move_to_pos = ego.dirs_to_steps(next_e)
            new_img = (next_e, 'moving')
            retval = True
        elif any(prev_e) and not any(next_e): # CASE stop walking
            if sum(prev_e)>1: 
                next_e = ego._pick_rndm_action(prev_e)
                raise Exception("Internal: prev dir")
            new_img = (prev_e, 'stopped')
            ego.spr.dirty=1
            retval = True # last update
        elif (not any(prev_e)) and (not any(next_e)): # CASE continue stopped
            new_img = (prev_e, 'stopped')
            retval = False
        else: raise Exception("Internal error: plyr move")

        if retval==False: return False
        if retval=='SENTINEL': raise Exception()

        ego.move_ppos(move_to_pos)
        if not new_img==None: ego.set_plyr_img(new_img[0], new_img[1])
        ego.gm.notify_move(ego, ego.get_bottom())
        return retval


    def set_plyr_actionable(ego, b):
        try:
          if b and ego._is_plyr_actionable: 
            raise Exception("Player is already actionable!")
        except: pass
        ego._is_plyr_actionable=b
    def is_plyr_actionable(ego):  return ego._is_plyr_actionable

    ''' Interface: Public method for changing this Plyr's state and behavior. '''
    def send_message(ego, msg, from_who=None):
        if msg=="Someone has caught me":
            ego._belt.add_pkmn(from_who)

    def get_pkmn_at_tpos(ego, t):
        return
        #print ego.gm.get_tile_occupants(t)
        for ent in ego.gm.ai_entities:
            print '\t',ent.get_tpos(), t
        x= [ent for ent in ego.gm.ai_entities if ent.get_tpos()==t]
        try:
            print x[-1].get_tpos()
        except: pass
    
    def do_primary_action(ego, mousepos):
        if not ego._is_plyr_actionable: return 
        ego._is_plyr_actionable = False
##        mouse_tile = ego.get_tile_under(mousepos)
#        mouse_tile = ego.get_tpos(mousepos)
#        agents = ego.get_pkmn_at_tpos(mouse_tile)
#        print 'here:',agents



class AIAgent(Agent):
    ''' AI class: a type of Agent that represents any(?) AI NPC with 
        dynamic behavior. Currently this is intended to be specifically & only
        for PKMN, either friendly or not, with extension to NPC 'players'
        pending necessity, at which point hopefully the design options 
        will be more clear. '''
    def __init__(ai, gm, team, options): 
        Agent.__init__(ai, gm, team)

        which_pkmn    = options['which_pkmn']
        init_pos      = options['pos']
        ai.stepsize_x = options['stepsize_x']
        ai.stepsize_y = options['stepsize_y']
        ai.mv_range   = options['move_range'].split('_')
        ai.move_speed = options['move_speed']
        ai.init_shift = options['init_shift']
        ai.catch_threshold = options['catch_threshold']
        ai.max_health = int(options['base_health'] * (1 if team=='plyr' else 0.8))
        ai.cur_health = ai.max_health

        ai.string_sub_class = 'pkmn'
        ai.pkmn_id = -1
        ai.snooze=0.0
        ai.pkmn_id = int(which_pkmn)
        ai.coll_check_range = (ai.mv_range[0], float(ai.mv_range[1]))
        ai.set_pkmn_img('d')
        ai.set_tpos(init_pos)
        ai.move_ppos(ai.init_shift)

        ai.gm.notify_new(ai)
        ai.gm.notify_move(ai, ai.get_position())

        ai.catch_counter = 0
        ai.is_being_caught = False
        ai.was_caught = False
        ai.needs_updating = False
        ai.free_to_act = False
        ai.avoided_catch = False
        ai.flags = [ai.catch_counter, ai.is_being_caught, ai.was_caught,  ai.needs_updating,\
                ai.free_to_act, ai.avoided_catch]


    def set_pkmn_img(ai, _dir, whitened=None):
        if ai.pkmn_id<0: raise Exception('internal: id not set')
        if type(_dir)==list: _dir = _dir.index(1)
        if type(_dir)==int:
            _dir = {UDIR:'u', LDIR:'l', DDIR:'d', RDIR:'r'}[_dir]
        if ai.img_id==_dir and whitened==None: return
        basename = 'pkmn sprite '+str(ai.pkmn_id)+_dir
        if whitened == None:
            ai.spr.image = ai.gm.imgs[basename]
        if whitened == 'half whitened':
            ai.spr.image = ai.gm.imgs[basename+' half whitened']
        if whitened == 'full whitened':
            ai.spr.image = ai.gm.imgs[basename+' full whitened']
        ai.img_id = _dir
        ai.spr.dirty=1
        ai.last_taken_action = _dir


    ''' _choose_action: a core element of the AI system. Chooses which action to
        take based on any factors. '''
    def _choose_action(ai):
        return 'wander2'
        if ai.team == ai.gm.Plyr.team and \
            dist(ai.gm.Plyr.get_tile_under(), ai.get_tile_under(),2)>2.5:
            return 'move_towards_player'
        else:
            return 'wander'

    ''' Agent workflow: After an act, and the frame finishes, other entities may
        need to do something to/with this agent. So, a messaging service is 
        implemented to facilitate that. Then, before this agent is free to alter
        the world in any way with act, it must go though all its messsages. This 
        system is maintained by flags. '''

    ''' Interface: Public method for changing this pkmn's state and behavior. '''
    def send_message(ai, msg, from_who=None):
        ai.needs_updating = True
        print '<>',msg
        if msg=='getting caught':
            if ai.avoided_catch:
                ai.is_being_caught = False
                ai.free_to_act=True
                ai.caught_by_what = None
            elif ai.catch_counter==0:
                ai.is_being_caught = True
                ai.free_to_act=False
                ai.caught_by_what = from_who
                ai.avoided_catch = False
        else: 
            ai.is_being_caught = False
        if msg=='initialized as free':
            ai.free_to_act=True

    ''' Interface: Call update_state before acting, else failure. '''
    def update_state(ai):
        if ai.was_caught: # This pkmn is no longer interactive
            pass
        elif ai.avoided_catch:
            ai.set_pkmn_img(ai.last_taken_action, whitened='Not whitened')
            ai.is_being_caught = False
            ai.avoided_catch = False  
        elif ai.is_being_caught:
            #print ai.catch_counter, ai.catch_threshold
            if ai.caught_by_what.how_open() > 1 or (ai.free_to_act and \
                            not ai.needs_updating):
                ai.avoided_catch = True  
                ai.is_being_caught = False  
                ai.catch_counter = 0
            else:
                ai.catch_counter += 1
                ai.set_pkmn_img(ai.last_taken_action, 'half whitened')
            # Set up getting-caught system.
    
    def _act_accordingly(ai):
        if ai.is_being_caught and not ai.avoided_catch \
                    and ai.catch_counter >= ai.catch_threshold:
            print '\t\tfoo'
            ai.is_being_caught = False
            ai.was_caught = True
            ai.set_pkmn_img(ai.last_taken_action, 'full whitened')
            ai.snooze = ai.move_speed
        elif ai.was_caught: # pause while getting stored 
            ai.gm.Plyr.send_message("Someone has caught me", ai)
            ai.kill_this_pkmn()
        else:
            ai.free_to_act=True


    ''' Interface: Call this when the entity is presumably ready to perform. '''
    def act(ai, debug=True): 
        if debug: 
            ai.flags = [ai.catch_counter, ai.is_being_caught, ai.was_caught,\
                        ai.needs_updating, ai.free_to_act, ai.avoided_catch]
            if np.random.rand()<0.1:
                print 'catch_counter // is_being_caught // was_caught // ',
                print 'needs_updating // free_to_act // avoided_catch'
            print ai.flags

        # First, check if updating is needed.
        if not ai.needs_updating: ai.update_state()
        ai.needs_updating = False

        # Next, if the AI has its agency, first pause for sake of frames/etc.
        if ai.snooze>=0: 
            ai.snooze -= 1
            return False
        ai.snooze=0.0 # normalize 

        # Next, if this AI's agency is restricted, do as such:
        ai._act_accordingly()
        if not ai.free_to_act: return False

        # Finally, nothing is in the way of letting this agent act freely:
        decision = ai._choose_action()
        if decision=='wander': return ai._take_action_Wander()
        if decision=='wander2': return ai._take_action_Wander_2()
        if decision=='move_towards_player': 
            return ai._take_action_Movetowards(ai.gm.Plyr)

    def _take_action_Movetowards(ai, target_Agent):
        goal_vec = _sub_aFb(ai.get_tile_under(), ai.gm.Plyr.get_tile_under())
        ideal = []; not_ideal = []
        if goal_vec[X]>=0: ideal.append(RDIR)
        if goal_vec[X]<=0: ideal.append(LDIR)
        if goal_vec[Y]<=0: ideal.append(UDIR)
        if goal_vec[Y]>=0: ideal.append(DDIR)
        random.shuffle(ideal); random.shuffle(not_ideal);
        moved_yet = False
        for vid in ideal:
            vec = [0]*len(DIRECTIONS); vec[vid]=1
            if (not moved_yet) and sum(ai.validate_move(vec))>0:
                ai.move_tpos(ai.moveparams_to_steps(vec))
                raise Exception('section todo')
                ai.set_pkmn_img(vec)
                ai.last_taken_action = vec
                moved_yet = True

        random_snooze = np.random.uniform(PKMN_MOVE_LOW, PKMN_MOVE_HIGH)
        ai.snooze = ai.snooze + ai.move_speed*random_snooze
        return moved_yet
        # For now, if not ideal, don't move at all.

    def _take_action_Wander_2(ai):
        poss_actions = [addvec(ai.get_position(), d) for d in DIR_TILE_VECS]
        valid_pos = ai.gm.get_multitiles(poss_actions, 'block_pkmn')
        if len(valid_pos)==0: return False
        choice = random.choice(valid_pos)
        #ai.set_pkmn_img(DIRVECS_TO_STR[sub_aFb(choice, tpos)])
        ai.set_pkmn_img(DIRVECS_TO_STR[sub_aFb(choice, ai.get_position())])
        ai.set_ppos( addvec(multvec(choice, ai.gm.tile_size), ai.init_shift))
        ai.gm.notify_move(ai, ai.get_position())
        ai.snooze += ai.move_speed*np.random.uniform(PKMN_WANDER_LOW, PKMN_WANDER_HIGH)
        return True
        

    def _take_action_Wander(ai):
        poss_actions = [1,1,1,1]
        valid_actions =ai.validate_move(poss_actions) # restrict if invalid
        optns = list(range(len(poss_actions)))
        random.shuffle(optns)
        did_i_move = False
        for i in optns:
            if valid_actions[i]==0: continue
            vec = [0]*len(valid_actions)
            vec[i]=1
            ai.move_tpos(ai.moveparams_to_steps(vec), no_log=True)
            ai.gm.notify_move(ai, ai._ppos_to_tpos(ai.get_ppos_rect().midbottom))
            #ai.set_pkmn_img(vec, 'whitened')
            ai.set_pkmn_img(vec)
            did_i_move=True
            ai.last_taken_action=vec
#            print "Pkmn's tile under:", ai.get_tpos()
                        
            break
        random_snooze = np.random.uniform(PKMN_WANDER_LOW, PKMN_WANDER_HIGH)
        ai.snooze = ai.snooze + ai.move_speed*random_snooze
        return did_i_move

    def _update_coll(ai): ai.coll = ai.ppos_rect.copy()

    def moveparams_to_steps(ai, dirs): 
        dx = (dirs[RDIR]-dirs[LDIR]) * ai.gm.smoothing * ai.stepsize_x
        dy = (dirs[DDIR]-dirs[UDIR]) * ai.gm.smoothing * ai.stepsize_y
        return (dx,dy)

    def kill_this_pkmn(ai):
        ai.gm.ai_entities.remove(ai)
        ai.gm.agent_entities.remove(ai)
        if ai.team=='enemy1':
            ai.gm.enemy_team_1.remove(ai)
        #ai.gm.notify_move(ai.get_tpos(), NULL_POSITION, ai.uniq_id)
        ai.gm.notify_kill(ai)

        # TODO: If I am on a team, remove me from that team's master agent...
        del ai

class MouseAgent(GhostEntity):
    ''' Mouse: a GhostEntity full with position and image but that should
        not interact directly with any other Agents.
        While still under design, the initial idea is that the mouse will
        indirectly signal other entities by updating the game manager's 
        databases and queues.    '''
    def __init__(mouse, gm):
        GhostEntity.__init__(mouse, gm)
        mouse.string_sub_class = 'target'
        mouse.gm.agent_entities.append(mouse)
        mouse.team = '--mouse--'
        mouse.spr.image = pygame.Surface(gm.tile_size).convert_alpha()
        mouse.update_position(mouse.gm.world_pcenter)
        mouse.gm.notify_new(mouse)

               
    def update_position(mouse, targ_ppos, cursor='default'):
        #targ_pos = mouse.get_tile_under((targ_ppos[X]+1,targ_ppos[Y]+1))
        #mouse._notify_gm_move(prev_pos)
#        mouse.gm.notify_move(mouse.get_ppos(), targ_ppos, mouse.uniq_id, mouse.team, \
#                mouse.string_sub_class)
        prev_pos = mouse.get_tpos()
        targ_pos = mouse.get_tpos((targ_ppos[X]+1,targ_ppos[Y]+1))
        mouse._set_tpos(targ_pos)
        mouse.set_cursor(cursor)
        if not prev_pos==targ_pos:
            mouse.gm.update_hud()

    def set_cursor(mouse, mode):
        # puts the desired cursor mode sprite at the current pos
        try:
            targ_color = {
                    'default':      (140,40,240), 
                    'hud action':   (200,200,255), \
                    'bad action':   (255,60,0), \
                    'good action':  (60,155,0) }[mode]
        except: print "Mouse mode not recognized:", mode

#       mouse.spr.image.fill((140,100,240,180))
        mouse.draw_target( targ_color )
#       mouse.spr.image = pygame.image.load('./resources/cursor1.png')
        mouse.spr.image.convert_alpha()
        mouse.spr.dirty=1

    def draw_target(mouse, (r,g,b) ):
        mouse.spr.image.fill((0,0,0,0))
        tx,ty = mouse.gm.tile_size
        tx = tx-2; ty=ty-2
        M = MOUSE_CURSOR_DISPL
#        for i in [1,2,3]:
        for i in [1,3,4,5]:
            for d in DIRECTIONS:
                rect_size = { UDIR: (tx-2*(i+1)*M, M),   DDIR: (tx-2*(i+1)*M, M),
                              LDIR: (M, ty-2*(i+1)*M),   RDIR: (M, ty-2*(i+1)*M) }[d]
                location = {
                    UDIR: ((i+1)*M, i*M),        DDIR: ((i+1)*M, ty-(i+1)*M), 
                    LDIR: (i*M, (i+1)*M),    RDIR: (tx-(i+1)*M, (i+1)*M), }[d]
#                print i, DIRNAMES[d], 'size/loc:',rect_size, location
                if rect_size[X]<=0 or rect_size[Y]<=0: continue
                s = pygame.Surface( rect_size ).convert_alpha()
                try:
                    s.fill( (r,g,b, MOUSE_GRAD[i-1]) )
                except:
                    s.fill( (r,g,b, MOUSE_GRAD[-1]) )
                mouse.spr.image.blit(s, location)
        s = pygame.Surface( (4,4) ).convert_alpha()
        s.fill( (r,g,b, 255) )
        mouse.spr.image.blit(s, (tx/2-2,ty/2-2) )





class Highligher(GhostEntity):
    def __init__(h, gm):
        GhostEntity.__init__(h, gm)
        h.string_sub_class = 'target'
#        h.gm.environmental_sprites.add(h)
        h.gm.move_effects.append(h)
#        h.gm.environmental_sprites.add(h.spr)
        h.team = '--plyr--'
        h.plyr = gm.Plyr
        h.spr.image = pygame.Surface(gm.tile_size).convert_alpha()
        h.update_position_and_image()
        h.gm.notify_new(h)

    def update_position_and_image(h): 
        prev_pos = h.get_tpos()
        r = h.plyr.ppos_rect
        h._set_tpos(h._ppos_to_tpos(divvec(addvec(r.center, r.midbottom),2)))
        if not prev_pos==h.get_tpos():
            h.draw_highlight()
            h.spr.dirty=1
    def update_move(h): h.update_position_and_image()

    def draw_highlight(h):
        r,g,b,a = (180,0,0,160)
        h.spr.image.fill((0,0,0,0))
        tx,ty = h.gm.tile_size
        tx = tx-2; ty=ty-2
        M = MOUSE_CURSOR_DISPL
#        for i in [1,2,3]:
        for i in [1,3,4,5]:
            for d in DIRECTIONS:
                rect_size = { UDIR: (tx-2*(i+1)*M, M),   DDIR: (tx-2*(i+1)*M, M),
                              LDIR: (M, ty-2*(i+1)*M),   RDIR: (M, ty-2*(i+1)*M) }[d]
                location = {
                    UDIR: ((i+1)*M, i*M),        DDIR: ((i+1)*M, ty-(i+1)*M), 
                    LDIR: (i*M, (i+1)*M),    RDIR: (tx-(i+1)*M, (i+1)*M), }[d]
#                print i, DIRNAMES[d], 'size/loc:',rect_size, location
                if rect_size[X]<=0 or rect_size[Y]<=0: continue
                s = pygame.Surface( rect_size ).convert_alpha()
                try:
                    s.fill( (r,g,b, MOUSE_GRAD[i-1]) )
                except:
                    s.fill( (r,g,b, MOUSE_GRAD[-1]) )
                h.spr.image.blit(s, location)
#        s = pygame.Surface( (4,4) ).convert_alpha()
#        s.fill( (180,0,0,100) )
#        h.spr.image.blit(s, (tx/2-2,ty/2-2) )

