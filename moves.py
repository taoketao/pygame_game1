import abstractEntities as ae
from utilities import *
from constants import *
import abc

class BasicMove(ae.Entity):
    def __init__(mv, gm):
        ae.Entity.__init__(mv, gm)
        mv.state=None
        mv.write_state_access=False
        mv.move_name = 'STUB move todo implement!!'
        mv.species = 'move'

    def set_state(mv, state):
        if not mv.state==None: raise Exception("State has already been set.")
        if state=='stateless': mv._storage={}
        else: mv.storage = state.s_dep[str(mv.uniq_id)+'::'+mv.move_name] = {}

    @abc.abstractmethod
    def DoAction(mv): raise Exception("Implement me! move",mv)

    def Reset(mv): pass
    def PrepareAction(mv): pass

# When commonalities occur, please abstract these away.
class ThrowPokeballMove(BasicMove):
    def __init__(mv, gm, src, dest, parent_logic=None):
        BasicMove.__init__(mv, gm)
        mv.move_name = 'cast pokeball'
        mv.write_state_access=True
        if parent_logic:
            mv.team = parent_logic.agent.team
            mv.set_state(parent_logic._state)
        else:
            mv.set_state('stateless')
        mv.storage['curpos'] = mv.storage['src'] = multvec(src,gm.ts())
        mv.storage['dest'] = multvec(dest,gm.ts())
        mv.storage['stage'] = STAGE_0
#        end_time = dist(src, dest,'eucl')//1
        mv.storage['cur time'] = { STAGE_0: 0, }
        mv.storage['cast time'] = { STAGE_0: CAST_POKEBALL_SPEED }
        mv.storage['vector'] = floorvec(sub_aFb(dest,src))

        mv.gm.notify_new_effect(mv, ppos = mv.storage['src'], img='pokeball')

    def DoAction(mv):
        S = mv.storage
        if S['cur time'][S['stage']]>=S['cast time'][S['stage']]:
            S['stage'] = next_stage(S['stage'])
        if S['stage'] == STAGE_0:
            mv.gm.notify_reset_previous_image(ppos=S['curpos'])
            S['cur time'][STAGE_0] += mv.gm.dt#S['cast speed']*
#            S['vector'] = multvec((sub_aFb(S['dest'], S['src'])), \
#                        S['cur time'][STAGE_0]/S['end time'][STAGE_0], int)
            #next_ppos = addvec(S['src'],S['vector'])
            next_ppos = addvec(S['src'], multvec(S['vector'], \
                        S['cur time'][STAGE_0]/S['cast time'][STAGE_0], int))
            mv.gm.notify_pmove(mv, next_ppos)
            S['curpos'] = next_ppos
