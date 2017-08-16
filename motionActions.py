from abstractActions import *

#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''     Convenience, Baseline, and Exemplar Actions and APs            '''


''' MotionAction: a base Action variant that '''
class MotionAction(Action):
    def __init__(action, logic):
        Action.__init__(action, logic.gm)
        action.logic = logic
        action.agent = logic.agent

    def find_viability(action): # TODO : a likely place to resume work.
        if action.name=='-': return action.VIABLE()
        if action.viability in [EVAL_T, EVAL_F]: return action.viability
        cur_ppos = action.logic.view_sensor('ppos', agent_id=action.agent.uniq_id)
        unit_step = action.logic.view('unit step')

        if EVAL_F in [cur_ppos, unit_step]:
            print "ERR?: cur_ppos & unit_step", cur_ppos, unit_step
            return action.INVIABLE()
        query_ppos = addvec(multvec(action.posvec, unit_step), cur_ppos)

        if action.logic.agent.species in ['plyr', 'pkmn']:
            query_tpos = action.logic.pTOt(query_ppos)
            return action.GETTRUTH(action.logic.view_sensor('tile obstr', \
                    tid=query_tpos, blck=action.logic.agent.species)==False)
        raise Exception(action.logic.agent.species, 'not impl yet')

    def find_viability__tile(action): # A version that checks only Tiles.
        assert(isinstance(action.agent, TileAgent))
        assert(action.gm.ts() == action.logic.view('unit step'))
        assert(action.agent.species in ['pkmn'] )
        if action.name=='-': return action.VIABLE()
        #if action.viability in [EVAL_T, EVAL_F]: return action.viability
        cur_t = action.logic.view_sensor('tpos', agent_id=action.agent.uniq_id)
        query_t = addvec(action.posvec, cur_t)
        print "At", cur_t, "querying", query_t
        return action.GETTRUTH(not action.logic.view_sensor('tile obstr', tid=query_t, blck='pkmn'))



    def implement(action):
#        print '*'*30,"ENACTING", action.index, action.posvec, WHICH_EVAL[action.viability]
        assert(action.viability==EVAL_T)
        if action.index<0: return
        action.agent.move_in_direction(action.posvec)

    def same(action, targ): return action.index==targ.index # etc
    def reset(action): 
#        print '<<<<   motion reseting:',action.name
        action.viability = EVAL_U # actually impt here


class MotionUp(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [1,0,0,0];      action.posvec = (0,-1);
        action.name = 'u';            action.index = 0
        action.null=False
class MotionLeft(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,1,0,0];      action.posvec = (-1,0);
        action.name = 'l';            action.index = 1
        action.null=False
class MotionDown(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,0,1,0];      action.posvec = (0,1);
        action.name = 'd';            action.index = 2
        action.null=False
class MotionRight(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,0,0,1];      action.posvec = (1,0);
        action.name = 'r';            action.index = 3
        action.null=False
class MotionStatic(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = [0,0,0,0];      action.posvec = (0,0);
        action.name = '-';            action.index = -1
        action.null=True
class MotionNull(MotionAction):
    def __init__(action, logic):
        MotionAction.__init__(action, logic)
        action.dvec = None;         action.posvec = NULL_POSITION;
        action.name = '__x__';      action.index = -2
        action.null=True

#
