from abstractActions import *


#-------------#-------------#--------------#--------------#--------------

'''     Pokemon logic APs               '''


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

# wander: pick a random valid direction and move there.
class wander(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.card_dirs = logic.view('available motions')
        ap.chooser = PickRand(ap.card_dirs)
    def find_viability(ap): return ap.chooser.find_viability()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.chooser.implement()
    def reset(ap): ap.viability = EVAL_U; ap.chooser.reset()


class BasicPkmnActionPicker(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.root = Priority(ap.ap.logic [ \
                wasCaughtProcessing(ap.ap.logic) ,\
                # is being caught,
                # use attack move (a big AP itself),
                wander(ap.ap.logic)
                ] )
    def find_viability(ap): return ap.root.find_viability()
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()
    def reset(ap): ap.viability = EVAL_U; ap.root.reset()
