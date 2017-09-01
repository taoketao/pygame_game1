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

class CatchPokeballAction(ActionPicker): 
    def __init__(ap, logic): ActionPicker.__init__(ap, logic)
    def find_viability(ap, dest):
        if not ap.logic.view('isPlayerActionable'): return ap.INVIABLE()
        ap.logic.update_global('isPlayerActionable', False)
        return ap.GETVIA(ap.logic.spawn_new('cast pokeball', 'move', dest=dest))

class ThrowPokeballAction(ActionPicker): 
    def __init__(ap, logic): ActionPicker.__init__(ap, logic)
    def find_viability(ap, dest):
        if not ap.logic.view('isPlayerActionable'): return ap.INVIABLE()
        ap.logic.update_global('isPlayerActionable', False)
        return ap.GETVIA(ap.logic.spawn_new('throw pokemon', 'move', dest=dest))

class HandlePlayerActionRequests(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.action_map = { 'catch': CatchPokeballAction(logic),\
                          'throw': ThrowPokeballAction(logic)   }

    def find_viability(ap):
        a_requests = ap.logic.view('action requests')
        ap.logic.update_ap('requests', a_requests, ap.uniq_id)
        if not any(a_requests.values()): return ap.INVIABLE()
        tid = ap.logic.view_sensor('mousepos')
        if ap.logic.view_sensor('tpos')==tid: return ap.INVIABLE()
        tile_blocked = ap.logic.view_sensor('tile obstr', tid=tid, \
                blck=['block_'+s for s in BLOCKING_SPECIES])
        ap.logic.update_ap('dest', tid, ap.uniq_id)
        if tile_blocked==True: return ap.INVIABLE()
        key = {True:'catch', False:'throw'}[ap.logic.view_sensor(\
                    'tile occ', tid=tid)]
        ap.logic.update_ap('selected', key, ap.uniq_id)
        via = ap.action_map[key].find_viability(tid)
        return ap.COPYEVAL(via)
            
    def implement(ap): 
        pass
#        req_id = ap.logic.view_my('selected', ap.uniq_id) 
#        ap.action_map[req_id].implement( dest = ap.logic.view_my('dest',ap.uniq_id) )
#        return 

    def reset(ap): 
        ap.viability=EVAL_U
        for a in ap.action_map.values(): a.reset()
#        if ap.viability==EVAL_T:
#            for req_id, req_TF in ap.logic.view_my('requests',ap.uniq_id).items():
#                if not req_TF: continue
#                ap.action_map[req_id].reset()

class PlayerAction(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.root = HandlePlayerActionRequests(logic)
    def find_viability(ap):  
        ap.logic.update_global('action requests', ap.gm.input_actions_map())
        return ap.COPYEVAL(ap.root.find_viability())
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
        ap.root = Priority(logic, [\
                Delay(logic),
                CondElse(logic, View(logic, 'isPlayerActionable'), \
                            PlayerAction(logic), Fail(logic)),
                PlayerMotion(logic)])
        

    def reset(ap): 
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


