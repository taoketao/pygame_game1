EVAL_T = 444444
EVAL_F = 555555
EVAL_U = 6666666
EVAL_R = 777777777
EVAL_ERR = 88888
EVAL_INIT = 99999
WHICH_EVAL = {\
    EVAL_T:'T',
    EVAL_F:'F',
    EVAL_U:'U',
    EVAL_R:'R',
    EVAL_ERR:'ERR',
    EVAL_INIT:'INIT'}
EVALS=[EVAL_T, EVAL_F, EVAL_U, EVAL_R, EVAL_ERR, EVAL_INIT]

X=0
Y=1
NULL_POSITION = (-1,-1)

UDIR = 0
LDIR = 1
DDIR = 2
RDIR = 3
SP_ACTION = 4;  PLYR_ACTIONS = [SP_ACTION]
UVEC=[1,0,0,0]
LVEC=[0,1,0,0]
DVEC=[0,0,1,0]
RVEC=[0,0,0,1]
xVEC=[0,0,0,0]
DIR_LONG_VECS = [UVEC, LVEC, DVEC, RVEC]
DIRECTIONS = EVENTS = [UDIR, LDIR, DDIR, RDIR]
DIR_TILE_VECS = [(0,-1), (-1,0), (0,1), (1,0)]
DIRVECS_TO_STR = {(0,1):'u',(1,0):'l',(-1,0):'r',(0,-1):'d'}
DIRNAMES = ['u','l','d','r']
def index_to_ltr(i):
    return {0:'u',1:'l',2:'d',3:'r',-1:'-'}[i]

index_to_ltr = {0:'u',1:'l',2:'d',3:'r',-1:'-'}
MTNKEYS = ['l','d','r','u','-']

DEFAULT_IMAGE_OFFSET = (0.0,0.0)


NULL_RESERVATION=-2342
RESERVABLE_SPECIES = [u'pkmn', u'plyr'] # What can reserve a tile?
NULL_UNIQ_ID=-2302

# These macros: for rendering, queries, etc.
BLOCKING_SPECIES = (u'plyr', u'pkmn') 
EFFECT_SPECIES = ( u'bar', u'move')
AFTEREFFECT_SPECIES = ( u'target', )

sql_all='SELECT * FROM agent_status;'
sql_tile_locs='SELECT tx,ty,img_str,uniq_id FROM agent_status;'
sql_get_pposes='SELECT tx,ty,px,py,species,img_str,uniq_id FROM agent_status;'
sql_get_tocc ='SELECT tx,ty,species FROM agent_status;'
sql_get_tocc2 ='SELECT tx,ty FROM agent_status;'
sql_get_tpos_of_who ='SELECT tx,ty FROM agent_status WHERE uniq_id=?;'
sql_query_tile = '''SELECT species, uniq_id, team FROM agent_status \
                    WHERE tx=? AND ty=?;'''
sql_query_tile_for_team = '''SELECT uniq_id FROM agent_status \
                    WHERE tx=? AND ty=? AND team=?;'''
sql_query_tile_for_Nteam = '''SELECT uniq_id FROM agent_status \
                    WHERE tx=? AND ty=? AND team=?;'''
sql_update_pos = '''UPDATE OR FAIL agent_status SET tx=?, ty=?, px=?, py=? 
                    WHERE uniq_id=?; '''
sql_img_update = 'UPDATE OR FAIL agent_status SET img_str=? WHERE uniq_id=?;'
sql_ins = 'INSERT INTO agent_status VALUES (?,?,?,?,?,?,?,?);'
sql_del_partial = 'DELETE FROM agent_status WHERE '

#*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_
#*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_
#*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*
SQL_get_tile_img_info = '''SELECT base_tile_img, obst_tile_img FROM map_info 
                            WHERE tx=? AND ty=? '''
SQL_map_settings = '''SELECT tx,ty,base_tile_img, obst_tile_img FROM map_info'''
SQL_get_all_occs ='SELECT tx,ty FROM map_occs;'
SQL_get_ent_ppos ='SELECT px,py FROM entities WHERE uniq_id=?;'
SQL_get_ent_spec_team ='SELECT species, team FROM entities WHERE uniq_id=?;'
SQL_is_blocking = 'SELECT tile_occupying FROM entities WHERE uniq_id=?;'
SQL_tile_occupied = 'SELECT COUNT(*) FROM map_occs WHERE tx=? AND ty=? ;'
SQL_get_pposes='SELECT px,py,species,img_str,uniq_id FROM entities;' # etc
#*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_
SQL_set_ent_ppos = 'UPDATE OR FAIL entities SET px=?, py=? WHERE uniq_id=?;'
SQL_img_update = 'UPDATE OR FAIL entities SET img_str=? WHERE uniq_id=?;'
SQL_map_set_occ_standing_loc = \
        'UPDATE OR FAIL map_occs SET standing_occupant=? WHERE tx=? AND ty=?;'
SQL_map_set_occ_moveto_loc = \
        'UPDATE OR FAIL map_occs SET movingto_occupant=? WHERE tx=? AND ty=?;'
SQL_map_set_occ_movefrom_loc = \
        'UPDATE OR FAIL map_occs SET movingfrom_occupant=? WHERE tx=? AND ty=?;'
#SQL_map_set_standing_occ = \
#        'UPDATE OR FAIL map_occs SET standing_occupant WHERE tx=?, ty=?;'

#*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_
#*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_
#*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_*()_
BAR_SCALING_FACTOR = 0.4
BAR_WIDTH = 4

STAGE_0, STAGE_1, STAGE_2, STAGE_3, STAGE_4, STAGE_5 = 990,991,992,993,994,995
def next_stage(s): 
    return {STAGE_0:STAGE_1, STAGE_1:STAGE_2, 
            STAGE_2:STAGE_3, STAGE_3:STAGE_4, 
            STAGE_4:STAGE_5, STAGE_5:None}  [s]

PB_OPENFRAMES = 30
POKEBALL_OPEN_SPEED = 16
CAST_POKEBALL_SPEED = 210 # in scaling ticks per tile. UNREALISTIC sanity
POKEBALL_SCALE = (0.35, 0.4) # looks solid when tile_size = (40,35)

TACKLE_SCALE = (0.7, 0.8)
TACKLE_SPEED = 300
TACKLE_LINGER = 100

PKMN_WANDER_DELAY = 1600
