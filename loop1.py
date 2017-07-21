import pygame, ConfigParser, sys
import numpy as np
import pygame.locals
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
        self.conffile = whichGameConfigFile
        self.init_database()
        self.scaler = self.Scaling(scale=1.5)
        pygame.init()
        self.init_game()

    def init_database(self):
        #self.connection = sql.connect("./.runtime_database.db") # ":memory:"
        self.connection = sql.connect( ":memory:" )
        self.db = self.connection.cursor()
        initialize_db_commands = [\
            """  CREATE TABLE tiles (tile_id INT PRIMARY KEY NOT NULL, 
                                    name TEXT NOT NULL, 
                                    filename TEXT NOT NULL, 
                                    block_player BOOLEAN
                                    ); """
                ]
        for cmd in initialize_db_commands:
            self.db.execute(cmd)

    def getTileByName(self, char):
        return self._image_stores[ self.db.execute('''SELECT tile_id 
                    FROM tiles WHERE name==?; ''', (char)).fetchone()[0]]

    def load_tile_table(self):
        # TODO: replace section with SQL database.
        self._image_stores = {}
        ts = self.scaler.tileSize
        for tname in self.cp.get('tiles','alltiles'):
            filename = self.cp.get(tname,'filename')
            uniqID = int(self.cp.get(tname, 'uniqID' ))
            self.db.execute( ''' INSERT INTO 
                    tiles   ( tile_id,  name, filename,  block_player)
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
            curR += 1
                
        
    def init_game(self):
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(path + self.conffile)

        X = self.scaler.tileSize(self.cp.get("mapsize",'x'))
        Y = self.scaler.tileSize(self.cp.get("mapsize",'y'))
        self.mapsize = (X,Y)
        self.screen = pygame.display.set_mode(self.mapsize)
        self.screen.fill((0,0,0))
        self.load_tile_table()
        pygame.display.flip()

    def run_game(self):
        for event in pygame.event.get():
            print (event.type)
        

if __name__=='__main__':
    cursess_game = Game()
    clock=pygame.time.Clock()
    while pygame.event.wait().type != pygame.locals.QUIT:
        clock.tick(10)
        cursess_game.run_game()
