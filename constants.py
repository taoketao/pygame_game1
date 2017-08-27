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

X=0
Y=1
NULL_POSITION = (-1,-1)

UDIR = 0
LDIR = 1
DDIR = 2
RDIR = 3
UVEC=[1,0,0,0]
LVEC=[0,1,0,0]
DVEC=[0,0,1,0]
RVEC=[0,0,0,1]
xVEC=[0,0,0,0]
DIR_LONG_VECS = [UVEC, LVEC, DVEC, RVEC]
DIRECTIONS = EVENTS = [UDIR, LDIR, DDIR, RDIR]
DIR_TILE_VECS = [(0,-1), (-1,0), (0,1), (1,0)]
DIRNAMES = ['u','l','d','r']
def index_to_ltr(i):
    return {0:'u',1:'l',2:'d',3:'r',-1:'-'}[i]

index_to_ltr = {0:'u',1:'l',2:'d',3:'r',-1:'-'}
MTNKEYS = ['l','d','r','u','-']

DEFAULT_IMAGE_OFFSET = (0.0,0.0)

RESERVABLE_SPECIES = [u'pkmn', u'plyr'] # What can reserve a tile?

NULL_RESERVATION=-2342

sql_all_AS='SELECT * FROM agent_status;'
sql_tile_locs='SELECT tx,ty,img_str,uniq_id FROM agent_status;'
sql_get_pposes='SELECT tx,ty,px,py,agent_type,img_str,uniq_id FROM agent_status;'
sql_get_tocc='SELECT tx,ty,agent_type FROM agent_status;'
sql_update_pos = '''UPDATE OR FAIL agent_status SET tx=?, ty=?, px=?, py=? 
                    WHERE uniq_id=?; '''


BLOCKING_SPECIES = [u'plyr', u'pkmn']
STD_FPS=1.0
