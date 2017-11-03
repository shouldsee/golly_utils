# isotropicRulegen.py
# Auxillary rule generator for isotropic, non-totalistic version of apgsearch
# The rulespace is the set of isotropic non-totalistic rules on the Moore
# neighbourhood, using Alan Hensel's notation.
# See http://www.ibiblio.org/lifepatterns/neighbors2.html

# Based on rule generator in apgsearch, by Adam P. Goucher
# Non-totalistic adaptation by Arie Paap, Oct. 2014
# Modifications:
# * add notationdict
# * adapt RuleGenerator variables for non-totalistic neighbourhood
# * add isotropicline() to save rule table lines for non-totalistic neighbourhoods
# * adapt saveCoalesceObjects() for non-totalistic rules
# * adapt saveClassifyObjects() for non-totalistic rules
# * adapt saveContagiousLife() for non-totalistic rules
# 

import golly as g
import os

# Generates the helper rules for apgsearch-isotropic, given a base isotropic 
# rule in Hensel's notation.
class RuleGenerator:

    # notationdict adapted from Eric Goldstein's HenselNotation->Ruletable(1.3).py
    # Modified for neighbourhood2 version of Hensel's notation
    notationdict = {
        "0"  : [0,0,0,0,0,0,0,0],   #    
        "1e" : [1,0,0,0,0,0,0,0],   #   N
        "1c" : [0,1,0,0,0,0,0,0],   #   NE
        "2a" : [1,1,0,0,0,0,0,0],   #   N,  NE
        "2e" : [1,0,1,0,0,0,0,0],   #   N,  E
        "2k" : [1,0,0,1,0,0,0,0],   #   N,  SE
        "2i" : [1,0,0,0,1,0,0,0],   #   N,  S
        "2c" : [0,1,0,1,0,0,0,0],   #   NE, SE
        "2n" : [0,1,0,0,0,1,0,0],   #   NE, SW
        "3a" : [1,1,1,0,0,0,0,0],   #   N,  NE, E
        "3n" : [1,1,0,1,0,0,0,0],   #   N,  NE, SE
        "3r" : [1,1,0,0,1,0,0,0],   #   N,  NE, S
        "3q" : [1,1,0,0,0,1,0,0],   #   N,  NE, SW
        "3j" : [1,1,0,0,0,0,1,0],   #   N,  NE, W
        "3i" : [1,1,0,0,0,0,0,1],   #   N,  NE, NW
        "3e" : [1,0,1,0,1,0,0,0],   #   N,  E,  S
        "3k" : [1,0,1,0,0,1,0,0],   #   N,  E,  SW
        "3y" : [1,0,0,1,0,1,0,0],   #   N,  SE, SW
        "3c" : [0,1,0,1,0,1,0,0],   #   NE, SE, SW
        "4a" : [1,1,1,1,0,0,0,0],   #   N,  NE, E,  SE
        "4r" : [1,1,1,0,1,0,0,0],   #   N,  NE, E,  S
        "4q" : [1,1,1,0,0,1,0,0],   #   N,  NE, E,  SW
        "4i" : [1,1,0,1,1,0,0,0],   #   N,  NE, SE, S
        "4y" : [1,1,0,1,0,1,0,0],   #   N,  NE, SE, SW
        "4k" : [1,1,0,1,0,0,1,0],   #   N,  NE, SE, W
        "4n" : [1,1,0,1,0,0,0,1],   #   N,  NE, SE, NW
        "4z" : [1,1,0,0,1,1,0,0],   #   N,  NE, S,  SW
        "4j" : [1,1,0,0,1,0,1,0],   #   N,  NE, S,  W
        "4t" : [1,1,0,0,1,0,0,1],   #   N,  NE, S,  NW
        "4w" : [1,1,0,0,0,1,1,0],   #   N,  NE, SW, W
        "4e" : [1,0,1,0,1,0,1,0],   #   N,  E,  S,  W
        "4c" : [0,1,0,1,0,1,0,1],   #   NE, SE, SW, NW
        "5i" : [1,1,1,1,1,0,0,0],   #   N,  NE, E,  SE, S
        "5j" : [1,1,1,1,0,1,0,0],   #   N,  NE, E,  SE, SW
        "5n" : [1,1,1,1,0,0,1,0],   #   N,  NE, E,  SE, W
        "5a" : [1,1,1,1,0,0,0,1],   #   N,  NE, E,  SE, NW
        "5q" : [1,1,1,0,1,1,0,0],   #   N,  NE, E,  S,  SW
        "5c" : [1,1,1,0,1,0,1,0],   #   N,  NE, E,  S,  W
        "5r" : [1,1,0,1,1,1,0,0],   #   N,  NE, SE, S,  SW
        "5y" : [1,1,0,1,1,0,1,0],   #   N,  NE, SE, S,  W
        "5k" : [1,1,0,1,0,1,1,0],   #   N,  NE, SE, SW, W
        "5e" : [1,1,0,1,0,1,0,1],   #   N,  NE, SE, SW, NW
        "6a" : [1,1,1,1,1,1,0,0],   #   N,  NE, E,  SE, S,  SW
        "6c" : [1,1,1,1,1,0,1,0],   #   N,  NE, E,  SE, S,  W
        "6k" : [1,1,1,1,0,1,1,0],   #   N,  NE, E,  SE, SW, W
        "6e" : [1,1,1,1,0,1,0,1],   #   N,  NE, E,  SE, SW, NW
        "6n" : [1,1,1,0,1,1,1,0],   #   N,  NE, E,  S,  SW, W
        "6i" : [1,1,0,1,1,1,0,1],   #   N,  NE, SE, S,  SW, NW
        "7c" : [1,1,1,1,1,1,1,0],   #   N,  NE, E,  SE, S,  SW, W
        "7e" : [1,1,1,1,1,1,0,1],   #   N,  NE, E,  SE, S,  SW, NW
        "8"  : [1,1,1,1,1,1,1,1],   #   N,  NE, E,  SE, S,  SW, W,  NW
        }
    
    allneighbours = [  
        ["0"],
        ["1e", "1c"],
        ["2a", "2e", "2k", "2i", "2c", "2n"],
        ["3a", "3n", "3r", "3q", "3j", "3i", "3e", "3k", "3y", "3c"],
        ["4a", "4r", "4q", "4i", "4y", "4k", "4n", "4z", "4j", "4t", "4w", "4e", "4c"],
        ["5i", "5j", "5n", "5a", "5q", "5c", "5r", "5y", "5k", "5e"],
        ["6a", "6c", "6k", "6e", "6n", "6i"],
        ["7c", "7e"],
        ["8"],
        ]
        
    allneighbours_flat = [n for x in allneighbours for n in x]
    
    numneighbours = len(notationdict)
    
    # Use dict to store rule elements, initialised by setrule():
    bee = {}
    ess = {}
    alphanumeric = ""
    rulename = ""
    
    # Save all helper rules:
    def saveAllRules(self):
    
        self.saveIsotropicRule()
        self.saveClassifyObjects()
        self.saveCoalesceObjects()
        self.saveExpungeObjects()
        self.saveExpungeGliders()
        self.saveIdentifyGliders()
        self.savePercolateInfection()
        self.saveEradicateInfection()
        self.saveContagiousLife()
    
    # Interpret birth or survival string
    def ruleparts(self, part):

        inverse = False
        nlist = []
        totalistic = True
        rule = { k: False for k, v in self.notationdict.iteritems() }
        
        # Reverse the rule string to simplify processing
        part = part[::-1]
        
        for c in part:
            if c.isdigit():
                d = int(c)
                if totalistic:
                    # Add all the neighbourhoods for this value
                    for neighbour in self.allneighbours[d]:
                        rule[neighbour] = True
                elif inverse:
                    # Add all the neighbourhoods not in nlist for this value
                    for neighbour in self.allneighbours[d]:
                        if neighbour[1] not in nlist:
                            rule[neighbour] = True
                else:
                    # Add all the neighbourhoods in nlist for this value
                    for n in nlist:
                        neighbour = c + n
                        if neighbour in rule:
                            rule[neighbour] = True
                        else:
                            # Error
                            return {}
                    
                inverse = False
                nlist = []
                totalistic = True

            elif (c == '-'):
                inverse = True

            else:
                totalistic = False
                nlist.append(c)
        
        return rule

    # Set isotropic, non-totalistic rule
    # Adapted from Eric Goldstein's HenselNotation->Ruletable(1.3).py
    def setrule(self, rulestring):
    
        # neighbours_flat = [n for x in neighbours for n in x]
        b = {}
        s = {}
        sep = ''
        birth = ''
        survive = ''
        
        rulestring = rulestring.lower()
        
        if '/' in rulestring:
            sep = '/'
        elif '_' in rulestring:
            sep = '_'
        elif (rulestring[0] == 'b'):
            sep = 's'
        else:
            sep = 'b'
        
        survive, birth = rulestring.split(sep)
        if (survive[0] == 'b'):
            survive, birth = birth, survive
        survive = survive.replace('s', '')
        birth = birth.replace('b', '')
        
        b = self.ruleparts(birth)
        s = self.ruleparts(survive)

        if b and s:
            self.alphanumeric = 'B' + birth + 'S' + survive
            self.rulename = 'B' + birth + '_S' + survive
            self.bee = b
            self.ess = s
        else:
            # Error
            g.note("Unable to process rule definition.\n" +
                    "b = " + str(b) + "\ns = " + str(s))
            g.exit()
            

    # Save a rule file:
    def saverule(self, name, comments, table, colours):
        
        ruledir = g.getdir("rules")
        filename = ruledir + name + ".rule"

        results = "@RULE " + name + "\n\n"
        results += "*** File autogenerated by saverule. ***\n\n"
        results += comments
        results += "\n\n@TABLE\n\n"
        results += table
        results += "\n\n@COLORS\n\n"
        results += colours

        # Only create a rule file if it doesn't already exist; this avoids
        # concurrency issues when booting an instance of apgsearch whilst
        # one is already running.
        if not os.path.exists(filename):
            try:
                f = open(filename, 'w')
                f.write(results)
                f.close()
            except:
                g.warn("Unable to create rule table:\n" + filename)

    # Defines a variable:
    def newvar(self, name, vallist):

        line = "var "+name+"={"
        for i in xrange(len(vallist)):
            if (i > 0):
                line += ','
            line += str(vallist[i])
        line += "}\n"

        return line

    # Defines a block of equivalent variables:
    def newvars(self, namelist, vallist):

        block = "\n"

        for name in namelist:
            block += self.newvar(name, vallist)

        return block

    def scoline(self, chara, charb, left, right, amount):

        line = str(left) + ","

        for i in xrange(8):
            if (i < amount):
                line += chara
            else:
                line += charb
            line += chr(97 + i)
            line += ","

        line += str(right) + "\n"

        return line

    def isotropicline(self, chara, charb, left, right, n):

        line = str(left) + ","
        neighbours = self.notationdict[n]
        
        for i in xrange(8):
            if neighbours[i]:
                line += chara
            else:
                line += charb
            line += chr(97 + i)
            line += ","

        line += str(right) + "\n"

        return line
        
    def saveIsotropicRule(self):
    
        comments = """
This is a two state, isotropic, non-totalistic rule on the Moore neighbourhood.
The notation used to define the rule was originally proposed by Alan Hensel.
See http://www.ibiblio.org/lifepatterns/neighbors2.html for details
"""

        table = """
n_states:2
neighborhood:Moore
symmetries:rotate4reflect
"""

        table += self.newvars(["a","b","c","d","e","f","g","h"], [0, 1])

        table += "\n# Birth\n"
        for n in self.allneighbours_flat:
            if self.bee[n]:
                table += "0,"
                table += str(self.notationdict[n])[1:-1].replace(' ','')
                table += ",1\n"
        
        table += "\n# Survival\n"
        for n in self.allneighbours_flat:
            if self.ess[n]:
                table += "1,"
                table += str(self.notationdict[n])[1:-1].replace(' ','')
                table += ",1\n"

        table += "\n# Death\n"
        table += self.scoline("","",1,0,0)
        
        colours = ""
        self.saverule(self.rulename, comments, table, colours)
    
    def saveHandlePlumes(self):

        comments = """
This post-processes the output of ClassifyObjects to remove any
unwanted clustering of low-period objects appearing in puffer
exhaust.

state 0:  vacuum

state 7:  ON, still-life
state 8:  OFF, still-life

state 9:  ON, p2 oscillator
state 10: OFF, p2 oscillator

state 11: ON, higher-period object
state 12: OFF, higher-period object
"""
        table = """
n_states:17
neighborhood:Moore
symmetries:permute

var da={0,2,4,6,8,10,12,14,16}
var db={0,2,4,6,8,10,12,14,16}
var dc={0,2,4,6,8,10,12,14,16}
var dd={0,2,4,6,8,10,12,14,16}
var de={0,2,4,6,8,10,12,14,16}
var df={0,2,4,6,8,10,12,14,16}
var dg={0,2,4,6,8,10,12,14,16}
var dh={0,2,4,6,8,10,12,14,16}

var a={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var b={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var c={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var d={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var e={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var f={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var g={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var h={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}


8,da,db,dc,dd,de,df,dg,dh,0
10,da,db,dc,dd,de,df,dg,dh,0

9,a,b,c,d,e,f,g,h,1
10,a,b,c,d,e,f,g,h,2
"""
        colours = """
1  255  255  255
2  127  127  127
7    0    0  255
8    0    0  127
9  255    0    0
10 127    0    0
11   0  255    0
12   0  127    0
"""
        self.saverule("APG_HandlePlumesCorrected", comments, table, colours)

    def saveExpungeGliders(self):

        comments = """
This removes unwanted gliders.
It is mandatory that one first runs the rules CoalesceObjects,
IdentifyGliders and ClassifyObjects.

Run this for two generations, and observe the population
counts after 1 and 2 generations. This will give the
following data:

number of gliders = (p(1) - p(2))/5
"""
        table = """
n_states:17
neighborhood:Moore
symmetries:rotate4reflect

var a={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var b={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var c={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var d={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var e={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var f={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var g={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var h={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}

13,a,b,c,d,e,f,g,h,14
14,a,b,c,d,e,f,g,h,0
"""
        colours = """
0    0    0    0
1  255  255  255
2  127  127  127
7    0    0  255
8    0    0  127
9  255    0    0
10 127    0    0
11   0  255    0
12   0  127    0
13 255  255    0
14 127  127    0
"""
        self.saverule("APG_ExpungeGliders", comments, table, colours)

    def saveIdentifyGliders(self):

        comments = """
Run this after CoalesceObjects to find any gliders.

state 0:  vacuum
state 1:  ON
state 2:  OFF
"""
        table = """
n_states:17
neighborhood:Moore
symmetries:rotate4reflect

var a={0,2}
var b={0,2}
var c={0,2}
var d={0,2}
var e={0,2}
var f={0,2}
var g={0,2}
var h={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var i={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var j={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var k={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var l={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var m={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var n={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var o={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var p={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
var q={3,4}
var r={9,10}
var s={11,12}

1,1,a,1,1,b,1,c,d,3
d,1,1,1,1,a,b,1,c,4

3,i,j,k,l,m,n,o,p,5
4,i,j,k,l,m,n,o,p,6

1,q,i,j,a,b,c,k,l,7
d,q,i,j,a,b,c,k,l,8
1,i,a,b,c,d,e,j,q,7
f,i,a,b,c,d,e,j,q,8

5,7,8,7,7,8,7,8,8,9
6,7,7,7,7,8,8,7,8,10
5,i,j,k,l,m,n,o,p,15
6,i,j,k,l,m,n,o,p,16
15,i,j,k,l,m,n,o,p,1
16,i,j,k,l,m,n,o,p,2

7,i,j,k,l,m,n,o,p,11
8,i,j,k,l,m,n,o,p,12

9,i,j,k,l,m,n,o,p,13
10,i,j,k,l,m,n,o,p,14
11,r,j,k,l,m,n,o,p,13
11,i,r,k,l,m,n,o,p,13
12,r,j,k,l,m,n,o,p,14
12,i,r,k,l,m,n,o,p,14

11,i,j,k,l,m,n,o,p,1
12,i,j,k,l,m,n,o,p,2
"""
        colours = """
0    0    0    0
1  255  255  255
2  127  127  127
7    0    0  255
8    0    0  127
9  255    0    0
10 127    0    0
11   0  255    0
12   0  127    0
13 255  255    0
14 127  127    0
"""
        self.saverule("APG_IdentifyGliders", comments, table, colours)

    def saveEradicateInfection(self):

        comments = """
To run after ContagiousLife to disinfect any cells in states 3 or 4.

state 0:  vacuum
state 1:  ON
state 2:  OFF
"""
        table = """
n_states:7
neighborhood:Moore
symmetries:permute

var a={0,1,2,3,4,5,6}
var b={0,1,2,3,4,5,6}
var c={0,1,2,3,4,5,6}
var d={0,1,2,3,4,5,6}
var e={0,1,2,3,4,5,6}
var f={0,1,2,3,4,5,6}
var g={0,1,2,3,4,5,6}
var h={0,1,2,3,4,5,6}
var i={0,1,2,3,4,5,6}

4,a,b,c,d,e,f,g,h,6
3,a,b,c,d,e,f,g,h,5
"""
        colours = """
0    0    0    0
1    0    0  255
2    0    0  127
3  255    0    0
4  127    0    0
5    0  255    0
6    0  127    0
"""
        self.saverule("APG_EradicateInfection", comments, table, colours)

    def savePercolateInfection(self):

        comments = """
Percolates any infection to all cells of that particular island.

state 0:  vacuum
state 1:  ON
state 2:  OFF
"""
        table = """
n_states:7
neighborhood:Moore
symmetries:permute

var a={0,1,2,3,4,5,6}
var b={0,1,2,3,4,5,6}
var c={0,1,2,3,4,5,6}
var d={0,1,2,3,4,5,6}
var e={0,1,2,3,4,5,6}
var f={0,1,2,3,4,5,6}
var g={0,1,2,3,4,5,6}
var h={0,1,2,3,4,5,6}
var i={0,1,2,3,4,5,6}

var q={3,4}
var da={2,4,6}
var la={1,3,5}

da,q,b,c,d,e,f,g,h,4
la,q,b,c,d,e,f,g,h,3
"""
        colours = """
0    0    0    0
1    0    0  255
2    0    0  127
3  255    0    0
4  127    0    0
5    0  255    0
6    0  127    0
"""
        self.saverule("APG_PercolateInfection", comments, table, colours)
        
    def saveExpungeObjects(self):

        comments = """
This removes unwanted monominos, blocks, blinkers and beehives.
It is mandatory that one first runs the rule ClassifyObjects.

Run this for four generations, and observe the population
counts after 0, 1, 2, 3 and 4 generations. This will give the
following data:

number of monominos = p(1) - p(0)
number of blocks = (p(2) - p(1))/4
number of blinkers = (p(3) - p(2))/5
number of beehives = (p(4) - p(3))/8
"""
        table = "n_states:17\n"
        table += "neighborhood:Moore\n"
        table += "symmetries:rotate4reflect\n\n"

        table += self.newvars(["a","b","c","d","e","f","g","h","i"], range(0, 17, 1))

        table += """
# Monomino
7,0,0,0,0,0,0,0,0,0

# Death
6,a,b,c,d,e,f,g,h,0
a,6,b,c,d,e,f,g,h,0

# Block
7,7,7,7,0,0,0,0,0,1
1,1,1,1,0,0,0,0,0,0
1,a,b,c,d,e,f,g,h,7

# Blinker
10,0,0,0,9,9,9,0,0,2
9,9,10,0,0,0,0,0,10,3
2,a,b,c,d,e,f,g,h,10
3,a,b,c,d,e,f,g,h,9
9,2,0,3,0,2,0,3,0,6

# Beehive
7,0,7,8,7,0,0,0,0,1
7,0,0,7,8,8,7,0,0,1
8,7,7,8,7,7,0,7,0,4
4,1,1,4,1,1,0,1,0,5
4,a,b,c,d,e,f,g,h,8
5,5,b,c,d,e,f,g,h,6
5,a,b,c,d,e,f,g,h,15
15,a,b,c,d,e,f,g,h,8
"""

        colours = """
0    0    0    0
1  255  255  255
2  127  127  127
7    0    0  255
8    0    0  127
9  255    0    0
10 127    0    0
11   0  255    0
12   0  127    0
13 255  255    0
14 127  127    0
"""
        self.saverule("APG_ExpungeObjects", comments, table, colours)

    def saveCoalesceObjects(self):

        comments = """
A variant of HistoricalLife which separates a field of ash into
distinct objects.

state 0:  vacuum
state 1:  ON
state 2:  OFF
"""
        table = "n_states:3\n"
        table += "neighborhood:Moore\n"
        table += "symmetries:rotate4reflect\n"

        table += self.newvars(["a","b","c","d","e","f","g","h","i"], [0, 1, 2])
        table += self.newvars(["da","db","dc","dd","de","df","dg","dh","di"], [0, 2])
        table += self.newvars(["la","lb","lc","ld","le","lf","lg","lh","li"], [1])

        table += "\n# Birth\n"
        for n in self.allneighbours_flat:
            if self.bee[n]:
                table += self.isotropicline("l","d","di",1,n)
        
        table += "\n# Survival\n"
        for n in self.allneighbours_flat:
            if self.ess[n]:
                table += self.isotropicline("l","d",1,1,n)

        table += "\n# Death\n"
        table += self.scoline("","",1,2,0)
        
        table += "\n# Bridge inductors\n"
        for n in self.allneighbours_flat:
            if self.bee[n]:
                table += self.isotropicline("l","","0",2,n)

        colours = """
0    0    0    0
1  255  255  255
2  127  127  127
"""
        self.saverule("APG_CoalesceObjects_"+self.alphanumeric, comments, table, colours)

    def saveClassifyObjects(self):

        comments = """
This passively classifies objects as either still-lifes, p2 oscillators
or higher-period oscillators. It is mandatory that one first runs the
rule CoalesceObjects.

state 0:  vacuum
state 1:  input ON
state 2:  input OFF

state 3:  ON, will die
state 4:  OFF, will remain off
state 5:  ON, will survive
state 6:  OFF, will become alive

state 7:  ON, still-life
state 8:  OFF, still-life

state 9:  ON, p2 oscillator
state 10: OFF, p2 oscillator

state 11: ON, higher-period object
state 12: OFF, higher-period object
"""
        table = "n_states:17\n"
        table += "neighborhood:Moore\n"
        table += "symmetries:rotate4reflect\n"

        table += self.newvars(["a","b","c","d","e","f","g","h","i"], range(0, 17, 1))
        table += self.newvars(["la","lb","lc","ld","le","lf","lg","lh","li"], range(1, 17, 2))
        table += self.newvars(["da","db","dc","dd","de","df","dg","dh","di"], range(0, 17, 2))
        table += self.newvars(["pa","pb","pc","pd","pe","pf","pg","ph","pi"], [0, 3, 4])
        table += self.newvars(["qa","qb","qc","qd","qe","qf","qg","qh","qi"], [5, 6])

        table += "\n"
        for n in self.allneighbours_flat:
            if self.bee[n]:
                table += self.isotropicline("l","d",0,6,n)
                table += self.isotropicline("l","d",2,6,n)
                table += self.isotropicline("q","p",3,9,n)
                table += self.isotropicline("q","p",4,12,n)

        table += "\n"
        for n in self.allneighbours_flat:
            if self.ess[n]:
                table += self.isotropicline("l","d",1,5,n)
                table += self.isotropicline("q","p",5,7,n)
                table += self.isotropicline("q","p",6,12,n)
        
        table += "\n"
        table += self.scoline("","",2,4,0)
        table += self.scoline("","",1,3,0)
        table += self.scoline("","",5,11,0)
        table += self.scoline("","",3,11,0)
        table += self.scoline("","",4,8,0)
        table += self.scoline("","",6,10,0)

        table += """
# Propagate interestingness
7,11,b,c,d,e,f,g,h,11
7,a,11,c,d,e,f,g,h,11
7,12,b,c,d,e,f,g,h,11
7,a,12,c,d,e,f,g,h,11
7,9,b,c,d,e,f,g,h,9
7,a,9,c,d,e,f,g,h,9
7,10,b,c,d,e,f,g,h,9
7,a,10,c,d,e,f,g,h,9
8,11,b,c,d,e,f,g,h,12
8,a,11,c,d,e,f,g,h,12
8,12,b,c,d,e,f,g,h,12
8,a,12,c,d,e,f,g,h,12
8,9,b,c,d,e,f,g,h,10
8,a,9,c,d,e,f,g,h,10
8,10,b,c,d,e,f,g,h,10
8,a,10,c,d,e,f,g,h,10

# Glider trails
7,13,b,c,d,e,f,g,h,11
7,a,13,c,d,e,f,g,h,11
7,14,b,c,d,e,f,g,h,11
7,a,14,c,d,e,f,g,h,11
8,13,b,c,d,e,f,g,h,14
8,a,13,c,d,e,f,g,h,14
8,14,b,c,d,e,f,g,h,14
8,a,14,c,d,e,f,g,h,14
9,13,b,c,d,e,f,g,h,11
9,a,13,c,d,e,f,g,h,11
9,14,b,c,d,e,f,g,h,11
9,a,14,c,d,e,f,g,h,11
10,13,b,c,d,e,f,g,h,14
10,a,13,c,d,e,f,g,h,14
10,14,b,c,d,e,f,g,h,14
10,a,14,c,d,e,f,g,h,14


9,11,b,c,d,e,f,g,h,11
9,a,11,c,d,e,f,g,h,11
9,12,b,c,d,e,f,g,h,11
9,a,12,c,d,e,f,g,h,11
10,11,b,c,d,e,f,g,h,12
10,a,11,c,d,e,f,g,h,12
10,12,b,c,d,e,f,g,h,12
10,a,12,c,d,e,f,g,h,12

# Gliders emitted by, or part of, other patterns
13,11,b,c,d,e,f,g,h,11
13,a,11,c,d,e,f,g,h,11
13,12,b,c,d,e,f,g,h,11
13,a,12,c,d,e,f,g,h,11
14,11,b,c,d,e,f,g,h,12
14,a,11,c,d,e,f,g,h,12
14,12,b,c,d,e,f,g,h,12
14,a,12,c,d,e,f,g,h,12
13,9,b,c,d,e,f,g,h,11
13,a,9,c,d,e,f,g,h,11
14,9,b,c,d,e,f,g,h,12
14,a,9,c,d,e,f,g,h,12
"""

        colours = """
0    0    0    0
1  255  255  255
2  127  127  127
7    0    0  255
8    0    0  127
9  255    0    0
10 127    0    0
11   0  255    0
12   0  127    0
13 255  255    0
14 127  127    0
"""
        self.saverule("APG_ClassifyObjects_"+self.alphanumeric, comments, table, colours)

    def saveContagiousLife(self):

        comments = """
A variant of HistoricalLife used for detecting dependencies between
islands.

state 0:  vacuum
state 1:  ON
state 2:  OFF
state 3:  Infected, ON
state 4:  Infected, OFF
state 5:  Treated, ON
state 6:  Treated, OFF
"""
        table = "n_states:7\n"
        table += "neighborhood:Moore\n"
        table += "symmetries:rotate4reflect\n"

        table += self.newvars(["a","b","c","d","e","f","g","h","i"], range(0, 7, 1))
        table += self.newvars(["la","lb","lc","ld","le","lf","lg","lh","li"], range(1, 7, 2))
        table += self.newvars(["da","db","dc","dd","de","df","dg","dh","di"], range(0, 7, 2))
        table += self.newvar("p",[3, 4])
        table += self.newvars(["ta","tb","tc","td","te","tf","tg","th","ti"], [3])
        table += self.newvars(["qa","qb","qc","qd","qe","qf","qg","qh","qi"], [0, 1, 2, 4, 5, 6])

        table += "\n"
        for n in self.allneighbours_flat:
            if self.bee[n]:
                table += self.isotropicline("l","d",4,3,n)
                table += self.isotropicline("l","d",2,1,n)
                table += self.isotropicline("l","d",0,1,n)
                table += self.isotropicline("l","d",6,5,n)
                table += self.isotropicline("t","q",0,4,n)
        
        table += "\n"
        for n in self.allneighbours_flat:
            if self.ess[n]:
                table += self.isotropicline("l","d",3,3,n)
                table += self.isotropicline("l","d",5,5,n)
                table += self.isotropicline("l","d",1,1,n)

        table += "\n# Default behaviour (death):\n"
        table += self.scoline("","",1,2,0)
        table += self.scoline("","",5,6,0)
        table += self.scoline("","",3,4,0)

        colours = """
0    0    0    0
1    0    0  255
2    0    0  127
3  255    0    0
4  127    0    0
5    0  255    0
6    0  127    0
"""
        self.saverule("APG_ContagiousLife_"+self.alphanumeric, comments, table, colours)
