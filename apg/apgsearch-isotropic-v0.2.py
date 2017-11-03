# apgsearch-isotropic v0.2
# Adaptation of Adam P. Goucher's apgsearch for isotropic, non-totalistic rules
#
# == Based on apgsearch v0.4 and v1.1 by Adam P. Goucher ==
# 
# Optimised soup searcher, v0.4 (beta release).
#
# -- Processes roughly 100 soups per (second . core . GHz).
#
# -- Can perfectly identify oscillators with period < 1000, well-separated
#    spaceships of low period, and certain infinite-growth patterns (such
#    guns and puffers, including both naturally-occurring types of switch
#    engine).
#
# -- Separates most pseudo-objects into their constituent parts, including
#    all pseudo-still-lifes of 18 or fewer live cells (which is the maximum
#    theoretically possible, given there is a 19-cell pseudo-still-life
#    with two distinct decompositions).
#
# -- Correctly separates non-interacting standard spaceships, irrespective
#    of their proximity. In particular, a LWSS-on-LWSS is registered as two
#    LWSSes, whereas an LWSS-on-HWSS is registered as a single spaceship
#    (since they interact by suppressing sparks).
#
# -- At least 99.9999999% reliable at identifying objects.
#
# -- Scores soups based on the total excitement of the ash objects.
#
# -- Preliminary support for other outer-totalistic rules.
#
# By Adam P. Goucher, with contributions by Andrew Trevorrow,
# Tom Rokicki, Nathaniel Johnston and Dave Greene.
#
# == Modifications by Arie Paap ==
# apgsearch-isotropic v0.2
# 
# * Update to some functions to apgsearch v1.1
#   * Support for symmetry options
#   * Record up to 10 sample soupids
# * Restore common objects in rules similar to Life to commonnames dict
# * Replace glidersexist test and restore use of IdentifyGliders and
#   ExpungeGliders in census()
# * Disable error correction
#
# apgsearch-isotropic v0.1
#
# * Remove RuleGenerator class and use isotropicRulegen instead
# * List of Life objects in commonnames dict removed
# * Removed Life-centric optimizations
#   * Removed countxwsses() and related code
#   * Don't use IdentifyGliders or ExpungeGliders in census()
#   * Replace ExpungeObjects with ExpungeSmallSL
# * enter_unid() evolves patterns for their period instead of 8 gen
# * fix bug in caching logic which doesn't cache small ships with period > 9
#   but does cache their bitstring

import isotropicRulegen
import golly as g
from glife import rect, pattern
import time
import math
import operator
import hashlib
import datetime
import os

# Takes approximately 350 microseconds to construct a 16-by-16 soup based
# on a SHA-256 cryptographic hash in the obvious way.
def hashsoup(instring, sym):

    s = hashlib.sha256(instring).digest()

    thesoup = []

    if sym in ['D2_x', 'D8_1', 'D8_4']:
        d = 1
    elif sym in ['D4_x1', 'D4_x4']:
        d = 2
    else:
        d = 0

    for j in xrange(32):

        t = ord(s[j])

        for k in xrange(8):

            if (sym == '8x32'):
                x = k + 8*(j % 4)
                y = int(j / 4)
            else:
                x = k + 8*(j % 2)
                y = int(j / 2)

            if (t & (1 << (7 - k))):

                if ((d == 0) | (x >= y)):

                    thesoup.append(x)
                    thesoup.append(y)

                elif (sym == 'D4_x1'):

                    thesoup.append(y)
                    thesoup.append(-x)

                elif (sym == 'D4_x4'):

                    thesoup.append(y)
                    thesoup.append(-x-1)

                if ((sym == 'D4_x1') & (x == y)):

                    thesoup.append(y)
                    thesoup.append(-x)

                if ((sym == 'D4_x4') & (x == y)):

                    thesoup.append(y)
                    thesoup.append(-x-1)

    # Checks for diagonal symmetries:
    if (d >= 1):
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(thesoup[x+1])
            thesoup.append(thesoup[x])
        if d == 2:
            if (sym == 'D4_x1'):
                for x in xrange(0, len(thesoup), 2):
                    thesoup.append(-thesoup[x+1])
                    thesoup.append(-thesoup[x])
            else:
                for x in xrange(0, len(thesoup), 2):
                    thesoup.append(-thesoup[x+1] - 1)
                    thesoup.append(-thesoup[x] - 1)
            return thesoup

    # Checks for orthogonal x symmetry:
    if sym in ['D2_+1', 'D4_+1', 'D4_+2']:
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(thesoup[x])
            thesoup.append(-thesoup[x+1])
    elif sym in ['D2_+2', 'D4_+4']:
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(thesoup[x])
            thesoup.append(-thesoup[x+1] - 1)

    # Checks for orthogonal y symmetry:
    if sym in ['D4_+1']:
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(-thesoup[x])
            thesoup.append(thesoup[x+1])
    elif sym in ['D4_+2', 'D4_+4']:
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(-thesoup[x] - 1)
            thesoup.append(thesoup[x+1])

    # Checks for rotate2 symmetry:
    if sym in ['C2_1', 'C4_1', 'D8_1']:
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(-thesoup[x])
            thesoup.append(-thesoup[x+1])
    elif sym in ['C2_2']:
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(-thesoup[x])
            thesoup.append(-thesoup[x+1]-1)
    elif sym in ['C2_4', 'C4_4', 'D8_4']:
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(-thesoup[x]-1)
            thesoup.append(-thesoup[x+1]-1)

    # Checks for rotate4 symmetry:
    if (sym in ['C4_1', 'D8_1']):
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(thesoup[x+1])
            thesoup.append(-thesoup[x])
    elif (sym in ['C4_4', 'D8_4']):
        for x in xrange(0, len(thesoup), 2):
            thesoup.append(thesoup[x+1])
            thesoup.append(-thesoup[x]-1)

    return thesoup


# Obtains a canonical representation of any oscillator/spaceship that (in
# some phase) fits within a 40-by-40 bounding box. This representation is
# alphanumeric and lowercase, and so much more compact than RLE. Compare:
#
# Common name: pentadecathlon
# Canonical representation: 4r4z4r4
# Equivalent RLE: 2bo4bo$2ob4ob2o$2bo4bo!
#
# It is a generalisation of a notation created by Allan Weschler in 1992.
def canonise(duration):

    representation = "#"

    # We need to compare each phase to find the one with the smallest
    # description:
    for t in xrange(duration):

        rect = g.getrect()
        if (len(rect) == 0):
            return "0"

        if ((rect[2] <= 40) & (rect[3] <= 40)):
            # Fits within a 40-by-40 bounding box, so eligible to be canonised.
            # Choose the orientation which results in the smallest description:
            representation = compare_representations(representation, canonise_orientation(rect[2], rect[3], rect[0], rect[1], 1, 0, 0, 1))
            representation = compare_representations(representation, canonise_orientation(rect[2], rect[3], rect[0]+rect[2]-1, rect[1], -1, 0, 0, 1))
            representation = compare_representations(representation, canonise_orientation(rect[2], rect[3], rect[0], rect[1]+rect[3]-1, 1, 0, 0, -1))
            representation = compare_representations(representation, canonise_orientation(rect[2], rect[3], rect[0]+rect[2]-1, rect[1]+rect[3]-1, -1, 0, 0, -1))
            representation = compare_representations(representation, canonise_orientation(rect[3], rect[2], rect[0], rect[1], 0, 1, 1, 0))
            representation = compare_representations(representation, canonise_orientation(rect[3], rect[2], rect[0]+rect[2]-1, rect[1], 0, -1, 1, 0))
            representation = compare_representations(representation, canonise_orientation(rect[3], rect[2], rect[0], rect[1]+rect[3]-1, 0, 1, -1, 0))
            representation = compare_representations(representation, canonise_orientation(rect[3], rect[2], rect[0]+rect[2]-1, rect[1]+rect[3]-1, 0, -1, -1, 0))

        g.run(1)

    return representation

# A subroutine used by canonise:
def canonise_orientation(length, breadth, ox, oy, a, b, c, d):

    representation = ""

    chars = "0123456789abcdefghijklmnopqrstuvwxyz"

    for v in xrange(int((breadth-1)/5)+1):
        zeroes = 0
        if (v != 0):
            representation += "z"
        for u in xrange(length):
            baudot = 0
            for w in xrange(5):
                x = ox + a*u + b*(5*v + w)
                y = oy + c*u + d*(5*v + w)
                baudot = (baudot >> 1) + 16*g.getcell(x, y)
            if (baudot == 0):
                zeroes += 1
            else:
                if (zeroes > 0):
                    if (zeroes == 1):
                        representation += "0"
                    elif (zeroes == 2):
                        representation += "w"
                    elif (zeroes == 3):
                        representation += "x"
                    else:
                        representation += "y"
                        representation += chars[zeroes - 4]
                zeroes = 0
                representation += chars[baudot]
    return representation

# Compares strings first by length, then by lexicographical ordering.
# A hash character is worse than anything else.
def compare_representations(a, b):

    if (a == "#"):
        return b
    elif (b == "#"):
        return a
    elif (len(a) < len(b)):
        return a
    elif (len(b) < len(a)):
        return b
    elif (a < b):
        return a
    else:
        return b

# Gets the period of an interleaving of degree-d polynomials:
def deepperiod(sequence, maxperiod, degree):

    for p in xrange(1, maxperiod, 1):

        good = True

        for i in xrange(maxperiod):

            diffs = [0] * (degree + 2)
            for j in xrange(degree + 2):

                diffs[j] = sequence[i + j*p]

            # Produce successive differences:
            for j in xrange(degree + 1):
                for k in xrange(degree + 1):
                    diffs[k] = diffs[k] - diffs[k + 1]

            if (diffs[0] != 0):
                good = False
                break

        if (good):
            return p
    return -1

# Analyses a linear-growth pattern, returning a hash:
def linearlyse(maxperiod):

    poplist = [0]*(3*maxperiod)

    for i in xrange(3*maxperiod):

        g.run(1)
        poplist[i] = int(g.getpop())

    p = deepperiod(poplist, maxperiod, 1)

    if (p == -1):
        return "unidentified"

    difflist = [0]*(2*maxperiod)

    for i in xrange(2*maxperiod):

        difflist[i] = poplist[i + p] - poplist[i]

    q = deepperiod(difflist, maxperiod, 0)

    moments = [0, 0, 0]

    for i in xrange(p):

        moments[0] += (poplist[i + q] - poplist[i])
        moments[1] += (poplist[i + q] - poplist[i]) ** 2
        moments[2] += (poplist[i + q] - poplist[i]) ** 3

    prehash = str(moments[1]) + "#" + str(moments[2])

    # Linear-growth patterns with growth rate zero are clearly errors!
    if (moments[0] == 0):
        return "unidentified"

    return "yl" + str(p) + "_" + str(q) + "_" + str(moments[0]) + "_" + hashlib.md5(prehash).hexdigest()

    
# This explodes pseudo-still-lifes and pseudo-oscillators into their
# constituent parts.
#
# -- Requires the period (if oscillatory) and graph-theoretic diameter
#    to not exceed 4096.
# -- Never mistakenly separates a true object.
# -- Correctly separates most pseudo-still-lifes, including the famous:
#    http://www.conwaylife.com/wiki/Quad_pseudo_still_life
# -- Works perfectly for all still-lifes of up to 17 bits.
# -- Doesn't separate 'locks', of which the smallest example has 18
#    bits and is unique:
#
#     ** **
#     ** **
#
#    * *** *
#    ** * **
#
# To use this function (standalone), merely copy it into a script of
# the following form:
#
#   import golly as g
#
#   def pseudo_bangbang():
#
#   [...]
#
#   pseudo_bangbang()
#
# and execute it in Golly with a B3/S23 universe containing any still-
# lifes or oscillators you want to separate. Pure objects correspond to
# connected components in the final state of the universe.
#
# This has dependencies on the rules ContagiousLife, PercolateInfection
# and EradicateInfection.
#
# Not to be confused with the Unix shell instruction for repeating the
# previous instruction as a superuser (sudo !!), or indeed with any
# parodies of this song: https://www.youtube.com/watch?v=YswhUHH6Ufc
#
# Adam P. Goucher, 2014-08-25
def pseudo_bangbang(alpharule):

    g.setrule("APG_ContagiousLife_" + alpharule)
    g.setbase(2)
    g.setstep(12)
    g.step()

    celllist = g.getcells(g.getrect())

    for i in xrange(0, len(celllist)-1, 3):
        
        # Only infect cells that haven't yet been infected:
        if (g.getcell(celllist[i], celllist[i+1]) <= 2):

            # Seed an initial 'infected' (red) cell:
            g.setcell(celllist[i], celllist[i+1], g.getcell(celllist[i], celllist[i+1]) + 2)

            prevpop = 0
            currpop = int(g.getpop())

            # Continue infecting until the entire component has been engulfed:
            while (prevpop != currpop):

                # Percolate the infection to every cell in the island:
                g.setrule("APG_PercolateInfection")
                g.setbase(2)
                g.setstep(12)
                g.step()

                # Transmit the infection across any bridges.
                g.setrule("APG_ContagiousLife_" + alpharule)
                g.setbase(2)
                g.setstep(12)
                g.step()

                prevpop = currpop
                currpop = int(g.getpop())
                
            g.fit()
            g.update()

            # Red becomes green:
            g.setrule("APG_EradicateInfection")
            g.step()


# Counts the number of live cells of each degree:
def degreecount():

    celllist = g.getcells(g.getrect())
    counts = [0,0,0,0,0,0,0,0,0]

    for i in xrange(0, len(celllist), 2):

        x = celllist[i]
        y = celllist[i+1]

        degree = -1

        for ux in xrange(x - 1, x + 2):
            for uy in xrange(y - 1, y + 2):

                degree += g.getcell(ux, uy)

        counts[degree] += 1

    return counts

# Counts the number of live cells of each degree in generations 1 and 2:
def degreecount2():

    g.run(1)
    a = degreecount()
    g.run(1)
    b = degreecount()

    return (a + b)


class Soup:

    # The rule generator:
    rg = isotropicRulegen.RuleGenerator()

    # Should we skip error-correction:
    skipErrorCorrection = False

    # A dict mapping binary representations of small possibly-pseudo-objects
    # to their equivalent canonised representation.
    #
    # This is many-to-one, as (for example) all of these will map to
    # the same pseudo-object (namely the beacon on block):
    #
    # ..**.**  ..**.**  **.....                           **.....
    # ..**.**  ...*.**  **.....                           *......
    # **.....  *......  ..**...                           ...*.**
    # **.....  **.....  ..**... [...12 others omitted...] ..**.**
    # .......  .......  .......                           .......
    # .......  .......  ..**...                           .......
    # .......  .......  ..**...                           .......
    #
    # The first few soups are much slower to process, as objects are being
    # entered into the cache.
    cache = {}

    # A dict to store memoized decompositions of possibly-pseudo-objects
    # into constituent parts. Caches results from pseudo_bangbang()
    # 
    # Initialized with ambiguous still lifes and any desired pseudo-objects
    # which should be censused without being decomposed
    decompositions = {  "xs18_3pq3qp3": ["xs14_3123qp3", "xs4_33"],
                        "xs10_2530352": ["xs10_2530352"],
    }

    # A dict of objects in the form {"identifier": ("common name", points)}
    #
    # As a rough heuristic, an object is worth 15 + log2(n) points if it
    # is n times rarer than the pentadecathlon.
    #
    # Still-lifes are limited to 10 points.
    # p2 oscillators are limited to 20 points.
    # p3 and p4 oscillators are limited to 30 points.
    #
    # List of Life objects removed
    # TODO: find a way to deal with common objects in new rules 
    commonnames = { "xp2_7": ("blinker", 0),
                    "xp2_2a54": ("clock", 0),
                    "xp2_7e": ("toad", 0),
                    "xp2_318c": ("beacon", 0),
                    "xs1_1": ("dot", 0),
                    "xs2_3": ("domino", 0),
                    "xs2_12": ("checker", 0),
                    "xs3_7": ("I tromino", 0),
                    "xs3_124": ("3 checker", 0),
                    "xs4_33": ("block", 0),
                    "xs4_f": ("I tetromino", 0),
                    "xs4_27": ("T tetromino", 0),
                    "xs4_252": ("tub", 0),
                    "xs5_253": ("boat", 0),
                    "xs6_bd": ("snake", 0),
                    "xs6_356": ("ship", 0),
                    "xs6_696": ("beehive", 0),
                    "xs6_25a4": ("barge", 0),
                    "xs6_39c": ("carrier", 0),
                    "xs7_3lo": ("long snake", 0),
                    "xs7_25ac": ("long boat", 0),
                    "xs7_178c": ("eater", 0),
                    "xs7_2596": ("loaf", 0),
                    "xs8_178k8": ("twit", 0),
                    "xs8_32qk": ("hook with tail", 0),
                    "xs8_69ic": ("mango", 0),
                    "xs8_6996": ("pond", 0),
                    "xs8_25ak8": ("long barge", 0),
                    "xs8_3pm": ("shillelagh", 0),
                    "xs8_312ko": ("canoe", 0),
                    "xs8_31248c": ("very long snake", 0),
                    "xs8_35ac": ("long ship", 0),
                    "xq4_153": ("glider", 0),
                    "xq4_1ba4": ("ant", 0),
                    "xq5_27": ("T ship", 0),
                    "xq4_6frc": ("lightweight spaceship", 0),
                    "xq4_27dee6": ("middleweight spaceship", 0),
                    "xq4_27deee6": ("heavyweight spaceship", 0),
                    "xs1_0_diehard": ("diehard", 0),
                    # Special case
                    "xs10_2530352": ("bi-boat", 0),
    }

    # First soup to contain a particular object:
    alloccur = {}

    # A tally of objects that have occurred during this run of apgsearch:
    objectcounts = {}

    # Any soups with positive scores, and the number of points.
    soupscores = {}

    # Temporary list of unidentified objects:
    unids = []

    # Things like glider guns and large oscillators belong here:
    superunids = []
    gridsize = 0
    resets = 0

    # For profiling purposes:
    qlifetime = 0.0
    ruletime = 0.0
    gridtime = 0.0

    glidersexist = False
    
    # Test if Life's glider works in this rule
    # Can expand this to determine which are the common small objects that
    # exist in the rule
    def testglider(self):
        
        g.new("Test glider existence")
        g.setrule(self.rg.rulename)

        clglider = [1,0,2,1,0,2,1,2,2,2]
        g.putcells(clglider)
        g.setbase(2)
        g.setstep(2)
        g.step()

        g.putcells(clglider,1,1,1,0,0,1,"xor")
        if int(g.getpop())==0:
            self.glidersexist = True
        
    # Increment object count by given value:
    def incobject(self, obj, incval):
        if (incval > 0):
            if obj in self.objectcounts:
                self.objectcounts[obj] = self.objectcounts[obj] + incval
            else:
                self.objectcounts[obj] = incval

    # Increment soup score by given value:
    def awardpoints(self, soupid, incval):
        if (incval > 0):
            if soupid in self.soupscores:
                self.soupscores[soupid] = self.soupscores[soupid] + incval
            else:
                self.soupscores[soupid] = incval

    # Increment soup score by appropriate value:
    def awardpoints2(self, soupid, obj):
        
        # Record the occurrence of this object:
        if (obj in self.alloccur):
            if (len(self.alloccur[obj]) < 10):
                if (soupid not in self.alloccur[obj]):
                    self.alloccur[obj] += [soupid]
        else:
            self.alloccur[obj] = [soupid]
        
        if obj in self.commonnames:
            self.awardpoints(soupid, self.commonnames[obj][1])
        elif (obj[0] == 'x'):
            prefix = obj.split('_')[0]
            prenum = int(prefix[2:])
            if (obj[1] == 's'):
                self.awardpoints(soupid, 10) # rare still-lifes are limited to 10 points
            elif (obj[1] == 'p'):
                if (prenum == 2):
                    self.awardpoints(soupid, 20) # p2 oscillators are limited to 20 points
                elif ((prenum == 3) | (prenum == 4)):
                    self.awardpoints(soupid, 30) # p3 and p4 oscillators are limited to 30 points
                else:
                    self.awardpoints(soupid, 40)
            else:
                self.awardpoints(soupid, 50)
        else:
            self.awardpoints(soupid, 50)

    # Assuming the pattern has stabilised, perform a census:
    def census(self, stepsize):
        
        g.setrule("APG_CoalesceObjects_" + self.rg.alphanumeric)
        g.setbase(2)
        g.setstep(min(8,stepsize))
        g.step()

        # glidersexist detection moved to separate method
        
        if (self.glidersexist):
            g.setrule("APG_IdentifyGliders")
            g.setbase(2)
            g.setstep(2)
            g.step()

        g.setrule("APG_ClassifyObjects_" + self.rg.alphanumeric)
        g.setbase(2)
        g.setstep(max(8, stepsize))
        g.step()
        
        # Only do this if we have an infinite-growth pattern:
        if (stepsize > 8):
            g.setrule("APG_HandlePlumesCorrected")
            g.setbase(2)
            g.setstep(1)
            g.step()
            g.setrule("APG_ClassifyObjects_" + self.rg.alphanumeric)
            g.setstep(stepsize)
            g.step()

        # Remove any gliders:
        if (self.glidersexist):
            g.setrule("APG_ExpungeGliders")
            g.run(1)
            pop5 = int(g.getpop())
            g.run(1)
            pop6 = int(g.getpop())
            self.incobject("xq4_153", (pop5 - pop6)/5)
        
        # Remove dots, dominos, triominos and blocks:
        g.setrule("APG_ExpungeSmallSL")
        pop0 = int(g.getpop())
        g.run(1)
        pop1 = int(g.getpop())
        g.run(1)
        pop2 = int(g.getpop())
        g.run(1)
        pop3 = int(g.getpop())
        g.run(1)
        pop4 = int(g.getpop())

        # Small Still Life objects removed by ExpungeSmallSL:
        self.incobject("xs1_1", (pop0-pop1))
        self.incobject("xs2_3", (pop1-pop2)/2)
        self.incobject("xs3_7", (pop2-pop3)/3)
        self.incobject("xs4_33", (pop3-pop4)/4)
        

    # Removes an object incident with (ix, iy) and returns the cell list:
    def grabobj(self, ix, iy):

        allcells = [ix, iy, g.getcell(ix, iy)]
        g.setcell(ix, iy, 0)
        livecells = []
        deadcells = []

        marker = 0
        ll = 3

        while (marker < ll):
            x = allcells[marker]
            y = allcells[marker+1]
            z = allcells[marker+2]
            marker += 3

            if ((z % 2) == 1):
                livecells.append(x)
                livecells.append(y)
            else:
                deadcells.append(x)
                deadcells.append(y)

            for nx in xrange(x - 1, x + 2):
                for ny in xrange(y - 1, y + 2):

                    nz = g.getcell(nx, ny)
                    if (nz > 0):
                        allcells.append(nx)
                        allcells.append(ny)
                        allcells.append(nz)
                        g.setcell(nx, ny, 0)
                        ll += 3

        return livecells

    # Command to Grab, Remove and IDentify an OBJect:
    def gridobj(self, ix, iy, gsize, gspacing, pos):

        allcells = [ix, iy, g.getcell(ix, iy)]
        g.setcell(ix, iy, 0)
        livecells = []
        deadcells = []

        # This tacitly assumes the object is smaller than 1000-by-1000.
        # But this is okay, since it is only used by the routing logic.
        dleft = ix + 1000
        dright = ix - 1000
        dtop = iy + 1000
        dbottom = iy - 1000

        lleft = ix + 1000
        lright = ix - 1000
        ltop = iy + 1000
        lbottom = iy - 1000

        lpop = 0
        dpop = 0

        marker = 0
        ll = 3

        while (marker < ll):
            x = allcells[marker]
            y = allcells[marker+1]
            z = allcells[marker+2]
            marker += 3

            if ((z % 2) == 1):
                livecells.append(x)
                livecells.append(y)
                lleft = min(lleft, x)
                lright = max(lright, x)
                ltop = min(ltop, y)
                lbottom = max(lbottom, y)
                lpop += 1
            else:
                deadcells.append(x)
                deadcells.append(y)
                dleft = min(dleft, x)
                dright = max(dright, x)
                dtop = min(dtop, y)
                dbottom = max(dbottom, y)
                dpop += 1

            for nx in xrange(x - 1, x + 2):
                for ny in xrange(y - 1, y + 2):

                    nz = g.getcell(nx, ny)
                    if (nz > 0):
                        allcells.append(nx)
                        allcells.append(ny)
                        allcells.append(nz)
                        g.setcell(nx, ny, 0)
                        ll += 3

        lwidth = max(0, 1 + lright - lleft)
        lheight = max(0, 1 + lbottom - ltop)
        dwidth = max(0, 1 + dright - dleft)
        dheight = max(0, 1 + dbottom - dtop)

        llength = max(lwidth, lheight)
        lbreadth = min(lwidth, lheight)
        dlength = max(dwidth, dheight)
        dbreadth = min(dwidth, dheight)

        self.gridsize = max(self.gridsize, llength)

        objid = "unidentified"
        bitstring = 0

        if (lpop == 0):
            objid = "nothing"
        else:
            if ((lwidth <= 7) & (lheight <= 7)):
                for i in xrange(0, lpop*2, 2):
                    bitstring += (1 << ((livecells[i] - lleft) + 7*(livecells[i + 1] - ltop)))

                if bitstring in self.cache:
                    objid = self.cache[bitstring]

        if (objid == "unidentified"):
            # This has passed through the routing logic without being identified,
            # so save it in a temporary list for later identification:
            self.unids.append(bitstring)
            self.unids.append(livecells)
            self.unids.append(lleft)
            self.unids.append(ltop)
        elif (objid != "nothing"):
            # The object is non-empty, so add it to the census:
            ux = int(0.5 + float(lleft)/float(gspacing))
            uy = int(0.5 + float(ltop)/float(gspacing))
            soupid = ux + (uy * gsize) + pos
            
            for comp in self.decompositions[objid]:
                self.incobject(comp, 1)
                self.awardpoints2(soupid, comp)


    # Tests for population periodicity:
    def naivestab(self, period, security, length):

        depth = 0
        prevpop = 0
        for i in xrange(length):
            g.run(period)
            currpop = int(g.getpop())
            if (currpop == prevpop):
                depth += 1
            else:
                depth = 0
            prevpop = currpop
            if (depth == security):
                # Population is periodic.
                return True

        return False

    # This should catch most short-lived soups with few gliders produced:
    def naivestab2(self, period, length):

        for i in xrange(length):
            r = g.getrect()
            if (len(r) == 0):
                return True
            pop0 = int(g.getpop())
            g.run(period)
            hash1 = g.hash(r)
            pop1 = int(g.getpop())
            g.run(period)
            hash2 = g.hash(r)
            pop2 = int(g.getpop())

            if ((hash1 == hash2) & (pop0 == pop1) & (pop1 == pop2)):

                if (g.getrect() == r):
                    return True
                
                g.run((2*int(max(r[2], r[3])/period)+1)*period)
                hash3 = g.hash(r)
                pop3 = int(g.getpop())
                if ((hash2 == hash3) & (pop2 == pop3)):
                    return True

        return False
            
    # Runs a pattern until stabilisation with a 99.99996% success rate.
    # False positives are handled by a later error-correction stage.
    def stabilise3(self):

        # Phase I of stabilisation detection, designed to weed out patterns
        # that stabilise into a cluster of low-period oscillators within
        # about 6000 generations.

        if (self.naivestab2(12, 10)):
            return 4;

        if (self.naivestab(20, 30, 100)):
            return 5;

        if (self.naivestab(40, 30, 150)):
            return 6;

        # Phase II of stabilisation detection, which is much more rigorous
        # and based on oscar.py.

        # Should be sufficient:
        prect = [-1000, -1000, 2000, 2000]

        # initialize lists
        hashlist = []        # for pattern hash values
        genlist = []         # corresponding generation counts

        for j in xrange(4000):

            g.run(30)

            h = g.hash(prect)

            # determine where to insert h into hashlist
            pos = 0
            listlen = len(hashlist)
            while pos < listlen:
                if h > hashlist[pos]:
                    pos += 1
                elif h < hashlist[pos]:
                    # shorten lists and append info below
                    del hashlist[pos : listlen]
                    del genlist[pos : listlen]
                    break
                else:
                    period = (int(g.getgen()) - genlist[pos])

                    prevpop = g.getpop()

                    for i in xrange(20):
                        g.run(period)
                        currpop = g.getpop()
                        if (currpop != prevpop):
                            period = max(period, 4000)
                            break
                        prevpop = currpop
                        
                    return max(1 + int(math.log(period, 2)), 3)

            hashlist.insert(pos, h)
            genlist.insert(pos, int(g.getgen()))

        g.setrule(self.rg.rulename)
        g.setbase(2)
        g.setstep(16)
        g.step()
        g.setrule(self.rg.rulename)

        return 12

    # Differs from oscar.py in that it detects absolute cycles, not eventual cycles.
    def bijoscar(self, maxsteps):

        initpop = int(g.getpop())
        initrect = g.getrect()
        if (len(initrect) == 0):
            return 0
        inithash = g.hash(initrect)

        for i in xrange(maxsteps):

            g.run(1)

            if (int(g.getpop()) == initpop):

                prect = g.getrect()
                phash = g.hash(prect)

                if (phash == inithash):

                    period = i + 1

                    if (prect == initrect):
                        return period
                    else:
                        return -period
        return -1

    # For a non-moving unidentified object, we check the dictionary of
    # memoized decompositions of possibly-pseudo-objects. If the object is
    # not already in the dictionary, it will be memoized.
    #
    # Low-period spaceships are also separated by this routine, although
    # this is less important now that there is a more bespoke prodecure
    # to handle disjoint unions of standard spaceships.
    #
    # @param moving  a bool which specifies whether the object is moving
    def enter_unid(self, unidname, soupid, moving):

        if not(unidname in self.decompositions):

            # Separate into pure components:
            if (moving):
                g.setrule("APG_CoalesceObjects_" + self.rg.alphanumeric)
                period = int(unidname[2:unidname.find('_')])
                g.run(period)
            else:
                pseudo_bangbang(self.rg.alphanumeric)

            listoflists = [] # which incidentally don't contain themselves.

            # Someone who plays the celllo:
            celllist = g.join(g.getcells(g.getrect()), [0])

            for i in xrange(0, len(celllist)-1, 3):
                if (g.getcell(celllist[i], celllist[i+1]) != 0):
                    livecells = self.grabobj(celllist[i], celllist[i+1])
                    if (len(livecells) > 0):
                        listoflists.append(livecells)

            listofobjs = []

            for livecells in listoflists:

                g.new("Subcomponent")
                g.setrule(self.rg.rulename)
                g.putcells(livecells)
                period = self.bijoscar(1000)
                canonised = canonise(abs(period))
                if (period < 0):
                    listofobjs.append("xq"+str(0-period)+"_"+canonised)
                elif (period == 1):
                    listofobjs.append("xs"+str(len(livecells)/2)+"_"+canonised)
                else:
                    listofobjs.append("xp"+str(period)+"_"+canonised)

            self.decompositions[unidname] = listofobjs

        # Actually add to the census:
        for comp in self.decompositions[unidname]:
            self.incobject(comp, 1)
            self.awardpoints2(soupid, comp)

    # This function has lots of arguments (hence the name):
    #
    # @param gsize     the square-root of the number of soups per page
    # @param gspacing  the minimum distance between centres of soups
    # @param ashes     a list of cell lists
    # @param stepsize  binary logarithm of amount of time to coalesce objects
    # @param intergen  binary logarithm of amount of time to run HashLife
    # @param pos       the index of the first soup on the page
    def teenager(self, gsize, gspacing, ashes, stepsize, intergen, pos):

        # If this gets incremented, we panic and perform error-correction:
        pathological = 0

        # Draw the soups:
        for i in xrange(gsize * gsize):

            x = int(i % gsize)
            y = int(i / gsize)

            g.putcells(ashes[3*i], gspacing * x, gspacing * y)

        # Because why not?
        g.fit()
        g.update()

        # For error-correction:
        if (intergen > 0):
            g.setrule(self.rg.rulename)
            g.setbase(2)
            g.setstep(intergen)
            g.step()

        # Apply rules to coalesce objects and expunge annoyances such as
        # blocks, blinkers, beehives and gliders:
        start_time = time.clock()
        self.census(stepsize)
        end_time = time.clock()
        self.ruletime += (end_time - start_time)

        # Now begin identifying objects:
        start_time = time.clock()
        celllist = g.join(g.getcells(g.getrect()), [0])

        if (len(celllist) > 2):
            for i in xrange(0, len(celllist)-1, 3):
                if (g.getcell(celllist[i], celllist[i+1]) != 0):
                    self.gridobj(celllist[i], celllist[i+1], gsize, gspacing, pos)

        # If we have leftover unidentified objects, attempt to canonise them:
        while (len(self.unids) > 0):
            ux = int(0.5 + float(self.unids[-2])/float(gspacing))
            uy = int(0.5 + float(self.unids[-1])/float(gspacing))
            soupid = ux + (uy * gsize) + pos
            unidname = self.process_unid()
            if (unidname == "PATHOLOGICAL"):
                pathological += 1
            if (unidname != "nothing"):

                if ((unidname[0] == 'x') & ((unidname[1] == 's') | (unidname[1] == 'p'))):
                    self.enter_unid(unidname, soupid, False)
                elif ((unidname[0] == 'x') & (unidname[1] == 'q')):
                        # Separates non-standard spaceships in medium proximity:
                        self.enter_unid(unidname, soupid, True)
                else:
                    self.incobject(unidname, 1)
                    self.awardpoints2(soupid, unidname)

        end_time = time.clock()
        self.gridtime += (end_time - start_time)

        return pathological

    # This basically orchestrates everything:
    def stabilise_soups_parallel(self, root, pos, gsize):

        ashes = []
        stepsize = 3

        g.new("Random soups")
        g.setrule(self.rg.rulename)

        gspacing = 0

        # Generate and run the soups until stabilisation:
        for i in xrange(gsize * gsize):

            # Generate the soup from the SHA-256 of the concatenation of the
            # seed with the index:
            g.putcells(hashsoup(root + str(pos + i), symmstring), -8, -8)

            # Run the soup until stabilisation:
            start_time = time.clock()
            stepsize = max(stepsize, self.stabilise3())
            end_time = time.clock()
            self.qlifetime += (end_time - start_time)

            # Ironically, the spelling of this variable is incurrrect:
            currrect = g.getrect()
            ashes.append(g.getcells(currrect))

            if (len(currrect) == 4):
                ashes.append(currrect[0])
                ashes.append(currrect[1])
                # Choose the grid spacing based on the size of the ash:
                gspacing = max(gspacing, 2*currrect[2])
                gspacing = max(gspacing, 2*currrect[3])
                g.select(currrect)
                g.clear(0)
            else:
                # Stabilized soup is empty
                ashes.append(0)
                ashes.append(0)
                self.incobject("xs1_0_diehard", 1)
                self.awardpoints2(str(pos+i), "xs1_0_diehard")
            g.select([])

        # Account for any extra enlargement caused by running CoalesceObjects:
        gspacing += 2 ** (stepsize + 1) + 1000

        # Remember the dictionary, just in case we have a pathological object:
        prevdict = self.objectcounts.copy()
        prevscores = self.soupscores.copy()
        prevunids = self.superunids[:]

        if (self.teenager(gsize, gspacing, ashes, stepsize, 0, pos) > 0):
            if (self.skipErrorCorrection == False):
                # Arrrggghhhh, there's a pathological object! Usually this means
                # that naive stabilisation detection returned a false positive.
                self.resets += 1
                
                # Reset the object counts:
                self.objectcounts = prevdict
                self.soupscores = prevscores
                self.superunids = prevunids

                # 2^18 generations should suffice. This takes about 30 seconds in
                # HashLife, but error-correction only occurs very infrequently, so
                # this has a negligible impact on mean performance:
                gspacing += 2 ** 19
                stepsize = max(stepsize, 12)
                
                # Clear the universe:
                g.new("Error-correcting phase")
                self.teenager(gsize, gspacing, ashes, stepsize, 18, pos)

        # Erase any ashes. Not least because England usually loses...
        ashes = []

    # Pop the last unidentified object from the stack, and attempt to
    # ascertain its period and classify it.
    def process_unid(self):

        g.new("Unidentified object")
        g.setrule(self.rg.rulename)
        y = self.unids.pop()
        x = self.unids.pop()
        livecells = self.unids.pop()
        bitstring = self.unids.pop()
        g.putcells(livecells, -x, -y, 1, 0, 0, 1, "or")
        period = self.bijoscar(1000)
        
        if (period == -1):
            # Infinite growth pattern, probably. Most infinite-growth
            # patterns are linear-growth (such as puffers, wickstretchers,
            # guns etc.) so we analyse to see whether we have a linear-
            # growth pattern:
            
            descriptor = linearlyse(1000)
            if (descriptor[0] == "y"):
                return descriptor

            # Okay, so it's not linear growth. It may be an unstabilised
            # ember that slipped through the net, but this will be handled
            # by error-correction (unless it persists another 2^18 gens,
            # which is so unbelievably improbable that you are more likely
            # to be picked up by a passing ship in the vacuum of space).
            self.superunids.append(livecells)
            self.superunids.append(x)
            self.superunids.append(y)
            
            return "PATHOLOGICAL"
        elif (period == 0):
            return "nothing"
        else:
            
            canonised = canonise(abs(period))

            if (canonised == "#"):

                # Okay, we know that it's an oscillator or spaceship with
                # a non-astronomical period. But it's too large to canonise
                # in any of its phases (i.e. transcends a 40-by-40 box).
                self.superunids.append(livecells)
                self.superunids.append(x)
                self.superunids.append(y)
                
                return "OVERSIZED"
            
            else:

                # Prepend a prefix according to whether it is a still-life,
                # oscillator or moving object:
                if (period == 1):
                    descriptor = ("xs"+str(len(livecells)/2)+"_"+canonised)
                elif (period > 0):
                    descriptor = ("xp"+str(period)+"_"+canonised)
                else:
                    descriptor = ("xq"+str(0-period)+"_"+canonised)

                if (bitstring > 0):
                    self.cache[bitstring] = descriptor

                return descriptor

    # This doesn't really do much, since unids should be empty and
    # actual pathological/oversized objects will rarely arise naturally.
    def display_unids(self):

        g.new("Unidentified objects")
        g.setrule(self.rg.rulename)

        rowlength = 1 + int(math.sqrt(len(self.superunids)/3))

        for i in xrange(len(self.superunids)/3):

            xpos = i % rowlength
            ypos = int(i / rowlength)

            g.putcells(self.superunids[3*i], xpos * (self.gridsize + 8) - self.superunids[3*i + 1], ypos * (self.gridsize + 8) - self.superunids[3*i + 2], 1, 0, 0, 1, "or")

        g.fit()
        g.update()

    # Saves a machine-readable textual file containing the census:
    def save_progress(self, numsoups, root, symmetry="C1"):

        g.show("Saving progress...")

        # Count the total number of objects:
        totobjs = 0
        censustable = "@CENSUS TABLE\n"
        tlist = sorted(self.objectcounts.iteritems(), key=operator.itemgetter(1), reverse=True)
        for objname, count in tlist:
            totobjs += count
            censustable += objname + " " + str(count) + "\n"

        g.show("Writing header information...")

        # The MD5 hash of the root string:
        md5root = hashlib.md5(root).hexdigest()

        # Header information:
        results = "@SEARCH apgsearch-isotropic v0.2\n"
        results += "@MD5 "+md5root+"\n"
        results += "@ROOT "+root+"\n"
        results += "@RULE "+self.rg.rulename+"\n"
        results += "@SYMMETRY "+symmetry+"\n"
        results += "@NUM_SOUPS "+str(numsoups)+"\n"
        results += "@NUM_OBJECTS "+str(totobjs)+"\n"

        results += "\n"

        # Census table:
        results += censustable

        g.show("Compactifying score table...")

        results += "\n"

        # Number of soups to record:
        highscores = 100

        results += "@TOP "+str(highscores)+"\n"

        ilist = sorted(self.soupscores.iteritems(), key=operator.itemgetter(1), reverse=True)

        # Empty the high score table:
        self.soupscores = {}
        
        for soupnum, score in ilist[:highscores]:
            self.soupscores[soupnum] = score
            results += str(soupnum) + " " + str(score) + "\n"

        g.show("Saving soupids for rare objects...")

        results += "\n@SAMPLE_SOUPIDS\n"
        for objname, count in tlist:
            # blinkers and gliders have no alloccur[] entry for some reason,
            # so the line below avoids errors in B3/S23, maybe other rules too?
            if objname in self.alloccur:
                results += objname
                for soup in self.alloccur[objname]:
                    results += " " + str(soup)
                results += "\n"

        g.show("Writing progress file...")

        dirname = g.getdir("data")
        separator = dirname[-1]
        progresspath = dirname + "apgsearch-isotropic" + separator + "progress" + separator
        if not os.path.exists(progresspath):
            os.makedirs(progresspath)

        filename = progresspath + "search_" + md5root + ".txt"
        
        try:
            f = open(filename, 'w')
            f.write(results)
            f.close()
        except:
            g.warn("Unable to create progress file:\n" + filename)

    # Save soup RLE:
    def save_soup(self, root, soupnum, symmetry):

        # Soup pattern will be stored in a temporary directory:
        souphash = hashlib.sha256(root + str(soupnum))
        rlepath = souphash.hexdigest()
        rlepath = g.getdir("temp") + rlepath + ".rle"
        
        results = "<a href=\"open:" + rlepath + "\">"
        results += str(soupnum)
        results += "</a>"

        try:
            g.store(hashsoup(root + str(soupnum), symmetry), rlepath)
        except:
            g.warn("Unable to create soup pattern:\n" + rlepath)

        return results
        
    # Display results in Help window:
    def display_census(self, numsoups, root, symmetry):

        dirname = g.getdir("data")
        separator = dirname[-1]
        apgpath = dirname + "apgsearch-isotropic" + separator
        objectspath = apgpath + "objects" + separator + self.rg.alphanumeric + separator
        if not os.path.exists(objectspath):
            os.makedirs(objectspath)

        results = "<html>\n<title>Census results</title>\n<body bgcolor=\"#FFFFCE\">\n"
        results += "<p>Census results after processing " + str(numsoups) + " soups in rule " + \
            self.rg.rulename + "(seed = " + root + ", symmetry = " + symmetry + "):\n"

        tlist = sorted(self.objectcounts.iteritems(), key=operator.itemgetter(1), reverse=True)    
        results += "<p><center>\n"
        results += "<table cellspacing=1 border=2 cols=2>\n"
        results += "<tr><td>&nbsp;Object&nbsp;</td><td align=center>&nbsp;Common name&nbsp;</td>\n"
        results += "<td align=right>&nbsp;Count&nbsp;</td><td>&nbsp;Sample occurrences&nbsp;</td></tr>\n"
        for objname, count in tlist:
            if (objname[0] == 'x'):
                if (objname[1] == 'p'):
                    results += "<tr bgcolor=\"#CECECF\">"
                elif (objname[1] == 'q'):
                    results += "<tr bgcolor=\"#CEFFCE\">"
                else:
                    results += "<tr>"
            else:
                results += "<tr bgcolor=\"#FFCECE\">"
            results += "<td>"
            results += "&nbsp;"
            
            # Using "open:" link enables one to click on the object name to open the pattern in Golly:
            rlepath = objectspath + objname + ".rle"
            if (objname[0] == 'x'):
                results += "<a href=\"open:" + rlepath + "\">"
            # If the name is longer than that of the block-laying switch engine:
            if len(objname) > 51:
                # Contract name and include ellipsis:
                results += objname[:40] + "&#8230;" + objname[-10:]
            else:
                results += objname
            if (objname[0] == 'x'):
                results += "</a>"
            results += "&nbsp;"

            if (objname[0] == 'x'):
                # save object in rlepath if it doesn't exist
                if not os.path.exists(rlepath):
                    # Canonised objects are at most 40-by-40:
                    rledata = "x = 40, y = 40, rule = " + self.rg.rulename + "\n"
                    # http://ferkeltongs.livejournal.com/15837.html
                    compact = objname.split('_')[1] + "z"
                    i = 0
                    strip = []
                    while (i < len(compact)):
                        c = ord2(compact[i])
                        if (c >= 0):
                            if (c < 32):
                                # Conventional character:
                                strip.append(c)
                            else:
                                if (c == 35):
                                    # End of line:
                                    if (len(strip) == 0):
                                        strip.append(0)
                                    for j in xrange(5):
                                        for d in strip:
                                            if ((d & (1 << j)) > 0):
                                                rledata += "o"
                                            else:
                                                rledata += "b"
                                        rledata += "$\n"
                                    strip = []
                                else:
                                    # Multispace character:
                                    strip.append(0)
                                    strip.append(0)
                                    if (c >= 33):
                                        strip.append(0)
                                    if (c == 34):
                                        strip.append(0)
                                        i += 1
                                        d = ord2(compact[i])
                                        for j in xrange(d):
                                            strip.append(0)
                        i += 1
                    # End of pattern representation:
                    rledata += "!\n"
                    try:
                        f = open(rlepath, 'w')
                        f.write(rledata)
                        f.close()
                    except:
                        g.warn("Unable to create object pattern:\n" + rlepath)
            
            results += "</td><td align=center>&nbsp;"
            if (objname in self.commonnames):
                results += self.commonnames[objname][0]
            results += "&nbsp;</td><td align=right>&nbsp;" + str(count) + "&nbsp;"
            results += "</td><td>"
            if objname in self.alloccur:
                results += "&nbsp;"
                for soup in self.alloccur[objname]:
                    results += self.save_soup(root, soup, symmetry) 
                    results += "&nbsp;"
            results += "</td></tr>\n"
        results += "</table>\n</center>\n"

        ilist = sorted(self.soupscores.iteritems(), key=operator.itemgetter(1), reverse=True)
        results += "<p><center>\n"
        results += "<table cellspacing=1 border=2 cols=2>\n"
        results += "<tr><td>&nbsp;Soup number&nbsp;</td><td align=right>&nbsp;Score&nbsp;</td></tr>\n"
        for soupnum, score in ilist[:50]:
            results += "<tr><td>&nbsp;"
            results += self.save_soup(root, soupnum, symmetry)
            results += "&nbsp;</td><td align=right>&nbsp;" + str(score) + "&nbsp;</td></tr>\n"
        
        results += "</table>\n</center>\n"
        results += "</body>\n</html>\n"
        
        htmlname = apgpath + "latest_census.html"
        try:
            f = open(htmlname, 'w')
            f.write(results)
            f.close()
            g.open(htmlname)
        except:
            g.warn("Unable to create html file:\n" + htmlname)
        

# Converts a base-36 case-insensitive alphanumeric character into a
# numerical value.
def ord2(char):

    x = ord(char)

    if ((x >= 48) & (x < 58)):
        return x - 48

    if ((x >= 65) & (x < 91)):
        return x - 55

    if ((x >= 97) & (x < 123)):
        return x - 87

    return -1


# Obtain the parameters to conduct the search:
number = int(g.getstring("How many soups to search?", "1000000"))
rootstring = g.getstring("What seed to use for this search (make this unique)?", datetime.datetime.now().replace(microsecond=0).isoformat()+"_")
rulestring = g.getstring("Which rule to use?", "B3/S2-i34q")
symmstring = g.getstring("What symmetries to use?", "C1")
# initpos = int(g.getstring("Initial position: ", "0"))
initpos = 0

if symmstring not in ["8x32", "C1", "C2_1", "C2_2", "C2_4", "C4_1", "C4_4", \
    "D2_+1", "D2_+2", "D2_x", "D4_+1", "D4_+2", "D4_+4", "D4_x1", "D4_x4", "D8_1", "D8_4"]:
    g.exit(symmstring+" is not a valid symmetry option")
soup = Soup()
soup.rg.setrule(rulestring)
soup.rg.saveAllRules()
soup.testglider()

# Disable error correction
soup.skipErrorCorrection = True

scount = 0
start_time = time.clock()

# We have 100 soups per page, instead of one. This parallel approach
# was suggested by Tomas Rokicki, and results in approximately a
# fourfold increase in soup-searching speed!
sqrtspp = 7
spp = sqrtspp ** 2

# Do stuff repeatedly:
for i in xrange(int((number-1)/spp)+1):

    page_time = time.clock()
    
    soup.stabilise_soups_parallel(rootstring, scount + initpos, sqrtspp)
    scount = spp*(i+1)
    
    current_speed = int((sqrtspp * sqrtspp)/(time.clock() - page_time))
    alltime_speed = int((scount)/(time.clock() - start_time))

    g.show(str(scount) + " soups processed (" + str(current_speed) +
        " per second current; " + str(alltime_speed) + " overall)" +
        " : (type 's' to see latest census or 'q' to quit).")

    # Automatically save progress every 250000 soups:
    if ((scount % 250000) == 0):
        soup.save_progress(scount, rootstring, symmstring)
    
    event = g.getevent()
    if event.startswith("key"):
        evt, ch, mods = event.split()
        if ch == "s":
            soup.save_progress(scount, rootstring, symmstring)
            soup.display_census(scount, rootstring, symmstring)
        elif ch == "q":
            break

end_time = time.clock()

soup.save_progress(scount, rootstring, symmstring)

# Give the number of soups processed together with the amount of time
# elapsed (and indications as to which parts of the script are taking
# the longest).
g.show(str(scount) + " soups processed in " + str(end_time - start_time) +
       "(" + str(soup.qlifetime) + ", " + str(soup.ruletime) + ", " + str(soup.gridtime) + ") secs.")

soup.display_unids()
soup.display_census(scount, rootstring, symmstring)
