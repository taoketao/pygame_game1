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
                    RespectLock(ap.logic),\
                    GetKO(ap.logic), 
                    GetCaught(ap.logic), \
                    Delay(ap.logic), \
#                    Tackle(ap.logic), \
                    Wander(ap.logic) ] )
    def find_viability(ap): 
        return ap.GETVIA(ap.root)
    def implement(ap): 
        assert(ap.viability==EVAL_T)
        ap.root.implement()
    def reset(ap):  ap.viability = EVAL_U; ap.root.reset()


class GetCaught(ActionPicker):
    def __init__(ap, logic): ActionPicker.__init__(ap, logic)
    def find_viability(ap):
        if not 'caughtbar' in ap.logic.belt.Dependents.keys():
            return ap.INVIABLE()
        cb = ap.logic.belt.Dependents['caughtbar'].view_pct()
        if cb <= 0: return ap.VIABLE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.logic.deliver_message( msg='you caught me',\
                recipient = {'_id':ap.logic.view('most recently caught by')}, \
                data = { 'pkmn_id' : ap.logic.view('pkmn_id'),\
                    'health_cur' : ap.logic.belt.health.view_metric()[0],\
                    'health_max' : ap.logic.belt.health.view_metric()[1] } )
        ap.logic.kill()

class GetKO(ActionPicker):
    def __init__(ap, logic): ActionPicker.__init__(ap, logic)
    def find_viability(ap):
        if not 'healthbar' in ap.logic.belt.Dependents.keys():
            return ap.INVIABLE()
        cb = ap.logic.belt.Dependents['healthbar'].view_pct()
        if cb <= 0: return ap.VIABLE()
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        ap.logic.deliver_message( msg='kill', recipient='me', data={} )
        ap.logic.kill()




class Tackle(ActionPicker):
    def __init__(ap, logic):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
#        ap.dir_posvecs = [m.posvec for m in logic.view('motions').values()\
#                            if m.index>=0]
        ap.dir_vecs = DIRVECS_TO_STR # eg (0,1)->u

    def find_viability(ap):
#        if random.random()<0.3: return ap.INVIABLE()
        dirs = ap.dir_vecs.keys()
        random.shuffle(dirs)
        curtpos = ap.logic.view_sensor('tpos')
        for cvec in dirs:
            dest = sub_aFb(cvec, curtpos)
            res = ap.logic.view_sensor('get agents at tile', tid=dest)
            print 'tackle:',res, dest
            if not res: continue
            for u_id in res:
                team, species = gm.db.execute(SQL_get_ent_spec_team, \
                                (u_id,)).fetchone()
                if team==ap.logic.agent.team: continue
                if species=='plyr': continue
                if not team in ap.gm.pkmn_damage_teams: continue

                ap.logic.update_global('img choice', ap.dir_vecs[cvec])
                ap.logic.update_global('delay', ap.logic.view('delay') + \
                            ap.logic.view('root delay'))
                return ap.GETVIA(ap.logic.spawn_new('tackle','move',dest=dest))

#            for ti,t in enumerate(res['team']):
#                if t==ap.logic.agent.team: continue
#                if res['species'][ti]=='plyr': continue
#                if t not in ap.gm.pkmn_damage_teams: continue
#                ap.logic.update_global('img choice', ap.dir_vecs[cvec])
#                ap.logic.update_global('delay', ap.logic.view('delay') + \
#                            ap.logic.view('root delay'))
#                return ap.GETVIA(ap.logic.spawn_new('tackle','move',dest=dest))
        return ap.INVIABLE()
    def implement(ap):
        assert(ap.viability==EVAL_T)
        print '\t',ap.agent.uniq_name,'tackling...'
        ap.logic.agent.set_img(ap.logic.view('img choice'))

class Wander(ActionPicker):
    ''' Wander: pick a random valid direction and move there. Does not attempt
    to avoid collisions on reserved tiles (which is otherwise case-handled. '''
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


class PickRandMove(ActionPicker):
    def __init__(ap, logic, components):
        ActionPicker.__init__(ap, logic)
        ap.write_state_access = True
        ap.logic.update_ap('mov choice', 'd', ap.uniq_id)
        ap.logic.update_global('img choice', 'd')
        ap.components = components

    def find_viability(ap):
        indices = list(range(len(ap.components)))
        random.shuffle(indices)
        for ci in indices:
            a = ap.components[ci]
            if EVAL_T==a.find_viability(): 
                ap.logic.update_ap('mov choice', a.name, ap.uniq_id)
                ap.logic.update_global('img choice', a.name)
                print ap.logic.agent.uniq_name,'identified valid action:', a.name
                return ap.VIABLE()
        ap.logic.update_ap('mov choice', '-', ap.uniq_id)
        return ap.Verify(ap.logic.belt.Actions['-'])
    def implement(ap):
        assert(ap.viability==EVAL_T)
        print '\t',ap.agent.uniq_name,'wandering...'
        ap.logic.update_global('delay', ap.logic.view('delay') + \
                            ap.logic.view('root delay'))
        prevtloc = ap.logic.view_sensor('tpos')
        ap.logic.belt.Actions[ap.logic.view_my('mov choice', ap.uniq_id)].implement()
        ap.logic.agent.set_img(ap.logic.view('img choice'), prevtloc)

    def reset(ap): 
        ap.viability = EVAL_U; 
        for c in ap.logic.belt.Actions.values(): c.reset()
        ap.logic.update_ap('mov choice', EVAL_U, ap.uniq_id) 

