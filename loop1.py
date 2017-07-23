import pygame, ConfigParser, sys, os
import numpy as np
import pygame.locals, pygame.key
from math import floor
import sqlite3 as sql

path='/Users/morganbryant/Desktop/Files/17/07_July/game/'

def isint(x): return floor(x)==x
class Game(object):

    class Scaling(object):
        def __init__(self1, scale=1):
            if isint(16*scale):
                self1.scale=int(16*scale)
            else:
                self1.scale=16
                print("Invalid scaling scale; default 1 used.")
        def tileSize(self1, x):
            return 1+self1.scale*int(x)

    def __init__(self, whichGameConfigFile='./config1.ini'):
        self.init_game(whichGameConfigFile)

    def init_database(self, db_diskloc=":memory:"):
        #self.connection = sql.connect("./.runtime_database.db") # ":memory:"
#        if not db_diskloc==":memory:":
#            if (not os.path.exists(db_diskloc) and 
#                    not os.path.isdir(db_diskloc): pass
#            else: db_diskloc = ":memory:"
        try: self.connection = sql.connect( db_diskloc )
        except: raise Exception("Bad database disk location: %s" % db_diskloc)
        self.db = self.connection.cursor()
        initialize_db_commands = [\
            """  CREATE TABLE tiles (tile_id INT PRIMARY KEY NOT NULL, 
                                    name TEXT NOT NULL, 
                                    filename TEXT NOT NULL, 
                                    block_player BOOLEAN 
                                    ); """, \
            """  CREATE TABLE tilemap (                
                    idx INT NOT NULL,           idy INT NOT NULL,
                    recttop INT,                rectleft INT, 
                    rectbot INT ,               rectright INT,
                    tile_name TEXT,             tile_id INT ); """
                ]
        for cmd in initialize_db_commands:
            self.db.execute(cmd)

    def getTileByName(self, char):
        # Get one well-scaled image identified by its string name. 
        return self._image_stores[ self.db.execute('''SELECT tile_id 
                    FROM tiles WHERE name==?; ''', (char)).fetchone()[0]]

    def load_tile_table(self):
        # Load tiles and map from config file. Store tile imgs, draw init map.
        self._image_stores = {}
        ts = self.scaler.tileSize
        for tname in self.cp.get('tiles','alltiles'):
            filename = self.cp.get(tname,'filename')
            uniqID = int(self.cp.get(tname, 'uniqID' ))
            self.db.execute( ''' INSERT INTO 
                    tiles   ( tile_id,  name, filename, block_player)
                    VALUES  ( ?, ?, ?, ? ) ; ''', 
                    (uniqID, tname, filename, bool(self.cp.get(tname,'block')))
            );
            image = pygame.image.load(filename).convert_alpha()
            image.fill((255, 255, 255, 255), None, pygame.BLEND_RGBA_MULT)
            image = pygame.transform.scale(image, (ts(1),ts(1)))
            self._image_stores[uniqID] = image

        mapcode = self.cp.get("map","map")
        gamemap = np.empty(self.mapsize)
        curR, curC = 0,0
        for char in mapcode:
            if char=='\n': 
                curC += 1
                curR = 0
                continue
            gamemap[curR,curC] = self.cp.get(char, 'uniqID')
            if char=='a':
                self.screen.blit(self.getTileByName('g'), (ts(curR), ts(curC)))
            self.screen.blit(self.getTileByName(char), (ts(curR), ts(curC)))

            self.db.execute(""" INSERT INTO tilemap ( idx, idy, recttop, rectleft, 
                    rectbot, rectright, tile_name) VALUES ( ?,?,?,?,?,?,? ); """,
                    (curC, curR, ts(curC), ts(curR), ts(curC+1), ts(curR+1),
                    char))
            print( "TLBR", ts(curC),ts(curR),ts(1+curC),ts(1+curR))
            curR += 1
                
        
    def init_game(self, whichGameConfigFile): # Game constructor initialization.
        # Source config files 
        self.conffile = whichGameConfigFile
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(path + self.conffile)
        # Spin up databases
        self.init_database()
        # Set global scaling standards
        self.scaler = self.Scaling(scale=1.5)
        X = self.scaler.tileSize(self.cp.get("mapsize",'x'))
        Y = self.scaler.tileSize(self.cp.get("mapsize",'y'))
        self.mapsize = (X,Y)
        # Setup pygame essentials: init, start screen, fill screen, render.
        pygame.init()
        self.screen = pygame.display.set_mode(self.mapsize)
        self.screen.fill((0,0,0))
        self.load_tile_table()
        pygame.display.flip() 
        # Internal constants
        self.old_move_dir = [0,0]

    def redraw_tiles_under(self, a_rect): 
        # Redraw tiles under a moved agent that used to be bounded by a_rect.
        for X in [a_rect.x, a_rect.x+a_rect.w]:
            for Y in [a_rect.y, a_rect.y+a_rect.h]:
                res = self.db.execute( """ 
                    SELECT    tile_name, recttop, rectleft, rectbot, rectright
                    FROM      tilemap    WHERE 
                    recttop>=?   AND  rectbot<=?    AND
                    rectleft>=?  AND  rectright<=?    ;""",
                    (a_rect.x, a_rect.x, a_rect.y, a_rect.y))
                print "TLBR",res.fetchall(), a_rect
                for c,x,y,_,__ in res.fetchall():
                    self.screen.blit(self.getTileByName(c), x,y)
        

    def run_game_frame(self, locR, img):
        prevlocR = locR
        keys_down = pygame.key.get_pressed() 
        if keys_down[pygame.K_q]:       return False
        self.new_mv = [0,0]
        if keys_down[pygame.K_UP]:      self.new_mv[1] -= 1 
        if keys_down[pygame.K_DOWN]:    self.new_mv[1] += 1 
        if keys_down[pygame.K_RIGHT]:   self.new_mv[0] += 1 
        if keys_down[pygame.K_LEFT]:    self.new_mv[0] -= 1 
        tmp_oldmv = self.old_move_dir[:]
        if sum([abs(x) for x in self.new_mv])==0:
            self.old_mv = self.new_mv
        elif sum([abs(x) for x in self.new_mv])==1:
            self.old_mv = self.new_mv
            locR[0] += 5 * self.new_mv[0]
            locR[1] += 5 * self.new_mv[1]
        else:
            locR[0] += 5 * self.old_mv[0]
            locR[1] += 5 * self.old_mv[1]
        self.redraw_tiles_under(prevlocR)
        self.screen.blit(img, locR)
        return True

if __name__=='__main__':
    cur_sess_game = Game()
    clock=pygame.time.Clock()
    initpos = [m//2+1 for m in cur_sess_game.mapsize]
    plyr_img = pygame.image.load('./player/1.png')
    plyr_loc = pygame.Rect(initpos, plyr_img.get_size())

    cont=True
    while pygame.event.wait().type != pygame.locals.QUIT and cont:
        clock.tick(10)
        cont = cur_sess_game.run_game_frame(plyr_loc, plyr_img)
        pygame.display.flip()
    pygame.quit()
