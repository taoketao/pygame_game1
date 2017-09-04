import abstractEntities as ae_module



class MessageHandler(ae_module.Entity):
    def __init__(mh, logic):
        ae_module.Entity.__init__(mh, logic.gm)
        mh.logic=logic
        mh.message_queue = []

    ''' MSG_xyz functions: these are the eventual messages that this
        recipient implements with respect to itself; senders must 'sign'.'''
    def MSG_catching(mh, msg, amount, sender):
        ''' MSG_catching: A Pkmn receives catching 'damage'.  ''' 
        print "catching message has been received and identified."
        assert( msg=='catching' )
        caughtbar = mh.logic.belt.Dependents['caughtbar']
        caughtbar.update_metric(-amount, 'delta')
        mh.logic.update_global('most recently caught by', \
                             sender.agent.uniq_id)
        mh.logic.update_global('caugh_counter', caughtbar.view_metric()[0])

    def MSG_got_caught(mh, msg, pokedex, health_cur, health_max):
        ''' MSG_catching: A Pkmn has been caught and ''' 
        assert( msg=='you caught me' )
        mh.logic.belt.Pkmn[len(mh.logic.belt.Pkmn)+1] = {\
            'pokedex' : pokedex, \
            'health_cur' : health_cur ,\
            'health_max' : health_max, }

    def MSG_spawn_pokemon(mh, msg, what_slot, dest):
#        name = 'Pkmn'+str(mh.logic.belt.pkmn_counter)
#        mh.gm.addNew('Agents',
        mh.logic.spawn_new('create pokemon', 'move',\
                        which_slot=what_slot, init_tloc=dest)

    def MSG_sigkill(mh, msg, _):
        assert(msg=='kill')
        mh.gm.entities.pop(mh.logic.agent.uniq_id)
        mh.logic.kill()

    def handle_messages(mh):
        # Read and process messages:
        while len(mh.message_queue)>0:
            Msg = mh.message_queue.pop(0)
#            print 'received message:',msg
            {   'catching':         mh.MSG_catching,
                'you caught me':    mh.MSG_got_caught,
                'create pokemon':   mh.MSG_spawn_pokemon,
                'kill':             mh.MSG_sigkill,
            }[Msg['msg']](**Msg)

    def _receive_message(mh, msg, **args):  # READ
        # This should process messages for redirection into dedicated functions:
        # handles data but NO metadata!    Wipes/converts data substantially.
        print "a message",msg,"has been received and identified."
        custom_args = {'msg':msg}
        if msg=='kill': pass
        if msg=='catching': # apply catch 'damage'
            custom_args['amount']=args['data']['amount']
            custom_args['sender']=args['data']['sender']
        if msg=='you caught me': # notify that [you] 
            custom_args['health_cur']=args['data']['health_cur']
            custom_args['health_max']=args['data']['health_max']
            custom_args['pokedex']=args['data']['pkmn_id']
        if msg=='create pokemon':
            custom_args['dest']=args['data']['dest']
            custom_args['what_slot']=args['data']['what']
        mh.message_queue.append(custom_args)

    def _deliver_message(mh, msg, **args): # WRITE
        ''' This ought to identify who receives messages: Metadata not data.'''
        print "a message",msg,'/',args,"is being delivered."

        args['data']['sender'] = mh.logic

        if msg=='kill' and msg['recipient']=='me':
            mh.logic.receive_message(msg, **args)
        elif msg=='catching':
            ents = [who[0] for who in mh.gm.query_tile_for_team(\
                    args['recipient']['pkmn_at_tile'], '--wild--')] 
            for e_id in ents:
                if not mh.gm.entities[e_id].isMasterAgent: continue
                mh.gm.entities[e_id].receive_message(msg, **args)
        elif msg=='you caught me':
            mh.gm.entities[args['recipient']['_id']].receive_message(msg, **args)
        elif msg=='create pokemon': 
            assert(args['recipient']=='me')
            mh.logic.receive_message(msg, **args)
        else:
            raise Exception(msg, args)
           # assert recipient.keys() subset: {target_tile, target_ent_ids}


# logic::spawn_new



 # b
