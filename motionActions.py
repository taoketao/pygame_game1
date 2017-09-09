from abstractActions import *
import moves as moves_module

#-------------#-------------#--------------#--------------#--------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-------------#-------------#--------------#--------------#--------------

'''     Convenience, Baseline, and Exemplar Actions and APs            '''

class AnimMotion(moves_module.BasicMove):
    ''' AnimMotion: this animates a motion of One Tile, piggybacking the 
        same baseline MotionAction AP object. That is, this object can
        be swapped directly into the belt.Actions where the original
        MotionAction stood, subject only to the extra parameters. '''
    # For now, just implement to working quality; add Super later, if appropriate.
    def __init__(action, logic, motionAction, speed):
        moves_module.BasicMove.__init__(action, logic.gm, logic)
        action.logic = logic
        action.agent = logic.agent

        action.put('active', False)  # aka running
        action.put('end time', speed) # an int number of ticks till complete
        ma = motionAction(logic)
        action.put('motion_object', ma) # eg, a MotionUp instance
        action.dvec=ma.dvec
        action.posvec=ma.posvec
        action.name=ma.name
        action.index=ma.index
        action.null=ma.null
        print 'Initialized animaction:', action.name, action.agent.uniq_name
        action.put('t',0 )
        
    def find_viability(action):
        print 'finding via animmotion:', action.name, action.agent.uniq_name
        if action.logic.ViewActionLock()==action.uniq_id:
            assert(action.get('active'))
            action.put( 't', action.get('t')+action.gm.dt )
            print ' ^- Result: successfully iterated dt.'
            return action.VIABLE()
        elif action.get('t')==0 and \
                 action.get('motion_object').find_viability()==EVAL_T\
                 and action.logic.LockAction( action.uniq_id ):
            # ^ check: ready to lock, valid action, successful lock: 
            action.put( 'active',   True)
            action.put( 'src',      action.logic.view_sensor('tpos') )
            action.put( 'dest',     addvec(action.get('motion_object').\
                                posvec, action.logic.view_sensor('tpos')))
            return action.VIABLE()
            print ' ^- Result: successfully initiated move.'
        return action.INVIABLE()
        
    def implement(action):
        assert(action.viability==EVAL_T and action.get('active'))
        print 'anim:',action.get('t'), action.get('end time'), \
                        action.agent.uniq_name, action.logic.view('delay'),
        if action.get('t')==0:
            print 'STARTING'
            action.gm.notify_new_motion(action.agent.uniq_id, \
                        prev= action.get('src'),\
                        new = action.get('dest'))
        elif action.get('t')>action.get('end time'):
            print 'STOPPING'
            action.gm.notify_stopping(action.agent.uniq_id, \
                        prev= action.get('src'),\
                        new = action.get('dest'))
            action.logic.UnLockAction( action.uniq_id )
            action.put('active', False)
            action.logic.update_global('delay', action.logic.view('delay')\
                    +action.logic.view('root delay'))
        else:
            print 'MOVING'
            lin = float(action.get('t'))/action.get('end time')
            next_fractional_tpos = addvec( multvec( action.get('src'), 1-lin),\
                    multvec( action.get('dest'), lin))
            next_ppos = multvec(next_fractional_tpos, action.gm.ts(), int)
            action.gm.notify_update(action.agent, 'entities', \
                                    px=next_ppos[X], py=next_ppos[Y])

        action.gm.display.queue_reset_tile( action.get('src'), 'tpos' )
        action.gm.display.queue_reset_tile( action.get('dest'), 'tpos' )
#            action.gm.notify_ppos( uid
#                    ppos = multvec(next_fractional_tpos, action.gm.ts(), int)
    def reset(action):
        action.get('motion_object').reset()
        action.viability = EVAL_U 

    def kill(action): 
        raise Exception("This kind of action should not be deletable")


''' MotionAction: a base Action variant that '''
class MotionAction(Action):
    def __init__(action, logic):
        Action.__init__(action, logic.gm)
        action.logic = logic
        action.agent = logic.agent
        action.convenience_query_tpos = None

    def find_viability(action):
        if action.name=='-': return action.VIABLE()
        if action.viability in [EVAL_T, EVAL_F]: return action.viability
        cur_ppos = action.logic.view_sensor('ppos', \
                                    agent_id=action.agent.uniq_id)
        unit_step = action.logic.view('unit step')
        if EVAL_F in [cur_ppos, unit_step]:
            print "ERR?: cur_ppos & unit_step", cur_ppos, unit_step
            return action.INVIABLE()
        query_ppos = addvec(multvec(action.posvec, unit_step), cur_ppos)
        action.convenience_query_tpos = query_tpos = \
                action.logic.pTOt(query_ppos)
        if query_tpos==action.logic.view_sensor('tpos'): return action.VIABLE()
        if action.logic.agent.species in BLOCKING_SPECIES:
            query_tpos = action.logic.pTOt(query_ppos)
#            print action.logic.view_sensor('tile occs', tid=query_tpos)
            print action.agent.uniq_name,': Agents at tile',query_tpos,':',action.logic.view_sensor('get agents at tile', tid=query_tpos)
            return action.GETTRUTH(action.logic.view_sensor('tile occs', \
                    tid=query_tpos)==0)#, blck=action.logic.agent.species)==False)
#            return action.GETTRUTH(action.logic.view_sensor('tile obstr', \
#                    tid=query_tpos, blck=action.logic.agent.species)==False)
        raise Exception(action.logic.agent.species, 'not impl yet')

    def implement(action):
        assert(action.viability==EVAL_T)
        if action.index<0: return
        action.agent.move_in_direction(action.posvec)

    def same(action, targ): return action.index==targ.index # etc
    def reset(action): action.viability = EVAL_U 


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

