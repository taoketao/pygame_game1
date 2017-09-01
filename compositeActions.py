import random
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
        ap.viability = EVAL_U; 
        for a in ap.components: a.reset() # naive

def All(g,l,c): return Sequential(g,l,c)
def Both(g,l,c): return All(g,l,c) if len(c)==2 else EVAL_ERR

# PRIORITY: Given a list, picks the first success in the list (if not any: EVAL_F)
class Priority(ActionPicker): # AKA, DoOneRetOne in order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.components = components
        ap.easy_init('pchoice')
    def find_viability(ap):
        for ci in range(len(ap.components)):
            c=ap.components[ci]
            if EVAL_T==c.find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABLE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.components[ap.logic.view_my(ap.key, ap.uniq_id)].implement()
    def reset(ap):
        ap.viability = EVAL_U
        for a in ap.components: a.reset()

# PickRand a.k.a. Random Priority: pick a viable element at random, if possible.
# Very basic outline; customized overhauls are recommended.
class PickRand(ActionPicker): # AKA, DoOneRetOne in no order
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.components = components
        ap.easy_init('rchoice')
    def find_viability(ap):
        indices = list(range(len(ap.components)))
        random.shuffle(indices)
        for i in indices:
            c = ap.components[i]; ci = c.index
            if EVAL_T==c.find_viability(): 
                ap.logic.update_ap(ap.key, ci, ap.uniq_id)
                return ap.VIABLE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.components[ap.logic.view_my(ap.key, ap.uniq_id)].implement()
    def reset(ap):
        ap.viability = EVAL_U
        for a in ap.components: a.reset()
#        for a in ap.components[:ap.logic.view_my(ap.key, ap.uniq_id)]: a.reset()




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


# CONDELSE: Returns what <do1> returns only when <cond>, else what <do2> returns.
class CondElse(ActionPicker):
    def __init__(ap, logic, cond, do1, do2):
        ActionPicker.__init__(ap, logic)
        ap.cond = cond
        ap.do1 = do1
        ap.do2 = do2
        ap.easy_init('valuation')

    def find_viability(ap):
        cond_via = ap.GETVIA(ap.cond)
        ap.logic.update_ap(ap.key, cond_via, ap.uniq_id)
        if cond_via==EVAL_T:
            ap.viability = ap.do1.find_viability()
            return ap.GETVIA(ap.do1)#ap.viability
        return ap.GETVIA(ap.do2)#ap.viability

    def implement(ap):
        { EVAL_T:ap.do1, EVAL_F:ap.do2 }\
                [ap.logic.view_my(ap.key, ap.uniq_id)]\
                .implement()
#
#        if ap.logic.view_my(ap.key, ap.uniq_id)==EVAL_T: ap.do1.implement()
#        elif ap.logic.view_my(ap.key, ap.uniq_id)==EVAL_F: ap.do2.implement()

    def reset(ap): 
        ap.viability = EVAL_U; 
        ap.cond.reset(); ap.do1.reset(); ap.do2.reset()
        ap.logic.update_ap(ap.key, EVAL_U, ap.uniq_id)




# TryCatch, Try: as expected
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
