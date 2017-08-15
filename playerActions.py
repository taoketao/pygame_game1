from abstractActions import *
from compositeActions import *



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
        # Messy messy, but so is lateral non-hierarchical variable passing
        curmove = ap.logic.view('curr move vec')[:] 
        prev = ap.logic.get_PDA()
        for index in range(len(curmove)):
            if curmove[index]:
                if not index==prev.index:
                    ap.logic.push_PDA(index) # key is down
            else:
                ap.logic.pop_PDA(index) # key is up
        curnew = ap.logic.get_PDA()
        if curnew.index==-1:
            ap.logic.update_global('mov choice', -1)
            ap.logic.update_global('prev motion', prev.index)
            ap.logic.push_PDA(prev.index)
        else:
            if not curnew==prev:  v=prev.index
            else:             v=curnew.index
#            ap.logic.update_global('img choice', v)
#            ap.logic.update_global('mov choice', v)
            ap.logic.update_global('prev motion', curnew.index)
            ap.logic.update_global('img choice', curnew.index)
            ap.logic.update_global('mov choice', curnew.index)
#            ap.logic.update_global('prev motion', {True:prev, False:curnew}[curnew==prev].index)
        return ap.VIABLE()

    def implement(ap): pass
        

# Actually carry out a picked action once ready:
class orderPDAAction(ActionPicker):
    def __init__(ap, logic, mode):
        ActionPicker.__init__(ap, logic)
        ap.VIABLE()
    def find_viability(ap): 
        x= ap.logic.get_PDA().find_viability()
        if ap.logic.get_PDA().find_viability()==EVAL_T:
            return ap.VIABLE()
        return ap.INVIABLE()
        return {EVAL_T:ap.VIABLE(), EVAL_F:ap.INVIABLE()}.get(x, EVAL_ERR)

    def reset(ap): ap.viability = EVAL_U;
    def implement(ap): 
        x= ap.logic.get_PDA().find_viability()
        assert(ap.viability==EVAL_T)
        if not ap.viability==EVAL_T:
            print 'default err'
            return logic.do_default()
#       hack:
        if ap.logic.view("mov choice")>=0: 
            return ap.logic.get_PDA().implement()


class SetPlayerCycleImage(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap,logic)
        ap.write_state_access = True
        ap.logic.update_ap('cycler', 0, ap.uniq_id)
        
    def find_viability(ap): return ap.VIABLE()
    def reset(ap): ap.viability=EVAL_U
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        if ap.logic.view("mov choice")<0: 
             ap.logic.update_ap('cycler', 0, ap.uniq_id)
        c = ap.logic.view_my('cycler', ap.uniq_id)
        mvname=ap.logic.get_PDA().index
#        print 'MVNAME', mvname,  ap.logic.view("mov choice")
        choose_img = ap.logic.view('img choice') * 3
        if choose_img<0: 
            raise Exception(map(ap.logic.view, ['img choice', 'mov choice', 'prev motion']))

        ap.logic.agent.set_img(choose_img + c )
#        ap.logic.update_global("Image", 'player sprite '+\
#                                str(choose_img + c ))
        if ap.logic.view("mov choice")<0: return
        c += 1
        if c==3: c=0
        ap.logic.update_ap('cycler', c, ap.uniq_id)
        



class PlayerMotion(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.root = Sequential(logic, [\
                    PickNewest(logic),\
                    orderPDAAction(logic, 'newest'),\
                    SetPlayerCycleImage(logic), \
                  ])
    #def find_viability(ap): return ap.Verify(ap.root)
    def find_viability(ap): 
        return ap.COPYEVAL(ap.root.find_viability())
#        print '\t',s; return s
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()
    def reset(ap): ap.viability = EVAL_U; ap.root.reset()

def ThrowPokeball(x,y): pass            


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
        ap.root = Try(logic, PlayerMotion(logic) )
        

    def reset(ap): 
        ap.viability = EVAL_U
        ap.root.reset()

    def find_viability(ap): 
        if not ap.viability == EVAL_U: raise Exception("Please call reset!")
        via= ap.root.find_viability()
#        print WHICH_EVAL[via]
        if via==EVAL_T: return ap.VIABLE(); 
        return ap.INVIABLE()
        return ap.Verify(ap.root)

    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()


