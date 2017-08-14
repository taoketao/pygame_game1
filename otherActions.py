from abstractActions import *

#-------------#-------------#--------------#--------------#--------------

'''   Mouse follower, almost a stub. Most of this code has been left
      unotuched, opting to piggyback on previous agents2 work.          '''

class MouseActionPicker(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
    def reset(ap): ap.viability=EVAL_U
    def find_viability(ap):
        ap.logic.update_global('mouse ppos',pygame.mouse.get_pos())
        return ap.VIABLE()
    def implement(ap):
        ap.logic.agent.update_position(ap.logic.pTOt(\
                ap.logic.view('mouse ppos')))
        
