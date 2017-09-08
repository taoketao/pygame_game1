
# Level DEVELOPMENT.  This affects game data.

t='a'; g='g'; d='d' # convenience
#               1  2  3  4  5  6  7  8  9
LEVEL_MAP = [ [ t, t, t, t, t, t, t, t, t ], \
              [ t, g, g, g, g, g, g, g, t ], \
              [ t, g, g, g, g, d, d, g, t ], \
              [ t, g, g, g, g, d, g, d, t ], \
              [ t, g, g, g, g, d, d, g, t ], \
              [ t, g, g, g, g, d, g, d, t ], \
              [ t, g, g, g, g, d, g, d, t ], \
              [ t, g, g, g, g, g, g, g, t ], \
              [ t, g, g, g, g, g, g, g, t ], \
              [ t, g, g, g, g, g, g, g, t ], \
              [ t, t, t, t, t, t, t, t, t ]  ]
TILE_INFO = {\
    t: { 'name':'apr_tile', 'blocks_walking':True, 'base_image':g, 'obst_image':t, \
            'filename':'apricorn_img.png' },   \
    d: { 'name':'drt_tile', 'blocks_walking':False, 'base_image':d, \
            'filename':'dirt_tile_img.png' },   \
    g: { 'name':'grs_tile', 'blocks_walking':False, 'base_image':g , \
            'filename':'grass_tile_img.png' }
}
TILE_INFO = {\
    t: { 'blocks_walking':True,  'base_image':g, 'obst_image':t },   \
    d: { 'blocks_walking':False, 'base_image':d },   \
    g: { 'blocks_walking':False, 'base_image':g }
}

GLOBAL_SETTINGS = {}

#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-

#   Moves, pokemon and otherwise. Note to self: for now, just make defaults.
#   Energies: Elemental, Physical, Natural, Supernatural

m_Tackle = {'name':         'Tackle',
            'img_scale':    (0.7,0.8),
            'velocity':     300, 
            'imgs':         ['burst'],
            'linger':       100,  
            'Type':         'Normal', 
            'damage':       35, 
            'energy_cost':  {'Physical':1}  ,
        }
m_VineWhip = {  'name':'VineWhip',
                'img_scale':(1,1),     
                'Type':'Grass', 
                'damage':35  ,
                'energy_cost':{'Natural':2, 'Elemental':1}, 
            }



#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-#-$-

#   Pokemon prefabs

POKEMON_PREFAB_SETTINGS = [\
    'this slot is intentionally left blank',\
    { 'index':1 , 
      'name':'Bulbasaur', 
      'base_health':1000, 
      'action_delay':1400, \
      'moves':[ m_Tackle, m_VineWhip ], 
      'intrinsic_energy':{'Natural':1,'Elemental':1}}
]
