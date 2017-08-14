import numpy as np
X=0; Y=1;
UDIR = 0;       LDIR = 1;       DDIR = 2;       RDIR = 3
UVEC=[1,0,0,0]; LVEC=[0,1,0,0]; DVEC=[0,0,1,0]; RVEC=[0,0,0,1]; xVEC=[0,0,0,0]
DIR_LONG_VECS = [UVEC, LVEC, DVEC, RVEC]
DIRECTIONS = EVENTS = [UDIR, LDIR, DDIR, RDIR]
DIR_TILE_VECS = [(0,-1), (-1,0), (0,1), (1,0)]
DIRNAMES = ['u','l','d','r']
NULL_POSITION = (-1,-1)
def Events_To_Vec(e):
    l=[]; 
    for a,b in zip(DIRECTIONS, DIR_TILE_VECS):
        if e[a]: l += [b]
    return l
def Vec_To_Event(v):
    es=[False]*len(EVENTS)
    for d in v:
        for a,b in zip(DIRECTIONS, DIR_TILE_VECS):
            if d==b: es[a]=True
    return es


def dist(p1,p2,Q): 
    if Q in [1,'manh']: 
        return abs(p1[X]-p2[X])+abs(p1[Y]-p2[Y])
    if Q in [2,'eucl']: 
        return ((p1[X]-p2[X])**2+(p1[Y]-p2[Y])**2)**0.5

def sub_aFb(a,b): return b[X]-a[X], b[Y]-a[Y]
def addpos(a,b,optn=None):
    try: 
        _,__=a[0], b[0]
        if optn in ('sub','subt','-','aFb'): return (b[X]-a[X], b[Y]-a[Y])
        if optn in ('bFa',): return (a[X]-b[X], a[Y]-b[Y])
        if optn in ('int',int): return (int(a[X]+b[X]), int(a[Y]+b[Y]))
        return (a[X]+b[X], a[Y]+b[Y])
    except: 
        try: 
            _=a[0]
            return (a[X]+b, a[Y]+b)
        except: 
            return (a+b[X], a+b[Y])
def addvec(a,b,c=None): return addpos(a,b,c)
def subpos(a,b): return addpos(a,b,'aFb')
def subvec(a,b): return subpos(a,b)
def floorvec(a,b=None):
    if b==None: return (int(a[X]), int(a[Y]))
    return (int(a), int(b))

def multc(v,c,optn=None): # reserved for c : scalar constant.
    if optn==None: return tuple([vi*c for vi in v])
    if optn==int: return tuple([int(vi*c) for vi in v])

def multpos(v,m,optn=None):
    try: 
        v[0];m[0]; 
        if optn =='//': 
            return (int(v[X]//m[X]), int(v[Y]//m[Y]))
        elif optn=='int' or optn==int:
            return (int(v[X]*m[X]), int(v[Y]*m[Y]))
        if optn =='/': 
            return ((float(v[X])/m[X]), (float(v[Y])/m[Y]))
        return (v[X]*m[X], v[Y]*m[Y])
    except: pass
    if optn==int or optn=='int': return (int(v[X]*m), int(v[Y]*m))
    elif optn in ('elemwise','e','vector'): return (v[X]*m[X], v[Y]*m[Y])
    elif optn in ('div', '/'): return (v[X]/float(m), v[Y]/float(m))
    elif optn =='//': return (int(v[X]//m), int(v[Y]//m))
    elif optn==None: return (v[X]*m, v[Y]*m)
    else: raise Exception()
def multvec(v,m,optn=None):return multpos(v,m,optn)
def divvec(v,m,optn='//'):
    if optn=='/': return (v[X]/m[X], v[Y]/m[Y])
    return multpos(v,m,optn)

def orvec(a, op, b): 
    if op=='>': op = lambda x,y: cmp(x,y)>0
    if op=='<': op = lambda x,y: cmp(x,y)<0
    if op=='>=': op = lambda x,y: cmp(x,y)>=0
    if op=='<=': op = lambda x,y: cmp(x,y)<=0
    if op=='=': op = lambda x,y: cmp(x,y)==0
    try:    return (op(a[X],b[X]) or op(a[Y],b[Y]))
    except: return (op(a[X],b) or op(a[Y],b))

def andvec(a, op, b): 
    if op=='>': op = lambda x,y: cmp(x,y)>0
    if op=='<': op = lambda x,y: cmp(x,y)<0
    if op=='>=': op = lambda x,y: cmp(x,y)>=0
    if op=='<=': op = lambda x,y: cmp(x,y)<=0
    if op=='=': op = lambda x,y: cmp(x,y)==0
    try:    return op(a[X],b[X]) and op(a[Y],b[Y])
    except: return op(a[X],b) and op(a[Y],b)

def floormod(a,b): return (int(a[Y]//b[Y])*b[Y], int(a[Y]//b[Y])*b[Y])
def roundvec(a): return (int(round(a[X])), int(round(a[Y])))


