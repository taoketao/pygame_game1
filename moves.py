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
        mv.custom_reset_tiles = False

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
                if not mv.custom_reset_tiles:
                    mv.gm.display.queue_reset_tile(floorvec(addvec(t, \
                                next_fractional_tpos)))
        mv._implement_landing()


class CustomProjectileMove(ProjectileMove):
    def __init__(mv, gm, dest, logic, dest_offset=(0,0), src_offset=(0,0)):
        ProjectileMove.__init__(mv, gm, dest, logic, \
                        dest_offset=dest_offset, src_offset=src_offset)
        mv.THROW_STAGE = STAGE_0
        mv.OPEN_STAGE = STAGE_1
        mv.RELEASE_STAGE = STAGE_2
        mv.EXIT_STAGE = STAGE_3

    def _do_open(mv): raise Exception("please implment")
    def _do_release(mv): raise Exception("please implment")
    def _do_exit(mv): raise Exception("please implment")
    def _process_landing(mv):
        if mv.THROW_STAGE == mv.get('stage'): return mv.VIABLE()
        if mv.OPEN_STAGE == mv.get('stage'):
            if mv.get('t') >= mv.get('stage1->2 t fin'):
                mv.put('stage', mv.RELEASE_STAGE)
            return mv.VIABLE()
        elif mv.RELEASE_STAGE == mv.get('stage') :
            mv.put('stage', mv.EXIT_STAGE)
            mv._do_exit()
            return mv.INVIABLE()
        elif mv.RELEASE_STAGE == mv.get('stage') :
            return mv.INVIABLE()
        else: 
            raise Exception("situation not handled:", mv.get('stage'))

    def _do_every_iter(mv):pass
    def _implement_landing(mv): 
        mv._do_every_iter()
        if mv.OPEN_STAGE == mv.get('stage'): 
            mv._do_open()
        elif mv.RELEASE_STAGE == mv.get('stage'):
            mv._do_release()

class Tackle(CustomProjectileMove):
    def __init__(mv, gm, dest, logic):
        CustomProjectileMove.__init__(mv, gm, dest, logic, \
                        dest_offset=(0.15,0.1), src_offset=(0.15,0.1))
        mv.move_name = 'Tackle:'
        mv.storage_key = str(mv.uniq_id)+':tackle:'
        mv.put('stage0->1 t fin', TACKLE_SPEED)# * mv.get('dist')) 
        mv.put('stage1->2 t fin', TACKLE_LINGER) 
        mv.gm.notify_new_effect(mv, tpos=floorvec(mv.get('src')), img='tackle',\
                team=mv.team)
        mv.Ready = True
        mv.custom_reset_tiles = True
    def _do_every_iter(mv): 
        mv.gm.display.queue_reset_tile(floorvec(addvec(mv.get('src'),0.5)))
        mv.gm.display.queue_reset_tile(floorvec(addvec(mv.get('dest'),0.5)))
    def _do_open(mv):
        damage=5
        if mv.Ready: 
            mv.logic.deliver_message( msg='direct damage',\
                recipient={'pkmn_at_tile':floorvec(mv.get('dest'))},\
                data={'amount': damage} )
    def _do_release(mv): pass
    def _do_exit(mv):
        mv.gm.display.queue_reset_tile(floorvec(addvec(mv.get('src'),0.5)))
        mv.gm.display.queue_reset_tile(floorvec(addvec(mv.get('dest'),0.5)))


class PokeballSuperMove(CustomProjectileMove):
    def __init__(mv, gm, dest, logic):
        CustomProjectileMove.__init__(mv, gm, dest, logic, \
                        dest_offset=(0.3,0.3), src_offset=(0,-0.5))
        mv.move_name = 'Pokeball:'
        mv.storage_key = str(mv.uniq_id)+':pokeball:'
        mv.put('stage0->1 t fin', int(CAST_POKEBALL_SPEED*mv.get('dist'))) 
        mv.put('stage1->2 t fin', PB_OPENFRAMES * POKEBALL_OPEN_SPEED) 
        mv.gm.notify_new_effect(mv, tpos=mv.get('src'), img='pokeball', team=mv.team)
    
    def _do_open(mv):
        img_num = mv.get('t')//POKEBALL_OPEN_SPEED
        mv.gm.notify_image_update(mv, 'pokeball-fade-'+str(img_num))
        mv._do_open_()
    def _do_exit(mv):
        mv.logic.update_global('isPlayerActionable', True)

# When commonalities occur, please abstract these away.
class CatchPokeballMove(PokeballSuperMove):
    def __init__(mv, gm, dest, logic, **_unused_arguments_):
        PokeballSuperMove.__init__(mv, gm, dest, logic)
        mv.move_name += 'catch'
        mv.storage_key += 'catch'
    def _do_open_(mv):
        img_num = mv.get('t')//POKEBALL_OPEN_SPEED
        catchdamage_algorithm = mv.gm.dt * (PB_OPENFRAMES-img_num)//100 
        mv.logic.deliver_message( msg='catching',\
                recipient={'pkmn_at_tile':floorvec(mv.get('dest'))},\
                data={'amount': catchdamage_algorithm} )
    def _do_release(mv): pass

class ThrowPokeballMove(PokeballSuperMove):
    def __init__(mv, gm, dest, logic, **_unused_arguments_):
        PokeballSuperMove.__init__(mv, gm, dest, logic)
        mv.move_name += 'throw_my'
        mv.storage_key += 'throw_my'
    def _do_open_(mv): pass
    def _do_release(mv):
        k = mv.logic.belt.Pkmn.keys()
        if len(k)==0: return
        else: what_pkmn_id = k[0]
        mv.logic.deliver_message( msg='create pokemon', recipient = 'me', \
                data = {'dest':floorvec(mv.get('dest')), 'what':what_pkmn_id })
