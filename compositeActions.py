from abstractActions import *

#-------------#-------------#--------------#--------------#--------------

'''     Standard Composite AP Nodes               '''


# SEQUENTIAL: does all the actions (in order), and returns EVAL_T iff each
#  returns EVAL_T. cp DoAllRetAny, DoAllRetAll.
class Sequential(ActionPicker): # in order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.components = components
        ap.write_state_access = True
    def find_viability(ap):
        for __ai, a in enumerate(ap.components):
            if not EVAL_T==a.find_viability(): 
                return ap.INVIABLE()
        return ap.VIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        for a in ap.components: 
            a.implement()
    def reset(ap):  
        for a in ap.components: a.reset() # naive
        ap.viability = EVAL_U; 

def All(g,l,c): return Sequential(g,l,c)
def Both(g,l,c): return All(g,l,c) if len(c)==2 else EVAL_ERR

# PRIORITY: Given a list, picks the first success in the list (if not any: EVAL_F)
class Priority(ActionPicker): # AKA, DoOneRetOne in order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.components = components
        ap.easy_init('choice')
    def find_viability(ap):
        for ci, c in enumerate(ap.components):
            if EVAL_T==c.find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABILE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.components[ap.logic.view_my(ap.key, ap.uniq_id)].implement()
    def reset(ap):
        ap.viability = EVAL_U
        for a in ap.components[:ap.logic.view_my(ap.key, ap.uniq_id)]: a.reset()

# PickRand a.k.a. Random Priority: pick a viable element at random, if possible.
class PickRand(ActionPicker): # AKA, DoOneRetOne in no order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.logic.update_ap('choice', EVAL_INIT, ap.uniq_id)
        ap.logic.update_ap('indices', EVAL_INIT, ap.uniq_id)
        ap.components = components

    def find_viability(ap):
        indices = list(range(len(ap.components)))
        random.shuffle(indices)
        ap.logic.update_ap('indices', indices, ap.uniq_id) # For other reference
        for ci in indices:
            if EVAL_T==ap.components[ci].find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABLE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.components[ap.logic.view_my('choice', ap.uniq_id)].implement()
    def reset(ap): 
        ap.viability = EVAL_U; 
        for c in ap.components: c.reset()
        ap.logic.update_ap('indices', EVAL_U, ap.uniq_id)
        ap.logic.update_ap('choice', EVAL_U, ap.uniq_id)


# COND: basic conditional. Returns what <do> returns only when <cond>, else EVAL_T
class Cond(ActionPicker):
    def __init__(ap, logic, cond, do):
        ActionPicker.__init__(ap, logic)
        ap.cond = cond
        ap.do = do
        ap.easy_init('valuation')

    def find_viability(ap):
        cond_via = ap.cond.find_viability()
        ap.logic.update_ap(ap.key, cond_via, ap.uniq_id)
        if cond_via==EVAL_T:
            ap.viability = ap.do.find_viability()
            return ap.viability
        return ap.VIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        if ap.logic.view_my(ap.key, ap.uniq_id)==EVAL_T: ap.do.implement()

    def reset(ap): 
        ap.viability = EVAL_U; ap.cond.reset(); ap.do.reset()
        ap.logic.update_ap(ap.key, EVAL_T, ap.uniq_id)

class TryCatch(ActionPicker):
    def __init__(ap, logic, tr, ca):
        ActionPicker.__init__(ap, logic)
        ap.tr, ap.ca = tr, ca
        ap.easy_init('valuation')

    def find_viability(ap):
        try_via = ap.tr.find_viability()
        ap.logic.update_ap(ap.key, try_via, ap.uniq_id)
        if try_via==EVAL_F:
            if ap.ca: return ap.GETVIA( ap.ca )
        return ap.VIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        if ap.logic.view_my(ap.key, ap.uniq_id)==EVAL_T: ap.tr.implement()
        elif ap.ca: ap.ca.implement() # if implemented, one of the two succeeded.
    def reset(ap):
        ap.viability = EVAL_U; 
        ap.tr.reset(); 
        if ap.ca: ap.ca.reset()
        ap.logic.update_ap(ap.key, EVAL_T, ap.uniq_id)
def Try(logic, tr): return TryCatch(logic, tr, None)
