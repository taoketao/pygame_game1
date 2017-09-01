import abstractActions as aa
from utilities import *
from constants import *
import abc

class BasicMove(aa.Action):
    ''' Moves are actions that typically display an animation, send 
        messages independently, and die off at some point. While these 
        are logged as an Agent's Dependents in the belt, their timing 
        does not always necessitate the timing mechanisms built into
        dependency; instead, the 'ownership' concept is highlighted.   '''
    def __init__(mv, gm, logic):
        aa.Action.__init__(mv, gm)
        mv.write_state_access=True
        mv.move_name = 'STUB move todo implement!!'
        mv.species = 'move'
        mv.storage_key = 'stub key::move'
        mv.team = logic.agent.team
        mv.logic=logic
        mv.logic.update_dep('stage', STAGE_0, mv)

    def DoAction(mv): 
        #assert(mv.viability==EVAL_T)
        return mv.implement()
    def PrepareAction(mv): return mv.find_viability()
    def Reset(mv): return mv.reset()

    @abc.abstractmethod
    def implement(mv): raise Exception("Implement me! move",mv)
    @abc.abstractmethod
    def find_viability(mv): raise Exception("Implement me! move",mv)
    @abc.abstractmethod
    def reset(mv): raise Exception("Implement me! move",mv)

    def kill(mv): 
        mv.gm.display.queue_reset_tile(mv.get('dest'), 'tpos')
        mv.gm.db.execute(sql_del_partial+'uniq_id=?;', (mv.uniq_id,) )
        mv.gm.entities.pop(mv.uniq_id)

    # Aliases:
    def get(mv, x): return mv.logic.view_dep(x,mv)
    def put(mv, x, y): mv.logic.update_dep(x,y,mv)

class ProjectileMove(BasicMove):
    ''' A class that FIRST launches an object to a location via linear 
        interpolation, THEN does something else custom if desired. '''
    def __init__(mv, gm, dest, logic, src_offset=None, dest_offset=None,\
            fragile=False):
        BasicMove.__init__(mv, gm, logic)
        mv.move_name = 'GENERIC PROJECTILE STUB'
        mv.source_logic = logic

        if src_offset==None: src_offset = (0,0) # nice for player
        if dest_offset==None: dest_offset = (0,0) # aims for tile center?

        src = addvec(divvec(logic.view_sensor('ppos'), gm.ts(), float), src_offset)
        dest = addvec(dest, dest_offset)
        mv.fragile=fragile
        mv.put('dest', dest) # in TPOS
        mv.put('src', src) #  in TPOS
        mv.put('uvec', unit_vector(sub_aFb(src,dest)))
        mv.put('dist', dist(src,dest,2))
        mv.put('t', 0)
        mv.put('stage0->1 t fin', 'STUB TODO') 

        l = [] # Reset tiles that were previously under me
        if mv.get('uvec')[X] < 0:
            l.append( (1,0) )
            if mv.get('uvec')[Y] < 0: 
                l.append( (0,1) )
                l.append( (1,1) )
            elif mv.get('uvec')[Y] > 0: 
                l.append( (0,-1) )
                l.append( (1,-1) )
        elif mv.get('uvec')[X] > 0:
            l.append( (-1,0) )
            if mv.get('uvec')[Y] < 0: 
                l.append( (0,1) )
                l.append( (-1,1) )
            elif mv.get('uvec')[Y] > 0: 
                l.append( (0,-1) )
                l.append( (-1,-1) )
        elif mv.get('uvec')[Y] > 0: l.append( (0,-1) )
        elif mv.get('uvec')[Y] < 0: l.append( (0,1) )
        mv.put('trail tiles', l)

    def _process_landing(mv): raise Exception("Please fill me in.")
    def _implement_landing(mv): raise Exception("Please fill me in.")
    def reset(mv): mv.viability=EVAL_U 
    def find_viability(mv): 
        t = mv.get('t')
        mv.put('t', t + mv.gm.dt)
        if mv.get('stage')==STAGE_0 and mv.get('t')>mv.get('stage0->1 t fin'):
            mv.put('stage', STAGE_1) # alter stage conditionally
            mv.put('t',0)
            return mv.VIABLE()
        return mv.COPYEVAL(mv._process_landing())

    def implement(mv):
        assert(mv.viability==EVAL_T)
        if mv.get('stage')==STAGE_0: 
            lin = float(mv.get('t'))/mv.get('stage0->1 t fin')
            next_fractional_tpos = addvec( \
                    multvec(mv.get('src'), 1-lin), multvec(mv.get('dest'), lin))
            mv.gm.notify_pmove(mv, multvec(next_fractional_tpos, mv.gm.ts()))
            for t in mv.get('trail tiles'):
                mv.gm.display.queue_reset_tile(floorvec(addvec(t, \
                        next_fractional_tpos)))
        mv._implement_landing()



# When commonalities occur, please abstract these away.
class CatchPokeballMove(ProjectileMove):
    def __init__(mv, gm, dest, logic, **_unused_arguments_):
        ProjectileMove.__init__(mv, gm, dest, logic, \
                        dest_offset=(0.3,0.3), src_offset=(0,-0.5))
        mv.move_name = 'cast pokeball'
        mv.storage_key = str(mv.uniq_id)+'::'+mv.move_name
        mv.put('stage0->1 t fin', int(CAST_POKEBALL_SPEED*mv.get('dist'))) 
        mv.put('stage1->2 t fin', PB_OPENFRAMES * POKEBALL_OPEN_SPEED) 
        mv.gm.notify_new_effect(mv, tpos=mv.get('src'), img='pokeball', team=mv.team)

    def _process_landing(mv): 
        if (mv.get('stage')==STAGE_1 and mv.get('t')>=mv.get('stage1->2 t fin'))\
                or mv.logic.view_sensor('tile occ', tid=mv.get('dest')):
            mv.put('stage', STAGE_2)
            mv.logic.update_global('isPlayerActionable', True)
            return mv.INVIABLE()
        return mv.VIABLE()

    def _implement_landing(mv): 
        if mv.get('stage')==STAGE_1: 
            img_num = mv.get('t')//POKEBALL_OPEN_SPEED
            mv.gm.notify_image_update(mv, 'pokeball-fade-'+str(img_num))
            mv.gm.send_message(\
                    msg='catching',  sender_team = mv.team, \
                    at = floorvec(mv.get('dest')), \
                    source_logic = mv.source_logic, \
                    amount = mv.gm.dt * (PB_OPENFRAMES-img_num)//100 )
            ''' amount can change depending on pokeball strength. '''


class ThrowPokeballMove(ProjectileMove):
    def __init__(mv, gm, dest, logic, **_unused_arguments_):
        ProjectileMove.__init__(mv, gm, dest, logic, \
                        dest_offset=(0.3,0.3), src_offset=(0,-0.5))
        mv.move_name = 'cast pokeball'
        mv.storage_key = str(mv.uniq_id)+'::'+mv.move_name
        mv.put('stage0->1 t fin', int(CAST_POKEBALL_SPEED*mv.get('dist'))) 
        mv.put('stage1->2 t fin', PB_OPENFRAMES * POKEBALL_OPEN_SPEED) 
        mv.gm.notify_new_effect(mv, tpos=mv.get('src'), img='pokeball', team=mv.team)

    def _process_landing(mv): 
        if mv.get('stage')==STAGE_1:
            img_num = mv.get('t')//POKEBALL_OPEN_SPEED
            if mv.logic.view_sensor('tile occ', tid=mv.get('dest')):
                mv.logic.update_global('isPlayerActionable', True)
                mv.put('stage', STAGE_2)
                return mv.INVIABLE()
            if mv.get('t')>=mv.get('stage1->2 t fin'):
                mv.logic.update_global('isPlayerActionable', True)
                mv.put('stage', STAGE_2)
                mv.gm.send_message(\
                        msg='throwing',  sender_team = mv.team, \
                        source_logic = mv.source_logic, \
                        at = floorvec(mv.get('dest')), \
                        amount = mv.gm.dt * (PB_OPENFRAMES-img_num)//100 )
                return mv.INVIABLE()
        return mv.VIABLE()

    def _implement_landing(mv): 
        if mv.get('stage')==STAGE_1: 
            img_num = mv.get('t')//POKEBALL_OPEN_SPEED
            mv.gm.notify_image_update(mv, 'pokeball-fade-'+str(img_num))
