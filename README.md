Overview:  

  - Welcome to Pokemon Battle Arena!
    (.... err, at least the bit I got done before school started again )

  - In this **extremely highly lifelike immersive** experience, take the 
    role of a Pokemon Trainer
    striving to defeat an army of wild red Bulbasaur with your own blue
    Bulbasaur! 
    
Game Instructions:

  - Walk around with WASD or arrow keys.
  - Use your mouse to select tiles.
  - Press space to send out a Pokemon from your belt or attempt to catch
        an wild enemy Pokemon!

Play Instructions:

  - Open a terminal shell
  - Type and hit enter: 
    > git clone https://github.com/taoketao/pygame_game1/tree/public
  - You'll need Python 2.7 (due to print statements, python3 will likely 
    not work). Type this:         
    >  python -c "print 'Hello world!'" 

    If that fails, go download Python 2.7. Then, for each of the 
    dependencies below, try this command: 
    >    python -c "import DEP"     where you replace DEP with the dependency.

    If it fails, do this command: pip install DEP
    If that fails also, go install pip. 
    
    Dependencies, many of which are standard:
        pygame ,    abc ,     numpy,      sqlite3,      ConfigParser,
        PIL python imaging library: Image, ImageOps,    operator,
        random,     os (os.path) ,     sys.
    (The ones of note are pygame, which is indispensable, and sqlite3. With
    light modification you may be able to do without sys, abc, random )

    Finally, you're ready to go. To play a game, do command:
    >   python rungame.py

    And if you want to quit to restart, press (don't tap) the   q   key, or
    hit CTRL+c while in the terminal.
    

Why did I make this?
  - I've had the dream of making this game for a while, but only recently found the 
    motivation, time, and means. I personally treated it like a challenge of
    writing massively scalable code. It is inspired primarily by the Pokemon 
    Gameboy Advance games, modern MOBAs, and tactical RTS games.
  - Partway through dev, I got very excited about a backend mechanic I needed.
    In the way that Tensorflow creates a "language" of operations on which 
    a user can build a network and let Tensorflow handle all behind-the-interface 
    operations (due to its unified structure), I needed a synchronous engine
    that could still facilitate easy behavior management. Facebook's GraphQL
    also follows a similar paradigm of providing interfaces. Especially if I
    were to implement a feature I hope to add one day, that the player can
    train individual pokemon to have fully customizable behaviors. 
  - For examples of what I'm talking about, see abstractActions.py or 
    compositeActions.py for the "behind-the-interface" synchronous languaging,
    and any of the other *Actions.py classes for examples of the game mechanic
    engine idea.
  - While the idea's far from fleshed out, (and actually provides no compute
    improvement when single-threaded), I'm glad to have laid out such a
    paradigm that indicates what may be a Behavior / Game Mechanic Engine.


Dev details:
 - This game was built entirely from the ground-up in native python and a hint
    of sql. I claim no ownership over Pokemon/Nintendo property. Any questions,
    please message me. Credits for art: JoshR691, Zephiel87,  
    https://www.spriters-resource.com/custom_edited/pokemoncustoms/sheet/18433/
    https://www.spriters-resource.com/game_boy_gbc/pokemongoldsilver/sheet/9087/

 - Basic game flow: A single Game Manager runs the core game. It facilitates
    all external resource accesses, interactions between objects, IO (...),
    and the quasi-concurrency of a frame-based game. The GM has many Agents 
    that make up the core of the game as independent, interacting objects.
    Nontrivial Agents have a Logic, which is the central handler of
    Actions (which are composed into a holistic behavior footprint), States
    (which maintain dynamic data fields), Belts (which house user-side game
    objects, resources, abilities, and enviroment sensors), messages (to 
    communicate with other Agents). Logics are used specifically because
    they can handle frame-based gameplay without race conditions/collisions
    in a way that also makes behavioral programming easy and intuitive.

 - Modules:
 
    rungame:            implements the Game Manager and game essentials

    display:            renders; invoked by game manager.

    constants:          defines global-read-access constants

    utilities:          defines FP utilities, esp. concerning 'vector' math

    abstractEntities:   implements Agent and visual object supers and helpers

    agents:             implements various Agents

    logic:              implements logics

    state:              implements States and some standard initializations 

    belt:               implements Belts and some standard initializations

    sensors:            implements generic and specific Sensors

    abstractActions:    implements Action supers, helpers, bases, exemplars

    compositeActions:   implements general-purpose library of component Actions

    attackActions:      implements Actions targeted at other Agents

    motionActions:      implements Actions that move an Agent in space

    playerActions:      implements Actions specific to the Player Agent

    pokemonActions:     implements Actions specific to AI Pokemon Agents

    otherActions:       staging area for stray actions. EG: mouse follow
