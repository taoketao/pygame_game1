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
