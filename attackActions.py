from utilities import *
from constants import *
from abstractActions import *

class DoAttack(ActionPicker):
    def __init__(atk, logic):
        ActionPicker.__init__(atk, logic)
        atk.agent=logic.agent
#        atk.logic=logic
#        atk.source_tid = src
#        atk.destn_tid = dst
    def find_viability(atk): return atk.VIABLE()
    def implement(atk): pass
    def reset(atk): atk.viability=EVAL_U

class ChooseRandAttack(ActionPicker):
    def __init__(atk, logic):
        ActionPicker.__init__(atk, logic)
        atk.agent=logic.agent
#        atk.logic=logic
#        atk.source_tid = src
#        atk.destn_tid = dst
    def find_viability(atk): return atk.VIABLE()
    def implement(atk): pass
    def reset(atk): atk.viability=EVAL_U

