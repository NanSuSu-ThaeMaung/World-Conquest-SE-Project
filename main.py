import pygame, random, time
from pygame.locals import *
from pygame.math import Vector2

pygame.init()

# Initial window dimensions
winRes = (1152, 648)
winWidth = winRes[0]
winHeight = winRes[1]
winCaption = 'World Conquest'

win = pygame.display.set_mode((winWidth, winHeight))
pygame.display.set_caption(winCaption)

# Global lists
objects = []
territories = []
plrTerritories = []
turnOrder = []

dice = {
    'blue': None,
    'red': None,
    'green': None,
    'purple': None,
    'yellow': None
}

continents = {
    'North America': ['Northwest Territory', 'Alberta', 'Alaska', 'Ontario', 'Greenland', 'Eastern Canada',
                      'Western US', 'Eastern US', 'Central America'],
    'South America': ['Venezuela', 'Brazil', 'Argentina', 'Peru'],
    'Europe': ['Great Britain', 'Northern Europe', 'Southern Europe', 'Western Europe', 'Iceland',
               'Scandinavia', 'Russia'],
    'Africa': ['Egypt', 'East Africa', 'Central Africa', 'North Africa', 'South Africa', 'Madagascar'],
    'Asia': ['Middle East', 'Afghanistan', 'Ural', 'Siberia', 'Yakutsk', 'Kamchatka', 'Irkutsk', 'Mongolia',
             'Japan', 'China', 'India', 'Southeast Asia'],
    'Australia': ['Indonesia', 'Western Australia', 'Eastern Australia', 'New Guinea'],
}

# Players that own all territories on a continent recieve these bonus troops when drafting
continentBonus = {
    'North America': 5,
    'South America': 2,
    'Europe': 5,
    'Africa': 3,
    'Asia': 7,
    'Australia': 2,
}

players = {
    'blue': None,
    'red': None,
    'green': None,
    'purple': None,
    'yellow': None
}

# Colours
teamColours = {
    'blue': (25,40,255),
    'red': (255,40,25),
    'green': (25,255,40),
    'purple': (230,25,255),
    'yellow': (230,255,25)
}

plrTeam = 'blue'

# Default font
font30 = pygame.font.Font(None, 30)

### Load classes
class Camera():
    def __init__(self):
        self.x, self.y = winWidth/2, winHeight/2
        self.vel = 7

        self.shakeVolume = 0
        self.shakeChange = 0
        self.maxShake = 30

        self.testPressed = False

    def move(self):
        shift = self.vel

        if keyInp[pygame.K_EQUALS]:  # Zoom in
            if not self.testPressed:
                mp.resize(1.5, 0)
                self.testPressed = True
        elif keyInp[pygame.K_MINUS]:  # Zoom out
            if not self.testPressed:
                mp.resize(1/1.5, 0)
                self.testPressed = True
        else:
            self.testPressed = False

        ## WASD keys to pan around the map (if zoomed in)
        if keyInp[pygame.K_w] and mp.y+shift < 0:
            self.y -= shift
            for obj in objects:
                obj.shift(0, shift, (0,0))

        if keyInp[pygame.K_s] and mp.y+mp.image.get_height()-shift > winHeight:
            self.y += shift
            for obj in objects:
                obj.shift(0, shift *-1, (0,0))

        if keyInp[pygame.K_a] and mp.x+shift < 0:
            self.x -= shift
            for obj in objects:
                obj.shift(shift, 0, (0,0))

        if keyInp[pygame.K_d] and mp.x+mp.image.get_width()-shift > winWidth:
            self.x += shift
            for obj in objects:
                obj.shift(shift *-1, 0, (0,0))

        # Screen Shake: Moves obj back and forth for 'shake' effects
        if self.shakeVolume > 0:
            if self.shakeChange > 0:
                # Shift objects to the left
                self.shakeChange -= self.shakeVolume
                self.x -= self.shakeVolume
                for obj in objects:
                    obj.shift(-self.shakeVolume, 0, (0,0))
                self.shakeVolume -= 1

            elif self.shakeChange < 0:
                # Shift objects to the right
                self.shakeChange += self.shakeVolume
                self.x += self.shakeVolume
                for obj in objects:
                    obj.shift(self.shakeVolume, 0, (0,0))
                self.shakeVolume -= 1

            else:
                # Shift objects to the right
                self.shakeChange += self.shakeVolume
                self.x += self.shakeVolume
                for obj in objects:
                    obj.shift(self.shakeVolume, 0, (0,0))
                self.shakeVolume -= 1

    def shake(self, amt):
        # Set initial screen shake amount
        self.shakeVolume += amt
        if self.shakeVolume > self.maxShake:
            self.shakeVolume = self.maxShake

    def goToStart(self):
        # Sets initial camera position by shifting objects to centre
        self.x -= camStartPos[0]
        self.y -= camStartPos[1]
        for obj in objects:
            obj.shift(-camStartPos[0], -camStartPos[1], (0, 0))


class Map():
    def __init__(self):
        self.scale = 0.3
        self.ogImage = pygame.image.load('Assets/map.png')
        self.image = pygame.transform.scale(self.ogImage, (int(self.ogImage.get_width() * self.scale),
                                                           int(self.ogImage.get_height() * self.scale)))
        self.image = self.image.convert()

        self.x = winWidth / 2 - self.image.get_width() / 2
        self.y = winHeight / 2 - self.image.get_height() / 2
        self.mlt = 1

        objects.append(self)

    ## Procedure used by Camera(), shifts objects and map depending on Zoom level or fullscreen
    def resize(self, mlt, scl):
        # Max and Min zoom multipliers
        if self.mlt*mlt > 2.5 or self.mlt*mlt < 0.9:
            return

        if scl: # Scale changes in windowed to fullscreen shift
            sclChange = 2.25 if self.scale < scl else 1/2.25
            self.scale = scl

        # Update map size
        self.mlt *= mlt
        self.image = pygame.transform.scale(self.ogImage, (int(self.ogImage.get_width() * self.scale * self.mlt),
                                                           int(self.ogImage.get_height() * self.scale * self.mlt)))
        self.image = self.image.convert()

        # Shift obj x,y positions by multiplier
        shift = [self.x, self.y]
        for obj in objects:
            obj.shift(-shift[0], -shift[1], (0,0))
            obj.x *= mlt
            obj.y *= mlt
            if scl:
                obj.x *= sclChange
                obj.y *= sclChange

        ## Find the bounds so that camera doesn't pan off of the game map
        size = 0.5 if self.mlt > 1.4 else -0.5
        topleft = [shift[0] + (self.ogImage.get_width()*self.scale - self.image.get_width())*size,
                   shift[1] + (self.ogImage.get_height()*self.scale - self.image.get_height())*size]
        bounds = [topleft[0] + self.image.get_width() - winWidth,
                  topleft[1] + self.image.get_height() - winHeight]
        topleft[0], topleft[1] = topleft[0] if topleft[0] > 0 else 0, topleft[1] if topleft[1] > 0 else 0
        bounds[0], bounds[1] = bounds[0] if bounds[0] < 0 else 0, bounds[1] if bounds[1] < 0 else 0
        # topleft, bounds = [0,0], [0,0]
        # print(topleft, bounds)
        # Shift objects to keep within bounds
        shift[0] += (self.ogImage.get_width()*self.scale - self.image.get_width()) * size
        shift[1] += (self.ogImage.get_height()*self.scale - self.image.get_height()) * size
        for obj in objects:
            obj.shift(shift[0] - bounds[0] - topleft[0], shift[1] - bounds[1] - topleft[1], (0, 0))

    # Universal object shift procedure
    def shift(self, x, y, fsMove):
        self.x += x + fsMove[0]
        self.y += y + fsMove[1]

    # Displays objects and images on screen
    def draw(self):
        win.blit(self.image, (int(self.x), int(self.y)))


class Country():
    conListFile = open('Assets/countryConnections.txt', 'r')
    connectionList = conListFile.read()

    nameFonts = []
    sizes = [10 * (i + 1) for i in range(7)]
    for s in sizes:
        nameFonts.append(pygame.font.Font('Assets/sylfaen.ttf', s))

    def __init__(self, x, y, name, team, pop, connections):
        self.x = x
        self.y = y
        self.name = name
        self.team = team
        self.pop = pop
        self.connections = connections

        # Mark if player owned
        self.colour = teamColours[team]
        if self.team == plrTeam:
            plrTerritories.append(self)

        # Find home continent
        self.continent = ''
        for c in continents:
            if self.name in continents[c]:
                self.continent = c
                break

        self.mouseHover = 0

        # Add to global lists
        territories.append(self)
        objects.append(self)

    # Run every frame: Check if mouse is hovered over country
    def update(self):
        self.mouseHover = 0
        if Vector2(currentMousePos).distance_to((self.x, self.y)) < 20*mp.mlt:
            self.mouseHover = 1

    # Changes team of country when captured by an opposing team
    def changeTeam(self, team):
        if self in plrTerritories:
            plrTerritories.remove(self)

        if team == plrTeam:
            plrTerritories.append(self)
        self.team = team
        self.colour = teamColours[team]

    # Universal object shift procedure
    def shift(self, x, y, fsMove):
        self.x += x + fsMove[0]
        self.y += y + fsMove[1]

    # Displays objects and images on screen
    def draw(self):
        ### TEST: Every country correctly recognised by all classes?
        ### PASS: Circle displayed on centre of every country
        # pygame.draw.circle(win, teamColours['red'], (self.x, self.y), 4)

        ### TEST: Every country correctly connected to all neighbours?
        ### PASS: Red line connecting only and all territories that should be connected
        # for t in territories:
        #     if t.name in self.connections:
        #         pygame.draw.line(win, teamColours['red'], (self.x, self.y), (t.x, t.y))

        ## Font size changes depending on various phase states of players in the game
        size = 0 if mp.mlt < 1.4 else 1 if mp.mlt < 2.0 else 2
        size += 1 if mp.scale > 0.5 else 0
        if self.mouseHover and self.team == plrTeam:
            size += 1
        elif self.team == currentTurn:
            if players[currentTurn].phase == 'attacking' or players[currentTurn].phase == 'chooseForAttack':
                if players[currentTurn].selT.name == self.name:
                    size += 1
        elif players[currentTurn].phase == 'chooseForAttack' and self.mouseHover:
            if self.name in players[currentTurn].selT.connections:
                size += 1
        elif players[currentTurn].phase == 'attacking':
            if players[currentTurn].atkT.name == self.name:
                size += 1
                pygame.draw.circle(win, teamColours[players[currentTurn].team], (self.x, self.y),
                                   30*(mp.mlt+mp.scale), 2)

        # Display country name and population
        nameText = Country.nameFonts[size].render(self.name, True, self.colour, (220,220,220))
        popText = Country.nameFonts[size+2].render(str(self.pop), True, self.colour)

        win.blit(nameText, (self.x - nameText.get_width()/2, self.y - nameText.get_height()/2 - 9 - 3*size))
        win.blit(popText, (self.x - popText.get_width()/2, self.y - popText.get_height()/2 + 9 + 3*size))


class Player():
    def __init__(self, team):
        self.team = team
        self.phase = 'draft'

        self.deployAmt = 0
        self.deploySel = 0
        self.selT = None
        self.atkT = None
        self.atkTPrevTeam = ''

        self.testPressed = False

    ## Run every frame IF it is the players turn currently
    def update(self):
        # Find number of deployable troops
        if self.phase == 'draft':
            self.deployAmt = getTroops(self.team)
            self.deploySel = self.deployAmt
            self.phase = 'chooseForDraft'

        # Choose country on which to draft, if no troops left move to attack phase
        if self.phase == 'chooseForDraft':
            if self.deployAmt <= 0:
                self.phase = 'attack'

            elif mouseClicked:
                for t in plrTerritories:
                    if t.mouseHover:
                        self.selT = t
                        self.phase = 'drafting'
                        break

        # Choose how many troops to draft on chosen country
        if self.phase == 'drafting':
            if mouseClicked:
                if not self.selT.mouseHover:
                    self.selT = None
                    self.phase = 'chooseForDraft'

            if keyInp[K_RETURN]:
                if not self.testPressed:
                    self.testPressed = True
                    self.selT.pop += self.deploySel
                    self.deployAmt -= self.deploySel
                    self.deploySel = self.deployAmt
                    self.phase = 'chooseForDraft'

            elif keyInp[K_UP]:
                if not self.testPressed:
                    self.testPressed = True
                    self.deploySel += 1
                    if self.deploySel > self.deployAmt:
                        self.deploySel = self.deployAmt

            elif keyInp[K_DOWN]:
                if not self.testPressed:
                    self.testPressed = True
                    self.deploySel -= 1
                    if self.deploySel < 1:
                        self.deploySel = 1

            elif keyInp[K_RIGHT]:
                if not self.testPressed:
                    self.testPressed = True
                    self.deploySel = self.deployAmt

            elif keyInp[K_LEFT]:
                if not self.testPressed:
                    self.testPressed = True
                    self.deploySel = 1
            else:
                self.testPressed = False

        # Choose own country that will launch the attack, OR move on to fortify phase
        if self.phase == 'attack':
            if mouseClicked:
                for t in plrTerritories:
                    if t.mouseHover:
                        if t.pop > 1:
                            self.selT = t
                            self.deployAmt, self.deploySel = t.pop, 3 if t.pop > 2 else 1
                            self.phase = 'chooseForAttack'
                        break
            elif keyInp[K_SPACE]:
                if not self.testPressed:
                    self.testPressed = True
                    self.phase = 'fortify'
            else:
                self.testPressed = False

        # Choose a valid target to attack with selected country
        if self.phase == 'chooseForAttack':
            if dice[self.team].rolling:
                if keyInp[K_RETURN]:
                    if not self.testPressed:
                        self.testPressed = True
                        for d in dice.values():
                            d.rolling = False
                else:
                    self.testPressed = False
                    return

            if mouseClicked:
                clickedTerritory = False
                for t in territories:
                    if t.mouseHover:
                        clickedTerritory = True
                        if t in plrTerritories: # Switch attacking territory
                            if t.pop > 1:
                                self.selT = t
                                self.deployAmt, self.deploySel = t.pop, 3 if t.pop > 2 else 1
                        elif t.name in self.selT.connections: # Valid target found if a neighbour
                            self.atkT = t
                            self.phase = 'attacking'
                        break
                if not clickedTerritory: # Cancel if no territories clicked (go back to choosing)
                    self.selT = None
                    self.atkT = None
                    self.phase = 'attack'

        # Dice roll calculations to decide victor between attacker and defender
        elif self.phase == 'attacking':
            if dice[self.team].rolling:
                if keyInp[K_RETURN]: # Skip dice roll animation
                    if not self.testPressed:
                        self.testPressed = True
                        for d in dice.values():
                            d.rolling = False
                else:
                    self.testPressed = False
                    return

            if mouseClicked: # Cancel attack
                self.phase = 'chooseForAttack'

            if self.selT.pop < 2: # Insufficient attacking forces, cancel attack
                self.selT = None
                self.atkT = None
                self.phase = 'attack'

            if keyInp[K_RETURN]:
                if not self.testPressed:
                    self.testPressed = True
                    # Roll dice
                    atkCommit = self.deploySel
                    defCommit = 2 if self.atkT.pop > 1 else 1
                    atkRoll = dice[self.team].roll(self.deploySel, True)
                    defRoll = dice[self.atkT.team].roll(defCommit, False)

                    # Compare faces of dice
                    for i in range(min([atkCommit, defCommit])):
                        if atkRoll[0] > defRoll[0]: # Attacker wins
                            self.atkT.pop -= 1
                        else: # Defender wins
                            self.selT.pop -= 1
                            self.deployAmt, self.deploySel = self.selT.pop, 3 if self.selT.pop > 2 else 1
                    if self.atkT.pop < 1: # Victory, claim country and move in troops
                        self.atkTPrevTeam = self.atkT.team
                        self.atkT.changeTeam(self.team)
                        self.atkT.pop += self.selT.pop - 1
                        self.selT.pop -= self.selT.pop - 1
                        cam.shake(15)
                        # Start attacking from captured territory
                        if self.atkT.pop > 1:
                            self.selT = self.atkT
                            self.deployAmt, self.deploySel = self.selT.pop, 3 if self.selT.pop > 2 else 1
                            self.phase = 'chooseForAttack'

            ## Up and down changes number of dice to attack with
            elif keyInp[K_UP]:
                if not self.testPressed:
                    self.testPressed = True
                    if self.deploySel < 3 and self.deployAmt > self.deploySel+1:
                        self.deploySel += 1

            elif keyInp[K_DOWN]:
                if not self.testPressed:
                    self.testPressed = True
                    if self.deploySel > 1:
                        self.deploySel -= 1
            else:
                self.testPressed = False

        ## Unfinished and unused phase: this would include a tree traversal across neighbouring
        ##                              countries to validate moving troops around own territories
        ##                              for defence
        if self.phase == 'fortify':
            # if mouseClicked: ## NOT FINISHED
            #     for t in plrTerritories:
            #         if t.mouseHover:
            #             self.selT = t
            #             self.phase = 'chooseForFortify'
            #             break
            self.phase = 'draft'
            # Change current turn to next player in turn order
            global currentTurn
            if self.team == turnOrder[len(turnOrder) - 1]:
                currentTurn = turnOrder[0]
            else:
                for i in range(len(turnOrder)):
                    if turnOrder[i] == self.team:
                        currentTurn = turnOrder[i+1]
                        break

        # if self.phase == 'chooseForFortify': ## NOT FINISHED
        #     if mouseClicked:
        #         for t in plrTerritories:
        #             if t.mouseHover and t != self.selT:
        #                 paths = [1]
        #                 while paths:
        #                     for c in t.connections:
        #                         for terObj in territories:
        #                             if terObj.name == c:
        #                                 break
        #                         if terObj in plrTerritories:



    # Displays objects and images on screen
    # Depending on phase, a message is displayed with instructions for the player
    def draw(self):
        if self.phase == 'chooseForDraft':
            displayText = 'Deploy Remaining: '+str(self.deployAmt)+' [Click] to select'
            deployText = Country.nameFonts[4].render(displayText, True, (220,220,220), teamColours[self.team])
            win.blit(deployText, ((winWidth-deployText.get_width())/2, winHeight-deployText.get_height()))

        elif self.phase == 'drafting':
            displayText = 'Deploy '+str(self.deploySel)+'/'+str(self.deployAmt)+' to '+self.selT.name+\
                          '? [Enter | Arrow keys]'
            deployText = Country.nameFonts[4].render(displayText, True, (220,220,220), teamColours[self.team])
            win.blit(deployText, ((winWidth-deployText.get_width())/2, winHeight-deployText.get_height()))

        elif self.phase == 'attack':
            displayText = '[Click]: Attack from | [Space]: End attack phase'
            deployText = Country.nameFonts[4].render(displayText, True, (220,220,220), teamColours[self.team])
            win.blit(deployText, ((winWidth-deployText.get_width())/2, winHeight-deployText.get_height()))

        elif self.phase == 'chooseForAttack':
            displayText = '[Click] on territory to attack'
            deployText = Country.nameFonts[4].render(displayText, True, (220,220,220), teamColours[self.team])
            win.blit(deployText, ((winWidth-deployText.get_width())/2, winHeight-deployText.get_height()))

        elif self.phase == 'attacking':
            maxDiceAmt = 3 if self.deployAmt > 2 else self.deployAmt
            displayText = '[Enter]: Attack with '+str(self.deploySel)+'/'+str(maxDiceAmt)+' vs '\
                          +str(self.atkT.name)+' '+str(2 if self.atkT.pop > 1 else 1)
            deployText = Country.nameFonts[4].render(displayText, True, (220,220,220), teamColours[self.team])
            win.blit(deployText, ((winWidth-deployText.get_width())/2, winHeight-deployText.get_height()))

        elif self.phase == 'fortify':
            displayText = '[Click] on territory from which to move troops'
            deployText = Country.nameFonts[4].render(displayText, True, (220,220,220), teamColours[self.team])
            win.blit(deployText, ((winWidth-deployText.get_width())/2, winHeight-deployText.get_height()))


class CpuPlayer():
    def __init__(self, team):
        self.team = team
        self.phase = 'draft'

        self.deployAmt = 0
        self.deploySel = 0
        self.selT = None
        self.atkT = None
        self.atkTPrevTeam = ''
        self.ownTs = []

        self.testPressed = False

    # Run every frame IF current computer player's turn
    def update(self):
        # Find available draft amount
        if self.phase == 'draft':
            self.deployAmt = getTroops(self.team)
            self.deploySel = self.deployAmt
            self.phase = 'chooseForDraft'

        # Choose a country to draft troops on
        if self.phase == 'chooseForDraft':
            # Find owned territories
            self.ownTs = []
            for t in territories:
                if t.team == self.team:
                    self.ownTs.append(t)

            if self.ownTs:
                self.selT = random.choice(self.ownTs)
                self.phase = 'drafting'
            else:
                self.phase = 'fortify'

        # Increase population on chosen country
        if self.phase == 'drafting':
            self.selT.pop += self.deploySel
            self.deployAmt -= self.deploySel
            self.deploySel = self.deployAmt
            self.phase = 'attack'

        # Find a valid country to attack from that has a valid neighbour to attack
        if self.phase == 'attack':
            if dice[self.team].rolling:
                if keyInp[K_RETURN]:
                    if not self.testPressed:
                        self.testPressed = True
                        for d in dice.values():
                            d.rolling = False
                else:
                    self.testPressed = False
                return

            # Find owned territories
            self.ownTs = []
            for t in territories:
                if t.team == self.team:
                    self.ownTs.append(t)
            self.ownTs.sort(key=lambda x:x.pop, reverse=True)

            for o in self.ownTs:
                if o.pop > 1:
                    # Search neighbours for target
                    for t in territories:
                        if (not (t in self.ownTs)) and t.name in o.connections:
                            # Set target if comp.plr thinks it can win (higher troop count)
                            if t.pop < o.pop:
                                self.selT = o
                                self.atkT = t
                                self.deployAmt, self.deploySel = o.pop, 3 if o.pop > 2 else 1
                                self.phase = 'attacking'
                                return
            # No valid targets to attack
            self.phase = 'fortify'
            # print(self.team, 'done attacking')

        # Dice roll calculations to decide victor between attacker and defender
        elif self.phase == 'attacking':
            if dice[self.team].rolling:
                if keyInp[K_RETURN]:
                    if not self.testPressed:
                        self.testPressed = True
                        for d in dice.values():
                            d.rolling = False
                else:
                    self.testPressed = False
                return

            # Lost battle
            if self.selT.pop < 2:
                self.selT = None
                self.atkT = None
                self.phase = 'attack'

            else:
                # Roll dice
                atkCommit = self.deploySel
                defCommit = 2 if self.atkT.pop > 1 else 1
                atkRoll = dice[self.team].roll(self.deploySel, True)
                defRoll = dice[self.atkT.team].roll(defCommit, False)

                # Compare dice faces
                for i in range(min([atkCommit, defCommit])):
                    if atkRoll[0] > defRoll[0]: # Attacker wins
                        self.atkT.pop -= 1
                    else: # Defender wins
                        self.selT.pop -= 1
                        self.deployAmt, self.deploySel = self.selT.pop, 3 if self.selT.pop > 2 else 1
                if self.atkT.pop < 1: # Victory, move troops into newly captured territory
                    self.atkTPrevTeam = self.atkT.team
                    if self.atkTPrevTeam == plrTeam:
                        cam.shake(15) # Player lost a territory to AI
                    self.atkT.changeTeam(self.team)
                    self.atkT.pop += self.selT.pop - 1
                    self.selT.pop -= self.selT.pop - 1
                    self.phase = 'attack'

        if self.phase == 'fortify':
            # if mouseClicked: ## NOT FINISHED
            #     for t in plrTerritories:
            #         if t.mouseHover:
            #             self.selT = t
            #             self.phase = 'chooseForFortify'
            #             break
            self.phase = 'draft'
            global currentTurn
            # Find and set next player in turn order
            if self.team == turnOrder[len(turnOrder) - 1]:
                currentTurn = turnOrder[0]
            else:
                for i in range(len(turnOrder)):
                    if turnOrder[i] == self.team:
                        currentTurn = turnOrder[i+1]
                        break


class Dice():
    def __init__(self, team):
        self.team = team
        self.images = []
        for i in range(6):
            self.images.append(pygame.image.load('Assets/dice/'+team+' dice/'+str(i+1)+'.png'))

        self.res = [1,1]
        self.rollTimer = 0
        self.rolls = 0
        self.attacking = True
        self.rolling = False

    # Sets a timer for roll animation and picks numbers 1 to 6 number of times specified in 'rolls' param
    # RETURNS: List() of INTEGERs (Results of dice rolls)
    def roll(self, rolls, attacking):
        self.rolling = True
        self.rolls = rolls
        self.attacking = attacking
        self.rollTimer = targetFps * 3

        self.res = [random.randint(1,6) for i in range(self.rolls)]
        self.res = sorted(self.res, reverse=True)

        return self.res

    # Displays objects and images on screen
    def draw(self):
        if self.rolling:
            self.rollTimer -= 1
            if self.rollTimer < 1:
                self.rolling = False
                return

            # Find bottom middle of screen to display dice
            y = (winHeight - self.images[0].get_height())/2 + winHeight/3
            y += -self.images[0].get_height()/2-10 if self.attacking else self.images[0].get_height()/2+10
            for i in range(self.rolls):
                x = (winWidth - self.images[0].get_width())/2 + (i-1)*self.images[0].get_width() + (i-1)*10
                win.blit(self.images[self.res[i]-1], (x,y))

### Load procedures
# Sets intial settings for the game
def levelLoader():
    global currentTurn, players, plr, dice, turnOrder

    pygame.event.pump()

    # Set up territories: Open list of territories and assign to Country() objects
    for ln in Country.connectionList.splitlines():
        commas = []
        for char in ln:
            if commas:
                commas.append(ln.find(',',commas[len(commas)-1]+1))
                if len(commas) > 2:
                    break
            else:
                commas.append(ln.find(','))
        name = ln[:commas[0]]
        x = int(ln[commas[0]+2:commas[1]])
        y = int(ln[commas[1]+2:commas[2]])
        connections = eval(ln[commas[2]+2:])

        nCountry = Country(x,y,name,random.choice(list(teamColours)),random.randint(1,6),connections)

    # Set up dice
    dice = {team:Dice(team) for team in teamColours}

    ### TEST: Are all objects assigned to a continent?
    ### PASS: Prints empty list
    ### FAIL: Prints out countries that have no continent registered
    # testT = []
    # for t in territories:
    #     found = False
    #     for cont in continents:
    #         for c in continents[cont]:
    #             if t.name == c:
    #                 found = True
    #     if not found:
    #         testT.append(t.name)
    # print(testT) # Should print empty list for PASS TEST

    # Set up turn order
    turnOrder = []

    # Add human and computer players
    teams = [t for t in teamColours]
    for i in range(len(teams)):
        team = random.choice(teams)
        turnOrder.append(team)
        teams.remove(team)
        # Add players
        if team == plrTeam:
            newPlr = Player(team)
            plr = newPlr
        else:
            newPlr = CpuPlayer(team)
        players[team] = newPlr

    currentTurn = turnOrder[0]

# Runs main function of player with currently active turn
def turnCycle():
    players[currentTurn].update()

# Finds number of troops a player can get when drafting
# RETURN: INTEGER (number of troops)
def getTroops(team):
    amt = 0

    # Add up owned territories
    owned = 0
    continentCount = {c:0 for c in continents}
    for t in territories:
        if t.team == team:
            owned += 1
            continentCount[t.continent] += 1
            # Get continent bonus in all territories in a continent owned
            if continentCount[t.continent] == len(continents[t.continent]):
                amt += continentBonus[t.continent]

    owned = owned if owned > 9 else 9 # Minimum 3 deployable troops
    amt += int(owned/3)
    return amt

# Order of displaying objects (calls obj.draw() functions)
def redrawWindow():
    win.fill((0,0,0))

    mp.draw()

    for t in territories:
        t.draw()

    plr.draw()

    for d in dice.values():
        d.draw()

    # FPS counter top right
    win.blit(fpsImage, (winWidth - fpsImage.get_width() - 5, fpsImage.get_height() - 10))

    pygame.display.flip()


# Main
clock = pygame.time.Clock()
fps = 0
targetFps = 60
fsToggle = False
cam = Camera()

currentTurn = plrTeam
plr = None

# Load level
levelLoader()

currentMousePos = (0,0)
mouseClicked = 0
keyInp = []

mp = Map()

run = True
while run:
    clock.tick(targetFps) # FPS

    # Global inputs
    currentMousePos = pygame.mouse.get_pos()
    keyInp = pygame.key.get_pressed()

    # Toggle fullscreen
    if keyInp[pygame.K_F11]:
        if not fsToggle:
            pygame.display.quit()
            pygame.display.init()

            displayInfo = pygame.display.Info()
            displays = pygame.display.list_modes()

            newRes = (displayInfo.current_w, displayInfo.current_h)

            # Shifts objects to fullscreen center
            fsObjShift = (int((newRes[0] - winWidth) / 2),
                          int((newRes[1] - winHeight) / 2))

            winWidth = newRes[0]
            winHeight = newRes[1]

            # Reset window
            win = pygame.display.set_mode(newRes, pygame.FULLSCREEN)
            pygame.display.set_caption(winCaption)

            for obj in objects:
                obj.shift(0, 0, fsObjShift)

            mp.resize(1, newRes[1] / mp.ogImage.get_height())

            fsToggle = True
        else:
            pygame.display.quit()
            pygame.display.init()

            # Shifts objects to window center
            fsObjShift = (int((winWidth - winRes[0]) / -2),
                          int((winHeight - winRes[1]) / -2))

            winWidth = winRes[0]
            winHeight = winRes[1]

            # Reset window
            win = pygame.display.set_mode((winWidth, winHeight))
            pygame.display.set_caption(winCaption)

            for obj in objects:
                obj.shift(0, 0, fsObjShift)

            mp.resize(1, winRes[1] / mp.ogImage.get_height())

            fsToggle = False

    cam.move()

    for t in territories:
        t.update()

    turnCycle()

    # Mouse inputs, QUIT
    mouseClicked = 0
    events = pygame.event.get()
    for event in events:

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left click
                mouseClicked = 1

        if event.type == pygame.QUIT: # Window closed, end game
            run = False
            break

    # Register fps
    fps = int(clock.get_fps())
    fpsText = str(fps) + 'fps'
    fpsImage = font30.render(fpsText, True, (255, 255, 255))

    redrawWindow()

pygame.quit()
quit()