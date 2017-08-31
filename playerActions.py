from abstractActions import *
from compositeActions import *
import numpy as np



#-------------#-------------#--------------#--------------#--------------

'''     Player-exclusive logic APs (as of now)   '''


# Pick Newest: using Pushdown automata, maintain newest. 
# This function is not general as-is, but can be cannibalized quite easily.
# Global state update: makes  

class PickNewest(ActionPicker): 
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.components = logic.view('available motions')#.copy()

        ap.logic.update_global("prev motion", 2)
        ap.logic.update_global("mov choice", -1)
        ap.logic.update_global("img choice", 2)


    def find_viability(ap):
        curmove = ap.logic.view('curr move vec') # Todo: receive GM messages for update!
        prev = ap.logic.get_PDA()
        # One: for consistent behavior, use old move if it's still valid.
        if curmove==ap.logic.view('prev move vec'): 
            if prev.find_viability()==EVAL_T:
                return ap.VIABLE()

        # Two: ingest new request into the Pushdown Automata (PDA).
        for index in range(len(curmove)):
            ltr = index_to_ltr[index]
            if curmove[index]:
                if not index==prev.index:
                    ap.logic.push_PDA(index) # key is down
            else:
                ap.logic.pop_PDA(index) # key is up
        new_aut = ap.logic.get_PDA()
        # Three: filter attempted moves for viability
        for act in ap.components.values():
            av = act.find_viability()
            if av==EVAL_F:
                ap.logic.pop_PDA(act.index)
        allowed_top_move = ap.logic.get_PDA()

        # Four: update global fields
        if allowed_top_move.index==-1:
            ap.logic.update_global('mov choice', -1)
            ap.logic.update_global('prev motion', new_aut.index)
            ap.logic.push_PDA(new_aut.index)
        else:
            for key in ['prev motion','img choice','mov choice']:
                ap.logic.update_global(key, allowed_top_move.index)

        return ap.Verify(allowed_top_move)

    def implement(ap): 
        if ap.logic.view("mov choice")>=0: 
            return ap.logic.get_PDA().implement()

    def reset(ap):
        ap.viability=EVAL_U
        for a in ap.components.values(): 
            a.reset()


class SetPlayerCycleImage(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap,logic)
        ap.write_state_access = True
        ap.logic.update_ap('cycler', 0, ap.uniq_id)
        
    def find_viability(ap): return ap.VIABLE()
    def reset(ap): 
        ap.viability=EVAL_U
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        if ap.logic.view("mov choice")<0: 
             ap.logic.update_ap('cycler', 0, ap.uniq_id)
        c = ap.logic.view_my('cycler', ap.uniq_id)
        choose_img = ap.logic.view('img choice') * 3
        if choose_img<0:  raise Exception(map(ap.logic.view, \
                    ['img choice', 'mov choice', 'prev motion']))

        ap.logic.agent.set_img(choose_img + c )
        if ap.logic.view("mov choice")<0: return
        c += 1
        if c==3: c=0
        ap.logic.update_ap('cycler', c, ap.uniq_id)
        



class PlayerMotion(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.root = Sequential(logic, [\
                    PickNewest(logic),\
                    SetPlayerCycleImage(logic)
                  ])
    def find_viability(ap):  
        ap.logic.update_global('prev move vec', ap.logic.view('curr move vec'))
        ap.logic.update_global('curr move vec', ap.gm.events[:4])
        return ap.COPYEVAL(ap.root.find_viability())
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.logic.update_global('delay', ap.logic.view('root delay'))
        ap.logic.update_global('prev move vec', ap.logic.view('curr move vec'))
        ap.root.implement()
    def reset(ap): 
        ap.viability = EVAL_U; 
        ap.root.reset()

class ThrowPokeballAction(ActionPicker): 
#    def __init__(ap, logic, parent_query): 
    def __init__(ap, logic): 
        ActionPicker.__init__(ap, logic)
#        ap.logic.update_ap('parent query', parent_query, ap.uniq_id)
    def find_viability(ap):
        ap.logic.update_global('isPlayerActionable', False)
        return ap.VIABLE() # the targ should be checked as viable already
#        ap.logic.update_ap('src') = parent.view_my('tile src', parent.uniq_id)
#        ap.logic.update_ap('targ') = parent.view_my('tile targ', parent.uniq_id)

#    def implement(ap): 
    def implement(ap, **arguments):
#        _get = ap.logic.view_my('parent') ap.logic.view_my('parent').uniq_id
        ap.logic.spawn_new('cast pokeball', 'move', dest=arguments['dest'])
#        pq = ap.logic.view_my('parent query')
#        ap.logic.spawn_dep('cast pokeball', 'Move', targ=pq('targ'), src=pq('src'))
#        ap.logic.spawn_dep('cast pokeball', 'Move', \
#                        targ = p.view_my('targ', p.uniq_id), 
#                        src = p.view_my('src', p.uniq_id))

class HandlePlayerActionRequests(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.action_map = { SP_ACTION: ThrowPokeballAction(logic) }
#        print ap.action_map, ThrowPokeballAction(logic)
#        import sys; sys.exit()
#        ap.action_map = { SP_ACTION: lambda dest:ap.logic.spawn_dep(\
#                            'cast pokeball', 'Move', dest=dest)}
#        ap.action_map = { SP_ACTION: lambda dest:ap.logic.spawn_dep(\
#                            'cast pokeball', 'Move', dest=dest)}
#        f = lambda x: ap.logic.view_my(x, ap.uniq_id)
#        help(ThrowPokeballAction)
#        tmp = ThrowPokeballAction(logic,  f )
#        ap.action_map = { SP_ACTION: tmp }
#        print 'ACTION MAP:', ap.action_map.items()

    def find_viability(ap):
        a_requests = ap.logic.view('action requests')
        ap.logic.update_ap('requests', a_requests, ap.uniq_id)
        if not any(a_requests.values()): return ap.INVIABLE()
        tid = ap.logic.view_sensor('mousepos')
        if ap.logic.view_sensor('tpos')==tid: return ap.INVIABLE()
        tile_blocked = ap.logic.view_sensor('tile obstr', tid=tid, \
                blck=['block_'+s for s in BLOCKING_SPECIES])
        if tile_blocked==True: return ap.INVIABLE()
        ap.logic.update_ap('dest', tid, ap.uniq_id)
        ap.logic.update_ap('selected', [a for a in a_requests.keys() if a_requests[a]==True][0], ap.uniq_id) # arbitrary select one requested action
        return ap.GETVIA( ap.action_map[ ap.logic.view_my('selected', \
                            ap.uniq_id) ] )
        # Todo: later convert this into a priority input handler.

#            ap.logic.update_global('action requests', all(all,(ap.logic.view(\
#                    'action requests'), [False]*len(PLYR_ACTIONS))))
#            
#            if any(a_requests): return ap.INVIABLE()
#            ap.logic.update_ap('action requests', {gi:False \
#                                    for gi in a_requests.keys()}, ap.uniq_id)
#            return ap.VIABLE() # ie, attempted but fails
        # check throw dist radius...
        #who_on_tile = ap.logic.view_sensor('get who at tile', tid=tid)
#        ap.logic.update_ap('src', ap.logic.view_sensor('tpos'), ap.uniq_id)
#
#        if len(who_on_tile)==0: return ap.INVIABLE()
#        if len(who_on_tile)>1: raise Exception("Tile occ > 1 not implemented!")
#        np.random.shuffle(who_on_tile)
#        for occ in who_on_tile:
#            if not (occ['team']==u'wild' and occ['species']==u'pkmn'):
#                return ap.INVIABLE()
#            put = ap.logic.update_ap # convenience
#            put('targ', tid, ap.uniq_id)
#            put('src', ap.logic.view('tpos'), ap.uniq_id)
#            put('occ',  occ['who id'], ap.uniq_id)
#            return ap.GETVIA(ap.action_map[req_id].find_viability())
#
#        return ap.VIABILITY_ERROR()



    def implement(ap): 
#        try: 
#             print ap.logic.view_my('requests',ap.uniq_id).keys(), '--2'
#             print ap.logic.view_my('requests',ap.uniq_id).values(), '--2'
#        except: pass
        #for req_id, req_TF in ap.logic.view_my('requests',ap.uniq_id).items():
        req_id = ap.logic.view_my('selected', ap.uniq_id) 
        print req_id, ap.action_map[req_id]
#            print req_id, req_TF, ap.action_map, ap.logic.view_my('dest',ap.uniq_id)
#            if not req_TF: continue
        #print ap.action_map.items(),'--3'
        #_get = lambda x : ap.logic.view_my(x, ap.uniq_id)
#        ''' No need: the logic invokes these after the master has acted. '''
        ap.action_map[req_id].implement( dest = ap.logic.view_my('dest',ap.uniq_id) )
        return 
#            print ap.logic._state.s_ap
#            ap.action_map[req_id]( src=_get('src'), dest=_get('dest') )
#            ap.action_map[req_id]( dest=_get('dest') )
#            ap.action_map[req_id].implement(\
#                    src=ap.logic.view_my('src',ap.uniq_id),\
#                    targ=ap.logic.view_my('targ',ap.uniq_id))

    def reset(ap): 
        try: pass#print ap.logic.view_my('requests',ap.uniq_id).items(), '--1'
        except: pass
        ap.viability=EVAL_U
        if ap.viability==EVAL_T:
            for req_id, req_TF in ap.logic.view_my('requests',ap.uniq_id).items():
                if not req_TF: continue
                ap.action_map[req_id].reset()


    pass # TODO resume here. Implement Player action input handler
class PlayerAction(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.root = HandlePlayerActionRequests(logic)
    def find_viability(ap):  
        ap.logic.update_global('action requests', ap.gm.input_actions_map())
        #ap.gm.events[4:])
        X = ap.root.find_viability()
        #print "Action attempt: ",WHICH_EVAL[X]
        return ap.COPYEVAL(X)
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()
    def reset(ap): 
        ap.viability = EVAL_U; 
        ap.root.reset()


class BasicPlayerActionPicker(ActionPicker): 
    # directly-used subclasses inherit from Entity.
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.logic.update_ap('last move', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('heading', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('cycle', EVAL_INIT, ap.uniq_id)

#        ap.root = Sequential(g,l, \
#            Cond(g,l, All(g,l,[View(g,l,'isPlayerActionable'), 
#                               nonempty('triggered actions')],\
#                          ThrowPokeball(g,l)),\
#            PlayerMotion(g,l)))
#        ap.root = Sequential(g,l, [View(g,l,'isPlayerActionable')])
#        ap.root = Try(logic, PlayerMotion(logic) )

        ap.root = Priority(logic, [\
#                Cond(logic, All(View(logic, 'isPlayerActionable'),\
#                                nonempty('triggered actions')
                CondElse(logic, View(logic, 'isPlayerActionable'), \
                            PlayerAction(logic), Fail(logic)),
                Delay(logic),
                PlayerMotion(logic)])
        

    def reset(ap): 
#        print 'basic player action ',ap.logic.view_sensor('tpos',agent_id=ap.logic.agent.uniq_id)
        ap.viability = EVAL_U
        ap.root.reset()

    def find_viability(ap): 
        if not ap.viability == EVAL_U: raise Exception("Please call reset!")
        via= ap.root.find_viability()
        if via==EVAL_T: return ap.VIABLE(); 
        return ap.INVIABLE()
        return ap.Verify(ap.root)

    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()


