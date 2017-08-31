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
        mv.gm.display.queue_reset_tile(mv.logic.view_sensor('tpos'), 'tpos')
        mv.gm.db.execute(sql_del_partial+'uniq_id=?;', (mv.uniq_id,) )
        mv.gm.entities.pop(mv.uniq_id)
#        mv.logic.belt.Spawns.pop(mv.move_name)

    # Aliases:
    def get(mv, x): return mv.logic.view_dep(x,mv)
    def put(mv, x, y): mv.logic.update_dep(x,y,mv)

# When commonalities occur, please abstract these away.
class ThrowPokeballMove(BasicMove):
    def __init__(mv, gm, dest, logic):
        BasicMove.__init__(mv, gm, logic)
#        if raw_input('pass or nah')=='n':
#            raise Exception("where did i come from hmmmmmm :)", mv.uniq_id)
#        else: pass
        mv.move_name = 'cast pokeball'
        mv.storage_key = str(mv.uniq_id)+'::'+mv.move_name

        #src = addvec(logic.view('tpos'), divvec(gm.ts(),2))
        src = addvec(logic.view_sensor('tpos'), 0.3)
        src = addvec(divvec(logic.view_sensor('ppos'), gm.ts(), 'f'), (0,-0.5))
        print 'src tpos:',src
#        dest = addvec(dest, divvec(gm.ts(),2))
        dest = addvec(dest, 0.3)
        mv.put('dest', dest) # in TPOS
        mv.put('src', src) #  in TPOS
#        mv.put('curloc', src)
        mv.put('uvec', unit_vector(sub_aFb(src,dest)))
        mv.put('dist', dist(src,dest,2))
#        mv.logic.update_dep('stage0->1 t',divvec(dist(src,dest,2),CAST_POKEBALL_SPEED))
#        mv.logic.update_dep('stage0->1 t', dist(src,dest,2))

        mv.put('t', 0)
        mv.put('stage0->1 t fin', int(CAST_POKEBALL_SPEED*mv.get('dist'))) 

#        mv.image_offset = divvec(multvec(POKEBALL_SCALE, gm.ts()), 2, '//')
#        mv.image_offset = addvec(divvec(gm.ts(),2), \
#                multvec(POKEBALL_SCALE, gm.ts()), 2)
#        mv.image_offset = addvec(divvec(gm.ts(),2), \
#                multvec(POKEBALL_SCALE, gm.ts()), 2)
        mv.gm.notify_new_effect(mv, ppos = src, img='pokeball', team=mv.team)

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
        print mv.get('src'), mv.get('dest'), sub_aFb(mv.get\
                ('src'), mv.get('dest')), mv.get('uvec'), mv.get('trail tiles')

#        if mv.uniq_id==290:
#            mv.gm._pretty_print_sql(sql_all)
#            raise Exception([(k,v,v.uniq_id) for k,v in logic.belt.Dependents.items()])


#        import sys
#        sys.exit()

#        if parent_logic:
#            mv.set_state(parent_logic._state)
#        else:
#            mv.set_state('stateless')
#
#        mv.storage['curpos'] = mv.storage['src'] = multvec(src,gm.ts())
#        mv.storage['dest'] = multvec(dest,gm.ts())
#        mv.storage['stage'] = STAGE_0
##        end_time = dist(src, dest,'eucl')//1
#        mv.storage['cur time'] = { STAGE_0: 0, }
#        mv.storage['cast time'] = { STAGE_0: CAST_POKEBALL_SPEED }
#        mv.storage['vector'] = floorvec(sub_aFb(dest,src))
#
    def reset(mv): mv.viability=EVAL_U 
    def find_viability(mv): 
        print 'cast t:', mv.get('t'), mv.gm.dt, mv.get('stage0->1 t fin')
        t = mv.get('t')
        mv.put('t', t + mv.gm.dt)
        print 'cast t:', mv.get('t'), mv.gm.dt, mv.get('stage0->1 t fin')
        if mv.get('stage')==STAGE_0 and mv.get('t')>mv.get('stage0->1 t fin'):
            mv.put('stage', STAGE_1) # alter stage conditionally
            mv.logic.update_global('isPlayerActionable', True)
#            mv.kill()
            return mv.INVIABLE()# for now
        return mv.VIABLE()


    def implement(mv):
        if mv.get('stage')==STAGE_0: 
#            next_ppos = multvec(multvec(addvec(mv.get('src'), multvec(\
#                                    mv.get('uvec'), mv.get('t'))), \
#                                    0.001), 40)
#
#
##            next_ppos = add src, multvec( mv.get(unit) , div [0->1] curt/mastert
#            next_ppos = addvec(mv.get('src'), multvec(mv.get('uvec'), \
#                    float(mv.get('t'))/mv.get('stage0->1 t fin')))
            lin = float(mv.get('t'))/mv.get('stage0->1 t fin')
            next_fractional_tpos = addvec( \
                    multvec(mv.get('src'), 1-lin), multvec(mv.get('dest'), lin))
            print next_fractional_tpos, mv.get('dest'), mv.get('src'), multvec(mv.get('uvec'),mv.get('t'))

            mv.gm.notify_pmove(mv, multvec(next_fractional_tpos, mv.gm.ts()))
#            mv.gm._pretty_print_sql(sql_all)
#            print mv.gm.db.execute(sql_all).fetchall()
            map(lambda dir_tile : mv.gm.display.queue_reset_tile(addvec(\
                dir_tile, next_fractional_tpos)), mv.get('trail tiles'))
            for t in mv.get('trail tiles'):
                print '\t',addvec(t, next_fractional_tpos), 
                mv.gm.display.queue_reset_tile(floorvec(addvec(t, next_fractional_tpos)))
            print next_fractional_tpos
        else:
            raise Exception()



#        S = mv.storage
#        if S['cur time'][S['stage']]>=S['cast time'][S['stage']]:
#            S['stage'] = next_stage(S['stage'])
#        if S['stage'] == STAGE_0:
#            mv.gm.notify_reset_previous_image(ppos=S['curpos'])
#            S['cur time'][STAGE_0] += mv.gm.dt#S['cast speed']*
##            S['vector'] = multvec((sub_aFb(S['dest'], S['src'])), \
##                        S['cur time'][STAGE_0]/S['end time'][STAGE_0], int)
#            #next_ppos = addvec(S['src'],S['vector'])
#            next_ppos = addvec(S['src'], multvec(S['vector'], \
#                        S['cur time'][STAGE_0]/S['cast time'][STAGE_0], int))
#            mv.gm.notify_pmove(mv, next_ppos)
#            S['curpos'] = next_ppos
