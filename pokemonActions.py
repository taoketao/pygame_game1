import random
from abstractActions import *
from compositeActions import *


#-------------#-------------#--------------#--------------#--------------

'''     Pokemon logic APs               '''


class WildPkmnBehavior(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.agent = logic.agent
        ap.write_state_access = True
        ap.root = Priority(ap.logic, [ \
                    Delay(ap.logic), \
                    # use attack move (a big AP itself),
                    Wander(ap.logic) ] )
#            Sequential(logic, \
#                # wasCaughtProcessing(ap.logic) ,\
#                # is being caught,
#                [Priority(ap.logic, [ \
#                    Delay(ap.logic), \
#                    # use attack move (a big AP itself),
#                    Wander(ap.logic) ] ),\
#                #Redraw(ap.logic)\
#                ])
    def find_viability(ap): 
        return ap.GETVIA(ap.root)
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()
    def reset(ap): ap.viability = EVAL_U; ap.root.reset()

class PickRandMove(ActionPicker):
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.logic.update_ap('mov choice', 'd', ap.uniq_id)
        ap.logic.update_global('img choice', 'd')
        ap.components = components
#        ap.Redraw = Redraw(logic)

    def find_viability(ap):
        indices = list(range(len(ap.components)))
        random.shuffle(indices)
        for ci in indices:
            a = ap.components[ci]
#            print '\t',a.name,  WHICH_EVAL[a.find_viability__tile()]
            if EVAL_T==a.find_viability__tile(): 
                ap.logic.update_ap('mov choice', a.name, ap.uniq_id)
                ap.logic.update_global('img choice', a.name)
                return ap.VIABLE()
        ap.logic.update_ap('mov choice', '-', ap.uniq_id)
#        ap.Verify(ap.Redraw)
        return ap.Verify(ap.logic.belt.Actions['-'])
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.logic.update_global('delay', ap.logic.view('root delay'))
        prevtloc = ap.logic.view_sensor('tpos')
        ap.logic.belt.Actions[ap.logic.view_my('mov choice', ap.uniq_id)].implement()
        ap.logic.agent.set_img(ap.logic.view('img choice'), prevtloc)
        #ap.redraw.implement_arg(prevtloc)
#        ap.Redraw.implement(prevtloc)

    def reset(ap): 
        ap.viability = EVAL_U; 
        for c in ap.logic.belt.Actions.values(): c.reset()
        ap.logic.update_ap('mov choice', EVAL_U, ap.uniq_id)
            
class Delay(ActionPicker): 
    # As used in Priority, returns EVAL_T to block if delay has not finished.
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
    def find_viability(ap):
        return (ap.VIABLE() if ap.logic.view('delay')>=0 else ap.INVIABLE())
    def implement(ap): assert(ap.viability==EVAL_T)
    def reset(ap): ap.viability=EVAL_U

# wander: pick a random valid direction and move there.
class Wander(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.card_dirs = [m for m in logic.view('motions').values() if m.index>=0]
        ap.chooser = PickRandMove(logic, ap.card_dirs)
        ap.index = None
    def find_viability(ap): 
        return ap.GETVIA(ap.chooser)
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.chooser.implement()
    def reset(ap): ap.viability = EVAL_U; ap.chooser.reset()

#class Redraw(ActionPicker):
#    def __init__(ap, logic):
#        ActionPicker.__init__(ap, logic)
#    def find_viability(ap): return ap.VIABLE()
##    def implement_arg(ap, prevtloc=None):
#    def implement(ap, prevtloc=None):
#        if prevtloc: 
#            ap.logic.agent.set_img(ap.logic.view('img choice'), prevtloc)
#        if not ap.logic.view('redraw')==ap.logic.view_sensor('tpos'):
#            ap.logic.agent.set_img(ap.logic.view('img choice'), ap.logic.view('redraw'))
#
#








# wasCaught: query if the pokemon was caught; execute pkmn removal from scene.
class wasCaughtProcessing(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = False # no update; read-only @ State 
        ap.key = 'was catch completed'
    def find_viability(ap): 
        return { True: ap.VIABLE(), False: ap.INVIABLE() }\
                    [ap.logic.view(ap.key)]
    def implement(ap):
        assert(ap.viability==EVAL_T)
        pass # set image to white and kill self
    def reset(ap): ap.viability = EVAL_U;
