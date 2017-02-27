# *************************************
# * Ash Pattern Generator (apgsearch) *
# *************************************
# * HACKED for custom rules           *
# *************************************
# * Version: v0.54+0.21i (beta release)*
# *************************************
# NOTICE: Below information may or may not be accurate.
# -- Processes roughly 100 soups per (second . core . GHz) in Life (B3/S23).
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
# -- NEW!  Pseudo-pattern detection and separation may now be turned off.
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
# -- Preliminary support for other outer-totalistic and isotropic
#    non-totalistic rules, including detection and classification
#    of various types of infinite growth.
#
# -- NEW!  Optionally uploads results to https://catagolue.appspot.com/census
#          (pseudo-pattern separation must be turned on).
#
# By Adam P. Goucher, with contributions from Andrew Trevorrow, Tom Rokicki,
# Nathaniel Johnston, Dave Greene, and Aidan Pierce.

import golly as g
from glife import rect, pattern
import time
import math
import operator
import hashlib
import datetime
import os
import urllib2

#Version "number"
vnum = "v0.54+0.21i"

'''#Stores whether the rule is outer-totalistic or not
ruletype = True'''

def get_server_address():
    # Should be 'http://catagolue.appspot.com' for the released version,
    # and 'http://localhost:8080' for the development version:    
    return 'http://catagolue.appspot.com'

# Engages with Catagolue's authentication system ('payment over SHA-256',
# affectionately abbreviated to 'payosha256'):
#
# The payosha256_key can be obtained from logging into Catagolue in your
# web browser and visiting http://catagolue.appspot.com/payosha256
def authenticate(payosha256_key, operation_name):

    g.show("Authenticating with Catagolue via the payosha256 protocol...")

    payload = "payosha256:get_token:"+payosha256_key+":"+operation_name

    req = urllib2.Request(get_server_address() + "/payosha256", payload, {"Content-type": "text/plain"})
    f = urllib2.urlopen(req)

    if (f.getcode() != 200):
        return None

    resp = f.read()

    lines = resp.splitlines()

    for line in lines:
        parts = line.split(':')

        if (len(parts) < 3):
            continue

        if (parts[1] != 'good'):
            continue

        target = parts[2]
        token = parts[3]

        g.show("Token " + token + " obtained from payosha256. Performing proof of work with target " + target + "...")

        for nonce in xrange(100000000):

            prehash = token + ":" + str(nonce)
            posthash = hashlib.sha256(prehash).hexdigest()

            if (posthash < target):
                break

        if (posthash > target):
            continue

        g.show("String "+prehash+" is sufficiently valuable ("+posthash+" < "+target+").")

        payload = "payosha256:pay_token:"+prehash+"\n"

        return payload

    return None

# Sends the results to Catagolue:
def catagolue_results(results, payosha256_key, operation_name, endpoint="/apgsearch", return_point=None):

    try:

        payload = authenticate(payosha256_key, operation_name)

        if payload is None:
            return 1

        payload += results

        req = urllib2.Request(get_server_address() + endpoint, payload, {"Content-type": "text/plain"})

        f = urllib2.urlopen(req)

        if (f.getcode() != 200):
            return 2

        resp = f.read()

        try:
            f2 = open(g.getdir("data")+"catagolue-response.txt", 'w')
            f2.write(resp)
            f2.close()

            if return_point is not None:
                return_point[0] = resp
            
        except:
            g.warn("Unable to save catagolue response file.")

        return 0

    except:

        return 1

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

# Checks if symmetry is a valid one.
def check(string):
    symmetries = {"C1": [],
                  "C2": ["1", "2", "4"],
                  "C4": ["1", "4"],
                  "D2": ["+1", "+2", "x"],
                  "D4": ["+1", "+2", "+4", "x1", "x4"],
                  "D8": ["1", "4"]}

    if len(string.split("_")) != 2:
        if string == "C1":
            return "C1"
        g.exit("Please enter a valid symmetry.")

    pr, z = string.split("_")
    if symmetries.has_key(pr):
        for part in symmetries[pr]:
            if part == z:
                return string

    g.exit("Please enter a valid symmetry.")

# Converts human-readable symmetry to
# machine-readable symmetry
def convert(sym):
    if sym == "C1":
        return "000000"
    pr, z = sym.split("_")

    if pr == "C2":
        if z == "1":
            return "000110"
        if z == "4":
            return "000220"
        else:
            return "000210"

    if pr == "C4":
        if z == "1":
            return "000001"
        else:
            return "000002"

    if pr == "D2":
        if z[0] == "+":
            return "00%s000" % (z[1:])
        else:
            return "100000"

    if pr == "D4":
        if z[0] == "+":
            ox = int(int(z[1:])/4)+1
            oy = 2-(int(z[1:])%2)
            return "0%d%d000" % (ox, oy)
        if z[0] == "x":
            if z[1:] == "1":
                return "200000"
            else:
                return "300000"

    if pr == "D8":
        if z == "1":
            return "111000"
        else:
            return "122000"

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

# Finds the gradient of the least-squares regression line corresponding
# to a list of ordered pairs:
def regress(pairlist):

    cumx = 0.0
    cumy = 0.0
    cumvar = 0.0
    cumcov = 0.0

    for x,y in pairlist:

        cumx += x
        cumy += y

    cumx = cumx / len(pairlist)
    cumy = cumy / len(pairlist)

    for x,y in pairlist:

        cumvar += (x - cumx)*(x - cumx)
        cumcov += (x - cumx)*(y - cumy)

    return (cumcov / cumvar)

# Analyses a pattern whose average population follows a power-law:
def powerlyse(stepsize, numsteps, ruletype):
#ALGO REF!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if ruletype:
        g.setalgo("HashLife")
    else:
        g.setalgo("RuleLoader")
    g.setbase(2)
    g.setstep(stepsize)

    poplist = [0]*numsteps

    poplist[0] = int(g.getpop())

    pointlist = []

    for i in xrange(1, numsteps, 1):

        g.step()
        poplist[i] = int(g.getpop()) + poplist[i-1]

        if (i % 50 == 0):

            g.fit()
            g.update()

        if (i > numsteps/2):

            pointlist.append((math.log(i),math.log(poplist[i]+1.0)))

    power = regress(pointlist)

    if (power < 1.10):
        return "unidentified"
    elif (power < 1.65):
        return "z_REPLICATOR"
    elif (power < 2.05):
        return "z_LINEAR"
    elif (power < 2.8):
        return "z_EXPLOSIVE"
    else:
        return "z_QUADRATIC"

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
def linearlyse(maxperiod, ruletype):

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

# If the universe consists only of disjoint *WSSes, this will return
# a triple (l, w, h) giving the quantities of each *WSS. Otherwise,
# this function will return (-1, -1, -1).
#
# This should only be used to separate period-4 moving objects which
# may contain multiple *WSSes.
def countxwsses():

    degcount = degreecount2()
    if (degreecount2() != degcount):
        # Degree counts are not period-2:
        return (-1, -1, -1)

    # Degree counts of each standard spaceship:
    hwssa = [1,4,6,2,0,0,0,0,0,0,0,0,4,4,6,1,2,1]
    mwssa = [2,2,5,2,0,0,0,0,0,0,0,0,4,4,4,1,2,0]
    lwssa = [1,2,4,2,0,0,0,0,0,0,0,0,4,4,2,2,0,0]
    hwssb = [0,0,0,4,4,6,1,2,1,1,4,6,2,0,0,0,0,0]
    mwssb = [0,0,0,4,4,4,1,2,0,2,2,5,2,0,0,0,0,0]
    lwssb = [0,0,0,4,4,2,2,0,0,1,2,4,2,0,0,0,0,0]

    # Calculate the number of standard spaceships in each phase:
    hacount = degcount[17]
    macount = degcount[16]/2 - hacount
    lacount = (degcount[15] - hacount - macount)/2
    hbcount = degcount[8]
    mbcount = degcount[7]/2 - hbcount
    lbcount = (degcount[6] - hbcount - mbcount)/2

    # Determine the expected degcount given the calculated quantities:
    pcounts = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    pcounts = map(lambda x, y: x + y, pcounts, map(lambda x: hacount*x, hwssa))
    pcounts = map(lambda x, y: x + y, pcounts, map(lambda x: macount*x, mwssa))
    pcounts = map(lambda x, y: x + y, pcounts, map(lambda x: lacount*x, lwssa))
    pcounts = map(lambda x, y: x + y, pcounts, map(lambda x: hbcount*x, hwssb))
    pcounts = map(lambda x, y: x + y, pcounts, map(lambda x: mbcount*x, mwssb))
    pcounts = map(lambda x, y: x + y, pcounts, map(lambda x: lbcount*x, lwssb))

    # Compare the observed and expected degcounts (to eliminate nonstandard spaceships):
    if (pcounts != degcount):
        # Expected and observed values do not match:
        return (-1, -1, -1)

    # Return the combined numbers of *WSSes:
    return(lacount + lbcount, macount + mbcount, hacount + hbcount)


# Generates the helper rules for apgsearch, given a base outer-totalistic rule.
#MAIN MODIFICATION NECCESSARY!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
class RuleGenerator:

    # Unless otherwise specified, assume standard B3/S23 rule:
    bee = [False, False, False, True, False, False, False, False, False]
    ess = [False, False, True, True, False, False, False, False, False]
    alphanumeric = "B3S23"
    slashed = "B3/S23"
    ruletype = True

    # Save all helper rules:
    def saveAllRules(self):
        
        self.saveClassifyObjects()
        self.saveCoalesceObjects()
        self.saveExpungeObjects()
        self.saveExpungeGliders()
        self.saveIdentifyGliders()
        self.saveHandlePlumes()
        self.savePercolateInfection()
        self.saveEradicateInfection()
        self.saveContagiousLife()
        self.savePropagateClassifications()
        if self.t:
            self.saveIdentifyTs()
            self.saveAdvanceTs()
            self.saveAssistTs()
            self.saveExpungeTs()
        
    def testPattern(self, clist, period, moving):
        g.new("Test pattern")
        g.setalgo("QuickLife")
        g.setrule(self.slashed)
        g.putcells(clist)
        r = g.getrect()
        h = g.hash(r)
        g.run(period)
        f = g.getrect()
        if int(g.getpop()) == 0:
            return False
        return h == g.hash(f) and (moving and f != r) or (not moving and f == r)
    
    #To use this standalone, just copy this into a separate file and add the lines
    '''import golly as g
class Foo:
    slashed = g.getstring("Enter name of rule to test", "Life")'''
    #before it and the lines
    '''foo = Foo()
g.show(foo.testHensel())'''
    #after it, and run it in Golly.
    def testHensel(self):
        #Dict containing all possible transitions:
        dict = { 
                 "0"  : "0,0,0,0,0,0,0,0",
                 "1e" : "1,0,0,0,0,0,0,0",  #   N 
                 "1c" : "0,1,0,0,0,0,0,0",  #   NE
                 "2a" : "1,1,0,0,0,0,0,0",  #   N,  NE
                 "2e" : "1,0,1,0,0,0,0,0",  #   N,  E 
                 "2k" : "1,0,0,1,0,0,0,0",  #   N,  SE
                 "2i" : "1,0,0,0,1,0,0,0",  #   N,  S 
                 "2c" : "0,1,0,1,0,0,0,0",  #   NE, SE
                 "2n" : "0,1,0,0,0,1,0,0",  #   NE, SW
                 "3a" : "1,1,1,0,0,0,0,0",  #   N,  NE, E
                 "3n" : "1,1,0,1,0,0,0,0",  #   N,  NE, SE 
                 "3r" : "1,1,0,0,1,0,0,0",  #   N,  NE, S      
                 "3q" : "1,1,0,0,0,1,0,0",  #   N,  NE, SW
                 "3j" : "1,1,0,0,0,0,1,0",  #   N,  NE, W
                 "3i" : "1,1,0,0,0,0,0,1",  #   N,  NE, NW
                 "3e" : "1,0,1,0,1,0,0,0",  #   N,  E,  S
                 "3k" : "1,0,1,0,0,1,0,0",  #   N,  E,  SW
                 "3y" : "1,0,0,1,0,1,0,0",  #   N,  SE, SW     
                 "3c" : "0,1,0,1,0,1,0,0",  #   NE, SE, SW 
                 "4a" : "1,1,1,1,0,0,0,0",  #   N,  NE, E,  SE
                 "4r" : "1,1,1,0,1,0,0,0",  #   N,  NE, E,  S  
                 "4q" : "1,1,1,0,0,1,0,0",  #   N,  NE, E,  SW
                 "4i" : "1,1,0,1,1,0,0,0",  #   N,  NE, SE, S
                 "4y" : "1,1,0,1,0,1,0,0",  #   N,  NE, SE, SW
                 "4k" : "1,1,0,1,0,0,1,0",  #   N,  NE, SE, W
                 "4n" : "1,1,0,1,0,0,0,1",  #   N,  NE, SE, NW 
                 "4z" : "1,1,0,0,1,1,0,0",  #   N,  NE, S,  SW
                 "4j" : "1,1,0,0,1,0,1,0",  #   N,  NE, S,  W
                 "4t" : "1,1,0,0,1,0,0,1",  #   N,  NE, S,  NW
                 "4w" : "1,1,0,0,0,1,1,0",  #   N,  NE, SW, W
                 "4e" : "1,0,1,0,1,0,1,0",  #   N,  E,  S,  W
                 "4c" : "0,1,0,1,0,1,0,1",  #   NE, SE, SW, NW
                 "5a" : "0,0,0,1,1,1,1,1",  #   SE, S,  SW, W,  NW
                 "5n" : "0,0,1,0,1,1,1,1",  #   E,  S,  SW, W,  NW
                 "5r" : "0,0,1,1,0,1,1,1",  #   E,  SE, SW, W,  
                 "5q" : "0,0,1,1,1,0,1,1",  #   E,  SE, S,  W,  NW
                 "5j" : "0,0,1,1,1,1,0,1",  #   E,  SE, S,  SW, NW 
                 "5i" : "0,0,1,1,1,1,1,0",  #   E,  SE, S,  SW, W 
                 "5e" : "0,1,0,1,0,1,1,1",  #   NE, SE, SW, W,  NW, 
                 "5k" : "0,1,0,1,1,0,1,1",  #   NE, SE, S,  W,  NW
                 "5y" : "0,1,1,0,1,0,1,1",  #   NE, E,  S,  W, NW 
                 "5c" : "1,0,1,0,1,0,1,1",  #   N,  E,  S,  W,  NW
                 "6a" : "0,0,1,1,1,1,1,1",  #   E,  SE, S,  SW, W,  NW
                 "6e" : "0,1,0,1,1,1,1,1",  #   NE, SE, S,  SW, W,  NW
                 "6k" : "0,1,1,0,1,1,1,1",  #   NE, E,  S,  SW, W,  NW
                 "6i" : "0,1,1,1,0,1,1,1",  #   NE, E,  SE, SW, W,  NW
                 "6c" : "1,0,1,0,1,1,1,1",  #   N,  E,  S,  SW, W,  NW
                 "6n" : "1,0,1,1,1,0,1,1",  #   N,  E,  SE, S,  W,  NW
                 "7e" : "0,1,1,1,1,1,1,1",  #   NE, E,  SE, S,  SW, W,  NW 
                 "7c" : "1,0,1,1,1,1,1,1",  #   N,  E,  SE, S,  SW, W,  NW
                 "8"  : "1,1,1,1,1,1,1,1",
                }
        
        #Represents the encoding in dict:
        neighbors = [(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]
        
        #Will store transitions temporarily:
        d2 = [{},{}]
        
        #Used to help a conversion later:
        lnums = []
        for i in xrange(9):
            lnums.append([j for j in dict if int(j[0]) == i])
        
        #Self-explanatory:
        g.setrule(self.slashed)
        
        #Test each transition in turn:
        for i in xrange(2):
            for j in dict:
                j2 = dict[j].split(",")
                g.new("Testing Hensel notation...")
                for k in xrange(len(j2)):
                    k2 = int(j2[k])
                    g.setcell(neighbors[k][0], neighbors[k][1], k2)
                g.setcell(0, 0, i)
                g.run(1)
                d2[i][j] = int(g.getcell(0, 0)) == 1
        
        #Will become the main table of transitions:
        trans_ = [[],[]]
        
        #Will become the final output string:
        not_ = "B"
        for i in xrange(2):
            #Convert d2 to a more usable form
            for j in xrange(9):
                trans_[i].append({})
                for k in lnums[j]:
                    trans_[i][j][k] = d2[i][k]
                    
            #Make each set of transitions:
            for j in xrange(9):
                
                #Number of present transitions for B/S[[j]]
                sum = 0
                for k in trans_[i][j]:
                    if trans_[i][j][k]:
                        sum += 1
                
                #No transitions present:
                if sum == 0:
                    continue
                
                #All transitions present:
                if sum == len(trans_[i][j]):
                    not_ += str(j)
                    continue
                    
                str_ = str(j) #Substring for current set of transitions
                
                #Minus sign needed if more than half of 
                #current transition set is present.
                minus = (sum >= len(trans_[i][j])/2)
                if minus:
                    str_ += "-"
                
                str2 = "" #Another substring for current transition set
                
                #Write transitions:
                for k in trans_[i][j]:
                    if trans_[i][j][k] != minus:
                        str2 += k[1:]
                
                #Append transitions:
                not_ += str_ + "".join(sorted(str2))
                
            if i == 0:
                not_ += "S"
                
        g.new("Test finished.")
        return not_
        
    # Set outer-totalistic or isotropic non-totalistic rule:
    def setrule(self, rulestring):
        
        mode = 0 #
        s = [False]*9
        b = [False]*9

        if '/' in rulestring:
            for c in rulestring:

                if ((c == 's') | (c == 'S')):
                    mode = 0

                if ((c == 'b') | (c == 'B')):
                    mode = 1

                if (c == '/'):
                    mode = 1 - mode

                if ((ord(c) >= 48) & (ord(c) <= 56)):
                    d = ord(c) - 48
                    if (mode == 0):
                        s[d] = True
                    else:
                        b[d] = True

            prefix = "B"
            suffix = "S"

            for i in xrange(9):
                if (b[i]):
                    prefix += str(i)
                if (s[i]):
                    suffix += str(i)

            self.alphanumeric = prefix + suffix
            self.slashed = prefix + "/" + suffix
            self.hensel = self.alphanumeric
            self.bee = b
            self.ess = s
            self.t = False
            self.g = self.ess[2] & self.ess[3] & (not self.ess[1]) & (not self.ess[4])
            self.g = self.g & (not (self.bee[4] | self.bee[5]))
        else:
            if os.path.exists(g.getdir("app") + "Rules/" + rulestring + ".rule"):
                self.rulepath = g.getdir("app") + "Rules/" + rulestring + ".rule"
            else:
                self.rulepath = g.getdir("rules") + rulestring + ".rule"
            self.alphanumeric = rulestring
            self.slashed = rulestring
            self.hensel = self.testHensel()
            self.ruletype = False
            self.t = self.testPattern([1,0,0,1,1,1,2,1], 5, True)
            self.g = self.testPattern([0,0,1,0,2,0,0,1,1,2], 4, True)
            #Leave bee and ess alone; we don't know what we're dealing with, so default to Life.
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

        block = ""

        for name in namelist:
            block += self.newvar(name, vallist)

        block += "\n"

        return block

    def scoline(self, chara, charb, left, right, amount):     #Second and third parameters not to be confused with Beta Canum Venaticorum and the main victim of a Paris terrorist attack, respectively.

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
n_states:18
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
n_states:18
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
n_states:18
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
    
    def saveIdentifyTs(self):
    
        comments = """
To identify the common spaceship xq4_27, also known as the T.

state 0:  vacuum
state 11:  p3+ on
state 12:  p3+ off
state 13:  T on
state 14:  T off
state 15:  not-T on
state 16:  not-T off
"""
        table = """
n_states:18
neighborhood:Moore
symmetries:rotate4reflect
var a={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17}
var aa=a
var ab=a
var ac=a
var ad=a
var ae=a
var af=a
var ag=a
var o={0,2,12,14}
var oa=o
var ob=o
var oc=o
var od=o
var s={5,6,17}
var sa=s
var sb=s
var sc=s
var n={7,8,9,10,11,15,16}
var xo={2,4,6,14}
var xn={1,3,5,13,17}
var i={11,12}
var io={0,1,2,11,12}
var ioa=io
var b={0,12}
11,11,o,12,11,12,11,12,oa,1
11,11,12,o,oa,io,oc,od,12,1
11,12,11,o,oa,ob,oc,12,12,1
11,12,12,12,12,12,12,12,12,1
11,12,11,o,oa,ob,oc,od,11,1
11,11,o,11,oa,11,io,io,io,1
11,11,11,11,11,12,o,oa,ob,1
11,11,11,o,oa,io,ob,oc,11,1
11,11,11,o,oa,ob,oc,12,12,1
11,11,o,11,oa,11,io,ioa,io,1
11,11,12,11,12,11,12,o,0,1
11,11,11,11,io,ioa,o,oa,ob,1
11,11,11,o,oa,ob,oc,od,12,1
12,11,o,11,oa,11,12,12,12,2
12,11,11,o,oa,ob,oc,11,12,2
12,11,12,12,11,12,11,12,12,2
12,11,12,12,11,i,o,oa,ob,2
12,11,12,12,o,oa,ob,12,12,2
b,11,11,o,io,oa,ioa,ob,11,2
12,11,11,12,o,o,oa,ob,ob,2
12,11,11,11,11,12,o,oa,ob,2
b,11,11,11,o,oa,ob,oc,od,2
1,1,2,1,2,1,2,1,2,15
1,2,1,o,oa,ob,oc,od,1,3
1,1,o,2,1,2,1,2,oa,3
1,1,2,o,oa,io,oc,od,2,3
1,2,1,o,oa,ob,oc,2,2,3
1,2,2,2,2,2,o,oa,ob,3
1,1,o,1,oa,1,io,ioa,io,3
1,1,2,1,2,1,12,2,0,3
1,1,2,1,2,1,2,o,0,3
1,1,1,1,io,ioa,o,oa,ob,3
1,1,1,2,o,oa,ob,2,1,3
1,1,1,o,oa,ob,oc,od,2,3
1,1,1,2,2,1,2,2,1,3
2,1,2,2,1,2,1,2,2,4
2,1,2,2,1,12,12,12,2,12
2,1,12,2,1,2,12,12,12,12
2,1,o,12,a,aa,ab,12,oa,12
2,2,1,2,12,1,o,o,o,12
2,1,o,1,oa,1,2,2,2,4
2,1,1,o,oa,ob,oc,1,2,4
2,1,2,1,2,1,2,2,2,4
2,1,2,2,1,io,o,oa,ob,4
2,1,2,2,o,oa,ob,oc,od,4
2,1,1,o,io,oa,ioa,ob,1,4
2,1,1,2,o,oa,ob,oc,od,4
2,1,1,1,o,oa,ob,oc,od,4
2,1,1,1,1,2,o,oa,ob,4
4,3,3,4,3,4,3,4,3,6
6,3,3,4,3,4,3,4,3,4
4,3,4,3,4,3,4,4,4,6
6,3,4,3,4,3,4,4,4,4
3,3,3,3,3,3,4,3,4,5
5,3,3,3,3,3,4,3,4,3
3,3,4,3,4,3,4,4,4,5
5,3,4,3,4,3,4,4,4,3
3,3,3,4,4,3,4,4,3,5
5,3,3,4,4,3,4,4,3,3
3,5,5,4,12,12,12,4,4,17
3,s,a,aa,ab,ac,ad,ae,af,5
4,s,a,aa,ab,ac,ad,ae,af,6
3,a,s,aa,ab,ac,ad,ae,af,5
4,a,s,aa,ab,ac,ad,ae,af,6
6,12,6,5,5,6,o,oa,ob,12
6,s,sa,sb,a,aa,ab,ac,ad,14
6,s,sa,a,aa,ab,ac,ad,sb,14
5,s,sa,a,aa,ab,ac,ad,sb,13
5,s,sa,sb,a,aa,ac,ac,ad,13
6,13,o,oa,oa,14,13,6,14,12
17,14,14,13,13,14,12,12,12,13
14,17,13,14,o,oa,12,12,12,12
xn,n,a,aa,ab,ac,ad,ae,af,15
xo,n,a,aa,ab,ac,ad,ae,af,16
xn,a,n,aa,ab,ac,ad,ae,af,15
xo,a,n,aa,ab,ac,ad,ae,af,16
1,a,aa,ab,ac,ad,ae,af,ag,15
2,a,aa,ab,ac,ad,ae,af,ag,16
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
17 127    0  127
"""
        self.saverule("APG_IdentifyTs", comments, table, colours)
    
    def saveAdvanceTs(self):
    
        comments = """
To filter out extraneous results from the output of APG_IdentifyTs.

state 0:  vacuum
state 11:  p3+ on
state 12:  p3+ off
state 13:  T on
state 14:  T off
state 15:  not-T on
state 16:  not-T off
"""
        table = """
n_states:18
neighborhood:Moore
symmetries:rotate4reflect
var a={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17}
var aa=a
var ab=a
var ac=a
var ad=a
var ae=a
var af=a
var ag=a
var in={1,3,5,15}
var io={2,4,6,16}
var i={1,2,3,4,5,6,15,16}
var o={0,12,14}
var oa=o
var ob=o
var oc=o
var od=o
var oe=o
var of=o
var og=o
var oo={12,14}
var c={0,12,13,14}
var ca=c
var t={13,14}
in,a,aa,ab,ac,ad,ae,af,ag,11
io,a,aa,ab,ac,ad,ae,af,ag,12
#Birth
o,13,13,13,oa,ob,oc,od,oe,13
o,13,13,oa,ob,13,oc,od,oe,13
o,13,13,oa,ob,oc,od,13,oe,13
o,13,13,oa,ob,oc,od,oe,13,13
o,13,oa,13,ob,13,oc,od,oe,13
o,13,oa,ob,13,oc,13,od,oe,13
#Inert
o,13,13,c,ca,oa,ob,oc,od,o
o,13,oa,c,ob,oc,od,oe,of,o
o,13,13,oa,13,ob,13,oc,13,o
o,oa,13,ob,c,oc,od,oe,of,o
o,13,oa,ob,13,oc,od,oe,of,o
o,13,oa,ob,oc,13,od,oe,of,o
o,13,13,oa,13,13,ob,oc,od,o
o,oa,13,ob,13,oc,13,od,13,o
o,oa,13,ob,oc,od,13,oe,of,o
#Survival
13,13,13,o,oa,ob,oc,od,c,13
13,13,o,13,oa,13,ob,oc,od,13
13,13,13,13,o,oa,ob,oc,od,13
13,c,o,oa,13,ob,13,oc,od,13
#Death
13,13,13,13,13,o,oa,ob,oc,14
13,13,13,13,13,13,o,c,oa,14
13,13,o,oa,ob,c,oc,od,oe,14
13,o,13,oa,ob,oc,od,oe,of,14
13,13,13,o,oa,13,ob,oc,13,14
13,o,oa,ob,oc,od,oe,of,og,14
#Not T
0,o,oa,ob,oc,od,oe,of,og,0
oo,o,oa,ob,oc,od,oe,of,og,12
o,a,aa,ab,ac,ad,ae,af,t,16
o,a,aa,ab,ac,ad,ae,t,af,16
13,a,aa,ab,ac,ad,ae,af,t,15
13,a,aa,ab,ac,ad,ae,t,af,15
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
17 127    0  127
"""
        self.saverule("APG_AdvanceTs", comments, table, colours)

    def saveExpungeTs(self):
    
        comments = """
To filter out extraneous results from the output of APG_IdentifyTs.

state 0:  vacuum
state 11:  p3+ on
state 12:  p3+ off
state 13:  T on
state 14:  T off
state 17:  about to die
"""
        table = """
n_states:18
neighborhood:Moore
symmetries:rotate8reflect
var a={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17}
var aa=a
var ab=a
var ac=a
var ad=a
var ae=a
var af=a
var ag=a
var o={0,12,14}
var oa=o
var ob=o
var oc=o
var od=o
var oe=o
var of=o
var og=o
var t={13,14}
13,o,oa,ob,oc,od,oe,of,og,17
13,13,o,oa,ob,oc,od,oe,of,17
13,13,13,o,oa,ob,oc,od,oe,17
13,13,13,o,oa,ob,oc,od,13,17
13,13,o,13,oa,13,ob,oc,od,17
13,13,13,13,13,13,o,13,oa,17
14,o,oa,ob,oc,od,oe,of,og,12
17,a,aa,ab,ac,ad,ae,af,ag,0
t,17,a,aa,ab,ac,ad,ae,af,17
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
17 127    0  127
"""
        self.saverule("APG_ExpungeTs", comments, table, colours)
        
    def saveAssistTs(self):
    
        comments = """
To help filter out extraneous results from the output of APG_IdentifyTs.

state 0:  vacuum
state 11:  p3+ on
state 12:  p3+ off
state 13:  T on
state 14:  T off
state 15:  not-T on
state 15:  not-T off
"""
        table = """
n_states:18
neighborhood:Moore
symmetries:rotate8reflect
var a={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17}
var aa=a
var ab=a
var ac=a
var ad=a
var ae=a
var af=a
var ag=a
var t={13,14}
var nt={15,16}
13,nt,a,ab,ac,ad,ae,af,ag,15
14,nt,a,ab,ac,ad,ae,af,ag,16
12,t,a,ab,ac,nt,ad,ae,af,16
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
17 127    0  127
"""
        self.saverule("APG_AssistTs", comments, table, colours)

    def saveEradicateInfection(self):

        comments = """
To run after ContagiousLife to disinfect any cells in states 3, 4, 7, and 8.

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
7  255    0  255
8  127    0  127
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
7  255    0  255
8  127    0  127
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
        table = "n_states:18\n"
        table += "neighborhood:Moore\n"
        table += "symmetries:rotate4reflect\n\n"

        table += self.newvars(["a","b","c","d","e","f","g","h","i"], range(0, 17, 1))

        table += """
# Monomino
6,0,0,0,0,0,0,0,0,0

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
        
        if self.ruletype: #Outer-totalistic
            table += "symmetries:permute\n\n"
    
            table += self.newvars(["a","b","c","d","e","f","g","h","i"], [0, 1, 2])
            table += self.newvars(["da","db","dc","dd","de","df","dg","dh","di"], [0, 2])
            table += self.newvars(["la","lb","lc","ld","le","lf","lg","lh","li"], [1])
    
            minperc = 10
    
            for i in xrange(9):
                if (self.bee[i]):
                    if (minperc == 10):
                        minperc = i
                    table += self.scoline("l","d",0,1,i)
                    table += self.scoline("l","d",2,1,i)
                if (self.ess[i]):
                    table += self.scoline("l","d",1,1,i)
    
            table += "\n# Bridge inductors\n"
    
            for i in xrange(9):
                if (i >= minperc):
                    table += self.scoline("l","d",0,2,i)
    
            table += self.scoline("","",1,2,0)
        else: #Isotropic non-totalistic
            rule1 = open(self.rulepath, "r")
            lines = rule1.read().split("\n")
            lines1 = []
            for i in lines:
                l1 = i.split("\r")
                for j in l1:
                    lines1.append(j)
            rule1.close()
            for q in xrange(len(lines1)-1):
                if lines1[q].startswith("@TABLE"):
                    lines1 = lines1[q:]
                    break
            vars = []
            for q in xrange(len(lines1)-1): #Copy symmetries and vars
                i = lines1[q]
                if i[:2] == "sy" or i[:1] == "sy":
                    table += i + "\n\n"
                if i[:2] == "va" or i[:1] == "va":
                    '''table += self.newvar(i[4:5].replace("=", ""), [0, 1, 2])
                    vars.append(i[4:5].replace("=", ""))'''
                if i != "":
                    if i[0] == "0" or i[0] == "1":
                        break
            
            alpha = "abcdefghijklmnopqrstuvwxyz"
            vars2 = []
            '''for i in alpha: 
                if not i in [n[0] for n in vars]: #Create new set of vars for OFF cells
                    table += self.newvars([i + j for j in alpha[:9]], [0, 2])
                    vars2 = [i + j for j in alpha[:9]]
                    break
                    
            for i in alpha: 
                if not i in [n[0] for n in vars] and not i in [n[0] for n in vars2]:
                    for j in xrange(5-len(vars)):
                        table += self.newvar(i + alpha[j], [0, 1, 2])
                        vars.append(i + alpha[j])
                    break'''
            vars = ["aa", "ab", "ac", "ad", "ae", "af", "ag", "ah"]
            vars2 = ["ba", "bb", "bc", "bd", "be", "bf", "bg", "bh"]
            table += self.newvars(vars, [0, 1, 2])
            table += self.newvars(vars2, [0, 2])
            
            for i in lines1:
                q = i.split("#")[0].replace(" ", "").split(",")
                if len(q[0]) > 1:
                    if len(q) == 1 and (q[0][1] == "0" or q[0][1] == "1"):
                        q = list(q[0])
                if len(q) > 1 and not i.startswith("var"):
                    vn = 0
                    vn2 = 0
                    for j in q[:-1]:
                        if j == "0":
                            table += vars2[vn2]
                            vn2 += 1
                        elif j == "1":
                            table += "1"
                        elif j != "#":
                            table += vars[vn]
                            vn += 1
                        table += ","
                    table += str(2-int(q[len(q)-1]))
                    table += "\n"
                
            for i in xrange(256): #Get all B3+ rules
                ncells = 0
                for j in xrange(8):
                    if (i & 2**j) > 0:
                        ncells += 1
                if ncells == 3:
                    q = "0,"
                    vn = 0
                    for j in xrange(8):
                        if i & 2**j > 0:
                            q += str((i & 2**j)/2**j) + ","
                        else:
                            q += vars[vn] + ","
                            vn += 1
                    q += "2\n"
                    table += q
                
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
        table = "n_states:18\n"
        table += "neighborhood:Moore\n"
        if self.ruletype: #Outer-totalistic
            table += "symmetries:permute\n\n"
    
            table += self.newvars(["a","b","c","d","e","f","g","h","i"], range(0, 17, 1))
            table += self.newvars(["la","lb","lc","ld","le","lf","lg","lh","li"], range(1, 17, 2))
            table += self.newvars(["da","db","dc","dd","de","df","dg","dh","di"], range(0, 17, 2))
            table += self.newvars(["pa","pb","pc","pd","pe","pf","pg","ph","pi"], [0, 3, 4])
            table += self.newvars(["qa","qb","qc","qd","qe","qf","qg","qh","qi"], [5, 6])
    #Serious modifications necessary:
            for i in xrange(9):
                if (self.bee[i]):
                    table += self.scoline("l","d",2,6,i)
                    table += self.scoline("q","p",3,9,i)
                    table += self.scoline("q","p",4,12,i)
                if (self.ess[i]):
                    table += self.scoline("l","d",1,5,i)
                    table += self.scoline("q","p",5,7,i)
                    table += self.scoline("q","p",6,12,i)
            table += self.scoline("","",2,4,0)
            table += self.scoline("","",1,3,0)
            table += self.scoline("","",5,11,0)
            table += self.scoline("","",3,11,0)
            table += self.scoline("","",4,8,0)
            table += self.scoline("","",6,10,0)
        
        else: #Isotropic non-totalistic
            rule1 = open(self.rulepath, "r")
            lines = rule1.read().split("\n")
            lines1 = []
            for i in lines:
                l1 = i.split("\r")
                for j in l1:
                    lines1.append(j)
            rule1.close()
            for q in xrange(len(lines1)-1):
                if lines1[q].startswith("@TABLE"):
                    lines1 = lines1[q:]
                    break
                if lines1[0].startswith("@TREE"):
                    g.warn("apgsearch v.0.54+0.1i does not support rule trees")
            vars = []
            for q in xrange(len(lines1)-1): #Copy symmetries and vars
                i = lines1[q]
                if i[:2] == "sy" or i[:1] == "sy":
                    table += i + "\n\n"
                if i[:2] == "va" or i[:1] == "va":
                    '''table += self.newvar(i[4:5].replace("=", ""), [0, 1, 2, 3, 4, 5, 6])
                    vars.append(i[4:5].replace("=", ""))'''
                if i != "":
                    if i[0] == "0" or i[0] == "1":
                        break
            alpha = "abcdefghijklmnopqrstuvwxyz"
            ovars = []
            '''for i in alpha: 
                if not i in [n[0] for n in vars]: #Create new set of vars for ON cells
                    table += self.newvars([i + j for j in alpha[:9]], [1, 5, 6])
                    ovars = [i + j for j in alpha[:9]]
                    break'''
            
            dvars = []
            
            vars = ["aa", "ab", "ac", "ad", "ae", "af", "ag", "ah"]
            dvars = ["ba", "bb", "bc", "bd", "be", "bf", "bg", "bh"]
            ovars = ["ca", "cb", "cc", "cd", "ce", "cf", "cg", "ch"]
            table += self.newvars(vars, xrange(7))
            table += self.newvars(dvars, [0, 2, 3, 4])
            table += self.newvars(ovars, [1, 5, 6])
            '''for i in alpha: 
                if not i in [n[0] for n in vars] and not i in [n[0] for n in ovars]: #Create new set of vars for OFF cells
                    table += self.newvars([i + j for j in alpha[:9]], [0, 2, 3, 4])
                    dvars = [i + j for j in alpha[:9]]
                    break
                    
            for i in alpha: 
                if not i in [n[0] for n in vars] and not i in [n[0] for n in ovars] and not i in [n[0] for n in dvars]:
                    for j in xrange(8-len(vars)):
                        table += self.newvar(i + alpha[j], [0, 1, 2, 3, 4, 5, 6])
                        vars.append(i + alpha[j])
                    break'''
            
            for i in lines1:
                q = i.split("#")[0].replace(" ", "").split(",")
                if len(q[0]) > 1:
                    if len(q) == 1 and (q[0][1] == "0" or q[0][1] == "1"):
                        q = list(q[0])
                if len(q) > 1:
                    vn = 0
                    ovn = 0
                    dvn = 0
                    if q[0] == "0" or q[0] == "1":
                        if q[0] == "0":
                            table += "2"
                        elif q[0] == "1":
                            table += "1"
                        elif q[0] != "#":
                            table += vars[vn]
                            vn += 1
                        table += ","
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += "1"
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        table += str(4-int(q[0])+2*int(q[len(q)-1]))
                        table += "\n"
                    elif not i.startswith("var"): #Line starts with a variable.
                        table += vars[vn] + ","
                        vn += 1
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += "1"
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        table += str(4+2*int(q[len(q)-1]))
                        table += "\n1,"
                        vn = 0
                        for j in q[1:-1]:
                            if j == "0":
                                table += "2"
                            elif j == "1":
                                table += "1"
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        table += str(3+2*int(q[len(q)-1]))
                        table += "\n"
            table += "2," + ",".join(vars[:8]) + ",4\n"
            table += "1," + ",".join(vars[:8]) + ",5\n"
                    
            for i in lines1:
                q = i.split("#")[0].replace(" ", "").split(",")
                if len(q[0]) > 1:
                    if len(q) == 1 and (q[0][1] == "0" or q[0][1] == "1"):
                        q = list(q[0])
                if len(q) > 1:
                    vn = 0
                    ovn = 0
                    dvn = 0
                    if q[0] == "0" or q[0] == "1":
                        table += str(4+2*int(q[0])) + ","
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += ovars[ovn]
                                ovn += 1
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[0] == "0" and q[len(q)-1] == "0":
                            table += "8"
                        if q[0] == "1" and q[len(q)-1] == "0":
                            table += "10"
                        if q[0] == "0" and q[len(q)-1] == "1":
                            table += "12"
                        if q[0] == "1" and q[len(q)-1] == "1":
                            table += "12"
                        table += "\n"
                    elif not i.startswith("var"): #Line starts with a variable.
                        table += "5,"
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += ovars[ovn]
                                ovn += 1
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[len(q)-1] == "0":
                            table += "7"
                        if q[len(q)-1] == "1":
                            table += "11"
                        table += "\n3,"
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += ovars[ovn]
                                ovn += 1
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[len(q)-1] == "0":
                            table += "9"
                        if q[len(q)-1] == "1":
                            table += "11"
                        table += "\n"
                        
            for i in lines1:
                q = i.split("#")[0].replace(" ", "").split(",")
                if len(q[0]) > 1:
                    if len(q) == 1 and (q[0][1] == "0" or q[0][1] == "1"):
                        q = list(q[0])
                if len(q) > 1:
                    vn = 0
                    ovn = 0
                    dvn = 0
                    if q[0] == "0" or q[0] == "1":
                        table += str(3+2*int(q[0])) + ","
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += ovars[ovn]
                                ovn += 1
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[0] == "0" and q[len(q)-1] == "0":
                            table += "11"
                        if q[0] == "1" and q[len(q)-1] == "0":
                            table += "11"
                        if q[0] == "0" and q[len(q)-1] == "1":
                            table += "9"
                        if q[0] == "1" and q[len(q)-1] == "1":
                            table += "7"
                        table += "\n"
                    elif not i.startswith("var"): #Line starts with a variable.
                        table += "6,"
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += ovars[ovn]
                                ovn += 1
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[len(q)-1] == "0":
                            table += "12"
                        if q[len(q)-1] == "1":
                            table += "10"
                        table += "\n4,"
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += ovars[ovn]
                                ovn += 1
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[len(q)-1] == "0":
                            table += "8"
                        if q[len(q)-1] == "1":
                            table += "12"
                        table += "\n"
            table += "4," + ",".join(vars[:8]) + ",8\n"
            table += "3," + ",".join(vars[:8]) + ",11\n"
            table += "6," + ",".join(vars[:8]) + ",12\n"
            table += "5," + ",".join(vars[:8]) + ",7\n"
                        
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

    def savePropagateClassifications(self):
        
        comments = """This propagates the result of running ClassifyObjects for two generations.
"""
        
        table = "n_states:18\n"
        table += "neighborhood:Moore\n"
        table += "symmetries:permute\n\n"
    
        table += self.newvars(["a","b","c","d","e","f","g","h","i"], range(0, 17, 1))
        
        table += """
7,11,b,c,d,e,f,g,h,11
7,12,b,c,d,e,f,g,h,11
7,9,b,c,d,e,f,g,h,9
7,10,b,c,d,e,f,g,h,9
8,11,b,c,d,e,f,g,h,12
8,12,b,c,d,e,f,g,h,12
8,9,b,c,d,e,f,g,h,10
8,10,b,c,d,e,f,g,h,10

7,13,b,c,d,e,f,g,h,11
7,14,b,c,d,e,f,g,h,11
8,13,b,c,d,e,f,g,h,14
8,14,b,c,d,e,f,g,h,14
9,13,b,c,d,e,f,g,h,11
9,14,b,c,d,e,f,g,h,11
10,13,b,c,d,e,f,g,h,14
10,14,b,c,d,e,f,g,h,14

9,11,b,c,d,e,f,g,h,11
9,12,b,c,d,e,f,g,h,11
10,11,b,c,d,e,f,g,h,12
10,12,b,c,d,e,f,g,h,12

13,11,b,c,d,e,f,g,h,11
13,12,b,c,d,e,f,g,h,11
14,11,b,c,d,e,f,g,h,12
14,12,b,c,d,e,f,g,h,12
13,9,b,c,d,e,f,g,h,11
14,9,b,c,d,e,f,g,h,12
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

        self.saverule("APG_PropagateClassification", comments, table, colours)
        #foo = "" + 2
    def saveContagiousLife(self):

        comments = """
A variant of HistoricalLife used for detecting dependencies between
islands.

state 0:  vacuum
state 1:  ON
state 2:  OFF
"""
        table = "n_states:7\n"
        table += "neighborhood:Moore\n"
        
        if self.ruletype:
            table += "symmetries:permute\n\n"

            table += self.newvars(["a","b","c","d","e","f","g","h","i"], range(0, 7, 1))
            table += self.newvars(["la","lb","lc","ld","le","lf","lg","lh","li"], range(1, 7, 2))
            table += self.newvars(["da","db","dc","dd","de","df","dg","dh","di"], range(0, 7, 2))
            table += self.newvar("p",[3, 4])
            table += self.newvars(["ta","tb","tc","td","te","tf","tg","th","ti"], [3])
            table += self.newvars(["qa","qb","qc","qd","qe","qf","qg","qh","qi"], [0, 1, 2, 4, 5, 6])

            for i in xrange(9):
                if (self.bee[i]):
                    table += self.scoline("l","d",4,3,i)
                    table += self.scoline("l","d",2,1,i)
                    table += self.scoline("l","d",0,1,i)
                    table += self.scoline("l","d",6,5,i)
                    table += self.scoline("t","q",0,4,i)
                if (self.ess[i]):
                    table += self.scoline("l","d",3,3,i)
                    table += self.scoline("l","d",5,5,i)
                    table += self.scoline("l","d",1,1,i)

            table += "# Default behaviour (death):\n"
            table += self.scoline("","",1,2,0)
            table += self.scoline("","",5,6,0)
            table += self.scoline("","",3,4,0)
        else:
            rule1 = open(self.rulepath, "r")
            lines = rule1.read().split("\n")
            lines1 = []
            for i in lines:
                l1 = i.split("\r")
                for j in l1:
                    lines1.append(j)
            rule1.close()
            for q in xrange(len(lines1)-1):
                if lines1[q].startswith("@TABLE"):
                    lines1 = lines1[q:]
                    break
            vars = []
            for q in xrange(len(lines1)-1): #Copy symmetries and vars
                i = lines1[q]
                if i[:2] == "sy" or i[:1] == "sy":
                    table += i + "\n\n"
                if i[:2] == "va" or i[:1] == "va":
                    '''table += self.newvar(i[4:5].replace("=", ""), [0, 1, 2, 3, 4, 5, 6])
                    vars.append(i[4:5].replace("=", ""))'''
                if i != "":
                    if i[0] == "0" or i[0] == "1":
                        break
            alpha = "abcdefghijklmnopqrstuvwxyz"
            ovars = []
            '''for i in alpha: 
                if not i in [n[0] for n in vars]: #Create new set of vars for ON cells
                    table += self.newvars([i + j for j in alpha[:9]], [1, 3, 5])
                    ovars = [i + j for j in alpha[:9]]
                    break'''
            dvars = []
            '''for i in alpha: 
                if not i in [n[0] for n in vars] and not i in [n[0] for n in ovars]: #Create new set of vars for OFF cells
                    table += self.newvars([i + j for j in alpha[:9]], [0, 2, 4, 6])
                    dvars = [i + j for j in alpha[:9]]
                    break
                    
            for i in alpha: 
                if not i in [n[0] for n in vars] and not i in [n[0] for n in ovars] and not i in [n[0] for n in dvars]:
                    for j in xrange(8-len(vars)):
                        table += self.newvar(i + alpha[j], [0, 1, 2, 3, 4, 5, 6])
                        vars.append(i + alpha[j])
                    break'''
            
            qvars = []
            '''for i in alpha:
                if not i in [n[0] for n in vars] and not i in [n[0] for n in ovars] and not i in [n[0] for n in dvars]:
                    table += self.newvars([i + j for j in alpha[:9]], [0, 1, 2, 4, 5, 6])
                    qvars = [i + j for j in alpha[:9]]
                    break'''
                    
            vars = ["aa", "ab", "ac", "ad", "ae", "af", "ag", "ah"]
            dvars = ["ba", "bb", "bc", "bd", "be", "bf", "bg", "bh"]
            ovars = ["ca", "cb", "cc", "cd", "ce", "cf", "cg", "ch"]
            qvars = ["da", "db", "dc", "dd", "de", "df", "dg", "dh"]
            table += self.newvars(vars, xrange(7))
            table += self.newvars(dvars, [0, 2, 4, 6])
            table += self.newvars(ovars, [1, 3, 5])
            table += self.newvars(qvars, [0, 1, 2, 4, 5, 6])
            
            for i in lines1:
                q = i.split("#")[0].replace(" ", "").split(",")
                if len(q[0]) > 1:
                    if len(q) == 1 and (q[0][1] == "0" or q[0][1] == "1"):
                        q = list(q[0])
                if len(q) > 1 and not i.startswith("var"):
                    vn = 0
                    ovn = 0
                    dvn = 0
                    qvn = 0
                    table += str(2-int(q[0])) + ","
                    for j in q[1:-1]:
                        if j == "0":
                            table += dvars[dvn]
                            dvn += 1
                        elif j == "1":
                            table += ovars[ovn]
                            ovn += 1
                        elif j != "#":
                            table += vars[vn]
                            vn += 1
                        table += ","
                    if q[len(q)-1] == "0":
                        table += "2"
                    if q[len(q)-1] == "1":
                        table += "1"
                    table += "\n"
                    vn = 0
                    ovn = 0
                    dvn = 0
                    qvn = 0
                    table += str(4-int(q[0])) + ","
                    for j in q[1:-1]:
                        if j == "0":
                            table += dvars[dvn]
                            dvn += 1
                        elif j == "1":
                            table += ovars[ovn]
                            ovn += 1
                        elif j != "#":
                            table += vars[vn]
                            vn += 1
                        table += ","
                    if q[len(q)-1] == "0":
                        table += "4"
                    if q[len(q)-1] == "1":
                        table += "3"
                    table += "\n"
                    vn = 0
                    ovn = 0
                    dvn = 0
                    qvn = 0
                    table += str(6-int(q[0])) + ","
                    for j in q[1:-1]:
                        if j == "0":
                            table += dvars[dvn]
                            dvn += 1
                        elif j == "1":
                            table += ovars[ovn]
                            ovn += 1
                        elif j != "#":
                            table += vars[vn]
                            vn += 1
                        table += ","
                    if q[len(q)-1] == "0":
                        table += "6"
                    if q[len(q)-1] == "1":
                        table += "5"
                    table += "\n"
                    
            for i in lines1:
                q = i.split("#")[0].replace(" ", "").split(",")
                if len(q[0]) > 1:
                    if len(q) == 1 and (q[0][1] == "0" or q[0][1] == "1"):
                        q = list(q[0])
                if len(q) > 1:
                    vn = 0
                    ovn = 0
                    dvn = 0
                    qvn = 0
                    if q[0] == "0":
                        table += "0,"
                        for j in q[1:-1]:
                            if j == "0":
                                table += dvars[dvn]
                                dvn += 1
                            elif j == "1":
                                table += ovars[ovn]
                                ovn += 1
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[len(q)-1] == "1":
                            table += "1"
                        else:
                            table += "0"
                        table += "\n"
                        
            for i in lines1:
                q = i.split("#")[0].replace(" ", "").split(",")
                if len(q[0]) > 1:
                    if len(q) == 1 and (q[0][1] == "0" or q[0][1] == "1"):
                        q = list(q[0])
                if len(q) > 1:
                    vn = 0
                    ovn = 0
                    dvn = 0
                    qvn = 0
                    if q[0] == "0":
                        table += "0,"
                        for j in q[1:-1]:
                            if j == "0":
                                table += qvars[qvn]
                                qvn += 1
                            elif j == "1":
                                table += "3"
                            elif j != "#":
                                table += vars[vn]
                                vn += 1
                            table += ","
                        if q[len(q)-1] == "1":
                            table += "4"
                        else:
                            table += "0"
                        table += "\n"

        colours = """
0    0    0    0
1    0    0  255
2    0    0  127
3  255    0    0
4  127    0    0
5    0  255    0
6    0  127    0
7  255    0  255
8  127    0  127
"""
        self.saverule("APG_ContagiousLife_"+self.alphanumeric, comments, table, colours)


class Soup:

    # The rule generator:
    rg = RuleGenerator()

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
    # into constituent parts. This is initialised with the unique minimal
    # pseudo-still-life (two blocks on lock) that cannot be automatically
    # separated by the routine pseudo_bangbang(). Any larger objects are
    # ambiguous, such as this one:
    #
    #     *
    #    * * **
    #     ** **
    #
    #    * *** *
    #    ** * **
    #
    # Is it a (block on (lock on boat)) or ((block on lock) on boat)?
    # Ahh, the joys of non-associativity.
    #
    # See http://paradise.caltech.edu/~cook/Workshop/CAs/2DOutTot/Life/StillLife/StillLifeTheory.html
    pseudo = False
    #If that becomes true by the time searching starts, this will become empty to start.
    decompositions = {"xs18_3pq3qp3": ["xs14_3123qp3", "xs4_33"],}

    # A dict of objects in the form {"identifier": ("common name", points)}
    #
    # As a rough heuristic, an object is worth 15 + log2(n) points if it
    # is n times rarer than the pentadecathlon.
    #
    # Still-lifes are limited to 10 points.
    # p2 oscillators are limited to 20 points.
    # p3 and p4 oscillators are limited to 30 points.
    commonnames = {"xp2_7": ("blinker", 0),
                   "xp2_7e": ("toad", 0),
                   "xp2_318c": ("beacon", 0),
                   "xp2_xrhewehrz253y4352": ("spark coil on distant-boats", 10),
                   "xp2_o8031u0u1308ozol555o0o555lozx6430346": ("[4-fold diags]", 10),
                   "xp2_rhewehr": ("spark coil", 15),
                   "xp2_c8b8acz31d153" :("symmetric griddles", 15),
                   "xp2_2a54": ("clock", 16),
                   "xp2_31ago": ("bipole", 17),
                   "xp2_0g0k053z32": ("quadpole", 18),
                   "xp2_g8gid1e8z1226": ("great on-off", 19),
                   "xp2_jlg4glj": ("[2-fold odd] pole variant", 20),
                   "xp2_318c0f9": ("cis-beacon and table", 20),
                   "xp2_wbq23z32": ("trans-beacon and table", 20),
                   "xp2_31egge13": ("test tubebaby", 20),
                   "xp2_31ago0ui": ("cis-bipole and table", 20),
                   "xp2_318c0fho": ("cis-beacon-down and long hook", 20),
                   "xp2_318c0f96": ("cis-beacon and cap", 20),
                   "xp2_3hu0og26": ("cis-beacon-up and long hook", 20),
                   "xp2_jlg44glj": ("[2-fold even] pole variant", 20),
                   "xp2_wbq2sgz32": ("beacon and two tails", 20),
                   "xp2_g0k053z11": ("tripole", 20),
                   "xp2_g45h1sz03": ("fox", 20),
                   "xp2_33gv1og26": ("Z_and_cis-beacon_and_block", 20),
                   "xp2_4alhewehr": ("030c029200f50292030c", 20),
                   "xp2_31egge1da": ("01860149007a004b0030", 20),
                   "xp2_253gv1og26": ("?-Z-and_beacon_and_boat", 20),
                   "xp2_xoga13z253": ("bipole on boat", 20),
                   "xp2_xoga13z653": ("ship on bipole", 20),
                   "xp2_4k1u1k4zx1": ("by flops", 20),
                   "xp2_c8b8aczw33": ("griddle and block", 20),
                   "xp2_w8o0uh3z32": ("trans-beacon-down and long hook", 20),
                   "xp2_mlhewehrz1": ("01860149007b014801870001", 20),
                   "xp2_4aarhewehr": ("spark_coil siamese hat", 20),
                   "xp2_318czw3553": ("trans-beacon and cap", 20),
                   "xp2_c813z31178c": ("?-eater_siamese_table and ?-beacon", 20),
                   "xp2_gbhewehrz11": ("0186014a0078014a01850003", 20),
                   "xp2_25acz31d153": ("griddle and long_boat", 20),
                   "xp2_wgbq2sgz642": ("bipole and 2_tails", 20),
                   "xp2_gbhewehrz01": ("?21?004", 20),
                   "xp2_j1u062goz11": ("cis-beacon and dock", 20),
                   "xp2_c88b9iczw32": ("001800280041005f0030000c000c", 20),
                   "xp2_318cz311dic": ("beehive_with_long_leg and cis-beacon", 20),
                   "xp2_35acz31d153": ("griddle and long_ship", 20),
                   "xp2_c8b8acz3553": ("griddle and cap", 20),
                   "xp2_318cz315b8o": ("0318031000d400da00020003", 20),
                   "xp2_c813z311dio": ("0300024001a30023002c006c", 20),
                   "xp2_c813z311dic": ("[[cis-beacon-up and beehive_fuse_longhook]]", 20),
                   "xp2_318cz3115a4": ("tub_with_long_leg and cis-beacon", 20),
                   "xp2_4k1v0f9zw11": ("griddle and table", 20),
                   "xp2_ca9baiczw32": ("1 beacon", 20),
                   "xp2_318cz311da4": ("cis-boat_with_long_leg and ?-beacon", 20),
                   "xp2_c813z3115a4": ("tub_with_long_leg and ?-beacon", 20),
                   "xp2_8e1t2gozw23": ("21P2", 20),
                   "xp2_31egge132ac": ("?-test_tubebaby siamese eater", 20),
                   "xp2_c813z311da4": ("cis-boat_with_long_leg and ?-beacon", 20),
                   "xp2_03lk46z6401": ("trans-beacon-up and long hook", 20),
                   "xp2_gk2t2sgzw23": ("00180028000b006a000a00140008", 20),
                   "xp2_rb88czx318c": ("?19?036", 20),
                   "xp2_c8b8acz0253": ("griddle and boat", 20),
                   "xp2_rb88brz0103": ("griddle and blocks", 20),
                   "xp2_c813z319lic": ("cis-loaf_with_long_leg and ?-beacon", 20),
                   "xp2_caabaiczw32": ("18P2.471", 20),
                   "xp2_wg0k053z642": ("pentapole", 20),
                   "xp2_35453z255dic": ("0308029400f4029603090006", 20),
                   "xp2_xg8o652zca02": ("tripole on boat", 20),
                   "xp2_0mlhewehrz32": ("030c029200f60290030e00010003", 20),
                   "xp2_03544oz4a511": ("odd test tubebaby", 20),
                   "xp2_0318cz69d596": ("00c0012c00ac01a3012300c0", 20),
                   "xp2_03544ozca511": ("trans-boat test tubebaby", 20),
                   "xp2_318cz39d1d96": ("018c0189006b0068000b00090006", 20),
                   "xp2_0318cz255d96": ("racetrack and ?-beacon", 20),
                   "xp2_03544ozcid11": ("beehive test tubebaby", 20),
                   "xp2_og2t1egozx32": ("00180024003400d500d300100018", 20),
                   "xp2_318czw3115a4": ("tub_with_long_leg and ?-beacon", 20),
                   "xp2_318czw3115ac": ("trans-boat_with_long_leg and trans-beacon", 20),
                   "xp2_04a96z31d153": ("[[loaf on griddle]]", 20),
                   "xp2_03lk453z6401": ("trans-beacon and dock", 20),
                   "xp2_6a88baiczx32": ("24P2", 20),
                   "xp2_069b8b5zc813": ("018001860069006b0008000b0005", 20),
                   "xp2_39u0og26z023": ("long_and_cis-beacon", 20),
                   "xp2_69b8baiczx32": ("22P2", 20),
                   "xp2_c813z311dik8": ("trans-loaf_with_long_leg and ?-beacon", 20),
                   "xp2_c8b8q4oz33x1": ("006c006a0008000b001800240018", 20),
                   "xp2_039c8a6zc813": ("?-hook_siamese_carrier and beacon", 20),
                   "xp2_69e0ehhe0e96": ("04620a950af506960060", 20),
                   "xp2_03544oz4ad11": ("cis-boat test tubebaby", 20),
                   "xp2_69b8b9iczx32": ("26P2", 20),
                   "xp2_ciab8brzw103": ("006c006a0008006b002800240018", 20),
                   "xp2_04aab8ozc813": ("01800184006a006a000b00080018", 20),
                   "xp2_og2t1e8z6221": ("00d800580046003d0001000e0008", 20),
                   "xp2_31agozca22ac": ("cis-bipole and dock", 20),
                   "xp2_318czw31178c": ("?-eater_siamese_table and ?-beacon", 20),
                   "xp2_g318cz1pl552": ("004000ac00ac02a303230030", 20),
                   "xp2_xrhewehrz253": ("boat on spark coil", 20),
                   "xp2_0318cz69d552": ("00c0012301a300ac00ac0040", 20),
                   "xp2_4k1v0ciczw11": ("griddle and beehive", 20),
                   "xp2_06996z31d153": ("griddle and pond", 20),
                   "xp2_318czcid1d96": ("0306030900d600d000160012000c", 20),
                   "xp2_04aab96zc813": ("racetrack and ortho-beacon", 20),
                   "xp2_wo44871z6221": ("eater plug", 20),
                   "xp2_xg8o653zca02": ("tripole on ship", 20),
                   "xp2_ci9b8brzw103": ("006c006a0008006b004800240018", 20),
                   "xp2_318cz311dik8": ("loaf_with_long_leg and cis-beacon-down", 20),
                   "xp2_og2t1acz6221": ("00d800580046003d0001000a000c", 20),
                   "xp2_09v0c813z321": ("23P2", 20),
                   "xp2_4k1u1k4zw121": ("why not", 20),
                   "xp2_rhewe44ewehr": ("long piston", 20),
                   "xp2_31agozwca22ac": ("trans-bipole and dock", 20),
                   "xp2_06a88a52zc813": ("tub_with_long_nine and ?-beacon", 20),
                   "xp2_8kaabaiczw103": ("[[?19?037]]", 20),
                   "xp2_0g04q23z345lo": ("03000100016300d5003400240018", 20),
                   "xp2_0c813z69d1dic": ("0180024001a3002301ac012c00c0", 20),
                   "xp2_0cimgm96zog26": ("0300030c00d200d60010001600090006", 20),
                   "xp2_04aab871zc813": ("anvil and ?-beacon", 20),
                   "xp2_w8o0uh32acz32": ("long_hook_siamese_eater and trans-beacon-down", 20),
                   "xp2_0ggm952z344ko": ("loaf test tubebaby", 20),
                   "xp2_0c813z255d1e8": ("cis-beacon and anvil", 20),
                   "xp2_0c813z65115a4": ("tub_with_long_nine and ?-beacon", 20),
                   "xp2_318c0s26zw311": ("00c000c300350034000400380020", 20),
                   "xp2_xohf0318cz253": ("long_hook_on_boat and cis-beacon-up", 20),
                   "xp2_651u8z318nge2": ("01980298020601fd0041000e0008", 20),
                   "xp2_03lkmzojc0cjo": ("lightbulb_and_cis-hook", 20),
                   "xp2_0318cz65115a4": ("tub_with_long_nine and ?-beacon", 20),
                   "xp2_25a88gz8ka221": ("tubs test tubebaby", 20),
                   "xp2_8ki1688gzx3421": ("4 boats", 20),
                   "xp2_wca9e0eiczc813": ("?-loaf_siamese_table_and_R-bee_and_beacon", 20),
                   "xp2_31a08zy0123cko": ("quadpole on ship", 20),
                   "xp2_356o8gz318nge3": ("031802980186007d0041002e0018", 20),
                   "xp2_0318cz8kid1d96": ("01000283024301ac002c01a0012000c0", 20),
                   "xp2_256o8gzy120ago": ("boat on quadpole", 20),
                   "xp2_ca1n0brz330321": ("fore and back", 20),
                   "xp2_c88b96z330318c": ("worm and cis-beacon_and_block", 20),
                   "xp2_c8b8acz3303552": ("?-griddle and R-bee_and_block", 20),
                   "xp2_0318cz259d1d96": ("?22?047", 20),
                   "xp2_0c8b8acz651156": ("griddle and dock", 20),
                   "xp2_3hu062goz01226": ("?-long_hook_siamese_eater and beacon", 20),
                   "xp2_03lkl3zojc0cjo": ("lightbulb_and_cis-C", 20),
                   "xp2_3p6gmkkozw1046": ("00c000a8002e0041005f0030000c000c", 20),
                   "xp2_62go0u1u066zy21": ("very_long_beehive and ?-beacon and block", 20),
                   "xp2_4a960u2kgzx6952": ("004000ac012a00c8000b0018002400280010", 20),
                   "xp2_c813z35t1eozx11": ("030005c0042303a300ac006c", 20),
                   "xp2_6t1ege11egozw11": ("031804a406bc02a502430180", 20),
                   "xp2_xrhewehrz653y4356": ("spark coil on distant-ships", 20),
                   "xp2_4a4owo4a96zx1221": ("loaf tub test tubebaby", 20),
                   "xp2_wgj1u0og26z25421": ("20P2", 20),
                   "xp2_318c0s48gzw359611": ("R-loaf_at_R-loaf and beacon", 20),
                   "xp2_g8o6hewehrz121011": ("0610052801e80526061500350002", 20),
                   "xp2_bh2882hbzd841148d": ("[4-fold] pole variant", 20),
                   "xp2_318czw35t1eozy111": ("0600060001b001a8002e0021001d0006", 20),
                   "xp2_3p606p3z0o555oz6430346": ("lightbulbs", 20),
                   "xp2_25a4owo4a52z4a521w125a4": ("04020a05050a029400f00294050a0a050402", 20),
                   "xp2_256o808ozxg999gzx110116a4": ("spark coil on diagnal_boats", 20),
                   "xp2_25ic0ci52zwhaaahz8k96069k8": ("tub_lightbulbs", 20),
                   "xp3_co9nas0san9oczgoldlo0oldlogz1047210127401": ("pulsar", 8),
                   "xp3_025qzraaahz08kb": ("[[long_hooks eating tubs]]", 10),
                   "xp3_03p606p3z252x252": ("[[short_hooks eating tubs]]", 10),
                   "xp3_0gs46364sgz13e8ogo8e31zy11": ("star", 15),
                   "xp3_4s3ia4oggzw12e": ("pulsar quadrant", 20),
                   "xp3_695qc8zx33": ("jam", 24),
                   "xp3_025qzrq221": ("trans-block tub eater", 28),
                   "xp3_4hh186z07": ("caterer", 29),
                   "xp3_025qz32qq1": ("cis-block tub eater", 30),
                   "xp3_3560uh224a4": ("longhook_eating_tub and trans-ship-up", 30),
                   "xp3_4a422hu06a4": ("cis-boat and long_hook_eating_tub", 30),
                   "xp3_2530fh884a4": ("longhook_eating_tub and cis-boat-up", 30),
                   "xp3_4a422hu0696": ("cis-beehive tub eater", 30),
                   "xp3_2560uh224a4": ("longhook_eating_tub and trans-boat-up", 30),
                   "xp3_2524sws4252": ("bent keys", 30),
                   "xp3_2524sws44a4": ("odd keys", 30),
                   "xp3_2522ewe2252": ("short keys", 30),
                   "xp3_4a422hu069a4": ("longhook_eating_tub and ortho-loaf-up", 30),
                   "xp3_4a422hu06996": ("longhook_eating_tub and cis-pond", 30),
                   "xp3_31ecsggsce13": ("keys variant", 30),
                   "xp3_6a889b8ozx33": ("00300033000900fe008000180018", 30),
                   "xp3_04qi3s4z33w1": ("trice tongs", 30),
                   "xp3_0g31u0ooz345d": ("0060009000b301a9001e000000180018", 30),
                   "xp3_6a889b8ozx356": ("0060005000100056009500d300100018", 30),
                   "xp3_co9na4oggzw12e": ("2 pulsar quadrants", 30),
                   "xp3_g8o0uh224a4z01": ("longhook_eating_tub and trans-boat-down", 30),
                   "xp3_g8o0uh224a4z11": ("longhook_eating_tub and trans-boat-down", 30),
                   "xp3_j1u0uh224a4z11": ("dock tub eater", 30),
                   "xp3_g31u0ooz11078c": ("00300033000900fe010001980018", 30),
                   "xp3_o4o0uh224a4z01": ("longhook_eating_tub and trans-beehive", 30),
                   "xp3_g88rb88gz11w8kb": ("longhook siamese hook_eating_tub and ?-block", 30),
                   "xp3_8k4o0uh224a4zw1": ("longhook_eating_tub and ortho-loaf-down", 30),
                   "xp3_g31u0o8zd5430fio": ("0300024801f80000007e008900b301b0", 30),
                   "xp3_0ggmmggs252z32w46": ("020005180298008000fe000900330030", 30),
                   "xp3_s471174sz11744711": ("cross", 30),
                   "xp3_g31u0u13gz1pgf0fgp1": ("00c600aa002800aa012901ab0028002800aa00c6", 30),
                   "xp3_ca66311366acz3566c88c6653": ("sym boat keys", 30),
                   "xp3_3js46364sj3zhje8ogo8ejhz11x1x11": ("4 blocks on star", 30),
                   "xp3_69ba99b606b99ab96z69d599d606d995d96": ("[4-fold]?p3", 30),
                   "xp3_s47117471174szt57y375tz1174471744711": ("cross 2", 30),
                   "xp3_3jc42s0s24cj3z08l55o0o55l8z6611210121166": ("[4-fold] trice tongs", 30),
                   "xp3_3jc42s0s24cj3z08l55t0t55l8z6611210121166": ("[4-fold] trice tongs variant", 30),
                   "xp3_co9na4o0o4an9oczwhaaah0haaahz63ita43034ati36": ("[4-fold] pulsar quadrants", 30),
                   "xp3_y43p606p3zo80gg8ka52x25ak8gg08ozol588g8gy3g8g885lozy2125qxq521zy46430346": ("[4-fold] short_hooks eating tubs", 30),
                   "xp4_y1g8bb8gzcc0u1y21u0cczy0124kk421zy311": ("octagon IV", 20),
                   "xp4_y1g8bb8gzcc0u1wccw1u0cczy0124kk421zy311": ("octagon IV w block", 20),
                   "xp4_37bkic": ("mold", 21),
                   "xp4_ssj3744zw3": ("mazing", 23),
                   "xp4_8eh5e0e5he8z178a707a871": ("cloverleaf", 25),
                   "xp4_hv4a4vh": ("monogram", 30),
                   "xp4_3lk453z34ats": ("cis-mold and dock", 30),
                   "xp4_199aaooaa991": ("?p4", 30),
                   "xp4_ciq3k3qiczcimgagmiczx343": ("cloverleaf siamese hat", 30),
                   "xp4_g8eh5e0e5he8gz0178a707a871": ("cloverleaf siamese beehives", 30),
                   "xp4_17f8a606a8f71z8ef1560651fe8": ("4 tails", 30),
                   "xp4_y38eh5e0e5he8zg88cgc89n8a707a8n98cgc88gzhara0arahy3hara0arahz1226162it2as0sa2ti2616221zy32ehke0ekhe2": ("[4-fold] cloverleafs", 30),
                   "xp5_idiidiz01w1": ("octagon II", 26),
                   "xp5_y131u0u13z3lkkk21x12kkkl3z32x12s0s21x23zy13210123": ("harbor", 30),
                   "xp5_3pmwmp3zx11": ("fumarole", 33),
                   "xp5_4aarahrrharaa4": ("hats ?p5", 40),
                   "xp5_25a84cgz8ka2461": ("tubs-fumarole", 40),
                   "xp5_35a84cgzoka2461": ("boats-fumarole", 40),
                   "xp5_39u0u93z0fm0mfzc97079c": ("bookends_pair ?p5", 40),
                   "xp5_356o8gy0g8o653zy09cvwvc9": ("ship-tie-boats fumarole", 40),
                   "xp5_oca71v0v17acoztll55o0o55lltz012747074721": ("[4-fold] hearts", 40),
                   "xp5_y1g6q11q6gzo624521y0125426oz03215a4owo4a5123zy2324423": ("[4-fold] tubs fumaroles"),
                   "xp5_y125a404a52z25a40653x35604a52z4a5206acxca6025a4zy14a52025a4": ("8 barges harbor", 40),
                   "xp5_y4g6q11q6gz0gg08kc321y0123ck80ggz6pg99gy8g99gp6zy0123ck8gwg8kc321zy5658856": ("[4-fold] boat-tie fumaroles", 40),
                   "xp5_y1256o8g0g8o652z256o8xg87078gx8o652zxol5558gxg8555loz253y1ogf0fgoy1352zy1253y3352": ("8 boats on harbor", 40),
                   "xp6_ccb7w66z066": ("unix", 20),
                   "xp6_3jc42sws24cj3z0g999gwg999gzcc3243w3423cc": ("[4-fold] pseudo trice tongs", 25),
                   "xp6_co9na4owo4an9oczw1iii1w1iii1zc65qk87w78kq56czw11y411": ("[4-fold] pseudo pulsar quadrants", 25),
                   "xp6_g80e55e08gz120ekke021": ("A for all", 45),
                   "xp8_gk2gb3z11": ("figure-8", 20),
                   "xp8_g3jgz1ut": ("blocker", 24),
                   "xp8_wgovnz234z33": ("Tim Coe's p8", 31),
                   "xp8_2erore2z07x7": ("smiley", 45),
                   "xp11_xg8k8x33x8k8gzw121ow111111wo121z33xfy6fx33zw25ak8022222208ka52zy633": ("Achim's p11", 50),
                   "xp14_j9d0d9j": ("tumbler", 25),
                   "xp15_4r4z4r4": ("pentadecathlon", 15),
                   "xp15_4r4y14r4z4r4y14r4": ("bi-pentadecathlon 1", 15),
                   "xp15_4r4y1uquz4r4y1fbf": ("bi-pentadecathlon 2", 15),
                   "xp15_4evy2ve4zzw75777757": ("bi-pentadecathlon 3", 15),
                   "xp15_4r4y1s212sz4r4y178g87": ("bi-pentadecathlon 4", 15),
                   "xp15_4evy2ve4zz02252222522": ("bi-pentadecathlon 5", 15),
                   "xp15_9f9y1skszbrby1vnvz232": ("bi-pentadecathlon 6", 15),
                   "xp15_9f9y2skszbrby2vnvz232": ("bi-pentadecathlon 7", 15),
                   "xp15_4r4xosu3usoz4r4x37fof73": ("bi-pentadecathlon 8", 15),
                   "xp15_9f9y18m8zbrby18n8z232y21": ("bi-pentadecathlon 9", 15),
                   "xp15_ijiy1gcgzmgmy1gfgz4c4y23": ("bi-pentadecathlon 10", 15),
                   "xp15_3v3y2gcgz9g9y2gfgzcfcy33": ("bi-pentadecathlon 11", 15),
                   "xp15_04evy2ve4zz772225w522277": ("bi-pentadecathlon 12", 15),
                   "xp15_3v3y08cec8z9g9zcfcy013731": ("bi-pentadecathlon 13", 15),
                   "xp15_4r4y1uquy14r4z4r4y1fbfy14r4": ("tri-pentadecathlon 1", 15),
                   "xp15_uquy14r4y1uquzfbfy14r4y1fbf": ("tri-pentadecathlon 2", 15),
                   "xp15_4r4xosu3usox4r4z4r4x37fof73x4r4": ("tri-pentadecathlon 3", 15),
                   "xp15_4r4y1s212sy14r4z4r4y178g87y14r4": ("tri-pentadecathlon 4", 15),
                   "xp15_sksy19f9y1skszvnvy1brby1vnvzy4232": ("tri-pentadecathlon 5", 15),
                   "xp15_sksy29f9y2skszvnvy2brby2vnvzy5232": ("tri-pentadecathlon 6", 15),
                   "xp15_4r4wg4211124gw4r4z4r4w148ggg841w4r4": ("tri-pentadecathlon 7", 15),
                   "xp15_s212sy14r4y1s212sz78g87y14r4y178g87": ("tri-pentadecathlon 8", 15),
                   "xp15_4evy2ve4zzw75777757z0goy2ogz137y2731": ("tri-pentadecathlon 9", 15),
                   "xp15_9f9y1sksy19f9zbrby1vnvy1brbz232y9232": ("tri-pentadecathlon 10", 15),
                   "xp15_9f9y2sksy29f9zbrby2vnvy2brbz232yb232": ("tri-pentadecathlon 11", 15),
                   "xp15_uquy14r4y14r4y1uquzfbfy14r4y14r4y1fbf": ("quad-pentadecathlon 1", 15),
                   "xp15_4evy2ve4zz02252222522z0goy2ogz137y2731": ("tri-pentadecathlon 12", 15),
                   "xp15_8m8y19f9y18m8z8n8y1brby18n8z01y2232y21": ("tri-pentadecathlon 13", 15),
                   "xp15_4evy2ve4zz722707707227z0goy2ogz137y2731": ("tri-pentadecathlon 14", 15),
                   "xp15_3v3y18cec8y13v3z9g9yb9g9zcfcy113731y1cfc": ("tri-pentadecathlon 15", 15),
                   "xp15_8cec8y03v3y08cec8zy59g9z13731y0cfcy013731": ("tri-pentadecathlon 16", 15),
                   "xp15_4r4xosu3uso0osu3usox4r4z4r4x37fof73037fof73x4r4": ("quad-pentadecathlon 2", 15),
                   "xp15_e0hh0ewe0hh0ezxsksssskszzx75777757ze0hh0ewe0hh0e": ("quad-pentadecathlon 3", 15),
                   "xp15_4r4wg421112404211124gw4r4z4r4w148ggg84048ggg841w4r4": ("quad-pentadecathlon 4", 15),
                   "xp15_4r4xg421112404211124gx4r4z4r4x148ggg84048ggg841x4r4": ("quad-pentadecathlon 5", 15),
                   "xp15_8m8y29f9y19f9y28m8z8n8y2brby1brby28n8z01y3232y1232y31": ("quad-pentadecathlon 6", 15),
                   "xp15_gcgy23v3y13v3y2gcgzgfgy29g9y19g9y2gfgz03y3cfcy1cfcy33": ("quad-pentadecathlon 7", 15),
                   "xp15_8cec8y03v3y13v3y08cec8zy59g9y19g9z13731y0cfcy1cfcy013731": ("quad-pentadecathlon 8", 15),
                   "xp15_178cy04r4zgs26y04r4": ("pentadecathlon w eaters", 25),
                   "xp15_4r4y0ccy04r4z4r4y066y04r4": ("bi-pentadecathlon w blocks", 25),
                   "xp15_sksy0ohf0fhoy0skszvnvy0c4o0o4cy0vnvzy423032": ("bi-pentadecathlon w sym-hooks_pair", 25),
                   "xp29_y8252y1252zy94c4x4c4z8k8y0ogydgoy08k8zy3hyfhz252y031yd13y0252zy9464x464zy88k8y18k8": ("p29 pre-pulsar-shuttle", 20),
                   "xp30_w33z8kqrqk8zzzw33": ("cis-queen-bee-shuttle", 24),
                   "xp30_w33z8kqrqk8zzzx33": ("trans-queen-bee-shuttle", 24),
                   "xp30_w33z8kqrqk8zzzz25brb52zwoo": ("symmetric queen-bee-shuttle 1", 24),
                   "xp30_ccx8k2s3yd3s2k8xcczy3103yd301": ("symmetric queen-bee-shuttle 2", 24),
                   "xp30_252y1252z04r4x4r4zzz04r4x4r4z8k8y18k8": ("[2-fold] p30 pre-pulsar-shuttle", 30),
                   "xp30_ya252y1252zycgy1gz0gy9333x333y9gz121y2277yb772y2121z8k8y24eeybee4y28k8zybcscxcsczzya4a4y14a4": ("[4-fold] p30 pre-pulsar-shuttle", 30),
                   "xp46_330279cx1aad3y833zx4e93x855bc": ("cis-twin-bees-shuttle", 35),
                   "xp46_330279cx1aad3zx4e93x855bcy8cc": ("trans-twin-bees-shuttle", 35),
                   "xq3_16614e8o4aa82cc2": ("edge-repair spaceship 1", 75),
                   "xq3_km92z1d9czxor33zy11": ("edge-repair spaceship 2", 75),
                   "xq3_mhqkzarahh0heezdhb5": ("dart", 75),
                   "xq3_3u0228mc53bgzof0882d6koq1": ("turtle", 75),
                   "xq4_153": ("glider", 0),
                   "xq4_6frc": ("lightweight spaceship", 6),
                   "xq4_27dee6": ("middleweight spaceship", 8),
                   "xq4_27deee6": ("heavyweight spaceship", 12),
                   "xq4_27dee6z4eb776": ("MWSS on MWSS 1", 20),
                   "xq4_27deee6z4eb7776": ("HWSS on HWSS 1", 20),
                   "xq4_27de6z4eb776": ("LWSS on MWSS 1", 40),
                   "xq4_27du6ze98885": ("LWSS on MWSS 3", 40),
                   "xq4_0791h1az8smec": ("LWSS on MWSS 2", 40),
                   "xq4_27de6z4eb7776": ("LWSS on HWSS 1", 40),
                   "xq4_6ed72z6777be4": ("LWSS on HWSS 2", 40),
                   "xq4_27de6z8smeeec": ("LWSS on HWSS 5", 40),
                   "xq4_27dumze988885": ("LWSS on HWSS 7", 40),
                   "xq4_27due6ze98885": ("MWSS on MWSS 5", 40),
                   "xq4_27de6zw8smeeec": ("LWSS on HWSS 3", 40),
                   "xq4_027deee6z8smec": ("LWSS on HWSS 4", 40),
                   "xq4_06eeed72zcems8": ("LWSS on HWSS 6", 40),
                   "xq4_27dee6zw4eb776": ("MWSS on MWSS 2", 40),
                   "xq4_677be4zx48889e": ("MWSS on MWSS 3", 40),
                   "xq4_06eed72zaghgis": ("MWSS on MWSS 4", 40),
                   "xq4_27dee6z4eb7776": ("MWSS on HWSS 2", 40),
                   "xq4_6eeed72zaghgis": ("MWSS on HWSS 10", 40),
                   "xq4_27duee6ze98885": ("MWSS on HWSS 11", 40),
                   "xq4_27duu6ze988885": ("MWSS on HWSS 13", 40),
                   "xq4_6eed72zaghhgis": ("MWSS on HWSS 14", 40),
                   "xq4_27dee6zw4eb7776": ("MWSS on HWSS 1", 40),
                   "xq4_06eeed72z677be4": ("MWSS on HWSS 3", 40),
                   "xq4_27dee6zx8smeeec": ("MWSS on HWSS 4", 40),
                   "xq4_aghgiszza1hh197": ("MWSS on HWSS 7", 40),
                   "xq4_02111197zcssqe4": ("MWSS on HWSS 9", 40),
                   "xq4_0791hh1az8smeec": ("MWSS on HWSS 12", 40),
                   "xq4_06eeed72zaghgis": ("MWSS on HWSS 15", 40),
                   "xq4_27duue6ze988885": ("HWSS on HWSS 7", 40),
                   "xq4_0sighhgazz791h1a": ("MWSS on HWSS 5", 40),
                   "xq4_sighhgazz791hh1a": ("MWSS on HWSS 6", 40),
                   "xq4_0aghhgiszza1h197": ("MWSS on HWSS 8", 40),
                   "xq4_27deee6zw4eb7776": ("HWSS on HWSS 2", 40),
                   "xq4_027deee6zsighhga": ("HWSS on HWSS 6", 40),
                   "xq4_06eeed72zaghhgis": ("HWSS on HWSS 8", 40),
                   "xq4_a1hh197zx6777be4": ("HWSS on HWSS 9", 40),
                   "xq4_27deee6zwsighhga": ("HWSS on HWSS 10", 40),
                   "xq4_0aghhgiszza1hh197": ("HWSS on HWSS 4", 40),
                   "xq4_aghhgiszzwa1hh197": ("HWSS on HWSS 5", 40),
                   "xq4_027deee6z4eqscc6": ("sidecar", 45),
                   "xq4_a1hhpnzy03mvo2ms8zy211": ("MWSS on pushalong", 55),
                   "xq4_82gfxossz34d72w37d6": ("HWSS on semi-X66", 60),
                   "xq4_0oorxroozdjio404oijd": ("X66", 66),
                   "xq7_3nw17862z6952": ("loafer", 70),
                   "xq7_7dfxg88gxfd7zw123u2222u321": ("weekender", 70),
                   "xq12_fh1i0i1hfzw8sms8zxfjf": ("lightweight schick engine", 50),
                   "xq12_xupuzw27d72zu10109ghuz3221": ("asymmetric schick engine", 50),
                   "xq12_v1120211vz01gpcpg1zxv7vzy01": ("middleweight schick engine", 50),
                   "xq12_v1120211vz120ioi021zw1vev1zx121": ("heavyweight schick engine", 50),
                   "xq16_gcbgzvgg826frc": ("Coe ship", 50),
                   "xs4_33": ("block", 0),
                   "xs4_252": ("tub", 0),
                   "xs5_253": ("boat", 0),
                   "xs6_bd": ("snake", 0),
                   "xs6_696": ("beehive", 0),
                   "xs6_356": ("ship", 0),
                   "xs6_39c": ("carrier", 0),
                   "xs6_25a4": ("barge", 0),
                   "xs7_25ac": ("long boat", 0),
                   "xs7_2596": ("loaf", 0),
                   "xs7_178c": ("eater", 0),
                   "xs7_3lo": ("long_snake", 2),
                   "xs8_3pm": ("shillelagh", 0),
                   "xs8_69ic": ("mango", 0),
                   "xs8_6996": ("pond", 0),
                   "xs8_35ac": ("long ship", 0),
                   "xs8_178k8": ("twit", 0),
                   "xs8_25ak8": ("long barge", 0),
                   "xs8_312ko": ("canoe", 0),
                   "xs8_31248c": ("very long snake", 3),
                   "xs8_32qk": ("hook with tail", 4),
                   "xs9_4aar": ("hat", 0),
                   "xs9_31ego": ("integral sign", 0),
                   "xs9_25ako": ("very long boat", 0),
                   "xs9_178ko": ("trans boat with tail", 0),
                   "xs9_178kc": ("cis boat with tail", 2),
                   "xs9_312453": ("long shillelagh", 4),
                   "xs9_25a84c": ("tub with long tail", 4),
                   "xs9_g0g853z11": ("long canoe", 4),
                   "xs9_178426": ("long_hook_with_tail", 6),
                   "xs9_31248go": ("very very long Snake", 8),
                   "xs10_35ako": ("very long ship", 0),
                   "xs10_g8o652z01": ("boat-tie", 0),
                   "xs10_32qr": ("block on table", 1),
                   "xs10_178kk8": ("beehive with tail", 1),
                   "xs10_69ar": ("loop", 2),
                   "xs10_358gkc": ("cis-shillelagh", 3),
                   "xs10_0drz32": ("broken snake", 3),
                   "xs10_g0s252z11": ("integral with tub", 3),
                   "xs10_3542ac": ("long integral", 4),
                   "xs10_1784ko": ("claw with tail", 4),
                   "xs10_3215ac": ("boat with long tail", 4),
                   "xs10_ggka52z1": ("trans barge with tail", 5),
                   "xs10_g8ka52z01": ("very long barge", 5),
                   "xs10_0j96z32": ("?10?006", 6),
                   "xs10_0cp3z32": ("?10?007", 6),
                   "xs10_4al96": ("barge siamese loaf", 7),
                   "xs10_178ka4": ("cis-barge with tail", 7),
                   "xs10_31eg8o": ("?10?010", 7),
                   "xs10_xg853z321": ("very long canoe", 8),
                   "xs10_drz32": ("?10?004", 9),
                   "xs10_25a8426": ("?10?009", 10),
                   "xs10_ggka23z1": ("?10?008", 10),
                   "xs10_2eg853": ("?10?011", 11),
                   "xs10_1784213": ("?10?012", 11),
                   "xs10_wg853z65": ("very^3 long Snake", 14),
                   "xs11_g8o652z11": ("boat tie ship", 0),
                   "xs11_g0s453z11": ("elevener", 2),
                   "xs11_ggm952z1": ("trans loaf with tail", 3),
                   "xs11_69lic": ("loaf siamese loaf", 4),
                   "xs11_178jd": ("11-loop", 4),
                   "xs11_178kic": ("cis loaf with tail", 4),
                   "xs11_2530f9": ("cis boat and table", 5),
                   "xs11_ggka53z1": ("trans-longboat with tail", 5),
                   "xs11_g0s253z11": ("trans boat with nine", 5),
                   "xs11_2ege13": ("?11?011", 6),
                   "xs11_2560ui": ("trans-boat and table", 6),
                   "xs11_178b52": ("?11-boat bend tail", 6),
                   "xs11_3586246": ("[11-snake]", 6),
                   "xs11_g0s256z11": ("cis-boat with nine", 6),
                   "xs11_31e853": ("?11?015", 7),
                   "xs11_31461ac": ("?11?004", 7),
                   "xs11_g8ka52z11": ("very very long boat", 7),
                   "xs11_25icz65": ("?11?013", 8),
                   "xs11_178c4go": ("?11?002", 8),
                   "xs11_32132ac": ("?11?005", 8),
                   "xs11_256o8go": ("boat on snake", 8),
                   "xs11_354c826": ("?11?010", 8),
                   "xs11_69jzx56": ("?11?008", 8),
                   "xs11_08o652z32": ("boat on aircraft", 8),
                   "xs11_178ka6": ("cis-longboat with tail", 9),
                   "xs11_25a84ko": ("?11?014", 9),
                   "xs11_3542156": ("?11?018", 9),
                   "xs11_69jzx123": ("?11?017", 9),
                   "xs11_25akg8o": ("?11?016", 10),
                   "xs11_178c48c": ("?11?022", 10),
                   "xs11_0cp3z65": ("?11?029", 10),
                   "xs11_31eg84c": ("?11?007", 10),
                   "xs11_358gka4": ("?11?006", 10),
                   "xs11_4ai3zx123": ("?11?021", 10),
                   "xs11_17842ac": ("?11?020", 11),
                   "xs11_35a8426": ("?11?019", 11),
                   "xs11_0drz65": ("?11?027", 12),
                   "xs11_25iczx113": ("?11?025", 12),
                   "xs11_wg84213z65": ("very very long canoe", 12),
                   "xs11_0g0s252z121": ("?11?028", 12),
                   "xs11_g88a52z23": ("?11?030", 13),
                   "xs11_3215a8o": ("?11?031", 14),
                   "xs11_17842sg": ("?11?023", 15),
                   "xs11_03ia4z65": ("very_long_hook_with_tail", 15),
                   "xs11_321eg8o": ("005000680008000b0005", 17),
                   "xs11_xg853zca1": ("very^4 long Snake", 18),
                   "xs12_raar": ("table on table", 0),
                   "xs12_g8o653z11": ("ship-tie", 0),
                   "xs12_178br": ("block and two tails", 3),
                   "xs12_330fho": ("trans block and longhook", 3),
                   "xs12_330f96": ("block and cap", 3),
                   "xs12_3hu066": ("cis block and longhook", 3),
                   "xs12_178c453": ("eater with nine", 3),
                   "xs12_2egm96": ("beehive bend tail", 5),
                   "xs12_2egm93": ("snorkel loop", 5),
                   "xs12_6960ui": ("beehive and table", 5),
                   "xs12_256o8a6": ("eater on boat", 5),
                   "xs12_o4q552z01": ("beehive at beehive", 5),
                   "xs12_0ggm96z32": ("beehive with nine", 5),
                   "xs12_69iczx113": ("trans-mango with tail", 6),
                   "xs12_g4q453z11": ("?12?006", 6),
                   "xs12_0g8o652z121": ("longboat on boat", 6),
                   "xs12_31egma": ("?12?013", 7),
                   "xs12_3123cko": ("ship on snake", 7),
                   "xs12_0ggm93z32": ("?12?004", 7),
                   "xs12_0g8o652z23": ("boat on eater", 7),
                   "xs12_651i4ozx11": ("?12?014", 7),
                   "xs12_0g8ka52z121": ("very very long barge", 7),
                   "xs12_3560ui": ("trans-ship and table", 8),
                   "xs12_6530f9": ("cis-ship and table", 8),
                   "xs12_0ggs252z32": ("?12?012", 8),
                   "xs12_32qj4c": ("cis-aircraft on table", 9),
                   "xs12_3542ako": ("?12?015", 9),
                   "xs12_178kia4": ("cis-mango with tail", 9),
                   "xs12_354qic": ("?12?017", 10),
                   "xs12_3215ako": ("?12?016", 10),
                   "xs12_252sga6": ("?12?034", 10),
                   "xs12_31eozx123": ("?12?019", 10),
                   "xs12_g8ka53z11": ("very very long ship", 10),
                   "xs12_5b8ozx123": ("?12?021", 10),
                   "xs12_08o653z32": ("ship on aircraft", 10),
                   "xs12_0ggka52z32": ("trans-barge with nine", 10),
                   "xs12_0gbaa4z121": ("?12?018", 10),
                   "xs12_0g0s256z121": ("?12?044", 10),
                   "xs12_358m93": ("?12?032", 11),
                   "xs12_178c2ko": ("?12?023", 11),
                   "xs12_178ka52": ("cis-longbarge with tail", 11),
                   "xs12_35icz65": ("?12?038", 11),
                   "xs12_35iczx113": ("?12?020", 11),
                   "xs12_g4q552z11": ("?12?024", 11),
                   "xs12_4ai3s4zx1": ("?12?026", 11),
                   "xs12_0g8ka52z23": ("trans-longbarge with tail", 11),
                   "xs12_0g8ge13z23": ("?12?022", 11),
                   "xs12_641j4czx11": ("?-carrier on carrier", 11),
                   "xs12_0g0s252z321": ("?12?008", 11),
                   "xs12_642tic": ("?12?059", 12),
                   "xs12_drz346": ("?12?043", 12),
                   "xs12_354cga6": ("?12?030", 12),
                   "xs12_4s0c93z11": ("trans-aircraft and table", 12),
                   "xs12_0gila4z32": ("cis-barge with nine", 12),
                   "xs12_39c0f9": ("para-aircraft and table", 13),
                   "xs12_32qb8o": ("rotated table", 13),
                   "xs12_358mic": ("?12?045", 13),
                   "xs12_358gka6": ("?12?068", 13),
                   "xs12_3pcz643": ("?12?055", 13),
                   "xs12_2ege123": ("?12?057", 13),
                   "xs12_628c0f9": ("?-carrier_and_table", 13),
                   "xs12_3lozx352": ("boat on long Snake", 13),
                   "xs12_03loz643": ("?12?046", 13),
                   "xs12_31eg8426": ("?12?035", 13),
                   "xs12_3pczw1246": ("?12?040", 13),
                   "xs12_69jzx1246": ("?12?049", 13),
                   "xs12_32qczx113": ("?12?072", 13),
                   "xs12_g88a53z23": ("?12?033", 13),
                   "xs12_69jzx1ac": ("?12?037", 14),
                   "xs12_0j96z346": ("very_very_long_integral", 14),
                   "xs12_0cq23z65": ("?12?058", 14),
                   "xs12_25a8og4c": ("?12?011", 14),
                   "xs12_25a8og8o": ("?12?054", 14),
                   "xs12_8ljgzx252": ("?12?065", 14),
                   "xs12_4alla4": ("honeycomb", 0),
                   "xs12_178ka23": ("?12?062", 15),
                   "xs12_31460ui": ("?12?060", 15),
                   "xs12_178k871": ("?12?042", 15),
                   "xs12_32130f9": ("snake and table", 15),
                   "xs12_31eg853": ("?12?071", 15),
                   "xs12_321e853": ("?12?029", 15),
                   "xs12_32akg84c": ("[[?12?073]]", 15),
                   "xs12_312312ko": ("?12?070", 15),
                   "xs12_17842156": ("00c6004900530020", 15),
                   "xs12_ck3123z11": ("?-snake_on_snake", 15),
                   "xs12_g88b52z23": ("005000680008000b00050002", 15),
                   "xs12_0g8k871z23": ("?-tub_with_tails", 15),
                   "xs12_0g8ka23z23": ("?12?031", 15),
                   "xs12_4ai3zx1246": ("?12?069", 15),
                   "xs12_5b8og4c": ("?-snake_eater_siamese_carrier", 16),
                   "xs12_4ap3z65": ("00c400aa00190003", 16),
                   "xs12_31230f9": ("table_and_?-snake", 16),
                   "xs12_32132qk": ("?12?066", 16),
                   "xs12_17842ak8": ("00c0004c005200250002", 16),
                   "xs12_025iczca1": ("0180014200250012000c", 16),
                   "xs12_kc3213z11": ("?-snake_on_snake", 16),
                   "xs12_ci52zw1246": ("?12?067", 16),
                   "xs12_25iczw1252": ("tub_bend_line_tub", 16),
                   "xs12_g853zdb": ("?12?063", 17),
                   "xs12_drz1226": ("?12?056", 17),
                   "xs12_25akg84c": ("barge_with_very_long_tail", 17),
                   "xs12_0ol3zca1": ("long_snake_siamese_long_snake", 17),
                   "xs12_25a842ac": ("00cc009200650002", 17),
                   "xs12_08o6413z32": ("?-carrier_on_carrier", 17),
                   "xs12_xg84213zca1": ("very^3 long canoe", 17),
                   "xs12_358m96": ("003200250015000a0004", 18),
                   "xs12_35861ac": ("0064004a00290013", 18),
                   "xs12_0gjl8z56": ("00a000d0001300150008", 18),
                   "xs12_1784c826": ("?-snake_eater_siamese_carrier", 18),
                   "xs12_3pczw1ac": ("?-very_long_snake_siamese_carrier", 18),
                   "xs12_ghn84cz1": ("[[hook w/ two tails]]", 18),
                   "xs12_3123c4go": ("?-snake_on_carrier", 18),
                   "xs12_ck3146z11": ("?-snake_on_carrier", 18),
                   "xs12_8o6413z32": ("?-snake_on_carrier", 18),
                   "xs12_ggdbz65": ("?-snake_on_snake", 19),
                   "xs12_321f84c": ("00580068000b000d", 19),
                   "xs12_178421e8": ("00c4004a00520023", 19),
                   "xs12_4ai3zx1ac": ("very_very_long_hook_with_tail", 19),
                   "xs12_0ggc93z641": ("00c000900030000c00090003", 20),
                   "xs13_4a960ui": ("ortho loaf and table", 4),
                   "xs13_g88m96z121": ("beehive at loaf", 4),
                   "xs13_69e0mq": ("R-bee and snake", 5),
                   "xs13_2530f96": ("[cis-boat and cap]", 5),
                   "xs13_0g8o653z121": ("longboat on ship", 5),
                   "xs13_32qb96": ("?13-head", 6),
                   "xs13_354djo": ("?13?016", 6),
                   "xs13_321fgkc": ("?13?009", 6),
                   "xs13_31egma4": ("[13-boat wrap eater]", 6),
                   "xs13_g8ge96z121": ("R-bee on beehive", 6),
                   "xs13_354mp3": ("?13?002", 7),
                   "xs13_3hu06a4": ("cis-boat-down and longhook", 7),
                   "xs13_31ege13": ("krake", 7),
                   "xs13_255q8a6": ("[eater tie beehive]", 7),
                   "xs13_djozx352": ("boat on shillelagh", 7),
                   "xs13_08ka96z321": ("?13?013", 7),
                   "xs13_0ggm952z32": ("?13-trans-loaf with nine", 7),
                   "xs13_2560uic": ("trans-boat and cap", 8),
                   "xs13_17871ac": ("?13?004", 8),
                   "xs13_25960ui": ("para-loaf and table", 8),
                   "xs13_2530fho": ("cis-boat-down and longhook", 8),
                   "xs13_2eg6p3zx1": ("?13-snorkel loop", 8),
                   "xs13_4aarzx123": ("?13?018", 8),
                   "xs13_31kmiczw1": ("?13?026", 8),
                   "xs13_0gbaicz121": ("?13?020", 8),
                   "xs13_0mk453z121": ("trans-boat-down and longhook", 8),
                   "xs13_6970bd": ("snake and R-bee", 9),
                   "xs13_3123qic": ("?13?028", 9),
                   "xs13_2560uh3": ("trans-boat-up and longhook", 9),
                   "xs13_356o8a6": ("?13-eater on ship", 9),
                   "xs13_c88a52z33": ("?13?003", 9),
                   "xs13_08u156z32": ("?13?033", 9),
                   "xs13_0gil96z32": ("?13-cis-loaf with nine", 9),
                   "xs13_08o696z321": ("beehive on hook", 9),
                   "xs13_0ggs253z32": ("?13?011", 9),
                   "xs13_0g8o652z321": ("boat on long ship", 9),
                   "xs13_39e0mq": ("hook and snake", 10),
                   "xs13_32qj96": ("?13?046", 10),
                   "xs13_259mge2": ("?13?007", 10),
                   "xs13_25ac0f9": ("cis-longboat and table", 10),
                   "xs13_354264ko": ("?13?048", 10),
                   "xs13_32qkzx346": ("?13?039", 10),
                   "xs13_g8ka23z56": ("?13?027", 10),
                   "xs13_g6q453z11": ("?13?067", 10),
                   "xs13_0ggka53z32": ("trans-longboat with nine", 10),
                   "xs13_wggm96z252": ("?13?032", 10),
                   "xs13_178n96": ("?13?005", 11),
                   "xs13_2ege1e8": ("sesquihat", 11),
                   "xs13_2lmge2z01": ("?13?057", 11),
                   "xs13_035iczca1": ("?13?035", 11),
                   "xs13_g0s2pmz11": ("?13?034", 11),
                   "xs13_08ob96z32": ("?13?031", 11),
                   "xs13_0gbaa4z321": ("?13?017", 11),
                   "xs13_0g8ka53z23": ("trans-very_longboat with tail", 11),
                   "xs13_wggm93z252": ("?13?040", 11),
                   "xs13_0gbb8oz121": ("?13?051", 11),
                   "xs13_0g8o653z23": ("ship on eater", 11),
                   "xs13_39e0db": ("snake and hook", 12),
                   "xs13_354c0f9": ("cis-eater on table", 12),
                   "xs13_358go8a6": ("?13?045", 12),
                   "xs13_3146178c": ("?13?019", 12),
                   "xs13_25a8oge2": ("?13?076", 12),
                   "xs13_3pczw1156": ("?13?029", 12),
                   "xs13_32arzx123": ("trans-eater and table", 12),
                   "xs13_0gbq23z121": ("trans-longboat and table", 12),
                   "xs13_0gbaa4z123": ("?13?050", 12),
                   "xs13_0g8ka52z321": ("very^3 longboat", 12),
                   "xs13_c9jzbd": ("?13?073", 13),
                   "xs13_32hu0oo": ("?13?092", 13),
                   "xs13_352sga6": ("?13?041", 13),
                   "xs13_32hu066": ("?13?055", 13),
                   "xs13_178c0f9": ("para-eater and table", 13),
                   "xs13_31eg84ko": ("?13?091", 13),
                   "xs13_0ggm96z56": ("?13?022", 13),
                   "xs13_oe1246z23": ("?13?038", 13),
                   "xs13_31eozx1252": ("?13?074", 13),
                   "xs13_0gba96z121": ("?13?065", 13),
                   "xs13_wg8o652z65": ("boat on canoe", 13),
                   "xs13_0ggs256z32": ("?13?014", 13),
                   "xs13_651i4ozw121": ("?13?069", 13),
                   "xs13_0g0s256z321": ("?13?100", 13),
                   "xs13_6246pic": ("?13?064", 14),
                   "xs13_178ka53": ("cis-very_longboat with tail", 14),
                   "xs13_31e86246": ("?13?043", 14),
                   "xs13_25akg853": ("?13?083", 14),
                   "xs13_3lozx356": ("ship on long Snake", 14),
                   "xs13_ci52z39c": ("?13?090", 14),
                   "xs13_256o8gkc": ("shillelagh on boat", 14),
                   "xs13_32132ako": ("?13?098", 14),
                   "xs13_25b8og8o": ("?13?097", 14),
                   "xs13_j5c48cz11": ("?13?099", 14),
                   "xs13_g8ka52z56": ("?13?071", 14),
                   "xs13_8ljgzx346": ("?13?047", 14),
                   "xs13_o4pb8oz01": ("001800240019000b00080018", 14),
                   "xs13_0gjla4z32": ("?13?087", 14),
                   "xs13_0o4871z643": ("?13?061", 14),
                   "xs13_g842156z123": ("?13?084", 14),
                   "xs13_0g0s253z321": ("?13?054", 14),
                   "xs13_178f123": ("?-snake_on_eater", 15),
                   "xs13_652sga6": ("?13?086", 15),
                   "xs13_32ac0f9": ("?13?078", 15),
                   "xs13_354215ac": ("?13?085", 15),
                   "xs13_32arz065": ("table_and_?-long_snake", 15),
                   "xs13_ghn871z1": ("?13?094", 15),
                   "xs13_178c48a6": ("?-eater_siamese_shillelagh", 15),
                   "xs13_256o8a52": ("?13?081", 15),
                   "xs13_17842ako": ("00c000a4004a00320003", 15),
                   "xs13_bdggkczw1": ("?13?093", 15),
                   "xs13_32qbzx113": ("?-eater_and_table", 15),
                   "xs13_0g6p56z121": ("?13?077", 15),
                   "xs13_25iczw1256": ("boat_bend_line_tub", 15),
                   "xs13_32qczx1246": ("?13?062", 15),
                   "xs13_39cggkczx1": ("?-carrier_on_eater", 15),
                   "xs13_0o4a52z643": ("00c000980064000a00050002", 15),
                   "xs13_08k8a52z321": ("006000500010002c001200050002", 15),
                   "xs13_69jwo8zx121": ("00300050004000230012000a0004", 15),
                   "xs13_j96zdb": ("?-long_shillelagh_siamese_snake", 16),
                   "xs13_c9jz39c": ("01930129006c", 16),
                   "xs13_6248n96": ("00300053005500280010", 16),
                   "xs13_321egma": ("0050006b000a00090006", 16),
                   "xs13_jhe8z65": ("?13?079", 16),
                   "xs13_641vg4c": ("?13?096", 16),
                   "xs13_35a8og4c": ("?13?080", 16),
                   "xs13_25b8og4c": ("?-boat_with_cis-tail_siamese_carrier", 16),
                   "xs13_31231ego": ("?13?060", 16),
                   "xs13_dj8gzx346": ("00c00080007000080013000d", 16),
                   "xs13_ggca52z65": ("snake on longboat", 16),
                   "xs13_0gbq23z23": ("?13?082", 16),
                   "xs13_w8o652zca1": ("very_long_snake_on_boat", 16),
                   "xs13_25iczx1156": ("00c000a00020002c001200050002", 16),
                   "xs13_wggka52z252": ("?-barge_line_tub", 16),
                   "xs13_wggs252z252": ("?-tub_with_tail_siamese_tub_with_tail", 16),
                   "xs13_0ggca52z641": ("aircraft on longboat", 16),
                   "xs13_31248gzy212ko": ("very^4 long canoe", 16),
                   "xs13_dbgzbd": ("016d01ab0010", 17),
                   "xs13_259m853": ("00660049002a00140008", 17),
                   "xs13_ci52zbd": ("?-tub_with_long_tail_siamese_snake", 17),
                   "xs13_3lozc96": ("?-shillelagh_siamese_long_snake", 17),
                   "xs13_178kq23": ("?-boat_with_tails", 17),
                   "xs13_35426853": ("00c30099006a0004", 17),
                   "xs13_32akg853": ("00c10087004800240018", 17),
                   "xs13_256o8ge2": ("?-snake_eater_on_boat", 17),
                   "xs13_2ege1246": ("00200050005300d50008", 17),
                   "xs13_0cp3z69c": ("?-long_shillelagh_siamese_carrier", 17),
                   "xs13_31eozca1": ("?13?070", 17),
                   "xs13_c9jzw1156": ("?-eater_on_carrier", 17),
                   "xs13_8ljgzx256": ("00c000a00050001300150008", 17),
                   "xs13_32hjkczw1": ("?-eater_on_snake", 17),
                   "xs13_3pa4zw1246": ("00c000980054002200010003", 17),
                   "xs13_0g8kq23z23": ("boat_with_cis-tails", 17),
                   "xs13_4ap3zw1252": ("004000a000430039000a0004", 17),
                   "xs13_0ggo8b5z32": ("?13?095", 17),
                   "xs13_0ggka52z56": ("00a000d000100014000a00050002", 17),
                   "xs13_69jzx1248c": ("very_very_long_cis-shillelagh", 17),
                   "xs13_0j9ak8z121": ("002000530029000a00140008", 17),
                   "xs13_6421eozx32": ("?13?088", 17),
                   "xs13_0g88b52z123": ("?-boat_line_boat", 17),
                   "xs13_25a88gzwca1": ("0080014000a3002500280010", 17),
                   "xs13_0g4q552z121": ("0030004800340008000a00050002", 17),
                   "xs13_358mp3": ("00330029000a00140018", 18),
                   "xs13_256o8b5": ("?-snake_eater_on_boat", 18),
                   "xs13_2ego8b5": ("?-snake_eater_siamese_eater", 18),
                   "xs13_3146o8a6": ("?13?089", 18),
                   "xs13_1784c871": ("?-snake_eater_siamese_eater", 18),
                   "xs13_69jzwc96": ("00c00120019300090006", 18),
                   "xs13_178ka246": ("?-tub_with_long_tail_and_tail", 18),
                   "xs13_0bq23z65": ("table_and_trans-long_snake", 18),
                   "xs13_dbgzw1156": ("?-eater_on_snake", 18),
                   "xs13_25a8og84c": ("?-tub_with_tail_siamese_long_snake", 18),
                   "xs13_ghn8426z1": ("004000700008001500130030", 18),
                   "xs13_g8k871z56": ("?-tub_with_long_tail_and_tail", 18),
                   "xs13_ggc871z65": ("?-eater_on_snake", 18),
                   "xs13_2eg8jdzx1": ("?-tub_with_long_tail_and_tail", 18),
                   "xs13_0gila4z56": ("00a000d000120015000a0004", 18),
                   "xs13_0ggm93z56": ("00c0009000680008000b0005", 18),
                   "xs13_wgila4z252": ("?-barge_line_tub", 18),
                   "xs13_ci53zw1246": ("00c00080004300250012000c", 18),
                   "xs13_0ok213zca1": ("[[long_snake siamese canoe]]", 18),
                   "xs13_4ai3zx1248c": ("018001000080004000230012000a0004", 18),
                   "xs13_3lo0ui": ("?13?101", 19),
                   "xs13_0drz254c": ("?-long_hook_with_tail_siamese_snake", 19),
                   "xs13_25icz69c": ("00c201250192000c", 19),
                   "xs13_321eg853": ("00c5008b004800280010", 19),
                   "xs13_35akg84c": ("long_boat_with_very_long_tail", 19),
                   "xs13_kq23z1ac": ("?-snake_eater_siamese_long_snake", 19),
                   "xs13_3ia4zc93": ("01830132006a0004", 19),
                   "xs13_8ljgzx652": ("004000a000d0001300150008", 19),
                   "xs13_32qczx1ac": ("?-very_long_snake_siamese_eater", 19),
                   "xs13_31248ge13": ("01830145004800500020", 19),
                   "xs13_03ia4z69c": ("00c001230192000a0004", 19),
                   "xs13_g84213zdb": ("01b001680004000200010003", 19),
                   "xs13_ggca23z65": ("?-eater_on_snake", 19),
                   "xs13_69jzx12ko": ("0300028000400020001300090006", 19),
                   "xs13_25akg8426": ("0080014300a500480030", 19),
                   "xs13_0g853zol3": ("?-long_snake_siamese_very_long_snake", 19),
                   "xs13_0kc0f9z32": ("long_snake_and_?-table", 19),
                   "xs13_03hik8z252": ("004000a30051001200140008", 19),
                   "xs13_3ia4zw1156": ("00c000a00024002a00120003", 19),
                   "xs13_0ggs252z56": ("?-tub_with_tail_siamese_snake_eater", 19),
                   "xs13_wggka23z252": ("00c00040005000280008000a00050002", 19),
                   "xs13_0354k8z6421": ("00c000830045002400140008", 19),
                   "xs13_ci52zw1248c": ("018001000080004200250012000c", 19),
                   "xs13_0g8gka52z23": ("00c0004000580024000a00050002", 19),
                   "xs13_1no3123": ("006d002b002000100030", 20),
                   "xs13_3146pic": ("0064004a001900050006", 20),
                   "xs13_1no3146": ("?-bookend_and_carrier", 20),
                   "xs13_1784cga6": ("00c000430059002a0004", 20),
                   "xs13_358e1246": ("00c8009500530030", 20),
                   "xs13_o861acz23": ("0058006800060001000a000c", 20),
                   "xs13_321eg8426": ("014001a3002500280010", 20),
                   "xs13_1784215a4": ("018c009200a50042", 20),
                   "xs13_j5c4goz11": ("00330029000c000800020006", 20),
                   "xs13_3lozx3146": ("?-long_snake_on_carrier", 20),
                   "xs13_3pczw1248c": ("?-long_canoe_siamese_carrier", 20),
                   "xs13_ca168ozx32": ("0018004800660001000a000c", 20),
                   "xs13_6413kczx32": ("003000100040006300150018", 20),
                   "xs13_0g8o6413z23": ("?-eater_on_carrier", 20),
                   "xs13_0ggc871z641": ("?-eater_on_carrier", 20),
                   "xs13_4ai30o8zx121": ("00100028002400620001000e0008", 20),
                   "xs14_69bqic": ("paperclip", 0),
                   "xs14_6970796": ("cis-mirrored R-bee", 0),
                   "xs14_g88b96z123": ("big S", 0),
                   "xs14_g88m952z121": ("half-bakery", 0),
                   "xs14_j1u066z11": ("block on dock", 1),
                   "xs14_69bo8a6": ("fourteener", 2),
                   "xs14_39e0e93": ("bookends", 2),
                   "xs14_6is079c": ("cis-rotated hook", 2),
                   "xs14_39e0eic": ("trans-hook and R-bee", 3),
                   "xs14_69e0eic": ("trans-mirrored R-bee", 3),
                   "xs14_39e0e96": ("cis-hook and R-bee", 4),
                   "xs14_g8o0e96z121": ("trans-rotated R-bee", 4),
                   "xs14_6960uic": ("beehive with cap", 5),
                   "xs14_j1u413z11": ("?14?007", 6),
                   "xs14_69la4ozx11": ("bi-loaf", 6),
                   "xs14_g8o69a4z121": ("para-R-bee on loaf", 6),
                   "xs14_4a9m88gzx121": ("[bi-loaf2]", 6),
                   "xs14_1no3tg": ("bookends", 7),
                   "xs14_31egm96": ("?14-beehive with long bend tail", 7),
                   "xs14_3hu0696": ("cis-beehive and longhook", 7),
                   "xs14_2egu156": ("?14?011", 7),
                   "xs14_o4s079cz01": ("para-hook and R-bee", 7),
                   "xs14_g8id96z121": ("?14?012", 7),
                   "xs14_g4s079cz11": ("[cis-mirrored offset hooks]", 7),
                   "xs14_39e0eio": ("trans-mirrored hook", 8),
                   "xs14_69960ui": ("pond and table", 8),
                   "xs14_31ego8a6": ("?14?019", 8),
                   "xs14_mmge13z1": ("?14?026", 8),
                   "xs14_i5q453z11": ("?14?025", 8),
                   "xs14_c88a53z33": ("?14?005", 8),
                   "xs14_g2u0696z11": ("trans-beehive and longhook", 8),
                   "xs14_o4id1e8z01": ("?14-mango with bend tail", 8),
                   "xs14_08o69a4z321": ("para-hook on loaf", 8),
                   "xs14_g88q552z121": ("R-loaf on beehive", 8),
                   "xs14_0g8o653z321": ("ship on long ship", 8),
                   "xs14_08o6952z321": ("ortho-hook on loaf", 8),
                   "xs14_g88m552z121": ("ortho-R-bee on loaf", 8),
                   "xs14_3hu0ui": ("longhook and table", 9),
                   "xs14_69f0f9": ("cap and table", 9),
                   "xs14_6970si6": ("ortho-hook and R-bee", 9),
                   "xs14_32qj4ko": ("?14?024", 9),
                   "xs14_4a9raa4": ("?14?051", 9),
                   "xs14_69arzx123": ("?14?041", 9),
                   "xs14_08u1e8z321": ("[hat join hook]", 9),
                   "xs14_0mk453z321": ("trans-ship and longhook", 9),
                   "xs14_69akgkczx1": ("loaf on eater", 9),
                   "xs14_65p68ozx11": ("?14?021", 9),
                   "xs14_g4s0796z11": ("shift-hook and R-bee", 9),
                   "xs14_08o0e96z321": ("meta-hook and R-bee", 9),
                   "xs14_08o0e93z321": ("trans-rotated hook", 9),
                   "xs14_3560uh3": ("ortho-ship and longhook", 10),
                   "xs14_4a9ria4": ("?14?016", 10),
                   "xs14_259e0mq": ("snake and R-loaf", 10),
                   "xs14_6530f96": ("cis-ship and cap", 10),
                   "xs14_3hu0okc": ("para-ship and longhook", 10),
                   "xs14_3560uic": ("trans-ship and cap", 10),
                   "xs14_djozx356": ("ship on shillelagh", 10),
                   "xs14_c88e13z33": ("?14?033", 10),
                   "xs14_c88b52z33": ("?14?029", 10),
                   "xs14_ci96zw1156": ("cis-mango with nine", 10),
                   "xs14_0g8ob96z23": ("?14?049", 10),
                   "xs14_08u1acz321": ("?14?048", 10),
                   "xs14_69jzx12453": ("?14?098", 10),
                   "xs14_65la4ozx11": ("?14?080", 10),
                   "xs14_wggm93z643": ("?14?087", 10),
                   "xs14_0gbaa4z343": ("?14?074", 10),
                   "xs14_0cq1e8z321": ("?14?032", 10),
                   "xs14_31egm93": ("?14?047", 11),
                   "xs14_dbgzmq1": ("?14?063", 11),
                   "xs14_cai3zbd": ("?14?064", 11),
                   "xs14_178f1e8": ("?14?044", 11),
                   "xs14_3hu06ac": ("cis-ship and longhook", 11),
                   "xs14_4aaraa4": ("hat siamese hat", 11),
                   "xs14_354c32ac": ("ortho-eater on eater", 11),
                   "xs14_256o8a53": ("trans-boat_with_tail on boat", 11),
                   "xs14_354cgs26": ("?14?076", 11),
                   "xs14_o8brzx123": ("?14?067", 11),
                   "xs14_0md1e8z32": ("?14?097", 11),
                   "xs14_0g8ehrz121": ("?14?093", 11),
                   "xs14_65pa4ozx11": ("?14?104", 11),
                   "xs14_0gbaicz321": ("?14?088", 11),
                   "xs14_69iczx1156": ("trans-mango with nine", 11),
                   "xs14_0gbb8oz321": ("?14?042", 11),
                   "xs14_69ak8zx1252": ("?14?065", 11),
                   "xs14_wggca52z2521": ("longboat on longboat", 11),
                   "xs14_64132qr": ("?14?077", 12),
                   "xs14_33gv146": ("?14?056", 12),
                   "xs14_3542tic": ("?14?130", 12),
                   "xs14_2552sga6": ("?14?040", 12),
                   "xs14_8o0uh3z23": ("trans-longhook and table", 12),
                   "xs14_g6pb8oz11": ("?14?082", 12),
                   "xs14_3lmge2z01": ("?14?014", 12),
                   "xs14_i5q8a6z11": ("?14?122", 12),
                   "xs14_0gbqicz23": ("?14?006", 12),
                   "xs14_o4s0796z01": ("shifted R-bee", 12),
                   "xs14_0gbap3z121": ("?14?117", 12),
                   "xs14_0gbb8oz123": ("?14?139", 12),
                   "xs14_wggm96z643": ("?14?119", 12),
                   "xs14_c88a52z352": ("?14?111", 12),
                   "xs14_64pb8ozx11": ("aircraft at cap", 12),
                   "xs14_64lb8ozw11": ("hook on hook", 12),
                   "xs14_g84q552z121": ("?14?091", 12),
                   "xs14_35ac0f9": ("cis-long_ship and table", 13),
                   "xs14_39c0f96": ("para-aircraft on cap", 13),
                   "xs14_178jq23": ("?14?018", 13),
                   "xs14_25is0qm": ("?14?163", 13),
                   "xs14_6421fgkc": ("?14?102", 13),
                   "xs14_178c2ego": ("?14?118", 13),
                   "xs14_4s0fhoz11": ("ortho-longhook and table", 13),
                   "xs14_j5s252z11": ("?14?142", 13),
                   "xs14_4s0f96z11": ("?14?140", 13),
                   "xs14_08u156z65": ("?14?106", 13),
                   "xs14_xok871z253": ("?14?153", 13),
                   "xs14_0m2s53z121": ("?14?073", 13),
                   "xs14_wggm96z652": ("?14?053", 13),
                   "xs14_wgil96z252": ("?14?109", 13),
                   "xs14_8ehjzw1252": ("eater on longboat", 13),
                   "xs14_65la8czw11": ("?14?120", 13),
                   "xs14_08ka952z321": ("?14?145", 13),
                   "xs14_wggm952z252": ("?14?138", 13),
                   "xs14_0g6p2sgz121": ("?14?081", 13),
                   "xs14_4a9j08ozx121": ("?14?151", 13),
                   "xs14_6970sic": ("cis-rotated R-bee", 14),
                   "xs14_69ic0f9": ("cis-mango and table", 14),
                   "xs14_178bq23": ("?14?069", 14),
                   "xs14_32132qr": ("?14?105", 14),
                   "xs14_0mp3zc96": ("?14?141", 14),
                   "xs14_25a8o653": ("ship_on_tub_with_tail", 14),
                   "xs14_39m8628c": ("?14?161", 14),
                   "xs14_cilmzx252": ("?14?123", 14),
                   "xs14_drz012156": ("?14?017", 14),
                   "xs14_4a9b8ozx32": ("?14?115", 14),
                   "xs14_04s39cz321": ("cis-aircraft on longhook", 14),
                   "xs14_xoka52z253": ("boat_on_very_long_boat", 14),
                   "xs14_0c88b5z253": ("?14?152", 14),
                   "xs14_0gbaa4z643": ("?14?075", 14),
                   "xs14_0ggm952z56": ("?14?134", 14),
                   "xs14_03lkk8z252": ("?14?125", 14),
                   "xs14_g8o652z1ac": ("?14?173", 14),
                   "xs14_0gbq23z321": ("trans-long ship_and_table", 14),
                   "xs14_wggm96z256": ("?14?148", 14),
                   "xs14_4s0ci96z11": ("trans-mango and table", 14),
                   "xs14_0g0s2pmz121": ("?14?092", 14),
                   "xs14_0c88a52z253": ("?14?166", 14),
                   "xs14_wggka52z643": ("?-barge_with_trans-tail_siamese_eater", 14),
                   "xs14_2ege1da": ("[[?14?180]]", 15),
                   "xs14_354cj96": ("?14?172", 15),
                   "xs14_259e0db": ("?-snake_and_R-loaf", 15),
                   "xs14_178bp46": ("?14?114", 15),
                   "xs14_25b8oge2": ("?14?124", 15),
                   "xs14_255q8a52": ("?14?089", 15),
                   "xs14_35icz69c": ("0186014900930060", 15),
                   "xs14_31230fho": ("cis-snake and longhook", 15),
                   "xs14_31e861ac": ("?14?112", 15),
                   "xs14_ggca53z65": ("snake on long ship", 15),
                   "xs14_4aq453z32": ("0064004a001a000400050003", 15),
                   "xs14_6ikm96z01": ("?-beehive_with_tail_siamese_snake", 15),
                   "xs14_31e8gzwbd": ("?14?110", 15),
                   "xs14_3146164ko": ("?14?121", 15),
                   "xs14_j5s246z11": ("?-amoeba-5,4,4", 15),
                   "xs14_0ml9a4z121": ("0020005600350009000a0004", 15),
                   "xs14_69eg8ozw23": ("?_eater_on_R-bee", 15),
                   "xs14_032qk8z253": ("?14?176", 15),
                   "xs14_gilmz1w252": ("?14?146", 15),
                   "xs14_08p78cz321": ("?-eater_on_hook", 15),
                   "xs14_wggm93z652": ("00c000a000500010001600090003", 15),
                   "xs14_0j5s26z121": ("?14?128", 15),
                   "xs14_31eozx1256": ("?14?046", 15),
                   "xs14_35iczx1156": ("?14?144", 15),
                   "xs14_0g6p56z321": ("006000500026001900050006", 15),
                   "xs14_4aarzx1252": ("?-tub_with_tail_siamese_hat", 15),
                   "xs14_25iczw178c": ("?-tub_with_long_tail_siamese_eater", 15),
                   "xs14_0gba96z321": ("boat on integral", 15),
                   "xs14_0gba96z123": ("?14?131", 15),
                   "xs14_ck31246z023": ("?14?129", 15),
                   "xs14_08k8a53z321": ("?14?171", 15),
                   "xs14_g84213z178c": ("?-eater_siamese_long_canoe", 15),
                   "xs14_wggka52z652": ("?-barge_line_boat", 15),
                   "xs14_25a88cz0253": ("?14?162", 15),
                   "xs14_wggc871z6221": ("?-eater_on_eater", 15),
                   "xs14_wggc871z2521": ("longboat on eater", 15),
                   "xs14_1no31e8": ("?-eater_and_bookend", 16),
                   "xs14_356o8b5": ("?-snake_eater_on_ship", 16),
                   "xs14_3542sga6": ("?14?154", 16),
                   "xs14_358go0ui": ("table_and_?-canoe", 16),
                   "xs14_3loz32ac": ("?-long_snake_on_eater", 16),
                   "xs14_3hu0og4c": ("?-carrier_and_long_hook", 16),
                   "xs14_j96z178c": ("?14?043", 16),
                   "xs14_2ego8a53": ("?-boat_with_trans-tail_siamese_eater", 16),
                   "xs14_330fh84c": ("00d800d0001300150008", 16),
                   "xs14_321fgka4": ("00b000d200150012000c", 16),
                   "xs14_256o8b52": ("cis-boat_with_tail on boat", 16),
                   "xs14_31ege123": ("00c500ab002800280010", 16),
                   "xs14_356o8gkc": ("?-shillelagh_on_ship", 16),
                   "xs14_628c2d96": ("006c00a900930060", 16),
                   "xs14_drz012552": ("?14?164", 16),
                   "xs14_252sgc4go": ("?-tub_with_tail_on_carrier", 16),
                   "xs14_8u15a4z32": ("?14?178", 16),
                   "xs14_3pmzw34a4": ("?-tub_with_tail_siamese_shillelagh", 16),
                   "xs14_0gil96z56": ("?14?159", 16),
                   "xs14_0ggraa4z32": ("?-eater_siamese_hat", 16),
                   "xs14_wg8o653z65": ("ship_on_canoe", 16),
                   "xs14_32qczx1156": ("?-integral_siamese_eater", 16),
                   "xs14_65la8ozx11": ("?-R-bee on R-bee", 16),
                   "xs14_69icga6zx1": ("002000530049002a00140008", 16),
                   "xs14_31eozx1253": ("?-boat_with_cis-tail_siamese_eater", 16),
                   "xs14_cp3z012552": ("beehive_with_tail_siamese_carrier", 16),
                   "xs14_08u15a4z32": ("00600048001e00010005000a0004", 16),
                   "xs14_0j9egoz121": ("?-tub_with_long_tail_siamese_hook", 16),
                   "xs14_xoge13z253": ("?14?127", 16),
                   "xs14_4aab8ozx32": ("?14?179", 16),
                   "xs14_69q4goz023": ("00300049002f00100004000c", 16),
                   "xs14_0o4a53z643": ("00c000a00050002600190003", 16),
                   "xs14_64lb8ozx11": ("?14?165", 16),
                   "xs14_wggm93z256": ("?14?070", 16),
                   "xs14_3pa4zw1156": ("?14?136", 16),
                   "xs14_65lmzw1023": ("cap_and_?-carrier", 16),
                   "xs14_cp3z012156": ("?14?168", 16),
                   "xs14_4a9mkk8zx1": ("hat siamese loaf", 16),
                   "xs14_wg8ka52z643": ("trans-longbarge with nine", 16),
                   "xs14_0g0si52z343": ("?14?086", 16),
                   "xs14_wggka52z256": ("?-barge_line_boat", 16),
                   "xs14_wggs252z652": ("?-boat_with_trans_tail_siamese_tub_with_trans_tail", 16),
                   "xs14_0g4q552z321": ("0060005000280008001600090006", 16),
                   "xs14_0gbaa4z1252": ("?14?167", 16),
                   "xs14_wg8k871z2521": ("very_long_barge_with_trans-tail", 16),
                   "xs14_dbz3553": ("?-cap_and_snake", 17),
                   "xs14_ci53zbd": ("?-boat_with_long_tail_siamese_snake", 17),
                   "xs14_39c0fho": ("?-long_hook_and_carrier", 17),
                   "xs14_3hu0oi6": ("cis-aircraft and longhook", 17),
                   "xs14_628c0f96": ("?-carrier_and_cap", 17),
                   "xs14_ci53z39c": ("?-boat_with_long_tail_siamese_carrier", 17),
                   "xs14_j9a4zc93": ("0193012900ac0040", 17),
                   "xs14_2530fh8o": ("00a000d0001200150036", 17),
                   "xs14_2ege12ko": ("00c4008a004a002b0010", 17),
                   "xs14_31460uic": ("cap_and_?-carrier", 17),
                   "xs14_642hu066": ("0018001000d300d50008", 17),
                   "xs14_2eg8o653": ("?14?061", 17),
                   "xs14_8k453zbd": ("?-integral_with_hook_siamese_snake", 17),
                   "xs14_3hu0628c": ("long_hook_and_?-carrier", 17),
                   "xs14_c9jz354c": ("[[eater fuse snake]]", 17),
                   "xs14_32130fho": ("long_hook_and_?-snake", 17),
                   "xs14_oe12koz23": ("?-cis-long_hook_with_tail_siamese_snake", 17),
                   "xs14_i5t246z11": ("?14?137", 17),
                   "xs14_8ehjkczw1": ("valentine", 17),
                   "xs14_0bq2sgz32": ("trans-legs_and_carrier", 17),
                   "xs14_1784264ko": ("?-long_hook_with_tail_siamese_eater", 17),
                   "xs14_0cq23z69c": ("?-eater_siamese_long_shillelagh", 17),
                   "xs14_3pczw12453": ("?-cis-shillelagh_siamese_carrier", 17),
                   "xs14_03hik8z643": ("00c000830071001200140008", 17),
                   "xs14_wgjla4z252": ("?-long_boat_line_tub", 17),
                   "xs14_0mk453z641": ("ortho-aircraft and longhook", 17),
                   "xs14_8ehjzw1074": ("?-eater_on_eater", 17),
                   "xs14_wgila4z643": ("?-barge_with_cis-tail_siamese_eater", 17),
                   "xs14_cai3zw1156": ("?14?156", 17),
                   "xs14_08o0uh3z32": ("?-long_hook_and_carrier", 17),
                   "xs14_wg8ge13z643": ("00c000a0002000280014000400050003", 17),
                   "xs14_025ak8z6511": ("long_barge_with_cis-nine", 17),
                   "xs14_0ck8a52z321": ("?-tub_with_long_tail_siamese_shillelagh", 17),
                   "xs14_4aabgzx1252": ("?14?107", 17),
                   "xs14_xgs252z4a43": ("?-tub_with_tail_siamese_tub_with_tail", 17),
                   "xs14_xg8o652zca1": ("long_canoe_on_boat", 17),
                   "xs14_651i4ozw321": ("00300050004300250012000c", 17),
                   "xs14_0g8ka53z321": ("very^3 long ship", 17),
                   "xs14_wg8k871z643": ("?-tub_with_tail_and_nine", 17),
                   "xs14_wggc453z643": ("?-eater_on_eater", 17),
                   "xs14_wggs252z256": ("?-cis-boat_with_tail_siamese_tub_with_tail", 17),
                   "xs14_wggka53z252": ("?14?090", 17),
                   "xs14_35a88gzwca1": ("0180014000a3002500280010", 17),
                   "xs14_wg8ka52z2521": ("very_very_very_long_barge", 17),
                   "xs14_4a51i4ozx121": ("00180024005200210005000a0004", 17),
                   "xs14_wg8k871z4701": ("?-barge_with_tails", 17),
                   "xs14_9f03pm": ("?-shillelagh_and_table", 18),
                   "xs14_3lozpi6": ("0323025500d8", 18),
                   "xs14_3123qp3": ("?-siamese_snakes_and_block", 18),
                   "xs14_ml96z56": ("?14?160", 18),
                   "xs14_32hu06a4": ("00a000d6001500120030", 18),
                   "xs14_jhke13z1": ("00330029000c000800070001", 18),
                   "xs14_358go8b5": ("?-snake_eater_siamese_canoe", 18),
                   "xs14_354260ui": ("table_and_?-shillelagh", 18),
                   "xs14_178kk871": ("beehive_with_cis-tails", 18),
                   "xs14_0mlicz56": ("00a000d600150012000c", 18),
                   "xs14_31460uh3": ("long_hook_and_?-carrier", 18),
                   "xs14_3hu06426": ("long_hook_and_?-snake", 18),
                   "xs14_651230f9": ("table_and_?-shillelagh", 18),
                   "xs14_178f1246": ("?-eater_on_long_snake", 18),
                   "xs14_39m86246": ("?14?174", 18),
                   "xs14_628c2dic": ("?-behive_siamese_tub_on_carrier", 18),
                   "xs14_6421egma": ("00600090005300d50008", 18),
                   "xs14_03iarz65": ("canoe_and_?-table", 18),
                   "xs14_4a9jz0bd": ("0190012b00ad0040", 18),
                   "xs14_2560uh23": ("00a200d5001600100030", 18),
                   "xs14_0o4a52zbd": ("?-barge_with_trans-tail_siamese_snake", 18),
                   "xs14_252sgc48c": ("?-tub_with_tail_on_snake", 18),
                   "xs14_3pmzx3213": ("?-shillelagh_on_snake", 18),
                   "xs14_0jhe8zca1": ("?-eater_on_long_snake", 18),
                   "xs14_6ikm93z01": ("?-great_snake_eater_siamese_snake", 18),
                   "xs14_g8ka53z56": ("very_long_boat_with_long_tail", 18),
                   "xs14_35akg8426": ("0180014300a500480030", 18),
                   "xs14_j5ka52z11": ("00330029000a001400280010", 18),
                   "xs14_djozx3146": ("?14?170", 18),
                   "xs14_0bt066z32": ("?-snake_siamese_carrier_and_block", 18),
                   "xs14_25b8og84c": ("?-boat_with_cis-tail_siamese_long_snake", 18),
                   "xs14_g4c0fhoz11": ("long_hook_and_?-carrier", 18),
                   "xs14_04ap56z311": ("00600024002a001900050006", 18),
                   "xs14_8ljgzx1156": ("00c000a000200030001300150008", 18),
                   "xs14_178ka4z311": ("?14?158", 18),
                   "xs14_8ljgzx34a4": ("?-tub_with_tail_siamese_snake_eater", 18),
                   "xs14_w8o653zca1": ("?14?149", 18),
                   "xs14_35iczw1256": ("boat_bend_line_boat", 18),
                   "xs14_031eozok21": ("?-very_very_long_snake_siamese_eater", 18),
                   "xs14_wgila4z652": ("?-boat_line_barge", 18),
                   "xs14_0ggo3tgz32": ("?-bookend_and_eater", 18),
                   "xs14_065la4z321": ("0060004600250015000a0004", 18),
                   "xs14_32qbzx1246": ("table_and_?-canoe", 18),
                   "xs14_8ehjzw1226": ("?-eater_on_eater", 18),
                   "xs14_ggka52sgz1": ("?-barge_with_tails", 18),
                   "xs14_358gzwok96": ("03000280004300250012000c", 18),
                   "xs14_8k4r9a4zw1": ("0018002800460039000a0004", 18),
                   "xs14_0ggca53z641": ("long_ship_on_carrier", 18),
                   "xs14_08o652z254c": ("?-snake_eater_on_boat", 18),
                   "xs14_ci53zw1248c": ("018001000080004300250012000c", 18),
                   "xs14_032ak8z6511": ("?-tub_with_tail_and_nine", 18),
                   "xs14_32qczx1248c": ("?-eater_siamese_long_canoe", 18),
                   "xs14_03iak8z2521": ("very_long_barge_with_cis-tail", 18),
                   "xs14_03iak8z6221": ("?14?169", 18),
                   "xs14_025a4ozc8421": ("018001020085004a00240018", 18),
                   "xs14_0drzrm": ("?-carrier_siamese_snakes", 19),
                   "xs14_3pajkc": ("?-shillelagh_on_snake", 19),
                   "xs14_5b8o0ui": ("?-snake_eater_and_table", 19),
                   "xs14_358e1da": ("006c002a00490033", 19),
                   "xs14_25a8o0ui": ("tub_with_trans-tail_and_?-table", 19),
                   "xs14_3iarz056": ("?14?177", 19),
                   "xs14_358gka53": ("00c300a1005200240018", 19),
                   "xs14_3hu06246": ("?14?150", 19),
                   "xs14_4a52sga6": ("00300052009500ca0004", 19),
                   "xs14_3pczwpic": ("?-very_long_shillelagh_siamese_carrier", 19),
                   "xs14_4ap3z69c": ("0180013300a90046", 19),
                   "xs14_252sgz0db": ("?-tub_with_tail_on_snake", 19),
                   "xs14_25a842ako": ("0180014c009200650002", 19),
                   "xs14_321eg84ko": ("0190012800c8000b0005", 19),
                   "xs14_08objoz32": ("?-snake_siamese_carrier_and_trans-block", 19),
                   "xs14_8ljgzx69c": ("0180012000d0001300150008", 19),
                   "xs14_raiczx113": ("006c00280024001a00020003", 19),
                   "xs14_8o0ojdz23": ("shillelagh_and_?-table", 19),
                   "xs14_025iczcip": ("0180024203250012000c", 19),
                   "xs14_25a84cga6": ("008001430099006a0004", 19),
                   "xs14_3lozx35a4": ("long_boat_on_long_snake", 19),
                   "xs14_8ljgzx696": ("00c0012000d0001300150008", 19),
                   "xs14_252sgzc93": ("?-tub_with_tail_on_carrier", 19),
                   "xs14_358go8gkc": ("?-shillelagh_siamese_canoe", 19),
                   "xs14_ol3zw32ac": ("?-eater_on_long_snake", 19),
                   "xs14_04al96z311": ("?-barge_with_cis-tail_siamese_loaf", 19),
                   "xs14_0gilicz641": ("00c00090003200150012000c", 19),
                   "xs14_c9jzw115a4": ("0080014000a0002000330009000c", 19),
                   "xs14_0ggka53z56": ("00c000a0005000280008000b0005", 19),
                   "xs14_4ap3zw1256": ("00c000a000430039000a0004", 19),
                   "xs14_4ap3zw1253": ("006000a000430039000a0004", 19),
                   "xs14_3lozx31246": ("?-long_snake_on_long_snake", 19),
                   "xs14_09fg4cz321": ("00600049002f00100004000c", 19),
                   "xs14_64kb9czw11": ("?-eater_siamese_carrier_siamese_snake_eater", 19),
                   "xs14_32arzx1252": ("tub_with_tail_and_trans-table", 19),
                   "xs14_0j9akoz121": ("002000530029000a00140018", 19),
                   "xs14_4aajkk8zx1": ("0008003800460031000e0008", 19),
                   "xs14_08o652z69c": ("?-long_shillelagh_on_boat", 19),
                   "xs14_g8ge13z1ac": ("0180010000e0001300250018", 19),
                   "xs14_4a9jzx1156": ("00c000a0002000330009000a0004", 19),
                   "xs14_ca9jzw1252": ("004000a000530029000a000c", 19),
                   "xs14_6413kczw65": ("?14?175", 19),
                   "xs14_3pczw115a4": ("?-tub_with_nine_siamese_carrier", 19),
                   "xs14_03iak8z643": ("?-tub_with_nine_and_tail", 19),
                   "xs14_0o4a52z39c": ("?-barge_with_trans-tail_siamese_carrier", 19),
                   "xs14_354qa4zx23": ("006000500010002d002b0010", 19),
                   "xs14_0g8gka53z23": ("00c000a000500024001a00020003", 19),
                   "xs14_02eg853z311": ("?-amoeba_5,4,4", 19),
                   "xs14_0g8kk871z23": ("00c0004000580024001a00020003", 19),
                   "xs14_31e88gzwca1": ("0180010000e3002500280010", 19),
                   "xs14_wggka23z652": ("?14?116", 19),
                   "xs14_69jzx1248go": ("very_very_very_long_cis-shillelagh", 19),
                   "xs14_wggka23z643": ("?-fuse_with_tails_siamese_eater", 19),
                   "xs14_w8k8a52z2521": ("004000a000500010002c001200050002", 19),
                   "xs14_g8421e8z1252": ("0030004800a400420001000e0008", 19),
                   "xs14_31248gzy212453": ("very_very_very_very_very_long_shillelagh", 19),
                   "xs14_0j96zrm": ("?-very_long_shillelagh_siamese_snake", 20),
                   "xs14_3loz1qm": ("031002ab006d", 20),
                   "xs14_c9jz6ip": ("0333024900cc", 20),
                   "xs14_32qk0f9": ("?-snake_eater_and_table", 20),
                   "xs14_1no31246": ("00d80055004300200060", 20),
                   "xs14_64268m96": ("?-beehive_siamese_tub_on_snake", 20),
                   "xs14_32arzca1": ("01b000a800850183", 20),
                   "xs14_358gu246": ("?-canoe_on_snake", 20),
                   "xs14_358e12ko": ("00c80094005200310003", 20),
                   "xs14_0cp3zoj6": ("0300026c00d90003", 20),
                   "xs14_321f84ko": ("00c000980068000b000d", 20),
                   "xs14_69jzxpic": ("018002400320001300090006", 20),
                   "xs14_3pczw6jo": ("carrier_siamese_carrier_siamese_carrier", 20),
                   "xs14_31248n96": ("00c600a50015000a0004", 20),
                   "xs14_g853zdjo": ("?-very_long_snake_siamese_shillelagh", 20),
                   "xs14_0g6p3zbc1": ("0180013000c80013000d", 20),
                   "xs14_178426853": ("0183013200aa0044", 20),
                   "xs14_wkc0f9z65": ("very_long_snake_and_?-table", 20),
                   "xs14_0gjla4z56": ("00a000d000130015000a0004", 20),
                   "xs14_i5m853z11": ("?-long_canoe_on_boat", 20),
                   "xs14_35a8og84c": ("?-boat_with_trans-tail_siamese_long_snake", 20),
                   "xs14_j5o652z11": ("003300290006001800280010", 20),
                   "xs14_rai3zx123": ("very_long_snake_and_?-table", 20),
                   "xs14_2ege1248c": ("004000a300a501a80010", 20),
                   "xs14_j5c2koz11": ("00330029000c0010000a0006", 20),
                   "xs14_gs25a4z56": ("00b000dc00020005000a0004", 20),
                   "xs14_256o8gka4": ("?-tub_with_long_tail_on_boat", 20),
                   "xs14_ok2156z65": ("00d800b40002000100050006", 20),
                   "xs14_g88a52zdb": ("?-tub_with_nine_siamese_snake", 20),
                   "xs14_25a8og853": ("?-tub_with_tail_siamese_canoe", 20),
                   "xs14_wgbq23z65": ("00c000a00010000b001a00020003", 20),
                   "xs14_1784215ac": ("018c009200a50043", 20),
                   "xs14_i5d2koz11": ("00320025000d000200140018", 20),
                   "xs14_358ge2z311": ("00630052000a000400380020", 20),
                   "xs14_oe1248cz23": ("0060002000400063002500280010", 20),
                   "xs14_31eg8oz311": ("00630042003a00040008000c", 20),
                   "xs14_0g84213zrm": ("036002d000080004000200010003", 20),
                   "xs14_gs25a4z146": ("0030009c00c20005000a0004", 20),
                   "xs14_ca9jzw1226": ("00c0004000530029000a000c", 20),
                   "xs14_g88a52zc96": ("0190012800c8000a00050002", 20),
                   "xs14_32qkzx34a4": ("0180008000b0005c000200050002", 20),
                   "xs14_08k453z4a43": ("01800140004c005200250002", 20),
                   "xs14_04ak871z311": ("?-barge_with_tails", 20),
                   "xs14_4ai31e8z011": ("0030001000230042003a000c", 20),
                   "xs14_wg8ka23z643": ("?-tub_with_nine_and_tail", 20),
                   "xs14_358gzw116io": ("?-very_long_snake_on_carrier", 20),
                   "xs14_25b88gzwca1": ("0080014001a3002500280010", 20),
                   "xs14_0g84213zol3": ("long_canoe_siamese_long_snake", 20),
                   "xs14_25iczx115a4": ("0080014000a00020002c001200050002", 20),
                   "xs14_wg8og853z65": ("siamese_canoes", 20),
                   "xs14_4ai3146zw23": ("0030001000400063002500280010", 20),
                   "xs14_0ck3146z321": ("?-shillelagh_on_carrier", 20),
                   "xs14_xg84215a4z321": ("060005000080004200250012000c", 20),
                   "xs15_354cgc453": ("moose antlers", 0),
                   "xs15_j1u06a4z11": ("cis-boat and dock", 3),
                   "xs15_259e0eic": ("trans R-bee and R-loaf", 4),
                   "xs15_3lkm96z01": ("bee-hat", 4),
                   "xs15_4a9raic": ("[15-bent-paperclip]", 5),
                   "xs15_259e0e96": ("cis-R-bee and R-loaf", 5),
                   "xs15_3lk453z121": ("trans boat and dock", 5),
                   "xs15_259e0eio": ("trans-hook and R-loaf", 6),
                   "xs15_259e0e93": ("cis-hook and R-loaf", 6),
                   "xs15_0gilicz346": ("?15?009", 6),
                   "xs15_o4s3pmz01": ("R-bee on shillelagh", 7),
                   "xs15_6t1egoz11": ("?15?028", 7),
                   "xs15_09v0ccz321": ("[hook join table and block]", 7),
                   "xs15_69bojd": ("?15?017", 8),
                   "xs15_25a8ob96": ("?15-tub scorp", 8),
                   "xs15_3213ob96": ("?15?013", 8),
                   "xs15_25960uic": ("para-loaf and cap", 8),
                   "xs15_25960uh3": ("para-loaf and longhook", 8),
                   "xs15_69aczw6513": ("para-hook and R-loaf", 8),
                   "xs15_g8o6996z121": ("R-bee on pond", 8),
                   "xs15_08o6996z321": ("hook on pond", 8),
                   "xs15_33gv1oo": ("?15?012", 9),
                   "xs15_178bqic": ("?15?059", 9),
                   "xs15_3hu069a4": ("ortho-loaf and longhook", 9),
                   "xs15_65123qic": ("?15?018", 9),
                   "xs15_0ggmp3z346": ("?15?052", 9),
                   "xs15_4a9b8oz033": ("?15?035", 9),
                   "xs15_06t1acz321": ("?15?022", 9),
                   "xs15_4ap6426z032": ("?15?005", 9),
                   "xs15_69ak8zx1256": ("?15?040", 9),
                   "xs15_0g8ka96z3421": ("?15-hovac on loaf", 9),
                   "xs15_0ggca96z3421": ("loaf on R-loaf", 9),
                   "xs15_4a960uic": ("?15?043", 10),
                   "xs15_4a970si6": ("?15?016", 10),
                   "xs15_25is0sic": ("?15?039", 10),
                   "xs15_oggm96z66": ("?15?025", 10),
                   "xs15_ca96zw3552": ("?15?014", 10),
                   "xs15_0g8ehrz321": ("?15?067", 10),
                   "xs15_06t1e8z321": ("?15?082", 10),
                   "xs15_69aczx3156": ("?15?054", 10),
                   "xs15_ca96zw3156": ("?15?015", 10),
                   "xs15_0gbb8oz343": ("?15?006", 10),
                   "xs15_kc0si96z11": ("snake and R-mango", 10),
                   "xs15_g88m596z121": ("?15?010", 10),
                   "xs15_0mk453z3421": ("?15?062", 10),
                   "xs15_0c8a52z2553": ("?15?034", 10),
                   "xs15_0g0si53z343": ("?15?033", 10),
                   "xs15_0j1u066z121": ("?15?024", 10),
                   "xs15_0ggca96z1243": ("R-loaf on loaf", 10),
                   "xs15_699m88gzx121": ("loaf on pond", 10),
                   "xs15_4aara96": ("?15?079", 11),
                   "xs15_259mge13": ("?15?041", 11),
                   "xs15_25is0si6": ("?15?058", 11),
                   "xs15_xoka52z653": ("?15?050", 11),
                   "xs15_0cid96z321": ("?15?004", 11),
                   "xs15_0j1u0ooz121": ("?15?088", 11),
                   "xs15_0mk453z1243": ("?15?044", 11),
                   "xs15_25a8czx6513": ("?15?074", 11),
                   "xs15_695q88gzx121": ("?15?029", 11),
                   "xs15_3pm0eic": ("R-bee and shillelagh", 12),
                   "xs15_178c0f96": ("?15?112", 12),
                   "xs15_4a970sic": ("?15?027", 12),
                   "xs15_25ac0fho": ("?15?155", 12),
                   "xs15_3loz12ego": ("?15?078", 12),
                   "xs15_j5q8a6z11": ("?15?056", 12),
                   "xs15_0gbap3z321": ("?15?177", 12),
                   "xs15_69aczx3552": ("?15?049", 12),
                   "xs15_08u1daz321": ("?15?057", 12),
                   "xs15_xok871z653": ("?15?087", 12),
                   "xs15_c88b52z352": ("?15?134", 12),
                   "xs15_69aczw2553": ("?15?036", 12),
                   "xs15_65la4ozw121": ("?15?100", 12),
                   "xs15_0gbaa4z3452": ("?15?064", 12),
                   "xs15_0c8a52z6513": ("?15?047", 12),
                   "xs15_wggm952z643": ("?15?032", 12),
                   "xs15_39e0mp3": ("hook and shillelagh", 13),
                   "xs15_178bpic": ("?15?073", 13),
                   "xs15_3pm0e96": ("?15?031", 13),
                   "xs15_2ego8br": ("?15?045", 13),
                   "xs15_69is0qm": ("?15?124", 13),
                   "xs15_255q8a53": ("?15?065", 13),
                   "xs15_25ac0f96": ("?15?141", 13),
                   "xs15_2ege1ego": ("?15?090", 13),
                   "xs15_358gu156": ("?15?170", 13),
                   "xs15_2egu15a4": ("?15?048", 13),
                   "xs15_31ege2ko": ("?15?125", 13),
                   "xs15_3lkia4z32": ("?15?072", 13),
                   "xs15_39u066z032": ("?15?132", 13),
                   "xs15_4aab8oz033": ("?15?080", 13),
                   "xs15_354miozw32": ("?15?099", 13),
                   "xs15_02llicz252": ("?15?092", 13),
                   "xs15_699mkk8zx1": ("?15?093", 13),
                   "xs15_c88e13z352": ("?15?019", 13),
                   "xs15_0gba96z343": ("?15?069", 13),
                   "xs15_0g0si96z343": ("beehive on R-mango", 13),
                   "xs15_0ggci96z643": ("?15?122", 13),
                   "xs15_g88a52z178c": ("?15?083", 13),
                   "xs15_4aabgzx3452": ("?15?103", 13),
                   "xs15_0ggci96z343": ("?15?042", 13),
                   "xs15_69b88czw252": ("?15?181", 13),
                   "xs15_xg8o653zca1": ("ship_on_long_canoe", 13),
                   "xs15_31eozx12552": ("?15?108", 13),
                   "xs15_0gbhe8z3421": ("?15?145", 13),
                   "xs15_0c88a52z2552": ("?15?110", 13),
                   "xs15_wggca52z6521": ("?15?149", 13),
                   "xs15_bd0ehr": ("?15?163", 14),
                   "xs15_4a9r8b5": ("006c002a0041003e0008", 14),
                   "xs15_3pq32ac": ("?15?105", 14),
                   "xs15_4a9ra96": ("?15?167", 14),
                   "xs15_39e0djo": ("?15?154", 14),
                   "xs15_256o8br": ("boat at table and block", 14),
                   "xs15_3hu0oka4": ("?15?184", 14),
                   "xs15_356o8a53": ("?15?173", 14),
                   "xs15_354c0f96": ("?15?095", 14),
                   "xs15_6413ob96": ("006c00a9008300700010", 14),
                   "xs15_178c2dio": ("?15?127", 14),
                   "xs15_39u0ooz32": ("?15?091", 14),
                   "xs15_bdgmiczw1": ("?15?089", 14),
                   "xs15_g8e13zpi6": ("?15?117", 14),
                   "xs15_39u066z32": ("?15?148", 14),
                   "xs15_3lkm93z01": ("?-great_snake_eater_siamese_hook", 14),
                   "xs15_cilmzx346": ("?15?150", 14),
                   "xs15_oggm93z66": ("?15?104", 14),
                   "xs15_wggm96z696": ("?15?130", 14),
                   "xs15_gilmz1w256": ("?15?051", 14),
                   "xs15_5b88a6z033": ("0050006b000b000800280030", 14),
                   "xs15_wgil96z643": ("?15?097", 14),
                   "xs15_0ggo8brz32": ("?15?194", 14),
                   "xs15_03lkk8z643": ("?15?151", 14),
                   "xs15_03lkk8z652": ("?15?161", 14),
                   "xs15_03pczok452": ("?15?183", 14),
                   "xs15_2lla8oz121": ("?15?075", 14),
                   "xs15_0ggraicz32": ("?-eater_siamese_loop", 14),
                   "xs15_8ehjzw1256": ("eater on long ship", 14),
                   "xs15_08o653z69c": ("?-ship_on_long_shillelagh", 14),
                   "xs15_0at1acz321": ("?15?166", 14),
                   "xs15_0at1e8z321": ("?15?063", 14),
                   "xs15_0c88a53z253": ("trans-boat_with_long_leg_and_trans-boat", 14),
                   "xs15_2552sgz0253": ("?-beehive_with_tail_on_boat", 14),
                   "xs15_03lk46z2521": ("ortho-long_hook_and_long_boat", 14),
                   "xs15_64lb8ozw121": ("?15?126", 14),
                   "xs15_025a8cz6513": ("?15?114", 14),
                   "xs15_31eozw122ac": ("?-integral_with_hook_siamese_eater", 14),
                   "xs15_g8hf0cicz01": ("?15?138", 14),
                   "xs15_0g0s2qrz121": ("[[?15?197]]", 14),
                   "xs15_xc8a52z6513": ("?15?111", 14),
                   "xs15_25aczw31156": ("trans-long_boat_and_long_hook", 14),
                   "xs15_02l2sgz2543": ("?15?081", 14),
                   "xs15_699m4k8zx11": ("?15?179", 14),
                   "xs15_g8id1egoz01": ("?15?023", 14),
                   "xs15_4a9r2qk": ("0068002e0041003a000c", 15),
                   "xs15_178c2d96": ("00c6004900550036", 15),
                   "xs15_25b8o653": ("?15?085", 15),
                   "xs15_69d2cga6": ("0060009300a9006a0004", 15),
                   "xs15_2lmge2z32": ("?15?118", 15),
                   "xs15_j5q453z11": ("[[anchor]]", 15),
                   "xs15_178c2c871": ("0183009200aa006c", 15),
                   "xs15_g4s3pmz11": ("?15?187", 15),
                   "xs15_0mlla4z32": ("?15?061", 15),
                   "xs15_035iczcip": ("0180024303250012000c", 15),
                   "xs15_65lmzx346": ("?-eater_and_cap", 15),
                   "xs15_g8ob96z56": ("?15?106", 15),
                   "xs15_69lmzx346": ("00c000800076001500090006", 15),
                   "xs15_w8u156zca1": ("?15?077", 15),
                   "xs15_0bq1e8z321": ("?15?107", 15),
                   "xs15_25aczw3553": ("?15?139", 15),
                   "xs15_ca9jzw3452": ("?15?178", 15),
                   "xs15_c88a53z352": ("trans-boat_with_long_leg_and_para-boat", 15),
                   "xs15_wgil96z652": ("?15?188", 15),
                   "xs15_c88b9czw33": ("00180048006b000b00080018", 15),
                   "xs15_xoka53z253": ("boat_on_very_long_ship", 15),
                   "xs15_0j9akoz321": ("?15?066", 15),
                   "xs15_wmk453z643": ("long_hook_and_?-eater", 15),
                   "xs15_0gba96z643": ("?15?165", 15),
                   "xs15_ciaj2aczw1": ("0010002800530041003e0008", 15),
                   "xs15_4s0s2pmzw1": ("00200050004b002a006a0004", 15),
                   "xs15_xoge13z653": ("ship_on_integral", 15),
                   "xs15_0j5s26z321": ("?-boat_with_leg_siamese_shillelagh", 15),
                   "xs15_0gbb8oz643": ("?15?142", 15),
                   "xs15_oggka52z66": ("?15?136", 15),
                   "xs15_wggm952z652": ("?15?119", 15),
                   "xs15_wggm952z256": ("?15?133", 15),
                   "xs15_8e1qczx1252": ("004000a0004c003a0001000e0008", 15),
                   "xs15_wg8ka53z643": ("?15?123", 15),
                   "xs15_0gbq2sgz121": ("?15?169", 15),
                   "xs15_ciabgzx1252": ("?15?102", 15),
                   "xs15_0g6p2sgz321": ("?15?055", 15),
                   "xs15_65la8ozw121": ("?15?068", 15),
                   "xs15_04aq453z311": ("006000500010002c002a00120003", 15),
                   "xs15_xc8a52z2553": ("tub_with_leg_and_meta-R-bee", 15),
                   "xs15_0g8gu156z23": ("00c0004000580028000b00090006", 15),
                   "xs15_w8o69a4z2521": ("?-tub_with_leg_on_loaf", 15),
                   "xs15_4a9ri96": ("?15?113", 16),
                   "xs15_5b8ob96": ("006600250041003e0008", 16),
                   "xs15_178c0fho": ("?15?121", 16),
                   "xs15_253gv146": ("?15?037", 16),
                   "xs15_2ege1da4": ("?15?195", 16),
                   "xs15_32hu0696": ("?15?162", 16),
                   "xs15_178f12ko": ("?-R-hat_siamese_canoe", 16),
                   "xs15_3hu0o8a6": ("long_hook_and_?-eater", 16),
                   "xs15_25is079c": ("?15?189", 16),
                   "xs15_3lkczc96": ("?-shillelagh_on_eater", 16),
                   "xs15_354c0fho": ("long_hook_and_?-eater", 16),
                   "xs15_25ako0ui": ("?15?143", 16),
                   "xs15_cilmzx256": ("?15?026", 16),
                   "xs15_j5s256z11": ("[[?15?196]]", 16),
                   "xs15_wmd1e8z65": ("?15?129", 16),
                   "xs15_wgbqicz65": ("?15?164", 16),
                   "xs15_04ap3zcip": ("03000260015300890006", 16),
                   "xs15_j5s253z11": ("003300290016000400050003", 16),
                   "xs15_cilmzx652": ("004000a000d600150012000c", 16),
                   "xs15_0ggs2pmz32": ("006000500010001c000200190016", 16),
                   "xs15_31eozw34ac": ("?-boat_with_very_long_tail_siamese_eater", 16),
                   "xs15_5b88a6zx33": ("[[dock_fuse_hook on block]]", 16),
                   "xs15_wggm93z696": ("0180012000d00010001600090006", 16),
                   "xs15_08o652zoj6": ("?-carrier_siamese_snake_on_boat", 16),
                   "xs15_31kmicz032": ("006000430015003400240018", 16),
                   "xs15_gjlmz1w252": ("tub_with_long_leg_and_cis-ship", 16),
                   "xs15_oggs252z66": ("?-tub_with_tail_siamese_table_and_block", 16),
                   "xs15_69arzx1252": ("?-loop_siamese_tub_with_tail", 16),
                   "xs15_03lkicz252": ("?15?076", 16),
                   "xs15_032qk8z653": ("?-boat_with_cis-tail_on_ship", 16),
                   "xs15_0ggrb8oz32": ("?-eater_siamese_table_and_cis-block", 16),
                   "xs15_03lk46z643": ("[[?-eater and longhook]]", 16),
                   "xs15_0gbaarz121": ("?15?137", 16),
                   "xs15_gilmz1w346": ("?-eater_siamese_table_and_boat", 16),
                   "xs15_39c8a6z033": ("?15?180", 16),
                   "xs15_0g6picz343": ("00600090006600190012000c", 16),
                   "xs15_0o4a96z39c": ("[[trans-loaf_with_tail fuse aircraft]]", 16),
                   "xs15_354m93zw32": ("?15?175", 16),
                   "xs15_wg8ob96z65": ("?15?159", 16),
                   "xs15_0ggra96z32": ("?-eater_siamese_loop", 16),
                   "xs15_03lka4z643": ("?15?116", 16),
                   "xs15_g853z123ck8": ("?-very_long_shillelagh_on_boat", 16),
                   "xs15_03iak8z6521": ("very_very_long_boat_with_cis-tail", 16),
                   "xs15_0c88b52z253": ("cis-boat_with_long_leg_and_trans-boat", 16),
                   "xs15_08o69icz321": ("?15?144", 16),
                   "xs15_025a8cz2553": ("?15?192", 16),
                   "xs15_259eg8ozx23": ("?-eater_on_R-loaf", 16),
                   "xs15_wggka53z643": ("?15?115", 16),
                   "xs15_8e1u8zx1252": ("?15?030", 16),
                   "xs15_69iczx115a4": ("?-tub_line_mango", 16),
                   "xs15_0c88a52z653": ("?15?060", 16),
                   "xs15_32qczx12453": ("?-cis-shillelagh_siamese_eater", 16),
                   "xs15_25akggozx66": ("trans-barge_with_long_leg_and_cis-block", 16),
                   "xs15_08k453zca43": ("?15?098", 16),
                   "xs15_31e88cz0253": ("?15?191", 16),
                   "xs15_cq23z012552": ("?15?086", 16),
                   "xs15_g8o69icz121": ("?15?174", 16),
                   "xs15_w8o6952z2521": ("?-tub_with_leg_on_loaf", 16),
                   "xs15_25a88gz4a511": ("?-binocle_tubs", 16),
                   "xs15_4aar9ic": ("?15?182", 17),
                   "xs15_4aar2qk": ("?-snake_eater_siamese_hat", 17),
                   "xs15_358ml96": ("?15?190", 17),
                   "xs15_2eg8ob96": ("?15?096", 17),
                   "xs15_4aarz0bd": ("?-hat_on_snake", 17),
                   "xs15_31ego0ui": ("?-integral_and_table", 17),
                   "xs15_2ego0uh3": ("long_hook_and_?-eater", 17),
                   "xs15_354ko0ui": ("?-integral_and_table", 17),
                   "xs15_64138n96": ("?15?094", 17),
                   "xs15_178c2dic": ("?-tub_siamese_beehive_on_eater", 17),
                   "xs15_32ac0f96": ("?-eater_and_cap", 17),
                   "xs15_252sgc453": ("?-tub_with_tail_on_eater", 17),
                   "xs15_pf0352z23": ("?-table_siamese_snake_and_?-boat", 17),
                   "xs15_ogkq23z66": ("?15?185", 17),
                   "xs15_25a8oge13": ("?-integral_siamese_tub_with_tail", 17),
                   "xs15_gbb871z23": ("?15?071", 17),
                   "xs15_256o8gka6": ("?-boat_on_boat_with_long_tail", 17),
                   "xs15_321ego8a6": ("014001a30021002e0018", 17),
                   "xs15_ogila4z66": ("cis-barge_with_long_leg_and_trans-block", 17),
                   "xs15_32qczx6jo": ("?-carrier_siamese_carrier_siamese_eater", 17),
                   "xs15_25a8o64ko": ("?-eater_on_tub_with_tail", 17),
                   "xs15_6248gu156": ("00c0012301a500280030", 17),
                   "xs15_g8o653z1ac": ("?-long_shillelagh_on_ship", 17),
                   "xs15_0gs252zpi6": ("0320025000dc000200050002", 17),
                   "xs15_02lla4z643": ("?-eater_on_tub_siamese_beehive", 17),
                   "xs15_4ap5a4z321": ("?-hook_siamese_mango_siamese_tub", 17),
                   "xs15_0c9b8oz253": ("?-Z_siamese_carrier_and_?-boat", 17),
                   "xs15_03lkk8z256": ("?15?176", 17),
                   "xs15_32qkgozw66": ("?-table_siamese_snake_eater_and_cis-block", 17),
                   "xs15_o8brzx1252": ("?-tub_with_tail_siamese_table_and_cis-block", 17),
                   "xs15_gs2596z146": ("?-loaf_with_cis-tail_siamese_carrier", 17),
                   "xs15_3iaczw178c": ("0180010000ec002a00120003", 17),
                   "xs15_4aligozw66": ("cis-barge_with_long_leg_and_cis-block", 17),
                   "xs15_32aczw3553": ("?-eater_and_cap", 17),
                   "xs15_0gjlicz641": ("00c00090003300150012000c", 17),
                   "xs15_c88a52z356": ("tub_with_long_leg_and_?-ship", 17),
                   "xs15_ck0o8brzw1": ("0060006000030079004a0004", 17),
                   "xs15_8k4ra96zw1": ("?-loop_siamese_loaf", 17),
                   "xs15_gilmz1w652": ("cis-boat_with_long_leg_and_cis-boat", 17),
                   "xs15_6ikm952z01": ("?-trans-loaf_with_tail_siamese_snake", 17),
                   "xs15_39c8a6zx33": ("?-hook_siamese_carrier_and_cis-block", 17),
                   "xs15_31ege2z311": ("?-amoeba_6,4,4", 17),
                   "xs15_0ggdjoz343": ("?-shillelagh_on_R-bee", 17),
                   "xs15_2530fpzx32": ("?-table_siamese_carrier_and_cis-boat", 17),
                   "xs15_0m2s53z321": ("?-boat_with_nine_siamese_shillelagh", 17),
                   "xs15_c82t52z311": ("006c00280022001d00050002", 17),
                   "xs15_0cq1daz321": ("0060004c003a0001000d000a", 17),
                   "xs15_wgil96z256": ("?15?053", 17),
                   "xs15_0c88b5z2552": ("?15?084", 17),
                   "xs15_0c88e13z253": ("?-eater_siamese_table_and_boat", 17),
                   "xs15_0g8ge13zc96": ("0180013000c80010000e00010003", 17),
                   "xs15_695q4ozw121": ("?-loaf_siamese_tub_siamese_beehive_siamese_tub", 17),
                   "xs15_0i5q453z121": ("?15?135", 17),
                   "xs15_0g8o0uh3z23": ("long_hook_and_?-eater", 17),
                   "xs15_0g8o652zc96": ("long_integral_on_boat", 17),
                   "xs15_35a88cz0253": ("?15?046", 17),
                   "xs15_25b88cz0253": ("cis-boat_with_long_leg_and_?-boat", 17),
                   "xs15_0c4gf9z2521": ("009000f0000c002200350002", 17),
                   "xs15_6512kozw643": ("?-cis-shillelagh_siamese_eater", 17),
                   "xs15_0g8o652zbc1": ("?-boat_with_long_tail_on_boat", 17),
                   "xs15_25a8czx2553": ("tub_with_leg_and_shift-R_bee", 17),
                   "xs15_wggka53z652": ("?-boat_line_long_boat", 17),
                   "xs15_065pa4z2521": ("004000a600450039000a0004", 17),
                   "xs15_wggs252z696": ("?15?186", 17),
                   "xs15_wggka52z696": ("?-barge_line_beehive", 17),
                   "xs15_0ggm96z12ko": ("0180024001a3002500280010", 17),
                   "xs15_wg8ka52z6521": ("very_very_very_very_long_boat", 17),
                   "xs15_wg8k871z6521": ("very_very_long_boat_and_trans-tail", 17),
                   "xs15_0256o8z4a521": ("boat_on_barge_with_cis-tail", 17),
                   "xs15_wggc871z6521": ("?-long_ship_on_eater", 17),
                   "xs15_32hu0ui": ("006c00280028006b0005", 18),
                   "xs15_354qajo": ("00680058000600390023", 18),
                   "xs15_35is0qm": ("boat_with_leg_and_?-snake", 18),
                   "xs15_6ags2pm": ("006c002a004900530020", 18),
                   "xs15_642132qr": ("long_snake_siamese_table_and_trans-block", 18),
                   "xs15_6952sga6": ("0060009300a9004a000c", 18),
                   "xs15_2egu2453": ("?-shillelagh_siamese_R-hat", 18),
                   "xs15_321fgs26": ("?-eater_siamese_long_eater_siamese_snake", 18),
                   "xs15_j9czd552": ("?-hat_on_carrier", 18),
                   "xs15_25b871ac": ("00cc009200550036", 18),
                   "xs15_32ac0fho": ("long_hook_and_?-eater", 18),
                   "xs15_321egm93": ("00c500ab002800480030", 18),
                   "xs15_32hu0653": ("00c500ab00680008000c", 18),
                   "xs15_178ko0ui": ("boat_with_trans-tail_and_?-table", 18),
                   "xs15_31ego8gkc": ("?-shillelagh_siamese_integral", 18),
                   "xs15_gs2596z56": ("?-loaf_with_cis-tail_siamese_snake", 18),
                   "xs15_3pmzw34ac": ("?-boat_with_trans-tail_siamese_shillelagh", 18),
                   "xs15_dbgz358go": ("03000200011000ab006d", 18),
                   "xs15_g5r8b5z11": ("?-amoeba_6,4,4", 18),
                   "xs15_djozx35a4": ("?-shillelagh_on_long_boat", 18),
                   "xs15_0o4a96zbd": ("?-loaf_with_trans-tail_siamese_snake", 18),
                   "xs15_354cgc2ko": ("0190012800ae00410003", 18),
                   "xs15_4s3iarzw1": ("?-long_hook_with_tail_on_table", 18),
                   "xs15_252sgc2ko": ("0198012800aa00450002", 18),
                   "xs15_4a51ug84c": ("00600090015300950018", 18),
                   "xs15_178c2cga6": ("0180009300a9006a0004", 18),
                   "xs15_3pczwd552": ("01800130006b000a000a0004", 18),
                   "xs15_ckl3zw34a4": ("?-eater_on_tub_with_tail", 18),
                   "xs15_cila8ozx32": ("?-tub_with_tail_siamese_loaf_siamese_carrier", 18),
                   "xs15_oggka23z66": ("00d800d000100014000a00020003", 18),
                   "xs15_3iaj2aczw1": ("?-table_siamese_eater_and_tub", 18),
                   "xs15_08o0uh3z65": ("long_hook_and_?-long_snake", 18),
                   "xs15_ggkc0fhoz1": ("long_hook_and_?-eater", 18),
                   "xs15_0ghn871z32": ("?-hat_with_nine", 18),
                   "xs15_0j9egoz321": ("?-boat_with_long_tail_siamese_hook", 18),
                   "xs15_g88e13zc96": ("0190012800c8000e00010003", 18),
                   "xs15_kc32acz123": ("?-shillelagh_on_eater", 18),
                   "xs15_2eg6p56zx1": ("0030004b006a001200140008", 18),
                   "xs15_3542arzx32": ("006c00290023001000500060", 18),
                   "xs15_0bdge2z321": ("0060004b002d0010000e0002", 18),
                   "xs15_cip68ozx32": ("00180048006600190012000c", 18),
                   "xs15_69iczx11da": ("014001a00020002c001200090006", 18),
                   "xs15_caarzw1226": ("?-snake_eater_siamese_R-hat", 18),
                   "xs15_wgjla4z652": ("?-long_boat_line_boat", 18),
                   "xs15_g88a53zc96": ("0190012800c8000a00050003", 18),
                   "xs15_wgjla4z643": ("?-long_boat_with_cis-tail_siamese_eater", 18),
                   "xs15_25t28cz321": ("00620045003d00020008000c", 18),
                   "xs15_0ml9a4z641": ("00c0009600350009000a0004", 18),
                   "xs15_69ab8ozx32": ("003000480028006b0009000c", 18),
                   "xs15_c88m96z311": ("?-hat_at_beehive", 18),
                   "xs15_g9fgka4z11": ("0060004c0032001500120030", 18),
                   "xs15_255mgmazx1": ("?-snake_eater_and_R-bee", 18),
                   "xs15_wgbq23z643": ("table_and_trans-integral", 18),
                   "xs15_0ggdjoz643": ("?-shillelagh_on_hook", 18),
                   "xs15_0kc0f9z346": ("long_shillelagh_and_?-table", 18),
                   "xs15_0gbq2sgz23": ("trans-legs_and_eater", 18),
                   "xs15_8ljgzx69a4": ("00800140012000d0001300150008", 18),
                   "xs15_0j9cz1215a4": ("0080014000ac002900530020", 18),
                   "xs15_0ok213zca23": ("?-canoe_on_eater", 18),
                   "xs15_0i5q8a6z121": ("?-eater_on_tubs", 18),
                   "xs15_0ck31e8z321": ("?-shillelagh_on_eater", 18),
                   "xs15_wg8o652z69c": ("?-boat_on_cis-shillelagh", 18),
                   "xs15_0ck8a53z321": ("0060005000280008001600190003", 18),
                   "xs15_4a4o796zx11": ("?-tub_with_tail_on_R-bee", 18),
                   "xs15_0gbaa4z1256": ("?15?193", 18),
                   "xs15_wggka52zc96": ("?15?158", 18),
                   "xs15_xok4871z253": ("?-great_snake_eater_on_boat", 18),
                   "xs15_wggs253z652": ("?-siamese_boats_with_trans_tail", 18),
                   "xs15_wggka53z256": ("?-long_boat_line_boat", 18),
                   "xs15_0g0s2pmz321": ("00600050002b000a000900050002", 18),
                   "xs15_255q88czx23": ("003000480031000f00080004000c", 18),
                   "xs15_wg8kq23z643": ("boat_with_cis-nine_and_cis-tail", 18),
                   "xs15_3542sgz0253": ("?-great_snake_eater_on_boat", 18),
                   "xs15_25a88cz0653": ("tub_with_long_leg_and_?-ship", 18),
                   "xs15_0g6pb8oz121": ("?15?152", 18),
                   "xs15_ca1u8zx1252": ("[[?15?195]]", 18),
                   "xs15_31eozx12156": ("?-great_snake_eater_siamese_eater", 18),
                   "xs15_03lk46z6221": ("long_hook_and_?-eater", 18),
                   "xs15_ci96zw115a4": ("?-tub_line_mango", 18),
                   "xs15_4aabgzx1256": ("00c000a00050002b000a000a0004", 18),
                   "xs15_25akozx6226": ("table_and_trans-very_long_boat", 18),
                   "xs15_25a4ozx122ac": ("01800140004000580024000a00050002", 18),
                   "xs15_4aab88gzx311": ("001000280028006b000a000a0004", 18),
                   "xs15_31248gzc8711": ("cis-long_hook_with_tail_siamese_eater", 18),
                   "xs15_4a9b88gzx311": ("?15?128", 18),
                   "xs15_4a9b88gzx321": ("001800280040003e0001000a000c", 18),
                   "xs15_031i4ozc8701": ("0180010300e1001200240018", 18),
                   "xs15_178kiar": ("?-amoeba_5,4,4", 19),
                   "xs15_ad1egma": ("0030004b002a00690006", 19),
                   "xs15_321fgka6": ("00b000d300150012000c", 19),
                   "xs15_3pm8628c": ("00c000ac002900530060", 19),
                   "xs15_6ags25ac": ("00300053009500ca0004", 19),
                   "xs15_39m861ac": ("00c400aa002900530020", 19),
                   "xs15_25b8o0ui": ("?-boat_with_tail_and_table", 19),
                   "xs15_3123cj96": ("00d600b50009000a0004", 19),
                   "xs15_3hu0ok46": ("long_hook_and_?-eater", 19),
                   "xs15_32ako0ui": ("boat_with_trans-tail_and_?-table", 19),
                   "xs15_35a8o0ui": ("boat_with_trans-tail_and_?-table", 19),
                   "xs15_31egu246": ("?-integral_on_snake", 19),
                   "xs15_69n842ac": ("006000a600a900530020", 19),
                   "xs15_cai3z3lo": ("[[2-long_snake attach eater]]", 19),
                   "xs15_32hu0okc": ("00a000d0001300150036", 19),
                   "xs15_ml56z1ac": ("?-cap_and_long_snake", 19),
                   "xs15_3146pb8o": ("00cc00940030000f0009", 19),
                   "xs15_c9jz6a9o": ("03000133014900cc", 19),
                   "xs15_j5ozd54c": ("long_shillelagh_and_?-table", 19),
                   "xs15_0jhe8zbc1": ("?-shillelagh_on_eater", 19),
                   "xs15_6ic0f9z32": ("long_shillelagh_and_?-table", 19),
                   "xs15_3pmzw34a6": ("0180013000dc000200050006", 19),
                   "xs15_352sgc48c": ("?-boat_with_trans-tail_on_snake", 19),
                   "xs15_8u15acz32": ("0068005e00010005000a000c", 19),
                   "xs15_08o652zrm": ("?-carrier_on_boat_siamese_snake", 19),
                   "xs15_2ege12453": ("0190012b00ca000a0004", 19),
                   "xs15_o5r8b5z01": ("?15?172", 19),
                   "xs15_4a60uh246": ("00300012019501560020", 19),
                   "xs15_25b8og853": ("?-boat_with_cis-tail_siamese_canoe", 19),
                   "xs15_0bq2sgz65": ("?-trans-legs_and_long_snake", 19),
                   "xs15_2ld2koz32": ("00620055000d000200140018", 19),
                   "xs15_6248hf0cc": ("0030002301a501a80010", 19),
                   "xs15_3hu0og84c": ("long_eater_and_?-long_snake", 19),
                   "xs15_330fh8426": ("01b001a3002500280010", 19),
                   "xs15_354cgs246": ("?-snake_eater_on_eater", 19),
                   "xs15_39m86248c": ("01800158005500a30040", 19),
                   "xs15_69ajkk8zx1": ("0028005800460031000e0008", 19),
                   "xs15_4a9mgmazx1": ("hook_with_tail at loaf", 19),
                   "xs15_g8idicz123": ("?-tub_siamese_beehive_on_R-bee", 19),
                   "xs15_c88e123z33": ("?-snake_eater_siamese_table_and_trans-block", 19),
                   "xs15_3pczw23ck8": ("?-boat_on_carrier_siamese_carrier", 19),
                   "xs15_3lkaa4z121": ("006200550016002800280010", 19),
                   "xs15_0g8kiarz23": ("?-amoeba_5,5,4", 19),
                   "xs15_4al9aczw23": ("00180028004b005500280010", 19),
                   "xs15_03hik8z696": ("00c0012300d1001200140008", 19),
                   "xs15_08u15a4z65": ("00c000a8001e00010005000a0004", 19),
                   "xs15_9f0c4ozx65": ("long_shillelagh_and_?-table", 19),
                   "xs15_0gs252z1qm": ("01000280010000ed002b0010", 19),
                   "xs15_09v04a6z32": ("?-table_siamese_carrier_and_trans-boat", 19),
                   "xs15_0gil96z1ac": ("00c001200150009300150008", 19),
                   "xs15_0c88b5z653": ("?15?109", 19),
                   "xs15_4aarzx1256": ("?-boat_with_trans-tail_siamese_hat", 19),
                   "xs15_6ao8a52z32": ("?-tub_with_long_nine_siamese_carrier", 19),
                   "xs15_gs2552z1ac": ("?-beehive_with_tail_siamese_long_snake", 19),
                   "xs15_3iab8oz121": ("tub_with_long_leg_and_?-table", 19),
                   "xs15_259abgzx65": ("004000a00090005300d50008", 19),
                   "xs15_0ml9a4z321": ("0060005600350009000a0004", 19),
                   "xs15_32arzx1256": ("boat_with_trans-tail_and_?-table", 19),
                   "xs15_3pmzw34213": ("00c00098006e0001000200040006", 19),
                   "xs15_69eg8oz321": ("?-R-bee_on_very_long_snake", 19),
                   "xs15_178czw3553": ("cap_and_?-eater", 19),
                   "xs15_3pczw1178c": ("?-elevener_siamese_carrier", 19),
                   "xs15_25iczx1178c": ("?15?101", 19),
                   "xs15_0gba96z1252": ("00600090005200d5000a0004", 19),
                   "xs15_4ai3146z321": ("0064004a00320003000100040006", 19),
                   "xs15_358gzx23cko": ("very_very_long_snake_on_ship", 19),
                   "xs15_cq23z012156": ("?15?156", 19),
                   "xs15_xgs252zca43": ("?15?160", 19),
                   "xs15_69jzx1248a6": ("00c001400100008000400020001300090006", 19),
                   "xs15_wggs253z256": ("?-boat_with_cis-tail_siamese_boat_with_trans-tail", 19),
                   "xs15_08k453z259c": ("0180014000430059002a0004", 19),
                   "xs15_69abgzx1252": ("00600090005000d4000a00050002", 19),
                   "xs15_04al56z2521": ("006000a000ac005200250002", 19),
                   "xs15_ciligzx1074": ("008000e00010003200150012000c", 19),
                   "xs15_0o4a52z354c": ("?-barge_with_trans-tail_siamese_eater", 19),
                   "xs15_wggraa4z252": ("?-tub_with_tail_siamese_hat", 19),
                   "xs15_178czw31156": ("long_hook_and_?-eater", 19),
                   "xs15_25ao8a6z032": ("?-eater_siamese_carrier_on_tub", 19),
                   "xs15_4a4o796zw11": ("?-tub_with_leg_on_R-bee", 19),
                   "xs15_wggs252zc96": ("0180012000d00010001c000200050002", 19),
                   "xs15_wgs25a4z643": ("?-barge_with_cis-tail_siamese_eater", 19),
                   "xs15_0g8ka52zc96": ("0180013000c80014000a00050002", 19),
                   "xs15_wo4k871z6221": ("loaf_and_trans-tails", 19),
                   "xs15_031i4oz4a611": ("?-cis-shillelagh_on_boat", 19),
                   "xs15_4ai3146zx123": ("00300028000400020061004e0018", 19),
                   "xs15_xg8ge13z4a43": ("018001400040005000280008000a00050002", 19),
                   "xs15_xggka52z4a52": ("0080014000a0005000100014000a00050002", 19),
                   "xs15_256o8gzy212ko": ("boat_on_very_long_canoe", 19),
                   "xs15_3lo0uic": ("long_snake_and_?-cap", 20),
                   "xs15_3pmzcip": ("?-long_shillelagh_siamese_shillelagh", 20),
                   "xs15_69jc48a6": ("?15?168", 20),
                   "xs15_62461tic": ("006000a000ad004b0030", 20),
                   "xs15_31461tic": ("00cc0092003500050006", 20),
                   "xs15_3pm86246": ("00c000ad002b00500060", 20),
                   "xs15_0cq23zrm": ("?-eater_siamese_carrier_siamese_snake", 20),
                   "xs15_0drz69ko": ("?-boat_with_very_long_tail_siamese_snake", 20),
                   "xs15_178kc0f9": ("00c30042005a00d40008", 20),
                   "xs15_2llicz56": ("00a200d500150012000c", 20),
                   "xs15_31eozcip": ("?-very_long_shillelagh_siamese_eater", 20),
                   "xs15_32qjc48c": ("?15?120", 20),
                   "xs15_g8jdzpic": ("?15?153", 20),
                   "xs15_6248c2dic": ("00800158015500a30040", 20),
                   "xs15_9v04acz32": ("?-table_siamese_snake_and_boat", 20),
                   "xs15_0gjlozc96": ("0180013000d300150018", 20),
                   "xs15_8o6picz23": ("00480078000600190012000c", 20),
                   "xs15_5bo8a6z32": ("0065004b00180008000a0006", 20),
                   "xs15_3146178ko": ("01980128006a00050003", 20),
                   "xs15_3146178kc": ("?-boat_with_cis-tail_on_carrier", 20),
                   "xs15_31eoz4a9o": ("0318012e01410083", 20),
                   "xs15_djozx354c": ("0180008000a0006000180013000d", 20),
                   "xs15_0ml56zca1": ("01800156003500050006", 20),
                   "xs15_wok453zdb": ("01a0016000180014000400050003", 20),
                   "xs15_j5ka53z11": ("003300290016000800050003", 20),
                   "xs15_69q453z32": ("00660049001a000400050003", 20),
                   "xs15_356o8gka4": ("?-tub_with_long_tail_on_ship", 20),
                   "xs15_c9jz358go": ("03000200011300a9006c", 20),
                   "xs15_woka52zdb": ("?-very_long_boat_on_snake", 20),
                   "xs15_31ege1246": ("01880155005300500020", 20),
                   "xs15_djozx31e8": ("016001900030000c000800070001", 20),
                   "xs15_j5o0uiz11": ("shillelagh_and_?-table", 20),
                   "xs15_0bq23z69c": ("0180008000b301a90006", 20),
                   "xs15_0ci52zojd": ("?-tub_with_long_tail_siamese_shillelagh", 20),
                   "xs15_gild2koz1": ("004000730009001a00240018", 20),
                   "xs15_35a842ako": ("0180014c009200650003", 20),
                   "xs15_3pmzx32ac": ("0180014000400060001600190003", 20),
                   "xs15_mkhjz1w252": ("tub_with_long_leg_and_?-snake", 20),
                   "xs15_g84213zdjo": ("?-long_canoe_siamese_shillelagh", 20),
                   "xs15_ckl3zx3213": ("006000200040006300150014000c", 20),
                   "xs15_db0ga6z311": ("006d002b00200010000a0006", 20),
                   "xs15_32hjkcz032": ("?-integral_on_snake", 20),
                   "xs15_kq23zw35a4": ("?-snake_eater_on_long_boat", 20),
                   "xs15_09v04acz32": ("?-carrier_siamese_table_and_?-boat", 20),
                   "xs15_32qbzx1156": ("integral_and_?-table", 20),
                   "xs15_3lozha6z11": ("0623055500d8", 20),
                   "xs15_wgila4z696": ("?-barge_line_beehive", 20),
                   "xs15_03iakoz643": ("?-boat_with_trans-tail_and_nine", 20),
                   "xs15_08u15acz32": ("00600048001e00010005000a000c", 20),
                   "xs15_g8idioz123": ("003000480072000d00120018", 20),
                   "xs15_0cilicz321": ("0060004c003200150012000c", 20),
                   "xs15_0ra246z643": ("?-shillelagh_and_bookend", 20),
                   "xs15_25iczwd54c": ("0180008000ac01b200050002", 20),
                   "xs15_0o48a52zbd": ("016001b800040008000a00050002", 20),
                   "xs15_2l2s53z121": ("00600050001c002200550022", 20),
                   "xs15_ca9jzw1256": ("00c000a000530029000a000c", 20),
                   "xs15_rai3zx1246": ("very_very_long_snake_and_?-table", 20),
                   "xs15_gs25acz146": ("0030009c00c20005000a000c", 20),
                   "xs15_ciab8oz023": ("00180025002b00680008000c", 20),
                   "xs15_6iog853z32": ("0066005200180010000800050003", 20),
                   "xs15_354q96zx23": ("006000500010002d004b0030", 20),
                   "xs15_ci5diczw11": ("000c0012002d00290012000c", 20),
                   "xs15_ckl3zw3426": ("?-snake_eater_on_eater", 20),
                   "xs15_3lk48cz056": ("00c000ad002b002000100030", 20),
                   "xs15_bdggma4zw1": ("0060004600250062001c0010", 20),
                   "xs15_35a8og8426": ("03000283010500e80030", 20),
                   "xs15_3p6o8a6zw1": ("006000530011002e00280010", 20),
                   "xs15_cp3z230352": ("?-table_siamese_carrier_and_trans-boat", 20),
                   "xs15_ck3123z643": ("00cc00940063000100020003", 20),
                   "xs15_08kaarz321": ("006c00280028001600090003", 20),
                   "xs15_354m96zw32": ("?15?147", 20),
                   "xs15_6agwrdzx121": ("?-cis-long_hook_with_tail_siamese_snake", 20),
                   "xs15_0g8k871zbc1": ("0160019000280014000800070001", 20),
                   "xs15_035ak8z6511": ("00c000a30025002a00140008", 20),
                   "xs15_0gba952z123": ("?15?140", 20),
                   "xs15_4ap3zw12552": ("004000a000a000430039000a0004", 20),
                   "xs15_08o653z254c": ("0180014000c30032002a0004", 20),
                   "xs15_0352sgz6413": ("?-boat_with_trans-tail_on_carrier", 20),
                   "xs15_0j5s246z121": ("00300025001b0008002800500020", 20),
                   "xs15_178k453zx23": ("?-amoeba_6,4,4", 20),
                   "xs15_8kih3zx34a4": ("0080014000830071001200140008", 20),
                   "xs15_039cz3115a4": ("tub_with_long_leg_and_?-carrier", 20),
                   "xs15_255q826zx23": ("0030004b0031000c00080004000c", 20),
                   "xs15_g84213zd54c": ("long_canoe_and_cis-table", 20),
                   "xs15_wg8oge13z65": ("01800140004000580034000200010003", 20),
                   "xs15_0178kcz6511": ("00c000a1002700280014000c", 20),
                   "xs15_31eozx125a4": ("?-barge_with_trans_tail_siamese_eater", 20),
                   "xs15_0gila4z12ko": ("0080014002a3012500280010", 20),
                   "xs15_0j5s252z121": ("00320025001a0008002800500020", 20),
                   "xs15_354kozx12ko": ("03000280008000b0006800050003", 20),
                   "xs15_0g8kc0f9z23": ("boat_with_trans-tail_and_?-table", 20),
                   "xs15_4a4o79czw11": ("?-tub_with_leg_on_hook", 20),
                   "xs15_32qkzx34213": ("00c000400058002e0001000200040006", 20),
                   "xs15_0252sgz4a53": ("?-tub_with_tail_on_long_boat", 20),
                   "xs15_wck31e8z311": ("?-snake_eater_on_eater", 20),
                   "xs15_0g8ka52zbc1": ("0160019000280014000a00050002", 20),
                   "xs15_4ap3zw12156": ("00c000a0002000430039000a0004", 20),
                   "xs15_312kozxc871": ("01800100008000530031000e0008", 20),
                   "xs15_c93s4zx1252": ("?-tub_with_long_leg_on_carrier", 20),
                   "xs15_3lk48cz0146": ("00c000ac0029002300100030", 20),
                   "xs15_08p78k8z321": ("?-tub_with_tail_on_hook", 20),
                   "xs15_wggka23z696": ("0180008000a000500010001600090006", 20),
                   "xs15_8kk8a52z641": ("00c8009400340008000a00050002", 20),
                   "xs15_08o652z69k8": ("01000280018200650052000c", 20),
                   "xs15_3pa4zw12453": ("00c0009800540022000100050006", 20),
                   "xs15_0o8a52zc453": ("0180009800a8006a00050002", 20),
                   "xs15_8kk3123z641": ("?15?146", 20),
                   "xs15_312kozy135a4": ("canoe_on_long_boat", 20),
                   "xs15_xg8o652z4a43": ("tub_with_nine_on_boat", 20),
                   "xs15_0c4oa52z2521": ("?-tub_with_long_tail_siamese_tub_with_tail", 20),
                   "xs15_g84213z178k8": ("0300020201050082005c0030", 20),
                   "xs15_69jwo4czx121": ("006000a000830045002400140008", 20),
                   "xs15_w8ka952z2521": ("00600090004800340008000a00050002", 20),
                   "xs15_25ao4a4z0321": ("?-tubs_on_hook", 20),
                   "xs15_xggka23z4a43": ("0180008000a000500010001c000200050002", 20),
                   "xs16_j1u0696z11": ("beehive on dock", 0),
                   "xs16_69egmiczx1": ("scorpion", 1),
                   "xs16_69bob96": ("symmetric scorpion", 4),
                   "xs16_259e0e952": ("cis-mirrored R-loaf", 5),
                   "xs16_g88m996z1221": ("bipond", 0),
                   "xs16_3hu0uh3": ("cis-mirrored longhook", 6),
                   "xs16_69960uic": ("pond and cap", 6),
                   "xs16_3lk453z321": ("trans-ship and dock", 6),
                   "xs16_0ca952z2553": ("trans-R-bee and R-mango", 6),
                   "xs16_0ggca96z3443": ("pond on R-loaf", 6),
                   "xs16_39e0ehr": ("hook and C", 7),
                   "xs16_697079ic": ("cis-R-bee and R-mango", 7),
                   "xs16_69is0si6": ("cis-hook and R-mango", 7),
                   "xs16_j1u0uiz11": ("table and dock", 7),
                   "xs16_j1u06acz11": ("cis-ship and dock", 7),
                   "xs16_259aczx6513": ("para-hook and R-havoc", 7),
                   "xs16_m2s079cz11": ("para-hook and C", 8),
                   "xs16_0ggs2qrz32": ("?16?007", 8),
                   "xs16_c4o0e96z321": ("ortho-R-bee and C", 8),
                   "xs16_0g8o69a4z3421": ("loaf on R-mango", 8),
                   "xs16_69e0ehr": ("R-bee and C", 9),
                   "xs16_69f0f96": ("mirrored_cap", 9),
                   "xs16_69is079c": ("?16?021", 9),
                   "xs16_0mp2sgz643": ("?16?055", 9),
                   "xs16_4aab96z033": ("?16?022", 9),
                   "xs16_0ca952z6513": ("trans-hook and R-mango", 9),
                   "xs16_08o0ehrz321": ("ortho-hook and C", 9),
                   "xs16_69ngbr": ("?16?036", 10),
                   "xs16_356o8br": ("?16?057", 10),
                   "xs16_3hu06996": ("?16?073", 10),
                   "xs16_259e0eik8": ("?16?093", 10),
                   "xs16_gbbo8a6z11": ("?16?019", 10),
                   "xs16_j1u06ioz11": ("para-aircraft and dock", 10),
                   "xs16_2ege96z321": ("?16?034", 10),
                   "xs16_4aab96zx33": ("?16?016", 10),
                   "xs16_08o6hrz643": ("?16?018", 10),
                   "xs16_39egmiczx1": ("?16?013", 10),
                   "xs16_c4gf96z321": ("?16?076", 10),
                   "xs16_0gjlicz346": ("?16?026", 10),
                   "xs16_0g8o653zbc1": ("ship_on_boat with longtail", 10),
                   "xs16_0mk453z3443": ("?16?056", 10),
                   "xs16_69b88czw652": ("?16?064", 10),
                   "xs16_0c8a53z2553": ("?16?015", 10),
                   "xs16_39s0ca4z321": ("?16?124", 10),
                   "xs16_g88q596z1221": ("?16?078", 10),
                   "xs16_0g8ka952z3421": ("?16?071", 10),
                   "xs16_3hu0uic": ("cap and longhook", 11),
                   "xs16_31egu156": ("?16?074", 11),
                   "xs16_259aria4": ("?16?100", 11),
                   "xs16_35is0sic": ("?16?045", 11),
                   "xs16_c9b871z33": ("?16?092", 11),
                   "xs16_xoka53z653": ("?16?152", 11),
                   "xs16_0jhu0ooz32": ("?16?042", 11),
                   "xs16_69baiczx32": ("?16?108", 11),
                   "xs16_c4o79cz321": ("?16?040", 11),
                   "xs16_gbap56z121": ("?16?038", 11),
                   "xs16_09v0ca4z321": ("?16?050", 11),
                   "xs16_3iaj2acz011": ("?16?043", 11),
                   "xs16_0259acz6513": ("?16?052", 11),
                   "xs16_wg0si96z2543": ("?16?033", 11),
                   "xs16_031e8gz8k871": ("?16?069", 11),
                   "xs16_1no3qic": ("?16?020", 12),
                   "xs16_69ara96": ("?16?062", 12),
                   "xs16_35a8ob96": ("?16?072", 12),
                   "xs16_35is0si6": ("?16?031", 12),
                   "xs16_raarzx123": ("?16?060", 12),
                   "xs16_h7ob96z11": ("?16?030", 12),
                   "xs16_mkhf0ccz1": ("?16?104", 12),
                   "xs16_0gjlkcz346": ("?16?027", 12),
                   "xs16_oggm952z66": ("?16?068", 12),
                   "xs16_69ligozw66": ("?16?035", 12),
                   "xs16_0c8a53z6513": ("?16?175", 12),
                   "xs16_0j1u0ooz321": ("?16?086", 12),
                   "xs16_8o6p96z1221": ("?16?103", 12),
                   "xs16_0c8a52z6953": ("?16?049", 12),
                   "xs16_xca952z2553": ("?16?006", 12),
                   "xs16_xca952z6513": ("?16?084", 12),
                   "xs16_gs2ib8ozx32": ("?16?032", 12),
                   "xs16_259mggozx66": ("?16?171", 12),
                   "xs16_0j1u066z321": ("?16?066", 12),
                   "xs16_0259acz2553": ("?16?029", 12),
                   "xs16_g88e13z178c": ("?16?028", 12),
                   "xs16_w8k8a53z6521": ("?16?011", 12),
                   "xs16_6ags2qr": ("?16?044", 13),
                   "xs16_259araa4": ("[[mango fuse hat]]", 13),
                   "xs16_358e1dio": ("?16?192", 13),
                   "xs16_6970si96": ("?16?159", 13),
                   "xs16_253gv1oo": ("[[cis-boat and long_Z and block]]", 13),
                   "xs16_ogil96z66": ("cis-loaf_with_long_leg_and_trans-block", 13),
                   "xs16_25is0sia4": ("?16?094", 13),
                   "xs16_25is0si52": ("?16?167", 13),
                   "xs16_mmge1e8z1": ("?16?088", 13),
                   "xs16_4a970sia4": ("?16?063", 13),
                   "xs16_69aczx3596": ("?16?023", 13),
                   "xs16_02llicz643": ("?16?090", 13),
                   "xs16_69aczw6953": ("?16?046", 13),
                   "xs16_6a88brzx32": ("?16?149", 13),
                   "xs16_62s0f9z321": ("?16?140", 13),
                   "xs16_6a88b52z033": ("?16?037", 13),
                   "xs16_697o4iczx11": ("?16?098", 13),
                   "xs16_8e1t6zx1252": ("?16?119", 13),
                   "xs16_69b88czw256": ("?16?067", 13),
                   "xs16_0j9m4koz121": ("?16?095", 13),
                   "xs16_354kmzx1256": ("?16?134", 13),
                   "xs16_0gilicz34a4": ("00600090015200950012000c", 13),
                   "xs16_0c93z651156": ("ortho-aircraft and dock", 13),
                   "xs16_039m4koz311": ("?16?097", 13),
                   "xs16_35a8czx6513": ("?16?048", 13),
                   "xs16_69p64k8zw121": ("?16?137", 13),
                   "xs16_25b8ob96": ("?16?138", 14),
                   "xs16_178f1ego": ("?16?116", 14),
                   "xs16_cim453z641": ("?16?125", 14),
                   "xs16_m2s0796z11": ("?16?113", 14),
                   "xs16_39cz651156": ("?16?133", 14),
                   "xs16_ca2s53z311": ("?16?183", 14),
                   "xs16_0pf033z643": ("?16?178", 14),
                   "xs16_69b88gzxbd": ("00c0012001a0002d002b0010", 14),
                   "xs16_35s2acz321": ("?-long_integral_siamese_long_hook", 14),
                   "xs16_03l2sgz2543": ("?16?085", 14),
                   "xs16_259aczx2553": ("?16?169", 14),
                   "xs16_69mggoz04a6": ("?16?163", 14),
                   "xs16_08u1egoz321": ("0060005000130035001400140008", 14),
                   "xs16_o4id1egoz01": ("?16?181", 14),
                   "xs16_25b88a6zw33": ("?16?054", 14),
                   "xs16_0g0s2qrz321": ("?16?128", 14),
                   "xs16_09v0ck8z321": ("?16?102", 14),
                   "xs16_2552sgz0653": ("?16?107", 14),
                   "xs16_0c88a53z2552": ("?16?039", 14),
                   "xs16_wggci96z2543": ("mango on R-loaf", 14),
                   "xs16_0ggm9icz1243": ("003000480090006e0009000a0004", 14),
                   "xs16_0c88a52z2596": ("?16?123", 14),
                   "xs16_0g8id96z3421": ("?16?146", 14),
                   "xs16_69ari96": ("002a005d0041003a000c", 15),
                   "xs16_4a9r2pm": ("?16?111", 15),
                   "xs16_2ego3qic": ("006c00aa008200730010", 15),
                   "xs16_358e1dic": ("00cc0092005500350002", 15),
                   "xs16_35ac0f96": ("cap_and_cis-long_ship", 15),
                   "xs16_2ege132ac": ("?16?132", 15),
                   "xs16_cilmzx696": ("[[boat tied to beehive]]", 15),
                   "xs16_4aqb96z32": ("?-racetrack_siamese_carrier", 15),
                   "xs16_628c1fgkc": ("00c0012c01a900230030", 15),
                   "xs16_3lmge2z32": ("006300550034000400380020", 15),
                   "xs16_wgil96z696": ("?-beehive_line_loaf", 15),
                   "xs16_0md1e8z346": ("0060009600cd0001000e0008", 15),
                   "xs16_0bq2sgz643": ("?16?161", 15),
                   "xs16_gjlkk8z146": ("0030009300d5001400140008", 15),
                   "xs16_j5s2552z11": ("?16?187", 15),
                   "xs16_g88b96zc93": ("?16?131", 15),
                   "xs16_gilmz1w696": ("?16?075", 15),
                   "xs16_0jhu066z32": ("?-eater_siamese_long_hook_and_trans-block", 15),
                   "xs16_65lmge2zw1": ("?16?105", 15),
                   "xs16_mligz1w696": ("?16?065", 15),
                   "xs16_wml5a4z643": ("?16?158", 15),
                   "xs16_ci5t2sgzw1": ("?-mango-siamese_beehive_with_tail", 15),
                   "xs16_0c88brz253": ("Z_and_trans-boat_and_block", 15),
                   "xs16_2ege93z321": ("[[?16?198]]", 15),
                   "xs16_2llm853z01": ("?16?077", 15),
                   "xs16_03lkicz643": ("?16?135", 15),
                   "xs16_03lkk8z696": ("?16?182", 15),
                   "xs16_25iczw11d96": ("00c0012001a0002c003200050002", 15),
                   "xs16_g8id1egoz11": ("?16?147", 15),
                   "xs16_4s0v1e8zw11": ("?-long_Z_siamese_eaters", 15),
                   "xs16_wggm952z696": ("?16?188", 15),
                   "xs16_0gba96z3452": ("0060009000ab004a00090006", 15),
                   "xs16_0giu0696z32": ("?16?186", 15),
                   "xs16_2lla8cz1221": ("?16?118", 15),
                   "xs16_69iczx1178c": ("?-mango_with_trans_tail_siamese_eater", 15),
                   "xs16_g8hf0cicz11": ("?16?082", 15),
                   "xs16_xc8a53z6513": ("?16?112", 15),
                   "xs16_6a88a52z253": ("?16?110", 15),
                   "xs16_wg8ob96z643": ("[[integral siamese ?]]", 15),
                   "xs16_o4q552sgz01": ("cis-beehive_at_beehive_with_tail", 15),
                   "xs16_0cq1egoz321": ("?16?173", 15),
                   "xs16_c88q552z311": ("?16?017", 15),
                   "xs16_69iczx115ac": ("?-mango_line_boat", 15),
                   "xs16_0gbb871z123": ("[[cis-boat with ? tail on block]]", 15),
                   "xs16_0i5t2sgz121": ("?16?185", 15),
                   "xs16_4a9la4ozx121": ("?-mango_at_mango", 15),
                   "xs16_w8o69a4z6521": ("?-loaf_on_boat_with_leg", 15),
                   "xs16_wggca53z6521": ("long_ship_on_long_ship", 15),
                   "xs16_0j1u06a4z121": ("?16?191", 15),
                   "xs16_0gilmz32w252": ("tub_with_long_nine_and_cis-boat", 15),
                   "xs16_w8o6952z6521": ("?16?151", 15),
                   "xs16_0gil9a4z3421": ("?16?176", 15),
                   "xs16_0c88b52z2552": ("?16?165", 15),
                   "xs16_25a88a6z0253": ("tub_with_long_nine_and_ortho-boat", 15),
                   "xs16_4a5pa4ozx121": ("?-mango-siamese-mango_siamese_tub", 15),
                   "xs16_660uhar": ("00580068000b006b0050", 16),
                   "xs16_330fhar": ("006d006b0008000b0005", 16),
                   "xs16_5b8ra96": ("?-snake_eater_siamese_loop", 16),
                   "xs16_3lozraa4": ("?-hat_on_long_snake", 16),
                   "xs16_3hu0oka6": ("long_hook_and_para-long_ship", 16),
                   "xs16_259e0mp3": ("?16?025", 16),
                   "xs16_2ego2tic": ("?-tub_siamese_R-bee_and_eater", 16),
                   "xs16_35ako0ui": ("cis-very_long_ship_and_table", 16),
                   "xs16_2ege1dic": ("004400aa00aa004b0030", 16),
                   "xs16_35is079c": ("[[?16?200]]", 16),
                   "xs16_1787164ko": ("?16?051", 16),
                   "xs16_39u0ooz65": ("?-long_snake_siamese_hook_and_block", 16),
                   "xs16_0gs2pmz643": ("00c00090007c000200190016", 16),
                   "xs16_g2u0uh3z11": ("cis-rotated_long_hook", 16),
                   "xs16_0o4a952zbd": ("?16?142", 16),
                   "xs16_o4o7picz01": ("?-bookend_siamese_mango_on_beehive", 16),
                   "xs16_03lkk8zc96": ("?16?155", 16),
                   "xs16_0bq2koz643": ("00c0008b007a000200140018", 16),
                   "xs16_0mmge13z32": ("0060005600160010000e00010003", 16),
                   "xs16_02llicz652": ("00c000a2005500150012000c", 16),
                   "xs16_354miczx56": ("00c000a00020006d004b0030", 16),
                   "xs16_69ab8oz033": ("?16?160", 16),
                   "xs16_3lkm952z01": ("?-loaf_with_trans-tail_siamese_hook", 16),
                   "xs16_2l2s53z321": ("?16?194", 16),
                   "xs16_wgbqicz643": ("00c000800070000b001a0012000c", 16),
                   "xs16_wml1e8z643": ("00c00080007600150001000e0008", 16),
                   "xs16_3lkaa4z321": ("006300550034000a000a0004", 16),
                   "xs16_39u08k8z321": ("?16?114", 16),
                   "xs16_gill2z1w652": ("?16?172", 16),
                   "xs16_c4o79icz011": ("?16?179", 16),
                   "xs16_0c88a53z653": ("trans-boat_with_long_leg_and_trans-ship", 16),
                   "xs16_358gzx2fgkc": ("0300028000400028001e000100050006", 16),
                   "xs16_03lk46z6521": ("[[trans-long_ship-up on long hook]]", 16),
                   "xs16_4s0v1aczw11": ("00180028004b006a000a000c", 16),
                   "xs16_0oggm96z4a6": ("beehive_with_long_leg_and_trans-boat", 16),
                   "xs16_g8kkm96z121": ("beehive_siamese_long_beehive_siamese_beehive", 16),
                   "xs16_0g6pb8oz321": ("006000500029000f00100014000c", 16),
                   "xs16_0c9b8oz2552": ("?-Z_siamese_carrier_and_beehive", 16),
                   "xs16_4aab88czx33": ("001800180000007e0041000e0008", 16),
                   "xs16_35a88cz0653": ("[[trans-boat_with_long_leg and cis-ship-up]]", 16),
                   "xs16_69ic8a6zw23": ("003000480025001b000800280030", 16),
                   "xs16_ciabgzx1256": ("00c000a00050002b000a0012000c", 16),
                   "xs16_0gs2arz3421": ("?16?109", 16),
                   "xs16_039u0ooz311": ("?-eater_siamese_hook_and_cis-block", 16),
                   "xs16_0ml2sgz1243": ("?16?150", 16),
                   "xs16_69abgzx3452": ("00600090005000d6000900050002", 16),
                   "xs16_04s0f96z321": ("?16?024", 16),
                   "xs16_0co2d96z321": ("0060005000100036002500090006", 16),
                   "xs16_o4ic0fhoz01": ("long_hook_and_ortho-mango", 16),
                   "xs16_g88a53z178c": ("?-boat_with_trans-nine_siamese_eater", 16),
                   "xs16_g89f0cicz11": ("?-table_siamese_eater_and_beehive", 16),
                   "xs16_0mligoz1246": ("00200056009500d200100018", 16),
                   "xs16_wggm952zc96": ("0180012000d000100016000900050002", 16),
                   "xs16_04a96z4a5113": ("?16?122", 16),
                   "xs16_25a4ozx12596": ("00c0012000a000580024000a00050002", 16),
                   "xs16_w8o6996z2521": ("tub_with_leg_on_pond", 16),
                   "xs16_069a4oz4a511": ("0080014600a9002a00240018", 16),
                   "xs16_0c88a52z6952": ("tub_with_long_leg_and_shift-loaf", 16),
                   "xs16_256o8a6z0321": ("?-elevener_on_boat", 16),
                   "xs16_65pajkc": ("?-shillelagh_at_shillelagh", 17),
                   "xs16_5b8ri96": ("006a002d0041003a000c", 17),
                   "xs16_69araic": ("?16?089", 17),
                   "xs16_32qr2qk": ("?-snake_eater_siamese_table_and_block", 17),
                   "xs16_259e0djo": ("shillelagh_and_?-R-loaf", 17),
                   "xs16_178bp453": ("00db008a0062001c0010", 17),
                   "xs16_35ac0fho": ("long_hook_and_cis-long_ship", 17),
                   "xs16_69f0ci96": ("?16?153", 17),
                   "xs16_354cgn96": ("00c6008500750012000c", 17),
                   "xs16_178c2djo": ("?16?129", 17),
                   "xs16_178jt066": ("00d80053004b00280018", 17),
                   "xs16_3hu069ic": ("?16?106", 17),
                   "xs16_31ege1da": ("?16?139", 17),
                   "xs16_6426gu156": ("00c0012d01ab00200030", 17),
                   "xs16_3lkiarz01": ("003600140012000a002b0030", 17),
                   "xs16_gbhegoz123": ("R-bee_on_integral", 17),
                   "xs16_25t2s53zx1": ("006600490036001400140008", 17),
                   "xs16_39u06a4z32": ("?16?193", 17),
                   "xs16_3pczw23cko": ("?-carrier_siamese_carrier_on_ship", 17),
                   "xs16_c88a53z356": ("trans-boat_with_long_leg_and_?-ship", 17),
                   "xs16_oe132acz23": ("?-eater_siamese_eater_siamese_snake", 17),
                   "xs16_j9c8a6z123": ("?-scorpio_siamese_carrier", 17),
                   "xs16_69iczxd552": ("?16?144", 17),
                   "xs16_39m453z321": ("?16?121", 17),
                   "xs16_oggs253z66": ("?-boat_with_trans-tail_siamese_table_and_trans-block", 17),
                   "xs16_gbq2koz123": ("0030004b007a000200140018", 17),
                   "xs16_g88bqicz23": ("006000200046003d0001000e0008", 17),
                   "xs16_08u156z69c": ("00c00140010000f300290006", 17),
                   "xs16_3lka96z121": ("006200550016002800480030", 17),
                   "xs16_03lka6z643": ("?16?157", 17),
                   "xs16_3pmzw342ac": ("?-great_snake_eater_siamese_shillelagh", 17),
                   "xs16_699mgmazx1": ("snake_eater_on_pond", 17),
                   "xs16_oggka53z66": ("trans-long_boat_with_long_leg_and_trans-block", 17),
                   "xs16_03lkicz652": ("00c000a3005500140012000c", 17),
                   "xs16_caikm96zw1": ("?-beehive_with_tail_siamese_shillelagh", 17),
                   "xs16_c8al96z311": ("?16?184", 17),
                   "xs16_0dbz651156": ("?-dock_and_snake", 17),
                   "xs16_0jhegoz343": ("integral_on_R-bee", 17),
                   "xs16_0co2ticz32": ("0060004c00180002001d0012000c", 17),
                   "xs16_gjlmz1w256": ("trans-boat_with_long_leg_and_cis-ship", 17),
                   "xs16_09fgkcz253": ("004000a9006f00100014000c", 17),
                   "xs16_c88m952z311": ("?-hat_at_loaf", 17),
                   "xs16_ggml56z1221": ("trans-mirrored_cap", 17),
                   "xs16_04a952z3553": ("[[trans-mango on cap]]", 17),
                   "xs16_39u06a4z032": ("?-hook_siamese_snake_and_cis-boat", 17),
                   "xs16_3pabgzx1252": ("barge_with_leg_and_?-snake", 17),
                   "xs16_62s0c93z321": ("?16?164", 17),
                   "xs16_xok4871z653": ("?-great_snake_eater_on_ship", 17),
                   "xs16_g88b52z178c": ("[[cis-boat_integral siamese eater]]", 17),
                   "xs16_0o4a96z354c": ("?-loaf_with_trans-tail_siamese_eater", 17),
                   "xs16_wggka53z696": ("?-long_boat_line_beehive", 17),
                   "xs16_025a8cz6953": ("tub_with_leg_and_ortho-R-loaf", 17),
                   "xs16_31eozx12596": ("?-loaf_with_trans-tail_siamese_eater", 17),
                   "xs16_08kkm96z321": ("?-great_snake_eater_siamese_long_bee_siamese_beehive", 17),
                   "xs16_g8ie0djoz01": ("tub_with_leg_and_?-shillelagh", 17),
                   "xs16_3iacz1215a4": ("0188009400a8006a00050002", 17),
                   "xs16_0gilmz56w23": ("00a000d00012001500560060", 17),
                   "xs16_035a8cz2553": ("boat_with_leg_and_para-R-bee", 17),
                   "xs16_ggm9acz1243": ("?-R-loaf_on_R-loaf", 17),
                   "xs16_g6q0si52z11": ("?16?174", 17),
                   "xs16_g8jd0eicz01": ("tub_with_long_tail_and_?-R-bee", 17),
                   "xs16_wcid1e8z311": ("?-beehive_with_tail_and_bend_tail", 17),
                   "xs16_69diczx1252": ("0060009000b0004c003200050002", 17),
                   "xs16_0652sgz4a53": ("?-long_boat_on_boat_with_cis-tail", 17),
                   "xs16_wgs2596z643": ("?-loaf_with_cis-tail_siamese_eater", 17),
                   "xs16_39m88cz0643": ("00c000930069001600100030", 17),
                   "xs16_0mligoz1226": ("00200056005500d200100018", 17),
                   "xs16_4aarzx12552": ("?-beehive_with_tail_siamese_hat", 17),
                   "xs16_0mp3z122156": ("00c000a00023005900560020", 17),
                   "xs16_ca1t6zx1252": ("004000a00046003d0001000a000c", 17),
                   "xs16_62s0fhoz011": ("?-rotated_long_hook", 17),
                   "xs16_4a9b88czx33": ("?16?190", 17),
                   "xs16_035a8cz6513": ("boat_with_leg_and_para-hook", 17),
                   "xs16_2eg6p2sgzx1": ("0010002b004a005200d40008", 17),
                   "xs16_xggka52z4a96": ("?-barge_line_loaf", 17),
                   "xs16_695q84ozx121": ("003000480052002d0009000a0004", 17),
                   "xs16_031e8gzc4871": ("01800083010100ee00280010", 17),
                   "xs16_25akozy135a4": ("[[very_long_boat tie long_boat]]", 17),
                   "xs16_g8o651248goz01": ("?-very_very_long_shillelagh_on_boat", 17),
                   "xs16_3pq3pm": ("?-shillelagh_siamese_snake_and_block", 18),
                   "xs16_69ar9ic": ("002c005a0041003d000a", 18),
                   "xs16_5b8raic": ("?-snake_eater_siamese_loop", 18),
                   "xs16_3pm861ac": ("00c400aa002900530060", 18),
                   "xs16_32qjc453": ("00c9008f00700014000c", 18),
                   "xs16_25b8r9a4": ("006c00aa0041003e0008", 18),
                   "xs16_4ad1egma": ("00600096005500d2000c", 18),
                   "xs16_178bq2sg": ("rotated_trans-legs", 18),
                   "xs16_358go8br": ("?-canoe_siamese_table_and_block", 18),
                   "xs16_2egu178c": ("eaters_siamese_long_eater", 18),
                   "xs16_2ege1dio": ("00c400aa002a004b0030", 18),
                   "xs16_2egu15ac": ("00300053005500d2000c", 18),
                   "xs16_641vg356": ("?-Z_siamese_carrier_and_cis-ship", 18),
                   "xs16_25is079a4": ("tub_with_leg_and_?-R-loaf", 18),
                   "xs16_356o8gka6": ("?-boat_with_long_tail_on_ship", 18),
                   "xs16_358gu15a4": ("?16?166", 18),
                   "xs16_3lkq23z32": ("?-amoeba_7,4,4", 18),
                   "xs16_31eoz359c": ("0198012e00a10063", 18),
                   "xs16_mkid1e8z1": ("00400070000b006a0052000c", 18),
                   "xs16_0ml56zc96": ("?-shillelagh_and_cap", 18),
                   "xs16_358go4qic": ("01800106008900550036", 18),
                   "xs16_352sgc453": ("?-boat_with_trans-tail_on_eater", 18),
                   "xs16_358go0uic": ("cap_and_?-canoe", 18),
                   "xs16_ogjla4z66": ("cis-long_boat_with_long_leg_and_trans-block", 18),
                   "xs16_35421fgkc": ("0198012800cb00090006", 18),
                   "xs16_69n8jdzx1": ("?-tub_with_long_tail_at_R-bee", 18),
                   "xs16_354268m93": ("01830159005600a00040", 18),
                   "xs16_08o653zrm": ("?-ship_on_carrier_siamese_snake", 18),
                   "xs16_699mkiczx1": ("?-loop_siamese_pond", 18),
                   "xs16_0giliczc96": ("0180013000d200150012000c", 18),
                   "xs16_gjlmz1w652": ("cis-boat_with_long_leg_and_?-ship", 18),
                   "xs16_6530fpzx32": ("?-table_siamese_carrier_and_cis-ship", 18),
                   "xs16_4aljgozw66": ("cis-long_boat_with_long_leg_and_cis-block", 18),
                   "xs16_0md1egoz32": ("00600056000d0001000e00100018", 18),
                   "xs16_69r4koz023": ("[[?16?199]]", 18),
                   "xs16_0gbaarz123": ("cis-boat_with_long_leg_and_cis-table", 18),
                   "xs16_02llicz256": ("004000a200d500150012000c", 18),
                   "xs16_69iczwc953": ("00c0012000930069000a000c", 18),
                   "xs16_0ml2sgz643": ("boat_with_cis-tail_and_hook", 18),
                   "xs16_gilmz1w69c": ("0180012000d6001500120030", 18),
                   "xs16_32akl3zx65": ("?-amoeba_7,4,4", 18),
                   "xs16_6s1raa4zw1": ("?16?156", 18),
                   "xs16_h7o31e8z11": ("006c002a0022001300500060", 18),
                   "xs16_03pmzoge21": ("0300020301d900560020", 18),
                   "xs16_35aczw3553": ("?16?120", 18),
                   "xs16_g8o652zpic": ("very_long_integral_on_boat", 18),
                   "xs16_35s2s53zx1": ("small_ghost", 18),
                   "xs16_mligz1w69c": ("0180012000d0001200150036", 18),
                   "xs16_0jhegoz643": ("?-eater_on_integral", 18),
                   "xs16_rai31e8z01": ("?-eater_siamese_table_and_cis-boat", 18),
                   "xs16_8ehik8z643": ("00c8008e0071001200140008", 18),
                   "xs16_0bdz651156": ("dock_and_?-snake", 18),
                   "xs16_3pmzw34aa4": ("?-beehive_with_tail_siamese_shillelagh", 18),
                   "xs16_ci96zwd552": ("00600090012b00ca000a0004", 18),
                   "xs16_gjlmz1w346": ("?-eater_siamese_table_and_ship", 18),
                   "xs16_64pb8oz321": ("?-eater_siamese_table_on_carrier", 18),
                   "xs16_0c4gf9z6521": ("00c000ac00440030000f0009", 18),
                   "xs16_ca1u8zx1256": ("00c000a00048003e0001000a000c", 18),
                   "xs16_wggraicz252": ("?-tub_with_tail_siamese_loop", 18),
                   "xs16_0c88b52z653": ("cis-boat_with_long_leg_and_?-ship", 18),
                   "xs16_o8ge952z065": ("?-R-loaf_on_shillelagh", 18),
                   "xs16_c88c453z352": ("?-eater_siamese_table_and_boat", 18),
                   "xs16_69iczx11da4": ("?-mango_line_boat", 18),
                   "xs16_0ok453zca23": ("?-eater_on_integral", 18),
                   "xs16_69aczx315a4": ("?16?126", 18),
                   "xs16_32qbgzx1256": ("very_long_ship_and_?-table", 18),
                   "xs16_0o4a952z39c": ("?-mango_with_trans-tail_siamese_carrier", 18),
                   "xs16_0i5q453z321": ("0064004a00340008000a00050003", 18),
                   "xs16_62s0f96z011": ("?16?170", 18),
                   "xs16_ca1v0kczx11": ("00180028004b0069000a000c", 18),
                   "xs16_04al56z6521": ("00c000a4004a003500050006", 18),
                   "xs16_gs2596z1226": ("?16?091", 18),
                   "xs16_08u1da4z321": ("?16?096", 18),
                   "xs16_3iabkk8z011": ("004800780006001900260030", 18),
                   "xs16_25akozxc871": ("?-eater_on_very_long_boat", 18),
                   "xs16_259q453z032": ("006600490032000c000800020006", 18),
                   "xs16_8e1qczx1256": ("00c000a0004c003a0001000e0008", 18),
                   "xs16_0co2dioz321": ("00600050001300350024000a0004", 18),
                   "xs16_ci96zw1178c": ("?-mango_with_cis-tail_siamese_eater", 18),
                   "xs16_xc8a53z2553": ("boat_with_leg_and_meta-R-bee", 18),
                   "xs16_039m853z311": ("0066004a00280014000800070001", 18),
                   "xs16_cc0v9zx1252": ("?-tub_with_leg_siamese_table_and_block", 18),
                   "xs16_069ak8zc871": ("?-loaf_siamese_tub_on_eater", 18),
                   "xs16_256o696zx23": ("003000480033000d003000500020", 18),
                   "xs16_ad1u8zx1252": ("?-tub_with_leg_siamese_loop", 18),
                   "xs16_o8gka52z643": ("?-barge_with_long_tail_siamese_C", 18),
                   "xs16_695q4ozw321": ("?-loaf_siamese_tub_siamese_beehive_siamese_boat", 18),
                   "xs16_xgil96z4a52": ("?-loaf_line_barge", 18),
                   "xs16_04s0fhoz321": ("trans-mirrored_long_hooks", 18),
                   "xs16_0gba952z343": ("00600090006b000a000900050002", 18),
                   "xs16_0o4a53z354c": ("?-long_boat_with_trans-tail_siamese_eater", 18),
                   "xs16_0cp3ck8z321": ("?-hook_siamese_carrier_on_boat", 18),
                   "xs16_08o0uh3z643": ("?-rotated_long_hooks", 18),
                   "xs16_0md1e8z1226": ("00200056004d00c1000e0008", 18),
                   "xs16_35akggozx66": ("trans-long_boat_with_long_leg_and_cis-block", 18),
                   "xs16_0352sgz4a53": ("?-boat_with_trans-tail_on_long_boat", 18),
                   "xs16_8kk31e8z641": ("00c80094003400030001000e0008", 18),
                   "xs16_09f0s4z6511": ("00c000a9002f0020001c0004", 18),
                   "xs16_25b88cz0653": ("cis-boat_with_long_leg_and_?-ship", 18),
                   "xs16_31e88cz0653": ("?-eater_siamese_table_and_ship", 18),
                   "xs16_2552sgz0c93": ("?-beehive_with_tail_on_carrier", 18),
                   "xs16_69p6426z032": ("?-pond_siamese_snakes", 18),
                   "xs16_ciljgzx1074": ("008000e00010003300150012000c", 18),
                   "xs16_0cq1da4z321": ("006000500010003600250012000c", 18),
                   "xs16_039u066z311": ("?-eater_siamese_hook_and_trans-block", 18),
                   "xs16_35a8czx2553": ("boat_with_leg_and_shift-R-bee", 18),
                   "xs16_cip6gzx3452": ("004000a00090006600190012000c", 18),
                   "xs16_c88m552z311": ("?16?117", 18),
                   "xs16_0co2dicz321": ("00600050001200350025000a0004", 18),
                   "xs16_25iczw123ck8": ("0100028001800060004c003200050002", 18),
                   "xs16_178k8a6z0321": ("0060002300290016000800280030", 18),
                   "xs16_0ggraa4z1226": ("?-siamese_hats", 18),
                   "xs16_25aczw3115a4": ("?16?059", 18),
                   "xs16_w8ka952z6521": ("00c000a000500010002c001200090006", 18),
                   "xs16_312kozw12ego": ("?16?143", 18),
                   "xs16_04a96z3115a4": ("tub_with_long_leg_and_?-loaf", 18),
                   "xs16_25a88gzc8711": ("0182010500ea002800280010", 18),
                   "xs16_0oggka52z4a6": ("trans-barge_with_long_leg_and_?-boat", 18),
                   "xs16_xg8o652zca23": ("elevener_on_boat", 18),
                   "xs16_0256o8z69521": ("loaf_with_trans-tail_on_boat", 18),
                   "xs16_4a9mk46zx121": ("?16?081", 18),
                   "xs16_xggka52zca52": ("?-long_boat_line_barge", 18),
                   "xs16_252s0ccz2521": ("?16?168", 18),
                   "xs16_wg0si52z6943": ("tub_with_leg_on_mango", 18),
                   "xs16_4a9jc4ozx121": ("00180028004600350009000a0004", 18),
                   "xs16_04akl3zc8421": ("01800158005400a200410003", 18),
                   "xs16_25a84k8z06511": ("004000a300550014002400280010", 18),
                   "xs16_xg8ka52z4a611": ("very_very_long_boat_on_boat", 18),
                   "xs16_5b8r9ic": ("006c002a0041003d000a", 19),
                   "xs16_4a9r8jd": ("006c002a0041005e0028", 19),
                   "xs16_1no31ego": ("00d80054004400250063", 19),
                   "xs16_3lkczpi6": ("0323025500d4000c", 19),
                   "xs16_259ar9a4": ("006c009a0041003e0008", 19),
                   "xs16_3pq32156": ("00d600b9000300600060", 19),
                   "xs16_178bp2sg": ("00d800540042003a000b", 19),
                   "xs16_3iarzc96": ("?-long_integral_and_table", 19),
                   "xs16_gbb8ozdb": ("01b0016b000b00080018", 19),
                   "xs16_2egmd1e8": ("0030004b005a00d2000c", 19),
                   "xs16_178ka52sg": ("?-long_boat_with_tails", 19),
                   "xs16_2egu16413": ("0190012b006a000a000c", 19),
                   "xs16_6421fgka6": ("00600090015301950018", 19),
                   "xs16_32hv04aa4": ("?-carrier_siamese_table_and_beehive", 19),
                   "xs16_mkic0f9z1": ("loop_and_trans-table", 19),
                   "xs16_iu0696z56": ("?-table_siamese_snake_and_trans-beehive", 19),
                   "xs16_31246pb8o": ("018c01540030000f0009", 19),
                   "xs16_642138n96": ("?-R-bee_siamese_tub_and_long_snake", 19),
                   "xs16_4a5123qic": ("00c00142010500f2002c", 19),
                   "xs16_64213ob96": ("00d80155010300e00020", 19),
                   "xs16_25960uh23": ("014601a9002a00240060", 19),
                   "xs16_178kc32ac": ("?-boat_with_cis-tail_on_eater", 19),
                   "xs16_drz230356": ("00c000a000600000007b004d", 19),
                   "xs16_321fgc453": ("018d010b00e800280010", 19),
                   "xs16_25is079k8": ("?-rotated_tub_with_leg", 19),
                   "xs16_8o0o8brz23": ("?-table_and_table_and_block", 19),
                   "xs16_wgil96zc96": ("0180012000d00012001500090006", 19),
                   "xs16_cilmzx34a4": ("008001400080007600150012000c", 19),
                   "xs16_65lmzx34a4": ("cap_and_?-tub_with_tail", 19),
                   "xs16_djozx35426": ("?-siamese_shillelaghs", 19),
                   "xs16_69m453z321": ("006600490036000400050003", 19),
                   "xs16_64ljgozw56": ("0060002000ad00cb00080018", 19),
                   "xs16_03lkcz8k96": ("?-tub_with_long_tail_on_eater", 19),
                   "xs16_0gbaarz321": ("trans-boat_with_long_leg_and_cis-table", 19),
                   "xs16_8u15a4z346": ("0068009e00c10005000a0004", 19),
                   "xs16_g8idjoz123": ("003000480072000d00130018", 19),
                   "xs16_ggmd1egoz1": ("008000e30015003400240018", 19),
                   "xs16_c88e13z356": ("?-eater_siamese_table_and_ship", 19),
                   "xs16_354cgs248c": ("0300020801d500530030", 19),
                   "xs16_03lkicz256": ("004000a300d500140012000c", 19),
                   "xs16_39ege2z321": ("00630049003a000400380020", 19),
                   "xs16_0ml2sgz343": ("?-boat_with_cis-tail_and_R-bee", 19),
                   "xs16_2lla8oz321": ("006200550035000a00080018", 19),
                   "xs16_c4o796z321": ("?-R-bee_on_C", 19),
                   "xs16_c88b52z356": ("cis-boat_with_long_leg_and_?-ship", 19),
                   "xs16_0drz32c826": ("?-snake_siamese_carrier_on_carrier", 19),
                   "xs16_ggmlicz146": ("0030009000d600150012000c", 19),
                   "xs16_9f0s26z311": ("0069002f0020001c00020006", 19),
                   "xs16_ogkq23z6a4": ("?-snake_eater_siamese_table_and_?-block", 19),
                   "xs16_39c8a6z253": ("?-hook_siamese_carrier_and_?-boat", 19),
                   "xs16_g8jdicz123": ("?-beehive_siamese_boat_on_R-bee", 19),
                   "xs16_c8al56z311": ("?-R-bee_on_hat", 19),
                   "xs16_cilmzx1156": ("?-boat_with_bend_tail_siamese_eater", 19),
                   "xs16_5b88a6z253": ("00a200d50016001000500060", 19),
                   "xs16_c4lb8oz321": ("006c00440035000b00080018", 19),
                   "xs16_8kid96z641": ("?-loaf_siamese_loaf_siamese_carrier", 19),
                   "xs16_wmp2sgz643": ("00c00080007600190002001c0010", 19),
                   "xs16_ckl3zw34ac": ("?-boat_with_trans-tail_on_eater", 19),
                   "xs16_cilmzx25a4": ("0080014000a0005600150012000c", 19),
                   "xs16_6a88b5z253": ("00a000d00010001600550062", 19),
                   "xs16_8k4r2pmzw1": ("0028005800460029006a0004", 19),
                   "xs16_178bbgzx65": ("008000e0001000d300d50008", 19),
                   "xs16_j9q32acz01": ("?-eater_siamese_snake_and_boat", 19),
                   "xs16_q6ge1daz01": ("0030004b002a006900050002", 19),
                   "xs16_3iab96z121": ("00620025002a006800480030", 19),
                   "xs16_ci96zw115ac": ("?-mango_line_boat", 19),
                   "xs16_0j9m453z121": ("0066004a00380004000a00050002", 19),
                   "xs16_oggo8a52z66": ("?-tub_with_tail_siamese_table_and_trans-block", 19),
                   "xs16_9f0s4zx1256": ("00c000a00044003c0000000f0009", 19),
                   "xs16_0c88b5z2596": ("014001a000260029006a0004", 19),
                   "xs16_259q453zw32": ("006600490032000c00080004000c", 19),
                   "xs16_c48c93z2552": ("?-carrier_siamese_snake_and_beehive", 19),
                   "xs16_g88e1daz056": ("005000b000800070001300150008", 19),
                   "xs16_03lkia4z252": ("004000a3005500140012000a0004", 19),
                   "xs16_wggs253z696": ("01800140008000700010001600090006", 19),
                   "xs16_c88q552z065": ("004000a000a00058001500130030", 19),
                   "xs16_ci4o0uh3zw1": ("?16?130", 19),
                   "xs16_4ap3zw12596": ("?16?136", 19),
                   "xs16_g84qajoz121": ("003000480024001a000a00130018", 19),
                   "xs16_gs259a4z146": ("0030009c00c200050009000a0004", 19),
                   "xs16_0c88b5z6952": ("014001a00024002a00690006", 19),
                   "xs16_08u156z254c": ("00c00140010300f2002a0004", 19),
                   "xs16_8e13z3115a4": ("tub_with_long_leg_and_?-eater", 19),
                   "xs16_0gbq2sgz321": ("long_ship_and_trans-legs", 19),
                   "xs16_0rdzg0t6z11": ("?-eater_siamese_long_snake_siamese_snake", 19),
                   "xs16_c88a52z35a4": ("tub_with_long_leg_and_para-long_boat", 19),
                   "xs16_g8jd0eioz01": ("tub_with_long_tail_and_?-hook", 19),
                   "xs16_2ege9a4zw23": ("002000380005003b004800280010", 19),
                   "xs16_c93s4zx1253": ("?-cis-boat_with_long_leg_on_carrier", 19),
                   "xs16_c93s4zx1256": ("?-trans-boat_with_long_leg_on_carrier", 19),
                   "xs16_g8idik8z123": ("?-loaf_siamese_tub_on_R-bee", 19),
                   "xs16_0g8o652zpi6": ("0320025000c80018000600050002", 19),
                   "xs16_3146248c453": ("?-eater_siamese_long_snake_siamese_carrier", 19),
                   "xs16_35ao8a6z032": ("?-trans-boat_with_long_nine_siamese_carrier", 19),
                   "xs16_xgil96z4a43": ("?-cis-loaf_with_tail_siamese_tub_with_tail", 19),
                   "xs16_0cp3z643033": ("?16?115", 19),
                   "xs16_0gilmz32w65": ("00a000d60015001200500060", 19),
                   "xs16_32qczx23ck8": ("03000100016000c80018000600050002", 19),
                   "xs16_g88r2qkz121": ("?-snake_eater_and_R-loaf", 19),
                   "xs16_ciaj2ak8zw1": ("0020005200a50082007c0010", 19),
                   "xs16_02l2sgz6943": ("?-tub_with_tail_on_mango", 19),
                   "xs16_c88b9czw352": ("0030009200d5001600100030", 19),
                   "xs16_caab8oz0252": ("?-long_Z_siamese_eater_and_tub", 19),
                   "xs16_8e1u8zx1256": ("?16?189", 19),
                   "xs16_gilmz1w1156": ("?-eater_siamese_table_and_boat", 19),
                   "xs16_c48a52z6513": ("tub_with_long_tail_and_?-hook", 19),
                   "xs16_0g8o653zc96": ("long_integral_on_ship", 19),
                   "xs16_08p7871z321": ("?-hook_on_hat", 19),
                   "xs16_0j5s256z121": ("00320025001b0008002800500020", 19),
                   "xs16_312kozx6aa6": ("canoe_and_?-cap", 19),
                   "xs16_3i1u066z121": ("006200250042003c000000300030", 19),
                   "xs16_mligz1w34a4": ("?-tub_with_leg_siamese_carrier_and_?-boat", 19),
                   "xs16_03lk48cz643": ("00c000830075001400040008000c", 19),
                   "xs16_69la4zx1156": ("barge_with_cis-nine_siamese_loaf", 19),
                   "xs16_0jhe853z121": ("0066004a00280018000600050002", 19),
                   "xs16_0354kozca23": ("?-integral_on_eater", 19),
                   "xs16_8kkl3zx1156": ("00c000a000230035001400140008", 19),
                   "xs16_25a8czw315a4": ("?-rotated-tub_with_leg", 19),
                   "xs16_8kai3zw125a4": ("0080014000a30052002a00140008", 19),
                   "xs16_25a8czw4a513": ("?-mirrored_tub_with_leg", 19),
                   "xs16_04all2zc8421": ("01800104008a005500350002", 19),
                   "xs16_4aajk46zx121": ("0030001200150066002800280010", 19),
                   "xs16_05b88gzc8711": ("0180010500eb002800280010", 19),
                   "xs16_04s0ci96z321": ("long_hook_and_trans-mango", 19),
                   "xs16_wck8a52z6521": ("[[?16?197]]", 19),
                   "xs16_25a88gz4ad11": ("?-binocle_boat_tub", 19),
                   "xs16_4aajk4ozx121": ("0018002400540033000a000a0004", 19),
                   "xs16_039s0ccz2521": ("?-tub_with_leg_siamese_carrier_and_block", 19),
                   "xs16_256o8gzca221": ("018201450046005800280010", 19),
                   "xs16_0g8p78cz3421": ("?-eater_on_R-mango", 19),
                   "xs16_xggm952z4a43": ("?16?148", 19),
                   "xs16_178kozy135a4": ("0180008000a000500030000c000a00050002", 19),
                   "xs16_31km9a4z0121": ("?-loaf_siamese_carrier_on_boat", 19),
                   "xs16_xg8o653z4a43": ("tub_with_nine_on_ship", 19),
                   "xs16_0256o8zca521": ("?-long_boat_with_trans-tail_on_boat", 19),
                   "xs16_wg6p2sgz2521": ("004000a00050002b000a001200140008", 19),
                   "xs16_25a88gzca511": ("?-binocle_tub_boat", 19),
                   "xs16_69ab88gzx311": ("003000480028006b000a000a0004", 19),
                   "xs16_xg8ge13z4a611": ("?-boat_on_boat_with_nine", 19),
                   "xs16_xg8k871z4a611": ("?-long_boat_with_tail_on_boat", 19),
                   "xs16_xg8ge13zca221": ("?-tub_with_nines", 19),
                   "xs16_69f03pm": ("?-shillelagh_and_cap", 20),
                   "xs16_9f032qr": ("?-tables_and_block", 20),
                   "xs16_69ir9ic": ("002c005a0041002d001a", 20),
                   "xs16_321fgbr": ("006d006b000800680050", 20),
                   "xs16_3lkcz1qm": ("031002ab00ad00c0", 20),
                   "xs16_3213on96": ("?-R-bee_siamese_boat_and_snake", 20),
                   "xs16_25a8objo": ("00d000bc000200650062", 20),
                   "xs16_wraiczbd": ("?-loop_on_snake", 20),
                   "xs16_j96zd553": ("01b300a900a60060", 20),
                   "xs16_25b8ria4": ("006800ae0041003a000c", 20),
                   "xs16_9f0330f9": ("?-tables_and_block", 20),
                   "xs16_35is0796": ("00c600a5005500120030", 20),
                   "xs16_ml56z69c": ("?-shillelagh_and_cap", 20),
                   "xs16_178jd453": ("?16?154", 20),
                   "xs16_gbdz11dic": ("?-beehive_with_tail_on_snake", 20),
                   "xs16_2egu16426": ("006000a000ad01ab0010", 20),
                   "xs16_0mkiarz32": ("006c00280024001400350003", 20),
                   "xs16_dbgz354ko": ("03000280009000ab006d", 20),
                   "xs16_252sgf123": ("016201a5002a00280018", 20),
                   "xs16_352sgc2ko": ("0198012800aa00450003", 20),
                   "xs16_6248go8br": ("?-very_long_snake_siamese_table_and_block", 20),
                   "xs16_0ggm96zrm": ("036002d00010001600090006", 20),
                   "xs16_178716853": ("01b300a900aa0044", 20),
                   "xs16_3pm86248c": ("?16?141", 20),
                   "xs16_25b8oge13": ("?-boat_with_cis-tail_siamese_integral", 20),
                   "xs16_178c1f84c": ("0198008800ab006d", 20),
                   "xs16_3hu0642ac": ("long_hook_and_?-shillelagh", 20),
                   "xs16_259mge123": ("014601a9002a00240018", 20),
                   "xs16_178c2ege2": ("?-hat_on_eater", 20),
                   "xs16_cilmzx69c": ("0180012000d600150012000c", 20),
                   "xs16_0ml96zc96": ("0180013600d500090006", 20),
                   "xs16_0ci53zojd": ("?-boat_with_long_tail_siamese_shillelagh", 20),
                   "xs16_2lmge2z56": ("00a200d500160010000e0002", 20),
                   "xs16_6ikm96z32": ("006600520014001600090006", 20),
                   "xs16_32hu069a4": ("014401aa002900260060", 20),
                   "xs16_354c32ako": ("?-boat_with_trans-tail_on_eater", 20),
                   "xs16_321560uh3": ("long_hook_and_?-shillelagh", 20),
                   "xs16_32qj4c826": ("012001e30019004c0060", 20),
                   "xs16_djozx35ac": ("0180014000a0006000180013000d", 20),
                   "xs16_25akgf123": ("016201a5002a00240018", 20),
                   "xs16_25a8o0uh3": ("?-long_hook_and_tub_with_tail", 20),
                   "xs16_354cgs256": ("0182010500eb00280018", 20),
                   "xs16_mkkb2acz1": ("?-eater_on_hat", 20),
                   "xs16_3lkia4z56": ("00c500ab0028004800500020", 20),
                   "xs16_cidharzw1": ("003600140022002d0012000c", 20),
                   "xs16_gs2d96z65": ("00d000bc0002000d00090006", 20),
                   "xs16_bt0653z32": ("?-siamese_snakes_and_ship", 20),
                   "xs16_32qbzca43": ("?16?004", 20),
                   "xs16_651248n96": ("?16?180", 20),
                   "xs16_08u1qrz32": ("?-snake_eater_siamese_carrier_and_block", 20),
                   "xs16_cp3z230356": ("?-table_siamese_carrier_and_ship", 20),
                   "xs16_69arzx1253": ("?-boat_with_cis-tail_siamese_loop", 20),
                   "xs16_0mk453zc96": ("?-long_hook_and_shillelagh", 20),
                   "xs16_6ao8b52z32": ("?-cis-boat_with_long_nine_siamese_carrier", 20),
                   "xs16_4aab8oz253": ("004400aa006a000b00080018", 20),
                   "xs16_o8brzx1256": ("?-boat_with_trans-tail_siamese_table_and_block", 20),
                   "xs16_cilmzw4a52": ("00600090015200d5000a0004", 20),
                   "xs16_31kmicz056": ("00c00085002b006800480030", 20),
                   "xs16_cilmzx3426": ("00c000400080007600150012000c", 20),
                   "xs16_c88e1e8z33": ("?-hat_siamese_table_and_block", 20),
                   "xs16_25a8kczwbd": ("0080014000ad002b00500060", 20),
                   "xs16_3iab8oz321": ("trans-boat_with_long_leg_and_?-table", 20),
                   "xs16_39u0ok8z32": ("?-hook_siamese_carrier_and_?-boat", 20),
                   "xs16_j96z116853": ("0198012800c60001000a000c", 20),
                   "xs16_ci60uh3z11": ("006000560015001100320003", 20),
                   "xs16_gs259a4z56": ("00b000dc000200050009000a0004", 20),
                   "xs16_69jzw23cko": ("0300028001800060005300090006", 20),
                   "xs16_2ego4og853": ("03000203011200aa006c", 20),
                   "xs16_354m96z321": ("006300510012003400480030", 20),
                   "xs16_8ehdicz023": ("001800240058004700390008", 20),
                   "xs16_3pa4zwd552": ("0180013000ab004a000a0004", 20),
                   "xs16_adhegoz023": ("00280059004700380004000c", 20),
                   "xs16_3pmzx32156": ("00c000a0002000400060001600190003", 20),
                   "xs16_6ao8a53z32": ("?-trans-boat_with_long_nine_siamese_carrier", 20),
                   "xs16_3pmk46zx23": ("?-shillelagh_siamese_eater_siamese_table", 20),
                   "xs16_g8id1e8z56": ("00b000c80012000d0001000e0008", 20),
                   "xs16_31248c0fho": ("?-very_long_snake_and_long_hook", 20),
                   "xs16_g8ob96z1ac": ("00c0012001a0003300250018", 20),
                   "xs16_0drz643033": ("?-long_hook_siamese_snake_and_block", 20),
                   "xs16_c88a53z39c": ("trans-boat_with_long_leg_and_?-carrier", 20),
                   "xs16_0g88brzc93": ("?-long_hook_siamese_carrier_and_trans-block", 20),
                   "xs16_3pmzw34ak8": ("?-barge_with_tail_siamese_shillelagh", 20),
                   "xs16_g88bpicz23": ("006000200046003d0001000a000c", 20),
                   "xs16_0gbq23zc96": ("long_integral_and_?-table", 20),
                   "xs16_2530fpzx65": ("009800f5000300c000a00040", 20),
                   "xs16_031eoz2lp1": ("006001d0021303150008", 20),
                   "xs16_ggm930f9z1": ("00d80054004400c800070001", 20),
                   "xs16_25iczxd596": ("00c0012000a001ac001200050002", 20),
                   "xs16_c9bkkozw32": ("?-bee_siamese_eater_at_carrier", 20),
                   "xs16_c9jzw11dic": ("?-beehive_with_tail_on_carrier", 20),
                   "xs16_0gbb8ozc93": ("01800130006b000b00080018", 20),
                   "xs16_caikm93zw1": ("?-shillelagh_siamese_great_snake_eater", 20),
                   "xs16_0j9q453z23": ("?-eater_on_long_shillelagh", 20),
                   "xs16_ckl3zx32ac": ("018001400040006300150014000c", 20),
                   "xs16_0bt0696z32": ("?-snake_siamese_carrier_and_beehive", 20),
                   "xs16_c9baiczw32": ("00180048006b002900240018", 20),
                   "xs16_64km96zw56": ("?-beehive_siamese_table_on_snake", 20),
                   "xs16_256o8gka52": ("barge_with_long_tail_on_boat", 20),
                   "xs16_iu0696z146": ("?-table_siamese_carrier_and_beehive", 20),
                   "xs16_4a9b8oz253": ("004400aa0069000b00080018", 20),
                   "xs16_31e88czwbd": ("?-eater_siamese_table_and_snake", 20),
                   "xs16_mk2t52z121": ("003600540022001d00050002", 20),
                   "xs16_2530fh8426": ("01b002a3012500280010", 20),
                   "xs16_08o653zoj6": ("?-carrier_siamese_snake_on_ship", 20),
                   "xs16_o4c0f96z23": ("shillelagh_and_?-cap", 20),
                   "xs16_4aq32acz32": ("0064004a001a00030002000a000c", 20),
                   "xs16_o8bdzx3156": ("?16?061", 20),
                   "xs16_wiu0652z643": ("00c000a0002000300010001600350002", 20),
                   "xs16_0g88e13zol3": ("?-elevener_siamese_long_snake", 20),
                   "xs16_gilmz1w25a4": ("0080014000a00056001500120030", 20),
                   "xs16_25a8czx6953": ("tub_with_leg_and_?-R-loaf", 20),
                   "xs16_g853z178kk8": ("010002800283010500e80030", 20),
                   "xs16_25bo8a6z032": ("003000530021001e000800200030", 20),
                   "xs16_0mp2sgz1243": ("0020005600990062001c0010", 20),
                   "xs16_0j9c84cz343": ("?-snake_siamese_carrier_on_beehive", 20),
                   "xs16_35s2mzx1074": ("00c000a000380044006800070001", 20),
                   "xs16_69abgzx1256": ("00c000a00050002b000a00090006", 20),
                   "xs16_8u15a4z1226": ("0028005e004100c5000a0004", 20),
                   "xs16_0252sgzca53": ("?-tub_with_tail_on_long_ship", 20),
                   "xs16_wggo3tgz652": ("00c000a00050001000180003001d0010", 20),
                   "xs16_39c8a52z033": ("?-tub_with_leg_siamese_snake_and_trans-block", 20),
                   "xs16_2560uiz0253": ("?-boat_on_table_and_boat", 20),
                   "xs16_065pa4z6521": ("00c000a600450039000a0004", 20),
                   "xs16_31248c2cga6": ("0600051300a9006a0004", 20),
                   "xs16_0ogjl8z4aa4": ("008001580150009300150008", 20),
                   "xs16_x8k453z255d": ("0180014000400050002b000a000a0004", 20),
                   "xs16_8ka9b8ozw23": ("001800140002007d00420008000c", 20),
                   "xs16_64lb8oz0321": ("003000130055006a0008000c", 20),
                   "xs16_02lmge2z252": ("004000a2005500160010000e0002", 20),
                   "xs16_8kih30f9zx1": ("00d80054004200c1000e0008", 20),
                   "xs16_25a8ci6zx65": ("0060004800350013005000a00040", 20),
                   "xs16_0c88e13z653": ("?-eater_siamese_table_and_?-ship", 20),
                   "xs16_x8o653zad11": ("0180014000c0003000280008000b0005", 20),
                   "xs16_25a84cgc48c": ("02000500026d01ab0010", 20),
                   "xs16_ggc2c871z56": ("00c00048005400340003000100020003", 20),
                   "xs16_0gba96z1256": ("00600090005300d5000a0004", 20),
                   "xs16_4ap64koz032": ("?-loaf_siamese_eater_siamese_snake", 20),
                   "xs16_354mioz0252": ("00c000a20025006a00480018", 20),
                   "xs16_0gs2arz6421": ("00d800500044003a00090003", 20),
                   "xs16_c84q552z311": ("006c00280024001a000500050002", 20),
                   "xs16_xgila4z4a96": ("?16?196", 20),
                   "xs16_03ihe8z6521": ("?-snake_eater_on_long_ship", 20),
                   "xs16_65la8cz0321": ("003000530055002a00080018", 20),
                   "xs16_0j9cz1259a4": ("00800140012c00a900530020", 20),
                   "xs16_4s0c453z643": ("?16?177", 20),
                   "xs16_69akg4czx56": ("006000900050002d000b00200030", 20),
                   "xs16_39u0652z032": ("?-hook_siamese_snake_and_R-bee", 20),
                   "xs16_8kk8a53z641": ("00c8009400340008000a00050003", 20),
                   "xs16_69eg8k8zx56": ("?-tub_with_long_tail_on_R-bee", 20),
                   "xs16_o4c32ak8z23": ("?-tub_with_tail_on_shillelagh", 20),
                   "xs16_xgila4zca52": ("?-long_boat_line_barge", 20),
                   "xs16_32qczx1178c": ("?-elevener_siamese_eater", 20),
                   "xs16_g88a52zd54c": ("01b000a80088018a00050002", 20),
                   "xs16_31eozx125ac": ("?-long_boat_with_trans-tail_siamese_eater", 20),
                   "xs16_25a8k8zc871": ("0182010500ea002800140008", 20),
                   "xs16_8e1tazx1252": ("004000a0004a003d0001000e0008", 20),
                   "xs16_8kkl3zx25a4": ("0080014000a30055001400140008", 20),
                   "xs16_32qczx115ac": ("0180014000a00020002c001a00020003", 20),
                   "xs16_39eg8k8zx56": ("?-tub_with_long_tail_on_hook", 20),
                   "xs16_3542sgz0653": ("00c000a30025004600380008", 20),
                   "xs16_gs25acz1226": ("?-long_boat_with_tail_siamese_eater", 20),
                   "xs16_0gs252zpia4": ("03200250015c008200050002", 20),
                   "xs16_0j9cz643113": ("00c000930069002c00200060", 20),
                   "xs16_wpf0ck8z321": ("?-eater_siamese_table_and_boat", 20),
                   "xs16_69eg8kozw23": ("003000480039000700080014000c", 20),
                   "xs16_wggra96z252": ("00600090005000d80008000a00050002", 20),
                   "xs16_35iczx1178c": ("01800140009000680008000e00010003", 20),
                   "xs16_25a8og4c826": ("02000503021901cc0060", 20),
                   "xs16_kc0v146z121": ("0034004c0020001f000100040006", 20),
                   "xs16_0gs2pmz1243": ("0068009800460039000a0004", 20),
                   "xs16_08p78kcz321": ("?-boat_with_cis-tail_on_hook", 20),
                   "xs16_oe132acz023": ("?-eater_siamese_eater_siamese_carrier", 20),
                   "xs16_xgs253zca43": ("0180014000800070001c000200050003", 20),
                   "xs16_xmk453z4a43": ("018001400040005000dc000200050002", 20),
                   "xs16_0i5q8a6z321": ("?-eater_on_boat_on_tub", 20),
                   "xs16_0g8o652z1qm": ("0100028001800060004d002b0010", 20),
                   "xs16_0o8a53zc453": ("?-boat_with_trans-tail_on_eater", 20),
                   "xs16_2lm88cz3421": ("00620095005600280008000c", 20),
                   "xs16_0j9c826z343": ("?-siamese_carriers_on_beehive", 20),
                   "xs16_31kmge13zw1": ("00c300a9002c0020001c0004", 20),
                   "xs16_0cq23ck8z32": ("?-boat_on_eater_siamese_carrier", 20),
                   "xs16_25is0cczw65": ("004000a0004b003d000000300030", 20),
                   "xs16_065pa4z3521": ("006000a600450039000a0004", 20),
                   "xs16_651231248a6": ("?-very_long_shillelagh_siamese_shillelagh", 20),
                   "xs16_g0t3oge2z11": ("00c000ac002a002200130030", 20),
                   "xs16_0696z31139c": ("018001200066002900260060", 20),
                   "xs16_4all2zx34a4": ("?-beehive_siamese_tub_on_tub_with_tail", 20),
                   "xs16_8ljgzx342ac": ("01800140004000800070001300150008", 20),
                   "xs16_wghn871z252": ("00d8005000500020001c000200050002", 20),
                   "xs16_628q552z311": ("006600220028001a000500050002", 20),
                   "xs16_c48a52z2553": ("tub_with_long_tail_and_?-R-bee", 20),
                   "xs16_08u164koz32": ("00c0008000230061002e00280010", 20),
                   "xs16_ca9b8oz0252": ("00300052009500d200100018", 20),
                   "xs16_32ak8zxc953": ("0180008000a000530029000a000c", 20),
                   "xs16_09f0kcz6511": ("00c000a9002f00200014000c", 20),
                   "xs16_0mp3zha6z11": ("0620055600d90003", 20),
                   "xs16_039m453z311": ("0066004a00380004000800070001", 20),
                   "xs16_35s2mzx1252": ("?16?070", 20),
                   "xs16_31eozw122ak8": ("0300020001d000680008000a00050002", 20),
                   "xs16_0gs2596z1246": ("0060009000a000430039000a0004", 20),
                   "xs16_0g6s178cz121": ("?-tub_with_leg_siamese_carrier_siamese_eater", 20),
                   "xs16_69ab88gzx321": ("003000480028006b0009000a0004", 20),
                   "xs16_25a4ozx11696": ("barge_with_leg_on_beehive", 20),
                   "xs16_0ggs25ak8z32": ("long_barge_with_cis-tail_and_?-eater", 20),
                   "xs16_wg8ka53z6521": ("very_very_very_very_long_ship", 20),
                   "xs16_352sgzy132ac": ("0180014000a0002000300008000e00010003", 20),
                   "xs16_8kai3zw116a4": ("0080014000c30032002a00140008", 20),
                   "xs16_0g88a52zok96": ("03000290012800c8000a00050002", 20),
                   "xs16_31egozy1354c": ("integral_on_eater", 20),
                   "xs16_31egozy135a4": ("01800140004000500030000c000a00050002", 20),
                   "xs16_xggka53z4a43": ("?-long_boat_with_trans_tail_siamese_tub_with_tail", 20),
                   "xs16_0356o8z4a521": ("?-barge_with_trans-tail_on_ship", 20),
                   "xs16_0g8gka53z643": ("00c000a0005000280008001600090003", 20),
                   "xs16_xg8ge13zca23": ("018001400040007000080010000e00010003", 20),
                   "xs16_4ai3s4ozx121": ("00180024005c00230012000a0004", 20),
                   "xs16_0gila8oz3421": ("?-tub_with_tail_on_R-loaf", 20),
                   "xs16_32q4ozx122ac": ("01800140004000580024001a00020003", 20),
                   "xs16_4a9mk4ozx121": ("00180024005400360009000a0004", 20),
                   "xs16_25a8kk8z0253": ("004000a200550016002800280010", 20),
                   "xs16_0rb88gzc8421": ("0180011b008b004800280010", 20),
                   "xs16_04aabgz4a511": ("0080014400aa002a002b0010", 20),
                   "xs16_ca168ozc8421": ("018c010a0081004600280018", 20),
                   "xs16_xg8o652zca43": ("0180014000a0002000280018000600050002", 20),
                   "xs16_0g8o652zo9a4": ("0300013001480098000600050002", 20),
                   "xs16_032q4ozca221": ("?-beehive_with_nine_and_tail", 20),
                   "xs16_31e8zw3115a4": ("tub_with_long_leg_and_?-eater", 20),
                   "xs16_31248gzcid11": ("030602090116009000500020", 20),
                   "xs16_354kozx122ac": ("?-siamese_integrals", 20),
                   "xs16_xg8k871zca23": ("018001400040007000080014000800070001", 20),
                   "xs16_0ggm952z12ko": ("01000280024001a3002500280010", 20),
                   "xs16_08o652zgb6z11": ("?-long_snake_siamese_snake_on_boat", 20),
                   "xs16_xg8o652z4a611": ("boat_on_ship_on_boat", 20),
                   "xs16_xg8ge13z4a521": ("018001400040005000280014000a00050002", 20),
                   "xs16_5b88gzx122ak8": ("028003400040005000280008000a00050002", 20),
                   "xs16_xog842156z253": ("03000480064000280018000600050002", 20),
                   "xs16_031e88gzog8421": ("030002030101008e004800280010", 20),
                   "xs16_031248gz8k8711": ("01000283010100e2002400280010", 20),
                   "xs17_2ege1ege2": ("twin hat", 2),
                   "xs17_2ege1t6zx11": ("?17?003", 6),
                   "xs17_3lk453z1243": ("ortho-loaf and dock", 7),
                   "xs17_3lk453z3421": ("para-loaf and dock", 8),
                   "xs17_4a97079ic": ("cis-R-loaf and R-mango", 9),
                   "xs17_5b8b96z033": ("?17?034", 9),
                   "xs17_g6p3qicz11": ("?17?005", 9),
                   "xs17_0696z311d96": ("?17?015", 9),
                   "xs17_0ca952z6953": ("trans-R-loaf and R-mango", 9),
                   "xs17_ca96z065156": ("para-R-loaf and C", 9),
                   "xs17_4aarahr": ("?17?026", 10),
                   "xs17_6a88brz033": ("?17?019", 10),
                   "xs17_4aab871z033": ("block and anvil", 10),
                   "xs17_4aarhar": ("?17?039", 11),
                   "xs17_259e0ehr": ("?17?040", 11),
                   "xs17_j1u06ak8z11": ("?17?021", 11),
                   "xs17_0mlhe8z3421": ("?17?047", 11),
                   "xs17_03lk453z643": ("?17?014", 11),
                   "xs17_69mggkczw66": ("?17?031", 11),
                   "xs17_09v0cicz321": ("?17?013", 11),
                   "xs17_69bo8br": ("?17?101", 12),
                   "xs17_mm0e96z56": ("?17?103", 12),
                   "xs17_5b8b96zx33": ("?17?023", 12),
                   "xs17_69baa4z253": ("?17?069", 12),
                   "xs17_69ab96z033": ("?17?055", 12),
                   "xs17_2ege952z321": ("?17?071", 12),
                   "xs17_69aczw65156": ("?17?059", 12),
                   "xs17_3lkiacz1221": ("?17?011", 12),
                   "xs17_255m88czw343": ("[[R-bee on beehive_with_tail]]", 12),
                   "xs17_069a4ozc8711": ("?17?035", 12),
                   "xs17_31e88gzc8711": ("?17?022", 12),
                   "xs17_03lk453z2521": ("?17?041", 12),
                   "xs17_ckggka52z066": ("?17?032", 12),
                   "xs17_0g8o6996z3421": ("R-mango on pond", 12),
                   "xs17_4a9r8br": ("?17?058", 13),
                   "xs17_g6t1qrz11": ("?17?020", 13),
                   "xs17_3lkm96z32": ("?17?049", 13),
                   "xs17_25ako0uic": ("?17?045", 13),
                   "xs17_4a970si96": ("?17?092", 13),
                   "xs17_330fho8a6": ("?-eater_siamese_long_hook_and_block", 13),
                   "xs17_25is0si96": ("?17?077", 13),
                   "xs17_69baiczw65": ("[[paperclip fuse long_snake]]", 13),
                   "xs17_3lka96z321": ("?17?067", 13),
                   "xs17_mllmz1w252": ("tub_with_long_leg_and_cis-cap", 13),
                   "xs17_gie0e93z56": ("?17?024", 13),
                   "xs17_gbb8b5z123": ("?17?009", 13),
                   "xs17_0gbb871z343": ("?17?125", 13),
                   "xs17_4aab96zw253": ("?17?109", 13),
                   "xs17_39u08kcz321": ("?17?050", 13),
                   "xs17_g84s3pmz121": ("?17?124", 13),
                   "xs17_0j1u0696z121": ("?17?118", 13),
                   "xs17_699mk4ozx121": ("?17?113", 13),
                   "xs17_69b88a6zw252": ("?17?027", 13),
                   "xs17_w8o6996z6521": ("?17?085", 13),
                   "xs17_2egu1qr": ("?17?121", 14),
                   "xs17_35is0sia4": ("?17?135", 14),
                   "xs17_321fgf123": ("?-long_hat_siamese_snakes", 14),
                   "xs17_0ok2qrz643": ("?17?054", 14),
                   "xs17_4aab96z253": ("?17?127", 14),
                   "xs17_o4s3qp3z01": ("?-R-bee_on_snake_and_block", 14),
                   "xs17_32qb96z321": ("?-head_siamese_eater", 14),
                   "xs17_09v0bdz321": ("?17?056", 14),
                   "xs17_c89f033z33": ("?17?137", 14),
                   "xs17_39u0ooz643": ("?17?080", 14),
                   "xs17_0c8a53z6953": ("?17?166", 14),
                   "xs17_0g8ob96zc96": ("?17?078", 14),
                   "xs17_o8b96zx3156": ("00c000a000260069000b00080018", 14),
                   "xs17_xohf033z253": ("?17?144", 14),
                   "xs17_178b9a4zw33": ("?17?037", 14),
                   "xs17_ckggm96z066": ("?17?064", 14),
                   "xs17_8e1t6zx1256": ("?17?086", 14),
                   "xs17_4a9baiczx32": ("0018002e0041003d00020008000c", 14),
                   "xs17_0c88brz2552": ("?17?093", 14),
                   "xs17_c4o79a4z321": ("?17?098", 14),
                   "xs17_0259acz6953": ("?17?004", 14),
                   "xs17_gwci96z11dd": ("?17?083", 14),
                   "xs17_g8ie0ehrz01": ("?17?079", 14),
                   "xs17_j1u06a8oz11": ("?-eater_and_dock", 14),
                   "xs17_cimggm96zx1": ("?17?042", 14),
                   "xs17_0ggciarz3421": ("?17?070", 14),
                   "xs17_660u1acz0321": ("003000330001003e004000280018", 14),
                   "xs17_031e8gz69d11": ("?17?063", 14),
                   "xs17_259aczw315a4": ("?17?172", 14),
                   "xs17_025a4oz69d11": ("?17?028", 14),
                   "xs17_0oggm96z4aa4": ("?17?120", 14),
                   "xs17_xg8ge13zca611": ("?17?017", 14),
                   "xs17_4aar2qr": ("?-hat_siamese_table_and_block", 15),
                   "xs17_4aaraar": ("?-hat_siamese_tables", 15),
                   "xs17_178c1fgkc": ("?17?162", 15),
                   "xs17_g5r8brz11": ("003600340004003600290003", 15),
                   "xs17_cp3qicz23": ("?17?131", 15),
                   "xs17_09v0f9z321": ("?17?087", 15),
                   "xs17_0mlla4z1ac": ("004000a00150015300d50008", 15),
                   "xs17_0gbaarz343": ("?17?100", 15),
                   "xs17_0gs2qrz643": ("?17?038", 15),
                   "xs17_2ll2sgz643": ("beehive_with_tail_and_?-hook", 15),
                   "xs17_c9baaczw33": ("?17?126", 15),
                   "xs17_gie0e96z56": ("?17?066", 15),
                   "xs17_ogil96z6a4": ("?17?153", 15),
                   "xs17_0c88brz653": ("Z_and_trans-ship_and_block", 15),
                   "xs17_4aab96z0352": ("?17?018", 15),
                   "xs17_6ao4a96z321": ("?17?150", 15),
                   "xs17_4a9b871z033": ("[[?17?174]]", 15),
                   "xs17_0ggm96z3ego": ("?17?053", 15),
                   "xs17_06t1egoz321": ("0060005000130015003400240018", 15),
                   "xs17_259aczx6953": ("?-R-loaf_and_R-mango", 15),
                   "xs17_69aczx359a4": ("?17?106", 15),
                   "xs17_354kl3z0643": ("?17?167", 15),
                   "xs17_j1u062sgz11": ("?17?036", 15),
                   "xs17_0jhu06a4z32": ("?-eater_siamese_long_hook_and_?-boat", 15),
                   "xs17_08e1t6z6511": ("?17?116", 15),
                   "xs17_g6q0si96z11": ("?-R-mango_and_shillelagh", 15),
                   "xs17_ca1t6zx1256": ("00c000a00046003d0001000a000c", 15),
                   "xs17_8e1t6zx1156": ("?-head_siamese_eater", 15),
                   "xs17_cimggm93zx1": ("00c000a600250041003e0008", 15),
                   "xs17_wggs2qrz252": ("tub_with_cis-tail_siamese_trans-legs_and_block", 15),
                   "xs17_0h7ob96z121": ("?17?112", 15),
                   "xs17_cc0v146z311": ("?17?084", 15),
                   "xs17_01784oz69d11": ("?17?029", 15),
                   "xs17_031e8gzck871": ("?17?168", 15),
                   "xs17_03lk453z4701": ("?17?147", 15),
                   "xs17_0356o8z69521": ("?17?010", 15),
                   "xs17_356o8a6z0321": ("ship on elevener", 15),
                   "xs17_w6a8a52z6513": ("tub_with_nine_and_meta-hook", 15),
                   "xs17_255q8a6z0321": ("elevener_on_beehive", 15),
                   "xs17_0651u8z4a521": ("?17?143", 15),
                   "xs17_0c88a53z2596": ("[[ortho-loaf and trans-boat_fuse_longhook]]", 15),
                   "xs17_025a4z69d113": ("?17?025", 15),
                   "xs17_wg0si96z6943": ("?-mango_on_R-mango", 15),
                   "xs17_660u1e8z0321": ("?17?081", 15),
                   "xs17_0ggm9icz3443": ("?17?169", 15),
                   "xs17_02lligz252w23": ("tub_with_long_nine_and_cis-beehive", 15),
                   "xs17_4a9r2qr": ("0068006e0001007a004c", 16),
                   "xs17_4aar1qr": ("?17?104", 16),
                   "xs17_4a9raar": ("004c007a0001007e0048", 16),
                   "xs17_69ir8jd": ("006a002d0041005a002c", 16),
                   "xs17_2ego3tic": ("?-boat_siamese_R-bee_and_eater", 16),
                   "xs17_69mge1da": ("00620095005500d2000c", 16),
                   "xs17_8u156zrm": ("036802de000100050006", 16),
                   "xs17_259ara96": ("?17?075", 16),
                   "xs17_rb0796z23": ("?-snake_and_block_and_R-bee", 16),
                   "xs17_25is0si53": ("boat_with_leg_and_cis-tub_with_leg", 16),
                   "xs17_9v0sicz23": ("?-table_siamese_table_and_R-bee", 16),
                   "xs17_okkm96z66": ("?17?105", 16),
                   "xs17_660uh32ac": ("?17?002", 16),
                   "xs17_8k4r2qrzw1": ("?17?145", 16),
                   "xs17_02llicz696": ("00c0012200d500150012000c", 16),
                   "xs17_0ggraarz32": ("?-eater_siamese_table_and_table", 16),
                   "xs17_31kmicz643": ("00c30081007400160012000c", 16),
                   "xs17_j1u0ol3z11": ("?-dock_and_long_snake", 16),
                   "xs17_c9b871z352": ("alef_and_?-boat", 16),
                   "xs17_69ab96zx33": ("0030004b006b002800480030", 16),
                   "xs17_0br0f9z321": ("?-hook_and_table_and_block", 16),
                   "xs17_39u0uiz023": ("?17?099", 16),
                   "xs17_178baa4zw33": ("?17?012", 16),
                   "xs17_4aligkczw66": ("?17?133", 16),
                   "xs17_39mggkczw66": ("00c00090006b000b000800280030", 16),
                   "xs17_gwci96zdd11": ("trans-mango_with_long_leg_and_trans-block", 16),
                   "xs17_6a88a53z253": ("trans-boat_with_long_nine_and_trans-boat", 16),
                   "xs17_0ggml96z346": ("0060009000d00016001500090006", 16),
                   "xs17_69r2qczw121": ("?17?115", 16),
                   "xs17_mligz1w69a4": ("?17?148", 16),
                   "xs17_2ege996zw23": ("0030004b004a003a00040008000c", 16),
                   "xs17_0gs2pmz3443": ("006800980046003900090006", 16),
                   "xs17_09v0ca6z321": ("?17?110", 16),
                   "xs17_iu0696z1226": ("?-table_siamese_eater_and_beehive", 16),
                   "xs17_0gjlka4z346": ("?17?119", 16),
                   "xs17_08u1dioz321": ("?17?161", 16),
                   "xs17_8e1t6zx1253": ("?17?122", 16),
                   "xs17_09v0ckoz321": ("cis-ship_and_long", 16),
                   "xs17_03lkia4z643": ("00c00083007500140012000a0004", 16),
                   "xs17_8kimgm96zx1": ("?17?128", 16),
                   "xs17_069b8ozc871": ("0180010600e9002b00080018", 16),
                   "xs17_gill2z1w696": ("beehive_with_long_leg_and_cis-beehive", 16),
                   "xs17_c88bb8ozw33": ("very_long_Z_and_blocks", 16),
                   "xs17_8kkl3zx69a4": ("00800140012300d5001400140008", 16),
                   "xs17_354micz0643": ("00c000a30021006e00480030", 16),
                   "xs17_0ggm93z3ego": ("0300024001a30021002e0018", 16),
                   "xs17_o4ie0djoz01": ("?-R-mango_and_shillelagh", 16),
                   "xs17_g88e13zc953": ("0190012800a8006e00010003", 16),
                   "xs17_6a88a52z653": ("?17?088", 16),
                   "xs17_0gbb871z643": ("00c00090006b000b000800070001", 16),
                   "xs17_0gba952z3452": ("0060009000ab004a000900050002", 16),
                   "xs17_0gbbo8a6z121": ("?-tub_with_leg_siamese_eater_and_block", 16),
                   "xs17_06996z3115a4": ("tub_with_long_leg_and_cis-pond", 16),
                   "xs17_0c88a53z6952": ("trans-boat_with_long_leg_and_para-loaf", 16),
                   "xs17_4a5pabgzx121": ("002c00320005003a004800280010", 16),
                   "xs17_4aq3qa4zw121": ("maple leaf", 16),
                   "xs17_xg8o653zca23": ("?17?046", 16),
                   "xs17_25a88a6z0653": ("tub_with_long_nine_and_ortho-ship", 16),
                   "xs17_0gilmz32w256": ("trans-boat_with_long_nine_and_cis-boat", 16),
                   "xs17_25a8czx65156": ("?17?129", 16),
                   "xs17_w8o69icz6521": ("?-boat_with_leg_on_mango", 16),
                   "xs17_032q4oz69611": ("?-beehive_on_R-bee_with_tail", 16),
                   "xs17_xg8ka52zca611": ("ship_on_very_very_long_boat", 16),
                   "xs17_xg8o652zca611": ("boat_on_ship_on_ship", 16),
                   "xs17_3pabqic": ("0068005e0001003d0026", 17),
                   "xs17_4a9riar": ("0058006e0001007a004c", 17),
                   "xs17_25b8rb8o": ("?-boat_with_cis-tail_siamese_table_and_block", 17),
                   "xs17_33gv1okc": ("Z_and_cis-ship_and_block", 17),
                   "xs17_okkm93z66": ("00d800d40014001600090003", 17),
                   "xs17_9v0si6z23": ("?-table_siamese_table_and_hook", 17),
                   "xs17_ml1egoz56": ("00b600d50001000e00100018", 17),
                   "xs17_69raicz32": ("?17?007", 17),
                   "xs17_2egu164ko": ("?17?134", 17),
                   "xs17_gjlmz1w696": ("beehive_with_long_leg_and_cis-ship", 17),
                   "xs17_raarzx1252": ("?-tub_with_tail_siamese_table_and_cis-table", 17),
                   "xs17_3jgf96z121": ("?-boat_on_cap_and_block", 17),
                   "xs17_mljgz1w696": ("beehive_with_long_leg_and_para-ship", 17),
                   "xs17_mm0e93z146": ("?17?171", 17),
                   "xs17_wgbqicz69c": ("00c001200190000b001a0012000c", 17),
                   "xs17_c89f0ccz33": ("?17?138", 17),
                   "xs17_0db8b5z253": ("00a000d0001000d600b50002", 17),
                   "xs17_39s0sicz32": ("?-siamese_carriers_and_?-R-bee", 17),
                   "xs17_2552sgc453": ("?-beehive_with_tail_on_eater", 17),
                   "xs17_mkhf0ca4z1": ("alef_and_?-boat", 17),
                   "xs17_cilmzw4a96": ("00c00120015600950012000c", 17),
                   "xs17_j5s2596z11": ("006600490035001200500060", 17),
                   "xs17_gillicz146": ("?17?117", 17),
                   "xs17_ci96zwd596": ("00c0012000a601a90012000c", 17),
                   "xs17_raaczx3156": ("R-hat_and_hook", 17),
                   "xs17_09fgkcz653": ("00c000a9006f00100014000c", 17),
                   "xs17_3lk64koz121": ("?-hook_siamese_eater_and_trans-boat", 17),
                   "xs17_g88b96zc952": ("0190012800a8004b00090006", 17),
                   "xs17_g8jd0eioz11": ("boat_with_long_tail_and_?-hook", 17),
                   "xs17_69aczx315ac": ("boat_with_leg_and_shift-R-loaf", 17),
                   "xs17_wggraicz652": ("?-boat_with_trans-tail_siamese_loop", 17),
                   "xs17_69bi2sgzw23": ("0030005c00420032000b00080018", 17),
                   "xs17_2lligz56w23": ("00a200d50015001200500060", 17),
                   "xs17_69baaczw252": ("R-racetrack_and_tub", 17),
                   "xs17_g88bap3z123": ("?-snake_and_worm", 17),
                   "xs17_25a4z311d96": ("trans-barge_and_worm", 17),
                   "xs17_08u1dicz321": ("?-beehive_with_bend_tail_siamese_hook", 17),
                   "xs17_gie0e96z146": ("006000900070000000730049000c", 17),
                   "xs17_mll2z1025a4": ("?17?155", 17),
                   "xs17_gilmz1w69a4": ("trans-loaf_with_long_leg_and_cis-boat", 17),
                   "xs17_65la8cz0343": ("?17?102", 17),
                   "xs17_62s0v1oozx1": ("?17?152", 17),
                   "xs17_03lkk8z69a4": ("00c001230155009400140008", 17),
                   "xs17_0gilicz34ac": ("00600090015300950012000c", 17),
                   "xs17_0ca1t6z6511": ("00c000ac002a0021001d0006", 17),
                   "xs17_35a8czx6953": ("boat_with_leg_and_?-R-loaf", 17),
                   "xs17_6a88b9czx33": ("?17?132", 17),
                   "xs17_gs2ll2z1243": ("004000a800ae0041003a000c", 17),
                   "xs17_0mp3z643033": ("?17?065", 17),
                   "xs17_m2s079k8z11": ("C_and_shift-tub_with_leg", 17),
                   "xs17_39eg6p3zx11": ("?-long_hook_on_long_integral", 17),
                   "xs17_3iaczw11d96": ("?17?146", 17),
                   "xs17_ggka23qicz1": ("010001c600250041003e0008", 17),
                   "xs17_03hu0ooz643": ("?17?072", 17),
                   "xs17_gil9acz1243": ("?-R-mango_on_R-loaf", 17),
                   "xs17_0cq1dioz321": ("006000500013003500240012000c", 17),
                   "xs17_31kmioz0346": ("00c000860029006b00480018", 17),
                   "xs17_8e1t2sgzw23": ("?-amoeba_6,6,4", 17),
                   "xs17_39u0696z032": ("?-hook_siamese_snake_and_trans-beehive", 17),
                   "xs17_gbb88cz1253": ("0030004b00ab00680008000c", 17),
                   "xs17_0mp3s4z3421": ("?-loaf_with_trans-tail_siamese_shillelagh", 17),
                   "xs17_8e1t246z311": ("?-amoeba_7,6,3", 17),
                   "xs17_2llmz320252": ("tub_with_nine_and_trans-R-bee", 17),
                   "xs17_0j9q453z321": ("?-long_shillelagh_on_long_ship", 17),
                   "xs17_ckggm93z066": ("?17?139", 17),
                   "xs17_0i5t2sgz321": ("?-beehive_with_tail_siamese_boat_with_leg", 17),
                   "xs17_25a8czw4a953": ("tub_with_leg_and_shift-R-mango", 17),
                   "xs17_0c88a52z6996": ("tub_with_long_leg_and_trans-pond", 17),
                   "xs17_31eozw122ako": ("03000280014000400058002e00010003", 17),
                   "xs17_069acz4a5123": ("tub_with_long_tail_and_?-R-loaf", 17),
                   "xs17_0j1u06acz121": ("tub_with_long_nine_and_para-ship", 17),
                   "xs17_04a96z31178c": ("?-eater_siamese_table_and_?-loaf", 17),
                   "xs17_25a88gzcid11": ("binocle_tub_beehive", 17),
                   "xs17_0g4s3qicz121": ("004000a0005600150031000e0008", 17),
                   "xs17_0ogka52z4aa6": ("barge_with_leg_and_trans-R-bee", 17),
                   "xs17_031e8gzok871": ("03000283010100ee00280010", 17),
                   "xs17_25akggkczx66": ("trans-barge_with_long_nine_and_cis-block", 17),
                   "xs17_0mligz32w652": ("cis-boat_with_long_nine_and_para-boat", 17),
                   "xs17_354mkk8z0252": ("00c000a20025006a002800280010", 17),
                   "xs17_259a4oz4a511": ("[[mango_?_tub]]", 17),
                   "xs17_0ml9ak8z1221": ("003000480032000d003200240018", 17),
                   "xs17_0c88b52z2596": ("cis-boat_with_long_leg_and_?-loaf", 17),
                   "xs17_0c88b52z6952": ("?17?030", 17),
                   "xs17_0ggcaarz1243": ("?17?165", 17),
                   "xs17_259ege2z0321": ("?17?068", 17),
                   "xs17_0mligkcz3201": ("[[cis-boat on bookend_siamese_eater]]", 17),
                   "xs17_069a4ozca511": ("0180014600a9002a00240018", 17),
                   "xs17_04a96zca5113": ("?17?142", 17),
                   "xs17_35a88a6z0253": ("trans-boat_with_long_nine_and_?-boat", 17),
                   "xs17_8kai3zw116ac": ("ship_on_long_boat_with_cis-tail", 17),
                   "xs17_03lk453z6221": ("dock_and_?-eater", 17),
                   "xs17_0gilmz32w652": ("?17?073", 17),
                   "xs17_0g6pb871z121": ("G_siamese_trans-legs_on_tub", 17),
                   "xs17_0g8ie0e96z23": ("?17?140", 17),
                   "xs17_xg8k871zca611": ("?17?033", 17),
                   "xs17_69ir2pm": ("006c002a0041005d002a", 18),
                   "xs17_4aar9ar": ("0058006e0001007e0048", 18),
                   "xs17_1no3tic": ("?-bookends_siamese_beehive", 18),
                   "xs17_354c32qr": ("?-eater_on_table_and_block", 18),
                   "xs17_321fgn96": ("00b600d500150012000c", 18),
                   "xs17_6421fgbr": ("00d800d5001300d000a0", 18),
                   "xs17_178jt2sg": ("00d800540052002a001b", 18),
                   "xs17_32hu0uic": ("00a000d6001500150036", 18),
                   "xs17_ml5ak8z56": ("?-R-bee_siamese_barge_and_snake", 18),
                   "xs17_31461vg33": ("?-Z_on_carrier_and_block", 18),
                   "xs17_33gv1og4c": ("?-Z_and_carrier_and_block", 18),
                   "xs17_69bo8gka6": ("00c00143010500f2002c", 18),
                   "xs17_259mge1e8": ("00c4012a00aa004b0030", 18),
                   "xs17_354ko0uic": ("integral_and_?-cap", 18),
                   "xs17_mmge1daz1": ("00400070000b006a00690006", 18),
                   "xs17_253gv1ok8": ("Z_and_cis-boats", 18),
                   "xs17_39u0mqz023": ("long_and_?-snake", 18),
                   "xs17_39mkicz321": ("ghost", 18),
                   "xs17_gbr0f9z121": ("?-R-bee_and_table_and_block", 18),
                   "xs17_cit1eozx32": ("0018004e0061001d0012000c", 18),
                   "xs17_wgs2qrz643": ("?17?090", 18),
                   "xs17_c8ad1e8z33": ("?-loop_siamese_table_and_block", 18),
                   "xs17_39mkkozw66": ("00c00090006b002b00280018", 18),
                   "xs17_g4s3qp3z11": ("?-hook_on_snake_and_block", 18),
                   "xs17_8k4raarzw1": ("?-loaf_siamese_table_on_table", 18),
                   "xs17_j9mkicz121": ("006600490036001400240018", 18),
                   "xs17_0gbaarz643": ("00d80050005000d600090003", 18),
                   "xs17_3pmkk8zx66": ("?-shillelagh_siamese_long_bee_and_trans-block", 18),
                   "xs17_69mgmaz321": ("00660049003600100016000a", 18),
                   "xs17_cilmzx69a4": ("00800140012000d600150012000c", 18),
                   "xs17_mm0e96z146": ("?17?159", 18),
                   "xs17_4a9licz253": ("?-mango_siamese_loaf_on_boat", 18),
                   "xs17_j9ab8oz123": ("worm_and_?-snake", 18),
                   "xs17_64km96z643": ("?-beehive_siamese_table_on_eater", 18),
                   "xs17_o8baarz023": ("006c00280028006b0009000c", 18),
                   "xs17_6s1fgkcz11": ("006000260029006b00480018", 18),
                   "xs17_ciarzx3453": ("006000a00080007b000a0012000c", 18),
                   "xs17_069jzciq23": ("01800246034900530060", 18),
                   "xs17_3pmkk8z066": ("?-shillelagh_siamese_long_R-bee_and_cis-block", 18),
                   "xs17_03lkicz696": ("00c0012300d500140012000c", 18),
                   "xs17_gbq1ticz01": ("?17?097", 18),
                   "xs17_69mkkozw66": ("?-beehive_siamese_long_R-bee_and_cis-block", 18),
                   "xs17_6a8c93z2552": ("?-hook_siamese_carrier_and_beehive", 18),
                   "xs17_69d2sgzw643": ("0060009000b30041003e0008", 18),
                   "xs17_3lm88cz1243": ("00c400aa0069001600100030", 18),
                   "xs17_g8ie0djoz11": ("boat_with_leg_and_?-shillelagh", 18),
                   "xs17_c97o4kozw23": ("0030001000560069000b00080018", 18),
                   "xs17_o8brzw122ac": ("018001400040005b002b00080018", 18),
                   "xs17_2ll2sgzw343": ("004000a800ae0041003e0008", 18),
                   "xs17_069b8oz3156": ("?17?157", 18),
                   "xs17_0c88b5z6996": ("014001a00026002900690006", 18),
                   "xs17_2lla8oz3421": ("006200950055002a00080018", 18),
                   "xs17_02lmge2z643": ("?-trans-legs_siamese_eater_and_boat", 18),
                   "xs17_3lkmz320252": ("tub_with_nine_and_?-hook", 18),
                   "xs17_035a8cz6953": ("boat_with_leg_and_?-R-loaf", 18),
                   "xs17_3lo0ok8z643": ("?-long_snake_siamese_hook_and_boat", 18),
                   "xs17_caab8oz0652": ("?-long_Z_siamese_eater_and_boat", 18),
                   "xs17_69mggoz0ca6": ("beehive_with_long_leg_and_ortho-ship", 18),
                   "xs17_03hu066z643": ("?-long_hook_siamese_eater_and_trans-block", 18),
                   "xs17_0g88brz3496": ("cis-mango_with_long_leg_and_trans-block", 18),
                   "xs17_xgil96z4a96": ("?-loaf_line_loaf", 18),
                   "xs17_gbahdaz1221": ("0030004b004a0031000d000a", 18),
                   "xs17_gbhe0eicz01": ("tub_with_nine_and_cis-R-bee", 18),
                   "xs17_0db88cz2553": ("?17?044", 18),
                   "xs17_0mligoz3426": ("00600096005500d200100018", 18),
                   "xs17_62s0s2pmzx1": ("004000a30095005400d40008", 18),
                   "xs17_2ll2sgz1243": ("?-beehive_with_tail_on_loaf", 18),
                   "xs17_0cq1dicz321": ("?17?141", 18),
                   "xs17_mkl3z10254c": ("0180008000a3005500140036", 18),
                   "xs17_o8gka53z643": ("?-long_boat_with_long_tail_siamese_C", 18),
                   "xs17_3pabgzx1256": ("long_boat_with_leg_and_?-snake", 18),
                   "xs17_39s0ca6z321": ("?-hook_siamese_carrier_and_ship", 18),
                   "xs17_69ab88czx33": ("003000480028006b000b00080018", 18),
                   "xs17_3iaj2acz121": ("?-eater_siamese_table_and_barge", 18),
                   "xs17_g6d1ege2z11": ("00c00084002a006a004b0030", 18),
                   "xs17_69ligozw6a4": ("cis-loaf_with_long_leg_and_?-boat", 18),
                   "xs17_3lkia4z1226": ("00c400aa002a004b00500020", 18),
                   "xs17_69iczx11dic": ("?-mango_line_beehive", 18),
                   "xs17_o8b96zx3552": ("004000a000a60069000b00080018", 18),
                   "xs17_0352sgzca53": ("?-long_ship_on_boat_with_cis-tail", 18),
                   "xs17_35iczw11d96": ("0180014000980068000b00090006", 18),
                   "xs17_ca1t2sgzw23": ("?-amoeba_6,6,4", 18),
                   "xs17_8kimgm93zx1": ("00c000ac002a0041003e0008", 18),
                   "xs17_g8o69arz121": ("?-loop_on_R-bee", 18),
                   "xs17_cc0v9zx1256": ("?-boat_with_leg_siamese_table_and_block", 18),
                   "xs17_ogehjzx3452": ("?-R-loaf_on_integral", 18),
                   "xs17_069b8oz3552": ("?17?158", 18),
                   "xs17_2lligoz1246": ("004400aa00a9004b00080018", 18),
                   "xs17_2lligz32w65": ("00a000d00012001500550062", 18),
                   "xs17_0ml9acz1243": ("?-mango_siamese_bookend_on_loaf", 18),
                   "xs17_8e13z3115ac": ("cis-boat_with_long_leg_and_?-eater", 18),
                   "xs17_25acz3115ac": ("trans-boat_with_long_leg_and_?-long_boat", 18),
                   "xs17_0oggm96zca6": ("beehive_with_long_leg_and_?-ship", 18),
                   "xs17_3lka952z121": ("006600490032000c003000500020", 18),
                   "xs17_660u93z2521": ("?-tub_with_tail_siamese_hook_and_block", 18),
                   "xs17_0ol3zca22ac": ("dock_and_?-long_snake", 18),
                   "xs17_mkl3z1025a4": ("barge_with_leg_and_cis-hook", 18),
                   "xs17_g4q2r9a4z11": ("00c000a8002e0041003a000c", 18),
                   "xs17_gbb8oge2z11": ("?-long_hook_siamese_eater_and_block", 18),
                   "xs17_03jgf9z2521": ("long_boat_on_table_and_block", 18),
                   "xs17_697o4czw343": ("?17?108", 18),
                   "xs17_25a8a6z3156": ("tub_with_nine_and_ortho-hook", 18),
                   "xs17_0c9b871z253": ("alef_and_?-boat", 18),
                   "xs17_259aczw4a513": ("tub_with_leg_and_para-R-mango", 18),
                   "xs17_25akozx622ac": ("long_hook_and_?-very_long_boat", 18),
                   "xs17_0c88c93z2553": ("?-carrier_siamese_table_and_R-bee", 18),
                   "xs17_256o696z0321": ("?17?016", 18),
                   "xs17_0c88e13z2596": ("?-eater_siamese_table_and_?-loaf", 18),
                   "xs17_0oggm93z4aa4": ("?17?096", 18),
                   "xs17_25iczw123cko": ("0300028001800060004c003200050002", 18),
                   "xs17_g88e13z178k8": ("?-tub_with_tail_siamese_elevener", 18),
                   "xs17_4aab94ozx311": ("001800240029006b000a000a0004", 18),
                   "xs17_06akl3zc8421": ("01800158005400a200c10003", 18),
                   "xs17_08o652z320f9": ("?-boat_on_carrier_on_table", 18),
                   "xs17_w6a8a52z2553": ("tub_with_nine_and_?-R-bee", 18),
                   "xs17_0gbq1e8z3421": ("?-snake_eater_and_R-mango", 18),
                   "xs17_0j9mkk8z1221": ("00300048002e0011000e00280030", 18),
                   "xs17_0gjlmz32w252": ("tub_with_long_nine_and_?-ship", 18),
                   "xs17_06a8a52z3156": ("tub_with_nine_and_shift-hook", 18),
                   "xs17_25a8kicz0253": ("004000a200550016002800480030", 18),
                   "xs17_2ege9a4zx113": ("002000380004003a004a002b0010", 18),
                   "xs17_xggm952z4a96": ("?-loaf_line_loaf", 18),
                   "xs17_0ogka52zca26": ("barge_with_leg_and_?-hook", 18),
                   "xs17_352s0ccz2521": ("?-boat_long_line_tub_and_block", 18),
                   "xs17_25ic8a6z2521": ("?-hook_on_barge_on_tub", 18),
                   "xs17_wck8a53z6521": ("00c000a000500010002c003200050003", 18),
                   "xs17_069b8oz4a511": ("0080014600a9002b00280018", 18),
                   "xs17_0j5c4oz34311": ("006000930065002c00240018", 18),
                   "xs17_32q4ozx12596": ("0180008000b000480034000a00090006", 18),
                   "xs17_25a8czw315ac": ("boat_with_leg_and_?-tub_with_leg", 18),
                   "xs17_gw8ka52zdd11": ("trans-long_barge_with_long_leg_and_trans-block", 18),
                   "xs17_08u1u8z32x23": ("?-hat_siamese_carriers", 18),
                   "xs17_64km996z0121": ("?-pond_siamese_table_on_boat", 18),
                   "xs17_025a8oz69d11": ("?-scorpio_siamese_tub_with_tail", 18),
                   "xs17_35iczw123ck8": ("03000280013000c80018000600050002", 18),
                   "xs17_2lla8k8z1221": ("?17?048", 18),
                   "xs17_04a96z3115ac": ("trans-boat_with_long_leg_and_?-loaf", 18),
                   "xs17_25aczw3115ac": ("trans-boat_with_long_leg_and_?-long_boat", 18),
                   "xs17_04aabgzc8711": ("?-sesquihat_siamese_eater", 18),
                   "xs17_35akozy135a4": ("very_long_ship_on_long_boat", 18),
                   "xs17_0j1u06a4z321": ("trans-boat_with_long_nine_and_para-boat", 18),
                   "xs17_0j9ege2z1221": ("?-mango_with_trans-tail_siamese_hook", 18),
                   "xs17_35a88gzca511": ("?-binocle_boats", 18),
                   "xs17_xg8ka53zca23": ("?-very_long_boat_with_trans-tail_siamese_eater", 18),
                   "xs17_32q4ozx1079c": ("?-beehive_with_tail_on_hook", 18),
                   "xs17_0c88e13z6952": ("?17?107", 18),
                   "xs17_ckgog853z066": ("?-canoe_siamese_hook_and_trans-block", 18),
                   "xs17_25ao4koz0643": ("?-scorpio_siamese_long_hook_on_tub", 18),
                   "xs17_wgba952z2543": ("00680098004000380004000a00090006", 18),
                   "xs17_252s0ccz6521": ("?-boat_long_line_tub_and_block", 18),
                   "xs17_0g88e1e8z3452": ("?-loaf_with_cis-tail_siamese_hat", 18),
                   "xs17_3pm0ehr": ("C_and_?-shillelagh", 19),
                   "xs17_69ar2pm": ("0068002e0041005d002a", 19),
                   "xs17_178nhar": ("006d002b00280013000d", 19),
                   "xs17_2530fhar": ("00b600d5001200d000a0", 19),
                   "xs17_259ar8b5": ("00d600590082007c0010", 19),
                   "xs17_259ari96": ("006a009d0041003a000c", 19),
                   "xs17_39mge1da": ("00c600a9002a004b0030", 19),
                   "xs17_32hv0796": ("00b600d5001500120030", 19),
                   "xs17_31ego4qic": ("01800146004900550036", 19),
                   "xs17_5bob96z32": ("0065004b0018000b00090006", 19),
                   "xs17_o5r8brz01": ("003600340004003600290006", 19),
                   "xs17_h7objoz11": ("003600160010000d002b0030", 19),
                   "xs17_mm0e93z56": ("?-block_and_hook_and_snake", 19),
                   "xs17_32hu06996": ("014601a9002900260060", 19),
                   "xs17_31ege1da4": ("018c0152005500560020", 19),
                   "xs17_8u1ticz23": ("0048007e0001001d0012000c", 19),
                   "xs17_178c1f871": ("R-hat_and_?-eater", 19),
                   "xs17_31ego0uh3": ("long_hook_and_?-integral", 19),
                   "xs17_4ad1egma4": ("00600096015500d2000c", 19),
                   "xs17_rb079cz23": ("?-snake_and_hook_and_block", 19),
                   "xs17_25ako0uh3": ("long_hook_and_para-very_long_boat", 19),
                   "xs17_35is079a4": ("boat_with_leg_and_R-loaf", 19),
                   "xs17_25is079ic": ("tub_with_leg_and_?-R-mango", 19),
                   "xs17_31ego0uic": ("?-integral_and_cap", 19),
                   "xs17_358go3qic": ("0188010e008100550036", 19),
                   "xs17_31egu15a4": ("018c0152005500520030", 19),
                   "xs17_6a8oge1da": ("00c0012300a101ae0018", 19),
                   "xs17_iu06952z56": ("?-table_siamese_snake_and_loaf", 19),
                   "xs17_39u0ok8z65": ("?-long_snake_siamese_hook_and_boat", 19),
                   "xs17_4allicz321": ("0064004a003500150012000c", 19),
                   "xs17_69jzw6b871": ("00c001200196000d0001000e0008", 19),
                   "xs17_6s1raiczw1": ("0018004e0061002d002a0010", 19),
                   "xs17_32hjkcz652": ("?-boat_with_?-nine_on_snake", 19),
                   "xs17_4aab8oz653": ("00c400aa006a000b00080018", 19),
                   "xs17_03loz32qic": ("01800258035500430060", 19),
                   "xs17_4aajkcz253": ("004400aa006a00130014000c", 19),
                   "xs17_2ll2sgz343": ("beehive_with_tail_and_R-bee", 19),
                   "xs17_8o6pb8oz23": ("?17?061", 19),
                   "xs17_354mhrzw32": ("006c00440035001300500060", 19),
                   "xs17_64km93z643": ("?-amoeba_8,4,4", 19),
                   "xs17_ogkaarzw65": ("?-snake_eater_on_hat", 19),
                   "xs17_raaczw178c": ("?-R-hat_and_eater", 19),
                   "xs17_3loz3462ac": ("018c01520036000400050003", 19),
                   "xs17_02lliczc96": ("0180012200d500150012000c", 19),
                   "xs17_mkhf0ck8z1": ("alef_and_?-boat", 19),
                   "xs17_0cp3qicz32": ("0060004c00190003001a0012000c", 19),
                   "xs17_3542sgc453": ("?-great_snake_eater_on_eater", 19),
                   "xs17_069jzrq221": ("03600346004900530020", 19),
                   "xs17_09v0sicz32": ("?-carrier_siamese_table_and_?-R-bee", 19),
                   "xs17_5b88a6z653": ("00c500ab00680008000a0006", 19),
                   "xs17_8ehegoz643": ("00c8008e0071000e00100018", 19),
                   "xs17_6970brzx32": ("?-R-bee_and_carrier_and_block", 19),
                   "xs17_0dr0f9z321": ("?17?095", 19),
                   "xs17_69fgjl8zx1": ("0036005400520031000e0008", 19),
                   "xs17_c970brzx32": ("?-hook_and_carrier_and_block", 19),
                   "xs17_6a88b52z253": ("cis-boat_with_long_nine_and_trans-boat", 19),
                   "xs17_39u0653z032": ("?-hook_siamese_snake_and_ship", 19),
                   "xs17_3p6862sgz11": ("?-amoeba_8,4,4", 19),
                   "xs17_0o8b96z8k96": ("01800240034c005200650002", 19),
                   "xs17_wpf0cicz321": ("?-eater_siamese_table_and_cis-beehive", 19),
                   "xs17_mp2sgzx34a4": ("00d001300080007c001200050002", 19),
                   "xs17_6a8q552z321": ("0066004a0028001a000500050002", 19),
                   "xs17_354cgc48gkc": ("0600040003b300a90046", 19),
                   "xs17_ckl3z047066": ("?-eater_on_table_and_block", 19),
                   "xs17_39s0si6z023": ("?-table_siamese_carrier_and_hook", 19),
                   "xs17_69baak8zx32": ("0030005c0042003d00020008000c", 19),
                   "xs17_g88b52zc953": ("0190012800a8006b00050002", 19),
                   "xs17_8ljgzx11dio": ("0300024001a000200030001300150008", 19),
                   "xs17_wmmge13z252": ("00c000ac002c0020001c000200050002", 19),
                   "xs17_3hu066z1246": ("00c4008a0079000300600060", 19),
                   "xs17_g88a52zd553": ("?-tub_with_nine_siamese_R-hat", 19),
                   "xs17_09v0c93z321": ("long_and_?-carrier", 19),
                   "xs17_699mggozx56": ("006000900090006d000b00080018", 19),
                   "xs17_cq23z230356": ("?-eater_siamese_table_and_ship", 19),
                   "xs17_2lla84cz321": ("006200550035000a00080004000c", 19),
                   "xs17_69eg8ozwc96": ("00c0012000e3001900260030", 19),
                   "xs17_xgbqicz4a43": ("0080014000800070000b001a0012000c", 19),
                   "xs17_gs2pmzx34a4": ("00800140009600790002001c0010", 19),
                   "xs17_gbhe0eioz01": ("tub_with_nine_and_cis-hook", 19),
                   "xs17_8kihf871zx1": ("00d8005400520031000e0008", 19),
                   "xs17_6icgf9z1221": ("004800780006001900250032", 19),
                   "xs17_0mp2sgz3443": ("0060009600990062001c0010", 19),
                   "xs17_259ab8ozw33": ("0034004c0020001f000100180018", 19),
                   "xs17_4adhegozw23": ("0018002400540035000b00080018", 19),
                   "xs17_mligoz1w6a4": ("?-Z_and_boats", 19),
                   "xs17_4ap3ck8z321": ("0064004a00390003000c00140008", 19),
                   "xs17_69mggzxci96": ("?-mango_line_beehive", 19),
                   "xs17_g6s17871z11": ("?-hat_siamese_carrier_siamese_hook", 19),
                   "xs17_i5q4oge2z11": ("00c000ac002a005200a30040", 19),
                   "xs17_0cp3ckoz321": ("?-hook_siamese_carrier_on_ship", 19),
                   "xs17_32q4ozxd871": ("?-eater_on_beehive_with_tail", 19),
                   "xs17_0j5s2sgz321": ("?-boat_with_leg_siamese_great_snake_eater", 19),
                   "xs17_39e0ooz039c": ("?-hook_and_carrier_and_block", 19),
                   "xs17_0g0siarz343": ("?-R-loop_on_beehive", 19),
                   "xs17_178kozx6aa6": ("boat_with_trans-tail_and_?-cap", 19),
                   "xs17_0ml2sgz3443": ("?-boat_with_cis-tail_on_pond", 19),
                   "xs17_69ic8a6zx56": ("0060009000480035001300500060", 19),
                   "xs17_0ggciarz343": ("?-R-bee_on_loop", 19),
                   "xs17_696o6iozw23": ("003000480031000f00300024000c", 19),
                   "xs17_ca1t6zx1156": ("00c000a00026003d0001000a000c", 19),
                   "xs17_2lligoz1226": ("?17?006", 19),
                   "xs17_rai312koz01": ("009800f4000200c100a30040", 19),
                   "xs17_j96o8a6z121": ("006600490032000c000800280030", 19),
                   "xs17_oggo8a53z66": ("00d800d0001000180008000a00050003", 19),
                   "xs17_0gilicz32ac": ("00600090015300950014000c", 19),
                   "xs17_4aabaiczx32": ("001800240029006b002800280010", 19),
                   "xs17_cill2zx34a4": ("008001400082007500150012000c", 19),
                   "xs17_25aczca5113": ("trans-boat_with_long_leg_and_?-long_boat", 19),
                   "xs17_0amgm96z321": ("00600050001c0022001500350002", 19),
                   "xs17_69iczx11dio": ("0300024001a00020002c001200090006", 19),
                   "xs17_rh6o8zx34a4": ("01b0011000c0003c002200050002", 19),
                   "xs17_259q453z311": ("006600490032000c000800070001", 19),
                   "xs17_354264215ac": ("060c04d203650003", 19),
                   "xs17_wg8ob96z69c": ("00c0012001a000300020001300090006", 19),
                   "xs17_0co2djoz321": ("00600050001300350024000a0006", 19),
                   "xs17_0bq1egoz321": ("integral_with_hook_and_hook", 19),
                   "xs17_0652sgzca53": ("?-cis-boat_with_tail_on_long_ship", 19),
                   "xs17_0jhu0ok8z32": ("?-eater_siamese_long_hook_and_boat", 19),
                   "xs17_03lkia4z652": ("00c000a3005500140012000a0004", 19),
                   "xs17_2lla8cz1243": ("004400aa00a9005600100030", 19),
                   "xs17_g88b96z11da": ("?-scorpio_siamese_snake_eater", 19),
                   "xs17_69arzx12552": ("?-beehive_with_tail_siamese_loop", 19),
                   "xs17_wjhu0ooz252": ("?-tub_with_tail_siamese_long_hook_and_block", 19),
                   "xs17_69akg8oz253": ("0062009500560028000800100018", 19),
                   "xs17_g88a53zc953": ("0190012800a8006a00050003", 19),
                   "xs17_0c88bdz2553": ("?17?114", 19),
                   "xs17_03lka23z643": ("?-amoeba_8,4,4", 19),
                   "xs17_696o652z065": ("0060009300650018006000a00040", 19),
                   "xs17_0ogil96z4a6": ("cis-loaf_with_long_leg_and_?-boat", 19),
                   "xs17_0o4km96z643": ("00c0009800640014001600090006", 19),
                   "xs17_08o69a4zmq1": ("02c00348003800060009000a0004", 19),
                   "xs17_wjhu066z252": ("?-tub_with_tail_siamese_long_hook_and_trans-block", 19),
                   "xs17_3pc0siczw23": ("?-siamese_carriers_on_R-bee", 19),
                   "xs17_gwci53zdd11": ("01b001a00020002c001200050003", 19),
                   "xs17_0c9jz651256": ("00c000ac0029005300a000c0", 19),
                   "xs17_2lla8cz3421": ("006200950055002a0008000c", 19),
                   "xs17_03l2sgz6943": ("00c0012300950062001c0010", 19),
                   "xs17_2560uiz0653": ("?-ship_on_table_and_boat", 19),
                   "xs17_2lm88cz3443": ("00620095009600680008000c", 19),
                   "xs17_wiu0696z643": ("?17?111", 19),
                   "xs17_g88ml96z123": ("00300050004c0032000d00090006", 19),
                   "xs17_25b88a6z0253": ("cis-boat_with_long_nine_and_?-boat", 19),
                   "xs17_1784ozx17871": ("010001c000200048003e0001000e0008", 19),
                   "xs17_0g8kaarz3421": ("00d800500050002c001200090006", 19),
                   "xs17_4s0fhe8zw121": ("00180028002b006a001200140008", 19),
                   "xs17_4a9b88czx352": ("00300012001500d6009000500020", 19),
                   "xs17_4aab88czx352": ("00300012001500d6005000500020", 19),
                   "xs17_31e8zw311da4": ("cis-boat_with_long_leg_and_?-eater", 19),
                   "xs17_259mggozw4a6": ("trans-loaf_with_long_leg_and_?-boat", 19),
                   "xs17_c4gka96z6221": ("00cc004400500034000a00090006", 19),
                   "xs17_wogka23z62ac": ("0180008000a000500013003500040006", 19),
                   "xs17_0oggm952z4a6": ("trans-loaf_with_long_leg_and_trans-boat", 19),
                   "xs17_xggm952zca43": ("?-loaf_with_trans-tail_siamese_boat_with_trans-tail", 19),
                   "xs17_0ggcaarz3421": ("00d8005000500034000a00090006", 19),
                   "xs17_g8id9a4z1243": ("003000480092006d0009000a0004", 19),
                   "xs17_04a96zc87113": ("0180010400ea002900260060", 19),
                   "xs17_032q4oz69701": ("?-R-bee_on_beehive_with_tail", 19),
                   "xs17_08kkm952z321": ("00c000a000380044003a00090006", 19),
                   "xs17_2egm9a4z0641": ("004000730009006c009000500020", 19),
                   "xs17_25a88a6zw39c": ("tub_with_long_nine_and_?-carrier", 19),
                   "xs17_31e88gzca511": ("0183014100ae002800280010", 19),
                   "xs17_0o4a952z354c": ("?-mango_with_trans-tail_siamese_eater", 19),
                   "xs17_039u0ok8z311": ("?-eater_siamese_hook_and_?-boat", 19),
                   "xs17_25b88a52zw33": ("?-boat_long_line_tub_and_block", 19),
                   "xs17_4aab94ozx321": ("001800280040005e0021000e0018", 19),
                   "xs17_354mik8z0252": ("00c000a20025006a004800280010", 19),
                   "xs17_0jhege2z1221": ("003000480034000a000a002b0030", 19),
                   "xs17_32aczw3115ac": ("trans-boat_with_long_leg_and_?-eater", 19),
                   "xs17_31e88a6z0253": ("?-long_hook_siamese_eater_and_?-boat", 19),
                   "xs17_0g8ge13z6b8o": ("0300020001c000230042003a000c", 19),
                   "xs17_02596zc93113": ("?-table_siamese_carrier_and_loaf", 19),
                   "xs17_4a9baa4zw252": ("racetrack_II_and_tub", 19),
                   "xs17_259a4z3115a4": ("008c0148012800aa00450002", 19),
                   "xs17_25a84ozc8711": ("0182010500ea002800240018", 19),
                   "xs17_0354m96z6421": ("00c0008300450024001600090006", 19),
                   "xs17_0gjlkk8z1246": ("00200050009300d5001400140008", 19),
                   "xs17_0cim453z6221": ("00c000a00020006c004a00320003", 19),
                   "xs17_xogka52z6952": ("?-barge_with_leg_on_loaf", 19),
                   "xs17_256o8a6z2521": ("?-tub_with_tail_siamese_eater_on_boat", 19),
                   "xs17_wgiu0696z252": ("?-tub_with_tail_siamese_table_and_trans-beehive", 19),
                   "xs17_wg0s2qrz2521": ("?17?051", 19),
                   "xs17_358gogkczx66": ("?-canoe_siamese_hook_and_cis-block", 19),
                   "xs17_35ak8a6z0321": ("0060005300290016000800280030", 19),
                   "xs17_031i4oz69d11": ("00c0012301a1003200240018", 19),
                   "xs17_wogka52z62ac": ("barge_with_leg_and_?-hook", 19),
                   "xs17_xg8o653z6a43": ("?-boat_with_cis-nine_on_ship", 19),
                   "xs17_03p6ge2z6221": ("00c00043005900260010000e0002", 19),
                   "xs17_064kl3zc8701": ("long_hook_and_?-integral", 19),
                   "xs17_025a8a6z6513": ("tub_with_nine_and_?-hook", 19),
                   "xs17_4ai3gzx11d96": ("00c0012001a0003000230012000a0004", 19),
                   "xs17_0ggcahrz3421": ("00d8008800500034000a00090006", 19),
                   "xs17_xg8o653zca43": ("?-boat_with_trans-nine_on_ship", 19),
                   "xs17_35aczw3115a4": ("tub_with_long_leg_and_?-long_ship", 19),
                   "xs17_255q88czw643": ("004000a000a30059001600100030", 19),
                   "xs17_0g88a52zol56": ("?-tub_with_nine_on_eater", 19),
                   "xs17_69mggkcz0641": ("?-beehive_with_long_nine_siamese_carrier", 19),
                   "xs17_ciabgzx122ac": ("0180014000400050002b000a0012000c", 19),
                   "xs17_ciligzx1078c": ("0180010000e00010003200150012000c", 19),
                   "xs17_25a88gzoid11": ("0302024501aa002800280010", 19),
                   "xs17_0ggkaarz3421": ("?-R-loaf_on_hat", 19),
                   "xs17_641v0ciczw11": ("0030009200d5001500120030", 19),
                   "xs17_02ege96z2521": ("006000900070000c007200450002", 19),
                   "xs17_05b88gzoid11": ("0300024501ab002800280010", 19),
                   "xs17_35a84oz4a511": ("0182014500aa002800480030", 19),
                   "xs17_35a84k8z06511": ("00c000a300550014002400280010", 19),
                   "xs17_0oggka52z4aa4": ("trans-barge_with_long_leg_and_trans-beehive", 19),
                   "xs17_2552sgzog8421": ("?-beehive_with_tail_siamese_long_canoe", 19),
                   "xs17_259aczy0315a4": ("?17?057", 19),
                   "xs17_25a84k8z4a511": ("0082014500aa0028004800500020", 19),
                   "xs17_252sggzx8ka52": ("?-long_barge_with_cis-tail_siamese_tub_with_tail", 19),
                   "xs17_ca1688gzwc871": ("006000a0010300c1002e00280010", 19),
                   "xs17_0g8o69icz3421": ("?-R-mango_on_mango", 19),
                   "xs17_64kr2qr": ("?-eater_on_table_and_block", 20),
                   "xs17_641vgbr": ("?-Z_siamese_carrier_siamese_snake_and_block", 20),
                   "xs17_3pq3qic": ("?17?074", 20),
                   "xs17_25b8ra96": ("?-boat_with_cis-tail_siamese_loop", 20),
                   "xs17_drz1qq23": ("02d0036b000b00080018", 20),
                   "xs17_33gv1oi6": ("?-carrier_siamese_Z_siamese_block", 20),
                   "xs17_4a60uhar": ("00b000d2001500d600a0", 20),
                   "xs17_259ar2qk": ("00d0005c008200790016", 20),
                   "xs17_drz122qr": ("036003400040005b002d", 20),
                   "xs17_25b8ri96": ("006a00ad0041003a000c", 20),
                   "xs17_69lic0f9": ("00c60049005500d2000c", 20),
                   "xs17_3lkk8zrm": ("?-krake_siamese_snake", 20),
                   "xs17_32hv0si6": ("00b000d3001500140036", 20),
                   "xs17_69jz6aar": ("?-long_shillelagh_on_eater", 20),
                   "xs17_drz32qic": ("02d80368000b00090006", 20),
                   "xs17_wraik8zbd": ("016001a0001b000a001200140008", 20),
                   "xs17_mkie0dbz1": ("R-loop_and_?-snake", 20),
                   "xs17_cq1ticz23": ("004c007a0001001d0012000c", 20),
                   "xs17_8ehe8zmq1": ("02c8034e0031000e0008", 20),
                   "xs17_25b8o0uic": ("?-boat_with_cis-tail_and_cap", 20),
                   "xs17_321f871ac": ("0198012800ab006d", 20),
                   "xs17_69r8b5z32": ("00660049001b0008000b0005", 20),
                   "xs17_6ao8brz32": ("?-very_long_eater_siamese_carrier_and_block", 20),
                   "xs17_64132qb96": ("00cc0179010300e00020", 20),
                   "xs17_mp3ck8z65": ("00d600b90003000c00140008", 20),
                   "xs17_178bp6426": ("01b000ab008d00700010", 20),
                   "xs17_4a53gv146": ("?-Z_siamese_carrier_and_long_boat", 20),
                   "xs17_25akgf1e8": ("008c014a00aa004b0030", 20),
                   "xs17_33gv16426": ("?-Z-on_snake_and_block", 20),
                   "xs17_178kkb2ac": ("?-beehive_with_tail_on_eater", 20),
                   "xs17_0at1qrz32": ("006c002c0040005c00290003", 20),
                   "xs17_cp3z32qic": ("0180024003430059006c", 20),
                   "xs17_2egu15a8o": ("010c01ca002a004b0030", 20),
                   "xs17_0ml56zcip": ("long_shillelagh_and_?-cap", 20),
                   "xs17_178f1eg8o": ("01b000a800a8006b0005", 20),
                   "xs17_69r2qkz32": ("00660049001b0002001a0014", 20),
                   "xs17_35a8o0uic": ("cap_and_?-boat_with_trans-tail", 20),
                   "xs17_354cgs2qk": ("01b000a8012e00c10003", 20),
                   "xs17_32ako0uic": ("boat_with_trans-tail_and_?-cap", 20),
                   "xs17_iu0e96z65": ("00d200be0000000e00090006", 20),
                   "xs17_32ako0uh3": ("018101470048005400d8", 20),
                   "xs17_178ko0uic": ("0180008600a500550036", 20),
                   "xs17_32hv04a96": ("016201a5002900260060", 20),
                   "xs17_3lkm93z32": ("006300550014003400480060", 20),
                   "xs17_31ege1ego": ("01880154005400550023", 20),
                   "xs17_3pmzw34aic": ("?-loaf_with_trans-tail_siamese_shillelagh", 20),
                   "xs17_mligkcz146": ("?-very_long_eater_siamese_carrier_and_cis-boat", 20),
                   "xs17_31kmicz256": ("00c20085002b006800480030", 20),
                   "xs17_o8alicz643": ("00d80088006a00150012000c", 20),
                   "xs17_amgmliczx1": ("0014001a0002001b002a0012000c", 20),
                   "xs17_256o8gka53": ("?-long_boat_with_long_tail_on_boat", 20),
                   "xs17_35iczxd596": ("018001400090006b000a00090006", 20),
                   "xs17_0jhu066z56": ("00a000d30011001e000000060006", 20),
                   "xs17_356o8go8a6": ("?-eater_siamese_snake_on_ship", 20),
                   "xs17_kc3qicz123": ("0034004c0063001a0012000c", 20),
                   "xs17_069jzc45lo": ("long_shillelagh_and_?-long_hook", 20),
                   "xs17_69lmzx34ac": ("0180014000800076001500090006", 20),
                   "xs17_wmd1egoz65": ("00c000a00016000d0001000e00100018", 20),
                   "xs17_03lkczo9a6": ("03000123015500d4000c", 20),
                   "xs17_69bq23z321": ("00660049002b001a00020003", 20),
                   "xs17_660uh3z253": ("?-long_hook_on_boat_and_block", 20),
                   "xs17_3lk2sgz643": ("great_snake_eater_and_hook", 20),
                   "xs17_j9mgmaz121": ("006600490036000400340028", 20),
                   "xs17_69ab8oz253": ("00620095005600d000100018", 20),
                   "xs17_0mmge13z56": ("00c00080007000080068006b0005", 20),
                   "xs17_ogjla4z6a4": ("cis-long_boat_with_long_leg_and_?-boat", 20),
                   "xs17_0br8b52z32": ("?-boat_with_cis-tail_siamese_carrier_and_block", 20),
                   "xs17_dj8gkcz643": ("00cd0093006800100014000c", 20),
                   "xs17_0jhu0ooz56": ("?-long_hook_siamese_snake_eater_and_cis-block", 20),
                   "xs17_0gilicz1qm": ("00c0012002a0012d002b0010", 20),
                   "xs17_8p7gs26z23": ("00600020002c0064001500130030", 20),
                   "xs17_8ehdiczw56": ("0030004800b3008d00700010", 20),
                   "xs17_3iab96z321": ("00630052002a000b00090006", 20),
                   "xs17_gbbo8b5z11": ("?-snake_eater_siamese_hook_and_block", 20),
                   "xs17_6ikm952z32": ("0066005200140016000900050002", 20),
                   "xs17_03lkczok96": ("03000283013500d4000c", 20),
                   "xs17_raaczx3552": ("R-hat_and_R-bee", 20),
                   "xs17_gbdz11dik8": ("?-loaf_with_trans-tail_on_snake", 20),
                   "xs17_03lkiczc96": ("0180012300d500140012000c", 20),
                   "xs17_0mllicz641": ("00c00096003500150012000c", 20),
                   "xs17_2lmge13z32": ("0062005500160010000e00010003", 20),
                   "xs17_3iaczw1pl3": ("03000120015000d300150018", 20),
                   "xs17_08u1ticz32": ("00600048001e0001001d0012000c", 20),
                   "xs17_gjlkicz146": ("0030009300d500140012000c", 20),
                   "xs17_39u06acz32": ("?-hook_siamese_carrier_and_?-ship", 20),
                   "xs17_2lmge2z1ac": ("0088015500d3001000e00080", 20),
                   "xs17_3542sgc2ko": ("03300250015600890003", 20),
                   "xs17_8o1vg33z23": ("?-Z_and_table_and_block", 20),
                   "xs17_ciarzwc453": ("?-loop_on_eater", 20),
                   "xs17_31km96z643": ("?-carrier_siamese_beehive_on_eater", 20),
                   "xs17_raarzw1226": ("?-snake_eater_siamese_table_and_cis-table", 20),
                   "xs17_6is0fpzx32": ("004c00790003001c00240030", 20),
                   "xs17_09v0796z32": ("00600049001f0000000700090006", 20),
                   "xs17_6t1ege2z11": ("00600024002a006a004b0030", 20),
                   "xs17_69egmazx56": ("006000900070000d006b0050", 20),
                   "xs17_c88e1daz33": ("?-loop_siamese_table_and_block", 20),
                   "xs17_6s1f871z11": ("?-R-hat_siamese_carrier_siamese_table", 20),
                   "xs17_3p6kk8z643": ("00c300990066002800280010", 20),
                   "xs17_ckgojdzx66": ("?17?130", 20),
                   "xs17_3hu08ozxbd": ("0180011000f0000d002b0030", 20),
                   "xs17_25a8oge1e8": ("0104028a010a00eb0030", 20),
                   "xs17_j9cz11d952": ("01980128006b0009000a0004", 20),
                   "xs17_3pmzw34a96": ("0180013000dc0002000500090006", 20),
                   "xs17_3lkia4z1ac": ("018801550053009000a00040", 20),
                   "xs17_wmlla4z643": ("?-R-bee_siamese_tub_with_tail_siamese_eater", 20),
                   "xs17_c88m93z39c": ("0180012000d000230029006c", 20),
                   "xs17_cilmzwca52": ("00600090015300d5000a0004", 20),
                   "xs17_wmkiarz252": ("?17?062", 20),
                   "xs17_6a88b5z653": ("?17?089", 20),
                   "xs17_39mgmaz321": ("?17?094", 20),
                   "xs17_ciarzxc952": ("?17?123", 20),
                   "xs17_3lk2sgz343": ("?17?136", 20),
                   "xs17_69lmzx34a6": ("?17?151", 20),
                   "xs17_gilmz1w6jo": ("?17?160", 20),
                   "xs17_c88bp46z33": ("?17?170", 20),
                   "xs17_gjlmz1w1156": ("?-eater_siamese_table_and_ship", 20),
                   "xs17_32qbzx1178c": ("elevener_and_?-table", 20),
                   "xs17_31eozw1qaa4": ("0300020001d0006b000a000a0004", 20),
                   "xs17_c871z31178c": ("?-eater_siamese_table_and_eater", 20),
                   "xs17_69ligzx4a96": ("?-loaf_line_loaf", 20),
                   "xs17_31eg84215ac": ("060c0512012501430080", 20),
                   "xs17_iu069a4z146": ("?-table_siamese_carrier_and_cis-loaf", 20),
                   "xs17_4aab9czw652": ("iron_and_trans-boat", 20),
                   "xs17_09v04a96z32": ("?-table_siamese_carrier_and_loaf", 20),
                   "xs17_0mljgoz1246": ("00200056009500d300100018", 20),
                   "xs17_0j1ug8oz343": ("?-long_eater_siamese_snake_on_beehive", 20),
                   "xs17_xgil96z6a43": ("?-loaf_with_cis_tail_siamese_boat_with_cis-tail", 20),
                   "xs17_oggs2552z66": ("?-beehive_with_tail_siamese_table_and_block", 20),
                   "xs17_0gs253zpia4": ("03200250015c008200050003", 20),
                   "xs17_69a4z32139c": ("?-snake_siamese_carrier_and_loaf", 20),
                   "xs17_0j96z32cga6": ("00c001400206018900530060", 20),
                   "xs17_8k8gehrzw23": ("?-tub_with_leg_on_C", 20),
                   "xs17_0db88cz6513": ("00c000ad002b00680008000c", 20),
                   "xs17_039u066zca1": ("?-very_long_snake_siamese_hook_and_block", 20),
                   "xs17_gwci53z11dd": ("018001400090006b000b00080018", 20),
                   "xs17_0mljgoz1226": ("00200056005500d300100018", 20),
                   "xs17_g09v0si6z11": ("?-table_siamese_carrier_and_hook", 20),
                   "xs17_697o4kozw23": ("0030005000560029000b00080018", 20),
                   "xs17_6ic8a52z643": ("00c60092006c0008000a00050002", 20),
                   "xs17_0kc0f96z346": ("?17?043", 20),
                   "xs17_g8o652zd54c": ("boat_on_ship_and_cis-table", 20),
                   "xs17_31e88czc871": ("?-eater_siamese_table_and_eater", 20),
                   "xs17_9fgcia4z023": ("006000260029006a001400100030", 20),
                   "xs17_65la8a6zw23": ("003000500055002b000800280030", 20),
                   "xs17_6ic8a52z343": ("00660092006c0008000a00050002", 20),
                   "xs17_g88bp453z23": ("?17?163", 20),
                   "xs17_gs2qbzx34a4": ("tub_with_long_leg_and_trans-legs", 20),
                   "xs17_ckggm96z641": ("00cc009400300010001600090006", 20),
                   "xs17_0giu0696z56": ("?-snake_eater_siamese_table_and_trans-beehive", 20),
                   "xs17_32qkgoz3146": ("?-snake_eater_siamese_table_on_carrier", 20),
                   "xs17_25iczw9f0cc": ("?-tub_with_long_tail_siamese_table_and_block", 20),
                   "xs17_cimk13z6421": ("00cc00920056003400010003", 20),
                   "xs17_xmk453z6a43": ("?-long_hook_and_tub_with_tail", 20),
                   "xs17_c48a53z6513": ("boat_with_long_tail_and_?-hook", 20),
                   "xs17_3j0v146z121": ("006c0069000b0008002800500020", 20),
                   "xs17_6akgf9z0641": ("?-table_on_carrier_on_boat", 20),
                   "xs17_2552sgz4a53": ("00820145014a008c00700010", 20),
                   "xs17_gg0si96z1cb": ("?-R-mango_on_shillelagh", 20),
                   "xs17_32arzx12596": ("0180008000a001b80004000a00090006", 20),
                   "xs17_xmk453zca43": ("boat_with_trans-tail_and_?-long_hook", 20),
                   "xs17_g8jdik8z123": ("0030005000560029000a00140018", 20),
                   "xs17_35s2sgz0643": ("00c000a30039004600380008", 20),
                   "xs17_c88e1e8z352": ("?-hat_siamese_table_and_boat", 20),
                   "xs17_06t1eoz6221": ("00c00046005d0021000e0018", 20),
                   "xs17_35is0cczw65": ("00c000a0004b003d000000300030", 20),
                   "xs17_cill2zx25a4": ("0080014000a2005500150012000c", 20),
                   "xs17_0mp3z342156": ("00c000a00023005900960060", 20),
                   "xs17_i5d2cga6z11": ("00c00084002a006900930060", 20),
                   "xs17_g8idicz1256": ("?-beehive_siamese_boat_on_beehive_siamese_tub", 20),
                   "xs17_32qkzx34a96": ("0180008000b0005c0002000500090006", 20),
                   "xs17_4a9dikozx32": ("00180024004a003900070008000c", 20),
                   "xs17_5b88czx3553": ("00a000d000100016003500050006", 20),
                   "xs17_0ggciarz643": ("?-hook_on_loop", 20),
                   "xs17_4a96z32139c": ("0180012000660029004a0064", 20),
                   "xs17_g8k453zd54c": ("01b000a80094018400050003", 20),
                   "xs17_6248ge132ac": ("00c003a3042506280010", 20),
                   "xs17_0gilla4z346": ("0060009000d200150015000a0004", 20),
                   "xs17_0ol3zc87066": ("?-long_hook_siamese_long_snake_and_trans-block", 20),
                   "xs17_25iczw19l96": ("01000280013000d200150012000c", 20),
                   "xs17_0bq1da4z321": ("006000500010003600050032002c", 20),
                   "xs17_ciic871z641": ("?-pond_siamese_eater_siamese_carrier", 20),
                   "xs17_ad1u8zx1256": ("?-boat_with_leg_siamese_loop", 20),
                   "xs17_02llicz25a4": ("0060009001520155008a0004", 20),
                   "xs17_g8hf0fhoz01": ("tub_with_long_leg_and_?-long_hook", 20),
                   "xs17_3lkaacz1221": ("006200550015002a00280018", 20),
                   "xs17_0iu0e96z641": ("?-table_siamese_carrier_and_?-R-bee", 20),
                   "xs17_39c88cz2553": ("?-table_siamese_carrier_and_R-bee", 20),
                   "xs17_3lm88cz3421": ("00c600a9006a001400100030", 20),
                   "xs17_cill2zx254c": ("0180008000a2005500150012000c", 20),
                   "xs17_cim453z6421": ("00cc00920056002400050003", 20),
                   "xs17_0j9ege2z321": ("006000530029000e0010000e0002", 20),
                   "xs17_gie0e93z146": ("00c000900070000000730049000c", 20),
                   "xs17_0ggm93zo9a6": ("0300024001ac002a00320003", 20),
                   "xs17_358628c48a6": ("060004c302990136", 20),
                   "xs17_wggra96z652": ("00c000a000500010001b000a00090006", 20),
                   "xs17_65p6o8a6zx1": ("0060009300d1002e00280010", 20),
                   "xs17_0cq231e8z65": ("?-eater_siamese_eater_siamese_long_snake", 20),
                   "xs17_08kq23z6aa6": ("0180008000b6005500250006", 20),
                   "xs17_3iacz1215ac": ("0188009400a8006a00050003", 20),
                   "xs17_4aarzx12596": ("00c0012000a00040003b000a000a0004", 20),
                   "xs17_c88c93z3156": ("?-table_siamese_carrier_and_hook", 20),
                   "xs17_gill2z1w69c": ("0180012200d5001500120030", 20),
                   "xs17_ca1t2kozw23": ("?-amoeba_6,6,4", 20),
                   "xs17_31egozx6aa6": ("integral_and_?-cap", 20),
                   "xs17_mll2z10254c": ("0180008000a2005500150036", 20),
                   "xs17_3123146178c": ("?-snake_siamese_carrier_on_eater", 20),
                   "xs17_0mlla4z1226": ("00200056005500d5000a0004", 20),
                   "xs17_39u06acz032": ("?-hook_siamese_snake_and_cis-ship", 20),
                   "xs17_o970796z023": ("0036005400540023000100040006", 20),
                   "xs17_4s0si52z643": ("00c4009c0060001c001200050002", 20),
                   "xs17_0jhu0652z32": ("?-eater_siamese_long_hook_and_boat", 20),
                   "xs17_ckl3zw34aa4": ("?-beehive_with_tail_on_eater", 20),
                   "xs17_xgil96zca52": ("0180014000a000500012001500090006", 20),
                   "xs17_39s0cicz321": ("?-hook_siamese_carrier_and_?-beehive", 20),
                   "xs17_xgil96zca43": ("?-loaf_with_cis-tail_siamese_tub_with_trans-tail", 20),
                   "xs17_ca1t6zx1253": ("006000a00046003d0001000a000c", 20),
                   "xs17_03pmz8ka252": ("010002830159005600a00040", 20),
                   "xs17_0oggm93zca6": ("0180015800d00010001600090003", 20),
                   "xs17_0dbgz69pz32": ("0cc0092d032b0010", 20),
                   "xs17_2llmz641023": ("00c200950035001600400060", 20),
                   "xs17_9f0s2kozw23": ("00600024002a0069000b00080018", 20),
                   "xs17_c82t2sgz311": ("006c00280022001d0002001c0010", 20),
                   "xs17_2egm453zw65": ("00c000a00020006d000b00700040", 20),
                   "xs17_0ggraicz1ac": ("?-long_hook_with_tail_siamese_loop", 20),
                   "xs17_x8ka53z255d": ("0180014000a00050002b000a000a0004", 20),
                   "xs17_31e8z3115ac": ("trans-boat_with_long_leg_and_?-eater", 20),
                   "xs17_695q8a6zw32": ("?-very_long_snake_siamese_eater_on_loaf", 20),
                   "xs17_69dik8z0643": ("0060009300b1004e00280010", 20),
                   "xs17_8ehdik8z023": ("0030001000160069002a00240018", 20),
                   "xs17_xohf0ccz253": ("?-long_hook_on_boat_and_cis-block", 20),
                   "xs17_32akgoz4aa6": ("0182008500a5005600100030", 20),
                   "xs17_3p6ge2kozw1": ("00c000ac002a004900530020", 20),
                   "xs17_g6q0si53z11": ("boat_with_leg_and_?-shillelagh", 20),
                   "xs17_065licz4a43": ("00800146008500750012000c", 20),
                   "xs17_ciic871z065": ("?-pond_siamese_eater_siamese_snake", 20),
                   "xs17_0j1u0uiz121": ("tub_with_long_nine_and_cis-table", 20),
                   "xs17_69q3pczw121": ("00300048002e0061004e0018", 20),
                   "xs17_0pf0352z643": ("?-shillelagh_siamese_table_and_boat", 20),
                   "xs17_gilmz1w34ac": ("?-boat_with_trans-tail_siamese_table_and_boat", 20),
                   "xs17_h7o312koz11": ("00d800540042002100a300c0", 20),
                   "xs17_c88a52sgz33": ("00c000c0000300f2008a00140008", 20),
                   "xs17_g85r8b5z121": ("006c00280044003a000900050002", 20),
                   "xs17_rb8ozw122ac": ("01b001a000280034000400050003", 20),
                   "xs17_0g8o653z1qm": ("?17?060", 20),
                   "xs17_39c8a52z253": ("?17?076", 20),
                   "xs17_8kkjaaczx23": ("?17?164", 20),
                   "xs17_0356o8zca521": ("?-long_boat_with_trans-tail_on_ship", 20),
                   "xs17_04aabgzca511": ("0180014400aa002a002b0010", 20),
                   "xs17_0mlhik8z3201": ("0060005600150031001200140008", 20),
                   "xs17_025a8a6z2553": ("tub_with_nine_and_?-R-bee", 20),
                   "xs17_0g88e13zok96": ("03000290012800c8000e00010003", 20),
                   "xs17_g8kid96z1221": ("?-loaf_siamese_loaf_siamese_loaf", 20),
                   "xs17_0gs2t52z3421": ("00600090005c0022001d00050002", 20),
                   "xs17_69eg8ka4zw23": ("004000a200a5006a001400100030", 20),
                   "xs17_0gie0dbz1246": ("00d000b0000000730049000a0004", 20),
                   "xs17_642t28cz2521": ("00620025004200bc004000100030", 20),
                   "xs17_xg8ob96z4a43": ("00c00140010000f000280008000a00050002", 20),
                   "xs17_03lo0ooz4a43": ("?-tub_with_leg_siamese_long_snake_and_?-block", 20),
                   "xs17_0g8ie0e93z23": ("01800158005000d4000a00020003", 20),
                   "xs17_xggka53zca52": ("0180014000a0005000100014000a00050003", 20),
                   "xs17_xogka52z2596": ("0080014000a00050001000360009000a0004", 20),
                   "xs17_xggka53z4a96": ("0180014000a0005000100016000900050002", 20),
                   "xs17_03pe0ooz6221": ("?-snake_eater_siamese_hook_and_block", 20),
                   "xs17_ci96zw1132ac": ("?-mango_with_cis-tail_siamese_eater", 20),
                   "xs17_31e8gzw354ko": ("03000280009000a8006e00010003", 20),
                   "xs17_069a4oz4ad11": ("0080014601a9002a00240018", 20),
                   "xs17_xogka52z4aa6": ("barge_with_leg_and_?-R-bee", 20),
                   "xs17_0178kk8z2553": ("?-beehive_with_tail_on_R-bee", 20),
                   "xs17_0gbb871z1252": ("008000e0001000d200d5000a0004", 20),
                   "xs17_0ggs252z3ego": ("?-tub_with_tail_siamese_eaters", 20),
                   "xs17_4ap56zw12552": ("004000a000a600450039000a0004", 20),
                   "xs17_32akozx622ac": ("?-boat_with_trans-tail_and_long_hook", 20),
                   "xs17_0gs2dik8z641": ("?-loaf_siamese_tub_with_tail_siamese_carrier", 20),
                   "xs17_39cggkcz0643": ("00c000930031000e000800280030", 20),
                   "xs17_312kozw32ako": ("?-boat_with_trans-tail_on_canoe", 20),
                   "xs17_4a4o796zw123": ("003000520055002a000800140018", 20),
                   "xs17_358ge96z0321": ("?-very_long_shillelagh_on_R-bee", 20),
                   "xs17_gw8ka52z11dd": ("trans-long_barge_with_long_leg_and_?-block", 20),
                   "xs17_354k8zx11d96": ("01800140004000580028000b00090006", 20),
                   "xs17_0j9c871z1252": ("?-carrier_siamese_eater_on_barge", 20),
                   "xs17_31eozw122ego": ("?-eater_siamese_snake_eater_siamese_eater", 20),
                   "xs17_35a4ozx12596": ("0180014000a000480034000a00090006", 20),
                   "xs17_25akozy135ac": ("very_long_boat_on_long_ship", 20),
                   "xs17_39mggkcz0641": ("00c000930069000c000800280030", 20),
                   "xs17_032q4oz69521": ("00c0012300a2005a00240018", 20),
                   "xs17_32akggkczx66": ("00c000400050002b000b000800280030", 20),
                   "xs17_35a8kk8z0253": ("00c000a200550016002800280010", 20),
                   "xs17_31e8zw3115ac": ("trans-boat_with_long_leg_and_?-eater", 20),
                   "xs17_25akozwca226": ("long_hook_and_?-very_long_boat", 20),
                   "xs17_032q4goz3543": ("006000a30082007a000400100018", 20),
                   "xs17_035s2acz2521": ("004000a30045003c0002000a000c", 20),
                   "xs17_25ic8a6z0343": ("?-hook_on_beehive_on_tub", 20),
                   "xs17_064kl3z4a521": ("long_hook_and_very_long_boat", 20),
                   "xs17_039u06a4z311": ("?-eater_siamese_hook_and_?-boat", 20),
                   "xs17_ciabgzx125a4": ("0080014000a00050002b000a0012000c", 20),
                   "xs17_0358gkcz2553": ("004000a300a5006800100014000c", 20),
                   "xs17_252s0f9z0321": ("tub_with_long_nine_and_para-table", 20),
                   "xs17_04akl3zca221": ("01800158005400a400450003", 20),
                   "xs17_04a96z4ad113": ("0080014401aa002900260060", 20),
                   "xs17_2596o8z4a521": ("?-barge_with_trans-tail_on_loaf", 20),
                   "xs17_0gjlkk8z1226": ("00200050005300d5001400140008", 20),
                   "xs17_04a96z311da4": ("cis-boat_with_long_leg_and_?-loaf", 20),
                   "xs17_358gozwok871": ("03000280004300250062001c0010", 20),
                   "xs17_25b88gzca511": ("?-binocle_boats", 20),
                   "xs17_0oggka52zca6": ("trans-barge_with_long_leg_and_?-ship", 20),
                   "xs17_652sggozw4a6": ("00c0014000820075001600100030", 20),
                   "xs17_06a8a52z3552": ("006000a600aa0048000a00050002", 20),
                   "xs17_69eg8k8z0643": ("006000930071000e001000280010", 20),
                   "xs17_321e8gzc4871": ("01830082010100ee00280010", 20),
                   "xs17_3p6gzw123ck8": ("03000260019000280018000600050002", 20),
                   "xs17_4a9di4ozx321": ("?-mangos_siamese_boat", 20),
                   "xs17_032q4ozc9701": ("0180012300e2001a00240018", 20),
                   "xs17_4aajk46zx146": ("00600023002900cc005000500020", 20),
                   "xs17_08p78kk8z321": ("00c000a000260069001600100030", 20),
                   "xs17_259a4oz0ad11": ("00800145012b00a800480030", 20),
                   "xs17_31eozx1259a4": ("?-mango_with_trans-tail_siamese_eater", 20),
                   "xs17_0j9mkk8z3201": ("?-very_long_shillelagh_siamese_long_bee_siamese_hat", 20),
                   "xs17_69abk4ozx121": ("003000480028006a00150012000c", 20),
                   "xs17_0okih3zca221": ("018001580054005200310003", 20),
                   "xs17_3hu08k8zw346": ("00c00088007e0001001300280010", 20),
                   "xs17_ckggka23z066": ("00c00040005000280008000b002b0030", 20),
                   "xs17_gill2z1w34a4": ("?-tub_with_tail_siamese_table_and_cis-beehive", 20),
                   "xs17_w4s0f96z2521": ("tub_with_long_leg_and_shift-cap", 20),
                   "xs17_xogka52zca26": ("barge_with_leg_and_meta-hook", 20),
                   "xs17_25aczw311da4": ("cis-boat_with_long_leg_and_?-long_boat", 20),
                   "xs17_0ggmlicz1246": ("0030004800a8006b0009000a0004", 20),
                   "xs17_25a8czwca513": ("?17?154", 20),
                   "xs17_259q48cz2521": ("004200a50092005c002000100030", 20),
                   "xs17_255m88czw643": ("004000a000a30069001600100030", 20),
                   "xs17_0bq2c826z321": ("00c000a00020006c000900730040", 20),
                   "xs17_31e88a52zw33": ("?-tub_with_long_leg_siamese_eater_and_?-block", 20),
                   "xs17_35akggozw4a6": ("trans-long_boat_with_long_leg_and_?-boat", 20),
                   "xs17_0ogila4z4aa4": ("cis-barge_with_long_leg_and_trans-beehive", 20),
                   "xs17_4aabk4ozx321": ("001800280050004e0031000e0008", 20),
                   "xs17_0ggka23z3ego": ("03000100014000a30021002e0018", 20),
                   "xs17_25a88gz39d11": ("008c014900ab002800280010", 20),
                   "xs17_g84pb871z121": ("00d800500044003a000900050002", 20),
                   "xs17_0ggkc0fhoz32": ("integral_and_?-long_hook", 20),
                   "xs17_0ggka52z3ego": ("?-barge_with_trans-nine_siamese_eater", 20),
                   "xs17_08kih3zoge21": ("03000230012800ae00410003", 20),
                   "xs17_xogka23zca26": ("01800140004000d800100014000a00020003", 20),
                   "xs17_25a88a6z6413": ("tub_with_long_nine_and_?-carrier", 20),
                   "xs17_651i4ozc4521": ("0186008500a1005200240018", 20),
                   "xs17_0g8hf0cicz23": ("0180008000a20055001500120030", 20),
                   "xs17_c4go0e93zw65": ("?-snake_siamese_carrier_and_hook", 20),
                   "xs17_woe1eg8oz321": ("018001400045006b002800280010", 20),
                   "xs17_0312kozcia43": ("?-canoe_siamese_loaf_with_trans-tail", 20),
                   "xs17_4all2zx34213": ("006000200040008200750015000a0004", 20),
                   "xs17_0312koz69a43": ("?17?052", 20),
                   "xs17_4a9f0ckzx311": ("?17?091", 20),
                   "xs17_0g9fgka4z321": ("?17?173", 20),
                   "xs17_0g84213z32qic": ("0300020001060089004b00280018", 20),
                   "xs17_354k8zy011dic": ("03000280008000a000500010001600090006", 20),
                   "xs17_0oggml2z4a6w1": ("Z_and_?-boats", 20),
                   "xs17_0g8id1egoz121": ("0080014000a30055001400240018", 20),
                   "xs17_178c0s4z06511": ("008000e300150034000400380020", 20),
                   "xs17_25ak8zy011dic": ("?-long_barge_line_beehive", 20),
                   "xs17_4s0gbaiczw121": ("001800240028006a00050002001c0010", 20),
                   "xs17_g84qijz11x252": ("004000a000530012001a000400280030", 20),
                   "xs17_ca51i4ozw2521": ("0030005000a20085004a00240018", 20),
                   "xs17_0c88a52z259a4": ("tub_with_long_leg_and_?-mango", 20),
                   "xs17_0o4aarz11x123": ("?-amoeba_8,4,4", 20),
                   "xs17_g84213431e8z11": ("060004000203011200aa006c", 20),
                   "xs17_252sggzy123ck8": ("?-tub_with_tail_siamese_eater_on_boat", 20),
                   "xs17_g8k461642acz01": ("02000500020301d900560020", 20),
                   "xs17_3pczw23ck8gzy21": ("?-siamese_carriers_on_long_ship", 20),
                   "xs18_rhe0ehr": ("dead spark coil", 0),
                   "xs18_69is0si96": ("[cis-mirrored R-mango]", 4),
                   "xs18_j1u0uh3z11": ("longhook and dock", 6),
                   "xs18_c4o0ehrz321": ("rotated C", 6),
                   "xs18_2egm9a4zx346": ("[loaf eater tail]", 6),
                   "xs18_3lk453z3443": ("pond and dock", 7),
                   "xs18_0mmge96z1221": ("?18?016", 7),
                   "xs18_8ehlmzw12452": ("?18?017", 7),
                   "xs18_j1u0uicz11": ("cap and dock", 9),
                   "xs18_69b88cz2553": ("?18?025", 9),
                   "xs18_g88bbgz011dd": ("?18?020", 9),
                   "xs18_69b88a6zw652": ("?18-boat huge", 9),
                   "xs18_354m453zw343": ("?18?030", 9),
                   "xs18_0c88b96z2553": ("?18?013", 9),
                   "xs18_gbbgn96z11": ("?18-block scorp", 10),
                   "xs18_gbbob96z11": ("?18?057", 10),
                   "xs18_0mllicz346": ("?18?006", 10),
                   "xs18_o8gehrz643": ("?18?012", 10),
                   "xs18_gs2ib96z1221": ("?18?022", 10),
                   "xs18_0mmge93z1221": ("?18?018", 10),
                   "xs18_ckggm952z066": ("?18?009", 10),
                   "xs18_69bo3qic": ("?18?060", 11),
                   "xs18_330fhu0oo": ("?18?058", 11),
                   "xs18_69baa4z653": ("?18?068", 11),
                   "xs18_69n8brzx11": ("?18?023", 11),
                   "xs18_m2s0si96z11": ("R-mango and C", 11),
                   "xs18_gillmz1w643": ("?18?014", 11),
                   "xs18_c88b96z3552": ("?18?015", 11),
                   "xs18_69b88cz6513": ("?18?029", 11),
                   "xs18_c88b96z3156": ("?18?074", 11),
                   "xs18_c89n871z311": ("?18?007", 11),
                   "xs18_259aczw359a4": ("?18?042", 11),
                   "xs18_g88bbgz0dd11": ("?18?070", 11),
                   "xs18_69baa4ozx311": ("?18?036", 11),
                   "xs18_02596z69d113": ("?18?003", 11),
                   "xs18_0c88b96z6513": ("?18?005", 11),
                   "xs18_69ir2qr": ("?18?050", 12),
                   "xs18_4alhe0e96": ("?18?033", 12),
                   "xs18_gbaqb96z11": ("?18?052", 12),
                   "xs18_gjlkmz1w643": ("?18?047", 12),
                   "xs18_m2s079icz11": ("?18?021", 12),
                   "xs18_ckgil96z066": ("?18?064", 12),
                   "xs18_4a9baaczx33": ("?18?105", 12),
                   "xs18_69baa4z2552": ("?18?063", 12),
                   "xs18_mm0e96z1226": ("?18?026", 12),
                   "xs18_259aczw4a953": ("?18?037", 12),
                   "xs18_69egdbgzx121": ("?18?090", 12),
                   "xs18_259aczx65156": ("?18?032", 12),
                   "xs18_69js3pm": ("?18?031", 13),
                   "xs18_4ap3qicz32": ("?18?116", 13),
                   "xs18_c88bqicz33": ("?18?135", 13),
                   "xs18_4aab96z2552": ("?18?093", 13),
                   "xs18_2596z311d96": ("?18?136", 13),
                   "xs18_8e1t2sgz311": ("?18?024", 13),
                   "xs18_0c9b871z2552": ("?18?082", 13),
                   "xs18_259mggkczx66": ("?18?106", 13),
                   "xs18_03lk453z6521": ("?18?055", 13),
                   "xs18_035a4oz69d11": ("?18?083", 13),
                   "xs18_0o8b96zog853": ("03000218010800ab00690006", 13),
                   "xs18_0651u8z69521": ("?18?104", 13),
                   "xs18_31egmicz0321": ("[[?18?165]]", 13),
                   "xs18_31ege96z0321": ("?18?076", 13),
                   "xs18_8kai3g8ozx343": ("?18?019", 13),
                   "xs18_69ar2qr": ("?18?067", 14),
                   "xs18_69ar1qr": ("?-loop_siamese_snake_and_block", 14),
                   "xs18_32qr2qr": ("?18?099", 14),
                   "xs18_69araar": ("?-loop_siamese_tables", 14),
                   "xs18_35is0si96": ("?18?079", 14),
                   "xs18_mm0e952z56": ("?18?096", 14),
                   "xs18_69b8brzx32": ("?18?059", 14),
                   "xs18_4a60uh32ac": ("?-long_hook_siamese_eater_and_block", 14),
                   "xs18_0gbaarz3452": ("cis-loaf_with_long_leg_and_cis-table", 14),
                   "xs18_gs2ll2z2543": ("?18?011", 14),
                   "xs18_ca9m4koz311": ("?18?035", 14),
                   "xs18_j1u06akoz11": ("?18?144", 14),
                   "xs18_g88b96zd552": ("?18?148", 14),
                   "xs18_wrb0796z321": ("?-eater_and_R-bee_and_block", 14),
                   "xs18_gbbgf9z1221": ("?18?087", 14),
                   "xs18_259aczw315ac": ("?18?051", 14),
                   "xs18_4aq3ob5zw121": ("?18?154", 14),
                   "xs18_69b88a6zw256": ("?18?077", 14),
                   "xs18_0j1u0696z321": ("trans-boat_with_long_nine_and_trans-beehive", 14),
                   "xs18_62s0ci96z321": ("?18?092", 14),
                   "xs18_09v0cia4z321": ("?18?137", 14),
                   "xs18_0mmge93z3201": ("?18?109", 14),
                   "xs18_g88m952sgz121": ("?18?133", 14),
                   "xs18_33gv164ko": ("?18?156", 15),
                   "xs18_39e0ehla4": ("?18?008", 15),
                   "xs18_69is079ic": ("shift-rotated_R-mango", 15),
                   "xs18_35is0si53": ("?18?084", 15),
                   "xs18_h7o3qicz11": ("0068002e0021001500560060", 15),
                   "xs18_mm0e96z1ac": ("?-block_and_R-bee_and_long_snake", 15),
                   "xs18_ca9f033z33": ("?-loaf_siamese_table_siamese_table_and_blocks", 15),
                   "xs18_5b8b96z0352": ("?18?152", 15),
                   "xs18_g6p2r9a4z11": ("?18?048", 15),
                   "xs18_6a88brz0352": ("?-very_long_eater_and_boat_and_block", 15),
                   "xs18_caaj2acz311": ("?-eater_siamese_eater_siamese_hat", 15),
                   "xs18_6t1mkiczw11": ("0030004a006d0021002e0018", 15),
                   "xs18_62s0f96z321": ("?18?056", 15),
                   "xs18_3lk64koz321": ("?18?149", 15),
                   "xs18_178bb8ozw33": ("?18?094", 15),
                   "xs18_j1u069icz11": ("?18?162", 15),
                   "xs18_g8ie0ehrz11": ("?18?071", 15),
                   "xs18_wmm0e96z643": ("?18?124", 15),
                   "xs18_gbb8b52z123": ("?18?089", 15),
                   "xs18_c4o79icz321": ("?18?098", 15),
                   "xs18_25b8b96zw33": ("?18?066", 15),
                   "xs18_0h7ob96z321": ("?18?065", 15),
                   "xs18_kq2r96z1221": ("0034005a0042003b00090006", 15),
                   "xs18_4aabaaczx33": ("?18?044", 15),
                   "xs18_mljgz1w69a4": ("trans-loaf_with_long_leg_and_para-ship", 15),
                   "xs18_0g6p3qicz121": ("004000a0005600150021002e0018", 15),
                   "xs18_259mggozwca6": ("?18?075", 15),
                   "xs18_4aab88a6zx33": ("003000280008000b006b002800280010", 15),
                   "xs18_312kozca22ac": ("?-canoe_and_dock", 15),
                   "xs18_0ml9ak8z3421": ("0060009600550029000a00140008", 15),
                   "xs18_69baa4ozx321": ("0030005c0042003d0001000a000c", 15),
                   "xs18_0j9mkicz1221": ("00300048002e0011000d002a0030", 15),
                   "xs18_0g88bqicz343": ("0060009000680008000b001a0012000c", 15),
                   "xs18_69mggkcz04a6": ("?18?123", 15),
                   "xs18_02lligz652w23": ("?18?147", 15),
                   "xs18_xo4k871z69521": ("?-loaf_with_trans-tail_at_loaf", 15),
                   "xs18_33gv1qr": ("?-Z_siamese_snake_and_blocks", 16),
                   "xs18_69argbr": ("?-loop_siamese_snake_and_block", 16),
                   "xs18_69arhar": ("?18?095", 16),
                   "xs18_178jd0e96": ("01b200a5009500560020", 16),
                   "xs18_2ege1fgkc": ("?18?108", 16),
                   "xs18_330fhu066": ("?-long_hook_siamese_long_hook_and_?-blocks", 16),
                   "xs18_09v0rrz32": ("?-table_siamese_carrier_and_blocks", 16),
                   "xs18_2ege1egma": ("00c4012a00aa01ab0010", 16),
                   "xs18_33gv1oka4": ("?18?129", 16),
                   "xs18_3jgf96z321": ("?18?039", 16),
                   "xs18_0mk2qrz643": ("?18?119", 16),
                   "xs18_c88bpicz33": ("006c00680008000b00190012000c", 16),
                   "xs18_gbaqj96z11": ("?18?086", 16),
                   "xs18_cillicz066": ("[[?18?166]]", 16),
                   "xs18_178c1fgka4": ("03300112015500d2000c", 16),
                   "xs18_6421egu156": ("[[long_hook_with_tail fuse part_scorpion]]", 16),
                   "xs18_5b8b96z253": ("00a200d5001600d000900060", 16),
                   "xs18_mmge1egoz1": ("008000e3001500d400d40008", 16),
                   "xs18_6t1qb96zw1": ("003600590043003a000a0004", 16),
                   "xs18_gbq1ticz11": ("?-R-bee_with_long_tail_and_boat", 16),
                   "xs18_j9ab96z123": ("?-big_S_siamese_snake", 16),
                   "xs18_6a88a53z653": ("?18?117", 16),
                   "xs18_2lla8cz3443": ("006200950095006a0008000c", 16),
                   "xs18_c4o0uh3z643": ("long_hook_and_shift-dock", 16),
                   "xs18_62s0fhoz321": ("para-long_hook_and_dock", 16),
                   "xs18_69ligkczw66": ("cis-loaf_with_long_nine_and_cis-block", 16),
                   "xs18_c84kl3z3543": ("00c000a8002e002100150036", 16),
                   "xs18_g8o653zd54c": ("ship_on_ship_and_cis-table", 16),
                   "xs18_0ml9acz3443": ("?-mango_siamese_bookend_on_pond", 16),
                   "xs18_rh6o8zx32ac": ("01b0011000c0003c002400050003", 16),
                   "xs18_2ll2sgz3443": ("?18?053", 16),
                   "xs18_3iabqicz011": ("?18?091", 16),
                   "xs18_259ab96zw33": ("003600590042003c0000000c000c", 16),
                   "xs18_35s2djoz011": ("?18?12", 16),
                   "xs18_4aab96z0356": ("racetrack_and_cis-ship", 16),
                   "xs18_3lkiacz3421": ("?-R-loaf_on_long_integral", 16),
                   "xs18_m2s079koz11": ("boat_with_leg_and_para-C", 16),
                   "xs18_ckggm96z4a6": ("?18?113", 16),
                   "xs18_5b8b96zw253": ("00a000d0001200d500960060", 16),
                   "xs18_2lligz32w652": ("cis-boat_with_long_nine_and_trans-beehive", 16),
                   "xs18_gill2z1w69a4": ("?18?132", 16),
                   "xs18_8kc0v1oozx23": ("very_long_Z_and_?-boat_and_block", 16),
                   "xs18_0ogka53z4aa6": ("long_boat_with_leg_and_trans-R-bee", 16),
                   "xs18_02ege96z6521": ("00c000a2004e0030000e00090006", 16),
                   "xs18_69ic8a6z0643": ("0060009300490036001000500060", 16),
                   "xs18_ckggka53z066": ("?18?138", 16),
                   "xs18_4a96z65115a4": ("tub_with_long_nine_and_?-loaf", 16),
                   "xs18_wg0siarz2543": ("?-R-loop_on_loaf", 16),
                   "xs18_31e88a53zw33": ("?18?041", 16),
                   "xs18_0c88b96zca23": ("trans-eater_and_worm", 16),
                   "xs18_354mik8z0643": ("00c000a30021006e004800280010", 16),
                   "xs18_0j9mkk8z3421": ("?18?088", 16),
                   "xs18_35a88a6z0653": ("trans-boat_with_long_nine_and_ortho-ship", 16),
                   "xs18_39e0ooz0354c": ("?18?125", 16),
                   "xs18_0gilmz32w696": ("?18?062", 16),
                   "xs18_3hu08kczw346": ("?-eater_siamese_long_hook_and_boat", 16),
                   "xs18_69a4z65115a4": ("?18?054", 16),
                   "xs18_wgbb871z2543": ("?18?163", 16),
                   "xs18_09v0cik8z321": ("long_and_?-loaf", 16),
                   "xs18_3hu08oz4a611": ("0182011500f6000800280030", 16),
                   "xs18_069a4z4a51156": ("tub_with_long_nine_and_?-loaf", 16),
                   "xs18_0gs2552z12ego": ("?18?145", 16),
                   "xs18_356o8zy0230f9": ("ship_on_carrier_and_?-table", 16),
                   "xs18_0gs2453z12ego": ("030002800083010100ee00280010", 16),
                   "xs18_259aczy0359a4": ("para-rotated_R-mango", 16),
                   "xs18_02lligz256w23": ("[[cis-boat fuse dock and beehive]]", 16),
                   "xs18_69ar8br": ("?-loop_siamese_table_and_block", 17),
                   "xs18_32hv0rr": ("006d006b00080068006c", 17),
                   "xs18_32qr1qr": ("?-table_siamese_snake_and_blocks", 17),
                   "xs18_2egu1tic": ("006c00aa00aa004b0030", 17),
                   "xs18_69e0ehar": ("?18?072", 17),
                   "xs18_697079ar": ("R-loop_and_?-R-bee", 17),
                   "xs18_35is079ic": ("?18?107", 17),
                   "xs18_j5s2qrz11": ("003600160010000e00290033", 17),
                   "xs18_qmgm96z66": ("?18?081", 17),
                   "xs18_660uhf0cc": ("?-long_hook_siamese_long_hook_and_blocks", 17),
                   "xs18_9v0sia4z23": ("?-table_siamese_table_and_R-loaf", 17),
                   "xs18_69fgkcz253": ("0062009500f6000800280030", 17),
                   "xs18_mljgf9z1w1": ("?-table_on_table_and_ship", 17),
                   "xs18_gbbo3tgz11": ("?-bookend_siamese_hook_siamese_block", 17),
                   "xs18_mkhf0cicz1": ("alef_and_cis-beehive", 17),
                   "xs18_660uh3z653": ("?-long_hook_on_ship_and_block", 17),
                   "xs18_cq2r96z1221": ("00300048006e0021002d001a", 17),
                   "xs18_69b8b52z033": ("003600550042003c000000300030", 17),
                   "xs18_wmmge13z643": ("00c000ac002c0020001c000400050003", 17),
                   "xs18_31eozw122qr": ("0360034000400058002e00010003", 17),
                   "xs18_69iczx19lic": ("?-mango_line_loaf", 17),
                   "xs18_c88ml2z3543": ("006c00a80088007600150002", 17),
                   "xs18_660u93z6521": ("?-boat_with_trans-tail_siamese_hook_and_block", 17),
                   "xs18_mm0e952z146": ("?-carrier_and_R-loaf_and_block", 17),
                   "xs18_gillicz1w66": ("0030004b00ab00a80048000c", 17),
                   "xs18_o8b96zx3596": ("00c0012000a60069000b00080018", 17),
                   "xs18_wmm0e93z643": ("?-eater_and_hook_and_block", 17),
                   "xs18_4aab871z253": ("anvil_and_?-boat", 17),
                   "xs18_g8eht2sgz11": ("?18?142", 17),
                   "xs18_69baaczw652": ("R-racetrack_and_cis-boat", 17),
                   "xs18_69b8jdz0311": ("?-amoeba_8,5,4", 17),
                   "xs18_g88r2qrz121": ("?-R-loaf_and_table_and_block", 17),
                   "xs18_697o796zw11": ("?18?130", 17),
                   "xs18_mk4r96z1221": ("003600540044003b00090006", 17),
                   "xs18_gbbo31e8z11": ("?-eater_and_hook_and_block", 17),
                   "xs18_0c88brz2596": ("[[ortho-loaf and long_Z and block]]", 17),
                   "xs18_0gil96z3ego": ("?-loaf_with_cis-nine_siamese_eater", 17),
                   "xs18_0c88brz6952": ("Z_and_trans-loaf_and_block", 17),
                   "xs18_4aab96zw653": ("racetrack_and_para-ship", 17),
                   "xs18_c9baacz0253": ("R-iron_and_cis-boat", 17),
                   "xs18_4aq3qicz023": ("00300010001600350041003e0008", 17),
                   "xs18_39e0uizw643": ("?-eater_siamese_table_and_hook", 17),
                   "xs18_3lkaacz1243": ("?-long_integral_siamese_beehive_on_loaf", 17),
                   "xs18_wrb079cz321": ("?-eater_and_hook_and_block", 17),
                   "xs18_j9mkia4z121": ("0066004900360014002400280010", 17),
                   "xs18_035a4z69d113": ("worm_and_cis-long_boat", 17),
                   "xs18_gw8ka53zdd11": ("trans-very_long_boat_with_long_leg_and_trans-block", 17),
                   "xs18_035a8oz69d11": ("?-scorpio_siamese_boat_with_trans-tail", 17),
                   "xs18_ci96zw11dik8": ("?18?155", 17),
                   "xs18_039u0ooz4a43": ("?-tub_with_long_leg_siamese_hook_and_block", 17),
                   "xs18_64km996z0321": ("?-pond_siamese_table_on_ship", 17),
                   "xs18_0j9m453z3421": ("00c000a00020006c009200c90006", 17),
                   "xs18_0mligz32w696": ("?18?158", 17),
                   "xs18_2l2s0sicz121": ("?-tub_line_tub_and_R-bee", 17),
                   "xs18_02ll2sgz2543": ("?-beehive_with_tail_and_R-loaf", 17),
                   "xs18_09v0ca52z321": ("long_and_trans-long-boat", 17),
                   "xs18_178baa4zx253": ("anvil_and_?-boat", 17),
                   "xs18_4a9b88a6zx33": ("?18?102", 17),
                   "xs18_352s0ccz6521": ("?-boat_long_line_boat_and_block", 17),
                   "xs18_0c88a53z6996": ("?18?120", 17),
                   "xs18_25a4ozx6b871": ("0080014000a00046003d0001000e0008", 17),
                   "xs18_6io0ep3z1221": ("0060005300110034002600090006", 17),
                   "xs18_259a4ozc8711": ("?-mango_with_bend_tail_siamese_eater", 17),
                   "xs18_069b8ozc8711": ("0180010600e9002b00280018", 17),
                   "xs18_3iakgkcz3421": ("?18?034", 17),
                   "xs18_2lla8kcz1221": ("?18?146", 17),
                   "xs18_39u08ka4z321": ("?18?111", 17),
                   "xs18_0gbb871z3452": ("?18?085", 17),
                   "xs18_04aab96z3113": ("racetrack_and_para-table", 17),
                   "xs18_0ggm952z3ego": ("?-loaf_with_trans-nine_siamese_eater", 17),
                   "xs18_06996z3115ac": ("trans-boat_with_leg_and_cis-pond", 17),
                   "xs18_0gbbo8a6z321": ("?18?112", 17),
                   "xs18_0g4s3qicz321": ("00c000a0005600150031000e0008", 17),
                   "xs18_69mggka4zw66": ("tub_long_line_beehive_and_?-block", 17),
                   "xs18_w3lk453z4a43": ("tub_with_tail_and_?-dock", 17),
                   "xs18_0ggmd1e8z1226": ("00300048005800d0000e0001000e0008", 17),
                   "xs18_g8o69a4z1254c": ("?-R-bee_with_tail_on_loaf", 17),
                   "xs18_0oggm952z4aa4": ("trans-loaf_with_long_leg_and_trans-beehive", 17),
                   "xs18_0gjlkia4z3201": ("00c00090007c0002001900260030", 17),
                   "xs18_0mligz32w25a4": ("trans-barge_with_long_nine_and_para-boat", 17),
                   "xs18_02lligz643w23": ("?-eater_siamese_long_hook_and_beehive", 17),
                   "xs18_3pq32qr": ("?-table_siamese_snake_and_blocks", 18),
                   "xs18_6is0siar": ("R-loop_and_?-hook", 18),
                   "xs18_31ege1dic": ("018c0152005500550022", 18),
                   "xs18_4ad1egm96": ("008c0152015500960060", 18),
                   "xs18_31ekhf033": ("01b301a5002c00240018", 18),
                   "xs18_33gv1o8a6": ("?-Z_and_eater_and_block", 18),
                   "xs18_j5c2djoz11": ("?-shillelagh_siamese_long_shillelagh_siamese_carrier", 18),
                   "xs18_g6p3qp3z11": ("?-long_integral_siamese_snake_and_block", 18),
                   "xs18_okkm952z66": ("?-loaf_siamese_long_R-bee_and_block", 18),
                   "xs18_ck0v1qrzw1": ("00580068000b0069006a0004", 18),
                   "xs18_3lkmicz056": ("00c000ad002b006800480030", 18),
                   "xs18_g9fgn96z11": ("0060004c0032001500150036", 18),
                   "xs18_2llm853z32": ("00660049002e0010000e00010003", 18),
                   "xs18_6t1u0uizw1": ("racetrack_and_cis-table", 18),
                   "xs18_6a88brz253": ("?18?110", 18),
                   "xs18_2530fho8a6": ("?-long_hook_siamese_eater_and_?-boat", 18),
                   "xs18_4aab96z653": ("racetrack_and_ortho-ship", 18),
                   "xs18_ciab96z643": ("?18?080", 18),
                   "xs18_8u1uge2z23": ("?-sesquihat_siamese_eater_siamese_table", 18),
                   "xs18_69ba96z253": ("0062009500d6005000900060", 18),
                   "xs18_j1u0ojdz11": ("dock_and_?-shillelagh", 18),
                   "xs18_31ege132ac": ("?-krake_siamese_eater", 18),
                   "xs18_rbgf1e8z01": ("006c006a000a006b00500020", 18),
                   "xs18_g8ob96zpic": ("033002480198000b00090006", 18),
                   "xs18_0c9b871z653": ("alef_and_?-ship", 18),
                   "xs18_cill2zx69a4": ("00800140012200d500150012000c", 18),
                   "xs18_xokc0f9z653": ("ship_on_ship_and_trans-table", 18),
                   "xs18_4aq3ckoz321": ("0064004a003a0003000c00140018", 18),
                   "xs18_69e0uizw643": ("?-eater_siamese_table_and_R-bee", 18),
                   "xs18_4s0si96z643": ("00c4009c0060001c001200090006", 18),
                   "xs18_w3pm453z253": ("?-shillelagh_siamese_hook_on_boat", 18),
                   "xs18_2llmz320256": ("boat_with_nine_and_?-R-bee", 18),
                   "xs18_35akgozca26": ("long_boat_with_leg_and_?-hook", 18),
                   "xs18_08e1t6zad11": ("014001a8002e0021001d0006", 18),
                   "xs18_25a88brzw33": ("006c00680008000b002b00500020", 18),
                   "xs18_wggs2qrz256": ("boat_with_cis-tail_siamese_trans-legs_and_block", 18),
                   "xs18_wggs2qrz652": ("boat_with_trans-tail_siamese_trans-legs_and_block", 18),
                   "xs18_696o653z065": ("00c000a000600018006500930060", 18),
                   "xs18_g88ml2zd543": ("?-G-siamese_trans-legs_on_boat", 18),
                   "xs18_g9fgf9z1221": ("?-table_siamese_pond_on_table", 18),
                   "xs18_0gjlka6z346": ("0060009000d300150014000a0006", 18),
                   "xs18_mll2z1025ac": ("long_boat_with_leg_and_?-R-bee", 18),
                   "xs18_gjlkkoz1246": ("00300053009500d400140018", 18),
                   "xs18_03lkicz69a4": ("00c00123015500940012000c", 18),
                   "xs18_mkl3z1025ac": ("long_boat_with_leg_and_cis-hook", 18),
                   "xs18_39egeiczw23": ("0060005600150035000a00080018", 18),
                   "xs18_69ba952z033": ("003600590042003c000000300030", 18),
                   "xs18_31eozw32qic": ("0300020001d80068000b00090006", 18),
                   "xs18_ca96z315ak8": ("barge_with_leg_and_?-R-loaf", 18),
                   "xs18_rh6o8zx34ac": ("01b0011000c0003c002200050003", 18),
                   "xs18_3pm4kozw343": ("?-hat_siamese_C_siamese_shillelagh", 18),
                   "xs18_31eozw1qq23": ("0300020001d0006b000b00080018", 18),
                   "xs18_0iu0696zc96": ("?-shillelagh_siamese_table_and_trans-beehive", 18),
                   "xs18_02llicz69a4": ("00c00122015500950012000c", 18),
                   "xs18_j5q4oge2z11": ("00c000ac002a005200a300c0", 18),
                   "xs18_0o8b96zok96": ("?18?122", 18),
                   "xs18_rh6o8zx34a6": ("01b0011000c0003c002200050006", 18),
                   "xs18_wggrb8oz696": ("?-beehive_with_tail_siamese_table_and_block", 18),
                   "xs18_0mmgdbz3421": ("?-R-loaf_on_snake_and_block", 18),
                   "xs18_gbbo3tgz011": ("?-bookend_and_R-bee_and_block", 18),
                   "xs18_xcil96z2553": ("?-siamese_loafs_on_R-bee", 18),
                   "xs18_39eg8ozca43": ("?-boat_with_nine_on_hook", 18),
                   "xs18_o4q2rq23z01": ("?-beehive_with_tail_siamese_table_and_block", 18),
                   "xs18_35a8czw315ac": ("cis-rotated_boat_with_leg", 18),
                   "xs18_354mkk8z0643": ("?-hook_siamese_hat_siamese_eater", 18),
                   "xs18_0ogil96z4aa4": ("cis-loaf_with_long_leg_and_trans-beehive", 18),
                   "xs18_ckggka52z4a6": ("trans-barge_with_long_nine_and_trans-boat", 18),
                   "xs18_g84213zdlge2": ("03000208010e008100550036", 18),
                   "xs18_660u1daz0321": ("0030004b002b00680008000a0006", 18),
                   "xs18_69akgkcz0643": ("loaf_on_elevener", 18),
                   "xs18_69ligoz04aa4": ("cis-loaf_with_long_leg_and_cis-beehive", 18),
                   "xs18_0g88bpicz343": ("?18?140", 18),
                   "xs18_354mgm952zx1": ("loaf_with_trans-tail_and_?-hook", 18),
                   "xs18_0mkkb96z1221": ("00300052004e0030000e00090006", 18),
                   "xs18_35a8czx65156": ("boat_with_leg_and_shift-C", 18),
                   "xs18_mligoz104aa4": ("Z_and_beehive_and_cis-boat", 18),
                   "xs18_0c88b52z6996": ("cis-boat_with_long_leg_and_trans-pond", 18),
                   "xs18_3p6gzw123cko": ("03000280018000600050002600190003", 18),
                   "xs18_4aar1u8zx121": ("?-hats_siamese_eater", 18),
                   "xs18_0okk871z4aa6": ("010001c000200056005500350002", 18),
                   "xs18_2lligkcz3201": ("?18?101", 18),
                   "xs18_0j5s2596z121": ("0066009200ac0048000a00050002", 18),
                   "xs18_0gbaik8z3453": ("0060009000ab006a001200140008", 18),
                   "xs18_25a84ozcid11": ("0182024501aa002800240018", 18),
                   "xs18_09v0c871z321": ("long_and_?-eater", 18),
                   "xs18_2llmz01w32ac": ("01800140004000600016001500350002", 18),
                   "xs18_0oggm96zcia4": ("beehive_with_long_leg_and_para-loaf", 18),
                   "xs18_0651u8zca521": ("0180014600a50041003e0008", 18),
                   "xs18_2ege9a4z0643": ("0040007300090076009000500020", 18),
                   "xs18_35a88gzoid11": ("030302890156005000500020", 18),
                   "xs18_4a9egoz0354c": ("004000ac012a00e200130030", 18),
                   "xs18_04a96z311dic": ("beehive_with_long_leg_and_?-loaf", 18),
                   "xs18_354mkia4zw32": ("00c0009600790002001c00200030", 18),
                   "xs18_0gilmz32w69c": ("0180012000d60015001200500060", 18),
                   "xs18_4akggm96zw66": ("beehive_long_line_tub_and_trans-block", 18),
                   "xs18_4a96o8z69521": ("?-loaf_with_trans-tail_on_loaf", 18),
                   "xs18_31egogkczx66": ("?18?046", 18),
                   "xs18_0oggm96z4aic": ("?18?131", 18),
                   "xs18_0mkid96z3201": ("0060005600140032000d00090006", 18),
                   "xs18_3p6geiczw121": ("0060005600150025002a00140008", 18),
                   "xs18_gg0s2qrz0343": ("00d800580040003e0001000e0008", 18),
                   "xs18_c970s4ozw6221": ("?18?127", 18),
                   "xs18_39m44ozx12156": ("00c000a0003800440024001600090003", 18),
                   "xs18_25a84koz02553": ("004000a200550015002600280018", 18),
                   "xs18_4aab88czw2552": ("00300012001500d5005200500020", 18),
                   "xs18_259aczy0315ac": ("boat_with_leg_and_shift-R-mango", 18),
                   "xs18_0ca52z65115a4": ("tub_with_long_leg_and_para-long_boat", 18),
                   "xs18_0g8o652z23cic": ("?-boat_on_eater_on_beehive", 18),
                   "xs18_g8o0e93z1254c": ("?-R-bee_with_tail_and_hook", 18),
                   "xs18_25a88cz4a5113": ("cis-mirrored_tub_with_long_leg", 18),
                   "xs18_0o4a952z116ac": ("?-mango_with_trans-tail_on_ship", 18),
                   "xs18_252sggzy123cko": ("?-tub_with_tail_siamese_eater_on_ship", 18),
                   "xs18_69iraar": ("004c007a0001007d004a", 19),
                   "xs18_69ir8br": ("006a006d0001007a004c", 19),
                   "xs18_69ar9ar": ("?-loop_siamese_table_siamese_snake", 19),
                   "xs18_3pm44mp3": ("?-shillelaghs_siamese_table", 19),
                   "xs18_39e0ehar": ("00c500ab0028006b0005", 19),
                   "xs18_0br8brz32": ("?-carrier_siamese_table_and_blocks", 19),
                   "xs18_35ako0uic": ("cap_and_cis-very_long_ship", 19),
                   "xs18_0drzrq226": ("?-Z_siamese_carrier_siamese_snake_and_block", 19),
                   "xs18_31ege1dio": ("018c0152005400550023", 19),
                   "xs18_bq1ticz23": ("R-bee_with_long_tail_and_table", 19),
                   "xs18_259ara952": ("00d601390082007c0010", 19),
                   "xs18_31ego3qic": ("0188014e004100550036", 19),
                   "xs18_3pmzciq23": ("0306026901ab00080018", 19),
                   "xs18_31ekhf0cc": ("?18?161", 19),
                   "xs18_39mge1da4": ("018c0152005500960060", 19),
                   "xs18_mkhf0ca6z1": ("alef_and_?-ship", 19),
                   "xs18_0mk2qrz343": ("00d800580040002e00690006", 19),
                   "xs18_mkhf0ckoz1": ("alef_and_?-ship", 19),
                   "xs18_69mgmqzw66": ("00600090006b000b00680058", 19),
                   "xs18_0gjliczpi6": ("0320025000d300150012000c", 19),
                   "xs18_mmge1da4z1": ("?18?139", 19),
                   "xs18_iu06996z56": ("?-table_siamese_snake_and_pond", 19),
                   "xs18_3lk453zc96": ("dock_and_?-shillelagh", 19),
                   "xs18_4s0v1qrzw1": ("00580068000b006a006a0004", 19),
                   "xs18_cil68ozxbd": ("00600090015000cd002b0030", 19),
                   "xs18_mkie0e93z1": ("R-loop_and_?-hook", 19),
                   "xs18_mllmz1w652": ("cis-boat_with_long_leg_and_cis-cap", 19),
                   "xs18_ckjaicz643": ("00cc00940073000a0012000c", 19),
                   "xs18_okkm93z6a4": ("0180012000d0005200550036", 19),
                   "xs18_3pmkicz066": ("00c0009b006b002800480030", 19),
                   "xs18_c9b871z356": ("alef_and_?-ship", 19),
                   "xs18_ca9f0ccz33": ("?-loaf_siamese_table_siamese_table_and_blocks", 19),
                   "xs18_0cp3qicz65": ("00c000ac00190003001a0012000c", 19),
                   "xs18_o4p7ojdz01": ("006c0028004a005500350002", 19),
                   "xs18_3lk453zbc1": ("dock_and_?-shillelagh", 19),
                   "xs18_69ab8oz653": ("00c600a9006a000b00080018", 19),
                   "xs18_mllmz1w256": ("trans-boat_with_long_leg_and_cis-cap", 19),
                   "xs18_wmkiarz643": ("?-bookends_siamese_eater", 19),
                   "xs18_69b8b5z253": ("00a000d0001000d600950062", 19),
                   "xs18_25a8ohf033": ("tub_with_tail_siamese_long_hook_and_?-block", 19),
                   "xs18_wmlla4zc96": ("0180012000d600150015000a0004", 19),
                   "xs18_3pmgmaz066": ("00c0009b006b000800680050", 19),
                   "xs18_69baarzx32": ("006c0029002b006800480030", 19),
                   "xs18_4aq3qicz32": ("0064004a001a0003001a0012000c", 19),
                   "xs18_69b8jdzw65": ("?-amoeba_8,5,4", 19),
                   "xs18_o4kmhrz0146": ("00d80088006b002900240018", 19),
                   "xs18_0md1e8z34ac": ("00600096014d0181000e0008", 19),
                   "xs18_6a8o6hrzw23": ("?18?100", 19),
                   "xs18_ciligzx6a96": ("00c00120015000d200150012000c", 19),
                   "xs18_03jgf9z6521": ("?-long_ship_on_table_and_block", 19),
                   "xs18_xraik8z3543": ("?18?157", 19),
                   "xs18_69mkia4z321": ("00660049003600140012000a0004", 19),
                   "xs18_2lmgdbz1221": ("?-R-bee_on_snake_and_boat", 19),
                   "xs18_xohf033z653": ("ship_on_long_hook_and_trans-block", 19),
                   "xs18_gbb8b5z1252": ("00a000d0001200d500d2000c", 19),
                   "xs18_0c9b8oz6996": ("00c0012c012900cb00080018", 19),
                   "xs18_0mp3z122qic": ("018002400343005900560020", 19),
                   "xs18_cill2zx34ac": ("?-beehive_with_bend_tail_siamese_boat_with_trans-tail", 19),
                   "xs18_6t1u06iozw1": ("racetrack_and_?-carrier", 19),
                   "xs18_rq2sgzx34a4": ("?-tub_with_legs_siamese_trans-legs_and_block", 19),
                   "xs18_03lkm96z252": ("?-beehive_line_tub_siamese_hook", 19),
                   "xs18_0696zbd1156": ("?-very_long_hook_siamese_snake_and_beehive", 19),
                   "xs18_69mgma4z321": ("00660049003600100016000a0004", 19),
                   "xs18_65la8cz2543": ("006200a500a9005600100030", 19),
                   "xs18_6a88b52z653": ("cis-boat_with_long_nine_and_trans-ship", 19),
                   "xs18_39u0ok8z643": ("?-hook_siamese_long_hook_and_?-boat", 19),
                   "xs18_0696z319l96": ("00c0012002a6012900260060", 19),
                   "xs18_xcil96z6513": ("hook_on_loaf_siamese_loaf", 19),
                   "xs18_ca2453z3553": ("long_integral_and_?-cap", 19),
                   "xs18_o4q2ri96z01": ("005000bc0082005500350002", 19),
                   "xs18_39mkia4z321": ("big_ghost", 19),
                   "xs18_69egeiczw23": ("0030004800390007003800240018", 19),
                   "xs18_69mkkoz04a6": ("?-long_R-bee_siamese_beehive_and_?-boat", 19),
                   "xs18_0j5c453zc93": ("?-dock_siamese_carriers", 19),
                   "xs18_178ba96zw33": ("006a002d0021001e000000180018", 19),
                   "xs18_65paj2aczx1": ("?-shillelagh_siamese_eater_on_boat", 19),
                   "xs18_0j1uge2z343": ("?-long_eater_siamese_eater_on_beehive", 19),
                   "xs18_3pmzw34aik8": ("?-mango_with_trans-tail_siamese_shillelagh", 19),
                   "xs18_g88b96z12pm": ("01800240034d005300480030", 19),
                   "xs18_69iczxd59a4": ("00c001200090006b000a000900050002", 19),
                   "xs18_660u93z3521": ("?-boat_with_cis-tail_siamese_hook_and_block", 19),
                   "xs18_gbhe0eicz11": ("boat_with_nine_and_cis-R-bee", 19),
                   "xs18_rb88czx178c": ("Z_and_?-eater_and_block", 19),
                   "xs18_69ab96zw253": ("0060009600d5005200900060", 19),
                   "xs18_0ojdzca22ac": ("dock_and_?-shillelagh", 19),
                   "xs18_o8brzx12596": ("00c0012000a00040003b000b00080018", 19),
                   "xs18_pf0sia4z023": ("?-carrier_siamese_table_on_R-loaf", 19),
                   "xs18_wggraiczc96": ("?-great_snake_eater_siamese_loop", 19),
                   "xs18_xgbqiczca23": ("0180014000400070000b001a0012000c", 19),
                   "xs18_3hu0ok8z643": ("?18?038", 19),
                   "xs18_ca9b8oz0696": ("006000a6012901a600200030", 19),
                   "xs18_o4qabq23z01": ("009000fc0002003d00250002", 19),
                   "xs18_25acz311dic": ("beehive_with_long_leg_and_?-long_boat", 19),
                   "xs18_0g6t1qrz121": ("?-tub_with_leg_siamese_shillelagh_and_block", 19),
                   "xs18_g886p3zdd11": ("01b001a80028002600190003", 19),
                   "xs18_jj0v146z121": ("006c0069000b0008006800500020", 19),
                   "xs18_wml1egoz643": ("00c000a0002000330005003400240018", 19),
                   "xs18_69acz6515a4": ("tub_with_nine_and_cis-R-loaf", 19),
                   "xs18_0bq1dicz321": ("beehive_with_long_tail_and_?-hook", 19),
                   "xs18_3iabpicz011": ("004c007a0001001d00260030", 19),
                   "xs18_c9baaczw352": ("R-iron_and_trans-boat", 19),
                   "xs18_6970v9zw321": ("?-table_siamese_eater_and_R-bee", 19),
                   "xs18_69egmaz0643": ("006000930071000e00680050", 19),
                   "xs18_c89f033z352": ("?-table_siamese_table_and_boat_and_block", 19),
                   "xs18_mligkcz1w66": ("?-very_long_eater_and_boat_and_block", 19),
                   "xs18_69r2qbzw121": ("0068002e0021006e00480030", 19),
                   "xs18_69ab96z0352": ("00600096005500d200900060", 19),
                   "xs18_25bob96z032": ("003600550042003c000800020006", 19),
                   "xs18_cikmgm96zx1": ("004000aa00ad0041003e0008", 19),
                   "xs18_gt3ob5z1221": ("00500068000e0061005d0006", 19),
                   "xs18_354mioz0696": ("?-beehive_with_tail_siamese_carrier_siamese_long_hook", 19),
                   "xs18_25a8a6z3596": ("tub_with_nine_and_?-R-loaf", 19),
                   "xs18_5bo796zw123": ("?-loop_siamese_beehive_siamese_eater", 19),
                   "xs18_32as0sicz032": ("?-eater_siamese_carrier_and_?-R-bee", 19),
                   "xs18_g88e13z178kc": ("?-boat_with_cis-tail_siamese_elevener", 19),
                   "xs18_4aabaa4zw256": ("00200050005300d5005200500020", 19),
                   "xs18_03lka96z2521": ("006000900050002c00aa00c50002", 19),
                   "xs18_0oggm93z4aic": ("0300024001a000260029006a0004", 19),
                   "xs18_3iab9a4z0123": ("006000260029006b004800280010", 19),
                   "xs18_069b8ozca511": ("0180014600a9002b00280018", 19),
                   "xs18_8u1mkicz0121": ("00180024001400360041003e0008", 19),
                   "xs18_31ege93z0321": ("00630055001400340008000a0006", 19),
                   "xs18_0mligz32w69c": ("0180012000d00012001500560060", 19),
                   "xs18_gw8ka53z11dd": ("trans-very_long_boat_with_long_leg_and_cis-block", 19),
                   "xs18_0330fpz35421": ("?-cis-shillelagh_siamese_table_and_block", 19),
                   "xs18_2lmg6qz32011": ("?-shillelagh_siamese_hook_and_boat", 19),
                   "xs18_4aq3s4oz32x1": ("0064004a001a0003001c00240018", 19),
                   "xs18_354mk46z0643": ("?-long_and_eater", 19),
                   "xs18_35akggkczx66": ("?18?141", 19),
                   "xs18_39egdbgzx121": ("?-loaf_siamese_carrier_on_hook", 19),
                   "xs18_0cp3z321079c": ("?18?045", 19),
                   "xs18_g8eh5egoz121": ("004000a000930065002c00240018", 19),
                   "xs18_w8u1dioz2521": ("004000a000500013003500140012000c", 19),
                   "xs18_0ml9akoz1221": ("003000480033000d003200240018", 19),
                   "xs18_64kja96z0321": ("0030004800280066001500130030", 19),
                   "xs18_31e88e13zw33": ("?-eater_on_eater_and_block", 19),
                   "xs18_3iabaa4z0123": ("006000260029006b002800280010", 19),
                   "xs18_252sgzciq221": ("018202450342005c00500020", 19),
                   "xs18_4a9r2qczx121": ("0018002e0041003b000a000a0004", 19),
                   "xs18_178b9a4z0253": ("008000e2001500d6009000500020", 19),
                   "xs18_03lkmicz3201": ("00600048001e0001001d00260030", 19),
                   "xs18_c8a52z315ak8": ("01000282014500aa0028006c", 19),
                   "xs18_0ggka53z3ego": ("03000280014000a30021002e0018", 19),
                   "xs18_2lla84czw346": ("004000a800ae0051001300200030", 19),
                   "xs18_35a8czw4a953": ("boat_with_leg_and_shift-R-mango", 19),
                   "xs18_2egm453zx346": ("00c000a30021006e000800700040", 19),
                   "xs18_3iar1e8z0121": ("?-eater_siamese_table_and_R-bee", 19),
                   "xs18_04a96zcid113": ("beehive_with_long_leg_and_?-loaf", 19),
                   "xs18_0ogka52zcia6": ("barge_with_leg_and_?-R-loaf", 19),
                   "xs18_xokk871z2596": ("?-loaf_on_R-bee_with_tail", 19),
                   "xs18_4ac0v1oozx23": ("very_long_Z_and_?-boat_and_block", 19),
                   "xs18_3pe0ok8z0643": ("00c0009b00710006001800280010", 19),
                   "xs18_0g88bqicz643": ("00c000a000200046003d0001000e0008", 19),
                   "xs18_0oggm93zcia4": ("0300024001a00024002a00690006", 19),
                   "xs18_0c88e13z6996": ("?-eater_siamese_table_and_trans-pond", 19),
                   "xs18_4a9b88czw653": ("00300010001600d5009300500020", 19),
                   "xs18_4a9mggkczx56": ("?-long_eater_siamese_snake_on_loaf", 19),
                   "xs18_031e8gz69l91": ("00c0012302a1012e00280010", 19),
                   "xs18_25acggzcia43": ("?-loaf_with_trans-tail_on_long_boat", 19),
                   "xs18_35iczw123cko": ("?18?160", 19),
                   "xs18_wiu069a4z643": ("?-eater_siamese_table_and_?-loaf", 19),
                   "xs18_0caabgz8k871": ("0100028c010a00ea002b0010", 19),
                   "xs18_ggmd1e8z1246": ("00300050009600cd0001000e0008", 19),
                   "xs18_3lmggkcz0146": ("?-very_long_eater_siamese_carrier_and_ship", 19),
                   "xs18_0g31eoz8ld11": ("?-eater_siamese_long_hook_and_block", 19),
                   "xs18_0ckgf96z6221": ("00c0004c00540030000f00090006", 19),
                   "xs18_08u1ege2z321": ("?-sesquihat_siamese_hook", 19),
                   "xs18_31e88a6z0653": ("?-eater_siamese_long_hook_and_ship", 19),
                   "xs18_25a88a6z4a53": ("tub_with_long_nine_and_?-long_boat", 19),
                   "xs18_31e88gzcid11": ("0306020901d6005000500020", 19),
                   "xs18_8o6llicz0121": ("00180024005c0043003a000a0004", 19),
                   "xs18_25aczw311dic": ("?18?028", 19),
                   "xs18_35a88gzcid11": ("?-binocle_beehive_boat", 19),
                   "xs18_0o80uh3zca43": ("0180015800880060001e00110003", 19),
                   "xs18_08u1dik8z321": ("?-loaf_with_bend_tail_siamese_hook", 19),
                   "xs18_699eg6qzx121": ("?-R-pond_on_tub_with_long_tail", 19),
                   "xs18_0ogka53zca26": ("long_boat_with_leg_and_trans-hook", 19),
                   "xs18_0ca1u8z69521": ("?18?103", 19),
                   "xs18_256o696zw643": ("0060009000660019006300a00040", 19),
                   "xs18_wg8kiarz2543": ("00d80050004800280016000900050002", 19),
                   "xs18_25b88gzcid11": ("?-binocle_boat_beehive", 19),
                   "xs18_ciq3c4ozx311": ("00180024002c0063001a0012000c", 19),
                   "xs18_39u06952z032": ("?-hook_siamese_snake_and_?-loaf", 19),
                   "xs18_0okk871zca26": ("01800158005400d4000800070001", 19),
                   "xs18_c82t2sgz0643": ("003000280008000b006a004a00140008", 19),
                   "xs18_6is0f9gzx311": ("00300024001c0003007a004a0004", 19),
                   "xs18_0ca2s53z6511": ("00c000ac002a0022001c00050003", 19),
                   "xs18_39u0oka4z023": ("long_and_cis-long_boat", 19),
                   "xs18_259a4ozca511": ("0182014500a9002a00240018", 19),
                   "xs18_g08e13z19l96": ("0300020c01d2005500120030", 19),
                   "xs18_0mligoz122ac": ("003000130095015400d40008", 19),
                   "xs18_06996z31178c": ("eater_siamese_table_and_cis-pond", 19),
                   "xs18_0oggm952zca6": ("0180015800d000100016000900050002", 19),
                   "xs18_0iu0ep3z1221": ("0060005600140034002600090006", 19),
                   "xs18_4akggm93zw66": ("00c000a200250042003c0000000c000c", 19),
                   "xs18_2lmggkcz01w66": ("very_long_eater_and_?-boat_and_block", 19),
                   "xs18_356o8zy011dic": ("ship_on_beehive_with_nine", 19),
                   "xs18_0g8id1egoz321": ("0180014000a30055001400240018", 19),
                   "xs18_32akggkczw4a6": ("0180008000a200550016001000500060", 19),
                   "xs18_0gwcq23z8ld11": ("03000100016000d00010001600350002", 19),
                   "xs18_ckgog853z06a4": ("?-canoe_siamese_hook_and_boat", 19),
                   "xs18_0g9f0kcz34311": ("006000900069002f00200014000c", 19),
                   "xs18_69ak8zx121ego": ("0300020001c0002000480034000a00090006", 19),
                   "xs18_25a8cicz06511": ("?18?126", 19),
                   "xs18_0g8ehu066z121": ("?-tub_with_long_leg_siamese_long_R-bee_and_trans-block", 19),
                   "xs18_g8o0e96z1254c": ("00c0012000e30002003a00240018", 19),
                   "xs18_312kozw122qic": ("03000200011000a80068000b00090006", 19),
                   "xs18_031e88gzo8a511": ("03000103014100ae002800280010", 19),
                   "xs18_256o8gzy134aic": ("0180024001400080007000080018000600050002", 19),
                   "xs18_0ggm96z3eg8gzx1": ("?-beehive_with_nine_siamese_tub_with_tail", 19),
                   "xs18_5b8raar": ("?-snake_eater_siamese_table_and_table", 20),
                   "xs18_69ariar": ("?-snake_siamese_loop_siamese_table", 20),
                   "xs18_69ir9ar": ("005a006d0001007a004c", 20),
                   "xs18_6is079ar": ("00b000d3001500e40086", 20),
                   "xs18_bdzbd1da": ("01ad016b0008000b0005", 20),
                   "xs18_32qbgn96": ("009600f500050032002c", 20),
                   "xs18_32qjc32ac": ("012801ee001100530060", 20),
                   "xs18_178jd0eio": ("01b000a6009400550023", 20),
                   "xs18_i5r8brz11": ("003600350002003c00250003", 20),
                   "xs18_ca9jz3lp1": ("03300253015500d8", 20),
                   "xs18_17871uge2": ("?-hat_siamese_long_eater_siamese_eater", 20),
                   "xs18_358go3tic": ("?-R-loaf_siamese_boat_and_canoe", 20),
                   "xs18_mmgm96z56": ("00b600d60010001600090006", 20),
                   "xs18_178brzwbd": ("?-snake_on_trans-legs_and_block", 20),
                   "xs18_qmgm93z66": ("00da00d60010001600090003", 20),
                   "xs18_3lkkozpi6": ("0323025500d400140018", 20),
                   "xs18_mlhe0mqz1": ("004000730009006a004b0030", 20),
                   "xs18_253gv1okc": ("?-Z_and_ship_and_boat", 20),
                   "xs18_358e1fgkc": ("?18?118", 20),
                   "xs18_2lliczpic": ("0322025501950012000c", 20),
                   "xs18_3lkiarz32": ("006c00280024001400550063", 20),
                   "xs18_356o8bp46": ("?-carrier_on_table_on_ship", 20),
                   "xs18_178jt0696": ("01b200a5009500520030", 20),
                   "xs18_4a9jz69ld": ("033602550152008c", 20),
                   "xs18_32hv079a4": ("016c01aa002900260060", 20),
                   "xs18_330fhm853": ("01b301a9002a00240018", 20),
                   "xs18_31egu178c": ("018c0154005500530030", 20),
                   "xs18_j5c453zdb": ("01b30165000c000400050003", 20),
                   "xs18_2ego1vg33": ("01b001a30022002a006c", 20),
                   "xs18_3146178br": ("?-carrier_on_trans-legs_and_block", 20),
                   "xs18_ciu0drzx32": ("?-snake_siamese_carrier_on_cap", 20),
                   "xs18_31egu2og4c": ("030002b000a300a9006c", 20),
                   "xs18_3lkm853z32": ("0063005500140034000800500060", 20),
                   "xs18_3pab96zw56": ("00c00098005500d300900060", 20),
                   "xs18_gs2d96z69c": ("00d0013c0182000d00090006", 20),
                   "xs18_rb079k8z23": ("?-tub_with_leg_and_snake_and_block", 20),
                   "xs18_69iczxdl96": ("01800240012000d600150012000c", 20),
                   "xs18_31e8gzcild": ("0306020901d500560020", 20),
                   "xs18_ciqjkczx66": ("00300048005800cb002b0030", 20),
                   "xs18_o8blkcz643": ("00d80088006b00150014000c", 20),
                   "xs18_oimge13z66": ("00d800d200160010000e00010003", 20),
                   "xs18_5b88brz033": ("006c00680008000b006b0050", 20),
                   "xs18_mllmz1w346": ("?18?061", 20),
                   "xs18_0jhu0uiz32": ("006000530011001e0000001e0012", 20),
                   "xs18_08u1qrz643": ("00d800580080007e00110003", 20),
                   "xs18_3pmkk8z4a6": ("?-long_bee_siamese_shillelagh_and_boat", 20),
                   "xs18_oghn871z66": ("00d800d000110017000800070001", 20),
                   "xs18_3loz320f96": ("018c01540030000f00090006", 20),
                   "xs18_9fgfhoz023": ("00480079000700780044000c", 20),
                   "xs18_0h7ojdz343": ("00b000c8001800e600890006", 20),
                   "xs18_8u1raa4z23": ("006000200028006e0021002e0018", 20),
                   "xs18_ciar2pmzw1": ("0028005e0041002d006a0004", 20),
                   "xs18_2ego8gu156": ("018002430342005a006c", 20),
                   "xs18_raaczx3596": ("R-hat_and_trans-R-loaf", 20),
                   "xs18_69r4koz643": ("00c60089007b000400140018", 20),
                   "xs18_4s3qicz643": ("00c4009c0063001a0012000c", 20),
                   "xs18_c88e13zdjo": ("0300020001c00043005900d6", 20),
                   "xs18_5bo796z321": ("?-loop_siames_hook_siamese_beehive", 20),
                   "xs18_oggo8brz66": ("?-siamese_tables_and_blocks", 20),
                   "xs18_69bkk8z653": ("00c600a9006b001400140008", 20),
                   "xs18_3p6gmaz643": ("00c30099006600100016000a", 20),
                   "xs18_cq2r9a4z23": ("006000200028006e0041003a000c", 20),
                   "xs18_caab4koz33": ("006c006a000a000b000400140018", 20),
                   "xs18_3iab96z643": ("00c30092006a000b00090006", 20),
                   "xs18_69ab96z253": ("00620095005600d000900060", 20),
                   "xs18_628c1fgka6": ("00c0012c02a903230030", 20),
                   "xs18_j9egm96z11": ("0062005500150032004c0060", 20),
                   "xs18_oggrb8oz66": ("00d800d00010001b000b00080018", 20),
                   "xs18_3iab96z343": ("?18?027", 20),
                   "xs18_0drz3210796": ("?-hook_siamese_snake_and_?-R-bee", 20),
                   "xs18_ca23z311dic": ("0180024001a30022002a006c", 20),
                   "xs18_0gjlicz32ac": ("00600090015301950014000c", 20),
                   "xs18_32qb871z321": ("?-trans-legs_siamese_eater_and_table", 20),
                   "xs18_69arzx12596": ("?-loaf_with_trans-tail_siamese_loop", 20),
                   "xs18_35a4ozxol56": ("?-long_boat_with_trans-tail_on_eater", 20),
                   "xs18_32156o8gka6": ("?-boat_with_long_tail_on_shillelagh", 20),
                   "xs18_rb88czx35a4": ("Z_and_trans-long_boat_and_block", 20),
                   "xs18_3lk2sgz3443": ("00c600a90029004600380008", 20),
                   "xs18_3pa4zw23qic": ("0300026001480098000b00090006", 20),
                   "xs18_8e1raiczw23": ("0018002e0021006d000a00080018", 20),
                   "xs18_08u156z69ko": ("01800280020301e50052000c", 20),
                   "xs18_gjlkicz1w66": ("0030004b002b00a800c8000c", 20),
                   "xs18_ca1t2sgz311": ("006c002a0021001d0002001c0010", 20),
                   "xs18_wmkk871z696": ("010001c000200050005000d600090006", 20),
                   "xs18_0ggm96zpia6": ("03200250015000d600090006", 20),
                   "xs18_3lka952z321": ("006600490032000c003000500060", 20),
                   "xs18_9fgciicz023": ("0060002600290069001600100030", 20),
                   "xs18_0o4a96zphe2": ("0320023801c4004a00090006", 20),
                   "xs18_39u06952z32": ("?-hook_siamese_carrier_and_?-loaf", 20),
                   "xs18_ml56z1248a6": ("cis-shillelagh_and_?-cap", 20),
                   "xs18_03lmge2z256": ("004000a300d500160010000e0002", 20),
                   "xs18_3lk6iozw343": ("?-hat_siamese_carrier_siamese_hook", 20),
                   "xs18_rb88czx354c": ("01b001a00020002c006a00020003", 20),
                   "xs18_8p7gf9z1221": ("0048007800060071004d000a", 20),
                   "xs18_69egeiozw23": ("003000480039000700380024000c", 20),
                   "xs18_178bdzx6513": ("R-loop_and_?-R-bee", 20),
                   "xs18_x8o653z695d": ("0180014000c00030002b000a00090006", 20),
                   "xs18_4aab8oz2596": ("004400aa012a00cb00080018", 20),
                   "xs18_069jzca2696": ("01800146004900d3012000c0", 20),
                   "xs18_8u15a8oz346": ("0068009e00c10005000a00080018", 20),
                   "xs18_0mkhf0ccz32": ("00c000800070000b006b00480018", 20),
                   "xs18_0jhu0ooz1ac": ("00300030000000f0011301950008", 20),
                   "xs18_wmmge13z652": ("00c000ac002c0020001c000200050003", 20),
                   "xs18_raabgzx3452": ("trans-loaf_with_long_nine_and_cis-table", 20),
                   "xs18_31kmp3z01ac": ("0180013000d3005501080180", 20),
                   "xs18_35a4z311d96": ("018c014800a8004b00090006", 20),
                   "xs18_c88c2dicz33": ("?-beehive_siamese_tub_on_table_and_block", 20),
                   "xs18_354cz69d113": ("01860149004b00680008000c", 20),
                   "xs18_8kkjq23z066": ("00c00040005800c8002b002b0010", 20),
                   "xs18_4a96zad1156": ("014401aa0029002600a000c0", 20),
                   "xs18_mkhjoz1w6a4": ("00d800500110019600350002", 20),
                   "xs18_25iczxdd1e8": ("010001c0002001a001ac001200050002", 20),
                   "xs18_3560uiz0653": ("table_on_ship_and_?-ship", 20),
                   "xs18_4a9egmqzx32": ("002c00340005003b004800280010", 20),
                   "xs18_03lka53z643": ("00c000a00050002800ae00c10003", 20),
                   "xs18_gbq23qicz01": ("0048007e0001006500a60040", 20),
                   "xs18_2lm0e96z056": ("?-R-bee_and_boat_and_snake", 20),
                   "xs18_0jiq32acz32": ("?-eater_siamese_table_and_eater", 20),
                   "xs18_0ol3zca25ac": ("01800158005500a301400180", 20),
                   "xs18_ciljgozwca4": ("006000900153019500120030", 20),
                   "xs18_0mp3zca22ac": ("dock_and_?-shillelagh", 20),
                   "xs18_259qb96z032": ("003600590042003c000800020006", 20),
                   "xs18_02llicz25ac": ("0060009001530155008a0004", 20),
                   "xs18_rq2kozx34a4": ("01b000b00080005c003200050002", 20),
                   "xs18_651u8zxc953": ("00c00140010000f30029000a000c", 20),
                   "xs18_3iaczw19l96": ("03000120015000d200150012000c", 20),
                   "xs18_cikl3zx69a4": ("00800140012300d500140012000c", 20),
                   "xs18_6ao2d96z321": ("0066004a00380002000d00090006", 20),
                   "xs18_3lm88cz3443": ("00c600a90069001600100030", 20),
                   "xs18_g88e13zd553": ("?-elevener_on_eater", 20),
                   "xs18_39mkkozw6a4": ("0180012000d6005500520030", 20),
                   "xs18_g85r8jdz121": ("006c00280044005a002900050002", 20),
                   "xs18_0mkid1e8z32": ("00c000800070000b006a0052000c", 20),
                   "xs18_mligoz1w6ac": ("?-Z-and_ship_and_boat", 20),
                   "xs18_69baikozx32": ("0030005c0042003900070008000c", 20),
                   "xs18_69ar4kozw23": ("003000480029006f00100014000c", 20),
                   "xs18_39u0oge2z32": ("00c000a30022006a002c008000c0", 20),
                   "xs18_ck0ol3z3543": ("00c000a8001e0001002d0036", 20),
                   "xs18_cilmggozx66": ("0030004800a8006b000b00080018", 20),
                   "xs18_g069icz19ld": ("cis-mango_with_long_leg_and_?-boat", 20),
                   "xs18_8e1u0drzx11": ("0064004a002a006b00480018", 20),
                   "xs18_4a9mge2z253": ("004400aa006900160010000e0002", 20),
                   "xs18_65lmzx34aa4": ("00c00140015000dc0002000500050002", 20),
                   "xs18_03lkk8zoja4": ("030002630155009400140008", 20),
                   "xs18_c89f0ck8z33": ("?-table_siamese_table_and_boat_and_block", 20),
                   "xs18_ggm970796z1": ("010001c00022005500550036", 20),
                   "xs18_65lmge13zw1": ("00c600a9002f0020001c0004", 20),
                   "xs18_xgs2qrz4a43": ("?-tub_with_leg_siamese_trans-legs_and_block", 20),
                   "xs18_mll2z1w32ac": ("0180014000400062001500150036", 20),
                   "xs18_2lm0uizw343": ("?-hat_siamese_table_and_boat", 20),
                   "xs18_25aczcid113": ("0182024501aa002c00200060", 20),
                   "xs18_gs2pmzx34ac": ("01800140009600790002001c0010", 20),
                   "xs18_0ca1t6zad11": ("014001ac002a0021001d0006", 20),
                   "xs18_cilmzx34aa4": ("0080014001400080007600150012000c", 20),
                   "xs18_259mkkozx66": ("?-long_R-bee_siamese_loaf_and_cis-block", 20),
                   "xs18_6is0fpz1221": ("004c00780002001d00250032", 20),
                   "xs18_0c93z69d552": ("?18?153", 20),
                   "xs18_wmmge13z256": ("00c000ac002c0020001c000200050006", 20),
                   "xs18_g069iczdl91": ("01b002a0012600290012000c", 20),
                   "xs18_5b88a6z6952": ("014601a9002a002400a000c0", 20),
                   "xs18_3ihu06a4z32": ("00c0008000700012001500d600a0", 20),
                   "xs18_0mp3z3462ac": ("01800140004300d900960060", 20),
                   "xs18_69eg8ozca23": ("01860149004e007000080018", 20),
                   "xs18_gbq1dicz121": ("0030004b003a0001000d0012000c", 20),
                   "xs18_g259acz11db": ("006000a0012d014b00880018", 20),
                   "xs18_39u069a4z32": ("?-hook_siamese_carrier_and_?-loaf", 20),
                   "xs18_39mkkoz04a6": ("0180012200d5005600500030", 20),
                   "xs18_2ege996zx56": ("0060009000930075000800700040", 20),
                   "xs18_cill2zx25ac": ("0180014000a2005500150012000c", 20),
                   "xs18_q6ge1dicz01": ("004000a20095005500d2000c", 20),
                   "xs18_628s2qrz032": ("006c002c0020001c000900230030", 20),
                   "xs18_03lmge2z652": ("00c000a3005500160010000e0002", 20),
                   "xs18_64km1e8z643": ("00c60084007400160001000e0008", 20),
                   "xs18_354kmzx12pm": ("?-boat_with_long_tail_and_long_hook", 20),
                   "xs18_4aab9aczx33": ("0018002e0041007e000000180018", 20),
                   "xs18_69fgkcz0643": ("?18?151", 20),
                   "xs18_0696z39d552": ("iron_and_beehive", 20),
                   "xs18_ca96z315a8o": ("03000100014600a9002a006c", 20),
                   "xs18_xml5a4zca43": ("?-boat_with_trans-tail_and_R-bee_siamese_tub", 20),
                   "xs18_39egma4zx56": ("?-hook_on_snake_on_boat", 20),
                   "xs18_xohf0ccz653": ("?-ship_on_long_hook_and_cis-block", 20),
                   "xs18_25t2sgz4a43": ("008201450172008c00700010", 20),
                   "xs18_0db8b52z253": ("?-cis-boat_with_long_leg_siamese_snake_and_?-boat", 20),
                   "xs18_x8u156z255d": ("00c00140010000f0002b000a000a0004", 20),
                   "xs18_c4o0ojdz643": ("dock_and_?-shillelagh", 20),
                   "xs18_3j0v146z321": ("006c0069000b0008002800500060", 20),
                   "xs18_c93z311dik8": ("trans-loaf_with_long_leg_and_?-carrier", 20),
                   "xs18_0jhu0696z32": ("?-long_hook_siamese_eater_and_beehive", 20),
                   "xs18_8kkljgozx66": ("001800180000007e0041000e00100018", 20),
                   "xs18_iu06996z146": ("?-table_siamese_carrier_and_pond", 20),
                   "xs18_0j1u0uiz321": ("006000530021001e0000001e0012", 20),
                   "xs18_69mkkozw6a4": ("?-bee_siamese_long_R-bee_and_?-boat", 20),
                   "xs18_o4q2r9icz01": ("004000aa00ad0041003a000c", 20),
                   "xs18_31kmge2z643": ("?-trans-legs_siamese_eater_and_carrier", 20),
                   "xs18_2lligoz3426": ("00620095005500d200100018", 20),
                   "xs18_69a4ozxol56": ("?-loaf_with_trans-tail_on_eater", 20),
                   "xs18_354kl3z4a43": ("dock_and_para-tub_with_tail", 20),
                   "xs18_4a9b8oz6952": ("00c4012a00a9004b00080018", 20),
                   "xs18_rb079a4z023": ("?-R-loaf_and_carrier_and_block", 20),
                   "xs18_0jhu0okcz32": ("?-eater_siamese_long_hook_and_ship", 20),
                   "xs18_gbqikoz1246": ("0030004b009a00d200140018", 20),
                   "xs18_g6s178b5z11": ("?-loop_siamese_carrier_siamese_hook", 20),
                   "xs18_cic88brzw23": ("006c00680008000b001900240018", 20),
                   "xs18_bd0u2kozw23": ("?18?004", 20),
                   "xs18_35a88czca53": ("?18?114", 20),
                   "xs18_3hu0628c48c": ("?18?150", 20),
                   "xs18_39u0o4oz65x1": ("?-long_snake_siamese_eater_and_beehive", 20),
                   "xs18_699mg6qzx121": ("0030004b004a0031000d000a0004", 20),
                   "xs18_039mkicz2521": ("004000a30049003600140012000c", 20),
                   "xs18_354mgmaz0252": ("00c000a20025006a000800680050", 20),
                   "xs18_352s0ccz6511": ("?-trans-boat_with_long_leg_siamese_eater_and_?-block", 20),
                   "xs18_178c8a6z3113": ("?-hook_siamese_eater_and_table", 20),
                   "xs18_035a8ozok871": ("03000283010500ea00280018", 20),
                   "xs18_69acggkczx56": ("0060009000500035000b000800280030", 20),
                   "xs18_312kmicz0643": ("00c000830041002e006800480030", 20),
                   "xs18_gwgila4zdd11": ("?-barge_with_cis-tail_siamese_table_and_block", 20),
                   "xs18_gw8o652zdl91": ("01b002a0012000280018000600050002", 20),
                   "xs18_696k4oz0ad11": ("00c0012500cb005800480030", 20),
                   "xs18_069acz4a5156": ("00c000ac002a00a901460080", 20),
                   "xs18_035a8a6z6513": ("boat_with_nine_and_?-hook", 20),
                   "xs18_ok8ge96z6221": ("00d8005400480030000e00090006", 20),
                   "xs18_w6a8a53z2553": ("boat_with_nine_and_meta-R-bee", 20),
                   "xs18_0gamge13z343": ("00c000ac00280024001a000500050002", 20),
                   "xs18_03lka23zc452": ("0180008300b50054000a00020003", 20),
                   "xs18_354mkk8z0256": ("00c000a20025006b002800280010", 20),
                   "xs18_3lo0ok8z3443": ("?-pond_siamese_long_snake_on_boat", 20),
                   "xs18_g88a52z19l96": ("0100028c0152005500520030", 20),
                   "xs18_0c4gf96z6521": ("00c000ac00440030000f00090006", 20),
                   "xs18_8o1v0ccz3421": ("006800980041003f0000000c000c", 20),
                   "xs18_0gillicz1246": ("0030004800a800ab0049000a0004", 20),
                   "xs18_025b8oz69d11": ("00c0012201a5002b00280018", 20),
                   "xs18_39m88a6z0643": ("00c0009300690016001000500060", 20),
                   "xs18_0i5p64koz321": ("00c000a000530011002e00480030", 20),
                   "xs18_g88b5oz011dd": ("0030014b01ab002800280010", 20),
                   "xs18_39u069a4z032": ("00c400aa00290066002000400060", 20),
                   "xs18_06a8a52z3596": ("tub_with_nine_and_?-R-loaf", 20),
                   "xs18_2egm996z0641": ("006000900090006c000900730040", 20),
                   "xs18_035a8a6z2553": ("boat_with_nine_and_?-R-bee", 20),
                   "xs18_4aab8oz035a4": ("004000ac00aa01a500220030", 20),
                   "xs18_39c8a52z2552": ("?-tub_with_leg_siamese_carrier_and_beehive", 20),
                   "xs18_xogka53zca26": ("long_boat_with_leg_and_?-hook", 20),
                   "xs18_312kmicz0256": ("00c000820045002b006800480030", 20),
                   "xs18_39cgcia4zx56": ("00c000900030000d0033004800500020", 20),
                   "xs18_3hu0696z0146": ("00c0008c00790003006000900060", 20),
                   "xs18_ckl3z0470652": ("004000a000c0000300f50094000c", 20),
                   "xs18_0gjlkk8z3426": ("00600090005300d5001400140008", 20),
                   "xs18_356o8a6z2521": ("?-tub_with_tail_siamese_eater_on_ship", 20),
                   "xs18_39mggkcz04a6": ("0180012200d50016001000500060", 20),
                   "xs18_0c9jz3215aa4": ("00800140014000b30029004c0060", 20),
                   "xs18_ca96z3116413": ("006c002a002900c6008000200060", 20),
                   "xs18_25a8kicz0653": ("004000a300550016002800480030", 20),
                   "xs18_2lm0e96z0146": ("?-R-bee_and_boat_and_carrier", 20),
                   "xs18_8ehd2sgzw123": ("00180024002a006a00130014000c", 20),
                   "xs18_wj5s2sgz4701": ("00c000400050002b000a001a00240030", 20),
                   "xs18_178baaczx252": ("008000e0001000d2005500520030", 20),
                   "xs18_39s0s4oz65x1": ("00c300a9001c0000001c00240018", 20),
                   "xs18_3hu08oz0c871": ("0180011300f1000e00280030", 20),
                   "xs18_0cklb8oz6221": ("snake_eater_siamese_R-bee_siamese_eater", 20),
                   "xs18_2lligkcz0146": ("004000ac00a9004b000800280030", 20),
                   "xs18_04aabgzcid11": ("0180024401aa002a002b0010", 20),
                   "xs18_4a97o4kozx23": ("0030005000960069000b00080018", 20),
                   "xs18_25acz31132ac": ("?-eater_siamese_table_and_long_boat", 20),
                   "xs18_0db88gz69d11": ("00c0012d01ab002800280010", 20),
                   "xs18_2lm88a6z3421": ("00620095005600280008000a0006", 20),
                   "xs18_w3lkia4z4a43": ("008001400083007500140012000a0004", 20),
                   "xs18_32qczx11dik8": ("03000100016000d000100016000900050002", 20),
                   "xs18_0g6pb871z321": ("00d8005400440038000a00050003", 20),
                   "xs18_32qbgzx25aa4": ("0180008000b001a4001a000500050002", 20),
                   "xs18_i5lmz11025a4": ("?-barge_with_long_tail_and_?-R-bee", 20),
                   "xs18_6a88b9czw253": ("006000500012001500d600900030", 20),
                   "xs18_8kkmhbgzx641": ("00300028000e0021005e002000080018", 20),
                   "xs18_8ehbaiczw121": ("0018002e0021006d001200140008", 20),
                   "xs18_0cq1e853z321": ("00c8009400520036000400050003", 20),
                   "xs18_cis0f9gzx311": ("0030001200150035004600380008", 20),
                   "xs18_255m88czwc93": ("?-eater_siamese_carrier_on_R-bee", 20),
                   "xs18_4a9b8oz035a4": ("004000ac012a01a500220030", 20),
                   "xs18_0g8ka53z6b8o": ("?-very_long_boat_with_trans-tail_siamese_eater", 20),
                   "xs18_039e0oozc871": ("?-hook_and_eater_and_block", 20),
                   "xs18_0gillicz1226": ("0030004800a800ab004a000a0004", 20),
                   "xs18_03lk48a6z643": ("00c000a0002000300006003900430060", 20),
                   "xs18_4a4o796zw343": ("0060009000e60019002600500020", 20),
                   "xs18_69eg8kiczw23": ("R-bee_on_loaf_with_trans_tail", 20),
                   "xs18_03lk2sgz2543": ("?-great_snake_eater_and_R-loaf", 20),
                   "xs18_31e88b52zw33": ("[[?18?164]]", 20),
                   "xs18_032q4oz69b41": ("00c001230162009a00240018", 20),
                   "xs18_2l2s0si6z121": ("004000a300550014005600a00040", 20),
                   "xs18_wcp3ckoz2521": ("004000a0005000130035002600080018", 20),
                   "xs18_4s0v1eozw121": ("00180028002b006a004a00140008", 20),
                   "xs18_02lla8oz6521": ("00c000a200550035000a00080018", 20),
                   "xs18_w8p7871z6521": ("00d800500050002c0008000a00050003", 20),
                   "xs18_0j1u06acz321": ("trans-boat_with_long_nine_and_?-ship", 20),
                   "xs18_08e1eozc9311": ("?-hat_siamese_eater_siamese_carrier", 20),
                   "xs18_06akl3zca221": ("01800158005400a400c50003", 20),
                   "xs18_gg0s2qrz1243": ("00d800580040003e0001000a000c", 20),
                   "xs18_31e88gz39d11": ("018c010900eb002800280010", 20),
                   "xs18_356o696z0321": ("006200550035000a000800280030", 20),
                   "xs18_gilmz1w34aa4": ("?-beehive_with_tail_siamese_table_and_boat", 20),
                   "xs18_25b88a6z0653": ("cis-boat_with_long_nine_and_?-ship", 20),
                   "xs18_6a88b9czx352": ("006000500010001600d500920030", 20),
                   "xs18_g842arz011dd": ("01b000ab008b004800280010", 20),
                   "xs18_39u06ak8z032": ("00c000ac002a0065002200400060", 20),
                   "xs18_0354koz69a43": ("?-integral_siamese_loaf_with_cis-tail", 20),
                   "xs18_ci4o79iczw11": ("?-R-mango_on_R-mango", 20),
                   "xs18_0ggs252zpia6": ("03200250015000dc000200050002", 20),
                   "xs18_w6a8a53z6513": ("00c000ac004400380000000e00090003", 20),
                   "xs18_025a8oz69l91": ("00c0012202a5012a00280018", 20),
                   "xs18_064kl3zca521": ("long_hook_and_?-very_long_ship", 20),
                   "xs18_03hu066z6226": ("00c00043005100de000000060006", 20),
                   "xs18_0c93z65115ac": ("trans-boat_with_long_nine_and_?-carrier", 20),
                   "xs18_8kkm9aczx252": ("?-R-loaf_siamese_long_beehive_on_tub", 20),
                   "xs18_178b9a4zw352": ("008000e0001600d5009200500020", 20),
                   "xs18_259aczwca513": ("boat_with_leg_and_?-R-mango", 20),
                   "xs18_259a4oz4ad11": ("0082014501a9002a00240018", 20),
                   "xs18_0cq1ege2z321": ("00c000a00024006a004a002b0010", 20),
                   "xs18_259ab8ozw352": ("004000a00096005500d200100018", 20),
                   "xs18_259a4oz0255d": ("00800144012a00aa004b0030", 20),
                   "xs18_03hu06a4z643": ("00c000a0002000300012001500560060", 20),
                   "xs18_39u06a4z0346": ("?-shillelagh_siamese_hook_and_cis-boat", 20),
                   "xs18_8ka96zw11d96": ("00c0012001a60029002a00140008", 20),
                   "xs18_35a84ozca511": ("0183014500aa002800480030", 20),
                   "xs18_1784ozx32qic": ("02000380004000980068000b00090006", 20),
                   "xs18_035s2acz6521": ("00c000a30045003c0002000a000c", 20),
                   "xs18_3pabgzx125a4": ("0180013000a001a80014000a00050002", 20),
                   "xs18_069baa4z3113": ("006000260029006b000a000a0004", 20),
                   "xs18_25a4ozci9611": ("?-barge_with_trans-tail_on_mango", 20),
                   "xs18_gw8k453zdl91": ("03000280008000a00050001200150036", 20),
                   "xs18_0c88e1e8z653": ("?-hat_siamese_table_and_ship", 20),
                   "xs18_65licggzx343": ("006000a000a8004e0031000e0008", 20),
                   "xs18_cill68ozx121": ("001800280046003500150012000c", 20),
                   "xs18_0j9mkicz3201": ("006000530009003600140012000c", 20),
                   "xs18_25ao4koz4a43": ("0082014500a2003c004000500030", 20),
                   "xs18_ggml2z1w69ic": ("trans-mango_with_long_leg_and_?-boat", 20),
                   "xs18_69a4ozx230f9": ("trans-loaf_with_long_leg_and_shift-table", 20),
                   "xs18_259acz4a5123": ("tub_with_long_tail_and_?-R-mango", 20),
                   "xs18_31e88gozc871": ("0183010100ee0028002000100030", 20),
                   "xs18_69aczw6515a4": ("tub_with_nine_and_?-R-loaf", 20),
                   "xs18_697079ozx311": ("00360054005400230001000e0008", 20),
                   "xs18_69ic8a6z6221": ("00c600490052002c0008000a0006", 20),
                   "xs18_04a96z311dio": ("0300024601a9002a00240060", 20),
                   "xs18_8o1v0bdz0121": ("006c00280048006b000a000a0004", 20),
                   "xs18_g88alicz1253": ("0030004800a8006a00150012000c", 20),
                   "xs18_312km96z0643": ("00c000830041002e006800900060", 20),
                   "xs18_w6t1egoz2521": ("?18?134", 20),
                   "xs18_25a8ozx6b871": ("0080014000a00026003d0001000e0008", 20),
                   "xs18_0ogka23zcia6": ("03000100014000ac002a00690006", 20),
                   "xs18_0o4km952z643": ("00c000a0002000580044003a00090006", 20),
                   "xs18_2lmggkcz1226": ("004400aa006a000b000800280030", 20),
                   "xs18_gilicz1w6aa4": ("00800140014c00d2001500120030", 20),
                   "xs18_39eg8kiczw23": ("00c000a200250069001600100030", 20),
                   "xs18_5b8b94ozx311": ("006c00280042003d0001000e0008", 20),
                   "xs18_0gjlmz32w256": ("trans-boat_with_long_nine_and_cis-ship", 20),
                   "xs18_0g88bpicz643": ("00c000a000200046003d0001000a000c", 20),
                   "xs18_0ggo2ticz1ac": ("00600090017000800030001300150008", 20),
                   "xs18_35iczw1784ko": ("03000280013000dc0002000400050003", 20),
                   "xs18_31kmkk8z0346": ("00c000860029006b002800280010", 20),
                   "xs18_6t1e8zw115a4": ("00c00170010800e8002a00050002", 20),
                   "xs18_gilicz1w62ac": ("01800140004c00d2001500120030", 20),
                   "xs18_0jhu066z1226": ("?-long_hook_siamese_eater_and_block", 20),
                   "xs18_256o8go4og4c": ("04000a00061301a9016c", 20),
                   "xs18_g88riicz1226": ("00300048004800db00120012000c", 20),
                   "xs18_xogka52z6996": ("?-barge_with_leg_on_pond", 20),
                   "xs18_xcik871z6513": ("?-loaf_with_cis-tail_on_hook", 20),
                   "xs18_3pcw8ozwdd11": ("01800130006b000b000800280030", 20),
                   "xs18_69ligkcz0641": ("0060009300a9004c000800280030", 20),
                   "xs18_69iczx11dik8": ("?18?097", 20),
                   "xs18_0jhu0og4cz32": ("?18?115", 20),
                   "xs18_0mkid96z1221": ("?18?143", 20),
                   "xs18_64kbaicz0321": ("?18?159", 20),
                   "xs18_31462sgz04a53": ("?-eater_siamese_carrier_on_long_boat", 20),
                   "xs18_0gbaak8z34311": ("00600090006b002a002a00140008", 20),
                   "xs18_354kozx122ego": ("?-elevener_siamese_integral", 20),
                   "xs18_25a8kia4z0253": ("004000a600490032000c003000500020", 20),
                   "xs18_0gilmz32w254c": ("0180008000a000560015001200500060", 20),
                   "xs18_032acz65115a4": ("00c000a30022002a00ac01400080", 20),
                   "xs18_06a88a52z8e13": ("tub_with_long_nine_and_?-eater", 20),
                   "xs18_25ao48a6z2521": ("0060005000100020001c005200a50042", 20),
                   "xs18_g88m552z1254c": ("?-loaf_with_cis-tail_on_R-bee", 20),
                   "xs18_25acggkczw643": ("?-long_boat_on_elevener", 20),
                   "xs18_0oggka53z4aa4": ("trans-long_boat_with_long_leg_and_beehive", 20),
                   "xs18_356o8zy011dio": ("030002800180006000500010001600090003", 20),
                   "xs18_64kbaicz01221": ("0030001200150069002a00240018", 20),
                   "xs18_0c48a52z4a953": ("tub_with_long_tail_and_?-R-mango", 20),
                   "xs18_ok453zw3215a4": ("?-tub_with_long_tail_on_integral", 20),
                   "xs18_62s0v18ozx121": ("00300020001c0002007d00420008000c", 20),
                   "xs18_25aczw3115ak8": ("01000280015800d000100014000a00050002", 20),
                   "xs18_0gg0siarz1243": ("?-R-loop_on_loaf", 20),
                   "xs18_35a8czy0315ac": ("0180014000a00020006c0008000a00050003", 20),
                   "xs18_03pe0ok8z6221": ("?-snake_eater_siamese_hook_and_boat", 20),
                   "xs18_4a9b88czw2552": ("00300012001500d5009200500020", 20),
                   "xs18_259acga6zw311": ("006000930049003a000400380020", 20),
                   "xs18_03p64k8z25521": ("004000a300b90046002400140008", 20),
                   "xs18_02ege952z2521": ("00600096005400340008000a00050002", 20),
                   "xs18_xg8o653zca611": ("0180014000c0003000280018000600050003", 20),
                   "xs18_0jhk6icz32011": ("006000530011003400260012000c", 20),
                   "xs18_0oggka52z4aic": ("01000280014000a000260029006a0004", 20),
                   "xs18_2552sgz8ka221": ("01020285028a010800e80030", 20),
                   "xs18_0gwraicz12543": ("0030004800a8004a000d0001000e0008", 20),
                   "xs18_31e8gzw358gkc": ("0300020001d800540022000100050006", 20),
                   "xs18_252s0ckoz2521": ("tub_long_line_tub_and_?-ship", 20),
                   "xs18_g88m552sgz121": ("00800140012300c2003a00240018", 20),
                   "xs18_0ok2qbgz643w1": ("00c0009800740002001a002b0010", 20),
                   "xs18_252s0ca4z6521": ("00c200a50042003c0000000c000a0004", 20),
                   "xs18_25a88a53zx253": ("?-boat_long_line_tub_and_boat", 20),
                   "xs18_69a4ozy011dic": ("?-loaf_with_trans-tail_siamese_beehive_with_trans-tail", 20),
                   "xs18_0ca23z65115a4": ("tub_with_long_nine_and_?-eater", 20),
                   "xs18_0gilmz32w25a4": ("0080014000a000560015001200500060", 20),
                   "xs18_0oggs252zcia4": ("?-tub_with_tail_siamese_table_and_loaf", 20),
                   "xs18_354k8zx178kk8": ("03000280008000b0005c0002000500050002", 20),
                   "xs18_0g8kkm93z3421": ("00c000a000380044003a000900050002", 20),
                   "xs18_0j9c0s4z64311": ("00c000930069002c0020001c0004", 20),
                   "xs18_0oggs252z4aic": ("?-tub_with_tail_siamese_table_and_?-loaf", 20),
                   "xs18_696o8zx123ck8": ("018002400180007000480018000600050002", 20),
                   "xs18_31e8g0siczx23": ("0180014200450065001600100030", 20),
                   "xs18_g88q552z1254c": ("beehive_on_R-loaf_with_cis-tail", 20),
                   "xs18_0g08e13zoh953": ("03000230012000a8006e00010003", 20),
                   "xs18_3lowggozw3496": ("?18?069", 20),
                   "xs18_025a88gz8kid11": ("01000282024501aa002800280010", 20),
                   "xs18_256o8gzy132ako": ("0300028001400040007000080018000600050002", 20),
                   "xs18_03lkk8gz252x32": ("0060004000380004003a004200a30040", 20),
                   "xs18_0354kl3z642101": ("dock_and_?-very_long_snake", 20),
                   "xs18_0c93g8gz259701": ("004000ac012900e3001000280010", 20),
                   "xs18_wggs248a53z252": ("0600052002500190001c000200050002", 20),
                   "xs18_031e88gz8k8711": ("?-tub_with_tail_siamese_hat_siamese_eater", 20),
                   "xs18_w8k46164koz311": ("040007000083010100ee00280010", 20),
                   "xs18_035a88gz8ka511": ("01000283014500aa002800280010", 20),
                   "xs18_0g8k46164koz121": ("020005000283010100ee00280010", 20),
                   "xs18_y2g8o653z0g8421z32": ("very_very_very_long_canoe_on_ship", 20),
                   "xs19_69bo7pic": ("?19?004", 6),
                   "xs19_69icw8ozxdd11": ("[mango with block on dock]", 6),
                   "xs19_69b88gz69d11": ("?19?002", 8),
                   "xs19_gbb8brz123": ("?19?005", 9),
                   "xs19_mlhe0eicz1": ("?19?006", 10),
                   "xs19_0c88b96z6953": ("?19?046", 10),
                   "xs19_2egu1uge2": ("?19?020", 11),
                   "xs19_69b8brz033": ("?19?018", 11),
                   "xs19_39u0eicz321": ("?19?032", 11),
                   "xs19_3hikl3z32w23": ("?19?015", 11),
                   "xs19_3lkmicz346": ("?19?009", 12),
                   "xs19_mlhe0e96z1": ("?19?011", 12),
                   "xs19_69acz69d113": ("?19?078", 12),
                   "xs19_69mgmiczw66": ("?19?007", 12),
                   "xs19_0mmge96z3421": ("?19?027", 12),
                   "xs19_39u0u93zw121": ("?19?019", 12),
                   "xs19_69b88a6zw696": ("?19?050", 12),
                   "xs19_0mlhegoz1243": ("?19?053", 12),
                   "xs19_39u0e96z321": ("?19?031", 13),
                   "xs19_0696z355d96": ("?19?098", 13),
                   "xs19_cimgm96z066": ("?19?023", 13),
                   "xs19_mkkm96z1226": ("?19?092", 13),
                   "xs19_39u08kicz321": ("?19?030", 13),
                   "xs19_069b871z3156": ("?19?013", 13),
                   "xs19_25akozca22ac": ("?19?102", 13),
                   "xs19_gbbo8brz11": ("long_and_blocks", 14),
                   "xs19_0mmgm96z346": ("?19?121", 14),
                   "xs19_cc0s2qrz311": ("?19?085", 14),
                   "xs19_69b8b9czx33": ("?19?042", 14),
                   "xs19_39u0e93z321": ("trans-hook_and_long_dock", 14),
                   "xs19_c88b96z3596": ("?19?016", 14),
                   "xs19_0mmge93z3421": ("?19?021", 14),
                   "xs19_6a88bb8ozx33": ("?19?044", 14),
                   "xs19_04aabgz311dd": ("?19?109", 14),
                   "xs19_3lkmik8z0146": ("?19?012", 14),
                   "xs19_069iczciq226": ("?19?067", 14),
                   "xs19_0ml1eoz34611": ("?19?062", 14),
                   "xs19_2lligz32w696": ("beehive_with_long_nine_and_trans-beehive", 14),
                   "xs19_g88bbgz1255d": ("?19?039", 14),
                   "xs19_69b8bbgzx311": ("003600560040003e0001000e0008", 14),
                   "xs19_09v0ciicz321": ("?19?022", 14),
                   "xs19_025t2sgz3543": ("?19?040", 14),
                   "xs19_02lligz696w23": ("?19?129", 14),
                   "xs19_69bo3tic": ("?19?003", 15),
                   "xs19_mlhe0eioz1": ("?19?107", 15),
                   "xs19_39mge132ac": ("?19?057", 15),
                   "xs19_mlhe0e93z1": ("G_and_trans-hook", 15),
                   "xs19_h7o7picz11": ("006c002a0029001500560060", 15),
                   "xs19_ckggm96zca6": ("?19?086", 15),
                   "xs19_g4q9bqicz11": ("00c000a6003d0041002e0018", 15),
                   "xs19_cimgm93z066": ("00c0009000680008006b004b0030", 15),
                   "xs19_699egmqzx32": ("?-R-pond_on_eater_siamese_carrier", 15),
                   "xs19_4aab96z6952": ("?19?076", 15),
                   "xs19_4a96z69d552": ("[[?19?132]]", 15),
                   "xs19_69baicz6511": ("?19?028", 15),
                   "xs19_39u0eioz321": ("?19?097", 15),
                   "xs19_09v0f96z321": ("trans-cap_and_long", 15),
                   "xs19_0iu0mp3z643": ("?-shillelagh_and_long", 15),
                   "xs19_39mgmiczw66": ("[[?19?133]]", 15),
                   "xs19_0gbbob96z121": ("?19?108", 15),
                   "xs19_2lmgmicz3201": ("?19?008", 15),
                   "xs19_62sggm96zw66": ("?19?081", 15),
                   "xs19_69mggkcz0ca6": ("beehive_with_long_nine_and_ortho-ship", 15),
                   "xs19_651u0ooz0c93": ("?-worm_siamese_carrier_and_block", 15),
                   "xs19_2lmge93z1221": ("?19?058", 15),
                   "xs19_069acz311d96": ("?19?049", 15),
                   "xs19_69b8bbgzx321": ("003600560040003e0001000a000c", 15),
                   "xs19_0c93z255d1e8": ("?19?080", 15),
                   "xs19_4a9baa4zw696": ("racetrack_II_and_beehive", 15),
                   "xs19_697obbgzx121": ("003600560050002e0009000a0004", 15),
                   "xs19_31ege996zx23": ("00c600a90029002e001000080018", 15),
                   "xs19_w69b871z6513": ("G_and_meta-hook", 15),
                   "xs19_69fgf9gzx121": ("?-loaf_siamese_table_on_cap", 15),
                   "xs19_25a8czw311d96": ("tub_with_leg_and_ortho-worm", 15),
                   "xs19_2lligz32w25a4": ("?19?069", 15),
                   "xs19_256o8gzciq221": ("big_S_on_boat", 15),
                   "xs19_0o4a952z178a6": ("?19?071", 15),
                   "xs19_0mm0ep3z32011": ("?19?103", 15),
                   "xs19_gbb88a6z11w33": ("003000330001003e004000660006", 15),
                   "xs19_xj1u066z4a611": ("?19?010", 15),
                   "xs19_0358g0s4z4a9611": ("?19?099", 15),
                   "xs19_0c88brz6996": ("Z_and_pond_and_block", 16),
                   "xs19_4aab871z653": ("?19?084", 16),
                   "xs19_69a4z69d552": ("racetrack_and_?-loaf", 16),
                   "xs19_gbhe0ehrz01": ("?19?126", 16),
                   "xs19_69d2sgz2553": ("?19?017", 16),
                   "xs19_39u0uicz023": ("?19?035", 16),
                   "xs19_6a88brz2552": ("?19?074", 16),
                   "xs19_c88ml3z3543": ("00c000a8006e001100150036", 16),
                   "xs19_gbb871z178c": ("?19?130", 16),
                   "xs19_5b8b96z2552": ("00a200d5001500d200900060", 16),
                   "xs19_0br0f96z321": ("?-cap_and_hook_and_dock", 16),
                   "xs19_0mkkm93z346": ("00c0009000680028002b00690006", 16),
                   "xs19_4airiiczw66": ("00300048004800db004b00500020", 16),
                   "xs19_gs2qb96z1221": ("0030005c0042003a000b00090006", 16),
                   "xs19_3hu08ozca611": ("0183015100de002000280018", 16),
                   "xs19_6996z65115a4": ("tub_with_long_nine_and_trans-pond", 16),
                   "xs19_0dj8b96z6221": ("?-amoeba_8,5,5", 16),
                   "xs19_wmm0e952z643": ("?19?072", 16),
                   "xs19_4a96kk8z2553": ("?19?110", 16),
                   "xs19_gs2t1e8z6221": ("[[3 tails]]", 16),
                   "xs19_0g31eoz8ll91": ("?19?073", 16),
                   "xs19_3lkk8a6z3421": ("00c600a9002a002c001000500060", 16),
                   "xs19_0g6p3qicz321": ("00c000a0005600150021002e0018", 16),
                   "xs19_6ikm996z1221": ("?19?120", 16),
                   "xs19_69r2qcz03421": ("0060009600d90042005c0030", 16),
                   "xs19_c97obbgzx121": ("?19?024", 16),
                   "xs19_g88bbgz17871": ("003000e8010800eb002b0010", 16),
                   "xs19_0ggs2qb96z32": ("0180010000e8002e0021001d0006", 16),
                   "xs19_696o696zw343": ("?-3some_beehives", 16),
                   "xs19_0gs2596z12ego": ("018002400283010100ee00280010", 16),
                   "xs19_0cc0si52z2553": ("?-R-bee_on_tub_with_leg_and_block", 16),
                   "xs19_2lm0eicz32011": ("0062005500160020002e0012000c", 16),
                   "xs19_03lkkl3z252w1": ("?19?124", 16),
                   "xs19_0g8o652z2fgkc": ("?-fourteener_on_boat", 16),
                   "xs19_69bq1tic": ("006c00b2008500750016", 17),
                   "xs19_39mge1dic": ("018c0152005500950062", 17),
                   "xs19_g6p7ojdz11": ("?-long_integral_siamese_R-bee_on_shillelagh", 17),
                   "xs19_rb079icz23": ("?-R-mango_and_snake_and_block", 17),
                   "xs19_8u1raicz23": ("?19?115", 17),
                   "xs19_6a88brz653": ("?-very_long_eater_and_ship_and_block", 17),
                   "xs19_178jt069a4": ("0364014a012900a60060", 17),
                   "xs19_1no3tgz643": ("?19?054", 17),
                   "xs19_mllmz1w696": ("?19?025", 17),
                   "xs19_69baarz033": ("006c00280028006b004b0030", 17),
                   "xs19_3jgv1ooz32": ("?19?101", 17),
                   "xs19_okkmhrzw66": ("00d80088006b002b00280018", 17),
                   "xs19_mmge1dicz1": ("008000e2001500d500d2000c", 17),
                   "xs19_g6t1uge2z11": ("00c000ac002a006a004b0030", 17),
                   "xs19_0mm0e96zc96": ("?-shillelagh_and_R-bee_and_block", 17),
                   "xs19_8e1v0brzx11": ("?-long_Z_siamese_eater_siamese_carrier_and_block", 17),
                   "xs19_pf0raicz011": ("0068002e0021006d004a0030", 17),
                   "xs19_69b8b5z2552": ("00a000d0001200d500950062", 17),
                   "xs19_69bkkoz2552": ("0062009500d5002a00280018", 17),
                   "xs19_oggo2ticz66": ("?19?061", 17),
                   "xs19_cimgml96zx1": ("0060009600b50041003e0008", 17),
                   "xs19_ciligoz4aa6": ("008c0152015500d200100018", 17),
                   "xs19_0mllicz34a4": ("00600096015500950012000c", 17),
                   "xs19_39u0uh3z023": ("?19?034", 17),
                   "xs19_178b96z3156": ("?19?077", 17),
                   "xs19_4a96z255d96": ("?19?105", 17),
                   "xs19_3lkkl3z56w1": ("00c500ab0028002800ac00c0", 17),
                   "xs19_0mmgm93z346": ("00c0009000680008006b00690006", 17),
                   "xs19_8e1qb96z311": ("?19?065", 17),
                   "xs19_0mligoz34aa4": ("006000960155015200900018", 17),
                   "xs19_6ikm9a4z3421": ("?-loaf_siamese_carrier_on_R-loaf", 17),
                   "xs19_8e1e8gz17871": ("002800ee010100ee00280010", 17),
                   "xs19_c970brz06421": ("?19?088", 17),
                   "xs19_ckggka52zca6": ("trans-barge_with_long_nine_and_?-ship", 17),
                   "xs19_0gilmz122qq1": ("?19?038", 17),
                   "xs19_0178b96z2553": ("?19?095", 17),
                   "xs19_w69b871z2553": ("G_and_meta-R-bee", 17),
                   "xs19_0o4km96z3543": ("006000b800840074001600090006", 17),
                   "xs19_69a4z65115ac": ("cis-boat_with_long_nine_and_?-loaf", 17),
                   "xs19_354ljgozw346": ("00c000a0002600a900cb00080018", 17),
                   "xs19_39u0ep3zw121": ("0063005500140036002400140008", 17),
                   "xs19_xoie0e96z253": ("hook_on_boat_and_?-R-bee", 17),
                   "xs19_0c9b871z2596": ("alef_and_?-loaf", 17),
                   "xs19_2lligz32w69c": ("0180012000d00012001500550062", 17),
                   "xs19_caab9iczw311": ("0018002e0041005f0020001c0004", 17),
                   "xs19_025acz69d552": ("racetrack_and_cis-long_boat", 17),
                   "xs19_0g84q23z8lld": ("R-loaf_with_trans-tail_and_?-R-bee", 17),
                   "xs19_69e0ok8z2553": ("?19?087", 17),
                   "xs19_69a4ozx6b871": ("00c0012000a00046003d0001000e0008", 17),
                   "xs19_31kmkicz0346": ("00c000860029006b002800480030", 17),
                   "xs19_4a9mge2z4a43": ("0084014a008900760010000e0002", 17),
                   "xs19_0caabgz69d11": ("00c0012c01aa002a002b0010", 17),
                   "xs19_c88b96z315a4": ("?19?048", 17),
                   "xs19_gw8u156zdd11": ("01b001a000200028001e000100050006", 17),
                   "xs19_0gilmz1qq221": ("?19?114", 17),
                   "xs19_4a96z65115ac": ("trans-boat_with_long_nine_and_?-loaf", 17),
                   "xs19_g8e1eoz011dd": ("003000eb010b00e800280010", 17),
                   "xs19_0178b96z6513": ("G_and_para-hook", 17),
                   "xs19_4aab871z2552": ("anvil_and_trans-beehive", 17),
                   "xs19_3lk64koz3421": ("[[para-loaf and eater_siamese eater]]", 17),
                   "xs19_2lmggz122qq1": ("?-boat_and_very_long_bee_and_block", 17),
                   "xs19_gbb88a6z1253": ("006000500010001600d500d2000c", 17),
                   "xs19_69fgbbgzx121": ("?-cap_on_loaf_and_block", 17),
                   "xs19_3p6o8gz178c1": ("?19?066", 17),
                   "xs19_g08o652z1pl4c": ("hook_on_boat_and_?-hook", 17),
                   "xs19_69icw8ozx11dd": ("?19?123", 17),
                   "xs19_3lkmk46z01w23": ("?19?037", 17),
                   "xs19_0cc0si52z6513": ("?-block_and_hook_on_tub_with_leg", 17),
                   "xs19_35a84koz02553": ("00c000a200550015002600280018", 17),
                   "xs19_25akozwca22ac": ("dock_and_trans-very_long_boat", 17),
                   "xs19_0gjlkk8z32w66": ("006000500013001500d400d40008", 17),
                   "xs19_0c4o0ehrz2521": ("tub_with_nine_and_shift-C", 17),
                   "xs19_354mggkczw346": ("scorpio_and_?-hook", 17),
                   "xs19_06996z4a51156": ("?19?055", 17),
                   "xs19_4aab88a6zw253": ("?19?033", 17),
                   "xs19_25is0ca6zx346": ("?-tub_with_leg_siamese_eater_and_ship", 17),
                   "xs19_31egozwca22ac": ("dock_and_?-integral", 17),
                   "xs19_069b88cz4a513": ("worm_and_?-tub_with_leg", 17),
                   "xs19_025a8a6z65156": ("tub_with_nine_and_para-C", 17),
                   "xs19_0oggm952z4aic": ("trans-loaf_with_long_leg_and_para-loaf", 17),
                   "xs19_354k8gzx125aic": ("beehive_with_nine_at_loaf", 17),
                   "xs19_0g8k46164koz1221": ("030004800283010100ee00280010", 17),
                   "xs19_4a97079ar": ("R-loop_and_?-R-loaf", 18),
                   "xs19_651uge1da": ("00c6012901aa002b0030", 18),
                   "xs19_69b8b5z653": ("00c600a9006b0008000b0005", 18),
                   "xs19_mm0ehrz146": ("?-C_and_carrier_and_block", 18),
                   "xs19_2530fhu0oo": ("?-long_R-bee_siamese_long_R-bee_and_boat_and_block", 18),
                   "xs19_09v0fhoz321": ("long_and_?-long_hook", 18),
                   "xs19_69akgoz6996": ("00c60129012a00d400100018", 18),
                   "xs19_rq2kmzx3452": ("?19?026", 18),
                   "xs19_5b8b96z0356": ("00a000d6001500d300900060", 18),
                   "xs19_35a88brzw33": ("006c00680008000b002b00500060", 18),
                   "xs19_g8p78brz121": ("?-R-bee_on_trans-legs_and_block", 18),
                   "xs19_cimkkm93zx1": ("?19?106", 18),
                   "xs19_0dbz255d1e8": ("anvil_and_?-snake", 18),
                   "xs19_mmgm96z1226": ("006c006a000a006b00900060", 18),
                   "xs19_c88bqicz352": ("006c00a80048000b001a0012000c", 18),
                   "xs19_8kk3qicz643": ("?19?047", 18),
                   "xs19_651u0oozwdb": ("?-worm_siamese_snake_and_block", 18),
                   "xs19_c88bq2sgz33": ("?-trans-legs_and_Z_and_block", 18),
                   "xs19_g0t3on96z11": ("00c000ac002a002500150036", 18),
                   "xs19_cimkkm96zx1": ("?19?045", 18),
                   "xs19_ciiria4z066": ("0030004b004b00d8004800500020", 18),
                   "xs19_mlhikoz1226": ("?19?059", 18),
                   "xs19_c8all2z3543": ("006c00a8008a007500150002", 18),
                   "xs19_ca9b8oz3552": ("006c00aa00a9004b00080018", 18),
                   "xs19_0mkkm96z346": ("0060009600d40014001600090006", 18),
                   "xs19_mlhikoz1246": ("006c00aa0089004b00280018", 18),
                   "xs19_wggs2qrzc96": ("01b000b0008000700010001600090003", 18),
                   "xs19_c88bp2sgz33": ("00c000c0000b00fa008200140018", 18),
                   "xs19_wmmge13z696": ("0180010000e0001000d000d600090006", 18),
                   "xs19_69icz622qic": ("worm_and_trans-mango", 18),
                   "xs19_g6s1vg33z11": ("?19?079", 18),
                   "xs19_4aab9cz2553": ("iron_and_?-R-bee", 18),
                   "xs19_9f0v1eozx11": ("iron_and_trans-table", 18),
                   "xs19_69ba96z2552": ("0062009500d5005200900060", 18),
                   "xs19_178b96z3552": ("G_and_ortho-R-bee", 18),
                   "xs19_xojd453z653": ("?-eater_siamese_shillelagh_on_ship", 18),
                   "xs19_2ege996z0643": ("0060009000900076000900730040", 18),
                   "xs19_025t2koz3543": ("006000a20085007d000200140018", 18),
                   "xs19_354mkk8z0696": ("01800146004900d6005000500020", 18),
                   "xs19_0j9mkicz3421": ("006000930049003600140012000c", 18),
                   "xs19_6s1v0ciczw11": ("R-iron_and_beehive", 18),
                   "xs19_069a4oz311dd": ("00600026002901aa01a40018", 18),
                   "xs19_2lla8koz3421": ("?-3some_loaf_beehive_boat", 18),
                   "xs19_o8b96zx359a4": ("00800140012000a60069000b00080018", 18),
                   "xs19_0oggm96zciic": ("beehive_with_long_leg_and_trans-pond", 18),
                   "xs19_08e1eoz69d11": ("?-scorpio_siamese_hat", 18),
                   "xs19_g88m552zdd11": ("?-cap_on_R-bee_and_trans-block", 18),
                   "xs19_35a84ozcid11": ("030602890156005000900060", 18),
                   "xs19_354mkk8z0c96": ("01800143004900d6005000500020", 18),
                   "xs19_gw8u156z11dd": ("00c00140010000f0002b000b00080018", 18),
                   "xs19_354mik8z0696": ("?19?029", 18),
                   "xs19_gbaa4oz011dd": ("0030004b00ab00a801a80010", 18),
                   "xs19_gjligkcz1226": ("?-very_very_long_eater_siamese_eater_and_trans-boat", 18),
                   "xs19_8ehdazw12553": ("006000a000aa004d0031000e0008", 18),
                   "xs19_69bo7p8zx121": ("?-hat_siamese_G", 18),
                   "xs19_g88b96z11dic": ("?-beehive_with_tail_siamese_scorpio", 18),
                   "xs19_bq2kmicz0121": ("0068002e00210016003400240018", 18),
                   "xs19_178bb8ozw352": ("008000e0001600d500d200100018", 18),
                   "xs19_4a9baaczx352": ("R-racetrack_II_and_trans-boat", 18),
                   "xs19_1787p2sgzx23": ("?-amoeba_8,5,5", 18),
                   "xs19_0o4km93z3543": ("00c000900068002e0021001d0006", 18),
                   "xs19_8e1mkicz3121": ("0068002e0041003600140012000c", 18),
                   "xs19_6ic88brz0123": ("?-Z_siamese_long_integral_and_block", 18),
                   "xs19_025acz255d96": ("racetrack_and_?-long_boat", 18),
                   "xs19_bq1mkicz0121": ("?19?041", 18),
                   "xs19_4a9baaczw253": ("R-racetrack_II_and_?-boat", 18),
                   "xs19_g88ci96z11dd": ("?-mango_siamese_long_R-bee_and_block", 18),
                   "xs19_0gbbgn96z121": ("?-R-bee_long_line_tub_and_block", 18),
                   "xs19_ca9baiczw311": ("0018002e0041007d0002001c0010", 18),
                   "xs19_69egm96zx146": ("?19?089", 18),
                   "xs19_ok2t1e8z6221": ("?-amoeba_8,6,4", 18),
                   "xs19_696k4oz4ad11": ("00c2012500cb005800480030", 18),
                   "xs19_g84c0fhozc93": ("019001280064000c0000000f00110018", 18),
                   "xs19_0ogilicz4aa6": ("00800158015000d200150012000c", 18),
                   "xs19_cc0si53z4a43": ("?-boat_with_leg_siamese_tub_with_leg_and_block", 18),
                   "xs19_ca96z33032ac": ("?-R-loaf_and_eater_and_block", 18),
                   "xs19_0c9b871z6952": ("alef_and_?-loaf", 18),
                   "xs19_8e1t2sgz0643": ("?-amoeba_8,6,4", 18),
                   "xs19_69ligkczx4a6": ("cis-loaf_with_long_nine_and_?-boat", 18),
                   "xs19_2lmge96z1221": ("?-R-bee_on_R-bee_and_boat", 18),
                   "xs19_4aabaa4zw696": ("004000a000a601a900a600a00040", 18),
                   "xs19_39u08ka6z321": ("long_dock_and_long_boat", 18),
                   "xs19_178kozca22ac": ("?19?125", 18),
                   "xs19_39e0ok8z2553": ("?-hook_and_boat_on_R-bee", 18),
                   "xs19_25b8b96zx253": ("0060009600d5001200d000a00040", 18),
                   "xs19_8u1t2sgz0123": ("?19?051", 18),
                   "xs19_69ligkczw6a4": ("cis-loaf_with_long_nine_and_?-boat", 18),
                   "xs19_31e88gz311dd": ("018c010800e8002b002b0010", 18),
                   "xs19_2lmge93z3201": ("?-hook_on_hook_and_boat", 18),
                   "xs19_696o8zx123cko": ("?19?112", 18),
                   "xs19_255mggkczw346": ("scorpio_and_?-R-bee", 18),
                   "xs19_3pe0okczw1226": ("00c0009800740002001a002b0030", 18),
                   "xs19_39u0o4oz643w1": ("?-hook_siamese_long_hook_and_beehive", 18),
                   "xs19_04a96zca51156": ("trans-boat_with_long_nine_and_?-loaf", 18),
                   "xs19_0mligz32w69a4": ("trans-loaf_with_long_nine_and_?-boat", 18),
                   "xs19_35a8cggozx696": ("?-boat_with_leg_on_beehive_with_tail", 18),
                   "xs19_ggm552sgz1243": ("?-R-bee_with_tail_and_R-loaf", 18),
                   "xs19_259q4ozx12596": ("[[mango siamese superhive siamese loaf]]", 18),
                   "xs19_0g88bqicz3452": ("0060009000a80048000b001a0012000c", 18),
                   "xs19_0c88b96z32156": ("worm_and_?-shillelagh", 18),
                   "xs19_03lk6icz47011": ("008000e30015003400260012000c", 18),
                   "xs19_0259ak8z69d11": ("00c0012201a50029002a00140008", 18),
                   "xs19_g8o6996z1254c": ("?-R-bee_with_tail_on_pond", 18),
                   "xs19_354m88a6zw343": ("00c000a0002600690016001000500060", 18),
                   "xs19_4aab88a6zx352": ("006000500012001500d6005000500020", 18),
                   "xs19_02egm9a4zc8421": ("01800102008e005000360009000a0004", 18),
                   "xs19_0259a4oz651311": ("?-mango_with_bend_tail_siamese_eater", 18),
                   "xs19_0354k8gzokc321": ("ship_with_long_boat_with_?-nine", 18),
                   "xs19_0259a4oz651321": ("00c000a200250069004a00240018", 18),
                   "xs19_352s0gzy0123cko": ("?-ship_on_boat_line_boat", 18),
                   "xs19_2552s0s2552zy11": ("?-binocle_beehives", 18),
                   "xs19_0ggo8a52z122ego": ("?-tub_with_tail_siamese_hat_siamese_eater", 18),
                   "xs19_0dbgz255k4ozx11": ("03000480069000ab00ad0040", 18),
                   "xs19_25a4o0o4a52zy0121": ("?-binocle_barges", 18),
                   "xs19_253gv1qr": ("?-Z_siamese_snake_and_cis-boat_and_block", 19),
                   "xs19_642hv0rr": ("00d800d5001300d000d8", 19),
                   "xs19_259argbr": ("00d600d9000200dc00b0", 19),
                   "xs19_65pabpic": ("006c009a00c1003d0026", 19),
                   "xs19_3pq3ob96": ("00d600b50001006e0068", 19),
                   "xs19_64pb8ob96": ("00cc0149010300fc0024", 19),
                   "xs19_ad1ege1da": ("00c6012900aa01ab0010", 19),
                   "xs19_354cgs2qr": ("?-eater_on_trans-legs_and_block", 19),
                   "xs19_33gv1oka6": ("?-Z_and_long_ship_and_block", 19),
                   "xs19_69egmaz653": ("00c600a9006e00100016000a", 19),
                   "xs19_ml5akoz1ac": ("?-R-bee_siamese_long_boat_and_long_snake", 19),
                   "xs19_178jd0e952": ("03660149012a00ac0040", 19),
                   "xs19_33gv1og853": ("?-Z_and_canoe_and_block", 19),
                   "xs19_2ege1ege13": ("031002ab00aa00aa0044", 19),
                   "xs19_5b8b96z653": ("00c500ab0068000b00090006", 19),
                   "xs19_h7o3ticz11": ("006c002a0025001500560060", 19),
                   "xs19_8u1vg33z23": ("?19?064", 19),
                   "xs19_bdgmicz643": ("00d300b1000e006800480030", 19),
                   "xs19_okiqb8oz66": ("00d800d40012001a000b00080018", 19),
                   "xs19_5b8b9aczx33": ("006c002a0041003f0000000c000c", 19),
                   "xs19_32acz39d1e8": ("alef_and_?-eater", 19),
                   "xs19_31eoz315aa6": ("?-R-bee_on_eater_siamese_eater", 19),
                   "xs19_69ab96z2552": ("00620095005500d200900060", 19),
                   "xs19_g85r8brz121": ("006c00680008006c005200090006", 19),
                   "xs19_gbq2rq23z01": ("?-siamese_tables_and_boat_and_block", 19),
                   "xs19_69b4koz2553": ("0062009500d5002600280018", 19),
                   "xs19_c9b8brzw321": ("?19?111", 19),
                   "xs19_md1qb96z011": ("003600590043003a00090006", 19),
                   "xs19_69ba952z253": ("0062009500d60050009000a00040", 19),
                   "xs19_xcil96z6953": ("00c0012001500090006c000a00090006", 19),
                   "xs19_ci96zwdd1e8": ("010001c0002001a601a90012000c", 19),
                   "xs19_3lkaacz3443": ("00c600a90029005600500030", 19),
                   "xs19_i5t2sga6z11": ("00c000ac002a006900930060", 19),
                   "xs19_8e1ra96z311": ("0068002e0021001b000a00090006", 19),
                   "xs19_3hu0okcz643": ("?-hook_siamese_long_hook_and_?-ship", 19),
                   "xs19_c9baarzw321": ("006c002a0029006b00480018", 19),
                   "xs19_ckgf9zx3553": ("006000a000a9006f00100014000c", 19),
                   "xs19_4aab8oz6996": ("00c4012a012a00cb00080018", 19),
                   "xs19_4a9b8bdzx33": ("006c002a0041007e000000180018", 19),
                   "xs19_wggraarz652": ("?-boat_with_trans-tail_siamese_table_and_table", 19),
                   "xs19_69acz6515ac": ("boat_with_nine_and_?-R-loaf", 19),
                   "xs19_5b8b96zw653": ("00a000d0001300d500960060", 19),
                   "xs19_0gbq1ticz23": ("00c000400056003500050032002c", 19),
                   "xs19_0ca1t6z255d": ("00c00170010b00aa006a0004", 19),
                   "xs19_ogilicz62ac": ("00d80050015201950012000c", 19),
                   "xs19_3pm0mmzw343": ("?-hat_siamese_shillelagh_and_block", 19),
                   "xs19_0mm0uh3z643": ("?-hook_and_long_hook_and_block", 19),
                   "xs19_gbb8b5z1156": ("00a000d0001300d500d4000c", 19),
                   "xs19_ciligozca26": ("018c0152005500d200100018", 19),
                   "xs19_wml5akoz643": ("?19?043", 19),
                   "xs19_0iu0uh3z643": ("long_and_trans-long_hook", 19),
                   "xs19_8ehm4koz643": ("00c8008e00710016000400140018", 19),
                   "xs19_01no3tgz643": ("?-bookends_siamese_eater", 19),
                   "xs19_8o6pb871z23": ("?-G-siamese_trans-legs_on_table", 19),
                   "xs19_o4qabpicz01": ("004000a600bd0041003a000c", 19),
                   "xs19_g88ml3zd543": ("?-G_siamese_trans-legs_on_ship", 19),
                   "xs19_wggs2qrz696": ("?-beehive_with_tail_siamese_trans-legs_and_block", 19),
                   "xs19_0ggm96zraa6": ("?-beehive_with_nine_on_eater", 19),
                   "xs19_6a88bdz2553": ("?-very_long_hook_siamese_snake_and_?-R-bee", 19),
                   "xs19_mkhf0cia4z1": ("?19?104", 19),
                   "xs19_g84q23zd5lo": ("030001000163009500540036", 19),
                   "xs19_gbb88czc953": ("0190012b00ab00680008000c", 19),
                   "xs19_3lkmicz01ac": ("01800158005500d300900060", 19),
                   "xs19_3lmg6qz32011": ("?-shillelagh_siamese_hook_and_ship", 19),
                   "xs19_0354qicz4a53": ("0080014300a50064001a0012000c", 19),
                   "xs19_035s2sgz3543": ("?-great_snake_eater_siamese_worm", 19),
                   "xs19_wggo2ticzc96": ("?-great_snake_eater_and_R-bee_siamese_tub", 19),
                   "xs19_069baa4z4a53": ("racetrack_and_?-long_boat", 19),
                   "xs19_354mgm96zw32": ("[[bookend on beehive_with_nine]]", 19),
                   "xs19_8ehbgf9zw121": ("?-eater_on_beehive_on_table", 19),
                   "xs19_699egoz0354c": ("00c0012c012a00e200130030", 19),
                   "xs19_32akozca22ac": ("dock_and_?-trans-boat_with_tail", 19),
                   "xs19_025iczok4d96": ("03000282008501b2012c00c0", 19),
                   "xs19_08u1fgkcz321": ("00c000a000260069002b00280018", 19),
                   "xs19_69b8b96zw252": ("0060009000d2001500d200900060", 19),
                   "xs19_g04al96zdd11": ("01b001a00024002a001500090006", 19),
                   "xs19_3lkaik8z1243": ("00c400aa00290056004800280010", 19),
                   "xs19_04aab96zc871": ("racetrack_and_?-eater", 19),
                   "xs19_ca952z315ak8": ("barge_with_leg_and_?-R-mango", 19),
                   "xs19_g88brz123ak8": ("0100029b014b006800480030", 19),
                   "xs19_g88b96z11dio": ("?-scorpio_siamese_great_snake_eater", 19),
                   "xs19_06996z311dic": ("beehive_with_long_leg_and_cis-pond", 19),
                   "xs19_069b8ozcid11": ("0180024601a9002b00280018", 19),
                   "xs19_ghn8b96z1023": ("?-hook_on_G", 19),
                   "xs19_ckggm952z4a6": ("trans-loaf_with_long_nine_and_?-boat", 19),
                   "xs19_6t1e8zw11da4": ("00c00170010800e8002b00050002", 19),
                   "xs19_259e0uizx643": ("?-table_siamese_eater_and_R-loaf", 19),
                   "xs19_0gbr0f9z3421": ("?-R-mango_and_table_and_block", 19),
                   "xs19_69baabgzx321": ("0032005e0040003e0001000a000c", 19),
                   "xs19_35acggzcia43": ("loaf_with_trans-tail_on_long_ship", 19),
                   "xs19_069b8oz359a4": ("006000a60129014b00880018", 19),
                   "xs19_8u1t2koz0123": ("00180028002b0069002a00240018", 19),
                   "xs19_gjligkcz1246": ("00300053009500d200100014000c", 19),
                   "xs19_0g88brz8ld11": ("?-siamese_long_hooks_and_boat_and_block", 19),
                   "xs19_259ab96zx253": ("0060009600d50052009000a00040", 19),
                   "xs19_0c88brz259a4": ("01b001a200250029006a0004", 19),
                   "xs19_02lm0eicz643": ("?-eater_and_R-bee_and_boat", 19),
                   "xs19_352sgzciq221": ("03060289010b00e800280010", 19),
                   "xs19_06s1fgkcz321": ("00c000a000260029006b00480018", 19),
                   "xs19_o49b8oz011dd": ("00300048012801ab002b0030", 19),
                   "xs19_w2egm96z6513": ("00c000a00022006e0010001600090006", 19),
                   "xs19_178ba96zw352": ("008000e0001600d5005200900060", 19),
                   "xs19_6t1e8zw115ac": ("0180014000a8002e0021001d0006", 19),
                   "xs19_69mk2sgzx343": ("006000900068002e0041003e0008", 19),
                   "xs19_178b9aczx652": ("008000e0001000d3009500520030", 19),
                   "xs19_8kkm996z6421": ("?19?052", 19),
                   "xs19_ciligoz06aa4": ("006000960155009500120030", 19),
                   "xs19_0gilmz56w696": ("00c0012000d60015001200d000a0", 19),
                   "xs19_2lla8kcz3421": ("?-3some_boat_beehive_loaf", 19),
                   "xs19_woggm96z6aa6": ("beehive_with_long_leg_and_?-cap", 19),
                   "xs19_25a8cz311d96": ("?19?113", 19),
                   "xs19_697o4koz0643": ("?-scorpio_on_R-bee", 19),
                   "xs19_c88bb871zw33": ("00d800580041003f0000000c000c", 19),
                   "xs19_g88b96z19la4": ("?-scorpio_siamese_barge_with_cis-tail", 19),
                   "xs19_gbbo31e8z121": ("?-eater_and_R-loaf_and_block", 19),
                   "xs19_6ac0v1oozx23": ("?-very_long_Z_and_ship_and_block", 19),
                   "xs19_c93ggkcz3543": ("006c00a90083007000100014000c", 19),
                   "xs19_0gjlka52z346": ("006000a0008000780004001a00250032", 19),
                   "xs19_g8p7gs26z123": ("006000a000ac0064001500130030", 19),
                   "xs19_c89f0352z352": ("?-table_siamese_table_and_blocks", 19),
                   "xs19_35a4ozx6b871": ("0180014000a00046003d0001000e0008", 19),
                   "xs19_3p6o6p3zw121": ("006300550014002a002a00140008", 19),
                   "xs19_35a8kicz0653": ("00c000a300550016002800480030", 19),
                   "xs19_0o8gehrz4a43": ("01b0011000e0001c002200350002", 19),
                   "xs19_cic0v1oozx23": ("very_long_Z_and_beehive_and_block", 19),
                   "xs19_39mgmmz321w1": ("006300490036001000160036", 19),
                   "xs19_8e1u06ioz311": ("anvil_and_?-carrier", 19),
                   "xs19_3lk453z1254c": ("dock_and_?-boat_with_cis-tail", 19),
                   "xs19_0c9baa4z2553": ("iron_and_?-R-bee", 19),
                   "xs19_4a9mge2z6243": ("00c4004a008900760010000e0002", 19),
                   "xs19_2lmggz1qq221": ("?-very_long_beehive_and_boat_and_block", 19),
                   "xs19_2lmgmicz0146": ("?19?056", 19),
                   "xs19_0caab96z3213": ("?-R-racetrack_and_snake", 19),
                   "xs19_0gbaqb96z121": ("006400bc0080007c001200050002", 19),
                   "xs19_31egozca22ac": ("dock_and_?-integral", 19),
                   "xs19_0caab8oz6513": ("?-long_Z_siamese_eater_and_hook", 19),
                   "xs19_0ciab96z4a43": ("00c0012001a000ac009200650002", 19),
                   "xs19_4aabaaczw253": ("very_very_long_bee_siamese_eater_and_?-boat", 19),
                   "xs19_wrb079k8z321": ("?-tub_with_leg_and_eater_and_block", 19),
                   "xs19_gill2z1w69ic": ("01800240012200d5001500120030", 19),
                   "xs19_25b8b96zw352": ("0060009000d2001500d600a00040", 19),
                   "xs19_69bo79ozx121": ("003600540044003b0009000a0004", 19),
                   "xs19_4aar0rbzx121": ("?-hat_siamese_hat_and_block", 19),
                   "xs19_3lk69jz32011": ("0064004a0032001400550063", 19),
                   "xs19_354mkk8z4a52": ("01820145004a00d4005000500020", 19),
                   "xs19_025a4z69d553": ("R-racetrack_and_cis-barge", 19),
                   "xs19_69mggka6zw66": ("?-boat_long_line_beehive_and_trans-block", 19),
                   "xs19_069b871z3552": ("G_and_?-R-bee", 19),
                   "xs19_ok4o796z6221": ("?-G_on_R-bee", 19),
                   "xs19_259a4ozcid11": ("0182024501a9002a00240018", 19),
                   "xs19_03pe0eioz321": ("?-hook_siamese_eater_and_?-hook", 19),
                   "xs19_0ogka53zcia6": ("long_boat_with_leg_and_?-R-loaf", 19),
                   "xs19_4aabaaczx352": ("very_very_long_bee_siamese_eater_and_boat", 19),
                   "xs19_2lligkcz01w66": ("very_long_eater_and_beehive_and_block", 19),
                   "xs19_25b88e13zw352": ("00c600a50022003c0000000c00140008", 19),
                   "xs19_025a4z69d1156": ("long_worm_and_cis-barge", 19),
                   "xs19_25a8c8a6zx696": ("?19?116", 19),
                   "xs19_0660u93z25521": ("?-beehive_with_tail_siamese_hook_and_block", 19),
                   "xs19_252s0siczw643": ("004000a2005500150016000800280030", 19),
                   "xs19_0j9mkia4z1221": ("00600090005c0022001900560060", 19),
                   "xs19_2lm0e96z01226": ("?-eater_and_R-bee_and_boat", 19),
                   "xs19_ckg853zx359a4": ("?-cis-shillelagh_on_R-mango", 19),
                   "xs19_02lligzc96w23": ("0180012200d50015001200500060", 19),
                   "xs19_259aczw315ak8": ("?19?090", 19),
                   "xs19_0c84q96z69521": ("00c0012c00a80044003a00090006", 19),
                   "xs19_0g8p78b5z3421": ("?-R-mango_on_loop", 19),
                   "xs19_wgbbo8a6z2521": ("?-barge_with_leg_siamese_eater_and_block", 19),
                   "xs19_0gilmz32w69a4": ("trans-loaf_with_long_nine_and_cis-boat", 19),
                   "xs19_0gjligkcz56w1": ("[[?19?131]]", 19),
                   "xs19_xoge132acz253": ("?-integral_siamese_eater_on_boat", 19),
                   "xs19_2lmgeicz01221": ("?-R-bee_at_R-bee_and_boat", 19),
                   "xs19_4akggm952zw66": ("?-loaf_long_line_tub_and_trans-block", 19),
                   "xs19_04a96z311dik8": ("trans-loaf_with_long_leg_and_?-loaf", 19),
                   "xs19_259mggkczw4a6": ("trans-loaf_with_long_nine_and_ortho-boat", 19),
                   "xs19_0c48a53z4a953": ("boat_with_long_tail_and_?-R-mango", 19),
                   "xs19_0gg0siarz3443": ("?-R-loop_on_pond", 19),
                   "xs19_0o4a952z17853": ("00800140012c00aa0041003e0008", 19),
                   "xs19_178b9a4z02552": ("008000e2001500d5009200500020", 19),
                   "xs19_0oggm952zcia4": ("trans-loaf_with_long_leg_and_?-loaf", 19),
                   "xs19_g8ehlmz11x252": ("004000a0005600150011000e00280030", 19),
                   "xs19_069a4zca51156": ("0180014600a9002a002400a000c0", 19),
                   "xs19_0gill2z32w25a4": ("trans-barge_with_long_nine_and_cis-beehive", 19),
                   "xs19_0ogill2z4aa401": ("?19?096", 19),
                   "xs19_0j9mk4oz342101": ("0060009300490036001400240018", 19),
                   "xs19_259mggzy134aic": ("?-siamese_loaf_with_trans-tails", 19),
                   "xs19_0178c4oz651321": ("00c000a100270068004c00240018", 19),
                   "xs19_0178k4oz4a9611": ("00800141012700c8003400240018", 19),
                   "xs19_035a88gz8kid11": ("?-loaf_binocle_boat", 19),
                   "xs19_69iczxh1t6zx11": ("?-mango_with_trans-nine_siamese_eater", 19),
                   "xs19_31e88gzy0123cko": ("0300028001800060005000280008000e00010003", 19),
                   "xs19_31eg8gzy0123cko": ("?-long_boat_with_trans-nine_on_ship", 19),
                   "xs19_65pabqic": ("0068009e00c1003d0026", 20),
                   "xs19_3pabob96": ("?19?100", 20),
                   "xs19_259ariar": ("00b000dc000200f90096", 20),
                   "xs19_259ar1qr": ("?19?091", 20),
                   "xs19_259araar": ("009600f9000200fc0090", 20),
                   "xs19_4a9r2qj4c": ("0068012e0181007a004c", 20),
                   "xs19_69f0cil96": ("00c60149015500d2000c", 20),
                   "xs19_32qbhu0oo": ("01b401ac0020002f0019", 20),
                   "xs19_69r8brz32": ("006c00680008006c00490033", 20),
                   "xs19_6a8ohf0f9": ("?-long_hook_siamese_eater_and_cis-table", 20),
                   "xs19_69mge1dic": ("008c0152015500950062", 20),
                   "xs19_356o8bqic": ("0188014e00c1003d0026", 20),
                   "xs19_69bq230f9": ("01a600bd0081018e0008", 20),
                   "xs19_3586178br": ("01b301a9002a01c40100", 20),
                   "xs19_39mge1dio": ("018c0152005400950063", 20),
                   "xs19_178br8b52": ("?-cis-boat_with_leg_siamese_trans-legs_and_block", 20),
                   "xs19_4aa40vhar": ("?19?063", 20),
                   "xs19_ci5r8brzw1": ("?-mango_siamese_table_siamese_boat_and_block", 20),
                   "xs19_4a9jz69ll8": ("010002b302a9012a00c4", 20),
                   "xs19_3jgfhoz343": ("?-long_hook_on_R-bee_and_block", 20),
                   "xs19_253gv1oka4": ("01b002a20125002a006c", 20),
                   "xs19_358ge1fgkc": ("03180228012b00a90046", 20),
                   "xs19_iu0e96z69c": ("00d2013e0180000e00090006", 20),
                   "xs19_259e0ehla4": ("018c0252015500d2000c", 20),
                   "xs19_9v079icz32": ("?-table_siamese_snake_and_R-mango", 20),
                   "xs19_gie0ehrz56": ("00d80088007000000070004b000d", 20),
                   "xs19_9v0raa4z23": ("?-table_siamese_table_and_hat", 20),
                   "xs19_ciar1qrzw1": ("0058006e0001006d006a0004", 20),
                   "xs19_69fgkcz653": ("00c600a9006f00100014000c", 20),
                   "xs19_oe1ticz643": ("00d8008e0061001d0012000c", 20),
                   "xs19_259mge1ego": ("031802a400aa00a90046", 20),
                   "xs19_69r2qrz023": ("006c002c0020006f00490030", 20),
                   "xs19_2560uhf033": ("03620355005600500030", 20),
                   "xs19_pf0sicz643": ("00d9008f0060001c0012000c", 20),
                   "xs19_0at1qrz643": ("00d80058008000be00510003", 20),
                   "xs19_4a60uhf0cc": ("00600056035503520030", 20),
                   "xs19_2egu2oge13": ("0300029b008a00aa006c", 20),
                   "xs19_mkiaraa4z1": ("008000e8001e00c100be0008", 20),
                   "xs19_dj8b96z643": ("00cd00930068000b00090006", 20),
                   "xs19_9v0si96z23": ("?-table_siamese_table_and_R-mango", 20),
                   "xs19_69ab96z653": ("00c600a9006a000b00090006", 20),
                   "xs19_cq1raicz23": ("00600020002a006d0041002e0018", 20),
                   "xs19_mmge1dioz1": ("008000e3001500d400d2000c", 20),
                   "xs19_6530fho8a6": ("01b002a30321002e0018", 20),
                   "xs19_bq2r9a4z23": ("0069002f0020006c004800280010", 20),
                   "xs19_3pmzcie033": ("0306026901ae000000180018", 20),
                   "xs19_6248hv0796": ("01b002a302a501280030", 20),
                   "xs19_6960uh32ac": ("011802ae02a101230030", 20),
                   "xs19_330fhu06a4": ("?-siamese_hooks_and_boat_and_block", 20),
                   "xs19_178ka23qic": ("0308013e014100a50046", 20),
                   "xs19_rb88brz023": ("006c0069000b00080068006c", 20),
                   "xs19_253gv164ko": ("?-eater_on_Z_and_boat", 20),
                   "xs19_qmgm952z66": ("cis-loaf_with_long_leg_siamese_snake_and_trans-block", 20),
                   "xs19_2llicz3ego": ("011802ae02a1012300c0", 20),
                   "xs19_cc0si96zbd": ("?19?070", 20),
                   "xs19_3iar2qrzw1": ("?19?094", 20),
                   "xs19_md1u0uiz011": ("0030004b006a002a004b0030", 20),
                   "xs19_xgs2qrzca43": ("01b000b000800070001c000200050003", 20),
                   "xs19_rb88czx3553": ("00d800d000100016003500050006", 20),
                   "xs19_gs2ll2z6943": ("00d0013c0082007500150002", 20),
                   "xs19_25b88brzw33": ("006c00680008000b006b00500020", 20),
                   "xs19_660uh3z3543": ("00c00088007e000100650066", 20),
                   "xs19_c88e1dioz33": ("00c000c0000300f500940012000c", 20),
                   "xs19_8e1raicz311": ("0068002e0021001b000a0012000c", 20),
                   "xs19_2596zbd1156": ("016201a50029002600a000c0", 20),
                   "xs19_ghn8brz1221": ("?-trans-legs_on_R-bee_and_block", 20),
                   "xs19_9fgcik8z643": ("00c9008f0070000c001200140008", 20),
                   "xs19_cillicz06a4": ("006000960155015200900060", 20),
                   "xs19_ckgil96z4a6": ("00c0012001500090001600550062", 20),
                   "xs19_3lkaarz1221": ("006c0028002a001500550062", 20),
                   "xs19_178716862sg": ("06c002ac02aa01120003", 20),
                   "xs19_69mggoz6aa6": ("00c60149015600d000100018", 20),
                   "xs19_0g6t1qrz321": ("?-shillelagh_siamese_boat_with_leg_and_block", 20),
                   "xs19_cq2r96z3421": ("006c009a0042003b00090006", 20),
                   "xs19_raarzw122ac": ("01b000a000a801b4000400050003", 20),
                   "xs19_jhe0eicz146": ("00cc008900730000007000480030", 20),
                   "xs19_69mgm93z321": ("0066004900360010001600090003", 20),
                   "xs19_mp3s4zx3453": ("?-shillelagh_on_worm", 20),
                   "xs19_g6s1ra96z11": ("00c000a8002e0061004d001a", 20),
                   "xs19_69baicz039c": ("00c0012c01a900a300900060", 20),
                   "xs19_0bd0uiz2553": ("?-R-bee_on_table_and_snake", 20),
                   "xs19_69mkkozw6ac": ("?-long_R-bee_siamese_beehive_and_?-ship", 20),
                   "xs19_2lmgma4z346": ("0062009500d600100016000a0004", 20),
                   "xs19_03pmzoka256": ("030002830159005600a000c0", 20),
                   "xs19_cilmzx34a96": ("00c0012001400080007600150012000c", 20),
                   "xs19_mlicz1462ac": ("?-boat_with_bend_tail_siamese_carrier_siamese_hook", 20),
                   "xs19_mlicz1w3596": ("00d801500090006c000a00090006", 20),
                   "xs19_gbq2ra96z01": ("?-table_siamese_loop_and_boat", 20),
                   "xs19_69mgmqzw6a4": ("00c0012000d6001500d200b0", 20),
                   "xs19_g069iczdlp1": ("01b002a0032600290012000c", 20),
                   "xs19_c9b88cz3553": ("006c00a900ab00680008000c", 20),
                   "xs19_cimgdbz6421": ("00d000b0000c006a00490033", 20),
                   "xs19_69b8b52z253": ("0062009500d6001000d000a00040", 20),
                   "xs19_08u1ticz643": ("?-R-bee_with_bend_tail_siamese_long_hook", 20),
                   "xs19_gbair9a4z11": ("00c00098006e0001007a004c", 20),
                   "xs19_ogiu0696z66": ("00d800d00012001e0000000600090006", 20),
                   "xs19_0dr0f96z321": ("?-hook_siamese_snake_and_cap", 20),
                   "xs19_ckjaik8z643": ("00cc00940073000a001200140008", 20),
                   "xs19_69iczw8ll96": ("01800240012200d500150012000c", 20),
                   "xs19_3pm0mqzw343": ("?-shillelagh_siamese_hat_siamese_snake", 20),
                   "xs19_9f0v1oozw23": ("?-very_long_Z_and_table_and_block", 20),
                   "xs19_0j96z345d96": ("00c0012001a600a900930060", 20),
                   "xs19_c9b871z35a4": ("010001c0002201a5012a006c", 20),
                   "xs19_ca9n871z311": ("006c002a00290017000800070001", 20),
                   "xs19_gbaar9a4z11": ("00c00088007e0001007a004c", 20),
                   "xs19_raarzx12552": ("00d80050005000dc0002000500050002", 20),
                   "xs19_3lk453z4a9o": ("030402aa00b2008302800300", 20),
                   "xs19_6s1v0796zw1": ("iron_and_?-R-bee", 20),
                   "xs19_g886p3zdl91": ("030002600190005200550036", 20),
                   "xs19_35iczxdd1e8": ("018001400090006b000b000800070001", 20),
                   "xs19_3pmkia4z066": ("00c0009b006b0028004800500020", 20),
                   "xs19_69baacz3213": ("R-racetrack_and_?-snake", 20),
                   "xs19_9f0v9zx1256": ("?-boat_with_leg_siamese_table_and_cis-table", 20),
                   "xs19_0cq1ticz643": ("00c0008c007a0001001d0012000c", 20),
                   "xs19_0ml5a8ozc96": ("0180013600d50005000a00080018", 20),
                   "xs19_cilligozx66": ("0030004800a800ab004b00080018", 20),
                   "xs19_321343hu066": ("05b006ab004b00080018", 20),
                   "xs19_3pmkkozw4ac": ("0180013000d2005500530030", 20),
                   "xs19_ca9b8oz3156": ("006c002a00a900cb00080018", 20),
                   "xs19_35aczcid113": ("03060289015600d000100018", 20),
                   "xs19_354c8716853": ("066304a102ae0118", 20),
                   "xs19_c9baacz0653": ("R-iron_and_cis-ship", 20),
                   "xs19_g88b96zd596": ("01b000a8012800cb00090006", 20),
                   "xs19_gbaqb871z11": ("00d2005e0040003e00090003", 20),
                   "xs19_g0t3objoz11": ("00c000ab002d002000160036", 20),
                   "xs19_8o6ht2sgz23": ("00c00040005b00ca002a00240018", 20),
                   "xs19_8kiqj96z066": ("0060009000c80058004b002b0010", 20),
                   "xs19_g84q23zdll8": ("[[R-loaf_with_tail and R-bee]]", 20),
                   "xs19_32qbhe8zx65": ("?-eater_siamese_table_on_shillelagh", 20),
                   "xs19_6a8oge132ac": ("?-integral_siamese_eaters", 20),
                   "xs19_03lkm96z652": ("00c000a300550014001600090006", 20),
                   "xs19_rb88czx35ac": ("?-Z_and_long_ship_and_block", 20),
                   "xs19_3lkcz3462ac": ("018c01520056006400050003", 20),
                   "xs19_gbq2ria4z11": ("00c000ac006a0001007e0048", 20),
                   "xs19_3p6gmiczw56": ("00c000980065000b006800480030", 20),
                   "xs19_g4qabpicz11": ("00c000a6003d0041003a000c", 20),
                   "xs19_3lmgdbz1221": ("?-R-bee_on_snake_and_ship", 20),
                   "xs19_bq2r96z1221": ("006a002d0021006e00480030", 20),
                   "xs19_69mgm96z321": ("0066004900360010001600090006", 20),
                   "xs19_ml1u0uiz101": ("0050006b000a006a004b0030", 20),
                   "xs19_3lkaik8z643": ("00c300a9002e0050004800280010", 20),
                   "xs19_39u0okcz643": ("00c30091007e0000001800280030", 20),
                   "xs19_3pmgma4zx66": ("00c000980068000b006b00500020", 20),
                   "xs19_0db871z6953": ("?-R-loop_and_R-loaf", 20),
                   "xs19_03lkm96z643": ("?-beehive_with_tail_siamese_eater_siamese_hook", 20),
                   "xs19_0h7objoz321": ("0060005100270018000b00130018", 20),
                   "xs19_ca9f033z352": ("?-loaf_siamese_tables_and_boat_and_block", 20),
                   "xs19_gba9ria4z11": ("00c0008c007a0001006e0058", 20),
                   "xs19_gbb8ria4z11": ("00c0008c007a0001006e0068", 20),
                   "xs19_2596z39d552": ("iron_and_cis-loaf", 20),
                   "xs19_0cp3qicz643": ("00c0008c00790003001a0012000c", 20),
                   "xs19_39mgm96z321": ("0063004900360010001600090006", 20),
                   "xs19_gbaik8zd54c": ("01b000ab008a019200140008", 20),
                   "xs19_2llmz122696": ("?-long_bee_siamese_beehive_and_?-R-bee", 20),
                   "xs19_0rb0796z643": ("?-shillelagh_and_R-bee_and_block", 20),
                   "xs19_35akgozcia6": ("long_boat_with_leg_and_ortho-R-loaf", 20),
                   "xs19_0mm0e93zc96": ("?-shillelagh_and_hook_and_block", 20),
                   "xs19_69b4koz6513": ("00c600a9002b006400140018", 20),
                   "xs19_ca9f0ccz352": ("006c00aa0049000f0000000c000c", 20),
                   "xs19_02llicz69ic": ("00c00122025501950012000c", 20),
                   "xs19_1784213ob96": ("063602550281010e0008", 20),
                   "xs19_651ug8oz653": ("00c600a50061001e001000080018", 20),
                   "xs19_mm0e952z1ac": ("?-R-loaf_and_long_snake_and_block", 20),
                   "xs19_4a9b871z653": ("00c400aa0069000b000800070001", 20),
                   "xs19_mmge1eg8oz1": ("010001c5002b01a801a80010", 20),
                   "xs19_0g88bdzrq23": ("0360035000480068000b000d", 20),
                   "xs19_ci53zw1qb96": ("00c001200290030b001a0012000c", 20),
                   "xs19_08o0uharz65": ("00d80050008800780000001800150003", 20),
                   "xs19_0696z39d596": ("00c0012000a601a901260060", 20),
                   "xs19_69ab9aczx33": ("003000480028006b004b00280018", 20),
                   "xs19_4s0f96z354c": ("00c0012001e30002007a004c", 20),
                   "xs19_gbbgf1e8z11": ("00c00090006b000a006a006c", 20),
                   "xs19_69ab96z0356": ("00600096005500d300900060", 20),
                   "xs19_4a9b8oz6996": ("00c4012a012900cb00080018", 20),
                   "xs19_4aab9cz6513": ("iron_and_?-hook", 20),
                   "xs19_3iabp46z321": ("?-boat_with_leg_on_carrier_siamese_table", 20),
                   "xs19_8k4mp3z3543": ("00c00098006e0021002d0016", 20),
                   "xs19_mkkl3z1w69c": ("0180012300d5001400140036", 20),
                   "xs19_3lkmz12269c": ("01880154005400d600090003", 20),
                   "xs19_69abaaczx33": ("?19?118", 20),
                   "xs19_mk2qb96z121": ("003600540022001a000b00090006", 20),
                   "xs19_mkhf0cik8z1": ("010001c6002901aa01240060", 20),
                   "xs19_696o6hrzw23": ("?19?122", 20),
                   "xs19_0mm0uh3z1243": ("00c00088007800060069006a0004", 20),
                   "xs19_0j5cik8z3453": ("0060009300a5006c001200140008", 20),
                   "xs19_0gj1uge2z643": ("?-eater_siamese_long_eater_and_hook", 20),
                   "xs19_35is0cczw69c": ("0180014000960079000300600060", 20),
                   "xs19_0j9mgmaz3421": ("006000930049003600100016000a", 20),
                   "xs19_0ogil96z4aic": ("cis-loaf_with_long_leg_and_?-loaf", 20),
                   "xs19_08u1jgz4ab43": ("00800148017e008100730010", 20),
                   "xs19_069b8ozoid11": ("0300024601a9002b00280018", 20),
                   "xs19_31egmicz2521": ("00c200850072000c006800480030", 20),
                   "xs19_03lkmicz4701": ("008000e30015003400160012000c", 20),
                   "xs19_314u0ooz3543": ("00c600850021007e000000180018", 20),
                   "xs19_697o7p8zx121": ("003600540054002b000a000a0004", 20),
                   "xs19_ckl3z0470653": ("006000a000c0000300f50094000c", 20),
                   "xs19_gg0s2qrz2543": ("00d800580040003e0001000d000a", 20),
                   "xs19_g8kkmp3z1226": ("00c000980068002b002a0012000c", 20),
                   "xs19_256o696zw39c": ("00c0012000c3003900cc01400080", 20),
                   "xs19_8o6llicz1221": ("00300048002e0061001d0012000c", 20),
                   "xs19_035s2koz3543": ("006000a30085007c000200140018", 20),
                   "xs19_696k4ozca511": ("0186014900a6003400240018", 20),
                   "xs19_6970brz06421": ("?-block_and_R-bee_and_canoe", 20),
                   "xs19_032acz69d552": ("00c0012301a200aa00ac0040", 20),
                   "xs19_69a4z65131e8": ("010001c000200064002a00a900c6", 20),
                   "xs19_0mkhf0ca4z32": ("0180010000e0001600d500920030", 20),
                   "xs19_0jhkmz346065": ("00a000d6001400d100930060", 20),
                   "xs19_04s0si96z39c": ("00c0012000900070000000730049000c", 20),
                   "xs19_0cq1fgkcz321": ("00c000a000260069004b00280018", 20),
                   "xs19_354kmicz0643": ("00c000a30021002e006800480030", 20),
                   "xs19_08o1vg33z643": ("00d800d0001000160034000400050003", 20),
                   "xs19_178c8a6z4a53": ("010201c5002a006c002000a000c0", 20),
                   "xs19_3lkm9a4z1221": ("?-loaf_siamese_hook_on_R-bee", 20),
                   "xs19_9v0s2mz23w11": ("?-table_siamese_table_and_C", 20),
                   "xs19_2lla8a6z1243": ("006000500010005600a900aa0044", 20),
                   "xs19_g8o652z1qaa6": ("0100028c018a006a004b0030", 20),
                   "xs19_xqm0e952z253": ("01800258015000c80018000600050002", 20),
                   "xs19_02596z69l913": ("00c0012202a5012900260060", 20),
                   "xs19_0g31eozold11": ("?-long_hook_siamese_eater_and_?-ship", 20),
                   "xs19_0cq1f871z321": ("00d8005400520036000400050003", 20),
                   "xs19_ca9n8426z065": ("006000400020001000e8009500530030", 20),
                   "xs19_0cil56zoge21": ("0300020c01d2005500250006", 20),
                   "xs19_02llmzc96221": ("0180012200d5005500560020", 20),
                   "xs19_03pmkk8z6226": ("?-long_bee_siamese_shillelagh_and_table", 20),
                   "xs19_031e8gz65lp1": ("00c000a302a1032e00280010", 20),
                   "xs19_ciabgzx178a6": ("00c00140010000f0002b000a0012000c", 20),
                   "xs19_8kkl30fhozx1": ("00d80050004e0141018e0008", 20),
                   "xs19_4a9e0drzx311": ("006c005a0002003b004800280010", 20),
                   "xs19_0o8b96zok453": ("03000298008800ab00690006", 20),
                   "xs19_0jhkmz346243": ("00600096005400d100930060", 20),
                   "xs19_8ehbaaczw123": ("0018002e0021006f00100014000c", 20),
                   "xs19_354kl3zca221": ("dock_and_?-integral", 20),
                   "xs19_iu06996z1226": ("00600090009000630002007a004c", 20),
                   "xs19_0at1eozc4521": ("0180008a00bd0041002e0018", 20),
                   "xs19_bdgmmzw12452": ("?-R-mango_on_snake_and_block", 20),
                   "xs19_39u06996z032": ("?-hook_siamese_snake_and_trans-pond", 20),
                   "xs19_4a96z6511da4": ("cis-boat_with_long_nine_and_?-loaf", 20),
                   "xs19_cil9abgzx311": ("?19?093", 20),
                   "xs19_660u1acz6511": ("00c600a60020003e0001000a000c", 20),
                   "xs19_31e88gzcil91": ("0306020901d5005200500020", 20),
                   "xs19_8e1mkk8z3521": ("006800ae00410036001400140008", 20),
                   "xs19_25acz3115ako": ("long_boat_with_long_leg_and_?-long_leg", 20),
                   "xs19_0gilmz1248ar": ("036001560115009200500020", 20),
                   "xs19_c4o0ep3z6521": ("00cc00a400580020000e00190003", 20),
                   "xs19_ca9baiczw321": ("0018002e0041007d000200140018", 20),
                   "xs19_0g9fgkcz3453": ("0060009000a9006f00100014000c", 20),
                   "xs19_4aar4kozx643": ("00200050005000db0021002e0018", 20),
                   "xs19_w9v0cicz6521": ("00c000a0005000120035001500120030", 20),
                   "xs19_xggrb8oz4a96": ("?-loaf_with_trans-tail_siamese_table_and_block", 20),
                   "xs19_0at1u8zc4521": ("0180008a00bd0041003e0008", 20),
                   "xs19_gjlkia4z1w66": ("0030002600190002007c0040000c000c", 20),
                   "xs19_032qb96z6521": ("00c000a30042003a000b00090006", 20),
                   "xs19_2l2s0sicz321": ("boat_line_tub_and_?-R-bee", 20),
                   "xs19_6996o8z69521": ("?-loaf_with_trans-tail_on_pond", 20),
                   "xs19_0c9baa4z6513": ("00c000ac0029006b000a000a0004", 20),
                   "xs19_2560uicz0653": ("004000a300650006007800480030", 20),
                   "xs19_0660uh3z4a53": ("?-long_boat_siamese_long_hook_and_block", 20),
                   "xs19_031e8z69d552": ("racetrack_and_?-eater", 20),
                   "xs19_2lmggz32w6jo": ("0300026000d00010001600550062", 20),
                   "xs19_69a4ozx6b853": ("00c0012000a00046003d0001000a000c", 20),
                   "xs19_3pc0sicz0643": ("00c0009b00310006003800480030", 20),
                   "xs19_354mhm853zx1": ("0193012900ea000400380020", 20),
                   "xs19_31egmik8zx66": ("00c000ac002a0021001e000000180018", 20),
                   "xs19_04aab96z4a53": ("racetrack_and_?-long_boat", 20),
                   "xs19_6a8ciarz0311": ("006c00280024001a000a002b0030", 20),
                   "xs19_ckggka53z4a6": ("long_boat_with_long_niene_and_?-boat", 20),
                   "xs19_0gjlmz32w696": ("00c0012000d60015001300500060", 20),
                   "xs19_25a8a6z315ac": ("tub_with_nine_and_?-boat_with_leg", 20),
                   "xs19_g6t1u8z11x56": ("00c000a8001e0001001d00260030", 20),
                   "xs19_0642arzoid11": ("036001500110009601890003", 20),
                   "xs19_ggc2ticz2543": ("005000b0008c0062001d0012000c", 20),
                   "xs19_6a88m96z6511": ("krake_at_beehive", 20),
                   "xs19_354mioz069a4": ("?-loaf_with_cis-tail_siamese_carrier_siamese_hook", 20),
                   "xs19_rh6o8zx34aa4": ("01b0011000c0003c0022000500050002", 20),
                   "xs19_04aab96z8e13": ("010001c4002a006a000b00090006", 20),
                   "xs19_w6t1egoz3521": ("006000a00046003d0001000e00100018", 20),
                   "xs19_069a4ozcil91": ("0180024602a9012a00240018", 20),
                   "xs19_0bt0eik8z321": ("00c000a000260069002a004c0060", 20),
                   "xs19_4aabgzx32qic": ("0180024003400050006b000a000a0004", 20),
                   "xs19_69ab88a6zx33": ("005000b30081007e000000180018", 20),
                   "xs19_32aczw319lic": ("cis-loaf_with_long_leg_and_?-eater", 20),
                   "xs19_04aabgz4a95d": ("00800144012a00aa01ab0010", 20),
                   "xs19_g88ci96zdd11": ("?-long_R-bee_siamese_mango_and_trans-block", 20),
                   "xs19_w69mge2z2553": ("006000900070000c0012002a002b0010", 20),
                   "xs19_2egm996zx346": ("006000930091006e000800700040", 20),
                   "xs19_g84q23z1pl4c": ("030001060164009500530030", 20),
                   "xs19_0c82ticz2553": ("004000ac00a80062001d0012000c", 20),
                   "xs19_gjlicz1w62ac": ("01800140004c00d2001500130030", 20),
                   "xs19_ci4oge13z643": ("00cc0092006400180010000e00010003", 20),
                   "xs19_ca52gz311dl8": ("?-Z_and_long_boat_and_boat", 20),
                   "xs19_03lk64koz643": ("?-eater_siamese_hook_and_eater", 20),
                   "xs19_g08ka52zdll8": ("01b002a002a80114000a00050002", 20),
                   "xs19_32acz311dik8": ("03180110015000d6000900050002", 20),
                   "xs19_25is0f9zx346": ("009000f30001003e004800a00040", 20),
                   "xs19_0ol3zc870696": ("?-long_hook_siamese_long_snake_and_beehive", 20),
                   "xs19_3lkiak8z1243": ("00c400aa0029004e005000280010", 20),
                   "xs19_259mggmazx66": ("0060009300520021001e000000180018", 20),
                   "xs19_3hu0og4cz643": ("?-long_hook_siamese_hook_and_snake", 20),
                   "xs19_04allicz6521": ("00c000a4004a003500150012000c", 20),
                   "xs19_8kimge13z066": ("00c000ac002a0021001e000000060006", 20),
                   "xs19_wggmd1e8z696": ("00c0012000d000100016000d0001000e0008", 20),
                   "xs19_3iaba96z0123": ("006000260029006b002800480030", 20),
                   "xs19_0g8jq23z6b8o": ("?-eater_siamese_snake_eater_and_table", 20),
                   "xs19_354kozwcc0f9": ("?-integral_on_table_and_block", 20),
                   "xs19_0c82ticz6513": ("00c000ac00280062001d0012000c", 20),
                   "xs19_0okk871zcia6": ("02000380004000ac00aa00690006", 20),
                   "xs19_wkq23ckoz643": ("?-eater_siamese_snake_eater_on_ship", 20),
                   "xs19_178c4ozcid11": ("02060389005600d000900060", 20),
                   "xs19_032acz255d96": ("racetrack_and_?-eater", 20),
                   "xs19_0c9jz66078a6": ("00c00140010000f3000900cc00c0", 20),
                   "xs19_32ar4koz0643": ("00c00043005100de002000280018", 20),
                   "xs19_db0ggkcz3543": ("00b600d50001000e000800280030", 20),
                   "xs19_035icz66079c": ("?-boat_with_long_tail_siamese_hook_and_block", 20),
                   "xs19_25b8b96z0253": ("0060009000d0001600d500a20040", 20),
                   "xs19_wmkk871z69a4": ("010001c000200050005200d500090006", 20),
                   "xs19_259mkk8z6521": ("?-loaf_siamese_long_R-bee_on_boat", 20),
                   "xs19_xmm0e93z4a43": ("?-tub_with_tail_and_hook_and_block", 20),
                   "xs19_0c9bkk8z2553": ("004000ac00a9006b001400140008", 20),
                   "xs19_6970v9z02521": ("?-tub_with_tail_siamese_table_and_R-bee", 20),
                   "xs19_06a8a53z3596": ("0180014000a0002600a900ca000c", 20),
                   "xs19_gbbo312koz11": ("0180012300e1000200d400d8", 20),
                   "xs19_0ggml2z346kp": ("010002b301a5002c00240018", 20),
                   "xs19_gbb8b52z1252": ("004000a000d0001200d500d2000c", 20),
                   "xs19_02llmz696221": ("00c0012200d5005500560020", 20),
                   "xs19_5b88b96zw256": ("00a000d00012001500d300900060", 20),
                   "xs19_xggs2qrz4a52": ("01b000b00080007000100014000a00050002", 20),
                   "xs19_0c9jz6a87066": ("00c0014c010900f3000000c000c0", 20),
                   "xs19_wggo3qicz696": ("00c0012000d0001000180003001a0012000c", 20),
                   "xs19_0mligoz342ac": ("006000960055015201900018", 20),
                   "xs19_259ab96zw352": ("0060009000d20055009600a00040", 20),
                   "xs19_oggo8brzw6a4": ("01b001a000220035001600100030", 20),
                   "xs19_c88e1egoz352": ("006c00a80048000e0001000e00100018", 20),
                   "xs19_0md1eoz34311": ("00600096006d0021002e0018", 20),
                   "xs19_mljgoz104aa4": ("?-Z_and_beehive_and_ship", 20),
                   "xs19_62sggm93zw66": ("00c000a300250044003c0000000c000c", 20),
                   "xs19_xmm0e96z4a43": ("?-tub_with_tail_and_R-bee_and_block", 20),
                   "xs19_39u0oka6z023": ("long_and_cis-long_ship", 20),
                   "xs19_0okkm96z4aa4": ("?-long_R-bee_siamese_bee_and_trans-beehive", 20),
                   "xs19_xohf0cicz253": ("01000280018000620055001500120030", 20),
                   "xs19_39mkkoz04aa4": ("0180012200d5005500520030", 20),
                   "xs19_2l2s0si6z321": ("?-boat_line_tub_and_hook", 20),
                   "xs19_6a88bq23z033": ("?-very_long_eater_and_table_and_block", 20),
                   "xs19_02596z255d93": ("iron_and_?-loaf", 20),
                   "xs19_25ak8zciq226": ("worm_and_cis-long_barge", 20),
                   "xs19_259abgzc8711": ("0182010500e9002a002b0010", 20),
                   "xs19_259e0oozw3lo": ("?-R-loaf_and_long_snake_and_block", 20),
                   "xs19_31eo0oozw6jo": ("?-eater_siamese_table_siamese_carrier_and_block", 20),
                   "xs19_06996z311dio": ("0300024601a9002900260060", 20),
                   "xs19_c8a53z315ak8": ("01000283014500aa0028006c", 20),
                   "xs19_3jgf9a4z1221": ("006c006a0009000e003000480030", 20),
                   "xs19_39mkkmz321w1": ("006300490036001400140036", 20),
                   "xs19_2eg6lliczx11": ("0030004b00ba008200740018", 20),
                   "xs19_03jgf96z2521": ("?-long_boat_on_cap_and_block", 20),
                   "xs19_354koz66078c": ("018601460040005e00310003", 20),
                   "xs19_3lo0okcz3443": ("?-pond_siamese_long_snake_on_ship", 20),
                   "xs19_31e8gzwamhe2": ("0300020001ca004d0031000e0008", 20),
                   "xs19_330fp2sgzw32": ("00d800d40012001a000b00200030", 20),
                   "xs19_8o0e9jzc9611": ("?19?128", 20),
                   "xs19_64k6pb8oz0121": ("00300029000f00f00094000a0004", 20),
                   "xs19_0gjlkia4z1226": ("0030002600190002007c008000700010", 20),
                   "xs19_3pczg8l596z01": ("060204c501aa002800240018", 20),
                   "xs19_0mk2qbgz643w1": ("?-bookend_and_hook_and_boat", 20),
                   "xs19_xmliczg0t6z11": ("0600040003a000d600150012000c", 20),
                   "xs19_039u0ok8z4a43": ("008001430089007e0000001800140008", 20),
                   "xs19_330fhik8zw321": ("?19?075", 20),
                   "xs19_wcimge13z2521": ("01800158005400440038000a00050002", 20),
                   "xs19_6akggka52zw66": ("?-boat_long_line_barge_and_block", 20),
                   "xs19_ckgog853z4aa4": ("?-canoe_siamese_hook_and_beehive", 20),
                   "xs19_2lligka4z3201": ("00c00090007c0002006500920060", 20),
                   "xs19_03lkiacz25421": ("[[R-mango on long integral]]", 20),
                   "xs19_2560u93z06521": ("?-boat_with_cis-tail_siamese_hook_and_boat", 20),
                   "xs19_35a4ozx3215ac": ("0180014000a000500010002c003200050003", 20),
                   "xs19_354kmzx123ck8": ("03000280008000b001a80018000600050002", 20),
                   "xs19_x39u0ooz4a511": ("?-tub_with_nine_and_cis-hook_and_cis-block", 20),
                   "xs19_25is0ciczx346": ("?-tub_with_leg_siamese_eater_and_beehive", 20),
                   "xs19_4akggm96zw6a4": ("beehive_long_line_tub_and_?-boat", 20),
                   "xs19_178baicz06421": ("008000e3001100d2005400480030", 20),
                   "xs19_32akozwca22ac": ("01800140004000580154018a00020003", 20),
                   "xs19_35a84koz06513": ("00c000a300550014002600280018", 20),
                   "xs19_31egogkczx6a4": ("?-integral_siamese_hook_and_boat", 20),
                   "xs19_0gj1uge2z1243": ("0040007000080078008600c9000a0004", 20),
                   "xs19_0gg2uge13z643": ("01800158005000500036000400050003", 20),
                   "xs19_0o4a952z35871": ("00800140012800ae0041003a000c", 20),
                   "xs19_4a9eg62sgzx32": ("004000ac012a00e2001300200030", 20),
                   "xs19_ck0og853z178c": ("?-eater_siamese_snake_and_canoe", 20),
                   "xs19_ggka231ege2z1": ("04000704008a010a00eb0030", 20),
                   "xs19_62s0si52z0643": ("006000500010002c002800aa00c50002", 20),
                   "xs19_25ak8gzciq221": ("?19?117", 20),
                   "xs19_0g88m952z345d": ("00800140012000d0002b002a0012000c", 20),
                   "xs19_64kmhacz03421": ("006000260029006a008c00500030", 20),
                   "xs19_69a4ozw4ab413": ("00c0012000a20045003d00020008000c", 20),
                   "xs19_06ak8a53z6521": ("00c000a6004a00340008000a00050003", 20),
                   "xs19_wcc0si52zc871": ("0180014000400060000c0068006a00050002", 20),
                   "xs19_178c88a6zx696": ("?-long_hook_siamese_eater_and_beehive", 20),
                   "xs19_025acz65115ac": ("trans-boat_with_long_nine_and_?-long_boat", 20),
                   "xs19_651u0ok8zw643": ("?19?127", 20),
                   "xs19_0c871z65115ac": ("trans-boat_with_long_nine_and_?-eater", 20),
                   "xs19_354k6p56zw121": ("00c60089007b0004001400280010", 20),
                   "xs19_259akgkczw643": ("?-elevener_on_mango", 20),
                   "xs19_c4oggm96z0346": ("?-beehive_with_long_leg_siamese_long_integral", 20),
                   "xs19_35acgcia4zx23": ("0180014600a9006a001400100030", 20),
                   "xs19_312kmik8zw346": ("00c000ac001a0001001e002000280018", 20),
                   "xs19_0oo0ep3zca221": ("0180015800580040002e00190003", 20),
                   "xs19_0g08ka23z8lld": ("?-tub_with_tail_and_leg_and_?-R-bee", 20),
                   "xs19_64kbaik8z0321": ("006000500026001900e2009c0010", 20),
                   "xs19_0g8ehu0ooz321": ("01800140009b006b002800280010", 20),
                   "xs19_3hu0696z01226": ("00c0008c007a0002006300900060", 20),
                   "xs19_0gjloz32w2596": ("00c0012000a000580015001300500060", 20),
                   "xs19_06a8a52z4a953": ("tub_with_nine_and_trans-R-mango", 20),
                   "xs19_g88m596z1254c": ("00c00120014300d2002a00240018", 20),
                   "xs19_652s0cicz2521": ("?-boat_long_line_tub_and_beehive", 20),
                   "xs19_0g8ehu066z321": ("0180014000980068002b002b0010", 20),
                   "xs19_0gbb8o653z121": ("?-tub_with_long_leg_on_ship_and_block", 20),
                   "xs19_256o6952zw643": ("0062009500560028000800100014000c", 20),
                   "xs19_xj1u0ooz4a611": ("0080014000c000330021001e000000180018", 20),
                   "xs19_259eg8oz0ca43": ("?-boat_with_trans-nine_on_R-loaf", 20),
                   "xs19_0oo0u93zca221": ("0180015800580040003e00090003", 20),
                   "xs19_069eg8oz4aa43": ("008001460149008e007000080018", 20),
                   "xs19_xj1u066z4a521": ("long_barge_with_long_nine_and_trans-block", 20),
                   "xs19_31eo0okcz0643": ("00c000a0002300350016001000500060", 20),
                   "xs19_x8o0ehrz8e121": ("01b0011000e0000000380024000800070001", 20),
                   "xs19_4acggm96z0643": ("?-beehive_with_tail_siamese_eater_on_boat", 20),
                   "xs19_32ak8gzciq221": ("03060109014b00a800480030", 20),
                   "xs19_259q48a6z2521": ("00600093004900360010005000a00040", 20),
                   "xs19_25a88b96zx256": ("006200a50082007c0000001000280030", 20),
                   "xs19_09v0s4oz643w1": ("?-long_hook_siamese_table_and_R_bee", 20),
                   "xs19_069a4zc871156": ("0180010600e9002a002400a000c0", 20),
                   "xs19_31248gz4a95lo": ("031002a800a4012201410083", 20),
                   "xs19_8eh7o4czw1243": ("00300026001900e2008c00700010", 20),
                   "xs19_0gamgm96z3421": ("0060009000680008006c005200090006", 20),
                   "xs19_259akgoz02596": ("00800144012a00a9005600100030", 20),
                   "xs19_04a96z4ad1156": ("00c000a00026002901aa01440080", 20),
                   "xs19_0g0t3ob96z121": ("00d80150010800e8002a00050002", 20),
                   "xs19_0g08k871z8lld": ("02000380004000a00056001500350002", 20),
                   "xs19_069acz8e13146": ("010001c60029006a002c008000c0", 20),
                   "xs19_25b88a53zx253": ("?-boat_long_line_boat_and_boat", 20),
                   "xs19_0ggm952z1qaa4": ("01000280024401aa002a002b0010", 20),
                   "xs19_0mljgz32w25a4": ("trans-barge_with_long_nine_and_?-ship", 20),
                   "xs19_069a4z311d552": ("00600026002901aa00a400a00040", 20),
                   "xs19_4aab94ozw6511": ("00200050005300d5009400240018", 20),
                   "xs19_4a96kk8z03543": ("0020005600950061002e00280010", 20),
                   "xs19_35a8cicz06511": ("00c000a300550014003400480030", 20),
                   "xs19_641v0cicz0321": ("?-very_very_long_hook_siamese_carrier_and_beehive", 20),
                   "xs19_6ao4o7hz32x11": ("0066004a00180004001800270031", 20),
                   "xs19_3lkkoz01w2596": ("01800158005000500034000a00090006", 20),
                   "xs19_wj5og853z2543": ("018c0104008800500034000a00090006", 20),
                   "xs19_0ci5pa4z25521": ("004000ac00b200450039000a0004", 20),
                   "xs19_178c2sgz02553": ("008000e200150035004600380008", 20),
                   "xs19_025acz8kid113": ("?19?014", 20),
                   "xs19_6icgf9gz23x11": ("?19?068", 20),
                   "xs19_0ca52z65115ac": ("?19?119", 20),
                   "xs19_0178c4ozca2311": ("0180014100470068002c00240018", 20),
                   "xs19_25is0g8ozw6943": ("00800140009600790002001c00200030", 20),
                   "xs19_04a96z4a5115a4": ("tub_long_line_tub_and_?-loaf", 20),
                   "xs19_0ggm552sgz3421": ("00800140012000e30002003a00240018", 20),
                   "xs19_0256o8zc970123": ("?-hook_on_boat_and_hook", 20),
                   "xs19_069a4oz4a97011": ("?-loaf_with_trans-tail_and_R-loaf", 20),
                   "xs19_32q48gzx11dia4": ("0300010001600090005000360009000a0004", 20),
                   "xs19_0ggo8hf0ck8z32": ("0600040003a200d5001600100030", 20),
                   "xs19_08u1t6gz32x121": ("00c20085002a0068002c00240018", 20),
                   "xs19_o4s3pcz01x1246": ("?-canoe_siamese_carrier_on_R-bee", 20),
                   "xs19_g88b96z8ljgzx1": ("03000480068300b200aa0044", 20),
                   "xs19_069b88gz624871": ("00c000460089010b00e800280010", 20),
                   "xs19_031e88gz259d11": ("004000a3012101ae002800280010", 20),
                   "xs19_wcc0s252zc8711": ("018001400040007000080068006a00050002", 20),
                   "xs19_256o8gzx643ak8": ("010002800180006c00440038000a00050002", 20),
                   "xs19_39e0o4oz04a611": ("0180012200e50006003800480030", 20),
                   "xs19_g08o652z11dkk8": ("?-hook_on_boat_and_?-R-bee", 20),
                   "xs19_4s0c9jzw113452": ("00600090005c0022001a000b00200030", 20),
                   "xs19_259mggzy123cko": ("loaf_with_trans-nine_on_ship", 20),
                   "xs19_25a8k8zw358gkc": ("018002800208011400a8006a00050002", 20),
                   "xs19_g88e1dmz11y156": ("0180010000830041002e006800480030", 20),
                   "xs19_31248gzxol54ko": ("03000280008000b002a80304000200010003", 20),
                   "xs19_0ok213zciarzw1": ("060004000236015500d2000c", 20),
                   "xs19_wggo8hf033z252": ("06c00680008000b0005c000200050002", 20),
                   "xs19_031e88gz8kid11": ("?19?060", 20),
                   "xs19_0g8k46164koz321": ("060005000283010100ee00280010", 20),
                   "xs19_25acggzy0123cko": ("long_boat_on_ship_on_ship", 20),
                   "xs19_256o8gzy0230eio": ("boat_on_hook_and_meta-hook", 20),
                   "xs19_2552s0s25a4zy11": ("?-binocle_beehive_barge", 20),
                   "xs19_25a8c48gzwc8711": ("0080014000a30021006e004800280010", 20),
                   "xs19_xgbaa4zg6p21z11": ("060004c003200050002b000a000a0004", 20),
                   "xs19_3542s0s2453zy11": ("060304890356005000500020", 20),
                   "xs19_25b88gzy0123cko": ("?-ship_on_boat_line_boat", 20),
                   "xs19_255mggzx1023ck8": ("eater_on_boat_and_?-R-bee", 20),
                   "xs19_0j5oz345k4ozx11": ("03000480069800a500930060", 20),
                   "xs19_2552s0s2453zy11": ("060604890356005000500020", 20),
                   "xs19_069mggzg8ka221z01": ("0200050602890156005000500020", 20),
                   "xs20_3lkkl3z32w23": ("mirrored dock", 3),
                   "xs20_6a88b96z2553": ("?20?044", 10),
                   "xs20_gbbo79cz1221": ("?20?009", 11),
                   "xs20_697ob96z0321": ("?20?002", 11),
                   "xs20_4a9n8brzx121": ("?20?066", 11),
                   "xs20_651u0oozw178c": ("?20?052", 11),
                   "xs20_259aczw311d96": ("?20?005", 11),
                   "xs20_0mlhegoz3443": ("?20?022", 12),
                   "xs20_69b88a6z2553": ("?20?048", 12),
                   "xs20_39u0mmz321011": ("?20?026", 12),
                   "xs20_0cc0si96z2553": ("?20?032", 12),
                   "xs20_354mggzx1023cko": ("?20?023", 12),
                   "xs20_caakl3z3543": ("?20?050", 13),
                   "xs20_g6p3sj96z11": ("?20?015", 13),
                   "xs20_mlhe8z102596": ("?20?012", 13),
                   "xs20_4aab9a4z2553": ("?20?074", 13),
                   "xs20_c88b96z359a4": ("?20?043", 13),
                   "xs20_4a9b8b96zx33": ("006c00aa0081007e000000180018", 13),
                   "xs20_69egmicz0643": ("?20?054", 13),
                   "xs20_69mgmiczx4a6": ("?20?025", 13),
                   "xs20_0c88b96z65156": ("?20?013", 13),
                   "xs20_69b8brz253": ("?20?035", 14),
                   "xs20_mlhe0eik8z1": ("?20?028", 14),
                   "xs20_ca9licz3543": ("?20?067", 14),
                   "xs20_69baacz2553": ("R-racetrack_and_trans-R-bee", 14),
                   "xs20_gbbo3qicz11": ("?20?094", 14),
                   "xs20_69acz69d1e8": ("G_and_cis-R-loaf", 14),
                   "xs20_4aab96z6996": ("trans-pond_and_racetrack", 14),
                   "xs20_259acz311d96": ("?20?060", 14),
                   "xs20_3lkkmicz3201": ("?20?075", 14),
                   "xs20_69mggzw2egnc": ("?20?029", 14),
                   "xs20_cid96zw11d96": ("?20?064", 14),
                   "xs20_69e0mmz03543": ("?20?073", 14),
                   "xs20_9f0v1eozx121": ("?-R-racetrack_II_and_trans-table", 14),
                   "xs20_259mgmiczx66": ("?20?042", 14),
                   "xs20_wrb079icz321": ("[[eater_and_block on R-mango]]", 14),
                   "xs20_4a9baa4z2553": ("?20?082", 14),
                   "xs20_0gillmz346w23": ("?20?110", 14),
                   "xs20_02596z69d1156": ("?20?037", 14),
                   "xs20_0gillmz32w643": ("?20?071", 14),
                   "xs20_04a96zcid1156": ("beehive_with_long_nine_and_ortho-loaf", 14),
                   "xs20_0mmge952z3421": ("?20?007", 14),
                   "xs20_0cc0si96z6513": ("?20?076", 14),
                   "xs20_0gjlk453z32w23": ("?20?040", 14),
                   "xs20_ca9bqicz33": ("006c006a0009000b001a0012000c", 15),
                   "xs20_caabqicz33": ("?20?033", 15),
                   "xs20_2llmz122qr": ("?-R-bee_and_long_R-bee_and_block", 15),
                   "xs20_2596z355d96": ("R-racetrack_and_trans-loaf", 15),
                   "xs20_g8e1t6zdd11": ("?20?079", 15),
                   "xs20_69b8brz0352": ("?20?055", 15),
                   "xs20_caab96z3552": ("R-racetrack_and_cis-R-bee", 15),
                   "xs20_gbbo796z1221": ("?-R-bee_on_R-pond_and_block", 15),
                   "xs20_69mgmiczw6a4": ("00c0012000d6001500d200900060", 15),
                   "xs20_69bq2kozx643": ("?20?087", 15),
                   "xs20_g88r3ob96z11": ("?20?046", 15),
                   "xs20_cimge96z6421": ("?20?111", 15),
                   "xs20_08e1ticz6513": ("?-R-bee_with_bend_tail_on_hook", 15),
                   "xs20_6a88b96z6513": ("ortho-hook_and_long_worm", 15),
                   "xs20_69b88brzx321": ("?20?024", 15),
                   "xs20_4aab8brzx321": ("006c006a0009006b002800280010", 15),
                   "xs20_2lmgmmz346w1": ("[[?20?116]]", 15),
                   "xs20_8e1mkk8z3543": ("006800ae00810076001400140008", 15),
                   "xs20_69b88a6z6513": ("[[trans-bookend-up and part_scorpion]]", 15),
                   "xs20_gbbgf96z1221": ("?20?045", 15),
                   "xs20_69b8b96zw256": ("very_long_worm_and_boat", 15),
                   "xs20_39u0e952z321": ("trans-R-loaf_and_long_dock", 15),
                   "xs20_4aabaa4z2553": ("?20?014", 15),
                   "xs20_3lkm996z1221": ("?20?058", 15),
                   "xs20_39u0eik8z321": ("?20?090", 15),
                   "xs20_6a88bqicz033": ("?20?099", 15),
                   "xs20_gt3ob96z1221": ("?20?096", 15),
                   "xs20_w4s3qicz3543": ("006000a00084007c0003001a0012000c", 15),
                   "xs20_g8o0ehrz1254c": ("R-bee_with_tail_and_C", 15),
                   "xs20_069b88czca513": ("?-boat_with_leg_and_worm", 15),
                   "xs20_0mmgml2z346w1": ("?-worm_and_boat_and_block", 15),
                   "xs20_02596z6511d96": ("?20?016", 15),
                   "xs20_04aab871zc871": ("?20?089", 15),
                   "xs20_6t1688gzw11dd": ("?20?049", 15),
                   "xs20_65ligzw1023cko": ("?20?092", 15),
                   "xs20_raaraar": ("?20?021", 16),
                   "xs20_2llmz1qq23": ("?20?078", 16),
                   "xs20_2llmzrq221": ("?-R-bee_and_long_R-bee_and_block", 16),
                   "xs20_gbaq3qicz11": ("00c0009600750001007e0048", 16),
                   "xs20_g8e1t6z11dd": ("?20?041", 16),
                   "xs20_caab96z3156": ("?20?070", 16),
                   "xs20_3pmgm96zx66": ("?20?085", 16),
                   "xs20_651u0ooz3543": ("006600a50081007e000000180018", 16),
                   "xs20_4aab8b96zx33": ("[[?20?114]]", 16),
                   "xs20_gad1eoz011dd": ("003000eb010b016800a80010", 16),
                   "xs20_39egmicz0643": ("00c000930071000e006800480030", 16),
                   "xs20_69b8n96z0311": ("?20?039", 16),
                   "xs20_2lligz1qq221": ("?-beehive_and_very_long_beehive_and_block", 16),
                   "xs20_mmge9a4z1243": ("006c006a00090076009000500020", 16),
                   "xs20_cimgm952z066": ("0060009600550021001e000000060006", 16),
                   "xs20_g88bbgz0d55d": ("?-very_long_beehive_and_table_and_block", 16),
                   "xs20_0ad1eoz69d11": ("?20?020", 16),
                   "xs20_3lkljgz346w1": ("?20?072", 16),
                   "xs20_04aab96z3553": ("?20?101", 16),
                   "xs20_2llmz32w32ac": ("01800140004000600016001500550062", 16),
                   "xs20_4a96kk8z6953": ("00c4012a00a90066001400140008", 16),
                   "xs20_6996z65115ac": ("trans-boat_with_long_nine_and_trans-pond", 16),
                   "xs20_g08o653zd5lo": ("[[ship on bookends]]", 16),
                   "xs20_ca1u8zx123cko": ("03000280018000600048003e0001000a000c", 16),
                   "xs20_02596z255d952": ("racetrack_II_and_trans-loaf", 16),
                   "xs20_0ca23z255d1e8": ("?-eater_and_anvil", 16),
                   "xs20_069b88cz4a953": ("?20?019", 16),
                   "xs20_0cc0si53z2553": ("?-boat_with_leg_on_R-bee_and_block", 16),
                   "xs20_0gjlkmz32w643": ("long_worm_and_para-hook", 16),
                   "xs20_03lkkl3z256w1": ("cis-boat_with_long_leg_and_cis-dock", 16),
                   "xs20_8kkm1mkk8zx121": ("[[hat fuse hat]]", 16),
                   "xs20_ci96z0o5l96zw1": ("0180024604a9032a00240018", 16),
                   "xs20_0gilmz12iaq1zx1": ("[[?20?115]]", 16),
                   "xs20_255mggzx1023cko": ("[[meta-hook_and_R-bee at ship]]", 16),
                   "xs20_2552s0gzy1123cko": ("ship_on_boat_line_beehive", 16),
                   "xs20_raarhar": ("cis-mirrored_snake_siamese_table", 17),
                   "xs20_354mp3qic": ("0198012e00e100150036", 17),
                   "xs20_660uhbqic": ("00d80168010b00eb0030", 17),
                   "xs20_okiqb96z66": ("00d800d40012001a000b00090006", 17),
                   "xs20_2llmz32qq1": ("?-R-bee_and_long_R-bee_and_block", 17),
                   "xs20_3j0v1qrz011": ("?-very_long_eater_siamese_snake_and_block", 17),
                   "xs20_6996z69d552": ("?20?056", 17),
                   "xs20_2ll68oz345d": ("008c0152015a00cb00200030", 17),
                   "xs20_ca9e0eicz33": ("?20?105", 17),
                   "xs20_0caab96z6513": ("R-racetrack_and_?-hook", 17),
                   "xs20_69e0uiz03543": ("?20?008", 17),
                   "xs20_wml1ege2z643": ("0180014000400064000a006a004b0030", 17),
                   "xs20_04a96zcid553": ("?-long_R-bee_siamese_beehive_and_?-loaf", 17),
                   "xs20_69b8ozx32qic": ("01800240034000580068000b00090006", 17),
                   "xs20_3lkm996z3201": ("?-pond_siamese_hook_on_hook", 17),
                   "xs20_0caab96z2553": ("?20?017", 17),
                   "xs20_69b88brzx311": ("006c006a000a000b006800480030", 17),
                   "xs20_2lligz122qq1": ("trans-very_long_bee_and_block_and_beehive", 17),
                   "xs20_8u1v0ccz3421": ("0068009e0041003f0000000c000c", 17),
                   "xs20_2lmgmicz1246": ("?20?098", 17),
                   "xs20_02596z69d553": ("R-racetrack_and_?-loaf", 17),
                   "xs20_xokc0fhoz653": ("ortho-ship_on_ship_and_long_hook", 17),
                   "xs20_ckgil96z4aa4": ("cis-loaf_with_long_nine_and_trans-beehive", 17),
                   "xs20_3lmge93z1221": ("?-R-bee_on_hook_and_ship", 17),
                   "xs20_gbb8b96z1213": ("?20?097", 17),
                   "xs20_4aab9a4z6513": ("racetrack_II_and_?-hook", 17),
                   "xs20_4aab871z6952": ("anvil_and_?-loaf", 17),
                   "xs20_069baiczc871": ("0180010600e9002b000a0012000c", 17),
                   "xs20_354kl3zca521": ("cis-very_long_ship_and_dock", 17),
                   "xs20_69q4gozca343": ("01860149007a008400700018", 17),
                   "xs20_0gbbob96z321": ("?20?018", 17),
                   "xs20_2596o696zx343": ("?-3some_loaf_beehives", 17),
                   "xs20_69ligkcz04aa4": ("cis-loaf_with_long_nine_and_cis-beehive", 17),
                   "xs20_0gjlkmz346w23": ("long_worm_and_cis-hook", 17),
                   "xs20_4a96z65115ak8": ("trans-barge_with_long_nine_and_?-loaf", 17),
                   "xs20_0g8eht2sgz321": ("?20?063", 17),
                   "xs20_0gadhu0ooz321": ("01800140009b006b002800480030", 17),
                   "xs20_356o8gzciq221": ("?20?062", 17),
                   "xs20_69baa4ozw6511": ("0060009000d30055005400240018", 17),
                   "xs20_35a8czw311d96": ("?-boat_with_leg_and_worm", 17),
                   "xs20_0g8o653zol54c": ("?20?027", 17),
                   "xs20_0cc0si52z6953": ("?-tub_with_leg_on_R-loaf_and_block", 17),
                   "xs20_4a9baaczw2552": ("R-racetrack_II_and_beehive", 17),
                   "xs20_0gillicz32w66": ("006000500012001500d500d2000c", 17),
                   "xs20_4a9baa4zw2553": ("racetrack_II_and_?-R-bee", 17),
                   "xs20_4a9eg8oz0359c": ("004000ac012a00e9001300200030", 17),
                   "xs20_25a8c4oz069d11": ("?-big_S_siamese_tub_with_leg", 17),
                   "xs20_69icw8k8zxdd11": ("?-mango_long_line_tub_and_cis-block", 17),
                   "xs20_64ljgzw1023cko": ("hook_on_ship_and_shift-hook", 17),
                   "xs20_2596o8zy0123cko": ("?-loaf_on_eater_on_ship", 17),
                   "xs20_330fhqb96": ("01b601ad0021002e0018", 18),
                   "xs20_2egt3ob96": ("00d80153010a00ea002c", 18),
                   "xs20_330fhu0ui": ("?-long_hook_siamese_long_hook_and_table_and_block", 18),
                   "xs20_caabpicz33": ("006c006a000a000b00190012000c", 18),
                   "xs20_qmgu156z66": ("00da00d60010001e000100050006", 18),
                   "xs20_09v0rrz643": ("?20?031", 18),
                   "xs20_6s1v0rrzw1": ("iron_and_blocks", 18),
                   "xs20_gbb871zc953": ("0190012b00ab006800070001", 18),
                   "xs20_6a88brz2596": ("?-very_long_eater_and_loaf_and_block", 18),
                   "xs20_5b8b96z6952": ("014601a9002a01a4012000c0", 18),
                   "xs20_ca9bo8a6z33": ("00c000c0000800fe008100530030", 18),
                   "xs20_3pmgm96z066": ("?-beehive_with_long_leg_siamese_shillelagh_and_?-block", 18),
                   "xs20_c97ob96z311": ("006c002900270018000b00090006", 18),
                   "xs20_2lmgm96z346": ("0062009500d60010001600090006", 18),
                   "xs20_69baacz6513": ("R-racetrack_and_trans-hook", 18),
                   "xs20_69a4z69d1da": ("014001a0002401aa012900c6", 18),
                   "xs20_gbb8brz1252": ("00d800d0001200d500d2000c", 18),
                   "xs20_ca5licz3543": ("006c00aa008500750012000c", 18),
                   "xs20_69b4kmz03543": ("0068002e002100d500960060", 18),
                   "xs20_3lkaarz32011": ("?20?080", 18),
                   "xs20_0g88b96zrq23": ("?20?107", 18),
                   "xs20_69q4goz4ab43": ("00c2012500bd0042001c0030", 18),
                   "xs20_w9v0f96z2521": ("?-tub_with_leg_siamese_table_and_cis-cap", 18),
                   "xs20_3lmge93z3201": ("?-hook_on_hook_and_ship", 18),
                   "xs20_8e1e8z311d96": ("worm_and_hat", 18),
                   "xs20_cimge93z6421": ("00cc009200560030000e00090003", 18),
                   "xs20_39mgmiczw6a4": ("0180012000d6001500d200900060", 18),
                   "xs20_69b88gz69l91": ("018c02520355005200500020", 18),
                   "xs20_8e1e8gz5b871": ("00a8016e010100ee00280010", 18),
                   "xs20_0gjl46z122qr": ("?-long_R-bee_and_hook_and_block", 18),
                   "xs20_69b8b9czx352": ("0060009000d0001600d500920030", 18),
                   "xs20_35a8cz311d96": ("worm_and_?-boat_with_leg", 18),
                   "xs20_o8bb8oz011dd": ("?20?104", 18),
                   "xs20_8k4t3ob96zw1": ("00d80150010e00e9002a0004", 18),
                   "xs20_gbbgf1e8z121": ("006c006a000a006b009000a00040", 18),
                   "xs20_ml1e8z110796": ("00d80158010000ee00290006", 18),
                   "xs20_0c9baa4z6953": ("?20?036", 18),
                   "xs20_33gv1ooz0643": ("?-hook_siamese_Z_and_blocks", 18),
                   "xs20_69a4z6511dic": ("beehive_with_long_nine_and_?-loaf", 18),
                   "xs20_0gbaqb96z321": ("00c000a00048003e0001003d0026", 18),
                   "xs20_ciu0e9jzx311": ("0064004a003a0003003c00240018", 18),
                   "xs20_2lmggz34aaq1": ("011802a401aa002a002b0010", 18),
                   "xs20_39e0okcz2553": ("?20?068", 18),
                   "xs20_0c88brz69d11": ("?-scorpio_siamese_Z_and_block", 18),
                   "xs20_69mgeiczx346": ("?-eater_on_R-bee_on_beehive", 18),
                   "xs20_g08o653zdll8": ("hook_on_ship_and_cis-R-bee", 18),
                   "xs20_4a9baa4z6513": ("racetrack_II_and_?-hook", 18),
                   "xs20_g9fgf96z1221": ("?-pond_siamese_table_on_cap", 18),
                   "xs20_2llmz12269a4": ("?-long_bee_siamese_loaf_and_R-bee", 18),
                   "xs20_35a88a6zca53": ("trans-boat_with_long_nine_and_long_ship", 18),
                   "xs20_39mgmicz04a6": ("0180012200d5001600d000900060", 18),
                   "xs20_696k4ozcid11": ("?20?010", 18),
                   "xs20_69baacz03156": ("R-racetrack_and_?-hook", 18),
                   "xs20_0gbbgn96z321": ("?-R-bee_bend_line_boat_and_block", 18),
                   "xs20_0gjlmz1qq221": ("?-ship_and_block_and_very_long_beehive", 18),
                   "xs20_08e1dqz69d11": ("?-scorpio_siamese_loop", 18),
                   "xs20_69mgmicz04a6": ("00c0012200d5001600d000900060", 18),
                   "xs20_8p7ob96z1221": ("003600540044003b000a00090006", 18),
                   "xs20_62s0ciarz321": ("dock_and_trans-loop", 18),
                   "xs20_6t1e8z116952": ("00c80178010600e9002a0004", 18),
                   "xs20_09f0sicz2553": ("?-R-bee_on_R-bee_and_table", 18),
                   "xs20_069b8oz311dd": ("00600026002901ab01a80018", 18),
                   "xs20_cc0s2qrz0643": ("00d800580040003e000100330030", 18),
                   "xs20_035a4z69d1156": ("worm_and_cis-long_boat", 18),
                   "xs20_0gs2qb96z3421": ("006000b8008400740016000900050002", 18),
                   "xs20_69ac0siczw253": ("?-R-bee_on_boat_and_R-loaf", 18),
                   "xs20_0ca96zca23156": ("?-eater_siamese_hook_and_R-loaf", 18),
                   "xs20_69diczx123ck8": ("0180024002c0013000c80018000600050002", 18),
                   "xs20_0cc0si53z6513": ("?-block_and_hook_on_boat_with_leg", 18),
                   "xs20_wcc0si96zc871": ("?-block_and_eater_and_R-mango", 18),
                   "xs20_62s0si96z0643": ("00600090004800380006003900430060", 18),
                   "xs20_0c89n871z6511": ("00d800500052002e0010000e00010003", 18),
                   "xs20_3p6gmiczw1226": ("00c000980064000a006a004b0030", 18),
                   "xs20_0mp3s4oz643w1": ("?-shillelagh_siamese_hook_on_R-bee", 18),
                   "xs20_2lmgmicz01w66": ("[[?20?113]]", 18),
                   "xs20_069baicz64132": ("00c000860029006b004a0012000c", 18),
                   "xs20_rb88gzx123cko": ("ship_on_cis-boat_with_long_leg_and_trans-block", 18),
                   "xs20_039u0eicz2521": ("?-tub_with_leg_siamese_hook_and_R-bee", 18),
                   "xs20_ckgoggm96zx66": ("?-beehive_with_long_leg_siamese_hook_and_block", 18),
                   "xs20_g08o653z1pl4c": ("?-hook_on_ship_and_hook", 18),
                   "xs20_69a4z65115ak8": ("?20?086", 18),
                   "xs20_3iabgzw125aic": ("loaf_at_loaf_and_trans-dock", 18),
                   "xs20_03lkkl3z652w1": ("trans-boat_with_long_leg_and_cis-dock", 18),
                   "xs20_4aab88a6zw2552": ("006000500012001500d5005200500020", 18),
                   "xs20_259q4ozx1259a4": ("?-long_bee_siamese_mangos", 18),
                   "xs20_0ggml2z32w69ic": ("mango_with_long_nine_and_ortho-boat", 18),
                   "xs20_wcc0s253zc8711": ("0180014000ac002c0020001c000400050003", 18),
                   "xs20_25a8c8a52zx696": ("?-tub_with_leg_siamese_tub_with_leg_and_beehive", 18),
                   "xs20_25ic0c4ozx11dd": ("00800140009000680008006b004b0030", 18),
                   "xs20_2552s0s2596zy11": ("?-binocle_loaf_beehive", 18),
                   "xs20_256o8gzw8k87066": ("tub_with_long_nine_on_boat_and_trans-boat", 18),
                   "xs20_0g8k46164koz3421": ("0200050004800283010100ee00280010", 18),
                   "xs20_3pq3sj96": ("?-mango_siamese_bookend_on_snake_and_block", 19),
                   "xs20_3pabqajo": ("cis-rotated_?-table_siamese_snake", 19),
                   "xs20_69is0siar": ("?20?084", 19),
                   "xs20_6248hv0rr": ("01b001a8002501a301b0", 19),
                   "xs20_4alhe0ehr": ("018c015200550152018c", 19),
                   "xs20_354djob96": ("01b6011500e1002e0018", 19),
                   "xs20_4a9r8bqic": ("00c8017e010100ea002c", 19),
                   "xs20_330fhe0eio": ("?-hook_and_very_long_bee_and_block", 19),
                   "xs20_br0rb8oz23": ("?-tables_and_blocks", 19),
                   "xs20_0drz321ehr": ("0360022001c0003b004d0060", 19),
                   "xs20_0j2arz8lld": ("?-table_and_hook_and_R-bee", 19),
                   "xs20_ca9e0e93z33": ("?-table_siamese_loaf_and_hook_and_block", 19),
                   "xs20_mmge1ege2z1": ("010001c4002a01aa01ab0010", 19),
                   "xs20_25ac0fho8a6": ("?-eater_siamese_long_hook_and_?-long_boat", 19),
                   "xs20_cimgm96z4a6": ("00c0012000d0001000d600950062", 19),
                   "xs20_cahfgkcz643": ("00cc008a0071000f00100014000c", 19),
                   "xs20_gbb8rb8oz11": ("?-long_hook_siamese_table_and_cis-blocks", 19),
                   "xs20_6t1u0uiczw1": ("racetrack_and_cis-cap", 19),
                   "xs20_6a88brz6952": ("01b001a00024002a00a900c6", 19),
                   "xs20_3lkia4z3ego": ("031802ae00a1012301400080", 19),
                   "xs20_mkhf0ciicz1": ("alef_and_?-pond", 19),
                   "xs20_6a8o0uh32ac": ("?-long_hook_siamese_eater_and_eater", 19),
                   "xs20_4a96z695d96": ("00c4012a00a901a6012000c0", 19),
                   "xs20_ciqjkkozx66": ("00300048005800cb002b00280018", 19),
                   "xs20_259mge132ac": ("?20?011", 19),
                   "xs20_rq2kmzx3496": ("?-bookend_and_R-mango_and_block", 19),
                   "xs20_cc0v1qrzw23": ("?-very_long_Z_siamese_snake_and_blocks", 19),
                   "xs20_gbap3qicz11": ("00c0009600750001006e0058", 19),
                   "xs20_okkmhrz04a6": ("01b0011000d6005500520030", 19),
                   "xs20_gbq2ra96z11": ("?-loop_siamese_table_and_ship", 19),
                   "xs20_ciljgoz4aa6": ("008c0152015500d300100018", 19),
                   "xs20_c4o0ehrz0bd": ("?-hook_siamese_snake_and_?-C", 19),
                   "xs20_69baarz0352": ("00d80050005200d500960060", 19),
                   "xs20_okihf033z66": ("00d800d400120011000f000000030003", 19),
                   "xs20_4a96zad1d96": ("014401aa002901a6012000c0", 19),
                   "xs20_69bqikozx66": ("0060009000d0005b004b00280018", 19),
                   "xs20_gbbgv1ooz11": ("?-shillelagh_siamese_Z_and_blocks", 19),
                   "xs20_69e0uiz2553": ("?-R-bee_on_table_and_R-bee", 19),
                   "xs20_g88e13zdlge2": ("0300020801ce004100550036", 19),
                   "xs20_0ghn8brz3421": ("?-R-loaf_on_trans-legs_and_block", 19),
                   "xs20_04aabgz319ld": ("00600024012a02aa01ab0010", 19),
                   "xs20_0q6gm96z3543": ("006000ba00860070001600090006", 19),
                   "xs20_6996kk8z2553": ("0062009500950066002800280010", 19),
                   "xs20_069b871z3596": ("G_and_?-R-loaf", 19),
                   "xs20_0iu0uh3z3443": ("?-pond_siamese_table_on_long_hook", 19),
                   "xs20_3lmgmicz3201": ("0063005500340006003400240018", 19),
                   "xs20_4a96z6511dic": ("beehive_with_long_nine_and_?-loaf", 19),
                   "xs20_3l2s0sicz321": ("boat_line_boat_and_R-bee", 19),
                   "xs20_4a96z255d1e8": ("anvil_and_?-loaf", 19),
                   "xs20_3lkmik8z1226": ("00c400aa002a006b004800280010", 19),
                   "xs20_8e1t2sgz3123": ("?-amoeba_9,6,4", 19),
                   "xs20_3hu0okcz3443": ("00c6008900790006001800280030", 19),
                   "xs20_ca952z315ako": ("long_boat_with_leg_and_?-R-mango", 19),
                   "xs20_69b8b9czw253": ("?20?088", 19),
                   "xs20_35s2lliczx11": ("00cc0092006d0021002e0018", 19),
                   "xs20_cc0ca96z3553": ("?-R-loaf_and_cap_and_block", 19),
                   "xs20_0gilmz34aaq1": ("006000900152015503560020", 19),
                   "xs20_69e0okcz6513": ("?-hook_on_ship_and_R-bee", 19),
                   "xs20_0178b96z6953": ("G_and_?-R-loaf", 19),
                   "xs20_25a8czcid552": ("?-long_bee_siamese_beehive_and_?-tub_with_leg", 19),
                   "xs20_3lkmz12269a4": ("?-long_beehive_siamese_loaf_and_hook", 19),
                   "xs20_xggs2qrz4a96": ("loaf_with_trans-tail_siamese_trans-legs_and_block", 19),
                   "xs20_2lmge93z3421": ("?-hook_on_R-loaf_and_boat", 19),
                   "xs20_xoie0e93z653": ("?20?077", 19),
                   "xs20_0mm0e952zc96": ("?-shillelagh_and_R-loaf_and_block", 19),
                   "xs20_0c88bqicz653": ("00c000ac00680008000b001a0012000c", 19),
                   "xs20_ml1e8gz1cd11": ("00d80153010b00e800280010", 19),
                   "xs20_69baacz03552": ("R-racetrack_and_?-R-bee", 19),
                   "xs20_9v0s2acz3421": ("009600f90002003c004000500030", 19),
                   "xs20_ciiriiczw4a4": ("00600090009201b5009200900060", 19),
                   "xs20_0g88brz8ll91": ("?20?065", 19),
                   "xs20_4aabaa4z6513": ("00c400aa002a006b000a000a0004", 19),
                   "xs20_025acz69d1da": ("014001ac002a01a5012200c0", 19),
                   "xs20_ckggm952zca6": ("trans-loaf_with_long_nine_and_?-ship", 19),
                   "xs20_0696z355d1e8": ("R-anvil_and_beehive", 19),
                   "xs20_69aczw69d1e8": ("G_and_?-R-loaf", 19),
                   "xs20_c88b96z315ac": ("worm_and_?-boat_with_leg", 19),
                   "xs20_2lmge96z3421": ("?20?059", 19),
                   "xs20_3lmggz122qq1": ("?-very_long_bee_and_ship_and_block", 19),
                   "xs20_0259arz69d11": ("01b000a80128014b00890006", 19),
                   "xs20_08e1dmz69d11": ("00d00168010800eb00290006", 19),
                   "xs20_06t1eoz69521": ("00c0012600bd0041002e0018", 19),
                   "xs20_0mll2sgz3443": ("00600096009500750002001c0010", 19),
                   "xs20_2lmgeicz1243": ("004400aa0069000e007000480030", 19),
                   "xs20_0c9b871z6996": ("alef_and_trans-pond", 19),
                   "xs20_39c0sicz2553": ("?-R-bee_on_R-bee_and_carrier", 19),
                   "xs20_g88bbgz6b871": ("00d00168010800eb002b0010", 19),
                   "xs20_3hu0e96zw346": ("?-long_hook_siamese_eater_and_R-bee", 19),
                   "xs20_06996z319lic": ("cis-loaf_with_long_nine_and_cis-pond", 19),
                   "xs20_ciar1qczx321": ("0018002e0041006f002800240018", 19),
                   "xs20_xoie0e96z653": ("hook_on_ship_and_trans-R-bee", 19),
                   "xs20_4a9mge2zca43": ("0184014a008900760010000e0002", 19),
                   "xs20_4a9baarzx311": ("006c002a002a006b004800280010", 19),
                   "xs20_ca96kicz0653": ("0030005300950066002800480030", 19),
                   "xs20_06t1u8z69521": ("00c0012600bd0041003e0008", 19),
                   "xs20_wgt3on1z4a43": ("?-bookends_siamese_tub_with_leg", 19),
                   "xs20_4a9e0uizw653": ("0048007800060075009300500020", 19),
                   "xs20_0ca2jz69d543": ("00c0012c01aa00a200930060", 19),
                   "xs20_cil68ozca611": ("018c015200d5002600280018", 19),
                   "xs20_4a9mge2z6a43": ("00c4014a008900760010000e0002", 19),
                   "xs20_g8o653zd54ko": ("long_hook_and_para-ship_on_ship", 19),
                   "xs20_0mm0uh3z3443": ("?-long_hook_on_pond_and_block", 19),
                   "xs20_8e1ra952z311": ("008000e0001000dc004200590036", 19),
                   "xs20_0gjlmz122qq1": ("cis-ship_and_block_and_very_long_beehive", 19),
                   "xs20_0g6t1uge2z121": ("0080014000ac002a006a004b0030", 19),
                   "xs20_8o1v0sicz0123": ("00300050005600d5001500120030", 19),
                   "xs20_0354kl3z4aa43": ("dock_and_?-beehive_with_tail", 19),
                   "xs20_069baicz31132": ("006000260029006b004a0012000c", 19),
                   "xs20_02596z259d552": ("racetrack_II_and_?-loaf", 19),
                   "xs20_0okkm952z4aa4": ("?-long_R-bee_siamese_loaf_and_beehive", 19),
                   "xs20_65pa3iaczx121": ("0068009e00c10033002400140008", 19),
                   "xs20_06996zc871156": ("?-long_hook_siamese_eater_and_cis-pond", 19),
                   "xs20_02596z255d552": ("004000a200a501a900a600a00040", 19),
                   "xs20_2lla8kicz1221": ("?-3some_beehives_loaf", 19),
                   "xs20_06996zca51156": ("trans-boat_with_long_nine_and_cis-pond", 19),
                   "xs20_0gjlmz32w69a4": ("trans-loaf_with_long_nine_and_cis-ship", 19),
                   "xs20_0g4qabqicz121": ("0080014000a6003d0041003e0008", 19),
                   "xs20_4a9egmiczw252": ("003000480068000a0075009200500020", 19),
                   "xs20_8kkljgozw4aa4": ("0030001201950155005200500020", 19),
                   "xs20_0c88bqicz2552": ("0060009000600006007d0041000e0008", 19),
                   "xs20_25a88b96zx696": ("00c0012001a60029002600a001400080", 19),
                   "xs20_25b8b96z02552": ("0060009000d2001500d500a20040", 19),
                   "xs20_25a8a6z4a5156": ("cis-mirrored_tub_with_nine", 19),
                   "xs20_c88baicz35421": ("006c00a80088004b002a0012000c", 19),
                   "xs20_0g88b96z1qa96": ("01800240034c0052004a002b0010", 19),
                   "xs20_0gadhu066z321": ("0180014000980068002b004b0030", 19),
                   "xs20_02ll2sgz47074": ("?-beehive_with_tail_and_R-hat", 19),
                   "xs20_06996z311dik8": ("01000280024601a9002900260060", 19),
                   "xs20_0okkm96zc8426": ("?-long_R-bee_siamese_beehive_and_?-long_snake", 19),
                   "xs20_3lkmik8z01w66": ("00c000ac00280068004b002b0010", 19),
                   "xs20_03lkkl3z643w1": ("?-table_siamese_eater_and_cis-dock", 19),
                   "xs20_352s0siczw643": ("00c000a2005500150016000800280030", 19),
                   "xs20_354mkk8z069a4": ("01800146004900d5005200500020", 19),
                   "xs20_62sggm96zw6a4": ("?-beehive_with_long_leg_siamese_eater_and_boat", 19),
                   "xs20_ciab88gzw11dd": ("0060009000a801a8002b002b0010", 19),
                   "xs20_0mkl3z12269a4": ("?-long_bee_siamese_loaf_and_hook", 19),
                   "xs20_06996z311d552": ("00600026002901a900a600a00040", 19),
                   "xs20_69icwckzxdd11": ("00c001200090006b000b000800680050", 19),
                   "xs20_4a9baa4zw6513": ("racetrack_II_and_?-hook", 19),
                   "xs20_0oggm952zciic": ("trans-loaf_with_long_leg_and_trans-pond", 19),
                   "xs20_o8bbgzx123cko": ("?-trans-boat_with_long_leg_on_ship_and_cis-block", 19),
                   "xs20_2lligz32w69a4": ("?20?061", 19),
                   "xs20_069a4zcid1156": ("beehive_with_long_nine_and_?-loaf", 19),
                   "xs20_0gilmz32w69ic": ("mango_with_long_nine_and_?-boat", 19),
                   "xs20_cic0v1ok8zx23": ("?-very_long_Z_and_beehive_and_boat", 19),
                   "xs20_4aab88a6zx356": ("006000500013001500d6005000500020", 19),
                   "xs20_mkkm453z1w252": ("?-long_and_tub_with_long_leg", 19),
                   "xs20_35a8c8a6zx696": ("?-boat_with_leg_siamese_hook_and_beehive", 19),
                   "xs20_354kl3zx125ac": ("dock_and_trans-very_long_ship", 19),
                   "xs20_4akggm96z0ca6": ("beehive_long_line_tub_and_?-ship", 19),
                   "xs20_0gw8e13z8ll913": ("?-Z_and_eater_and_beehive", 19),
                   "xs20_ckgiljgzx1w346": ("?-eaters_siamese_table_and_boat", 19),
                   "xs20_2lm862sgz01226": ("004000ac006a00120063004000380008", 19),
                   "xs20_0255q4ozoge221": ("0300020201c50045005a00240018", 19),
                   "xs20_kcw8o652z0dd11": ("00c000c0000000f001080098018600050002", 19),
                   "xs20_g08o653z11d4ko": ("ship_on_hook_and_para-hook", 19),
                   "xs20_69ak8gzx121eic": ("?-R-bee_on_beehive_at_loaf", 19),
                   "xs20_069q4oz6a87011": ("?-loaf_with_tail_siamese_worm", 19),
                   "xs20_0354q4ozc97011": ("0180012300e50004003a00240018", 19),
                   "xs20_ci970s4ozx6221": ("R-bee_with_tail_and_cis-R-mango", 19),
                   "xs20_25a8c8a6zw3552": ("?20?112", 19),
                   "xs20_0ojd88gz4aa611": ("00800158015300cd002800280010", 19),
                   "xs20_0j9eg6p3z121w1": ("?20?091", 19),
                   "xs20_31egogkczw4aa4": ("?-integral_siamese_hook_and_cis-beehive", 19),
                   "xs20_0gw8o653z8ll91": ("030002800180006000500012001500350002", 19),
                   "xs20_39c88c93zw2552": ("?-carriers_siamese_table_and_beehive", 19),
                   "xs20_04s0ci52zc97011": ("long_and_trans-tub_with_long_leg", 19),
                   "xs20_069e0o4ozc871w1": ("?-eater_and_R-bee_and_beehive", 19),
                   "xs20_2560u1u0652zy11": ("very_long_beehive_and_?-boats", 19),
                   "xs20_354q4gzy0123cko": ("0300028001800060005000280008001600090003", 19),
                   "xs20_354k8gzx122dik8": ("?-loaf_at_loaf_with_trans-nine", 19),
                   "xs20_raar1qr": ("?-table_siamese_snake_and_table_and_block", 20),
                   "xs20_ra9r8br": ("006d006b0000007f0049", 20),
                   "xs20_65pabojd": ("00d60059008300bc0064", 20),
                   "xs20_178jr8br": ("00db00da000200f40098", 20),
                   "xs20_330fho8br": ("01b301a30020002f0019", 20),
                   "xs20_2egu1raic": ("00ac016a010a00eb0030", 20),
                   "xs20_2egu1vg33": ("?20?095", 20),
                   "xs20_69bqic0f9": ("0186009d00a101ae0018", 20),
                   "xs20_i5lmzdlk9": ("01b202a502950136", 20),
                   "xs20_2egu1qb96": ("00d0016b010a00ea002c", 20),
                   "xs20_32qb8r9ic": ("012c01ea0001007d004a", 20),
                   "xs20_354qabqic": ("0188013e00c1003d0026", 20),
                   "xs20_db8f1e8z33": ("006d006b0008000f0001000e0008", 20),
                   "xs20_69707960ui": ("?-R-bees_and_table", 20),
                   "xs20_2egm970796": ("01b002ab02aa0112000c", 20),
                   "xs20_mkhf03pmz1": ("alef_and_?-shillelagh", 20),
                   "xs20_mkhf0f96z1": ("alef_and_cis-cap", 20),
                   "xs20_259mge1dic": ("018c0252015500950062", 20),
                   "xs20_0dr0rrz643": ("?-long_hook_siamese_snake_and_blocks", 20),
                   "xs20_178f123qic": ("0368015e014100c50006", 20),
                   "xs20_330fho0uh3": ("?-long_hooks_and_block", 20),
                   "xs20_6a8ob960ui": ("fourteener_and_?-table", 20),
                   "xs20_6is079c0f9": ("?-rotated_hook_and_?-table", 20),
                   "xs20_mlhu0ooz56": ("00b600d50011001e000000180018", 20),
                   "xs20_mkiaraicz1": ("008000ea001d00c100be0008", 20),
                   "xs20_2llmzpia43": ("03220255015500960060", 20),
                   "xs20_4ad1egu156": ("018c0252035500560060", 20),
                   "xs20_651ug8ob96": ("01860289020b01e80058", 20),
                   "xs20_4ap3qicz643": ("00c4008a00790003001a0012000c", 20),
                   "xs20_mllmz104a96": ("cis-loaf_with_long_leg_and_cis-cap", 20),
                   "xs20_j1u069arz11": ("dock_and_?-loop", 20),
                   "xs20_ciab8brzw23": ("006c00680008006b002900240018", 20),
                   "xs20_gbbgn96z123": ("0036005600500026001900050006", 20),
                   "xs20_xokiarz6996": ("01b000a0009000500036000900090006", 20),
                   "xs20_69acz69l913": ("018c0252015500d200100018", 20),
                   "xs20_g88m93zd5lo": ("0300024001a3005500540036", 20),
                   "xs20_o4q2raarz01": ("beehive_with_tail_siamese_table_and_?-table", 20),
                   "xs20_j96o8brz121": ("006c00680008000c003200490066", 20),
                   "xs20_4a960uh32ac": ("011802ae04a103230030", 20),
                   "xs20_3hu0mqz3443": ("?-pond_siamese_long_hook_on_snake", 20),
                   "xs20_cillicz4aa4": ("008c0152015500950012000c", 20),
                   "xs20_okihf0ccz66": ("00d800d400120011000f0000000c000c", 20),
                   "xs20_0mllicz34ac": ("00600096015501950012000c", 20),
                   "xs20_3jgv1ok8z32": ("?-Z_siamese_eater_and_boat_and_block", 20),
                   "xs20_rb8ozw6b871": ("?-head_siamese_table_and_trans-block", 20),
                   "xs20_0c9b871zojd": ("alef_and_?-shillelagh", 20),
                   "xs20_gbbgra96z11": ("?-loop_siamese_shillelagh_and_block", 20),
                   "xs20_4a96z69d1da": ("?20?057", 20),
                   "xs20_0mlla4z3ego": ("0080014002a302a101ae0018", 20),
                   "xs20_6t1egm96z11": ("00c0004c005200d500950062", 20),
                   "xs20_35s2djoz321": ("0066004a00340015001300500060", 20),
                   "xs20_mmge1dik8z1": ("010001c6002901aa01a40018", 20),
                   "xs20_0mp3qicz643": ("00c0009600790003001a0012000c", 20),
                   "xs20_ci6kl3z3543": ("00c000a8002e0061004d0036", 20),
                   "xs20_3lkmge2z346": ("00c600a9002b0068000800700040", 20),
                   "xs20_j9ab96z1256": ("00cc0092005500d300900060", 20),
                   "xs20_39mgmp3zw66": ("00c000980068000b006b009000c0", 20),
                   "xs20_g88b96zdl96": ("01b002a8012800cb00090006", 20),
                   "xs20_2llmge2z346": ("0062009500d500160010000e0002", 20),
                   "xs20_gbq2rq23z11": ("00c000ac006c0000007f0049", 20),
                   "xs20_j5s2uge2z11": ("?-eater_on_shillelagh_siamese_hook", 20),
                   "xs20_c9baiczc871": ("018c010900eb002a0012000c", 20),
                   "xs20_c9baa4z3596": ("iron_and_?-R-loaf", 20),
                   "xs20_gbaara96z11": ("00c00088007e0001007d004a", 20),
                   "xs20_g8o653zdlkc": ("cap_and_para-ship_on_ship", 20),
                   "xs20_178baarzw33": ("006c00280028006b000b00700040", 20),
                   "xs20_g6s178brz11": ("?-hook_siamese_carrier_siamese_trans-legs_and_block", 20),
                   "xs20_okkmhrzw6a4": ("01b0011200d5005600500030", 20),
                   "xs20_3lkmicz34a4": ("018c0152005500d200900060", 20),
                   "xs20_8p7graa4z23": ("00c00040005800ce0021002e0068", 20),
                   "xs20_mk1fgkcz1ac": ("00d80055010301e0001000500060", 20),
                   "xs20_3i1v0rrz011": ("?-very_long_hook_siamese_snake_and_block", 20),
                   "xs20_okiq32acz66": ("00d800d40012001a00030002000a000c", 20),
                   "xs20_0bq2rq23z32": ("00c00080002c006c0000007f0049", 20),
                   "xs20_69baiczad11": ("014601a9002b002a0012000c", 20),
                   "xs20_5b8b9cz2553": ("00a200d5001500d600900030", 20),
                   "xs20_mllmz1w69a4": ("trans-loaf_with_long_leg_and_cis-cap", 20),
                   "xs20_3pmkk8zcia4": ("?-long_R-bee_siamese_shillelagh_and_loaf", 20),
                   "xs20_651ugmqzx66": ("006000a00080007b000b00680058", 20),
                   "xs20_69e0uiz6513": ("?-hook_on_table_and_R-bee", 20),
                   "xs20_wmm0ehrz643": ("?-C_and_eater_and_block", 20),
                   "xs20_69ab8oz6996": ("00c60129012a00cb00080018", 20),
                   "xs20_o4q2riarz01": ("beehive_with_tail_siamese_table_and_?-snake", 20),
                   "xs20_bq2r96z3421": ("?20?047", 20),
                   "xs20_3lm0uiz3443": ("?20?106", 20),
                   "xs20_178bdzx65156": ("R-loop_and_?-C", 20),
                   "xs20_wmmge13z69a4": ("0180010000e0001000d200d500090006", 20),
                   "xs20_8ehlmzw56074": ("008000e0001600d500b1000e0008", 20),
                   "xs20_oggo2ticz6a4": ("00d80150009000180002001d0012000c", 20),
                   "xs20_69b8ozx122qr": ("03600340004000580028000b00090006", 20),
                   "xs20_cc0v1acz3521": ("006c00ac0040003f0001000a000c", 20),
                   "xs20_ciklb8ozx346": ("00300048002800ae00d100130018", 20),
                   "xs20_178bdzw359a4": ("010001c0002c01aa016900050002", 20),
                   "xs20_0mmgmp3z1246": ("00c000980068000b0069006a0004", 20),
                   "xs20_0g88b96z32qr": ("018002400340005b004b00280018", 20),
                   "xs20_8e1e8gz311dd": ("0068002e002101ae01a80010", 20),
                   "xs20_6t1acz11079c": ("0180012c00ea0001003d0026", 20),
                   "xs20_039eg8oz355d": ("006000a300a901ae001000080018", 20),
                   "xs20_cic0s2qrzx23": ("008000e2001500d500d200100018", 20),
                   "xs20_0ml1eozc9611": ("0180013600d50021002e0018", 20),
                   "xs20_wgs2qb96z643": ("0180014000400068002e0021001d0006", 20),
                   "xs20_0ciqb96z6226": ("00c0004c005200da000b00090006", 20),
                   "xs20_6a88brz0178c": ("01b001a30021002e00a800c0", 20),
                   "xs20_8ehbgzw1qa96": ("00c001200150034b0031000e0008", 20),
                   "xs20_6t1acz116952": ("00c80178010600a9006a0004", 20),
                   "xs20_oiege96z6221": ("00d80052004e0030000e00090006", 20),
                   "xs20_3pe0okiczx56": ("00c000a200250069004e001000080018", 20),
                   "xs20_03p6gzok45lo": ("long_integral_and_?-dock", 20),
                   "xs20_69b8ozx1qq23": ("0180024003400050006b000b00080018", 20),
                   "xs20_0ca9licz6513": ("?-R-mango_siamese_loaf_on_hook", 20),
                   "xs20_g84q96z1pgf2": ("01800248017e008100530030", 20),
                   "xs20_c4o0ehrz039c": ("?-hook_siamese_carrier_and_C", 20),
                   "xs20_01784ozad1dd": ("014001a1002701a801a40018", 20),
                   "xs20_3lkia4z34aa4": ("018c01520055009500a20040", 20),
                   "xs20_69ligkcz0ca6": ("cis-loaf_with_long_nine_and_?-ship", 20),
                   "xs20_354kozca22qk": ("0306028a008800a8006b0005", 20),
                   "xs20_651248go3qic": ("06c00aa0081307090106", 20),
                   "xs20_31eg8ozrq221": ("?-boat_with_nine_and_long_leg_and_block", 20),
                   "xs20_g88bbgz1pl91": ("very_long_R-bee_and_boat_and_block", 20),
                   "xs20_0ok2qj96z643": ("00c000a00020006c004a0021001d0006", 20),
                   "xs20_ca52gz319ll8": ("?-Z_and_long_boat_and_beehive", 20),
                   "xs20_6a88brz035a4": ("?-very_long_eater_and_long_boat_and_block", 20),
                   "xs20_31egmicz6521": ("00c300a1004e003000160012000c", 20),
                   "xs20_0mmgm952z346": ("006000a0008000780004006a00690006", 20),
                   "xs20_35s2552z354c": ("018c014a00720083014001400080", 20),
                   "xs20_02llmzojc221": ("030002620195005500560020", 20),
                   "xs20_31e88gz2egmd": ("0308020e01c1004d00560020", 20),
                   "xs20_178kkozca2ac": ("018101470048015401940018", 20),
                   "xs20_6a88bpicz033": ("006000600006007d008100ca000c", 20),
                   "xs20_39u0oka4z643": ("?-hook_siamese_long_hook_and_cis-long_boat", 20),
                   "xs20_ml96z1248a53": ("00d80154012200c10005000a000c", 20),
                   "xs20_4a9baaczx356": ("R-racetrack_II_and_?-ship", 20),
                   "xs20_32qb8n96zx11": ("?-R-bee_at_R-bee_and_table", 20),
                   "xs20_03lkm853z643": ("00c60092005c0020001c000400050003", 20),
                   "xs20_8e1mkicz3521": ("006800ae0041003600140012000c", 20),
                   "xs20_3lkiak8z3443": ("00c600a90029004e005000280010", 20),
                   "xs20_0c8al96z255d": ("?-sesquihat_at_loaf", 20),
                   "xs20_32qb8b96zx23": ("009600f50001003e002000080018", 20),
                   "xs20_25bo3qicz032": ("006800ae00410035001600400060", 20),
                   "xs20_wh7ob96z6521": ("00c000a0005100270018000b00090006", 20),
                   "xs20_0ogjlkcz4aa6": ("?-very_long_hook_siamese_eater_and_trans-R-bee", 20),
                   "xs20_ca23qicz3113": ("006c002a00220063001a0012000c", 20),
                   "xs20_3lkiegoz1243": ("00c400aa0029004e007000080018", 20),
                   "xs20_69b8b52z2552": ("0062009500d5001200d000a00040", 20),
                   "xs20_gbb88gz1pl91": ("?-very_long_R-bee_and_boat_and_block", 20),
                   "xs20_jhegmicz1221": ("0066004500390006003400240018", 20),
                   "xs20_8e1u0mp3zw23": ("00c400aa002a004b00680008000c", 20),
                   "xs20_3lkkl3z1ac01": ("018801550053005001580180", 20),
                   "xs20_caab9a4z3123": ("R-racetrack_II_and_?-snake", 20),
                   "xs20_ogiu069a4z66": ("01800180000001e001260029006a0004", 20),
                   "xs20_069baa4z3553": ("shift-cap_and_racetrack", 20),
                   "xs20_3pmkia4zw4a6": ("0180013000d20055009600a00040", 20),
                   "xs20_3lmge96z1221": ("R-bee_on_R-bee_and_ship", 20),
                   "xs20_069mgmaz4aa6": ("00a000d0001000d6012500c50002", 20),
                   "xs20_69a4ozxqb853": ("018002400140008b007a000200140018", 20),
                   "xs20_0cq2ria4z643": ("00c000a00020002c006a0041003e0008", 20),
                   "xs20_259aczca5156": ("boat_with_nine_and_?-R-mango", 20),
                   "xs20_0ogiliczcia6": ("01800258015000d200150012000c", 20),
                   "xs20_6icgf96z3421": ("00660092004c0030000f00090006", 20),
                   "xs20_gw8u156zdl91": ("01b002a001200028001e000100050006", 20),
                   "xs20_0696z359d1e8": ("010001c0002001a6012900a60060", 20),
                   "xs20_g88brz123cic": ("0180025b018b006800480030", 20),
                   "xs20_0g6p7ojdz121": ("00d80054009400a8006a00050002", 20),
                   "xs20_0ok2qb96z643": ("00c000a000200068004e0021001d0006", 20),
                   "xs20_w2egm96z6953": ("00c0012000d0001000ec008a00090006", 20),
                   "xs20_08e1ticz2553": ("004000a800ae0061001d0012000c", 20),
                   "xs20_3lk453z349go": ("dock_and_?-cis-shillelagh", 20),
                   "xs20_j5kmz11078a6": ("01980148005000de000100050006", 20),
                   "xs20_178kkmiczx66": ("00c00046005d0021001e000000180018", 20),
                   "xs20_3lmgmicz0146": ("00c000ac0069000b006800480030", 20),
                   "xs20_25aczcid1156": ("0182024501aa002c002000a000c0", 20),
                   "xs20_0g88brzc4lp1": ("?-long_R-bee_and_hook_and_block", 20),
                   "xs20_gs2araiczw32": ("?-trans-legs_siamese_loop_siamese_carrier", 20),
                   "xs20_g88bbgz178b5": ("003000e80108016b00ab0010", 20),
                   "xs20_8e1u0uh3zw23": ("00c400aa002a002b00680008000c", 20),
                   "xs20_mligoi6z1226": ("006c00aa004a000b001800480060", 20),
                   "xs20_4aabaaczx356": ("00300053005500d6005000500020", 20),
                   "xs20_3hikoz3462ac": ("018c01120096005400350003", 20),
                   "xs20_4aabaarzx321": ("006c002a0029006b002800280010", 20),
                   "xs20_oge1dicz6226": ("00d80050004e00c1000d0012000c", 20),
                   "xs20_ckggka53zca6": ("trans-long_boat_with_long_nine_and_?-ship", 20),
                   "xs20_0gilmz3ege21": ("006001d0021201d500560020", 20),
                   "xs20_4a9b8brzx321": ("006c006a0009006b004800280010", 20),
                   "xs20_39mgmiczx4a6": ("0180012000d0001200d500960060", 20),
                   "xs20_ckggrb8ozx66": ("?-long_hook_siamese_table_and_blocks", 20),
                   "xs20_069baa4zca53": ("racetrack_and_?-long_ship", 20),
                   "xs20_c82t2sgz3543": ("006c00a80082007d0002001c0010", 20),
                   "xs20_wiu0mp3z4a43": ("?-tub_with_leg_siamese_table_and_shillelagh", 20),
                   "xs20_mp3qa4ozx321": ("0034004c0060002f00290012000c", 20),
                   "xs20_cilla8ozx346": ("0030004800a800ae005100130018", 20),
                   "xs20_3lkkmz122643": ("racetrack_and_?-long_hook", 20),
                   "xs20_ckl3zw470796": ("00c0012000e0000000e300950014000c", 20),
                   "xs20_gbb88brz0123": ("006c00680008000b0069006a0004", 20),
                   "xs20_0mp3qicz1243": ("00300048005800c60099006a0004", 20),
                   "xs20_3pm4koz06943": ("0180013600d90042005c0030", 20),
                   "xs20_651u0oozc453": ("0186008500a1007e000000180018", 20),
                   "xs20_4aab8oz69d11": ("00c4012a01aa002b00280018", 20),
                   "xs20_3lk68oz0d871": ("0180015b005100ce00280030", 20),
                   "xs20_8u1v0f9z0121": ("?-very_very_long_bee_siamese_eater_and_table", 20),
                   "xs20_0mk1vg4cz643": ("?-Z-siamese_carriers_and_hook", 20),
                   "xs20_031e8gzad1dd": ("014001a3002101ae01a80010", 20),
                   "xs20_6is0si52z643": ("long_dock_and_trans-tub_with_leg", 20),
                   "xs20_0ca1ticz2553": ("004000ac00aa0061001d0012000c", 20),
                   "xs20_03lm0e93z643": ("?-eater_and_hook_and_ship", 20),
                   "xs20_2lmggz3ege21": ("011802ae01a1002e00280010", 20),
                   "xs20_6t1e8z11079c": ("0180012800ee0001003d0026", 20),
                   "xs20_69mgeioz0643": ("?-hook_on_hook_on_beehive", 20),
                   "xs20_c9baq4oz33x1": ("006c0069000b000a001a00240018", 20),
                   "xs20_4aabkk8z2553": ("004400aa00aa006b001400140008", 20),
                   "xs20_g8o696z1qq23": ("018002580188006b004b0030", 20),
                   "xs20_04a96z355d93": ("0060012601a900aa00a40060", 20),
                   "xs20_mmggm96z1w66": ("006c00680008000b006b00900060", 20),
                   "xs20_0md1eozc9611": ("0180013600cd0021002e0018", 20),
                   "xs20_0mkkm96z34a4": ("00c0012000d00052005500d2000c", 20),
                   "xs20_okihf0cczw66": ("00300030000000f0008b004b00280018", 20),
                   "xs20_2lmggz1qaa43": ("011002ab01aa002a00240018", 20),
                   "xs20_025aczad1d96": ("014001a2002501aa012c00c0", 20),
                   "xs20_178bb871zw33": ("00db005a0042003c000000300030", 20),
                   "xs20_31e8zoid1156": ("0303024101ae0028002000a000c0", 20),
                   "xs20_2ll6o8goz643": ("?-R-bee_on_snake_and_hook", 20),
                   "xs20_8e1u0uiz0643": ("004800780000007e008100730010", 20),
                   "xs20_0cc0fpz69d11": ("013001e80008006b00690006", 20),
                   "xs20_3lkid96z3201": ("0066004900350006003800480060", 20),
                   "xs20_354kl3zcip01": ("cis-shillelagh_and_?-C", 20),
                   "xs20_2lmgmicz1226": ("004400aa006a000b006800480030", 20),
                   "xs20_wgie0ehrz643": ("0180015800500150018c000400050003", 20),
                   "xs20_g8e1dmz011dd": ("00d0016b010b00e800280010", 20),
                   "xs20_oie0e96z6226": ("?-R-bee_and_hook_and_table", 20),
                   "xs20_cc0ci52z355d": ("008001400090006b000a006a006c", 20),
                   "xs20_69e0okcz2553": ("?-R-bee_on_ship_and_R-bee", 20),
                   "xs20_gj1u0ooz6943": ("00d001330081007e000000180018", 20),
                   "xs20_8e1dagz17871": ("002800ee0101016e00a80010", 20),
                   "xs20_2lm0uicz1243": ("?-cap_on_loaf_and_boat", 20),
                   "xs20_69eg6qz4a611": ("00c2012500e6001800c800b0", 20),
                   "xs20_wkq23qicz643": ("018001400040006600250041003e0008", 20),
                   "xs20_0o8bliczc453": ("?-boat_with_cis-tail_siamese_loaf_at_eater", 20),
                   "xs20_69egm96z0643": ("?-R-bee_on_eater_on_beehive", 20),
                   "xs20_178bb8oz0653": ("008000e3001500d600d000100018", 20),
                   "xs20_354mkk8zca52": ("0183014500a40056001400140008", 20),
                   "xs20_8ehmkk8z3146": ("0068002e009100d6001400140008", 20),
                   "xs20_oimge96z6221": ("00d8005200560030000e00090006", 20),
                   "xs20_caajkkozw346": ("00300050005600c9002b00280018", 20),
                   "xs20_8o0uh3z34aa6": ("0180011600f500050032002c", 20),
                   "xs20_25is0sicz643": ("00c200850072001c0000001c0012000c", 20),
                   "xs20_09f0sicz6513": ("?-R-bee_on_hook_and_table", 20),
                   "xs20_39mgeiczx346": ("00c000900068000e0071004b0030", 20),
                   "xs20_4a9ba96zw696": ("00c0012000a601a9012600a00040", 20),
                   "xs20_4a9b8brzx311": ("006c006a000a006b004800280010", 20),
                   "xs20_gbb88brz0113": ("006c00680008000b006a006a0004", 20),
                   "xs20_69egeicz0643": ("006000930071000e007000480030", 20),
                   "xs20_03pczok4d952": ("03000283009901ac012000a00040", 20),
                   "xs20_4a9b8bdzx352": ("00b000d2001500d6009000500020", 20),
                   "xs20_69e0mqz03543": ("0060009600750001006e0058", 20),
                   "xs20_4a9b8b96zx33": ("?20?001", 20),
                   "xs20_65lmzw14b871": ("?20?034", 20),
                   "xs20_69e0ok8z6953": ("?20?069", 20),
                   "xs20_gbaacz11dik8": ("?20?108", 20),
                   "xs20_35aczw319lic": ("?20?109", 20),
                   "xs20_35is0ca6zx346": ("?-boat_with_leg_siamese_eater_and_ship", 20),
                   "xs20_0354miczca243": ("018001430045008400760012000c", 20),
                   "xs20_25a8czx69d1e8": ("G_and_para-tub_with_leg", 20),
                   "xs20_2lmggkcz32w66": ("006200550016001000d000d4000c", 20),
                   "xs20_69ac0si6zw253": ("?-hook_on_boat_and_R-loaf", 20),
                   "xs20_gbbo312koz121": ("00d800d4000200e1012301400080", 20),
                   "xs20_gbbgf9z11w123": ("0060005300090036001000160036", 20),
                   "xs20_259m4k8z69611": ("00c2012500c90036002400140008", 20),
                   "xs20_35a88b96zx652": ("00c600a50041003e0000000800140018", 20),
                   "xs20_xokk871zca2ac": ("01b0011000e0000000380024001a00020003", 20),
                   "xs20_3lmgeicz01221": ("0060005600350005003a00240018", 20),
                   "xs20_6akggm952zw66": ("?-loaf_long_line_boat_and_trans-block", 20),
                   "xs20_wo4a96zmll8z1": ("?-loaf_with_trans-tail_on_hat", 20),
                   "xs20_ol3w8oz6a8711": ("00d80155010300e0002000280018", 20),
                   "xs20_0ggm552zrq221": ("0360035000500056002500050002", 20),
                   "xs20_6t1688gzwdd11": ("00c00170010b00cb002800280010", 20),
                   "xs20_c88b9acz06513": ("00300050009600d4001500130030", 20),
                   "xs20_0ggm952z32qic": ("01000280024601a9002b00280018", 20),
                   "xs20_39u069a4z0346": ("?-shillelagh_siamese_hook_and_loaf", 20),
                   "xs20_0oghn871z4aa4": ("010001c0002001d00112001500350002", 20),
                   "xs20_j1u08oz11079c": ("?-scorpio_siamese_dock_siamese_hook", 20),
                   "xs20_259eg8oz4aa43": ("008201450149008e007000080018", 20),
                   "xs20_3p6o8z11078a6": ("0188013800c0003e002100050006", 20),
                   "xs20_ckgo3d4kozx23": ("0030001000e30129018e00100018", 20),
                   "xs20_0j2acz345d113": ("0060009300a201aa002c00200060", 20),
                   "xs20_0ggm552z122qr": ("?-R-bee_and_long_R-bee_and_block", 20),
                   "xs20_65l688gzwdd11": ("00c00140015b00cb002800280010", 20),
                   "xs20_08kk3qicz4a43": ("00800148009400740003001a0012000c", 20),
                   "xs20_04amgm93z6521": ("?-great_snake_eater_on_boats", 20),
                   "xs20_0mll2z12269a4": ("?20?030", 20),
                   "xs20_ciabgzx123cko": ("03000280018000600050002b000a0012000c", 20),
                   "xs20_0g84q96zrq221": ("0360035000480044003a00090006", 20),
                   "xs20_25b88cz4ad113": ("cis-mirrored_cis-boat_with_long_leg", 20),
                   "xs20_0gbbo3tgz1221": ("?-bookend_and_R-mango_and_block", 20),
                   "xs20_259mggzciq221": ("?-scorpio_siamese_loaf_with_trans-tail", 20),
                   "xs20_4aabaaczw2552": ("00300052005500d5005200500020", 20),
                   "xs20_0g8ka96z1qa9o": ("trans-loaf_at_loaf_and_?-table", 20),
                   "xs20_6996kk8z03543": ("0060009600950061002e00280010", 20),
                   "xs20_031e8zcc0f913": ("?-table_siamese_table_and_eater_and_block", 20),
                   "xs20_0g8ehraa4z321": ("?-boat_with_long_tail_siamese_C_siamese_hat", 20),
                   "xs20_0ggm552z32qq1": ("01000280029001ab002b00280018", 20),
                   "xs20_0g88b96zol552": ("030002b000a800a8004b00090006", 20),
                   "xs20_660u1t6z06221": ("006000b80084007a000200630060", 20),
                   "xs20_ca1u0o8a6zx56": ("00600050001000180003007d008000500030", 20),
                   "xs20_x8u1egozca521": ("0180014000a0005000130035001400140008", 20),
                   "xs20_25akozwkq22ac": ("01800140004000580354028a00050002", 20),
                   "xs20_c88bb871z0253": ("00d800580041003f0000000c000a0004", 20),
                   "xs20_2lla84czw3453": ("004000a800ae0051001500260030", 20),
                   "xs20_4ac0si52z2553": ("006000900070000c006800aa00450002", 20),
                   "xs20_069b871z4a513": ("010001c0002c01a8012a00c50002", 20),
                   "xs20_6a88bb8ozx352": ("?-very_very_very_long_eater_and_boat_and_block", 20),
                   "xs20_2lligz32w25ac": ("long_boat_with_long_nine_and_trans-beehive", 20),
                   "xs20_3lk48a6zw3453": ("00c000a8002e0021001500560060", 20),
                   "xs20_g31e8gz19ld11": ("00300312021501d600500030", 20),
                   "xs20_3iab88gzwdd11": ("0180009000ab01ab002800280010", 20),
                   "xs20_0j9mkia4z3421": ("006000930049003600140012000a0004", 20),
                   "xs20_0g8o696zrq221": ("0360035000480058002600090006", 20),
                   "xs20_08o6hu066z643": ("018001400040005800c8002b002b0010", 20),
                   "xs20_069acz4a515ac": ("0180014000ac002a00a901460080", 20),
                   "xs20_69ligzy06b871": ("00c00120015000900016000d0001000e0008", 20),
                   "xs20_g069b8oz11d96": ("0030002001a6012900cb00080018", 20),
                   "xs20_039u0e96z2521": ("?-tub_with_leg_siamese_hook_and_trans-R-bee", 20),
                   "xs20_025acz6511dic": ("beehive_with_long_nine_and_?-long_boat", 20),
                   "xs20_wcc0si53zc871": ("0180014000ac002c0060000c000400050003", 20),
                   "xs20_wgbbo8a6z6521": ("0180014000a00048003e000100330030", 20),
                   "xs20_4a9baa4z03552": ("racetrack_II_and_?-R-bee", 20),
                   "xs20_06a88b52zca53": ("0180014600aa00680008000b00050002", 20),
                   "xs20_w8kkm952zca26": ("?-long_bee_siamese_loaf_and_hook", 20),
                   "xs20_c4o7p4oz643w1": ("00cc008400780007001900240018", 20),
                   "xs20_35akggzciq221": ("03060289014b00a800280030", 20),
                   "xs20_39e0okcz0354c": ("?20?083", 20),
                   "xs20_03p6o8a6z2552": ("0060009000600028002e001100530060", 20),
                   "xs20_354km2sgzw643": ("?-long_hook_siamese_eater_and_hook", 20),
                   "xs20_8kiabaiczx321": ("00180028004600b90082007c0010", 20),
                   "xs20_06a8c0f9z3156": ("?-hooks_and_table", 20),
                   "xs20_04aab871z4a53": ("anvil_and_?-long_boat", 20),
                   "xs20_0ca952sgz2553": ("00600090007000030072004a00240018", 20),
                   "xs20_0gbr0fhoz1221": ("?-long_hook_and_R-loaf_and_block", 20),
                   "xs20_03lkih3z696w1": ("beehive_with_long_leg_and_?-long_shillelagh", 20),
                   "xs20_354kl3zx1o9a4": ("03000280008000b002a30312000a0004", 20),
                   "xs20_ckgoge13z4aa4": ("?-hook_siamese_integral_and_beehive", 20),
                   "xs20_0gj1uge2z3443": ("?-long_eater_siamese_eater_on_pond", 20),
                   "xs20_4a9e0okczw653": ("00300028001800060075009300500020", 20),
                   "xs20_03hu0e96z6221": ("00c000430051003e0000000e00090006", 20),
                   "xs20_035a8a6z65156": ("boat_with_nine_and_?-C", 20),
                   "xs20_4a9b88a6zw653": ("006000500010001600d5009300500020", 20),
                   "xs20_6a4o79icz0321": ("?-boat_with_nine_on_R-mango", 20),
                   "xs20_35a88czca5113": ("0183014500aa00280028006c", 20),
                   "xs20_g88ci96z11dl8": ("?-long_R-bee_siamese_mango_and_boat", 20),
                   "xs20_0mligkcz32w66": ("006000560015001200d000d4000c", 20),
                   "xs20_069aczca515a4": ("boat_line_tub_and_?-R-loaf", 20),
                   "xs20_0o80gbdzc4lp1": ("02c0034000300013005500640006", 20),
                   "xs20_wraarz321w123": ("00c300a50024003c0000003c0024", 20),
                   "xs20_0gjlkmicz32w1": ("00c00088007e0001001d00260030", 20),
                   "xs20_8kiabaiczx311": ("00180024002a006a002b002400140008", 20),
                   "xs20_25ak8zca262ac": ("siamese_hooks_and_long_barge", 20),
                   "xs20_2596o8z8kic32": ("010202850249018600780048", 20),
                   "xs20_31e88czc87113": ("?-cis-mirrored_eater_siamese_table", 20),
                   "xs20_08kkm952z62ac": ("?-long_beehive_siamese_loaf_and_?-hook", 20),
                   "xs20_cilmggzx66074": ("00d800580040003e0001000d000a0004", 20),
                   "xs20_354s0siczw643": ("00c000a0002300390006003800480030", 20),
                   "xs20_3lm0eicz32011": ("0063005500340002003a00240018", 20),
                   "xs20_39e0mmz651101": ("00c300a9002e002000160036", 20),
                   "xs20_g8ehik8z1169c": ("0030002800ce0131019200140008", 20),
                   "xs20_gwci96zhhldz1": ("trans-mango_with_long_leg_and_?-eater", 20),
                   "xs20_0660u93z69521": ("0180012000f8000400ca00c90006", 20),
                   "xs20_gg2u0mp3z0343": ("00c000ac00280048006b000a000a0004", 20),
                   "xs20_gjligoz1w6aa4": ("?-long_Z_and_R-bee_and_boat", 20),
                   "xs20_o8allmzx12452": ("00600090004800390007003800240018", 20),
                   "xs20_0ca52z255d1e8": ("anvil_and_?-long_boat", 20),
                   "xs20_259mkk8z062ac": ("?-long_bee_siamese_loaf_and_hook", 20),
                   "xs20_0gs2qb96z6421": ("00c000a000100068002e0021001d0006", 20),
                   "xs20_69acggzx1qa96": ("01800240014000d0002b002a0012000c", 20),
                   "xs20_xmm0e952z4a43": ("?-tub_with_tail_and_R-loaf_and_block", 20),
                   "xs20_31e80uh3zx643": ("?-long_hook_siamese_eater_and_eater", 20),
                   "xs20_8e1t6zx1259a4": ("00c00120009000680008000b001a0012000c", 20),
                   "xs20_06a88a53zca53": ("0180014600aa00680008000a00050003", 20),
                   "xs20_31e88b96zx256": ("?-worm_siamese_eater_and_?-boat", 20),
                   "xs20_0ggm453z122qr": ("?-long_R-bee_and_hook_and_block", 20),
                   "xs20_w8kkm952z4aa6": ("?-long_bee_siamese_loaf_and_R-bee", 20),
                   "xs20_0ggm453z1qq23": ("?-long_R-bee_and_hook_and_block", 20),
                   "xs20_3lk462sgz1243": ("?-long_hook_siamese_eater_and_loaf", 20),
                   "xs20_0g4q9bqicz121": ("0080014000a6003d0041002e0018", 20),
                   "xs20_gilligoz1w6a4": ("?-very_long_Z_and_beehive_and_boat", 20),
                   "xs20_178c826z4a953": ("?-eater_siamese_carrier_and_R-mango", 20),
                   "xs20_652s0siczw643": ("006000a0004300390006003800480030", 20),
                   "xs20_08ehe0eicz321": ("01800140002200d5005500560020", 20),
                   "xs20_4a9baa4z03156": ("racetrack_II_and_?-hook", 20),
                   "xs20_g08o0uh3zd543": ("01b000a0008800780000001e00110003", 20),
                   "xs20_0kc0si96z3453": ("0060009400ac0060001c001200090006", 20),
                   "xs20_4a96o8a6z6511": ("00c400aa0029002600180008000a0006", 20),
                   "xs20_o8allmzx10256": ("00c000a0005600150035000a00080018", 20),
                   "xs20_0mq0si96z1243": ("006000900048003800060059006a0004", 20),
                   "xs20_ci9b88gzwdd11": ("00600090012b01ab002800280010", 20),
                   "xs20_04adhe8z35521": ("006000a400aa004d0031000e0008", 20),
                   "xs20_354kmzx123cko": ("trans-ship_on_ship and longhook", 20),
                   "xs20_069a4z8e1d952": ("?20?053", 20),
                   "xs20_xj1u0oozca611": ("?20?100", 20),
                   "xs20_651u0okczw643": ("?20?103", 20),
                   "xs20_651u0o8gzwdbw1": ("?-worm_siamese_snake_and_trans-boat", 20),
                   "xs20_25ic84k8zwdd11": ("00800140009b006b0028004800500020", 20),
                   "xs20_0cc0s93z653032": ("?-carrier_siamese_table_and_ship_and_block", 20),
                   "xs20_255m88gz4a9611": ("?-loaf_at_beehive_on_R-bee", 20),
                   "xs20_069b8oz31134a4": ("008001580088006b002900260060", 20),
                   "xs20_3pe0mmzw110252": ("00c000ac002c0060004c003200050002", 20),
                   "xs20_gbq2koz11w34a4": ("00800140009800740002001a002b0030", 20),
                   "xs20_0c88brz253w123": ("?-Z-siamese_eater_and_boat_and_block", 20),
                   "xs20_025a8cz6513156": ("00c000ac0028006a002500a200c0", 20),
                   "xs20_03iar44oz65x11": ("?-canoe_siamese_pond_on_table", 20),
                   "xs20_0bq2kl3z321011": ("0062004e00300006003400350003", 20),
                   "xs20_0gieg6p3z343w1": ("00c000ac002800480056002500050002", 20),
                   "xs20_259mggzy12fgkc": ("01800280020001e0005000100016000900050002", 20),
                   "xs20_255m88gz4aa511": ("00820145014500da002800280010", 20),
                   "xs20_0259a4oz255d11": ("004000a200a501a9002a00240018", 20),
                   "xs20_g88c2egm952z11": ("0600041803a400aa00690006", 20),
                   "xs20_0c97o4oz651221": ("00c000ac00290047005800240018", 20),
                   "xs20_8k4o0uh32aczw1": ("010002b004a30321002e0018", 20),
                   "xs20_31e8wok8zw3553": ("?-cap_on_boat_and_?-eater", 20),
                   "xs20_0ggo8hf0cicz32": ("0600040003a200d5001500120030", 20),
                   "xs20_252s0sia4zw643": ("0080014600a9002a002c001000500060", 20),
                   "xs20_25a88baa4zx253": ("0088014e0081007e0000001800280010", 20),
                   "xs20_g8k461vg352z01": ("?-tub_with_tail_on_Z_and_boat", 20),
                   "xs20_0cc0c9jz651321": ("00c8009400320006003400350003", 20),
                   "xs20_259q4oa6zw3421": ("00600093004900360014002400280010", 20),
                   "xs20_0354kl3z651221": ("dock_and_?-long_integral", 20),
                   "xs20_02lmgmicz25201": ("004000a200550016003000160012000c", 20),
                   "xs20_069a4oz3597011": ("006000a6012900ea000400380020", 20),
                   "xs20_25ic0c4ozxdd11": ("008001400090006b000b006800480030", 20),
                   "xs20_0cc0ci52z69d11": ("00c0012c01ac0020002c001200050002", 20),
                   "xs20_259aczy0315ako": ("03000280014000a00020006c000a000900050002", 20),
                   "xs20_069q48gz69a611": ("00c00126014900da002400280010", 20),
                   "xs20_4a9b88a6zw2552": ("006000500012001500d5009200500020", 20),
                   "xs20_0ml5q4oz641011": ("?-R-bee_at_R-bee_and_carrier", 20),
                   "xs20_0mm0e96z320113": ("0062004e00300006003500350002", 20),
                   "xs20_02l2s0sicz4701": ("0180008000a000560015005500a20040", 20),
                   "xs20_0rhc88gz4aa611": ("0080015b015100cc002800280010", 20),
                   "xs20_354kl3zxmdzx11": ("?-dock_and_siamese_snakes", 20),
                   "xs20_o4id2cgc453z01": ("0608041403aa00a900450002", 20),
                   "xs20_ci9b8ozw1134a4": ("0080014000980068002b00290012000c", 20),
                   "xs20_31e88cik8zx253": ("01800144004a00790006001800280010", 20),
                   "xs20_025a8czca23156": ("tub_with_leg_and_?-eater_siamese_hook", 20),
                   "xs20_0259a4oz8kid11": ("01000282024501a9002a00240018", 20),
                   "xs20_252s0gzxol54ko": ("03000280008000b002a0031c000200050002", 20),
                   "xs20_0g069a4zold113": ("?-Z_and_loaf_and_ship", 20),
                   "xs20_0c84kl3zc97011": ("0180015800580040002e00690003", 20),
                   "xs20_g6t1688628cz11": ("0600050001330349024c0180", 20),
                   "xs20_ckgiljgzx1w652": ("00c001400088007e0001001300280030", 20),
                   "xs20_0ogkai3z4a6065": ("0180009a00a60050001600350002", 20),
                   "xs20_0ojb88gz4aa611": ("00800158015300cb002800280010", 20),
                   "xs20_628c88b96zx253": ("?-worm_siamese_carrier_and_boat", 20),
                   "xs20_0354kl3z8e1221": ("C_and_?-great_snake_eater", 20),
                   "xs20_25a8a6zx6515a4": ("?20?003", 20),
                   "xs20_0g04a96zold113": ("?20?081", 20),
                   "xs20_651ug8gzy234aa4": ("03000480068000a000d00010001600090006", 20),
                   "xs20_xg0g8o653z69d11": ("06000500030000c000a8001e000100050006", 20),
                   "xs20_0g8o653zhaacz11": ("0620055001480198000600050003", 20),
                   "xs20_0gilmzhaq221z01": ("022005500352005500560020", 20),
                   "xs20_xg8hf0ca4z4a611": ("?-trans-boat_with_long_leg_on_boat_and_?-boat", 20),
                   "xs20_25ic0sik8zw1252": ("0080014400aa0029004e005000280010", 20),
                   "xs20_259mggca4zw6421": ("00c0012200a500460038000800500060", 20),
                   "xs20_35iczxh1t6zw121": ("0c000a00048203450042005c0030", 20),
                   "xs20_wggm96zgba8oz11": ("0600056001500110031600090006", 20),
                   "xs20_25akgo4ozwca221": ("0080014000a300550014003400480030", 20),
                   "xs20_31eg8gzy023ciic": ("03000280008000a0005000100036000900090006", 20),
                   "xs20_0g6t1642ak8z121": ("020005000282008501b2012c00c0", 20),
                   "xs20_69a4ozg0s453z11": ("?-loaf_with_trans-tail_siamese_elevener", 20),
                   "xs20_0c93z255ll2zx11": ("?-very_long_bee_and_carrier_and_block", 20),
                   "xs20_cia40v1o8gozy21": ("00600026002905a506a20040", 20),
                   "xs20_039u0o4oz4a43w1": ("?-tub_with_long_leg_siamese_hook_and_beehive", 20),
                   "xs20_255mg6246zw1243": ("?-R-bee_and_loaf_and_snake", 20),
                   "xs20_25akgozg8ka26z01": ("02020505028a0154005000d8", 20),
                   "xs20_32qcy0ok8zx12453": ("?-boat_on_cis-shillelagh_siamese_eater", 20),
                   "xs20_069aczg8o6513z01": ("?20?102", 20),
                   "xs20_ca2s0g88a52zx1221": ("02000506020901cb002800480030", 20),
                   "xs20_y1g8o653zg8o65z11": ("ship_on_canoe_on_ship", 20),
                   "xs21_69b8b96zw696": ("?21?018", 11),
                   "xs21_699e0okczw653": ("?21?003", 12),
                   "xs21_oe1v0rrz011": ("?21?021", 13),
                   "xs21_39u0ehrz321": ("?21?001", 13),
                   "xs21_g88rbgn96z11": ("?21?023", 13),
                   "xs21_gbb8b96z11w33": ("?21?035", 13),
                   "xs21_6a88bbgzw255d": ("?21?009", 13),
                   "xs21_4a9m88gzcia521": ("triloaf_I", 13),
                   "xs21_04s0ci53zc97011": ("[[?21?076]]", 13),
                   "xs21_gbbo7picz11": ("?21?010", 14),
                   "xs21_c88mlicz3543": ("?-G_siamese_boat_with_bend_tail", 14),
                   "xs21_69acz6511d96": ("?21?034", 14),
                   "xs21_mmge996z1243": ("?21?039", 14),
                   "xs21_0mmgu156z346": ("?21?051", 14),
                   "xs21_c8a52z355d96": ("?21?069", 14),
                   "xs21_o8b9aczx359a4": ("00800140012c00aa0069000b00080018", 14),
                   "xs21_03lkkl3zc96w1": ("?21?031", 14),
                   "xs21_2lla8cz643033": ("00c200950075000a0068006c", 14),
                   "xs21_0g8e1eoz6b871": ("?21?002", 14),
                   "xs21_699eg8oz0359c": ("?21?058", 14),
                   "xs21_354m88gzcia521": ("?21?072", 14),
                   "xs21_69b88a6z033033": ("?21?033", 14),
                   "xs21_ca1t2sgz3543": ("?-amoeba_10,6,4", 15),
                   "xs21_0mlhe0e96z32": ("?21?052", 15),
                   "xs21_69b8bb8ozx33": ("?21?040", 15),
                   "xs21_2llmz12269ic": ("?21?013", 15),
                   "xs21_c88bbgz311dd": ("?21?030", 15),
                   "xs21_oo0e9jz6a871": ("?21?042", 15),
                   "xs21_354mgmiczw346": ("?21?022", 15),
                   "xs21_0ggciqb96z343": ("?-R-bee_on_paperclip", 15),
                   "xs21_3lkmk46z32w23": ("long_and_cis-dock", 15),
                   "xs21_0cc0si96z6953": ("?21?045", 15),
                   "xs21_0ca96z6511d96": ("cis-R-loaf_and_long_worm", 15),
                   "xs21_8o6p3qicz0123": ("?21?068", 15),
                   "xs21_69ak8gzcie1221": ("?21?017", 15),
                   "xs21_255m88gzcia521": ("?21?032", 15),
                   "xs21_ca9b8brzw33": ("006c006a0001007f0040000c000c", 16),
                   "xs21_69b8brz2552": ("?21?050", 16),
                   "xs21_4a9baa4z6953": ("racetrack_II_and_?-R-loaf", 16),
                   "xs21_69acz69d1156": ("?21?053", 16),
                   "xs21_0mlhu066z346": ("006000a0008000780008006b004b0030", 16),
                   "xs21_8e1t2sgz3543": ("?21?025", 16),
                   "xs21_6996kk8z6953": ("00c60129012a00cc005000500020", 16),
                   "xs21_xrhe0eicz253": ("C_on_boat_and_cis-R-bee", 16),
                   "xs21_69ab8b96zx33": ("?21?008", 16),
                   "xs21_4aabaa4z6953": ("00c4012a00aa006b000a000a0004", 16),
                   "xs21_0mlhu0ooz346": ("?21?047", 16),
                   "xs21_69baik8z2553": ("?21?073", 16),
                   "xs21_0iu0ep3z34611": ("?21?024", 16),
                   "xs21_69b8bbgzw6511": ("0060009000d3001500d400d40008", 16),
                   "xs21_3lkkl3z32w252": ("?21?019", 16),
                   "xs21_4a9b8b96zw253": ("?21?046", 16),
                   "xs21_0ca96z69d1156": ("?21?012", 16),
                   "xs21_g88e1ege1e8z11": ("?21?071", 16),
                   "xs21_0259acz6513156": ("long_dock_and_cis-R-mango", 16),
                   "xs21_39eg88gzcia521": ("?21?015", 16),
                   "xs21_69ak8gzx122dik8": ("triloaf_II", 16),
                   "xs21_69b8brz653": ("00d800d0001000d600950063", 17),
                   "xs21_mlhe0ehrz1": ("G_and_cis-C", 17),
                   "xs21_ca9bojdz33": ("?21?027", 17),
                   "xs21_259e0ehu0oo": ("[[?21?078]]", 17),
                   "xs21_69acz69d553": ("R-racetrack_and_?-R-loaf", 17),
                   "xs21_rq1t6zx3453": ("?-shillelagh_siamese_worm_and_block", 17),
                   "xs21_6a88brz6996": ("?21?055", 17),
                   "xs21_xrhe0eioz253": ("C_on_boat_and_?-hook", 17),
                   "xs21_3lkmioz122ac": ("01880154005400d500930030", 17),
                   "xs21_cimgm96z4aa4": ("00c0012000d0001200d500950062", 17),
                   "xs21_xrhe0e96z253": ("?21?048", 17),
                   "xs21_0mlhe0eicz32": ("0180010000e2001500d500960060", 17),
                   "xs21_3lmggz1qaa43": ("031002ab01aa002a00240018", 17),
                   "xs21_2lligz12ege3": ("011002a802ae0121002e0018", 17),
                   "xs21_0mlhe0e93z32": ("018c0152005600d0000e00010003", 17),
                   "xs21_ca9b8oz359a4": ("006c00aa012901a500220030", 17),
                   "xs21_ad1e8gz5b871": ("?21?037", 17),
                   "xs21_bd0mkk8z3543": ("00d600b50001006e002800280010", 17),
                   "xs21_69b8f1e8z033": ("?-R-G-siamese_eater_and_trans-block", 17),
                   "xs21_gbb8b96z1253": ("?21?028", 17),
                   "xs21_g88ci96z19ll8": ("?-long_R-bee_siamese_mango_and_cis-beehive", 17),
                   "xs21_j1u0mmz11w346": ("?21?061", 17),
                   "xs21_4a9egmiczw652": ("003000480068000a0075009300500020", 17),
                   "xs21_069iczciq22ac": ("cis-mango_and_long_worm", 17),
                   "xs21_4s3pcz11078a6": ("?-worm_siamese_carrier_on_table", 17),
                   "xs21_xml1egoz66074": ("?21?038", 17),
                   "xs21_03lkkl3z696w1": ("beehive_with_long_leg_and_cis-dock", 17),
                   "xs21_6996z65115ak8": ("trans-barge_with_long_nine_and_trans-pond", 17),
                   "xs21_ca9d2sgz02553": ("?-mango_with_cis-tail_siamese_table_on_R-bee", 17),
                   "xs21_4a9b8b96zx352": ("006c00aa0081007e0000001800280010", 17),
                   "xs21_6t1e88gzwdd11": ("00c00170010b00eb002800280010", 17),
                   "xs21_39mgmicz04aa4": ("0180012200d5001500d200900060", 17),
                   "xs21_0mmgml3z346w1": ("?-worm_and_ship_and_block", 17),
                   "xs21_j1u0uiz11w346": ("long_and_trans-dock", 17),
                   "xs21_259egmiczw643": ("0060009600550031000e000800280030", 17),
                   "xs21_4a9baa4z033033": ("racetrack_II_and_blocks", 17),
                   "xs21_35ic0c4ozxdd11": ("018001400090006b000b006800480030", 17),
                   "xs21_4aab88gz255d11": ("004400aa00aa01ab002800280010", 17),
                   "xs21_0gill2z32w69ic": ("mango_with_long_nine_and_cis-beehive", 17),
                   "xs21_3hu0o4ozc87011": ("?21?006", 17),
                   "xs21_69ic0c4ozxdd11": ("00c001200090006b000b006800480030", 17),
                   "xs21_35a8c4oz069d11": ("?-big_S_siamese_boat_with_leg", 17),
                   "xs21_0gjl46z32023ck8": ("C_on_boat_and_?-hook", 17),
                   "xs21_256o8gzx6430eio": ("boat_on_C_and_?-hook", 17),
                   "xs21_2llmz3ege3": ("?21?059", 18),
                   "xs21_354pb8r9a4": ("036c022a0181007e0048", 18),
                   "xs21_mkkmhrz1246": ("00d80088006b0029002a006c", 18),
                   "xs21_g8e1t6z19ld": ("018002e0021601d500520030", 18),
                   "xs21_rr0v9zx34a4": ("?-tub_with_long_leg_siamese_table_and_trans-blocks", 18),
                   "xs21_5b8b96z6996": ("014601a9002901a6012000c0", 18),
                   "xs21_3pmz4aaq2sg": ("?21?060", 18),
                   "xs21_8e1v0rrzw23": ("006c006c0000007f004100380008", 18),
                   "xs21_0mmgehrz1243": ("00d800880070000e0069006a0004", 18),
                   "xs21_xrhe0e93z253": ("?-C_on_boat_and_hook", 18),
                   "xs21_35aczcid1156": ("beehive_with_long_nine_and_?-long_ship", 18),
                   "xs21_g88r3on96z11": ("?-R-bee_siamese_boat_and_hook_and_block", 18),
                   "xs21_c88b96z330f9": ("?-worm_and_table_and_block", 18),
                   "xs21_xc9bqicz6513": ("0180012000e00006003d0021000e0018", 18),
                   "xs21_6t1e8zwdd113": ("00c00170010b00eb00280008000c", 18),
                   "xs21_8e1daz311d96": ("worm_and_cis-loop", 18),
                   "xs21_4aab9a4z6953": ("racetrack_II_and_?-R-loaf", 18),
                   "xs21_6is0si96z643": ("?21?056", 18),
                   "xs21_ad1mkk8z3543": ("006a00ad00810076001400140008", 18),
                   "xs21_ca9lmz330343": ("?-mango_siamese_bookend_on_R-bee_and_block", 18),
                   "xs21_o81v0rrz0123": ("006c006c0000007f0041000a000c", 18),
                   "xs21_03lk453zo9a43": ("dock_and_?-loaf_with_cis-tail", 18),
                   "xs21_04aab871zca53": ("anvil_and_?-long_ship", 18),
                   "xs21_069b871z4a953": ("G_and_cis-R-mango", 18),
                   "xs21_039u0e96z6521": ("?-boat_with_leg_siamese_hook_and_?-R-bee", 18),
                   "xs21_g88r3ob96z121": ("00d80158010000ee002900050002", 18),
                   "xs21_39c0ccz69d113": ("?-worm_and_carrier_and_block", 18),
                   "xs21_0ca96z255d952": ("racetrack_II_and_?-R-loaf", 18),
                   "xs21_69b8b9czw2552": ("0060009000d2001500d500920030", 18),
                   "xs21_178b96zx65156": ("G_and_shift_C", 18),
                   "xs21_2lm0e93zw3453": ("00c0009600750001006e00a80040", 18),
                   "xs21_g84q952z178b6": ("00800140012600bd0041002e0018", 18),
                   "xs21_xj1u0ooz69d11": ("00c00140010000f0002b000b000800280030", 18),
                   "xs21_259e0uiz02553": ("?-R-bee_on_table_and_R-loaf", 18),
                   "xs21_255mgmiczw346": ("big_S_and_R-bee", 18),
                   "xs21_69a4z6511dik8": ("trans-loaf_with_long_nine_and_?-loaf", 18),
                   "xs21_xj1u066z69d11": ("00c00140010000f000280008000b002b0030", 18),
                   "xs21_6a8c88brzw253": ("00d800d0001000160035001200500060", 18),
                   "xs21_252s0sicz3543": ("006200a50082007c0000001c0012000c", 18),
                   "xs21_cimgm952z06a4": ("00800140012000d0001200d500960060", 18),
                   "xs21_0ca1u0ooz255d": ("004000ac00aa01a1001e000000180018", 18),
                   "xs21_69mgmicz04aa4": ("00c0012200d5001500d200900060", 18),
                   "xs21_3lkm96z320123": ("006600490036001400550063", 18),
                   "xs21_gj1u0ooz11078c": ("00300033000100fe010001980018", 18),
                   "xs21_6t168ozw1134ac": ("018001400098006800260021001d0006", 18),
                   "xs21_69e0o4oz259701": ("00c4012a00e9000e003000480030", 18),
                   "xs21_354km453zw3443": ("?-hook_siamese_long_hook_and_pond", 18),
                   "xs21_0ggml3z32w69ic": ("mango_with_long_nine_and_ortho-ship", 18),
                   "xs21_g8g0gbdz12pgf2": ("02c00348003e0001003300480030", 18),
                   "xs21_69b88gzx321eic": ("?-big_S_on_R-bee", 18),
                   "xs21_0caakl3z651221": ("?-long_integral_siamese_beehive_on_long_integral", 18),
                   "xs21_062s0si52z3543": ("long_worm_and_?-tub_with_leg", 18),
                   "xs21_651u0ok8zw178c": ("?-worm_siamese_eater_and_boat", 18),
                   "xs21_4aab88a6zw6952": ("00c000a00024002a01a900a600a00040", 18),
                   "xs21_256o8gzxol54ko": ("?21?020", 18),
                   "xs21_025a8cz69d1156": ("long_worm_and_?-tub_with_leg", 18),
                   "xs21_4aabaa4z033033": ("003600360000003e0041003e0008", 18),
                   "xs21_xm2s079cz4a611": ("?-hook_and_boat_on_C", 18),
                   "xs21_651u08kk8zw39c": ("?-worm_siamese_carrier_and_beehive", 18),
                   "xs21_0696z355ll2zx11": ("?-beehive_and_very_long_R-bee_and_block", 18),
                   "xs21_256o8g0siczx643": ("boat_on_C_and_para-R-bee", 18),
                   "xs21_4a960u1u066zy21": ("?-loaf_and_very_long_beehive_and_block", 18),
                   "xs21_356o8gzy023ciic": ("?-pond_on_hook_on_ship", 18),
                   "xs21_25960u1u0oozy21": ("?-very_long_bee_and_loaf_and_block", 18),
                   "xs21_256o8gzx6430eic": ("boat_on_C_and_?-R-bee", 18),
                   "xs21_256o8g0si6zx643": ("?-hook_and_boat_on_C", 18),
                   "xs21_wgj1u0og4cz25421": ("mango_with_long_nine_and_?-carrier", 18),
                   "xs21_rahv0rr": ("006d006b0008006b006d", 19),
                   "xs21_65pabob96": ("00d60159010300fc0024", 19),
                   "xs21_69ar2qj96": ("00ca017d010100ae0068", 19),
                   "xs21_33gv1qb96": ("01b601ad0021002e0068", 19),
                   "xs21_39e0ehraa4": ("?-C_siamese_hat_and_hook", 19),
                   "xs21_3lmgm96z346": ("00c600a9006b0008006800900060", 19),
                   "xs21_2530fhe0e96": ("?-long_R-bee_and_R-bee_and_boat", 19),
                   "xs21_259e0ehf033": ("?-R-loaf_and_long_R-bee_and_block", 19),
                   "xs21_caab8brzw33": ("?-very_long_Z_siamese_eater_and_blocks", 19),
                   "xs21_39u0mp3z643": ("?-hook_siamese_long_hook_and_shillelagh", 19),
                   "xs21_69ngn96z321": ("0066004900370010001700090006", 19),
                   "xs21_6996z69d1da": ("014001a0002601a9012900c6", 19),
                   "xs21_o8br0rrzw23": ("?-siamese_tables_and_3_blocks", 19),
                   "xs21_259e0ehf0cc": ("?-long_R-bee_and_R-loaf_and_block", 19),
                   "xs21_6996z69d596": ("00c6012901a900a6012000c0", 19),
                   "xs21_okiqb96z6a4": ("00d801540092001a000b00090006", 19),
                   "xs21_g39czdd1dio": ("0300024001ac002901a301b0", 19),
                   "xs21_c9b8brz0696": ("?-long_Z_siamese_carrier_and_beehive_and_block", 19),
                   "xs21_cimgm96zca6": ("018c015200d60010001600090006", 19),
                   "xs21_3lkiegoz3443": ("?-R-pond_on_shillelagh_siamese_eater", 19),
                   "xs21_69ab8brzx311": ("006c006a000a006b002800480030", 19),
                   "xs21_mkkl3z122696": ("?-long_R-bee_siamese_beehive_and_long_hook", 19),
                   "xs21_178b96z4a953": ("?21?026", 19),
                   "xs21_69b8bp46z033": ("006c00a90083007c000400600060", 19),
                   "xs21_wbq1ticz4a43": ("00800140008b007a0001001d0012000c", 19),
                   "xs21_6t1e8gz17871": ("00c8017e010100ee00280010", 19),
                   "xs21_4aab871z6996": ("anvil_and_trans-pond", 19),
                   "xs21_c88e1fgkcz33": ("01800180000601e9012b00280018", 19),
                   "xs21_31egmicz4aa6": ("0182010500e5001600d000900060", 19),
                   "xs21_9f032acz3553": ("?-eater_and_table_and_cap", 19),
                   "xs21_0db8b96z2553": ("?-worm_siamese_snake_and_?-R-bee", 19),
                   "xs21_2lligz1qaa43": ("011002ab02aa012a00240018", 19),
                   "xs21_og88brz6a871": ("01b001a8002e002100150036", 19),
                   "xs21_c88gehrz3543": ("?-G_on_C", 19),
                   "xs21_ca9e0eik8z33": ("?-loaf_siamese_table_and_R-loaf_and_block", 19),
                   "xs21_3lmge96z3421": ("?-R-loaf_on_R-bee_and_ship", 19),
                   "xs21_gbbo3qicz121": ("0068006e00010075009600a00040", 19),
                   "xs21_c4o1vg33z643": ("Z_and_dock_and_block", 19),
                   "xs21_ciiriiczw4ac": ("00600090009301b5009200900060", 19),
                   "xs21_0c88brz69l91": ("036003500052005500d2000c", 19),
                   "xs21_2lmgeioz3443": ("?-R-pond_on_hook_and_boat", 19),
                   "xs21_3lk453z34a96": ("dock_and_cis-loaf_siamese_loaf", 19),
                   "xs21_3jgf9a4z3443": ("?-pond_on_loaf_siamese_table_and_block", 19),
                   "xs21_ciar0rdzx321": ("?-snake_siamese_eater_on_loop", 19),
                   "xs21_2llmz122dkk8": ("?-R-bee_on_R-bee_and_R-bee", 19),
                   "xs21_caajkk8z3543": ("006c00aa008a0073001400140008", 19),
                   "xs21_4aab88brzx33": ("00c800ce000100fe008000180018", 19),
                   "xs21_3lkkl3z32w65": ("00c600aa0028002800ab00c5", 19),
                   "xs21_0178brz69d11": ("?-scorpio_siamese_trans-legs_and_block", 19),
                   "xs21_3lmgmmz346w1": ("?-worm_and_ship_and_block", 19),
                   "xs21_8e1t2koz3543": ("006800ae0081007d000200140018", 19),
                   "xs21_caarz3303453": ("006c006a000a007b008000a00060", 19),
                   "xs21_069acz355d96": ("R-racetrack_and_para-R-loaf", 19),
                   "xs21_okkmgm96zw66": ("0060009000680008006b002b00280018", 19),
                   "xs21_cimgm93z4aa4": ("?21?065", 19),
                   "xs21_g88ml96zd543": ("01b000a800880076001500090006", 19),
                   "xs21_0okkmp3zca26": ("?-shillelagh_siamese_long_R-bee_and_hook", 19),
                   "xs21_4amgehrz0643": ("?-boat_on_hook_on_C", 19),
                   "xs21_4a9bqicz039c": ("0060009000b001a3012900ac0040", 19),
                   "xs21_c9baacz33w33": ("R-iron_and_blocks", 19),
                   "xs21_4aab8b96zw253": ("006800ae0081007e0000001800140008", 19),
                   "xs21_069b871z359a4": ("G_and_?-R-mango", 19),
                   "xs21_0gbbo3qicz121": ("00800140009600750001006e0068", 19),
                   "xs21_g88bbgz122rq1": ("mirror_and_?-blocks", 19),
                   "xs21_69acz651164ko": ("03000280008000c0002c002a00a900c6", 19),
                   "xs21_xoie0e952z653": ("hook_on_ship_and_?-R-loaf", 19),
                   "xs21_069baiczc8711": ("0180010600e9002b002a0012000c", 19),
                   "xs21_651u0eicz2521": ("006200a50082007c0000007000480030", 19),
                   "xs21_069a4zcil9156": ("cis-loaf_with_long_nine_and_?-loaf", 19),
                   "xs21_4ac0si96z2553": ("?-R-mango_on_R-bee_and_boat", 19),
                   "xs21_0g4s0si96z3kp": ("01800240012000e0000000e0009300250018", 19),
                   "xs21_0g6p3sj96z121": ("00d80154012400a8006a00050002", 19),
                   "xs21_gbb88a6z12596": ("00c000a00026002901aa01a40018", 19),
                   "xs21_g88ge93z178b6": ("?-paperclip_on_hook", 19),
                   "xs21_gbaab96z11w33": ("0032005e0040003e000100330030", 19),
                   "xs21_0caab871z2553": ("R-anvil_and_?-R-bee", 19),
                   "xs21_4s0v9z11078a6": ("?-worm_siamese_table_and_table", 19),
                   "xs21_2lligz32w69ic": ("mango_with_long_nine_and_trans-beehive", 19),
                   "xs21_2596o696zx39c": ("00c0012000c3003900cc012001400080", 19),
                   "xs21_69baik8z0354c": ("00c0012c01aa00a2009300500020", 19),
                   "xs21_0g8e1t6z8ld11": ("018002e0021001d0005600350002", 19),
                   "xs21_2lla8cz343033": ("006c0068000a007500950062", 19),
                   "xs21_0ckggm96zoka6": ("beehive_with_long_nine_and_?-long_ship", 19),
                   "xs21_g88bbgz123qq1": ("mirror_and_?-blocks", 19),
                   "xs21_178b9acz02553": ("008000e2001500d5009600500030", 19),
                   "xs21_0o44m93z178b6": ("0180012000d6004d0041003e0008", 19),
                   "xs21_8u1j4k8zc9611": ("0188013e00c10033002400140008", 19),
                   "xs21_2lla8a6zw3453": ("006000560015005100ae00a80040", 19),
                   "xs21_g88baicz1255d": ("0060009000ab01aa002a00240018", 19),
                   "xs21_cid1e8gzw11dd": ("006000900168010800eb002b0010", 19),
                   "xs21_0mlhege2z1243": ("0040007000080070008e00a9006a0004", 19),
                   "xs21_g88bbgz1qq321": ("mirror_and_?-blocks", 19),
                   "xs21_3lmgmicz01w66": ("00c000ac00680008006b004b0030", 19),
                   "xs21_0178b96z65156": ("G_and_?-C", 19),
                   "xs21_178baacz02553": ("R-anvil_and_?-R-bee", 19),
                   "xs21_4ac0si96z6513": ("?-R-mango_on_hook_and_boat", 19),
                   "xs21_0g6p7ob96z121": ("00d80154011400e8002a00050002", 19),
                   "xs21_3lmggkcz32w66": ("00c600aa00680008000b002b0030", 19),
                   "xs21_69b88gzciq321": ("01860249034b006800480030", 19),
                   "xs21_256o8gzx643si6": ("?-hook_on_C_on_boat", 19),
                   "xs21_069b88a6z4a513": ("long_worm_and_?-tub_with_leg", 19),
                   "xs21_069mggz8kic543": ("010002860249019600b000900060", 19),
                   "xs21_g8o0uhe0e96z01": ("?-long_R-bee_and_R-bee_and_boat", 19),
                   "xs21_39eg88b96zx123": ("?-hook_on_big_S", 19),
                   "xs21_39e0o4ozc97011": ("0183012900ee0000003800480030", 19),
                   "xs21_0cc0ci96z69d11": ("00c0012c01ac0020002c001200090006", 19),
                   "xs21_256o8geiozx643": ("?-C_on_hook_on_boat", 19),
                   "xs21_3hu0o4czc87011": ("?-long_hook_siamese_long_hook_and_hook", 19),
                   "xs21_0312kozgs2qaa4": ("0200038300410342015401580080", 19),
                   "xs21_39e0o4oz259701": ("0184012a00e9000e003000480030", 19),
                   "xs21_25a8ciicz02553": ("?-tub_with_leg_siamese_pond_on_R-bee", 19),
                   "xs21_39e0o4czc97011": ("?-hook_and_hook_and_hook", 19),
                   "xs21_352s0sia4zw643": ("0180014600a9002a002c001000500060", 19),
                   "xs21_39u0o4oz0c9611": ("?21?062", 19),
                   "xs21_0ca9lmz6511023": ("00c000ac002a0029001500560060", 19),
                   "xs21_08e1mkicz25521": ("006000900068000e0061002d002a0010", 19),
                   "xs21_255q48gz69a511": ("00c20125014500ba002400280010", 19),
                   "xs21_31egogkczw4aic": ("?-integral_siamese_eater_and_loaf", 19),
                   "xs21_0696k4oz8kid11": ("01000286024901a6003400240018", 19),
                   "xs21_35a8c8a6zw3552": ("?-boat_with_leg_siamese_hook_and_?-R-bee", 19),
                   "xs21_35ic84k8zwdd11": ("01800140009b006b0028004800500020", 19),
                   "xs21_035s26z3543033": ("006000a30085007c000200660060", 19),
                   "xs21_354m88b96zx123": ("?-big_S_on_hook", 19),
                   "xs21_25akggkczwciic": ("trans-barge_with_long_nine_and_cis-pond", 19),
                   "xs21_04a9mge2z4aa43": ("00800144014a008900760010000e0002", 19),
                   "xs21_69ic0c4ozx11dd": ("00c00120009000680008006b004b0030", 19),
                   "xs21_69icwck8zxdd11": ("?-mango_long_line_boat_and_cis-block", 19),
                   "xs21_cc0si52z330346": ("?-tub_with_leg_siamese_hook_and_blocks", 19),
                   "xs21_031e88gz6511dd": ("00c000a30021002e01a801a80010", 19),
                   "xs21_08e1qczc970123": ("0180012800ee0001003a004c0060", 19),
                   "xs21_259q3q952zx121": ("00d601390082006c002800280010", 19),
                   "xs21_g8o0ehf0ck8z121": ("?-long_R-bee_and_R-bee_and_block", 19),
                   "xs21_25960u1u066zy21": ("031004ab02ab012800280010", 19),
                   "xs21_4a960u1u0oozy21": ("?-loaf_and_very_long_beehive_and_block", 19),
                   "xs21_0696z3ll552z011": ("?-very_long_R-bee_and_beehive_and_block", 19),
                   "xs21_0ggmligkcz346w1": ("?-worm_siamese_eater_and_boat", 19),
                   "xs21_259akggzy01023cko": ("?-ship_on_hook_on_mango", 19),
                   "xs21_64pbaqb96": ("00cc0179010300fc0024", 20),
                   "xs21_69argbqic": ("00d8016e010100ed002a", 20),
                   "xs21_354djobjo": ("01b6011600e0002d001b", 20),
                   "xs21_69ar2qb96": ("00ca017d010100ee0028", 20),
                   "xs21_32qr2qj96": ("012601fd0001006a006c", 20),
                   "xs21_5b8r3ob96": ("01b600b5010100ee0028", 20),
                   "xs21_651uge1dic": ("018c0252035500550062", 20),
                   "xs21_69baarz653": ("00d80050005000d600950063", 20),
                   "xs21_j9araarz11": ("?-long_and_snake_siamese_table", 20),
                   "xs21_rbgn96z643": ("?-C_siamese_eater_on_R-bee_and_block", 20),
                   "xs21_4a60uhbqic": ("01b002d2021501d60060", 20),
                   "xs21_db8bqicz33": ("006d006b0008000b001a0012000c", 20),
                   "xs21_2llmz1qaip": ("?-snake_and_long_bee_and_R-bee", 20),
                   "xs21_178f1egm93": ("03630155015400d2000c", 20),
                   "xs21_0j9arz8lld": ("?-siamese_hooks_and_R-bee_and_snake", 20),
                   "xs21_69bo8go8br": ("03060305000103de0268", 20),
                   "xs21_caar9a4z39c": ("?-racetrack_II_siamese_eater_and_carrier", 20),
                   "xs21_mlhu0ooz1ac": ("00d80155011300f0000000300030", 20),
                   "xs21_caabqicz352": ("?-fourteener_siamese_Z_and_boat", 20),
                   "xs21_3pmkk8zciic": ("?-long_R-bee_siamese_shillelagh_and_cis-pond", 20),
                   "xs21_2560uhe0eic": ("02300550055603550022", 20),
                   "xs21_2llmz1iu056": ("011002a902af01a00014000c", 20),
                   "xs21_259e0eio0ui": ("?-R-loaf_and_hook_and_table", 20),
                   "xs21_c9b8ria4z33": ("00c000c0000c00fa0081002e0068", 20),
                   "xs21_4ap7ob96z32": ("00c000800028006e009100550036", 20),
                   "xs21_69b8bdz6513": ("?-worm_siamese_snake_and_?-hook", 20),
                   "xs21_mmge1fgkcz1": ("010001c6002901ab01a80018", 20),
                   "xs21_g8e1t6zdl91": ("01b002a8012e0021001d0006", 20),
                   "xs21_0db8brz2596": ("?-Z_siamese_snake_and_loaf_and_block", 20),
                   "xs21_mc1v0rrz011": ("006c0069000b006a00690006", 20),
                   "xs21_25b8brz3156": ("00d800d0001300d500a40046", 20),
                   "xs21_6996z695d96": ("00c60129012a00cb00090006", 20),
                   "xs21_69e0uiz6953": ("00c6012900ea000c00f00090", 20),
                   "xs21_3pmkkozca26": ("?-siamese_long_R-bees_siamese_shillelagh_and_?-hook", 20),
                   "xs21_3lkkm96z346": ("00c600a9002b0028006800900060", 20),
                   "xs21_2530fhe0eic": ("?-R-bee_and_long_R-bee_and_boat", 20),
                   "xs21_69riicz32ac": ("00cc012401b5009300900060", 20),
                   "xs21_cc0v1qrz311": ("006c002c0040007c0002001a001b", 20),
                   "xs21_gbbo3qp3z11": ("00d600b60000006e00690003", 20),
                   "xs21_651uge132ac": ("031804ae06a100a300c0", 20),
                   "xs21_8e1v0si6z311": ("R-anvil_and_?-hook", 20),
                   "xs21_8e1e8gz319ld": ("0068002e012102ae01a80010", 20),
                   "xs21_wmkhf033z696": ("01b001a4002c0020001c0002000500050002", 20),
                   "xs21_wcp3qicz6a43": ("00c00140008c00790003001a0012000c", 20),
                   "xs21_8e1t6zw6b853": ("006000a00106017d00c1000e0008", 20),
                   "xs21_69mgmiczw6ac": ("00c0012000d6001500d300900060", 20),
                   "xs21_2lligz34aaq1": ("011802a402aa012a002b0010", 20),
                   "xs21_3lmgmicz1226": ("00c400aa006a000b006800480030", 20),
                   "xs21_4s0v1ooz3543": ("006400bc0080007f000100180018", 20),
                   "xs21_69egmmz653w1": ("00c600a9006e001000160036", 20),
                   "xs21_4aabk46z255d": ("00c00040005001ab00aa00aa0044", 20),
                   "xs21_0h7o3qp3z321": ("00d600b400040068006a00050003", 20),
                   "xs21_354kl3z4aaq1": ("0304028a008a00ab02b00300", 20),
                   "xs21_39mgmicz0ca6": ("?21?063", 20),
                   "xs21_0gilmz12egmb": ("016002d6021501d200500020", 20),
                   "xs21_4s0f9gz5b871": ("00a4017c010000ef00290010", 20),
                   "xs21_mkiqbz10ca23": ("00d80050009300b501a4000c", 20),
                   "xs21_0mlhe0eioz32": ("0180010000e3001500d400960060", 20),
                   "xs21_2lmgm952z346": ("0062009500d600100016000900050002", 20),
                   "xs21_kq2raicz1243": ("0034005a0082007b000a0012000c", 20),
                   "xs21_69b88gz69lp1": ("018c02520355005300500020", 20),
                   "xs21_39mgmiczw6ac": ("0180012000d6001500d300900060", 20),
                   "xs21_wrb8ob96z321": ("018001400048007e000100650066", 20),
                   "xs21_4a96z6519lic": ("cis-loaf_with_long_nine_and_?-loaf", 20),
                   "xs21_69a4z6519lic": ("018c025401500092001500090006", 20),
                   "xs21_cc0v1oozca43": ("018c014c0080007f000100180018", 20),
                   "xs21_cimgm952z4a6": ("008c015200d600100016000900050002", 20),
                   "xs21_4a9b8brzw652": ("00d800d0001200d5009300500020", 20),
                   "xs21_raa4ozx6b871": ("01b000a000a00046003d0001000e0008", 20),
                   "xs21_8e1t2sgzca43": ("0188014e0081007d0002001c0010", 20),
                   "xs21_gbaab96z1253": ("0060009000d00056005500d2000c", 20),
                   "xs21_ciiria4z4aa4": ("008c01520152009b0012000a0004", 20),
                   "xs21_0gilmzbmge21": ("016002d0021201d500560020", 20),
                   "xs21_gbbgf1egoz11": ("0180012300d5001400d400d8", 20),
                   "xs21_03ia4oz2ehld": ("0060009601550131030e0008", 20),
                   "xs21_314u0uiz3543": ("?-worm_siamese_carrier_and_table", 20),
                   "xs21_06996z355d93": ("iron_and_pond", 20),
                   "xs21_g4q9bob96z11": ("01800148007e008100550036", 20),
                   "xs21_4aaba96z2553": ("00600090005000d6005500550022", 20),
                   "xs21_5b8baa4z2553": ("00a200d5001500d6005000500020", 20),
                   "xs21_651u0oozwdjo": ("?-worm_siamese_shillelagh_and_?-boat", 20),
                   "xs21_69baikozw696": ("00c0012001a600a9009600500030", 20),
                   "xs21_w9v0f96z6521": ("00c000a0005000100036001500150036", 20),
                   "xs21_gillmz1w69ko": ("03000280013600d5001500120030", 20),
                   "xs21_3pmggmiczx66": ("00c000a600250041007e000000180018", 20),
                   "xs21_3lkm2sgz3443": ("?-hook_siamese_eater_and_R-pond", 20),
                   "xs21_69f0v1oozx23": ("?-very_long_Z_and_cap_and_block", 20),
                   "xs21_0gilliczo9a6": ("03000130015200d500150012000c", 20),
                   "xs21_gbb8bq23z123": ("?-worm_and_table_and_block", 20),
                   "xs21_259acz39d552": ("iron_and_?-R-mango", 20),
                   "xs21_2lligz3ege21": ("011802ae02a1012e00280010", 20),
                   "xs21_699e0uizw653": ("0060009000930075000600780048", 20),
                   "xs21_69b8b9czx356": ("0060009000d0001600d500930030", 20),
                   "xs21_8e1qcz3543ac": ("0180014c007a008100ae0068", 20),
                   "xs21_69ab9a4z6513": ("00c600a9002a006b0009000a0004", 20),
                   "xs21_o8b94oz6b871": ("[[?21?079]]", 20),
                   "xs21_69eg6qzca611": ("?21?014", 20),
                   "xs21_35s2pmz0178c": ("01800148007e0081013300d0", 20),
                   "xs21_6996z6511dic": ("018c025402500190001600090006", 20),
                   "xs21_697o796zw343": ("?-3some_beehive_R-bees", 20),
                   "xs21_4a9fgkcz2553": ("004400aa00a9006f00100014000c", 20),
                   "xs21_696k4ozcil91": ("0186024902a6013400240018", 20),
                   "xs21_05b8b96zca53": ("0180014500ab0068000b00090006", 20),
                   "xs21_2lmgeicz3443": ("?-R-pond_on_R-bee_and_boat", 20),
                   "xs21_2lmggzdmge21": ("01a202d5021601d000500020", 20),
                   "xs21_c88ml56z3543": ("006c00a800880076001500050006", 20),
                   "xs21_0h7o7picz321": ("00c000a0005600150029002a006c", 20),
                   "xs21_09v0rbzc4521": ("01a001b8000401fa01220003", 20),
                   "xs21_g8e1eoz0d55d": ("003000eb010a00ea002b0010", 20),
                   "xs21_3lk453z34a9o": ("031802a400aa009202830300", 20),
                   "xs21_3lmgmicz1246": ("00c400aa0069000b006800480030", 20),
                   "xs21_69b8bdz03156": ("?-worm_siamese_snake_and_hook", 20),
                   "xs21_g88b96zdl913": ("01b002a80128002b00690006", 20),
                   "xs21_ogilmz66w696": ("00d800d00012001500d6012000c0", 20),
                   "xs21_ca9lmz311643": ("006c002a002900d500960060", 20),
                   "xs21_330f9gz69l91": ("030c0312001503d202500020", 20),
                   "xs21_4a9fgkcz6513": ("00c400aa0029006f00100014000c", 20),
                   "xs21_mllicz10ca26": ("00d801500153009500640006", 20),
                   "xs21_3iabaarz0123": ("?-siamese_tables_and_worm", 20),
                   "xs21_69b8brz03146": ("00d800d3001100d400960060", 20),
                   "xs21_0gilmz3egma1": ("006001d0021202d501560020", 20),
                   "xs21_ml1e8gz1255d": ("00d80154010a00ea002b0010", 20),
                   "xs21_69b8bq23z033": ("009600f50001003e002000060006", 20),
                   "xs21_0g88brzra871": ("03600350005c0042002a001b", 20),
                   "xs21_0bd0uicz2553": ("?-cap_on_R-bee_and_snake", 20),
                   "xs21_c9b8b96z3123": ("006c0029004b0068000b00090006", 20),
                   "xs21_69ngbrz06421": ("00d800d4000a00e900930060", 20),
                   "xs21_2lmggz12egmb": ("016002d0021001d600550022", 20),
                   "xs21_9f0ccz311d96": ("?-worm_and_table_and_block", 20),
                   "xs21_wmm0uh3zca43": ("?-boat_with_leg_and_long_hook_and_block", 20),
                   "xs21_259acz319l96": ("011802900252015500d2000c", 20),
                   "xs21_259a4oz319ld": ("011802900252015500960060", 20),
                   "xs21_8e1e8gzdj871": ("01a8026e010100ee00280010", 20),
                   "xs21_069b8brz3113": ("006c006a0002007c0040000f0009", 20),
                   "xs21_8e1dagz311dd": ("0068002e002101ad01aa0010", 20),
                   "xs21_4airiicz6226": ("00c4004a005200db00120012000c", 20),
                   "xs21_4aljgzcic543": ("0184024a019500b300900060", 20),
                   "xs21_8kaar2qrzw11": ("009000fc000200dd00d2000c", 20),
                   "xs21_0ml1uge2z643": ("00c000a00020006c000a006a004b0030", 20),
                   "xs21_69r88gzrq221": ("03660349005b004800280010", 20),
                   "xs21_025a4oz69lld": ("00c0012202a502aa01a40018", 20),
                   "xs21_wciqj96zca26": ("01800140004c00d2001a001300090006", 20),
                   "xs21_mllicz1w6aa4": ("00d8015001500096006500050002", 20),
                   "xs21_cc0ci96z355d": ("00c001200090006b000a006a006c", 20),
                   "xs21_3lmggz12ege3": ("031002a801ae0021002e0018", 20),
                   "xs21_g39cz1pl9156": ("?-very_very_long_eater_and_carrier_and_boat", 20),
                   "xs21_3lkicz34aik8": ("031802a400aa012900c50002", 20),
                   "xs21_ml1e8z107996": ("00d80150010e00e900290006", 20),
                   "xs21_0db8b96z6513": ("[[?21?080]]", 20),
                   "xs21_0mp3qicz3443": ("0060009600990063001a0012000c", 20),
                   "xs21_3lkl3z122696": ("?-long_bee_siamese_beehive_and_C", 20),
                   "xs21_6a88baarzx33": ("?-very_very_very_long_eater_and_table_and_block", 20),
                   "xs21_69ab9arzx321": ("006c002a0049006b002800480030", 20),
                   "xs21_69acz255dik8": ("?-long_bee_siamese_loaf_and_R-loaf", 20),
                   "xs21_69egmicz4a43": ("00c2012500e2001c00d000900060", 20),
                   "xs21_0pf0siczca43": ("01800159008f0060001c0012000c", 20),
                   "xs21_gs2u0ehrzx32": ("?-long_Z_siamese_eater_and_C", 20),
                   "xs21_69b88brzw652": ("00d800d00012001500d300900060", 20),
                   "xs21_0gilmz32qq23": ("?-siamese_very_long_R-bees_and_boat_and_block", 20),
                   "xs21_g08u156zdlkc": ("01b002a00288019e000100050006", 20),
                   "xs21_g88mliczd543": ("01b000a80088007600150012000c", 20),
                   "xs21_o4s0fpz0d871": ("013001e8000e0071004b0030", 20),
                   "xs21_08ehe8z660vi": ("00c000c8000e03f1024e0008", 20),
                   "xs21_3pmgmiczw4ac": ("0180013000d2001500d300900060", 20),
                   "xs21_8k4t3on96zw1": ("00d80150014e00a9006a0004", 20),
                   "xs21_069acz4all96": ("?21?054", 20),
                   "xs21_69abaa4z2553": ("?21?067", 20),
                   "xs21_0gbap3qicz121": ("00800140009600750001006e0058", 20),
                   "xs21_xmmge13z66074": ("01b001a0002000380004003400350003", 20),
                   "xs21_caabaicz06511": ("00300053005500d4005400480030", 20),
                   "xs21_4a96z65131ego": ("0300020001c000200066002900aa00c4", 20),
                   "xs21_69e0u2sgzw643": ("?-eater_siamese_very_long_eater_and_R-bee", 20),
                   "xs21_0g8e1t6z230f9": ("00c00170010900ef0020001c0004", 20),
                   "xs21_069b8jdz64132": ("00c000860029006b00480013000d", 20),
                   "xs21_69egeik8z0643": ("006000930071000e0070004800280010", 20),
                   "xs21_69abaaczw2552": ("00600090005200d5005500520030", 20),
                   "xs21_6996kicz03543": ("[[?21?077]]", 20),
                   "xs21_69b88bdzw2552": ("00b000d20015001500d200900060", 20),
                   "xs21_3pe0oka6z0643": ("?21?007", 20),
                   "xs21_39u0u93z03421": ("00c0009600790002007c009000c0", 20),
                   "xs21_35is0si6z0643": ("?-boat_with_leg_siamese_hook_and_?-hook", 20),
                   "xs21_660u1jgzwd543": ("00c000c0000b00fa0102019c0010", 20),
                   "xs21_0o8ge93zckgf2": ("?-fourteener_on_hook", 20),
                   "xs21_699egmiczw252": ("0060009600950071000e001000280010", 20),
                   "xs21_0cimge13z62ac": ("0180010000e0001000d3009500640006", 20),
                   "xs21_4ac0cp3z69d11": ("0180013000680008006b00a90046", 20),
                   "xs21_6t1e88gzw11dd": ("00c00170010800e8002b002b0010", 20),
                   "xs21_0ca9e0eicz253": ("?-loaf_siamese_table_and_R-bee_and_boat", 20),
                   "xs21_4a5lmzx470696": ("?-R-bee_siamese_tub_and_table_and_beehive", 20),
                   "xs21_4a960uiz65113": ("?-long_hook_on_table_and_loaf", 20),
                   "xs21_0dr0rbgz643w1": ("00c0008d007b0000001b002b0010", 20),
                   "xs21_0ca23z69d1da4": ("00c0012c01aa002201a301400080", 20),
                   "xs21_6a89fgkczw253": ("006000500012009500f6000800280030", 20),
                   "xs21_0j9a4z345dik8": ("01000280024401aa00a900930060", 20),
                   "xs21_g88bbgz19ld11": ("?-siamese_very_long_R-bees_and_boat_and_block", 20),
                   "xs21_g88ge96z178b6": ("00c0012000e6001d0021002e0018", 20),
                   "xs21_651u0ok8z3543": ("006600a50081007e0000001800280010", 20),
                   "xs21_06996z8e1d952": ("010001c6002901a9012600a00040", 20),
                   "xs21_08e1u0ooz255d": ("004000a800ae01a1001e000000180018", 20),
                   "xs21_g88bbgz11dl91": ("?-siamese_very_long_R-bees_and_boat_and_block", 20),
                   "xs21_64kmkl3z643w1": ("long_and_?-eater_siamese_table", 20),
                   "xs21_4a952z6511dio": ("0300024001a20025002900aa00c4", 20),
                   "xs21_25akgkczca2ac": ("01820145004a015401900014000c", 20),
                   "xs21_cic0f9gzw11dd": ("006000900068000801eb012b0010", 20),
                   "xs21_025acz6519lic": ("cis-loaf_with_long_nine_and_?-long_boat", 20),
                   "xs21_0mll2z122dkk8": ("?-R-bee_on_R-bee_and_R-bee", 20),
                   "xs21_31egmmz355201": ("00c600850075000a0068006c", 20),
                   "xs21_69e0oge2z2553": ("?-R-bee_on_eater_and_R-bee", 20),
                   "xs21_8u1v0j3z23w11": ("?-eater_siamese_table_siamese_very_long_eater_and_block", 20),
                   "xs21_cilligzx66074": ("00d800580040003e0001000d0012000c", 20),
                   "xs21_259mgmiczx6a4": ("00800140012000d6001500d200900060", 20),
                   "xs21_0c88bqicz2596": ("0060009000b001a000260029006a0004", 20),
                   "xs21_g8ge952z1qhe2": ("01000280024801ce0031004b0030", 20),
                   "xs21_35s2aczx11dic": ("0300028000e00110015000d600090006", 20),
                   "xs21_2lligkcz32w66": ("006200550015001200d000d4000c", 20),
                   "xs21_35ao4koz66074": ("?-worm_siamese_Z_on_boat_and_block", 20),
                   "xs21_3p6gmp3zw1226": ("00c0009b006a000a0064009800c0", 20),
                   "xs21_03lkmz6962452": ("00c0012300d50054009600a00040", 20),
                   "xs21_oggcaarz04a96": ("?-R-hat_on_boat_with_cis-tail", 20),
                   "xs21_0okid1e8z4aa6": ("00800158015400d2000d0001000e0008", 20),
                   "xs21_3lm0ep3z32011": ("?-long_integral_siamese_hook_and_ship", 20),
                   "xs21_0okkb2acz4aa6": ("?-R-bee_on_eater_and_R-bee", 20),
                   "xs21_wrb079icz6221": ("?-R-mango_and_snake_eater_and_block", 20),
                   "xs21_cc0s2ticz0643": ("006000500010001600d500d5000a0004", 20),
                   "xs21_0gbq1uge2z321": ("0180014000ac006a000a006b0050", 20),
                   "xs21_xc9jz2llldz01": ("064004ac01aa002a002b0010", 20),
                   "xs21_wg6p3qicz6521": ("0180014000a0005600150021002e0018", 20),
                   "xs21_35a88b96zx696": ("0180014000a00026002901a6012000c0", 20),
                   "xs21_69mggm952zw66": ("?-loaf_long_line_beehive_and_trans-block", 20),
                   "xs21_02596z695d552": ("00c0012200a501a900a600a00040", 20),
                   "xs21_0cc0si53z6953": ("?-boat_with_leg_on_R-loaf_and_block", 20),
                   "xs21_69ac0siczwc93": ("00c0012000a30069000c007000900060", 20),
                   "xs21_g88bbgz1qr221": ("003003480368004b004b0030", 20),
                   "xs21_4a9egmiczw256": ("003000480068000b0075009200500020", 20),
                   "xs21_354lb8oz4a611": ("?-C_on_hook_on_boat", 20),
                   "xs21_4a4o7piczw343": ("00300052009500aa0068001400140008", 20),
                   "xs21_0c8al56z69d11": ("00c00140015800a8002b00690006", 20),
                   "xs21_2lm0e96zw3453": ("0060009600750001006e00a80040", 20),
                   "xs21_354mgu156zw32": ("0186012900eb0008003800400060", 20),
                   "xs21_69jqik8z04aa4": ("00c00122019500b5009200500020", 20),
                   "xs21_8ehjzw1470si6": ("?-eater_on_hook_and_hook", 20),
                   "xs21_39u06996z0346": ("?-shillelagh_siamese_hook_and_pond", 20),
                   "xs21_069baik8zc871": ("0180010600e9002b000a001200140008", 20),
                   "xs21_0ckggm96z6aa6": ("beehive_with_long_nine_and_?-cap", 20),
                   "xs21_4aab8ob96zx32": ("00c8014e010100fe002000080018", 20),
                   "xs21_35a8czw8e1d96": ("0180014000a100270068000b00090006", 20),
                   "xs21_2lligoz32w6ac": ("?-very_long_eater_and_beehive_and_ship", 20),
                   "xs21_0cc0s2qrz6511": ("00d80058004000380004003400350003", 20),
                   "xs21_mmgmk13z1w643": ("?-worm_and_carrier_and_block", 20),
                   "xs21_651u066z69611": ("00c60149010600f8000800c000c0", 20),
                   "xs21_oo1v0cicz6221": ("00d800580041003f0000000c0012000c", 20),
                   "xs21_69b8b9cz06413": ("0060009300d1001400d600900030", 20),
                   "xs21_259aczx69d1e8": ("01b000a8008800700000001c001200090006", 20),
                   "xs21_069baicz8e132": ("010001c60029006b004a0012000c", 20),
                   "xs21_3lmggz32w69ic": ("mango_with_long_nine_and_?-ship", 20),
                   "xs21_3lk2qcz343032": ("?-long_integral_siamese_table_and_R-bee", 20),
                   "xs21_3lo0o8gozcia6": ("?-R-loaf_and_long_snake_and_snake", 20),
                   "xs21_ojaaczx1784ko": ("030002800080010000ec002a000a00130018", 20),
                   "xs21_gjlk453z1w696": ("0180014600490056015001900018", 20),
                   "xs21_09f0sia4z2553": ("006000900070000c006a002900260060", 20),
                   "xs21_4aab8b96zx352": ("006800ae0081007e0000001800280010", 20),
                   "xs21_0ml5q8a6z3421": ("0060009600550025001a0008000a0006", 20),
                   "xs21_cc0v9zx123cko": ("?-long_on_ship_and_block", 20),
                   "xs21_39c8a6z651156": ("?-long_hook_siamese_carrier_and_dock", 20),
                   "xs21_8e138v1oozx32": ("006c00a80088019b000b00200030", 20),
                   "xs21_c88e132acz356": ("00c001400180000001e30121002e0018", 20),
                   "xs21_0gbb8b52z3453": ("006c00ac0040003c0002000d00090006", 20),
                   "xs21_069a4z355d552": ("006000a600a901aa00a400a00040", 20),
                   "xs21_0gillmz56w643": ("00a000d00012001500d500960060", 20),
                   "xs21_64pb8b52z0643": ("006c00a90043003c00040008000a0006", 20),
                   "xs21_c8861t6zc8711": ("018c010800e800260021001d0006", 20),
                   "xs21_0ggm9icz32cjo": ("00c00120024301b9002600280018", 20),
                   "xs21_039egmaz4aa43": ("00a000d0001c00e2012501850002", 20),
                   "xs21_39e0u2kozw643": ("00c000ac002a0069000b000800280030", 20),
                   "xs21_0ggm552z3ege3": ("?-C_siamese_hat_and_R-bee", 20),
                   "xs21_178fhik8zw643": ("00d8005400520031000e000800280030", 20),
                   "xs21_gbb8bl8z12311": ("003600340002003d0042005c0030", 20),
                   "xs21_39u0u2sgzw123": ("?-hook_siamese_eaters_siamese_long_Z", 20),
                   "xs21_259mgmiczw4a6": ("00800140012200d5001600d000900060", 20),
                   "xs21_2lmgml2z346w1": ("worm_and_boats", 20),
                   "xs21_0g88m552z8lld": ("?-R-bee_on_R-bee_and_R-bee", 20),
                   "xs21_69ac0siczw653": ("?-R-bee_on_ship_and_R-loaf", 20),
                   "xs21_0mkl3z122d4ko": ("03000280008301b5005400560020", 20),
                   "xs21_0ca9b871z2553": ("00d800540042003e0000000e00090006", 20),
                   "xs21_39u0u1jz32x11": ("?-hook_siamese_carrier_and_cis-dock", 20),
                   "xs21_0ggo8brz34aic": ("0360034000460069002a00240018", 20),
                   "xs21_0ml1u0uiz1221": ("00600090006b000a006a004b0030", 20),
                   "xs21_g88b9icz1255d": ("00600090012b01aa002a00240018", 20),
                   "xs21_3lkkmicz01w66": ("00c000ac00280028006b004b0030", 20),
                   "xs21_wgbbgn96z2521": ("?-R-bee_bend_line_barge_and_block", 20),
                   "xs21_069d2sgzca513": ("0180014600a9002d0062001c0010", 20),
                   "xs21_ciabhegozw123": ("00180074008400b5004b00280018", 20),
                   "xs21_br0raicz01221": ("0068006e0001006d002a00240018", 20),
                   "xs21_4a9fgkcz03543": ("00300028000e00f1009500560020", 20),
                   "xs21_06is0si96z643": ("?-eater_siamese_hook_and_R-mango", 20),
                   "xs21_xmm0e952zca43": ("03000280014000400060000c006a00690006", 20),
                   "xs21_g88m9a4z178b6": ("004000a0012600dd0021002e0018", 20),
                   "xs21_33gv18kczx346": ("?-Z_siamese_eater_and_boat_and_block", 20),
                   "xs21_31eo0uicz0643": ("00c000a6002500350016001000500060", 20),
                   "xs21_259aczw8e1d96": ("G_and_?-R-mango", 20),
                   "xs21_g88b9acz11d93": ("006000a0012c01a9002b00280018", 20),
                   "xs21_0c4o0ehrzc871": ("01b0011000e000000038004e00610003", 20),
                   "xs21_3lkk8ge2z3443": ("00c600a90029002e0010000800700040", 20),
                   "xs21_0ggm453z3ege3": ("03000280009801ae0021002e0018", 20),
                   "xs21_3pm0e9a4zx352": ("00c400aa0029004e0060001800140008", 20),
                   "xs21_06is079icz643": ("?-eater_siamese_hook_and_R-mango", 20),
                   "xs21_0697ob96z6421": ("00c000a000100008002e005100550036", 20),
                   "xs21_0o4km952zd543": ("01a000b8008400740016000900050002", 20),
                   "xs21_gg0si52zdlge2": ("01b002b0020001dc005200050002", 20),
                   "xs21_3hu0uh3z01243": ("00c0008c007a0001007e008800c0", 20),
                   "xs21_39e0oka4z2553": ("?-long_boat_on_R-bee_and_hook", 20),
                   "xs21_4a5lmzwc87066": ("00c000c0000000f601150185000a0004", 20),
                   "xs21_cikljgozw4aa4": ("0060009000520155019500120030", 20),
                   "xs21_g6p7gf9z11w32": ("006c002a002a0064001500130030", 20),
                   "xs21_69m88czxdd113": ("?21?016", 20),
                   "xs21_255mgm93z0643": ("?21?029", 20),
                   "xs21_33gv1s6z03421": ("?21?041", 20),
                   "xs21_0jhkmz32w69ic": ("?21?049", 20),
                   "xs21_39u066z643033": ("?21?057", 20),
                   "xs21_cic87piczw113": ("?21?064", 20),
                   "xs21_0gt3ob96z3421": ("?21?066", 20),
                   "xs21_4a9b8b5zw6513": ("?21?074", 20),
                   "xs21_g88rb8o6413z11": ("?-long_on_carrier_and_block", 20),
                   "xs21_0mp3s4oz124701": ("00200056009900e3001c00240018", 20),
                   "xs21_699mggc2egozx1": ("0300048c0494031500e30080", 20),
                   "xs21_69mggogkczx4a6": ("00c0012000d0001200150036001000500060", 20),
                   "xs21_o4s3pmz01w34a4": ("00800140009600790003001c00240018", 20),
                   "xs21_xo97079a4z3521": ("020005000680008000c60029002a006c", 20),
                   "xs21_0gs29raa4z3421": ("00800140012000c8005e0041002e0018", 20),
                   "xs21_02596z69d115a4": ("00c0012201a50029002600a001400080", 20),
                   "xs21_0o4o0o8b5zd543": ("?-snake_eater_and_anvil", 20),
                   "xs21_08kkm9jzoge201": ("0320025001a000a800ae00410003", 20),
                   "xs21_02lligz652w696": ("beehive_long_line_boat_and_?-beehive", 20),
                   "xs21_03lkkl3zc45201": ("?-snake_eater_siamese_table_and_cis-dock", 20),
                   "xs21_025a88gz695lp1": ("00c0012200a502aa032800280010", 20),
                   "xs21_25akgozx622qic": ("0180024003400058005000d4000a00050002", 20),
                   "xs21_w8e1u0oozca511": ("0180014000a8002e0021001e000000180018", 20),
                   "xs21_g8o0uhe0e93z01": ("?-hook_and_long_R-bee_and_boat", 20),
                   "xs21_08e1lmzc970121": ("0180012800ee0001003500560020", 20),
                   "xs21_8o0u1ticz01243": ("0030004800b8008600790002001c0010", 20),
                   "xs21_04a9mge2zca243": ("01800144004a008900760010000e0002", 20),
                   "xs21_25t2c88gzxdd11": ("008001400170008b006b002800280010", 20),
                   "xs21_35akggkczw4aic": ("long_boat_with_long_nine_and_?-loaf", 20),
                   "xs21_8kkm1mkiczx121": ("001800240014003600410036001400140008", 20),
                   "xs21_25a8c8a6zw3596": ("?-tub_with_leg_siamese_hook_and_R-loaf", 20),
                   "xs21_259q4oz6a87011": ("?-mango_with_tail_siamese_worm", 20),
                   "xs21_w4a96zml553z11": ("?-long_hook_siamese_long_hook_and_loaf_and_block", 20),
                   "xs21_xo8hf0ck8z3543": ("03000480068000a200d5001600100030", 20),
                   "xs21_0mmgmk13z346w1": ("00c0009600360000003e002100050006", 20),
                   "xs21_69icw8kczxdd11": ("mango_long_line_boat_and_cis-block", 20),
                   "xs21_g88b96zh1t6z11": ("?-scorpio_siamese_eaters", 20),
                   "xs21_g8o0uhe0eicz01": ("020005620355005500560020", 20),
                   "xs21_352s0ccz330346": ("00c600a60040003e000100330030", 20),
                   "xs21_69baa4oz04a511": ("[[?21?075]]", 20),
                   "xs21_w8e1u066zc8711": ("?-anvil_siamese_eater_and_trans-block", 20),
                   "xs21_02llicz4706226": ("00c0004c005200d5001500e20080", 20),
                   "xs21_0oo0e9jz4aa611": ("0190012800e80006003500350002", 20),
                   "xs21_g88bbgz12303lo": ("030002b0006b000b006800480030", 20),
                   "xs21_8k4o1vg32aczw1": ("010002b004a30321002e0068", 20),
                   "xs21_0gilmz32w23cko": ("?-dock_on_ship_and_boat", 20),
                   "xs21_g88mligz178dw1": ("003000e8010801b6001500120030", 20),
                   "xs21_31eg6kk8zw3543": ("00c000a8002e00210016003400240018", 20),
                   "xs21_wcc0si52zca513": ("0180014000ac002c0060001c001200050002", 20),
                   "xs21_025a84oz6511dd": ("00c000a20025002a01a801a40018", 20),
                   "xs21_0g88b96zol3033": ("030002b000680008006b00690006", 20),
                   "xs21_2560u2koz03543": ("004000ac006a0009000b006800480030", 20),
                   "xs21_0gilmz32w25ako": ("very_long_boat_with_long_nine_and_?-boat", 20),
                   "xs21_g88rbgz11wok96": ("00c001200290030b001b000800280030", 20),
                   "xs21_660uhik8zw4aa4": ("00c000c0000200f50115009200500020", 20),
                   "xs21_0ml5a4oz344311": ("0060009600950065002a00240018", 20),
                   "xs21_2552s0siczx643": ("00c0012200d500150016000800280030", 20),
                   "xs21_256o8gzx8e1eic": ("0180024001c0003001c80118000600050002", 20),
                   "xs21_xg8ie0e96zca23": ("060004000380008000a00056001500350002", 20),
                   "xs21_35ic0c4ozx11dd": ("01800140009000680008006b004b0030", 20),
                   "xs21_xo8hf0352z3543": ("03600540024000580028000b00090006", 20),
                   "xs21_255q88gzcia611": ("?-R-loaf_on_R-bee_on_beehive", 20),
                   "xs21_39eg8ozx122qic": ("0300024001c0003000480068000b00090006", 20),
                   "xs21_252s0si6zw3543": ("00600048003e0001003d004600a00040", 20),
                   "xs21_g8o0uhf0356z01": ("?-ship_and_siamese_long_hooks_and_boat", 20),
                   "xs21_0696k4ozci9611": ("01800246012900c6003400240018", 20),
                   "xs21_g88ci96z123cic": ("01800246012900c6005800480030", 20),
                   "xs21_0mligz32w25ako": ("very_long_boat_with_long_nine_and_?-boat", 20),
                   "xs21_xjhe8zgbaq1z11": ("?-hook_and_hook_on_eater", 20),
                   "xs21_312kozwc870796": ("018001400020001000300016001500550062", 20),
                   "xs21_09f0s4ozc97011": ("?-cap_and_hook_and_table", 20),
                   "xs21_32akgozx622qic": ("03000100014000ac00280068000b00090006", 20),
                   "xs21_0gilmz346069k8": ("01000280012000d6001500d200900060", 20),
                   "xs21_02lmgmicz65201": ("00c000a200550016003000160012000c", 20),
                   "xs21_g88mhrz11x6aa4": ("00c0012000e0000300390026000800280030", 20),
                   "xs21_o8g31eoz069d11": ("?-long_integral_siamese_hook_siamese_eater", 20),
                   "xs21_0cai3z4a430e93": ("0080014c008a0072000301c001200060", 20),
                   "xs21_0mligoz34606a4": ("0080015800d0001200d500960060", 20),
                   "xs21_0354koz39e0346": ("?-integral_siamese_hook_and_hook", 20),
                   "xs21_259mggkczwcia4": ("trans-loaf_with_long_nine_and_?-loaf", 20),
                   "xs21_g88m952z123cic": ("01000286024901a6005800480030", 20),
                   "xs21_259mggzxoge1e8": ("01000280024001a30021002e0010000e0002", 20),
                   "xs21_035a88a6z8ka53": ("trans-boat_with_long_nine_and_ortho-very_long_boat", 20),
                   "xs21_g897o4ozc97011": ("0190012800e90007003800240018", 20),
                   "xs21_035a8cz6513156": ("long_dock_and_?-tub_with_leg", 20),
                   "xs21_0iu0e9jz122611": ("00c8009400740003007a004a0004", 20),
                   "xs21_25t2sggkczx146": ("00c0012000d30051005e002000080018", 20),
                   "xs21_035s2acz330346": ("006000630005007c008200ca000c", 20),
                   "xs21_06t1e8gzca4311": ("01800146009d0061002e00280010", 20),
                   "xs21_32qc0c4ozxdd11": ("0180008000b0006b000b006800480030", 20),
                   "xs21_gbq2koz11w34ac": ("01800140009800740002001a002b0030", 20),
                   "xs21_651u08oz4a9521": ("?21?036", 20),
                   "xs21_651u08oz4aa611": ("?21?043", 20),
                   "xs21_4a60u1t6zw6221": ("?21?070", 20),
                   "xs21_352s0ggkczw3543": ("0180014000a30021002e006800480030", 20),
                   "xs21_xdbzo4id1156z01": ("mango_with_long_nine_and_?-snake", 20),
                   "xs21_0ggml2z346069k8": ("01000280012200d5001600d000900060", 20),
                   "xs21_25a8a52zx6515a4": ("00880154008800700000001c002200350002", 20),
                   "xs21_wg88c1fgkcz6521": ("060005000280010600e9002b00080018", 20),
                   "xs21_069b8ozckjh1zx1": ("018002860269062b00280018", 20),
                   "xs21_0mk48a52z343033": ("00600096007400040068006a00050002", 20),
                   "xs21_256o8gzy0230ehr": ("?-hook_on_boat_and_C", 20),
                   "xs21_0gil56z32023ck8": ("C_on_boat_and_?-R-bee", 20),
                   "xs21_0gjl46z3iaq1zw1": ("030001200556065500520030", 20),
                   "xs21_6a8o0ok453zx643": ("0300020301c1002e0068002000280018", 20),
                   "xs21_xg8id1egoz4a611": ("02000500030000c000a30055001400240018", 20),
                   "xs21_xca952zggm953z1": ("R-loaf_with_trans-tail_and_?-R-mango", 20),
                   "xs21_0g8ehlmz321x252": ("0080014300850072000c006800480030", 20),
                   "xs21_wg88c1fgkcz2543": ("030004800280010600e9002b00080018", 20),
                   "xs21_0gilmzo5o643z01": ("030004b0031200d500960060", 20),
                   "xs21_259acw8ozx69d11": ("?-scorpio_and_R-mango", 20),
                   "xs21_255mggca6zw3421": ("R-loaf_on_ship_and_R-bee", 20),
                   "xs21_xg88bp453z4a611": ("06c00440030000f000880018000600050002", 20),
                   "xs21_g8o0ehu06a4z121": ("?-R-bee_and_long_R-bee_and_boat", 20),
                   "xs21_0o4o0uh3z11078c": ("0180011000f30001003e004000380008", 20),
                   "xs21_8koxok453zx3543": ("060004000382004500c6005800480030", 20),
                   "xs21_31e88gzw3125aic": ("?-loop_siamese_eater_at_loaf", 20),
                   "xs21_0ggc970sia4z321": ("?-hook_on_ship_and_R-loaf", 20),
                   "xs21_39eg8gzx122dik8": ("03000280008001a0005000480034000a00090006", 20),
                   "xs21_w4s0gs25a4z3543": ("?-barge_with_tail_and_worm", 20),
                   "xs21_259e0eiozy43123": ("?-hook_on_snake_and_R-loaf", 20),
                   "xs21_4a51u0u15a4zy11": ("018c02520555025200500020", 20),
                   "xs21_0gbb8ozo5l91z01": ("?-siamese_long_hooks_and_loaf_and_block", 20),
                   "xs21_35ic0sik8zw1252": ("0180014400aa0029004e005000280010", 20),
                   "xs21_03lkaak8z652011": ("00c000a300550014002a002a00140008", 20),
                   "xs21_256o8gzwck87066": ("01000280018600650042003c0000000c000c", 20),
                   "xs21_696o8gzx122dik8": ("?-loaf_on_R-loaf_on_beehive", 20),
                   "xs21_4a9mggzx124bkk8": ("?-R-loaf_at_beehive_and_loaf", 20),
                   "xs21_6a40v1u0ok8zy11": ("?-very_long_R-bee_and_boats", 20),
                   "xs21_08obbgz3iaq1zw1": ("006002480558034b002b0010", 20),
                   "xs21_gbb886248goz123": ("03000500040303c5002803300300", 20),
                   "xs21_g88a52zg5u066z11": ("061004a803c8000a00c500c2", 20),
                   "xs21_25a88c48gzx69d11": ("0080014000a000260029006b004800280010", 20),
                   "xs21_wg8k46164koz6521": ("0c000a0005000283010100ee00280010", 20),
                   "xs21_xca52z2ll552z011": ("?-very_long_bee_and_long_boat_and_block", 20),
                   "xs21_259m88gzy1116ako": ("0600050002800180006000480034000a00090006", 20),
                   "xs21_0gg08o653z1245lo": ("030002800180006300550014002400280010", 20),
                   "xs21_2560u2gzy1123cko": ("ship_on_boat_with_long_leg_and_?-boat", 20),
                   "xs21_ca2s0ggca52zx1221": ("big_S_on_long_boat", 20),
                   "xs21_25a8og8gzy2470696": ("04000ac00a80048000b0005c000200050002", 20),
                   "xs21_69ak8g0s252zx1221": ("02020505048a034800a800900060", 20),
                   "xs21_35icz0g8l552z0121": ("0c000a0604890356005000500020", 20),
                   "xs21_69ak8gzx1221eg8gzy51": ("0300048002800160009000500020001c000200050002", 20),
                   "xs22_69b88cz69d113": ("?22?002", 7),
                   "xs22_08o0u93zoif032": ("?22-trans-mirrored long", 7),
                   "xs22_2llmz1qaar": ("?22?009", 9),
                   "xs22_69b8b96z2553": ("?22?008", 11),
                   "xs22_09v0v9z3210123": ("?22?024", 12),
                   "xs22_wg8kie0e96z2543": ("?22?048", 12),
                   "xs22_ca9bob96z33": ("?22?013", 13),
                   "xs22_02llmzcnge21": ("018002e2021501d500560020", 13),
                   "xs22_3lkljgz32w643": ("?22?031", 13),
                   "xs22_02596z69bp552": ("?22?032", 13),
                   "xs22_g88bbob96z123": ("?22?023", 13),
                   "xs22_ca1u8zx122ria4": ("?22?015", 13),
                   "xs22_gbb8bpicz123": ("?22?018", 14),
                   "xs22_69b8bqicz033": ("?22?049", 14),
                   "xs22_69b8b96z6513": ("?22?005", 14),
                   "xs22_gbb8bqicz123": ("?22?004", 14),
                   "xs22_69b8b96z03552": ("cis-very_long_worm_and_R-bee", 14),
                   "xs22_699m88gzcia521": ("?22?037", 14),
                   "xs22_0g8ka96zraahz011": ("?22?038", 14),
                   "xs22_69bojbo8a6": ("[[?22?061]]", 15),
                   "xs22_39e0ehe0e96": ("?-hook_and_long_beehive_and_R-bee", 15),
                   "xs22_gbaabqicz123": ("006000a00086007d0001007e0048", 15),
                   "xs22_69b8bpicz033": ("?22?021", 15),
                   "xs22_3lk6gmiczw343": ("?22?042", 15),
                   "xs22_02596z69d1d96": ("very_long_worm_and_loaf", 15),
                   "xs22_03lkkl3z470641": ("?22?019", 15),
                   "xs22_0iu0u93z643032": ("?22?020", 15),
                   "xs22_wg8kie0e93z2543": ("trans-loaf_at_R-loaf_and_trans-hook", 15),
                   "xs22_039q4oz6a870123": ("?22?034", 15),
                   "xs22_0g8ka96zraahzw11": ("?22?045", 15),
                   "xs22_ra1v0rrz011": ("?22?022", 16),
                   "xs22_2llmz12egnc": ("?22?030", 16),
                   "xs22_ciiriiczwcic": ("[[minus zero]]", 16),
                   "xs22_caab9a4z3553": ("?22?026", 16),
                   "xs22_3lkaacz343033": ("?-long_integral_siamese_beehive_on_R-bee_and_block", 16),
                   "xs22_0gbbo7picz121": ("?-mango_siamese_bookend_on_tub_with_leg_and_block", 16),
                   "xs22_69b8b96z03156": ("?22?033", 16),
                   "xs22_g88b9icz178b5": ("00600090012a01ad0021002e0018", 16),
                   "xs22_3lkkl3z122643": ("racetrack_and_cis-dock", 16),
                   "xs22_3lkkl3z32w652": ("cis-boat_with_long_nine_and_cis-dock", 16),
                   "xs22_0259acz69d1156": ("[[?22?062]]", 16),
                   "xs22_69b88czw69d113": ("?22?053", 16),
                   "xs22_69b88c4gozw69a4": ("?-worm_siamese_carrier_and_?-loaf", 16),
                   "xs22_069ak8gz8kie1221": ("?22?058", 16),
                   "xs22_caabob96z33": ("00c000c0000800fe008100750016", 17),
                   "xs22_3586178bqic": ("?22?012", 17),
                   "xs22_rb0v1qrz011": ("006d006b0008006b004b0030", 17),
                   "xs22_69e0ehe0eic": ("?-long_beehive_and_R-bees", 17),
                   "xs22_069riicz69a6": ("?22?028", 17),
                   "xs22_69b88brzw696": ("01b001a00026002901a6012000c0", 17),
                   "xs22_caar4koz3543": ("?-big_S_siamese_R-hat", 17),
                   "xs22_354kl3zrq221": ("?-block_and_long_hook_and_dock", 17),
                   "xs22_gba9bqicz123": ("006000a00086007d0001006e0058", 17),
                   "xs22_03lkmzcnge21": ("018002e3021501d400560020", 17),
                   "xs22_69b8brz0c871": ("01b001a8002e01a1012300c0", 17),
                   "xs22_cc0s2qrz3543": ("00d800580040003e000100350036", 17),
                   "xs22_0c9baiczck871": ("0180028c010900eb002a0012000c", 17),
                   "xs22_gbbo79icz1221": ("?22?056", 17),
                   "xs22_6t1u8z11078a6": ("00c80178010000fe002100050006", 17),
                   "xs22_g88b9qj96z123": ("00d80168010000be006100050006", 17),
                   "xs22_0mmgu156z34a4": ("00c00140010000f0001200d500d2000c", 17),
                   "xs22_39e0mp3z03543": ("?22?043", 17),
                   "xs22_04a96zoid1d96": ("0300024401aa002901a6012000c0", 17),
                   "xs22_3lkljgz346w23": ("long_worm_and_cis-C", 17),
                   "xs22_39e0mmzc97011": ("?-hooks_and_blocks", 17),
                   "xs22_caabaicz35421": ("006c00aa008a004b002a0012000c", 17),
                   "xs22_8e1lmz3303496": ("00c00120009600750001006e0068", 17),
                   "xs22_2ll6gmiczw343": ("0060009600750001006e002800280010", 17),
                   "xs22_354kl3zx123cko": ("?22?006", 17),
                   "xs22_09v0rbz3210123": ("?22?014", 17),
                   "xs22_0dr0rdz3210123": ("cis-mirrored_?-hook_siamese_snake", 17),
                   "xs22_0c88b96z69d113": ("trans-rotated_worm", 17),
                   "xs22_0iu0e93z643033": ("?22?007", 17),
                   "xs22_0gbb88gz8lld11": ("?-very_long_R-bee_and_R-bee_and_block", 17),
                   "xs22_04s0v9zc970123": ("trans-mirrored_long", 17),
                   "xs22_0ggmmge96z346w1": ("?-worm_on_R-bee_and_block", 17),
                   "xs22_xg4s079iczca611": ("boat_on_hook_and_shift-R-mango", 17),
                   "xs22_o8wci96z0hhldz01": ("mango_with_long_nine_and_?-eater", 17),
                   "xs22_gg0s29e0eicz1221": ("03000480068200b5009500560020", 17),
                   "xs22_39e0ehf0f9": ("?-hook_and_long_R-bee_and_table", 18),
                   "xs22_6530fhqb96": ("01b602d5021301d00060", 18),
                   "xs22_g8e1t6zd55d": ("01b000a800ae01a1001d0006", 18),
                   "xs22_8e1v0rrz311": ("R-anvil_and_blocks", 18),
                   "xs22_ca1v0rrz311": ("006c006c0000007c0042002a001b", 18),
                   "xs22_3lkmz12egnc": ("031002a800ae01a1001d0006", 18),
                   "xs22_259e0ehraa4": ("?22?044", 18),
                   "xs22_69acz69d1ego": ("0300020001c0002c01aa012900c6", 18),
                   "xs22_gs2qb96z6aa4": ("?22?016", 18),
                   "xs22_4a96z69d1dic": ("0180024001a0002601a9012a00c4", 18),
                   "xs22_6a88brz69d11": ("?-scorpio_siamese_very_long_eater_and_block", 18),
                   "xs22_ca952z355d96": ("R-racetrack_and_cis-R-mango", 18),
                   "xs22_caab9a4z33w33": ("R-racetrack_II_and_blocks", 18),
                   "xs22_0ca9bqicz2552": ("0060009000600006007d0041002e0018", 18),
                   "xs22_6996z6511dik8": ("trans-loaf_with_long_nine_and_trans-pond", 18),
                   "xs22_0g6p7ob96z321": ("?22?051", 18),
                   "xs22_259acz359d113": ("008c014a012900ab00680008000c", 18),
                   "xs22_c8970796z3552": ("?-cis-legs_and_R-bees", 18),
                   "xs22_31e8gz31pl4ko": ("0318021001d30055002400050003", 18),
                   "xs22_xi5t2sgz69d11": ("00c00140010000f0002b000a001a00240018", 18),
                   "xs22_8u1v0brz01221": ("006c006a000a006b004a0012000c", 18),
                   "xs22_wmmge1egoz643": ("03000280008000e3001500d400d40008", 18),
                   "xs22_gg0si96zdlge2": ("01b002b0020001dc005200090006", 18),
                   "xs22_0mlhu06a4z346": ("00c00140010000f0001200d500960060", 18),
                   "xs22_0mmgmp3z32w66": ("?-very_long_eater_siamese_shillelagh_and_blocks", 18),
                   "xs22_6t1qcz11078a6": ("00c80178010000be006100050006", 18),
                   "xs22_39e0ooz697066": ("?-R-bee_and_hook_and_blocks", 18),
                   "xs22_gbb8b96z12156": ("0060009000d3001500d400d2000c", 18),
                   "xs22_0gbbo3qicz321": ("01800140009600750001006e0068", 18),
                   "xs22_2llmggz1qq221": ("?22?029", 18),
                   "xs22_4s0si96z178a6": ("00c00120009600750001007e0048", 18),
                   "xs22_02lligzok96243": ("03000282013500d5005200900060", 18),
                   "xs22_o4o0uhe0e96z01": ("?-long_R-bee_and_R-bee_and_beehive", 18),
                   "xs22_c82t52z3303453": ("006c00680002007d008500a20060", 18),
                   "xs22_0354kozgs2qaa4": ("anvil_and_?-integral", 18),
                   "xs22_wcc0si96z4a953": ("R-mango_on_R-mango_and_block", 18),
                   "xs22_0259acz6511d96": ("para-R-mango_and_long_worm", 18),
                   "xs22_69b88czx311d96": ("trans-rotated_worm", 18),
                   "xs22_69icwciczxdd11": ("?-mango_long_line_beehive_and_cis-block", 18),
                   "xs22_069b88a6zca513": ("?-boat_with_leg_and_long_worm", 18),
                   "xs22_069b88a6z4a953": ("long_worm_and_?-R-mango", 18),
                   "xs22_651u0okczw178c": ("?-worm_siamese_eater_and_ship", 18),
                   "xs22_09v0ccz321079c": ("?-long_and_hook_and_block", 18),
                   "xs22_25akgka52zca26": ("?22?057", 18),
                   "xs22_4a9b8b96zw2552": ("006c00aa0081007e0000001800240018", 18),
                   "xs22_g4s0sie0e96z11": ("?-R-bee_and_siamese_R-bees_and_hook", 18),
                   "xs22_02ll68oz69a611": ("00c00122015500d5002600280018", 18),
                   "xs22_08o0e93zoif033": ("?-long_and_eater_and_block", 18),
                   "xs22_39e0o4oz699701": ("?-R-pond_on_beehive_and_hook", 18),
                   "xs22_0354kl3zokc321": ("dock_and_cis-ship_on_ship", 18),
                   "xs22_j1u0mmz11w3452": ("?-dock_and_R-loaf_and_block", 18),
                   "xs22_c8970sicz02553": ("?-R-bee_on_R-bee_and_cis-legs", 18),
                   "xs22_xm2s079a4z4a611": ("?22?060", 18),
                   "xs22_25a88a6z4a51156": ("cis-mirrored_tub_with_long_nine", 18),
                   "xs22_0ggmmge93z346w1": ("?-worm_on_hook_and_block", 18),
                   "xs22_4aicgn98czx1243": ("?22?025", 18),
                   "xs22_g8861u0ooz011dd": ("00300030000000f0010b00cb002800280010", 18),
                   "xs22_256o8gzx643sia4": ("?-R-loaf_on_C_on_boat", 18),
                   "xs22_g88ci96zo5ldz01": ("?22?039", 18),
                   "xs22_0ggo0ep3z1qq221": ("0300026001d000080068002b002b0010", 18),
                   "xs22_0g03pmz1230fgkc": ("?-worm_siamese_shillelagh_and_?-boat", 18),
                   "xs22_0ml1e8z320115ac": ("0180014000a8002e0021001500560060", 18),
                   "xs22_69mggozo4q226z01": ("?22?052", 18),
                   "xs22_259a4o0o8a6zx643": ("mango_with_long_nine_and_?-eater", 18),
                   "xs22_259m88gzy01252ako": ("06000500024001a0005000480034000a00090006", 18),
                   "xs22_259eg88m952zy0121": ("?-loaf_at_loaf_on_R-loaf", 18),
                   "xs22_69bqhbqic": ("00d8016e010100ed0036", 19),
                   "xs22_69bobbo8a6": ("01b002b3020101fe0048", 19),
                   "xs22_okiq3qicz66": ("00d800d40012001a0003001a0012000c", 19),
                   "xs22_69e0eis079c": ("?-R-bee_and_siamese_hooks_and_hook", 19),
                   "xs22_69b8brz2596": ("01b001a0002601a9012a00c4", 19),
                   "xs22_0oe1t6zckld": ("paperclip_and_?-cap", 19),
                   "xs22_39e0e970796": ("?-R-bee_and_siamese_hooks_and_hook", 19),
                   "xs22_69e0ehe0e96": ("?-long_bee_and_R-bees", 19),
                   "xs22_39e0ehe0eic": ("?-hook_and_long_bee_and_R-bee", 19),
                   "xs22_69baab96zx33": ("006600bd0081007e000000180018", 19),
                   "xs22_gbb88gz19lld": ("?-very_long_R-bee_and_R-bee_and_block", 19),
                   "xs22_69baacz65156": ("R-racetrack_and_cis-C", 19),
                   "xs22_08u1lmzcib43": ("01a002b8020401fa00490006", 19),
                   "xs22_03lk46zcnge3": ("018002e3021501d400640006", 19),
                   "xs22_3p6gmicz3543": ("00c6009d0061000e006800480030", 19),
                   "xs22_gbb88gzd5lp1": ("01b000ab02ab032800280010", 19),
                   "xs22_ml1e8gzd5871": ("01b600b5010100ee00280010", 19),
                   "xs22_69fgfhoz0643": ("0060009300f1000e00f000880018", 19),
                   "xs22_caabaa4z3553": ("?22?059", 19),
                   "xs22_0mllmz122qq1": ("?-cap_and_block_and_very_long_beehive", 19),
                   "xs22_25aczcid1d96": ("0182024501aa002c01a0012000c0", 19),
                   "xs22_cc0c9jz319ld": ("0320025600d5001200d000d8", 19),
                   "xs22_iu0e96z6a871": ("00d2015e010000ee00290006", 19),
                   "xs22_0mmgehrz3443": ("?-C_on_R-pond_and_block", 19),
                   "xs22_4s0s2qrz3543": ("00d800580040003e0001003d0026", 19),
                   "xs22_g25a4ozdd1dd": ("01b001a2002501aa01a40018", 19),
                   "xs22_0mllmz34aa43": ("006000960155015500960060", 19),
                   "xs22_g8e1t6z19ll8": ("018002e2021501d500520030", 19),
                   "xs22_okihe0e96z66": ("01800180000001e00116009500550022", 19),
                   "xs22_0db0brz69d11": ("?-scorpio_and_snake_and_block", 19),
                   "xs22_g88bbgz19lld": ("?-very_long_R-bee_and_R-bee_and_block", 19),
                   "xs22_2lmgu156z346": ("0062009500d60010001e000100050006", 19),
                   "xs22_39e0uicz2553": ("?-dock_on_R-bee_and_hook", 19),
                   "xs22_69b8n96z6511": ("00c600a9002b0028001700090006", 19),
                   "xs22_j1u0tj871z11": ("01b300a50094005400350003", 19),
                   "xs22_gbaabpicz123": ("006000a00086007d0001007a004c", 19),
                   "xs22_caab9arzw352": ("?-very_long_Z_siamese_eater_siamese_snake_and_cis-boat", 19),
                   "xs22_g89fgkczd553": ("01b000a800a9006f00100014000c", 19),
                   "xs22_354cz69d1d96": ("very_long_worm_and_eater", 19),
                   "xs22_6s1v0rbzw1221": ("006c0069000b006a002a00240018", 19),
                   "xs22_2lmgmmz346w23": ("?-long_worm_and_boat_and_block", 19),
                   "xs22_651u0uiczw643": ("006000a0008300790006007800480030", 19),
                   "xs22_mll2z10470796": ("00d801500152008e0000000e00090006", 19),
                   "xs22_352s0sicz3543": ("00c600a50041003e0000003800480030", 19),
                   "xs22_2lmgeik8z3443": ("?-R-pond_on_R-loaf_and_boat", 19),
                   "xs22_06996z359d552": ("006000a6012901a900a600a00040", 19),
                   "xs22_069a4zcid1d96": ("0180024601a9002a01a4012000c0", 19),
                   "xs22_cimgm952z4aa4": ("008c0152015600900016000900050002", 19),
                   "xs22_354s0sicz3543": ("?-worm_siamese_eater_and_?-R-bee", 19),
                   "xs22_0caabqicz2552": ("?-fourteener_siamese_Z_and_beehive", 19),
                   "xs22_ca9baicz35421": ("006c00aa0089004b002a0012000c", 19),
                   "xs22_259aczw355d96": ("R-racetrack_and_?-R-mango", 19),
                   "xs22_gs2t1eoz0c871": ("003000e00108017e008100730010", 19),
                   "xs22_4a9e0uiczw653": ("00300048007800060075009300500020", 19),
                   "xs22_2llmz346078k8": ("011802a402ac01a0001c000200050002", 19),
                   "xs22_69acz69d115a4": ("00c6012901aa002c002000a001400080", 19),
                   "xs22_651ugmiczw4a6": ("00c00140010200f5001600d000900060", 19),
                   "xs22_0gjl453zrq221": ("?-C_and_long_R-bee_and_block", 19),
                   "xs22_4a9egmiczw696": ("0060009000d0001600e9012600a00040", 19),
                   "xs22_mlligoz1w62ac": ("?-long_Z_and_R-bee_and_hook", 19),
                   "xs22_0g8e1t6z8ll91": ("018002e0021001d2005500350002", 19),
                   "xs22_0gbaq3qicz321": ("01800140009600750001007e0048", 19),
                   "xs22_2ll2s53zw3453": ("00c000a6003d004100ae00a80040", 19),
                   "xs22_c88b9cz311d93": ("006c012901ab00280028006c", 19),
                   "xs22_0okiqb96z4aa4": ("00c0012001a000b00092005500350002", 19),
                   "xs22_8e1u0uicz0643": ("006000500010001600d5005500560020", 19),
                   "xs22_4ac0si96z6953": ("?-R-mango_on_R-loaf_and_boat", 19),
                   "xs22_kc0si96z178a6": ("00c00120009600750001006e0058", 19),
                   "xs22_39egmmz651221": ("?-long_integral_siamese_beehive_on_eater_and_block", 19),
                   "xs22_g88ml96z178a6": ("00c00120015600d50021002e0018", 19),
                   "xs22_69b8bb8ozx352": ("006c00ac0080007f0001001800140008", 19),
                   "xs22_25960gz319lld": ("?-long_Z_and_R-bee_and_loaf", 19),
                   "xs22_651u0okcz3543": ("006600a50081007e0000001800280030", 19),
                   "xs22_4a9e0uiz03553": ("?22?055", 19),
                   "xs22_cc0v1kmiczx121": ("0030002601ad01a1002e00280010", 19),
                   "xs22_0mkl3z12430eio": ("0300024001c000030075009400560020", 19),
                   "xs22_0259a4oz6511dd": ("00c000a20025002901aa01a40018", 19),
                   "xs22_c8all2z3303452": ("006c0068000a0075009500a20040", 19),
                   "xs22_8kiabaik8zx343": ("0010007c0082013900c6002800280010", 19),
                   "xs22_o4ie0ehu0ooz01": ("?-long_R-bee_and_R-mango_and_block", 19),
                   "xs22_4a9eg8oz0178b6": ("004000a8012e00e1001d00260030", 19),
                   "xs22_0ca9lmz2530346": ("?-bookend_siamese_mango_on_hook_and_boat", 19),
                   "xs22_4aab96zw651156": ("racetrack_and_?-dock", 19),
                   "xs22_09v0rdz3210123": ("long_and_?-hook_siamese_snake", 19),
                   "xs22_3lkkl3z01w69a4": ("?22?011", 19),
                   "xs22_04a9baa4z4a953": ("racetrack_II_and_?-R-mango", 19),
                   "xs22_35a8ciicz02553": ("00c000a6004900390006003800480030", 19),
                   "xs22_69baa4oz0c8711": ("00c0012301a100ae00a800480030", 19),
                   "xs22_g88e1egu156z11": ("0600041803a800ab00a90046", 19),
                   "xs22_0ml9abgz344311": ("?-long_bee_siamese_pond_on_shillelagh", 19),
                   "xs22_0mlhe8gz34a611": ("00600096015500d1002e00280010", 19),
                   "xs22_062s0si96z3543": ("long_worm_and_?-R-mango", 19),
                   "xs22_352sgzw4aaq2sg": ("anvil_and_?-boat_with_trans-tail", 19),
                   "xs22_04aab9a4z4a953": ("racetrack_II_and_?-R-mango", 19),
                   "xs22_ciligkcz066066": ("003600360000003e00410065000a0004", 19),
                   "xs22_0g8o69a4z6bgf2": ("00c00170020801f800460009000a0004", 19),
                   "xs22_039u0eik8z6521": ("?-boat_with_leg_siamese_hook_and_R-loaf", 19),
                   "xs22_69b88gzx320fgkc": ("01800280020001e0001000480068000b00090006", 19),
                   "xs22_69ac0sik8zw2552": ("00800144012a00e9000e003000480030", 19),
                   "xs22_025b88a6z651156": ("cis-boat_with_long_nine_and_?-dock", 19),
                   "xs22_xg8ge1diczca611": ("06000500030000c000a2005500150012000c", 19),
                   "xs22_354mic8a6zw1243": ("0180013300e9000e0030004800280010", 19),
                   "xs22_0g8861t6z345d11": ("?22?017", 19),
                   "xs22_25akgka52zw4aa6": ("barge_line_barge_and_R-bee", 19),
                   "xs22_25ac0c4ozw311dd": ("0080014000ac00680008006b004b0030", 19),
                   "xs22_651u0u164kozy01": ("031004a806ae00a100a30040", 19),
                   "xs22_69960u1u0oozy21": ("very_long_bee_and_pond_and_trans-block", 19),
                   "xs22_g8o0ehe0eicz121": ("0200050005220355005500560020", 19),
                   "xs22_0g88b96zhaarz11": ("0620055001480368000b00090006", 19),
                   "xs22_69acggzx320fgkc": ("?-big_S_on_R-loaf", 19),
                   "xs22_0gilligkcz346w1": ("?-worm_siamese_eater_and_beehive", 19),
                   "xs22_xm2s0si52z4a611": ("0200051802a800a001a80018000600050002", 19),
                   "xs22_0okk8a52zca2453": ("018001580054009400a8006a00050002", 19),
                   "xs22_0g8o69e0eicz1221": ("?-R-loaf_on_R-bee_and_R-bee", 19),
                   "xs22_35a84o0oka4zx643": ("06000502024501aa002c002000a000c0", 19),
                   "xs22_39mggozg4q226z11": ("0603048903560050005000d8", 19),
                   "xs22_0g88e1ege1e8z121": ("?-twinpeaks_siamese_tub_with_tail", 19),
                   "xs22_0g8ka960uh3z1221": ("loaf_at_loaf_and_?-long_hook", 19),
                   "xs22_0gilmz344mk3zx11": ("?-mirror_and_boat_and_block", 19),
                   "xs22_8k4o0ehrzw11y0352": ("02000500030c00ca00a9002600a000c0", 19),
                   "xs22_259m88gzy0123cia4": ("?-loaf_at_R-loaf_on_loaf", 19),
                   "xs22_ca2s0g8o653zx1221": ("06000506030900cb00a800480030", 19),
                   "xs22_69icw8ozwo5l91zx1": ("mango_with_long_nine_and_?-loaf", 19),
                   "xs22_69bqhf0f9": ("01b600ad00a101ae0018", 20),
                   "xs22_65lmzcnge3": ("018602e5021501d60060", 20),
                   "xs22_9v0raarz23": ("006c00280028006c0000007f0049", 20),
                   "xs22_660uhe0ehr": ("?-C_and_long_R-bee_and_block", 20),
                   "xs22_39e0mp3qic": ("031802ae00a101950036", 20),
                   "xs22_178brzcild": ("03600356005503890206", 20),
                   "xs22_330fhe0ehr": ("03630355005400550023", 20),
                   "xs22_6960uhbqic": ("01b002d2021501d50062", 20),
                   "xs22_8u1vgbrz23": ("?-table_siamese_eater_siamese_Z_siamese_snake_and_block", 20),
                   "xs22_25b8r3ob96": ("01b602b5020201dc0050", 20),
                   "xs22_39e0ehbqic": ("031802ae00a101ad0016", 20),
                   "xs22_31ekhf0f96": ("0336029500d500960060", 20),
                   "xs22_69bqhf0ca6": ("01b002d3021501d60060", 20),
                   "xs22_39e0ehu0ui": ("?22?003", 20),
                   "xs22_raar2qrz011": ("0049007f0000007b004b0030", 20),
                   "xs22_69b8brz6952": ("01b001a0002401aa012900c6", 20),
                   "xs22_69e0e960uic": ("03000536055503550022", 20),
                   "xs22_697079e0e96": ("hook_siamese_hook_and_?-R-bees", 20),
                   "xs22_6960uhe0eic": ("02300552055503550022", 20),
                   "xs22_697079e0eic": ("?-R-bee_and_siamese_hooks_and_R-bee", 20),
                   "xs22_39e0e970si6": ("?-siamese_hooks_and_hooks", 20),
                   "xs22_69acz255dhr": ("0360022001ac00aa00a90046", 20),
                   "xs22_caar2qrz311": ("?-sesquihat_siamese_table_and_block", 20),
                   "xs22_39e0e97079c": ("0636055401550363", 20),
                   "xs22_g8e1t6z1pld": ("018002e0021601d500530030", 20),
                   "xs22_6960uhe0e96": ("?22?041", 20),
                   "xs22_gbaicz1pl4ko": ("0300028c009202aa032b0030", 20),
                   "xs22_651u0uiz3543": ("006600a50081007e000000780048", 20),
                   "xs22_69b8brz035a4": ("01b001a2002501aa012c00c0", 20),
                   "xs22_8e1t6zwqb871": ("004001c0020b02fa0182001c0010", 20),
                   "xs22_gbbojd4koz11": ("?-shillelagh_siamese_hooks_and_block", 20),
                   "xs22_i5p6kk8zd543": ("01b200a500990066001400140008", 20),
                   "xs22_178bbgz311dd": ("010c01c8002801ab01ab0010", 20),
                   "xs22_31e8zcid1d96": ("0306020901d6005000160012000c", 20),
                   "xs22_6t1e8zwdd1e8": ("010001c0002801ae01a1001d0006", 20),
                   "xs22_0g88brz2fgmd": ("03600356004d0041003e0008", 20),
                   "xs22_gbbo7picz121": ("?-mango_siamese_bookend_on_R-loaf_and_block", 20),
                   "xs22_ml1u0uiz1243": ("006c00aa0081007e000000780048", 20),
                   "xs22_g2596zdll913": ("?-long_Z_and_loaf_and_R-bee", 20),
                   "xs22_c8allicz3543": ("beehive_with_bend_tail_siamese_G", 20),
                   "xs22_oe1t6zw9f033": ("00600060000601fd0121000e0018", 20),
                   "xs22_gbbo3ticz121": ("?-R-bee_siamese_boat_and_R-loaf_and_block", 20),
                   "xs22_0o4kl3z9f0dd": ("0180015b005b0040003f0009", 20),
                   "xs22_699egmaz6513": ("00c600a90029006e00100016000a", 20),
                   "xs22_8e1lmz9f0346": ("012801ee00010075009600c0", 20),
                   "xs22_69e0uh3z6513": ("?-long_hook_on_hook_and_R-bee", 20),
                   "xs22_069jz69e1d96": ("00c0012601c9003301a0012000c0", 20),
                   "xs22_69e0uicz6513": ("?-hook_on_cap_and_R-bee", 20),
                   "xs22_c9baik8z3553": ("006c00a900ab006a001200140008", 20),
                   "xs22_ca9b8brz0253": ("00d800d0001000d6009500520030", 20),
                   "xs22_0cp3z2ehu156": ("?-great_snake_eater_siamese_carrier_siamese_eater_siamese_long_bee", 20),
                   "xs22_69e0uicz2553": ("?-cap_on_R-bee_and_R-bee", 20),
                   "xs22_ca1u0uiz3543": ("006c00aa0081007e0000001e0012", 20),
                   "xs22_6t1e8gz5b871": ("00ca017d010100ee00280010", 20),
                   "xs22_caab8oz311dd": ("?-very_long_eater_siamese_long_Z_siamese_eater_and_block", 20),
                   "xs22_xoie0ehrz653": ("030002b000a002a80318000600050003", 20),
                   "xs22_02llmzcngc23": ("018002e20215019500560060", 20),
                   "xs22_0i5lmz8llc23": ("?-shillelagh_on_R-bee_and_R-bee", 20),
                   "xs22_caabkk8z3553": ("006c00aa00aa006b001400140008", 20),
                   "xs22_mp3s4oz0345d": ("00d0013c0182007a004b0030", 20),
                   "xs22_354kl3z32qq1": ("?-dock_and_long_hook_and_block", 20),
                   "xs22_3pmgmiczwcic": ("?-shillelagh_siamese_worm_and_beehive", 20),
                   "xs22_g88bbgz1pl5d": ("very_long_R-bee_and_hook_and_block", 20),
                   "xs22_cc0f9gz319ld": ("00d800d0001203d502560020", 20),
                   "xs22_0mkiqb96z346": ("006000ba00860070001e000100050006", 20),
                   "xs22_g88bbgzd5lp1": ("?-very_long_R-bee_and_hook_and_block", 20),
                   "xs22_8kkjqicz4aa6": ("00880154015400d3001a0012000c", 20),
                   "xs22_j9acz1255d96": ("0198012400aa006a000b00090006", 20),
                   "xs22_ad1qcz3543ac": ("0180014c007a008100ad006a", 20),
                   "xs22_gbaq3ob96z11": ("0180012800ee000100f50096", 20),
                   "xs22_69f0rbz25521": ("?22?046", 20),
                   "xs22_3hu0mmzc87011": ("siamese_long_hooks_and_blocks", 20),
                   "xs22_2lmgmmz346221": ("?-racetrack_and_boat_and_block", 20),
                   "xs22_cimg6p3zca221": ("018c015200560050002600190003", 20),
                   "xs22_8o0e952zqb853": ("03480178010000ae006900050002", 20),
                   "xs22_0mlhege2z3443": ("0060009600950071000e0010000e0002", 20),
                   "xs22_8kkmhf033z066": ("01b001a8002e0021001e000000060006", 20),
                   "xs22_g0gil96zdlge2": ("01b002a0021001d2005500090006", 20),
                   "xs22_0ggm453z1qaar": ("?-hook_and_long_R-bee_and_table", 20),
                   "xs22_0ggca96z3egnc": ("?-paperclip_on_R-loaf", 20),
                   "xs22_035s2djoz6511": ("00c000a30025003c0002000d00130018", 20),
                   "xs22_69a4z259d1ego": ("0300020001c0002001a4012a00a90046", 20),
                   "xs22_699egmiczw256": ("0060009600950071000e001000280018", 20),
                   "xs22_69e0mmz697011": ("?-R-bees_and_blocks", 20),
                   "xs22_c89n8b52z3521": ("?-loop_siamese_tub_at_loop_siamese_tub", 20),
                   "xs22_xok97079cz653": ("boat_with_leg_on_ship_and_cis-hook", 20),
                   "xs22_3lmgml2z346w1": ("?-worm_and_ship_and_boat", 20),
                   "xs22_4a9egoz697066": ("00d800d0000e00e9012a00c4", 20),
                   "xs22_ca9mgmiczw346": ("?-big_S_on_R-loaf", 20),
                   "xs22_gbb8b96z12552": ("0060009000d2001500d500d2000c", 20),
                   "xs22_69eg6p3z4a611": ("0180013000c8001800e6012500c2", 20),
                   "xs22_0mlhu0ooz34a4": ("0060009601550091001e000000180018", 20),
                   "xs22_w2llm853z4a96": ("0198012400b8004000380004000a00090006", 20),
                   "xs22_4a9riicz062ac": ("00600090009301b5012400a60040", 20),
                   "xs22_2llmggzraa401": ("?-hat_siamese_very_long_hook_and_?-R-bee", 20),
                   "xs22_0mlhu0ok8z346": ("?22?010", 20),
                   "xs22_0o8bl46zc4lp1": ("0180009802a8032b003500040006", 20),
                   "xs22_g88bb8oz178b5": ("?-very_very_long_hook_siames_loop_and_block", 20),
                   "xs22_g08o696zdlgf2": ("01b002a0020801f8004600090006", 20),
                   "xs22_6is0si53z3443": ("?-hook_siamese_pond_on_boat_with_leg", 20),
                   "xs22_xcp3qicz4aa43": ("00c0012000d00010001600350021000e0018", 20),
                   "xs22_ca1v0sicz0643": ("006000500010001600d5009500520030", 20),
                   "xs22_651u0eicz6511": ("?-worm_siamese_eater_and_R-bee", 20),
                   "xs22_gj1u0uicz1243": ("006000560015001500d6009000500020", 20),
                   "xs22_o4c0si96zc953": ("0198012400ac0060001c001200090006", 20),
                   "xs22_gillicz1w6aa6": ("00c0014c015200d5001500120030", 20),
                   "xs22_2lligz34269ko": ("03000280013000d2005500950062", 20),
                   "xs22_2llmggz3kq221": ("011802a502ab01a800280030", 20),
                   "xs22_02llmzc960696": ("0180012200d5001500d6012000c0", 20),
                   "xs22_0c9baicz69d11": ("00c0012c01a9002b002a0012000c", 20),
                   "xs22_69b8bb8ozw253": ("006c00ac0080007f0001001800280010", 20),
                   "xs22_0mkhfgkcz3443": ("0060009600940071000f00100014000c", 20),
                   "xs22_259mkk8zca2ac": ("loaf_siamese_long_beehive_and_trans-C", 20),
                   "xs22_ciqjkkozw4aa4": ("0060009000b20195005500520030", 20),
                   "xs22_699e0uiczw253": ("?-cap_on_boat_and_R-pond", 20),
                   "xs22_w6t1ug8oz3543": ("00c0012001a0002d002b006800480030", 20),
                   "xs22_0oe138n96z643": ("?-R-bee_siamese_tub_and_shillelagh_siamese_eater", 20),
                   "xs22_6996o8zciic32": ("?-pond_on_table_on_pond", 20),
                   "xs22_09f0si96z2553": ("?-R-mango_on_R-bee_and_table", 20),
                   "xs22_g88b9icz178b6": ("00600090012601ad0021002e0018", 20),
                   "xs22_04aabqiczc871": ("0180010400ea002a000b001a0012000c", 20),
                   "xs22_ciab94ozw11dd": ("0060009000a801a8012b004b0030", 20),
                   "xs22_0ca1t2sgz255d": ("004000ac00aa01a1001d0002001c0010", 20),
                   "xs22_0o4s3qicz3543": ("006000b80084007c0003001a0012000c", 20),
                   "xs22_259acz311d553": ("008c0148012800ab006a000a000c", 20),
                   "xs22_0g8o696z3egna": ("01800240018a007d0041002e0018", 20),
                   "xs22_0oggraarz4aa4": ("?-table_siamese_table_and_table_and_beehive", 20),
                   "xs22_3lkkl3z32w256": ("trans-boat_with_long_nine_and_cis-dock", 20),
                   "xs22_2llmgmicz32w1": ("00c00088007e0001007500960060", 20),
                   "xs22_gbb88a6z11d96": ("00c000a00026002901ab01a80018", 20),
                   "xs22_w4a9bqicz6513": ("0180012000e00006003d0041002e0018", 20),
                   "xs22_8u1v0fpz01221": ("006c002a002a006b004a0012000c", 20),
                   "xs22_69b8f1e8z0352": ("006c00aa008a007b0000006000500020", 20),
                   "xs22_j9e0ooz115aa6": ("0198012800ea000500350036", 20),
                   "xs22_g8e1vg33z1253": ("00d800d4001400160031000d000a0004", 20),
                   "xs22_651u0uizw178c": ("?-worm_siamese_eater_and_table", 20),
                   "xs22_wml1uge2z2543": ("00c0012000a0006c000a006a004b0030", 20),
                   "xs22_3lkl3z12269a4": ("?-long_bee_siamese_loaf_and_C", 20),
                   "xs22_4a9b8b96zx356": ("006c00aa0081007e0000001800280030", 20),
                   "xs22_0ciqb96z622ac": ("00c0012001a300b5009400640006", 20),
                   "xs22_4a9b8brzw6511": ("00d800d4001400d5009300500020", 20),
                   "xs22_2llmgmqz01226": ("?-long_Z_siamese_eater_siamese_snake_and_R-bee", 20),
                   "xs22_c871u0uizx643": ("0048007800060079008300e000100030", 20),
                   "xs22_6ac0si96z6513": ("?-R-mango_on_hook_and_ship", 20),
                   "xs22_caabo7hz33x11": ("006c006a000a000b001800270031", 20),
                   "xs22_69acz651315ac": ("0180014000a00020006c002a00a900c6", 20),
                   "xs22_cil6gmiczw343": ("0030004800ae0061000e006800480030", 20),
                   "xs22_6ac0si96z2553": ("?-R-bee_on_R-mango_and_ship", 20),
                   "xs22_4ac0si53z6953": ("?-boat_with_leg_on_R-loaf_and_boat", 20),
                   "xs22_3iabaicz34311": ("00c60049005600d4005400480030", 20),
                   "xs22_mm0e9a4z10796": ("00d800d0000e00e9012600a00040", 20),
                   "xs22_64kmkl3z696w1": ("?-table_siamese_eater_and_beehive_with_long_leg", 20),
                   "xs22_2llmz32011dic": ("?-beehive_with_tail_siamese_hook_and_R-bee", 20),
                   "xs22_gbbo79koz1221": ("?-boat_with_leg_on_R-pond_and_block", 20),
                   "xs22_g88baicz178b6": ("0060009000a601ad0021002e0018", 20),
                   "xs22_4a9bqicz0354c": ("0060009000b301a2012a00ac0040", 20),
                   "xs22_06996z355d952": ("R-racetrack_II_and_pond", 20),
                   "xs22_0ca1vg33z6513": ("00d800d4001200160030000e00090003", 20),
                   "xs22_g88baicz178b5": ("0060009000aa01ad0021002e0018", 20),
                   "xs22_4aab8ob96z033": ("00c8014e010100fe002000060006", 20),
                   "xs22_259mgmiczwca6": ("00800140012300d5001600d000900060", 20),
                   "xs22_69b88gzx3egnc": ("018002e0021001c80068000b00090006", 20),
                   "xs22_3jgf9a4zw3453": ("00c000c8000e00f1009500560020", 20),
                   "xs22_04a96z4a9r996": ("00c0012001260369012a01440080", 20),
                   "xs22_0178cz69d1dic": ("0180024001ac002801a7012100c0", 20),
                   "xs22_0g6p3sj96z321": ("0180014000ac002a004900550036", 20),
                   "xs22_ca9baicz33032": ("006c006a0009006b004a0012000c", 20),
                   "xs22_g8ehikoz178a6": ("003000e8010e015100d200140018", 20),
                   "xs22_651u0ok8zwdjo": ("?-worm_siamese_shillelagh_and_?-boat", 20),
                   "xs22_69akgoz697066": ("00d800d0001400ea012900c6", 20),
                   "xs22_cc0s2pmz66074": ("00cc00cc000000fc008200190016", 20),
                   "xs22_wgbaqb96z6521": ("0180014000a00048003e0001003d0026", 20),
                   "xs22_39e0oka6z2553": ("00c20095007500060018002800500060", 20),
                   "xs22_0g8e1dqz6b871": ("?22?036", 20),
                   "xs22_gg0si52zpgf0cc": ("0330021001e0001c019201850002", 20),
                   "xs22_0gg31eoz345lp1": ("006001d002130315003400240018", 20),
                   "xs22_025a88gz69d1dd": ("00c0012201a5002a01a801a80010", 20),
                   "xs22_w62s0fhoz69521": ("trans-loaf_with_long_nine_and_?-long_hook", 20),
                   "xs22_64kmhegoz03443": ("0060002600290069008e007000080018", 20),
                   "xs22_0c82uge13z6513": ("?-integral_on_hook_on_carrier", 20),
                   "xs22_69ac0sicz0c453": ("00c0012300a2006a000c007000900060", 20),
                   "xs22_og88ci96z6a871": ("00d80150010800e8002c001200090006", 20),
                   "xs22_3lmgeik8z01243": ("?-R-loaf_at_R-loaf_and_ship", 20),
                   "xs22_0g84cj96z6b871": ("00c00170010800e4002c001300090006", 20),
                   "xs22_oo0u93zw4706ac": ("0180014000c3000900fe008000180018", 20),
                   "xs22_04a9e0eicz3156": ("0060012001c000020075009500560020", 20),
                   "xs22_695m88gz69a511": ("00c60129014500da002800280010", 20),
                   "xs22_o8g0s2qrz06943": ("01b000b00080007c0002001900260030", 20),
                   "xs22_0iu0e96z643033": ("00c00092007e0000006e00690006", 20),
                   "xs22_c82t2sgz330343": ("006c00680002007d0082007c0010", 20),
                   "xs22_259mggkcz06aa6": ("trans-loaf_with_long_nine_and_?-cap", 20),
                   "xs22_6a88baaczw6513": ("006000500013001500d4005600500030", 20),
                   "xs22_8kihfgkczx3426": ("005000680008006e009100d200140018", 20),
                   "xs22_259mk4ozca2641": ("01820145004900d6009400240018", 20),
                   "xs22_0br0rdz3210123": ("?-hook_siamese_snake_and_hook_and_block", 20),
                   "xs22_4a9eg8oz0358b6": ("004000ac012a00e1001d00260030", 20),
                   "xs22_0g88b96z8ll913": ("?-scorpio_siamese_Z_and_beehive", 20),
                   "xs22_259mggkczwciic": ("trans-loaf_with_long_nine_and_cis-pond", 20),
                   "xs22_39u0ml3z321011": ("?-hook_siamese_hook_and_ship_and_block", 20),
                   "xs22_35a8c8a6zw3596": ("0180014000ac002a0069002600a000c0", 20),
                   "xs22_0caab96z253033": ("0060009600d60050005600350002", 20),
                   "xs22_8kiab8oz06a871": ("0030002801ae00a1009500560020", 20),
                   "xs22_69b88cicz0c871": ("?-worm_siamese_beehive_and_eater", 20),
                   "xs22_4s0si96z116aa4": ("?-R-bee_on_table_and_R-mango", 20),
                   "xs22_c88ehjz33w1256": ("?-eater_siamese_table_on_long_ship_and_block", 20),
                   "xs22_39e0eigozwca26": ("?-cis-legs_and_hooks", 20),
                   "xs22_32qb8n9a4zx121": ("012c01ea00090076004800280010", 20),
                   "xs22_69a4z2lll96z01": ("031004ab02aa012a00240018", 20),
                   "xs22_354mhf0cczx146": ("0198012800eb000b0030002000080018", 20),
                   "xs22_660u1acz330346": ("006600660000007e008100ca000c", 20),
                   "xs22_39e0o4oz699611": ("0186012900e90006003800480030", 20),
                   "xs22_04aab96zca5113": ("trans-boat_with_long_leg_and_?-racetrack", 20),
                   "xs22_g88b96z12hu0oo": ("03000306000903cb022800480030", 20),
                   "xs22_069b88cz311d96": ("?-rotated_worm", 20),
                   "xs22_0g88b96zohf033": ("0300023001e80008006b00690006", 20),
                   "xs22_4a96z2lll96z01": ("011002ab04aa032a00240018", 20),
                   "xs22_699e0eiczw6511": ("00600096009500750002001c00200030", 20),
                   "xs22_4aabk4oz259611": ("004400aa012a00cb003400240018", 20),
                   "xs22_35ac0si6z02553": ("?-R-bee_on_hook_and_long_ship", 20),
                   "xs22_03lkkl3z69a401": ("cis-loaf_with_long_leg_and_cis-dock", 20),
                   "xs22_ciab96zw113156": ("00c000a000260069002b002a0012000c", 20),
                   "xs22_4aacggm96zw696": ("?-beehive_line_beehive_on_R-bee", 20),
                   "xs22_2llmgmmz3201w1": ("?22?040", 20),
                   "xs22_04aabaa4z4a953": ("00800144012a00aa006b000a000a0004", 20),
                   "xs22_256o8gzrhe1221": ("?-boat_on_R-loaf_on_C", 20),
                   "xs22_xca96z6t1t6zw1": ("03000480029801ae0021002e0018", 20),
                   "xs22_08u1lmzoi70121": ("0300024800fe0001003500560020", 20),
                   "xs22_0mligz346069ko": ("03000280012000d0001200d500960060", 20),
                   "xs22_0mlhik8z346066": ("0060009600d5001100d200d40008", 20),
                   "xs22_330f92sgzw2553": ("00d800d40012001a0003001c00240018", 20),
                   "xs22_gg0si52zdlge21": ("01b002b0020001dc005200250002", 20),
                   "xs22_0mligz346069ic": ("01800240012000d0001200d500960060", 20),
                   "xs22_0cimkl3z62ac01": ("01800158005000d3009500640006", 20),
                   "xs22_g39u0mmz11x346": ("?-hook_siamese_carrier_and_hook_and_block", 20),
                   "xs22_69e0o4oz699701": ("?-R-pond_on_beehive_and_R-bee", 20),
                   "xs22_0ca9e0eicz2552": ("?-table_siamese_loaf_and_R-bee_and_beehive", 20),
                   "xs22_xraa4zxol3z653": ("?-hat_on_long_snake_on_ship", 20),
                   "xs22_j9c0c4oz11dd11": ("01980128006b000b006800480030", 20),
                   "xs22_039e0okcz4a953": ("[[R-mango_on_ship and bookend]]", 20),
                   "xs22_0oo0e93zoie033": ("0300025801d80000006e00690003", 20),
                   "xs22_39u0ehbgz321x1": ("00c600aa0028006a002500a200c0", 20),
                   "xs22_39u0u1eozw1221": ("00c400aa002a006b002900240018", 20),
                   "xs22_08e1t2sgz65123": ("00c000a8002e0041007d0002001c0010", 20),
                   "xs22_3lk2q4oz0d8611": ("0180015b0051008600b800480030", 20),
                   "xs22_3lkmk46z320146": ("00c600aa0028006c002900230060", 20),
                   "xs22_6996k4ozc97011": ("0186012900e90006003400240018", 20),
                   "xs22_0c8970si6z2553": ("00c0012000e0000600e4009500130030", 20),
                   "xs22_0mmggm96z32w66": ("00600090006b000b00080068006a0006", 20),
                   "xs22_2lla8cz6430352": ("00c200950075000a006800ac0040", 20),
                   "xs22_0mligoz34606ac": ("0180015800d0001200d500960060", 20),
                   "xs22_0ckgo0uh3z62ac": ("018001400046005200dc000000070009000c", 20),
                   "xs22_g8o0uh3z1qq221": ("0300023001e80008006b004b0030", 20),
                   "xs22_354miczw122qic": ("03000280009001a8012800cb00090006", 20),
                   "xs22_069acz4a511d96": ("00c0012001a0002c002a00a901460080", 20),
                   "xs22_cc0v1u0oozx123": ("?22?054", 20),
                   "xs22_0ml1e8z3201178c": ("0180010000e8002e0021001500560060", 20),
                   "xs22_0660u156z4a9611": ("00c00140010800f8000600c900c50002", 20),
                   "xs22_g88ge1ege1e8z11": ("0c00091006ab00aa00aa0044", 20),
                   "xs22_0ml1e8z121079a4": ("00800140012800ee0001003500560020", 20),
                   "xs22_0ckgill2zo8a6w1": ("0300010c015400d00012001500350002", 20),
                   "xs22_6a88baicz035421": ("006000560015001100d2005400480030", 20),
                   "xs22_0gill2z32w34aic": ("?-loaf_with_trans-tail_siamese_long_hook_and_cis-beehive", 20),
                   "xs22_0gill2z346069k8": ("01000280012200d5001500d200900060", 20),
                   "xs22_62s0si52z321074": ("?-tub_with_leg_siamese_table_and_dock", 20),
                   "xs22_660u1v04aiczy01": ("?-very_long_R-bee_and_loaf_and_block", 20),
                   "xs22_0ggc97079koz321": ("?-hook_on_ship_and_boat_with_leg", 20),
                   "xs22_gg0gbq2sgz0345d": ("[[ship with 4 tails]]", 20),
                   "xs22_259e0o4kozw3543": ("00c0012000a60069000b006800480030", 20),
                   "xs22_xca952zml552z11": ("?-R-mango_and_long_R-bee_and_block", 20),
                   "xs22_69acz25t1h3zx11": ("031004a802ae01a100230030", 20),
                   "xs22_2ego2u0u156zy21": ("030004b306a200aa00ac0040", 20),
                   "xs22_252s0ccz3543033": ("006c006c0000007c008200a50062", 20),
                   "xs22_0gbb8b96z121w33": ("006c00ac0080007c000200650062", 20),
                   "xs22_352s0g08ozx8lld": ("03000280010000e200150035001600400060", 20),
                   "xs22_g88m5hu06a4z121": ("0200050004b0031200d500960060", 20),
                   "xs22_0cc0ca52z69d113": ("00c0012c01ac0020002c006a00050002", 20),
                   "xs22_o48ge5hu0ooz011": ("0300049b054b026800480030", 20),
                   "xs22_0ca1u066z259611": ("00c000c0000800f8010600a9006a0004", 20),
                   "xs22_0cc0ca23z69d113": ("?-worm_and_eater_and_block", 20),
                   "xs22_2llmz12ia9ozw11": ("030001200556065500550022", 20),
                   "xs22_xca1u0oozca2311": ("0300020001c00070000b006b004800280010", 20),
                   "xs22_660u1u06996zy01": ("very_long_bee_and_pond_and_cis-block", 20),
                   "xs22_35akggzx66074ko": ("03000280014000ac002c0020001c000400050003", 20),
                   "xs22_08e1t6z6t1hzw11": ("030005c0042303a100ae0018", 20),
                   "xs22_08o0ehe0eicz321": ("?22?035", 20),
                   "xs22_0641v0kcz4a9611": ("00800146012400c1003f00200014000c", 20),
                   "xs22_0651u066z4a9611": ("00c000c0000800f80106014900c50002", 20),
                   "xs22_wg8kic0fhoz2543": ("?-loaf_at_loaf_and_long_hook", 20),
                   "xs22_256o8geik8zx643": ("?-C-on_boat_on_R-loaf", 20),
                   "xs22_2596z3ll552z011": ("?-very_long_R-bee_and_loaf_and_block", 20),
                   "xs22_cia40v1u0oozy21": ("?-loaf_and_very_long_R-bee_and_block", 20),
                   "xs22_31ke1lmzx110256": ("01980124006c0020004c003200050003", 20),
                   "xs22_25akgozw4a60796": ("?-barge_with_leg_on_R-bee_and_boat", 20),
                   "xs22_0gilmzr6ge21z01": ("036004d0021201d500560020", 20),
                   "xs22_354c0cczx69d113": ("?22?050", 20),
                   "xs22_25a8c0c4ozx69d11": ("0080014000a000260069000b006800480030", 20),
                   "xs22_256o8g0sia4zx643": ("02000506030900ca00ac002000a000c0", 20),
                   "xs22_354kmzo4k543z011": ("big_S_and_?-long_hook", 20),
                   "xs22_gg0s2ac0fhoz1221": ("big_S_and_?-long_hook", 20),
                   "xs22_xg84o0uh3z4a9611": ("?22?027", 20),
                   "xs22_0gbb88gz321w3ego": ("0300020001d000680008000b002b00500060", 20),
                   "xs22_0696z355ll2zw121": ("006006500952065500560020", 20),
                   "xs22_wgj1u0ok46z25421": ("mango_with_long_nine_and_?-eater", 20),
                   "xs22_2560u15u0oozy111": ("023005480358004b004b0030", 20),
                   "xs22_0g8ge970si6z1221": ("0300048002860164005500530030", 20),
                   "xs22_gwca96z1p5p13zw1": ("?-long_Z_and_R-loaf_and_beehive", 20),
                   "xs22_0gilmz346kk3zx11": ("?-mirror_and_boat_and_block", 20),
                   "xs22_641v04s0796zy011": ("030c0509056b024800480030", 20),
                   "xs22_wo4a96z2ldz01256": ("0c0012000a03040503b200ac0040", 20),
                   "xs22_356o8gzy01470sic": ("boat_with_leg_on_ship_and_shift_R-bee", 20),
                   "xs22_8ko0o4c32aczy0346": ("?-eater_on_dock_and_ortho-boat", 20),
                   "xs22_651u08ozy01210796": ("03000480068000b000900056002500050002", 20),
                   "xs22_660u1eg628czy0121": ("004006ac06a900a3009000500020", 20),
                   "xs22_259eg8gzy0122dik8": ("?-R-loaf_on_loaf_at_loaf", 20),
                   "xs22_wg842u0696z254311": ("0300048002e001100092005500350002", 20),
                   "xs22_2596o80u156zy0121": ("03060489068a00b4009000500020", 20),
                   "xs22_651u08o0eiozy0121": ("03000486068400b5009300500020", 20),
                   "xs22_y2ca952zg8o6513z11": ("?-hook_on_ship_and_R-mango", 20),
                   "xs22_69iczx115acggzy4123": ("?-mango_line_boat_on_ship", 20),
                   "xs23_259e0ehu0ui": ("?23?002", 13),
                   "xs23_69acz69d1d96": ("?23?006", 13),
                   "xs23_69b8b96z033033": ("?23?009", 13),
                   "xs23_0ca96z69d1d96": ("?23?018", 14),
                   "xs23_gbb8b96z123033": ("?23?010", 14),
                   "xs23_xrhe0ehrz253": ("?23?008", 15),
                   "xs23_cie0e9jzw11dd": ("?23?013", 15),
                   "xs23_256o8gzx6430ehr": ("?23?011", 15),
                   "xs23_0354ljgz8kc32023": ("?-C_and_boat_on_C", 15),
                   "xs23_ml1e8gzdl871": ("01b602b5020201dc00500020", 16),
                   "xs23_0caabqicz2596": ("?23?004", 16),
                   "xs23_3lkkl3z342643": ("00c600a9002b002a00a900c6", 16),
                   "xs23_02596z699r996": ("00c00122012503690126012000c0", 16),
                   "xs23_9f0s26z3543033": ("009600f50001003e004000660006", 16),
                   "xs23_39e0o4czc970123": ("?-hook_and_hook_and_C", 16),
                   "xs23_4ais0s2qb96zy21": ("?23?017", 16),
                   "xs23_651u0o4kozw3543": ("?-big_S_siamese_worm", 16),
                   "xs23_699e0o4k8zw69521": ("?23?014", 16),
                   "xs23_xg8o652zm2s346z11": ("?23?005", 16),
                   "xs23_69b8brz6996": ("01b001a0002601a9012900c6", 17),
                   "xs23_g88bbgzdd1dd": ("?-very_long_R-bee_and_3_blocks", 17),
                   "xs23_69b8brz0bd11": ("01b001a8002801ab012d00c0", 17),
                   "xs23_okihf0f9z6a4": ("012001e0000001e00110009200550036", 17),
                   "xs23_259e0ehe0e96": ("?-R-loaf_and_long_bee_and_R-bee", 17),
                   "xs23_69b8bqicz0352": ("006800ae0081007d0006006000500020", 17),
                   "xs23_0mlhu0ooz34ac": ("0060009601550191001e000000180018", 17),
                   "xs23_69b88b9czw2553": ("006600a40081007f0000001c00240018", 17),
                   "xs23_256o8gehrzx643": ("?-C_on_boat_on_C", 17),
                   "xs23_c8970sicz06953": ("?23?019", 17),
                   "xs23_69ac0siiczw2552": ("?-R-pond_on_beehive_and_R-loaf", 17),
                   "xs23_259ac0c4ozx69d11": ("big_S_and_?-R-mango", 17),
                   "xs23_0g8ka96zraahz0121": ("?-R-loaf_at_loaf_and_R-loaf", 17),
                   "xs23_259m88gzy0123ciic": ("?23?016", 17),
                   "xs23_69b8baarzx33": ("009600f5000100fe008000180018", 18),
                   "xs23_259e0ehe0eic": ("?-R-loaf_and_long_beehive_and_R-bee", 18),
                   "xs23_0gs2arz3egld": ("03600156011500e1002e0018", 18),
                   "xs23_3lkkl3z32w696": ("beehive_with_long_nine_and_cis-dock", 18),
                   "xs23_3lkkl3z32w69c": ("018c015400500050015601890003", 18),
                   "xs23_0ca9bob96z253": ("00d80154010200fe0020000600050002", 18),
                   "xs23_ok4o7picz2543": ("00600090005000d600950069000a000c", 18),
                   "xs23_4aabaicz69d11": ("00c4012a01aa002b002a0012000c", 18),
                   "xs23_ciiriicz062ac": ("00600096009401b5009300900060", 18),
                   "xs23_ml56z18f0c453": ("?-cap_and_long_hook_and_eater", 18),
                   "xs23_gjlmgmicz1w66": ("006000560035000100fe008000180018", 18),
                   "xs23_0gbbo7picz321": ("?23?007", 18),
                   "xs23_okkmgu156zw66": ("00c0012801ae0021003f0000000c000c", 18),
                   "xs23_c88b96z33035ac": ("?-worm_and_long_ship_and_block", 18),
                   "xs23_mmgmk453z1w643": ("?-worm_and_long_hook_and_block", 18),
                   "xs23_gbaab96z123033": ("003600560040003e0001003d0026", 18),
                   "xs23_4a96ki6z699701": ("00c4012a012900e6001400320006", 18),
                   "xs23_3lk6kl3zca1011": ("?-hook_siamese_hook_and_long_snake_and_block", 18),
                   "xs23_03p6ge96z69521": ("00c0012300b900460030000e00090006", 18),
                   "xs23_2lla8a6z343033": ("006200950075000a0068006a0006", 18),
                   "xs23_ml1u0ooz11078c": ("00d80158010000fe000100330030", 18),
                   "xs23_178bb8oz069d11": ("010001c6002901ab01a800280030", 18),
                   "xs23_g39cggzdlhe221": ("01b002a3022901cc005000500020", 18),
                   "xs23_3hu0o4czc870123": ("?-long_hook_siamese_long_hook_and_C", 18),
                   "xs23_0gill2sgz346074": ("?-R-G_and_beehive_with_tail", 18),
                   "xs23_69b88c8a6zx3552": ("?-worm_siamese_hook_and_R-bee", 18),
                   "xs23_0mll2z344lkk8zx1": ("?23?012", 18),
                   "xs23_69acz03ll552zw11": ("?-very_long_R-bee_and_R-loaf_and_block", 18),
                   "xs23_259m88gzy0123ci96": ("?-loaf_at_R-loaf_on_R-mango", 18),
                   "xs23_xg84s0si52z4a9611": ("R-loaf_at_loaf_and_?-tub_with_leg", 18),
                   "xs23_ca9licz359a6": ("?-R-mango_siamese_loaf_on_bookend_siamese_mango", 19),
                   "xs23_69b88gz69lld": ("018c02520355005500560020", 19),
                   "xs23_caabob96z352": ("006c00aa004a000b0018000b00090006", 19),
                   "xs23_9f0f9z311d96": ("worm_and_tables", 19),
                   "xs23_69aczciqb952": ("01860249034a016c012000a00040", 19),
                   "xs23_4a9b8brz2553": ("00d800d0001000d6009500550022", 19),
                   "xs23_gbb8b96zc953": ("0190012b00ab0068000b00090006", 19),
                   "xs23_ca9b8brz3123": ("006c006a0001007f0040000b000d", 19),
                   "xs23_6996z69d1dic": ("?23?001", 19),
                   "xs23_ml1u0uiz2543": ("006a00ad0081007e000000780048", 19),
                   "xs23_39e0uicz6953": ("?-R-loaf_on_cap_and_hook", 19),
                   "xs23_69e0uicz6953": ("?-R-loaf_on_cap_and_R-bee", 19),
                   "xs23_gbb88gzdd1dd": ("01b001ab002b01a801a80010", 19),
                   "xs23_3hu08oz3egld": ("0318022e01e1001500560060", 19),
                   "xs23_3hu0oozciq226": ("0306022901eb00080068006c", 19),
                   "xs23_6a8cgn96z2553": ("0062005500150036000800e800900060", 19),
                   "xs23_wmk2qb96z6943": ("00c00174010c00e0002c000a000900050002", 19),
                   "xs23_gg0si96zdlka6": ("?-R-bee_siamese_boat_and_R-mango_and_block", 19),
                   "xs23_0dbgz69d1eik8": ("01000280024001c0003001ab012d00c0", 19),
                   "xs23_3lkmkl3z346w1": ("00c600a9002b0068002800ac00c0", 19),
                   "xs23_3lkaacz34b413": ("018c0152005d00a200a8006c", 19),
                   "xs23_2llmz346074ko": ("03000280008000e0001600d500950062", 19),
                   "xs23_2lmgmqz346066": ("00da00d6001000d600950062", 19),
                   "xs23_db8baicz35421": ("00b600d5001100d2005400480030", 19),
                   "xs23_g886l56z178jd": ("0180028002b601990042005c0030", 19),
                   "xs23_mmgml56z1w643": ("?-worm_and_cap_and_block", 19),
                   "xs23_4a9baicz69d11": ("00c4012a01a9002b002a0012000c", 19),
                   "xs23_31egmiczca2ac": ("01830141004e015001960012000c", 19),
                   "xs23_4amge996zx3453": ("0060009600950072000c006800480030", 19),
                   "xs23_g88b96z11dmge2": ("004001c6020902cb01a800280030", 19),
                   "xs23_178baa4zckg853": ("anvil_and_?-cis-shillelagh", 19),
                   "xs23_0db8b5oz651311": ("00c000ad002b0068002b00250018", 19),
                   "xs23_69b88brz033032": ("006c0069000b0008006b004b0030", 19),
                   "xs23_0caab96z653033": ("?-R-racetrack_and_ship_and_block", 19),
                   "xs23_2lligz346069ic": ("01800240012000d0001200d500950062", 19),
                   "xs23_39e0u2sgz03543": ("00c000ac002a006a000b006800480030", 19),
                   "xs23_069b8b96z4a513": ("very_long_worm_and_trans-tub_with_leg", 19),
                   "xs23_0g88m552z2fgld": ("01000280028001b600550041003e0008", 19),
                   "xs23_cq1u0mmz012543": ("0068006e0001007d0082005c0030", 19),
                   "xs23_0gwci96zol55lo": ("trans-mango_with_long_leg_and_cis-dock", 19),
                   "xs23_03lkmik8z47066": ("00d800580040003e0001003a004c0060", 19),
                   "xs23_031e88gz69d1dd": ("00c0012301a1002e01a801a80010", 19),
                   "xs23_69mgmik8z04aa6": ("00c0012200d5001500d6009000500020", 19),
                   "xs23_o4ie0ehraa4z01": ("?-hat_siamese_C_and_?-R-mango", 19),
                   "xs23_0178b96z69d113": ("G_and_?-worm", 19),
                   "xs23_651ugmiczw4aa4": ("00c00140010200f5001500d200900060", 19),
                   "xs23_0c8970796z6953": ("?-cis-legs_and_R-loaf_and_R-bee", 19),
                   "xs23_0ca9lmz8kkd221": ("?-mango_siamese_bookend_on_bee_on_R-bee", 19),
                   "xs23_0oo0u156zcia611": ("?-worm_on_R-loaf_and_block", 19),
                   "xs23_09v0v9z32101252": ("?-tub_with_leg_siamese_table_and_long", 19),
                   "xs23_35a84ozw330f853": ("0180014000ac002c0040003f0001000a000c", 19),
                   "xs23_08u1qcz321078a6": ("00c00140010c00fa0001003e00480060", 19),
                   "xs23_wc897079a4z3156": ("?-cis-legs_and_R-loaf_and_hook", 19),
                   "xs23_69acz2ll553z011": ("?-very_long_R-bee_and_R-loaf_and_block", 19),
                   "xs23_09f0c8a6z651156": ("00cc008400780000006e002900230060", 19),
                   "xs23_0gbb8b96z321w33": ("00c600a60040003e000100350036", 19),
                   "xs23_0g88baicz6b8711": ("00c00170010800e8002b002a0012000c", 19),
                   "xs23_259acgciczw3543": ("00c0012200950075000a006800480030", 19),
                   "xs23_0o4s3qicz11078c": ("0060009000b30181007e004000380008", 19),
                   "xs23_03lkmk4oz696w11": ("00c0012300d500140016003400240018", 19),
                   "xs23_0gg08o653z32cll8": ("?-R-bee_on_long_integral_on_ship", 19),
                   "xs23_0gwc88a53zold113": ("?-Z_and_trans-boat_with_long_leg_and_ship", 19),
                   "xs23_4aicgg0si96zx1243": ("trans-loaf_at_loaf_on_?-R-mango", 19),
                   "xs23_w6996zo4id1156z01": ("mango_with_long_nine_and_cis-pond", 19),
                   "xs23_25a8c0c4ozw178711": ("0080014000a8002e0061000e006800480030", 19),
                   "xs23_ci4o0ehrzw11y0352": ("boat_on_C_and_?-R-mango", 19),
                   "xs23_y0g8o6952zo4kb221z01": ("?-cis-legs_siamese_loaf_on_loafs", 19),
                   "xs23_178nhe0ehr": ("03630155015400950063", 20),
                   "xs23_259e0mp3qic": ("0360054c042a03a900c6", 20),
                   "xs23_3pm4iu06996": ("?-shillelagh_siamese_snake_siamese_table_and_pond", 20),
                   "xs23_ca1v0rrz0643": ("00d800d8000000fe008100530030", 20),
                   "xs23_8u1v0rrz0123": ("?-very_very_long_bee_siamese_eater_and_blocks", 20),
                   "xs23_mm0u1qrz0343": ("00d800580080007e0001006e0068", 20),
                   "xs23_39e0mmz69b43": ("0186012900ed000200dc00d0", 20),
                   "xs23_3lkkl3z3ego1": ("031802ae00a100a302b00300", 20),
                   "xs23_69aba96z6953": ("00c6012900aa01ac00a0012000c0", 20),
                   "xs23_354micz2egnc": ("0308028e008101bd012600c0", 20),
                   "xs23_g39u0oozd5lo": ("?-siamese_hooks_and_hook_and_block", 20),
                   "xs23_g8ehjzd59aq1": ("01b000a8012e015103530020", 20),
                   "xs23_g88mhrzdd1e8": ("01b001a8002801d60111001b", 20),
                   "xs23_641343hu0uic": ("06c00a800a9306a9006c", 20),
                   "xs23_0j96z6b8raic": ("01800240014003660109017300c0", 20),
                   "xs23_39e0e970sia4": ("?-R-loaf_and_siamese_hooks_and_hook", 20),
                   "xs23_69b8brz65132": ("00d800d2001600d400950063", 20),
                   "xs23_c82t1qrz3543": ("00d80058008000be004100150036", 20),
                   "xs23_354czojd1d96": ("?-worm_siamese_shillelagh_and_?-eater", 20),
                   "xs23_0mlhe0ehrz32": ("018c015200560150018e00010003", 20),
                   "xs23_gbaa4ozdll91": ("01b002ab02aa012a00240018", 20),
                   "xs23_gbbobap56z11": ("?-long_on_shillelagh_and_block", 20),
                   "xs23_gbaa4ozd5lp1": ("01b000ab02aa032a00240018", 20),
                   "xs23_md1e8zdd1156": ("01b601ad0021002e00a800c0", 20),
                   "xs23_ca96z178bqic": ("0180024003400166010900ea002c", 20),
                   "xs23_gbaq3sj96z11": ("table_on_mango_siamese_bookend_and_hook", 20),
                   "xs23_6996z69d1dio": ("0300024001a0002601a9012900c6", 20),
                   "xs23_g6p3qiczd543": ("01b000a600990063001a0012000c", 20),
                   "xs23_8e1lmz39d543": ("0068012e01a100b500960060", 20),
                   "xs23_c88bbgzrb871": ("036c0168010800eb002b0010", 20),
                   "xs23_3pmgmmzx66074": ("00d800580040003e0002003400350003", 20),
                   "xs23_699egmiczw696": ("00c00120012600e9001600d000900060", 20),
                   "xs23_og4s3qicz6943": ("00d801300084007c0003001a0012000c", 20),
                   "xs23_035a4z699r996": ("00c001230125036a0124012000c0", 20),
                   "xs23_69b88brz04a96": ("01b001a00026002901a5012200c0", 20),
                   "xs23_mkl3z12470796": ("?-cis-R-legs_siamese_loaf_and_hook_and_R-bee", 20),
                   "xs23_4a9egmiczwoj6": ("00c0012001a0002c01d9024301400080", 20),
                   "xs23_651ugmiczwca6": ("00c00140010300f5001600d000900060", 20),
                   "xs23_ca9ba96z33w33": ("006c006a0009000b006a00690006", 20),
                   "xs23_0qmgm952zciic": ("trans-loaf_with_long_leg_siamese_snake_and_trans-pond", 20),
                   "xs23_c82u0mp3z3543": ("00c000ac0029004b0068000b00090006", 20),
                   "xs23_ca952z359mge2": ("00d801540252028d0101000e0008", 20),
                   "xs23_03lm0uicz6943": ("?-R-mango_and_cap_and_ship", 20),
                   "xs23_35is0si6zca43": ("018301450092007c00000070009000c0", 20),
                   "xs23_4a9b8brz04a96": ("01b001a0002601a9012500a20040", 20),
                   "xs23_69e0eicz69d11": ("00c6012901ae0020002e0012000c", 20),
                   "xs23_4aab8brz03552": ("00d800d0001200d5005500560020", 20),
                   "xs23_697o3qicz0643": ("006800ae00a100550016001000500060", 20),
                   "xs23_0ca9bojdz2552": ("00d80054008200be0060000600090006", 20),
                   "xs23_c9b8b96z33w33": ("006c0069000b0008006b00690006", 20),
                   "xs23_ca970796z3156": ("?-cis-legs_siamese_loaf_and_R-bee_and_hook", 20),
                   "xs23_0mllmz3460696": ("00c0012000d6001500d500960060", 20),
                   "xs23_c84s3qicz3543": ("006c00a80084007c0003001a0012000c", 20),
                   "xs23_39e0eicz69d11": ("0186012900eb000800e800900060", 20),
                   "xs23_gbb8bp2sgz123": ("00d800d4000200fa010b014000c0", 20),
                   "xs23_0mlhu0ooz32ac": ("0060005601550191001e000000180018", 20),
                   "xs23_3iabaa4zwd553": ("?-sesquihat_siamese_eater_siamese_table", 20),
                   "xs23_69acz259hu0oo": ("03000300000003c0022c012a00a90046", 20),
                   "xs23_651u0mmzwd543": ("00d000dc000200fa010b014000c0", 20),
                   "xs23_2lm88gz12ehld": ("01b002a8022801d600550022", 20),
                   "xs23_0mlhu0696z346": ("00c00140010000f0001200d500950062", 20),
                   "xs23_06996z39d1d96": ("00c0012001a6002901a901260060", 20),
                   "xs23_8u1v0fhoz1221": ("006c002a002a00ab00ca00090006", 20),
                   "xs23_06996zcid1d96": ("0180024601a9002901a6012000c0", 20),
                   "xs23_okihlmz66w643": ("00d800d40012001100d500960060", 20),
                   "xs23_caab9arz02552": ("?-very_long_Z_siamese_eater_siamese_snake_and_beehive", 20),
                   "xs23_69aczw699ria4": ("01800240014c00d20012001b0009000a0004", 20),
                   "xs23_ca9lmz3303496": ("00c00120009600750009006a006c", 20),
                   "xs23_gbbo3ticz0123": ("006c006a00050075009600500030", 20),
                   "xs23_3lkkmicz32w66": ("00c600aa00280028006b004b0030", 20),
                   "xs23_035acz69d1dic": ("0180024001ac002a01a5012300c0", 20),
                   "xs23_69mkkm952zw66": ("?-loaf_siamese_very_long_bee_siamese_bee_and_block", 20),
                   "xs23_okimgu156zw66": ("00c0012c01aa0021003f0000000c000c", 20),
                   "xs23_69b8bbgzw255d": ("00c0012001a4002a01aa01ab0010", 20),
                   "xs23_0ck5r8brz6221": ("?-loaf_with_cis-tail_siamese_eater_siamese_table_and_block", 20),
                   "xs23_0caabp2sgz653": ("0180014000c0000b00fa008200740018", 20),
                   "xs23_0g39u066z8lld": ("01800180000001e00256031500350002", 20),
                   "xs23_6a8oge1ego8a6": ("?-krake_siamese_eaters", 20),
                   "xs23_3pmkkmzcia401": ("?23?003", 20),
                   "xs23_39e0u2sgz0ca43": ("0180012300e5000200fc008000700010", 20),
                   "xs23_69b88ge2z69d11": ("00c6012901ab00280028001000e00080", 20),
                   "xs23_04ap3z6a870796": ("00c00144010a00f9000300e0012000c0", 20),
                   "xs23_25ac0sicz4a953": ("?-R-mango_on_R-bee_and_long_boat", 20),
                   "xs23_69baa4ozca2311": ("01860149004b006a002a00240018", 20),
                   "xs23_0ggo4q9bqicz32": ("0600040003a600bd0041002e0018", 20),
                   "xs23_0ggrhe0eicz346": ("01800280020001e20055001500560060", 20),
                   "xs23_4a9egmmz2553w1": ("006c006800080076009500550022", 20),
                   "xs23_0gbaa4oz8lld11": ("010002b002ab01aa002a00240018", 20),
                   "xs23_4a9fgbrz031221": ("?-boat_with_long_tail_on_loaf_siamese_table_and_block", 20),
                   "xs23_4a9e0uicz04a53": ("0060009000f0000c00ea012500a20040", 20),
                   "xs23_0oimgm952z4aa6": ("00c0012c00a80042003e0000000e00090006", 20),
                   "xs23_0g06996zol5d93": ("030002b000a001a6012900690006", 20),
                   "xs23_69ab8b96zw2552": ("006a00ad0081007e0000001800240018", 20),
                   "xs23_g069abgz19ll91": ("0030012002a602a9012a002b0010", 20),
                   "xs23_4a960gz69d1dl8": ("010002b001a0002601a9012a00c4", 20),
                   "xs23_0o4aab96z17871": ("00c0012001a000a800ae0041003e0008", 20),
                   "xs23_ml1u066z102596": ("00d80150010400fa000900c600c0", 20),
                   "xs23_gbb8brz123w123": ("00c600a50021003e000000360036", 20),
                   "xs23_0ca9e0eicz6952": ("00c0012c00aa0049000e0000000e0012000c", 20),
                   "xs23_69ba9la8ozx321": ("00d80164010800f7000900280030", 20),
                   "xs23_25akgka52zcia6": ("01820245014a00d400100014000a00050002", 20),
                   "xs23_04aaba96zca513": ("0180014400aa002a006b000a00090006", 20),
                   "xs23_3lkkl3z1226074": ("anvil_and_cis-dock", 20),
                   "xs23_39u0u1t6zw1221": ("00c600a9002b006a002a00240018", 20),
                   "xs23_gs2t1u0oozx343": ("0030004800a800ab01ab002800280010", 20),
                   "xs23_ca1t2sgz330343": ("006c006a0001007d0082007c0010", 20),
                   "xs23_cc0v1e8z330346": ("?-eater_siamese_very_very_very_long_hook_and_blocks", 20),
                   "xs23_0ca9lmz6511643": ("00c000ac002a002900d500960060", 20),
                   "xs23_g8ge9a4z123chr": ("0080015b025101c6003800480030", 20),
                   "xs23_ca2s53z3303453": ("?-worm_siamese_long_integral_and_block", 20),
                   "xs23_69bo8gzxcid552": ("018002400340006600490036001400140008", 20),
                   "xs23_69baa4oz039d11": ("00c0012c01a900ab00a800480030", 20),
                   "xs23_caakl3z3303452": ("006c006a000a0074009500a30040", 20),
                   "xs23_0ca970si6z2553": ("00c0012000e0000600e4009500530030", 20),
                   "xs23_699eg8oz0178b6": ("00c00128012e00e1001d00260030", 20),
                   "xs23_39u0u1t6z023w1": ("00c600a9002b006a002a00240060", 20),
                   "xs23_03hu06a4z32qic": ("008001400180000601e9022b03080018", 20),
                   "xs23_0g88bbgz12ehld": ("003000300000003c004200390006003400240018", 20),
                   "xs23_0okie0e93z4aa6": ("?-cis-legs_siamese_loaf_and_R-bee_and_hook", 20),
                   "xs23_0o4iqb96z11oi6": ("018002400340016c0129008300700010", 20),
                   "xs23_c9b871z3303156": ("?-alef_and_hook_and_block", 20),
                   "xs23_33gv1oka4z0643": ("01b001a20025002a006c002000a000c0", 20),
                   "xs23_25ac0si6z4a953": ("?-R-mango_on_hook_and_long_boat", 20),
                   "xs23_3lkl3z32025a8o": ("031802a800a002a80314000a00020003", 20),
                   "xs23_3hu0ooz34622ac": ("018c011200f60004003400350003", 20),
                   "xs23_j1u0ohf0ca4z11": ("?-dock_and_long_hook_and_boat", 20),
                   "xs23_651ugmicz03146": ("006000a600840079000b006800480030", 20),
                   "xs23_39e0u156zwc453": ("0180012000e3000200fa010c014000c0", 20),
                   "xs23_0178cz259d1d96": ("00c0012001a0002c01a8012700a10040", 20),
                   "xs23_4a9egeicz03543": ("003000480070000e0071009500560020", 20),
                   "xs23_j1u0ohf0352z11": ("063605150112015005600600", 20),
                   "xs23_g8e1t6zo5ldz01": ("031004a802ae01a1001d0006", 20),
                   "xs23_4a9egeioz03543": ("003000480068000b0075009400560020", 20),
                   "xs23_4s0v18oz39c321": ("0064013c0180007f004100280018", 20),
                   "xs23_cimggm952zwcic": ("01000280024001a00026002901a6012000c0", 20),
                   "xs23_2lmgml2z346221": ("0062009500d60050005600350002", 20),
                   "xs23_3jgf94oz344311": ("?-pond_siamese_loop_siamese_table_and_block", 20),
                   "xs23_0gbaa4ozrq2311": ("03600350004b006a002a00240018", 20),
                   "xs23_69b8brz033w123": ("00c600a60020003e000100350036", 20),
                   "xs23_0mmgml56z346w1": ("?-worm_and_cap_and_block", 20),
                   "xs23_5b8b96zw651156": ("00d80054008400780000001e00210033", 20),
                   "xs23_4a9egmicz03543": ("003000480068000e0071009500560020", 20),
                   "xs23_c8allmz3303421": ("006c0068000a0075009500560020", 20),
                   "xs23_0c88b96z69f033": ("?-worm_and_cap_and_block", 20),
                   "xs23_g88b96z1255dic": ("0180024601a900ab00a800480030", 20),
                   "xs23_0ca52z69d1dik8": ("01000280024001a2002501aa012c00c0", 20),
                   "xs23_03lkkl3z69ic01": ("cis-mango_with_long_leg_and_cis-dock", 20),
                   "xs23_0ca9ege2z69d11": ("00c0012c01aa0029002e0010000e0002", 20),
                   "xs23_032q48gz31ehld": ("0060002301c2023a02a401a80010", 20),
                   "xs23_4a9egm96z03543": ("006000900068000e0071009500560020", 20),
                   "xs23_2llm88gz1qq221": ("011002ab02ab01a8004800500020", 20),
                   "xs23_39u0u1jz643w11": ("?-long_hook_siamese_hook_and_dock", 20),
                   "xs23_0ca2s0f9z69d11": ("012001e000000078008800ab00690006", 20),
                   "xs23_2lm88gz122dll8": ("011002a801a80056005500350002", 20),
                   "xs23_0c88bbgz6511dd": ("00c000ac0028002801ab01ab0010", 20),
                   "xs23_031egmicz65156": ("00d800880070000e0011001500560060", 20),
                   "xs23_4a960u1t6zx6221": ("racetrack_with_?-tail_and_?-loaf", 20),
                   "xs23_wca9e0eik8z6413": ("?-loaf_siamese_table_and_R-loaf_and_carrier", 20),
                   "xs23_g8ehlmz11x23ck8": ("0100028001800060005600150011000e00280030", 20),
                   "xs23_0cc0si52z697074": ("?-tub_with_leg_siamese_table_and_R-bee_and_block", 20),
                   "xs23_0ok4o796z4aa611": ("00c0012001c800380046005500350002", 20),
                   "xs23_4a9eg8k8z0178b6": ("004000a8012e00e1001d002600500020", 20),
                   "xs23_ca1u08kcz330346": ("006c006a0001007e008000c80014000c", 20),
                   "xs23_4ako0u1ra96zy21": ("02c005a2042503aa00ac0040", 20),
                   "xs23_0mm0e952z643033": ("?-R-loaf_and_hook_and_blocks", 20),
                   "xs23_o8bbgzx12hu0652": ("?-tub_with_long_legs_and_boat_and_block", 20),
                   "xs23_69ac0ciiczx3543": ("00800146012900e90006003400240018", 20),
                   "xs23_356o8gzy023ciar": ("0360014002400180007000480018000600050003", 20),
                   "xs23_69b88cicz0c8711": ("?-worm_siamese_beehive_with_tail_siamese_eater", 20),
                   "xs23_xo4iu069a4z3543": ("060009000d000160012600a9006a0004", 20),
                   "xs23_69ac0sik8zw6952": ("00c0012000a60069000a0074009000500020", 20),
                   "xs23_mligogkcz104aa4": ("?-hook_siamese_Z_and_beehive_and_boat", 20),
                   "xs23_25ao4kozc827066": ("[[?23?021]]", 20),
                   "xs23_0oo0e952zoie033": ("?23?020", 20),
                   "xs23_32qkggmiczw6246": ("010001c600250041007e000000680058", 20),
                   "xs23_0mligoz346w2596": ("00c0012000a000580010001200d500960060", 20),
                   "xs23_0mk453z34706952": ("0060009600f4000400c5012300a00040", 20),
                   "xs23_62s0s26gu156zx1": ("060009630d55011401940008", 20),
                   "xs23_025ac0s4z6511dd": ("00c000a20025002a01ac01a0001c0004", 20),
                   "xs23_0oo1v0kcz4aa611": ("00800158015800c1003f00200014000c", 20),
                   "xs23_4ako0u156zxc871": ("?-worm_siamese_eater_and_long_boat", 20),
                   "xs23_0gilmgmicz346w1": ("00c00140010800fe0001003500560020", 20),
                   "xs23_259a4ozy0ol5ako": ("033002900160008000600020002c001200090006", 20),
                   "xs23_xm2s079icz4a611": ("?-C_on_boat_and_?-R-mango", 20),
                   "xs23_64km88q552zx346": ("01800249018f0070004c000800280030", 20),
                   "xs23_69acz69l9h3zx11": ("031804a402aa01a500230030", 20),
                   "xs23_259a4ozw330f871": ("00c00120009000680008006b006a000a000c", 20),
                   "xs23_69b88ci6z0c8711": ("00c0012301a1002e00280068009000c0", 20),
                   "xs23_0ggml3z346069ic": ("01800240012300d5001600d000900060", 20),
                   "xs23_4a9eg6p96zx3421": ("00c4012a012900ce0050004800280010", 20),
                   "xs23_g88e13z12319lic": ("0180024002a30121002e006800480030", 20),
                   "xs23_0dr0rdz32101252": ("?-tub_with_leg_siamese_snake_and_hook_siamese_snake", 20),
                   "xs23_c871u4hf0cczy11": ("01980148056b064b00500020", 20),
                   "xs23_0gilmge96z346w1": ("?-worm_on_R-bee_and_boat", 20),
                   "xs23_mmggs2552z1w6a4": ("00d800d00010001600750082014001400080", 20),
                   "xs23_2lligz3kk643z011": ("0230054b054b025800480030", 20),
                   "xs23_6960u1u062sgzy11": ("?-eater_and_beehive_and_very_long_beehive", 20),
                   "xs23_256o8g0si96zx643": ("020205050486029801a8002000280018", 20),
                   "xs23_651u0o4k8zw178c1": ("?-worm_siamese_eater_and_loaf", 20),
                   "xs23_4aicw8o652zx11dd": ("02000506030900ca00840078000000600060", 20),
                   "xs23_31egogka52zw4aa4": ("?-barge_with_leg_siamese_integral_and_beehive", 20),
                   "xs23_354kl3z8kkl21zx1": ("06200550016b010a050a0604", 20),
                   "xs23_2lligz344lk3zx11": ("023005480548026b004b0030", 20),
                   "xs23_69iczg84pb96z011": ("03020485024901a6003400240018", 20),
                   "xs23_gg0s2dhu0ooz1221": ("03000480069b00ab00a800480030", 20),
                   "xs23_4a60u1u06996zy11": ("very_long_bee_and_pond_and_boat", 20),
                   "xs23_69q4ozwhaq552zx1": ("0300048002e2011500d6002800280010", 20),
                   "xs23_3560u19u0oozy111": ("?-mirror_and_ship_and_block", 20),
                   "xs23_0ggca970si6z3421": ("?-loaf_siamese_cis-legs_on_loaf_and_?-hook", 20),
                   "xs23_259a4o0oka6zx643": ("mango_with_long_nine_and_?-long_ship", 20),
                   "xs23_4aabgz255lk3zx11": ("011002a802a806ab004b0030", 20),
                   "xs23_2lligz344mk3zx11": ("023005480548025b004b0030", 20),
                   "xs23_2lligz3km443z011": ("0230054b055b024800480030", 20),
                   "xs23_2lligz346kk3zx11": ("023005480558024b004b0030", 20),
                   "xs23_gwca53z1p5l96zw1": ("0600051802a401aa002900260060", 20),
                   "xs23_69a4z03ll56z0321": ("?-loaf_and_siamese_long_hooks_and_ship", 20),
                   "xs23_04a9m88gzciic321": ("?-loaf_at_R-loaf_on_pond", 20),
                   "xs23_3560u15u0oozy111": ("?-mirror_and_ship_and_block", 20),
                   "xs23_4aicggca952zx1243": ("?-trans-loaf_at_loaf_on_R-mango", 20),
                   "xs23_25is0gg0siczx3443": ("020005020285008501b6009000900060", 20),
                   "xs23_256o8gzy018f0ciic": ("boat_on_boat_with_long_leg_and_trans-pond", 20),
                   "xs23_31eowg8kiczx12543": ("0600050201050189009600a800480030", 20),
                   "xs23_6a4o0ehrzw11y0352": ("C_on_boat_and_?-boat_with_leg", 20),
                   "xs23_0ogilmzga60643z11": ("0600055800d0001200d500960060", 20),
                   "xs23_0354kl3zgbq221z01": ("?-dock_and_long_hook_and_boat", 20),
                   "xs23_178baa4zg8k453z01": ("anvil_and_?-tub_with_nine", 20),
                   "xs23_0g8o69e0eik8z1221": ("?-R-loaf_on_R-bee_and_cis-R-loaf", 20),
                   "xs23_gg0s29e0eik8z1221": ("060009000d060169012a00ac0040", 20),
                   "xs23_3pmggzxmkl2zw1221": ("?23?015", 20),
                   "xs23_cik8gwo8a52zx34521": ("?-loaf_at_cis-loaf_with_tail_siamese_tub_with_tail", 20),
                   "xs23_069mggkcz0o4aa4z11": ("beehive_with_long_nine_and_?-beehive_with_tail", 20),
                   "xs23_259aczx65156o8gzy51": ("boat_on_C_and_?-R-mango", 20),
                   "xs23_y2ggm96z0g8ka96z1221": ("trans-loaf_at_loaf_line_beehive", 20),
                   "xs24_c89n8brz33032": ("?24?002", 12),
                   "xs24_09v0v9z6430346": ("?24?008", 12),
                   "xs24_39u0u93z3210123": ("?24?001", 12),
                   "xs24_4aab96z255d96": ("?24?005", 15),
                   "xs24_31e8w8ozc8711dd": ("?-very_long_eater_siamese_eater_and_eater_and_block", 15),
                   "xs24_69b8bqicz653": ("?24?004", 16),
                   "xs24_178b9cz8e1d93": ("cis-mirrored_alef", 16),
                   "xs24_069b8b96z4a953": ("very_long_worm_and_trans-R-mango", 16),
                   "xs24_35a8c0c4ozw178711": ("0180014000a8002e0061000e006800480030", 16),
                   "xs24_8e1lmz330fgkc": ("01800280021601f50001006e0068", 17),
                   "xs24_69b88cz6511d96": ("long_worm_and_trans-worm", 17),
                   "xs24_69b88a6z69d113": ("long_worm_and_cis-worm", 17),
                   "xs24_cc0si96z330eio": ("?-R-mango_and_hook_and_blocks", 17),
                   "xs24_0259acz69d1d96": ("very_long_worm_and_cis-R-mango", 17),
                   "xs24_3lkkl3z3204a96": ("cis-loaf_with_long_nine_and_cis-dock", 17),
                   "xs24_69ak8gzx1qab4ko": ("0310027001800070004800280016000900050002", 17),
                   "xs24_35is0cczca43033": ("?-boat_with_leg_siamese_boat_with_leg_and_blocks", 17),
                   "xs24_c8970sia4z06953": ("?-R-loaf_on_R-loaf_and_cis-legs", 17),
                   "xs24_39u0ml3z3210123": ("?-hook_siamese_hook_and_ships", 17),
                   "xs24_69ligozo4ai26z011": ("cis-mirrored_cis-loaf_with_long_leg", 17),
                   "xs24_2ll68oz3egld": ("011802ae02a1019500560060", 18),
                   "xs24_69b8brz69d11": ("01b001a8002801ab012900c6", 18),
                   "xs24_69b8b96z65156": ("very_long_worm_and_C", 18),
                   "xs24_4a9fgbrz03543": ("00d800d0000e00f1009500560020", 18),
                   "xs24_gbb8b96z11d96": ("00c0012001a6002901ab01a80018", 18),
                   "xs24_3lkkl3z122qq1": ("?-dock_and_very_long_bee_and_block", 18),
                   "xs24_259e0uicz4a513": ("?-tub_with_leg_on_cap_and_R-loaf", 18),
                   "xs24_2lmgmicz346066": ("0062009500d6001000d600d2000c", 18),
                   "xs24_mm0u156z11079c": ("?-worm_siamese_hook_and_cis-blocks", 18),
                   "xs24_c897079a4z3596": ("cis-legs_and_?-R-loafs", 18),
                   "xs24_4a9b8b96zw6996": ("00c0012001a6002901a9012600a00040", 18),
                   "xs24_35a88a6zca51156": ("cis-mirrored_trans-boat_with_long_nine", 18),
                   "xs24_69b88ciiczw2553": ("?-worm_siamese_pond_on_R-bee", 18),
                   "xs24_g88ehjz1230fgkc": ("01800280021301f1000e006800480030", 18),
                   "xs24_0354kl3zo4kb421z01": ("loaf_at_loaf_and_cis-dock", 18),
                   "xs24_256o8gzx4a52acggzy5121": ("04000a0006000190012800d0002000280018000600050002", 18),
                   "xs24_3hu0uhe0e96": ("?-long_hook_and_long_R-bee_and_R-bee", 19),
                   "xs24_g8e1t6zdlld": ("01b002a802ae01a1001d0006", 19),
                   "xs24_0gilmzrq2qq1": ("?-very_long_R-bee_and_boat_and_blocks", 19),
                   "xs24_8o6ll2z2fgld": ("010002b602b50181007e0048", 19),
                   "xs24_2lmggz1qq2qr": ("036003500050035603550022", 19),
                   "xs24_69e0e97079ic": ("?-R-mango_and_siamese_hooks_and_R-bee", 19),
                   "xs24_03lk453zcnge3": ("paperclip_and_?-dock", 19),
                   "xs24_4aab9cz255d93": ("cis-mirrored_irons", 19),
                   "xs24_gbaabob96z123": ("00d2015e010000fe002100050006", 19),
                   "xs24_3lmgmmz346065": ("?-worm_siamese_snake_and_ship_and_block", 19),
                   "xs24_8e1u0uicz3543": ("006800ae0081007e0000001e0012000c", 19),
                   "xs24_69b88cz69d553": ("?24?009", 19),
                   "xs24_8ehmkkoz178a6": ("00300050005600d5011100ee0028", 19),
                   "xs24_ml1u0uicz1243": ("006c00aa0081007e0000007800480030", 19),
                   "xs24_178b96z8e1d96": ("cis-mirrored_G", 19),
                   "xs24_354kl3z69d543": ("paperclip_and_?-dock", 19),
                   "xs24_c88b96z311d553": ("006c0028002801ab012a00ca000c", 19),
                   "xs24_g8e1e8gz0dd1dd": ("003600360000003e00410036001400140008", 19),
                   "xs24_0ca9lmz69d5421": ("00c0012c01aa00a9009500560020", 19),
                   "xs24_0ojb88a6zciq23": ("018002580353004b00680008000a0006", 19),
                   "xs24_699egmicz04a96": ("00c00122012500e9001600d000900060", 19),
                   "xs24_69b8baaczw6513": ("006800ae0081007f0000001c00240030", 19),
                   "xs24_3pm0u156zw3453": ("00c600a9002b00480068002c00240018", 19),
                   "xs24_j1u069e0eicz11": ("?-dock_and_R-bees", 19),
                   "xs24_2lmgmmz3460643": ("very_long_worm_and_boat_and_block", 19),
                   "xs24_0mmggm93z1qaa4": ("0300024001a00024002a01aa01ab0010", 19),
                   "xs24_3lkkl3z32w69a4": ("018c0154005000500156018900050002", 19),
                   "xs24_0c88b96z69d553": ("R-racetrack_and_?-worm", 19),
                   "xs24_069b8b96zca513": ("very_long_worm_and_?-boat_with_leg", 19),
                   "xs24_4a9baa4z69d113": ("racetrack_II_and_?-worm", 19),
                   "xs24_69b88czw69d1156": ("long_worm_and_?-worm", 19),
                   "xs24_4a96z69d996zx33": ("023005480958064b004b0030", 19),
                   "xs24_69is0si6zw66074": ("?-long_and_R-mango_and_block", 19),
                   "xs24_354miozw3460796": ("01800140004c00d200960030000e00090006", 19),
                   "xs24_25a8a53z4a515ac": ("0183014500aa002800aa01450082", 19),
                   "xs24_8kihe0eicz06aa4": ("0060009000e0000000e20115009500560020", 19),
                   "xs24_04s0si96zc97066": ("?-long_and_R-mango_and_block", 19),
                   "xs24_0ogie0mp3zca246": ("?-cis-legs_and_shillelags", 19),
                   "xs24_c4gv1e8gzw6a871": ("00600040001601f5010100ee00280010", 19),
                   "xs24_ggmmge996z1w643": ("?-worm_on_R-pond_and_block", 19),
                   "xs24_69ac0siiczw2596": ("?-R-pond_on_loaf_and_R-loaf", 19),
                   "xs24_358e1u0oozw3543": ("0190012800a8006b000b006800480030", 19),
                   "xs24_69b8baicz035421": ("006800ae0081007d0002006400480030", 19),
                   "xs24_ciligozciai26zw1": ("018c025205550252005000d8", 19),
                   "xs24_354kljgzw32w69a4": ("trans-loaf_with_long_nine_and_shift-dock", 19),
                   "xs24_g8ge1egmmz11y2346": ("06000500010301c5002a01a801a80010", 19),
                   "xs24_178baa4zg0s453z11": ("anvil_and_?-elevener", 19),
                   "xs24_j1u0ok4oz11y13453": ("big_S_and_?-dock", 19),
                   "xs24_356o8gzg8k45loz11": ("trans-boat_with_long_nine_and_?-ship_on_ship", 19),
                   "xs24_0354kl3zgbai21z011": ("?-dock_and_long_hook_and_beehive", 19),
                   "xs24_y2o4a96zo4ie0ddz01": ("?-loaf_with_trans-tail_and_R-mango_and_block", 19),
                   "xs24_j1u0o48gz11x1169a4": ("?-trans-loaf_at_loaf_and_dock", 19),
                   "xs24_xg8hf0ck8z32qahzx1": ("?-tub_with_long_legs_and_boats", 19),
                   "xs24_69e0ehv0si6": ("03600156055506550062", 20),
                   "xs24_69960uhbqic": ("036005a6042903a900c6", 20),
                   "xs24_gbb8b96zd553": ("01b000ab00ab0068000b00090006", 20),
                   "xs24_c9baqb96z352": ("006c00a9004b000a001a000b00090006", 20),
                   "xs24_69b8brz0355d": ("01b001ab002a01aa012c00c0", 20),
                   "xs24_330fhe0ehla4": ("0d8c0d5201550152008c", 20),
                   "xs24_3lkkl3zrq221": ("?-dock_and_siamese_long_hooks_and_block", 20),
                   "xs24_g6llmzdlge21": ("01b002a6021501d500560020", 20),
                   "xs24_ca9lmz3587ko": ("0300029600f5010900aa006c", 20),
                   "xs24_3lkl3z12egnc": ("031002a800ae02a1031d0006", 20),
                   "xs24_2ll6o6hrzw343": ("00d800880060001e006100ae00a80040", 20),
                   "xs24_ca1u0uicz3543": ("006c00aa0081007e0000001e0012000c", 20),
                   "xs24_3lmgmicz34aa4": ("018c015200d5001500d200900060", 20),
                   "xs24_o4c0siarzc953": ("01b000a000900070000c006a00490033", 20),
                   "xs24_ml1u0uicz0343": ("006800ae0081007e0000007800480030", 20),
                   "xs24_gba9bob96z123": ("00da0156010000fe002100050006", 20),
                   "xs24_8u1lmz320fgkc": ("01800280021601f50001005e0068", 20),
                   "xs24_3lkkl3z32w6jo": ("?-cis-mirrored_docks_siamese_carrier", 20),
                   "xs24_wmlhe0eicz696": ("010002800280010000e2001500d500960060", 20),
                   "xs24_mm0u1eoz1245d": ("00d800d4000200fa010b00e00030", 20),
                   "xs24_3lkmicz122qic": ("031002a800a801ab012900c6", 20),
                   "xs24_x5bob96z178b6": ("00d80150010800f00020000b001a0012000c", 20),
                   "xs24_gwca9jzdlld11": ("03200250015000d6001500150036", 20),
                   "xs24_8e1daz359d1e8": ("010001c0002a01ad012100ae0068", 20),
                   "xs24_259e0ehe0e952": ("long_bee_and_R-loafs", 20),
                   "xs24_2lmgmmz1qq221": ("01b001a8002801ab02ab0110", 20),
                   "xs24_3lkaacz34a953": ("018c0152005500a900aa006c", 20),
                   "xs24_4aabaicz69l91": ("00c4012a02aa012b002a0012000c", 20),
                   "xs24_02llmz69e0e96": ("00c0012201d5001501d6012000c0", 20),
                   "xs24_651u0mp3z3543": ("00c600a9002b00480068000b00090006", 20),
                   "xs24_ca1u0mp3z3543": ("00c400aa0029004b0068000b00090006", 20),
                   "xs24_69b8brz253w123": ("006c00ac0080007c0004006500a30040", 20),
                   "xs24_69b8bb8ozw2596": ("00c0012001a4002a01a901a600200030", 20),
                   "xs24_8kit1eoz4aa611": ("00880154015200dd0021002e0018", 20),
                   "xs24_0mmgmp3z346066": ("00c0009b006b0008006b00690006", 20),
                   "xs24_0ggr1eoz12egld": ("006001d602150361002e00280010", 20),
                   "xs24_354kl3zw345d96": ("01800140004c0052015a018b00090006", 20),
                   "xs24_wmlhe0eik8z652": ("06000500020001c6002901aa012c00c0", 20),
                   "xs24_8o0u156z23cll8": ("01800282021501f5000600780048", 20),
                   "xs24_651ugmiczwcia4": ("01800280020601e9002a01a4012000c0", 20),
                   "xs24_2lmgmioz346w66": ("00d800d20016001000d600950062", 20),
                   "xs24_69b8bb8ozx35a4": ("[[?24?010]]", 20),
                   "xs24_69b88czw69d553": ("00c0012001a60029002b006a000a000c", 20),
                   "xs24_3hu0u156zw3453": ("00c600a9002b00280068002c00240018", 20),
                   "xs24_3lkmki6z32w643": ("00c600aa00280068002b00490066", 20),
                   "xs24_2llmggz122ege3": ("011002a802a801ae0021002e0018", 20),
                   "xs24_3lk453z320f871": ("018c01540050004f0141018e0008", 20),
                   "xs24_3lk453zhaarz11": ("?-dock_and_R-bee_and_hook", 20),
                   "xs24_3lkmkl3z122641": ("?-iron_and_siamese_hooks", 20),
                   "xs24_8kit1eoz06a871": ("003000e8010e0171009500560020", 20),
                   "xs24_mm0u93z11078a6": ("?-worm_siamese_hook_and_trans-blocks", 20),
                   "xs24_cimgehegozx343": ("003000480068000e0071008e007000080018", 20),
                   "xs24_caakl3z3303496": ("?-beehive_siamese_long_integral_on_R-mango_and_block", 20),
                   "xs24_4s0si96zd542ac": ("01a400bc0080005c015201890006", 20),
                   "xs24_69ic0ciczw8lld": ("?-mango_line_behive_and_R-bee", 20),
                   "xs24_o4ie0ehf0f9z01": ("?-R-mango_and_long_R-bee_and_table", 20),
                   "xs24_08e1lmz69f0343": ("00c0012801ee0001007500960060", 20),
                   "xs24_35a4o7piczx343": ("?-mango_siamese_bookend_siemese_beeheves_on_long_boat", 20),
                   "xs24_j1u06970796z11": ("?-dock_and_R-bees", 20),
                   "xs24_69b8oz65122qic": ("018c0254035000480068000b00090006", 20),
                   "xs24_4a9e0uicz0ca53": ("0060009000f0000c00ea012500a30040", 20),
                   "xs24_g88bb8oz19ll91": ("0060005003520355005500520030", 20),
                   "xs24_0ml1u0uh3z3421": ("018c01520056005000d6000900050002", 20),
                   "xs24_025iczoje0f952": ("0300026201c5001201ec012000a00040", 20),
                   "xs24_08e1e8gz69d1dd": ("00c0012801ae002101ae01a80010", 20),
                   "xs24_651u0uiczw178c": ("?-worm_siamese_eater_and_cap", 20),
                   "xs24_3lmggkcz34aik8": ("031802a401aa0029002500a200c0", 20),
                   "xs24_69baa4oz255d11": ("00c4012a01aa00ab00a800480030", 20),
                   "xs24_0g88b96z345dhr": ("0180025b03510056005400240018", 20),
                   "xs24_6996kkmz6953w1": ("00d80050005000cc012a012900c6", 20),
                   "xs24_39mge996zx3453": ("00c600a90029004e003000160012000c", 20),
                   "xs24_0ml1e8gz34a95d": ("006000960155012100ae01a80010", 20),
                   "xs24_3lk453z342bkk8": ("031802a400a8009a028503050002", 20),
                   "xs24_039u0mmz660743": ("?-hook_siamese_Z_siamese_eater_and_blocks", 20),
                   "xs24_699egmicz03543": ("0060009600950071000e006800480030", 20),
                   "xs24_69b88gz6519ll8": ("?-scorpio_siamese_very_long_eater_and_beehive", 20),
                   "xs24_g08e1t6z11dll8": ("018002e2021501d5005600100030", 20),
                   "xs24_6t1u0uiczw1074": ("006000b8008400780007007900480030", 20),
                   "xs24_0ca9liczc97074": ("?-R-mango_siamese_loaf_siamese_table_and_hook", 20),
                   "xs24_0ggca96z347ojd": ("?-shillelagh_on_cap_on_R-loaf", 20),
                   "xs24_699egmmz2553w1": ("006c006800080076009500950062", 20),
                   "xs24_g88ge952zdlgf2": ("01b002a8020801f0004e000900050002", 20),
                   "xs24_0mmgml96z32w66": ("0060009600b60040003e000100330030", 20),
                   "xs24_0mlhegm96z1243": ("008c015201560090006e0009000a0004", 20),
                   "xs24_ml1u066z11079c": ("00d80158010000fe000900c300c0", 20),
                   "xs24_cimggm952z4aa6": ("00c0012600a50041003e0000000e00090006", 20),
                   "xs24_0br0rb8oz65w32": ("?-table_siamese_table_and_long_snake_and_blocks", 20),
                   "xs24_3pmgmicz066066": ("shillelagh_siamese_worm_and_blocks", 20),
                   "xs24_069e0uiczca513": ("?-tub_with_leg_on_cap_and_?-R-bee", 20),
                   "xs24_069b88gzoid1dd": ("0300024601a9002b01a801a80010", 20),
                   "xs24_039q4ozcis3453": ("018002430389007a008400b80060", 20),
                   "xs24_3lkkl3z3462452": ("00c600a9002b002a00a900c50002", 20),
                   "xs24_ca1vg33z330346": ("00c000c3000900fe008000560036", 20),
                   "xs24_j1u0uh3z11w34a4": ("?-long_hook_siamese_tub_with_leg_and_cis-dock", 20),
                   "xs24_0jhu0uhjz32y123": ("0183010100ee0028002800aa00c6", 20),
                   "xs24_3pe0e996zw115a4": ("0180013000e8000800ea0125012200c0", 20),
                   "xs24_314u0e93z330346": ("00c600860020007e00010073009000c0", 20),
                   "xs24_0ca96z259f0cik8": ("0100028002400180000601e9012a00ac0040", 20),
                   "xs24_69b88ciiczx3543": ("00c00146010900f90006003400240018", 20),
                   "xs24_g04a96zdl913156": ("01b002a00124002a0069002600a000c0", 20),
                   "xs24_6ak81v079iczx11": ("01b002a304a5052a02240018", 20),
                   "xs24_ckgiljgzx660696": ("00c0012000d0001300d500d200100014000c", 20),
                   "xs24_0ggrhe0eik8z346": ("03000500040003c600a9002a00ac00c0", 20),
                   "xs24_0oe1lmz643034ac": ("01800140009600750001006e009800c0", 20),
                   "xs24_259e0ep3z065132": ("?-carrier_siamese_eaters_and_R-loaf", 20),
                   "xs24_354kl3zw320fgkc": ("03000280009800a802a0031e000100050006", 20),
                   "xs24_660u1u0oozw3543": ("006000600006007d0081007e000000180018", 20),
                   "xs24_39u0o4cz321079c": ("018c012400f80000003e00490063", 20),
                   "xs24_xo8hf0ca4z178b6": ("0180024002c0068000a000d6001500120030", 20),
                   "xs24_0mm0u1arz643w11": ("00d80054008400780000006e00690003", 20),
                   "xs24_354mge996zw3443": ("0186012900e9000e0030004800480030", 20),
                   "xs24_651u0mmz3303421": ("006c006a0001007e008000a60066", 20),
                   "xs24_0mm0u1t6zca1011": ("?-R-racetrack_and_long_snake_and_block", 20),
                   "xs24_x3pe0eik8z69521": ("?-loaf_with_trans-tail_siamese_hook_and_?-R-loaf", 20),
                   "xs24_62s0ca23qicz321": ("06000500010601650541063e0008", 20),
                   "xs24_69a4z69d996zx33": ("?-mirror_and_loaf_and_block", 20),
                   "xs24_69egmmzx1023cko": ("?-R-bee_on_hook_on_ship_and_block", 20),
                   "xs24_o4kmhf0ciicz011": ("030005c6042903a900a60060", 20),
                   "xs24_4a96z699d96z033": ("0230054b094b065800480030", 20),
                   "xs24_354c8a6zca23156": ("018301450044006c002800aa00c6", 20),
                   "xs24_0356o8zc97078a6": ("0180012300e5000600f80108014000c0", 20),
                   "xs24_4a96z699b96zx33": ("023005480948066b004b0030", 20),
                   "xs24_06a88b96z311d96": ("long_worm_and_?-worm", 20),
                   "xs24_69icwci96zx11dd": ("mango_long_line_mango_and_boat", 20),
                   "xs24_0o4a96z118f1d96": ("00c0012001a6002901ea010400380020", 20),
                   "xs24_0ca9b871z653033": ("00d800540042003e0000003600350003", 20),
                   "xs24_bq2s0ccz2303453": ("00d2005e0040003e000100350036", 20),
                   "xs24_g8ie0ehe0eicz11": ("?-boat_with_leg_and_long_bee_and_R-bee", 20),
                   "xs24_02llmggozc96066": ("0180012200d5001500d600d000100018", 20),
                   "xs24_0ca96z2llla4z32": ("?-tub_with_nine_siamese_long_bee_and_R-loaf", 20),
                   "xs24_178f1e8gzw39d11": ("010001c0002c01e9010b00e800280010", 20),
                   "xs24_0ci6o6p3zc97011": ("?-long_integral_siamese_bee_on_shillelagh_siamese_hook", 20),
                   "xs24_2lm0u1qczw34521": ("?-racetrack_II_with_bend_tail_and_boat", 20),
                   "xs24_oo0u93zw4706996": ("?-Z_siamese_eater_and_pond_and_block", 20),
                   "xs24_cimggka23qiczx1": ("010007c608250a41063e0008", 20),
                   "xs24_69b8b9icz035421": ("006c00aa0081007d0002006400480030", 20),
                   "xs24_09v0v9z32101256": ("?-boat_with_leg_siamese_table_and_long", 20),
                   "xs24_0gilmgmicz32w66": ("006000500012001500d600d000160012000c", 20),
                   "xs24_06t1u8z321078a6": ("00c00140010800fe0001003d00460060", 20),
                   "xs24_69bq2s0si96zy01": ("030205c5042903aa00ac0040", 20),
                   "xs24_69b88c2sgzx3553": ("00c00144010a00fa0003003c00240018", 20),
                   "xs24_0gs2t1eoz4aa611": ("?24?007", 20),
                   "xs24_69bq2s0cia4zx121": ("030005c6042903aa00a400a00040", 20),
                   "xs24_039u0uiz65210146": ("?-(boat_with_leg_siamese_hook)_and_(carrier_siamese_table)", 20),
                   "xs24_0g4c88b96zol3033": ("030002b00064000c00680068000b00090006", 20),
                   "xs24_39e0mmzy04706952": ("?-hook_and_loaf_and_table_and_block", 20),
                   "xs24_032qkggzciq22643": ("018002430342005a005400d000900060", 20),
                   "xs24_259mggmkk8zx6226": ("01800248014e0081007e000000780048", 20),
                   "xs24_04a9eg8gzcild221": ("0180024402aa01a9004e005000280010", 20),
                   "xs24_0ml1e8z32011dik8": ("01000280024001a8002e0021001500560060", 20),
                   "xs24_0ml1u0ok453z1221": ("060c04120396005000d600090006", 20),
                   "xs24_69960u2s0siczy21": ("?-pond_and_long_R-bee_and_R-bee", 20),
                   "xs24_069ak8gz3phe1221": ("[[?24?011]]", 20),
                   "xs24_259ac0siiczx2552": ("[[tear_on_beehive and R-mango]]", 20),
                   "xs24_gg2u0ehu0ooz1221": ("?-block_and_long_R-bee_and_worm", 20),
                   "xs24_o8wci96z0hhldz32": ("mango_with_long_nine_and_?-integral", 20),
                   "xs24_354c5j08ozx69d11": ("?-scorpio_siamese_carrier_siamese_dock", 20),
                   "xs24_g88e1t6z1p5p1zw1": ("030005c0042003a600a900a60060", 20),
                   "xs24_356o8gzy0pgf0cic": ("trans-boat_with_long_nine_on_ship_and_trans-beehive", 20),
                   "xs24_259e0o8zw330fge2": ("01000280025801d80000007e0041000e0008", 20),
                   "xs24_69b8ozwgbacz2543": ("0c0212051a0902d603500030", 20),
                   "xs24_025960gz6511dll8": ("?-very_very_long_eater_and_loaf_and_R-bee", 20),
                   "xs24_2lligzhaaq23z011": ("?-very_long_R-bee_and_R-bee_and_beehive", 20),
                   "xs24_8k4o1v0ra96zw1x1": ("02b005a0042603a900aa0044", 20),
                   "xs24_0mlhe8gz32w358go": ("?24?003", 20),
                   "xs24_xg84s0si96z4a9611": ("06000900050002c0012c00aa006900050002", 20),
                   "xs24_2596o8gzy01230ehr": ("?-loaf_on_siamese_hooks_and_C", 20),
                   "xs24_g8g0s2pm0e93z1221": ("0c400aa00290065200d500090006", 20),
                   "xs24_0j9mggzg5u0643z11": ("060004b303c9001600d000900060", 20),
                   "xs24_069acz0ml552z3421": ("?-R-loaf_and_long_R-bee_and_loaf", 20),
                   "xs24_0g8o0u1jz121x11d96": ("03000500040203c500aa002c002000a000c0", 20),
                   "xs24_0gg0g8ie0e93z343032": ("0c000ac0028006a00056001500350002", 20),
                   "xs24_y0oggm952z0ggca6z321": ("trans-loaf_with_long_leg_and_?-ship_on_ship", 20),
                   "xs25_8e1v0rrz3543": ("?25?003", 11),
                   "xs25_660u1uge2z3543": ("?25?001", 14),
                   "xs25_ml1u0ooz11078a6": ("00d80158010000fe000100350036", 15),
                   "xs25_ca1v0rrz3543": ("00d800d8000000fe008100550036", 17),
                   "xs25_db0v1u8z330321": ("?-very_very_long_bee_siamese_eaters_and_snake_and_block", 17),
                   "xs25_g39s0s4ozdll8w1": ("?-hook_siamese_carrier_and_R-bees", 17),
                   "xs25_259arhe0ehr": ("063605590142055c0630", 18),
                   "xs25_caabo7picz33": ("?-mango_siamese_bookend_on_eater_siamese_Z_and_block", 18),
                   "xs25_ca9lmz330fgkc": ("?-worm_on_mango_siamese_bookend_and_block", 18),
                   "xs25_3lkkl3z32w69ic": ("mango_with_long_nine_and_cis-dock", 18),
                   "xs25_cimge9jz06a871": ("squid", 18),
                   "xs25_3jgv1eoz346221": ("00c600c9000b00fa008200740018", 18),
                   "xs25_6a88bbgz6511dd": ("very_long_krake_and_blocks", 18),
                   "xs25_651u0ooz1787066": ("00d800d8000000fe010100e50026", 18),
                   "xs25_0okimge96z4aic01": ("0180024001c0003001a0012600a9006a0004", 18),
                   "xs25_wmlhe862sgz25421": ("03000480024001c3003201aa012c00c0", 18),
                   "xs25_69aczra95d96": ("03660149012a00ac01a0012000c0", 19),
                   "xs25_6t1e8zwdd1d96": ("00c00170010b00eb0028000b00090006", 19),
                   "xs25_0ml1e8gz12ehld": ("0020005601d5022102ae01a80010", 19),
                   "xs25_39e0e93z69d113": ("worm_and_?-hooks", 19),
                   "xs25_69f0ccz6511d96": ("?-long_worm_and_cap_and_block", 19),
                   "xs25_3lmgmmz3460643": ("very_long_worm_and_ship_and_block", 19),
                   "xs25_3lkkl3z3460696": ("[[?25?007]]", 19),
                   "xs25_cc0v1qb96z0643": ("00d80168010b00eb00280008000a0006", 19),
                   "xs25_2llm88gz12egld": ("011002a802ae01a1005500560020", 19),
                   "xs25_0o4p7ob96z3543": ("00d80150011400ea002a000b00090006", 19),
                   "xs25_33gv1e8gzw6a871": ("01800180001601f5010100ee00280010", 19),
                   "xs25_6996z699d96zx33": ("?-mirror_and_pond_and_block", 19),
                   "xs25_651u0u2sgzw3543": ("00c0012c01aa002a002b006800480030", 19),
                   "xs25_0ok2u0696zca2453": ("018001580054008200be0060000600090006", 19),
                   "xs25_0259acz25t1t52zx1": ("004000ac03aa042903a500a20040", 19),
                   "xs25_2llmzrq2qr": ("03620355005503560360", 20),
                   "xs25_3lkkl3z346": ("[[beehive with ? tail on dock]]", 20),
                   "xs25_356o8zrq22qr": ("036303450046005803480360", 20),
                   "xs25_259e0ehu0uh3": ("?-long_hook_and_long_R-bee_and_R-loaf", 20),
                   "xs25_0gjl46zrq2qr": ("?-siamese_long_R-bees_and_hook_and_blocks", 20),
                   "xs25_md1e8zdd1d96": ("01b601ad002101ae012800c0", 20),
                   "xs25_3iabaarzw11dd": ("01b000ab00ab01a800a800900180", 20),
                   "xs25_0gbb8brz6b871": ("01b001a0002801ae01a1001d0006", 20),
                   "xs25_69b88cz69d1db": ("?-worm_siamese_snake_and_worm", 20),
                   "xs25_2llmggozrq226": ("?-R-bee_and_very_very_long_eater_siamese_Z_and_block", 20),
                   "xs25_ciq3ob96z4aa6": ("00c0012001a00030018600b500950062", 20),
                   "xs25_mllmgmicz1w66": ("006c00a800a8006b000b006800480030", 20),
                   "xs25_w6s1raarz3543": ("013001e4000c01e80128000b00090006", 20),
                   "xs25_g88b9iczdd1dd": ("01b001a8002801ab01a90012000c", 20),
                   "xs25_3lkkl3z12ege3": ("031802ae00a100ae02a80310", 20),
                   "xs25_ca9n8brz33032": ("?-cis-legs_at_cis_legs_siamese_loaf_and_blocks", 20),
                   "xs25_cc0s2arz66079c": ("01b000a30089007e000000660066", 20),
                   "xs25_xmlhe0e96z4a96": ("030004800280010000e0001600d500950062", 20),
                   "xs25_0ad1e8gz69d1dd": ("00c0012a01ad002101ae01a80010", 20),
                   "xs25_ml1u0mmz110743": ("006c00ac0080007f0001006e0068", 20),
                   "xs25_354c5jz259d543": ("0184014a0049006b014a0192000c", 20),
                   "xs25_0j5c5jz345d543": ("0060009300a501ac00a500930060", 20),
                   "xs25_3lmgml3z346221": ("R-racetrack_and_ships", 20),
                   "xs25_69b88cz6970796": ("worm_and_R-bees", 20),
                   "xs25_354c5jz255d543": ("0184014a004a006b014a0192000c", 20),
                   "xs25_39c0ccz69d1d96": ("01860129006b0008006b00690006", 20),
                   "xs25_caab8ria4z0696": ("006000a600a901a6002001b0009000a00040", 20),
                   "xs25_4a9f0rbz651321": ("?-hook_siamese_eater_and_loaf_siamese_table_and_block", 20),
                   "xs25_wml1uge13zca43": ("031802a400ac00a0006c0008000a00050003", 20),
                   "xs25_ca1t6z358f0352": ("006c00aa010101fd0006006000a00040", 20),
                   "xs25_4aab88gz69d1dd": ("00c4012a01aa002b01a801a80010", 20),
                   "xs25_3lmgmicz346066": ("00c600a9006b0008006b004b0030", 20),
                   "xs25_oo1v0v1oozx343": ("?-very_very_very_long_hat_and_blocks", 20),
                   "xs25_ckgv1eoz06a871": ("00600056001501f1010e00e80030", 20),
                   "xs25_09f0ccz69d1d96": ("00c0012c01ac002001af012900c0", 20),
                   "xs25_wmmge1egmaz643": ("06000500010001c6002901aa01ab0010", 20),
                   "xs25_0c88bbgz69d1dd": ("00c0012c01a8002801ab01ab0010", 20),
                   "xs25_wmlhe0e952z696": ("031804a402ac01a0001c0002000500050002", 20),
                   "xs25_69ab8b96zw6996": ("00c0012001a6002901a900a6012000c0", 20),
                   "xs25_069n8brz4aa611": ("01b001a8002801d6012500c50002", 20),
                   "xs25_0mlhe0ehla4z32": ("06000400038c005203550252018c", 20),
                   "xs25_mmgu1dmz122611": ("006c006a000a007b008400b40068", 20),
                   "xs25_0iu0uhf0ccz643": ("03000280008001b000ab00ab01a80018", 20),
                   "xs25_ca1v0brz330321": ("006c006a0009006b0048002b001b", 20),
                   "xs25_0g39u0696z8lld": ("018002400180000001e00256031500350002", 20),
                   "xs25_mmgehlmz1x3443": ("006c006800080070008e00a900690006", 20),
                   "xs25_g8e1e8gzdd11dd": ("01b001a8002e002101ae01a80010", 20),
                   "xs25_0g8e1eozgt3on1": ("020003b00068030e02e1002e0018", 20),
                   "xs25_69b8bb8ozw6996": ("?25?005", 20),
                   "xs25_mlhegmmz1x3443": ("?25?006", 20),
                   "xs25_09v0c970si6z321": ("?-rotated_hook_and_long", 20),
                   "xs25_69ac0siiczw6996": ("?-pond_on_R-pond_and_R-loaf", 20),
                   "xs25_ml1u0696z122156": ("?-very_long_worm_siamese_long_integral_and_beehive", 20),
                   "xs25_69e0eikozwca2ac": ("00c0012000e3000500e4009500530030", 20),
                   "xs25_xj1u0ok8z69d543": ("018002e0021001d000560015001200500060", 20),
                   "xs25_3lk688b96zw3453": ("0186012500e1001e00c0005800480030", 20),
                   "xs25_69mk2u0oozw6943": ("00c0012000d60059008200fc000000300030", 20),
                   "xs25_69egmmzx122bkk8": ("?-R-bee_on_siamese_hooks_on_beehive_and_block", 20),
                   "xs25_xj1u06996z69d11": ("031804a804a003200028001e000100050006", 20),
                   "xs25_0mkkm453z34aa43": ("01800140004c00d20055005500d2000c", 20),
                   "xs25_mkiabaik8z1w343": ("006c00280048005600d10056004800280010", 20),
                   "xs25_6t1u0ooz11078a6": ("00d80158010000fe0001003d0026", 20),
                   "xs25_0g88ci96zol55lo": ("?-long_R-bee_siamese_mango_and_?-dock", 20),
                   "xs25_08e1qczc97078a6": ("0180012800ee000100fa010c014000c0", 20),
                   "xs25_69ab8b96zw65113": ("006a00ad0081007e000000780044000c", 20),
                   "xs25_08e1u8zc97078a6": ("0180012800ee000100fe0108014000c0", 20),
                   "xs25_0mmgm453z1qq221": ("03000280009001a8002801ab01ab0010", 20),
                   "xs25_9v0s2acz2303453": ("?-very_long_worm_and_siamese_tables", 20),
                   "xs25_4aab88b96zx3596": ("00c8014e010100fe00000038004800500020", 20),
                   "xs25_g88bbgz1230fgnc": ("018002e0021001eb000b006800480030", 20),
                   "xs25_g8o0u1t6z1qq221": ("018002e0021001e80008006b004b0030", 20),
                   "xs25_9f0s2acz3303453": ("?-very_long_worm_and_table_and_block", 20),
                   "xs25_ca1v0ccz3303453": ("?25?002", 20),
                   "xs25_xokie0e96zca2ac": ("?-C_and_cis-legs_siamese_loaf_and_R-bee", 20),
                   "xs25_651u0mkiczw3543": ("00c0012a01ad0021002e006800480030", 20),
                   "xs25_mlhe88a6z102596": ("?-G_siamese_long_hook_on_loaf", 20),
                   "xs25_0ca9dikoz651156": ("?-R-loaf_siamese_mango_on_dock", 20),
                   "xs25_660u1lmz1787011": ("00d80158010000fe000100ce00c8", 20),
                   "xs25_35a88bbgzw311dd": ("0180014000ac0028002801ab01ab0010", 20),
                   "xs25_6996z69d996z033": ("?-mirror_and_pond_and_block", 20),
                   "xs25_ck8ge1eozw6b871": ("006000500026001d00e1010e00e80030", 20),
                   "xs25_03hu0o4czckgf023": ("01800283021101fe000000580064000c", 20),
                   "xs25_4s0ci9bob96zw121": ("03600550040b03ea009200140008", 20),
                   "xs25_354kl3zra221z056": ("?-dock_and_long_hook_and_long_snake", 20),
                   "xs25_0cimge996z8ka221": ("01800240024001d0002801a8012a00c50002", 20),
                   "xs25_cikm4hf0cik8zx11": ("0180074608290baa05240060", 20),
                   "xs25_0gill2z12iu078k8": ("01000280010000e2001503d5025200500020", 20),
                   "xs25_69ege2s0si6zx121": ("0200056305550354009600a00040", 20),
                   "xs25_039e0ooz31132qic": ("0180025803580040006e002900230060", 20),
                   "xs25_wca2s0si96z4ad11": ("03000500020001c0002c01aa012900c50002", 20),
                   "xs25_6icg7p2sgz012543": ("0060004c0032000d00e1009e004000380008", 20),
                   "xs25_69b8b96zx3116426": ("02c0034800380000003e004100550036", 20),
                   "xs25_4a970s2ibqiczy21": ("0308053e0941064d00560020", 20),
                   "xs25_8o0u1raicz012543": ("003000e80108016b00aa002a00240018", 20),
                   "xs25_2ego0u156zw6a871": ("00c00140010800fe00010035001600e00080", 20),
                   "xs25_69ege2s0siczx121": ("?25?004", 20),
                   "xs25_ckggc2c8a53zx3453": ("06000520025301d1000e006800480030", 20),
                   "xs25_699e0o44ozw699611": ("00c00120012600e900090036004800480030", 20),
                   "xs25_35aczwj9d9a4zw123": ("0c000a0005660349005b004800280010", 20),
                   "xs25_o48q552z8llk46zx1": ("02000518050802cb00aa012a00c4", 20),
                   "xs25_o4ie0ehlmz01y2652": ("03000500020201c5002901aa012c00c0", 20),
                   "xs25_xok4mgm96z6952011": ("020005400570020801d80066000900050002", 20),
                   "xs25_w696z2lll552z1221": ("?-R-bee_and_very_very_long_bee_and_beehive", 20),
                   "xs25_0g8g08e13z2fgn853": ("0300020001d800540002003d0041003e0008", 20),
                   "xs25_g88e1eoz1230354ko": ("03000280009800ae0061000e006800480030", 20),
                   "xs25_0g8ka96z122dkk871": ("?-trans-loaf_at_loaf_on_R-bee_with_tail", 20),
                   "xs25_g8ge996z1254312ko": ("03000280004600290069008e00b000480030", 20),
                   "xs25_0ggmlhe0eik8z3201": ("0c00090007c6002901aa012c00c0", 20),
                   "xs25_g88g0ggm952z122rk3": ("030004800280010600e90029002e001000080018", 20),
                   "xs25_06996z0gbhd96z1221": ("04000a060969062901a6012000c0", 20),
                   "xs25_069b88czg8jd453z01": ("02000506026901ab008800a8006c", 20),
                   "xs25_gwg8g2u0696zdd11011": ("0c000c0000000f6009500092001500350002", 20),
                   "xs26_69b88a6z69d1156": ("?26?007", 13),
                   "xs26_c88baacz311d553": ("?26?005", 14),
                   "xs26_g88ml1eoz178a611": ("?26?001", 15),
                   "xs26_259mkk8zg84qaa4z011": ("cis-mirrored_loaf_siamese_long_beehive", 15),
                   "xs26_69baacz69d553": ("cis-mirrored_R-racetrack", 17),
                   "xs26_g84q55q4oz01169521": ("?26?009", 17),
                   "xs26_69ab9cz695d93": ("?26?002", 18),
                   "xs26_03lkkl3zcnge21": ("030002b000a800ae02a1031d0006", 18),
                   "xs26_3lkkl3z34606jo": ("031802a400ac00a002ac03190003", 18),
                   "xs26_35is0si53zw65056": ("cis-mirrored_?-boat_with_leg_siamese_snake", 18),
                   "xs26_0ggo0u156z122egld": ("01800280021601f50001006e002800280010", 18),
                   "xs26_69e0u1u0e96zy0121": ("?-very_very_long_bee_and_R-bees", 18),
                   "xs26_660uhe0ehu066": ("031802a81aab1aab0110", 19),
                   "xs26_g88e1t6zdd1dd": ("01b001a8002801ae01a1001d0006", 19),
                   "xs26_5b8b96zad1d96": ("014501ab002801ab012900c6", 19),
                   "xs26_69b88cz69d1d96": ("very_long_worm_and_cis-worm", 19),
                   "xs26_69baiczw69aqic": ("01800240034c0152012a00cb00090006", 19),
                   "xs26_c88b96z358e1db": ("016001a6002901cb010800a8006c", 19),
                   "xs26_c8allicz315aa6": ("006c002800aa0155015500d2000c", 19),
                   "xs26_6a88b9cz6511d93": ("?26-mirrored_huge", 19),
                   "xs26_069b8b96z311d96": ("00c0012001a6002901ab012800c8000c", 19),
                   "xs26_xca9bqicz651156": ("0330021001e00006007d0041002e0018", 19),
                   "xs26_ciljgozciai26zw11": ("018c025205550653005000d8", 19),
                   "xs26_o4ie0ehlmz01y2696": ("020005000500020201c5002901aa012c00c0", 19),
                   "xs26_rhe0o4o0ehrzy0121": ("long_bee_and_Cs", 19),
                   "xs26_33gv1c88gzw6a8711": ("01b001a00028002e0061000e006800480030", 19),
                   "xs26_g88m5he8gz0116a871": ("00300048005800c6012900c6005800480030", 19),
                   "xs26_j1u06960u1jz11y311": ("?-docks_and_beehive", 19),
                   "xs26_651u0o8gzw110122dik8": ("R-loaf_at_loaf_and_?-worm", 19),
                   "xs26_259e0ehv0rr": ("?-siamese_long_R-bees_and_R-loaf_and_blocks", 20),
                   "xs26_caariicz31eic": ("00d80150014e03690126012000c0", 20),
                   "xs26_ca9lmzdj87074": ("01ac026a010900f5001600e00080", 20),
                   "xs26_69b8bqicz6996": ("00c6012901a9002601a000b000900060", 20),
                   "xs26_3lkkl3z32qq23": ("?-dock_and_siamese_very_long_R-bees_and_block", 20),
                   "xs26_mkiarhe0eicz1": ("?-bookends_siamese_C_and_R-bee", 20),
                   "xs26_c88b96z355d553": ("?-very_long_R-bee_siamese_eater_and_?-worm", 20),
                   "xs26_08o6ll2zoif0dd": ("0300024801f8000601b501b50002", 20),
                   "xs26_08e1v0rrz65123": ("00d800d8000000fe0082007400150003", 20),
                   "xs26_ca1t6z358f0356": ("00c000a00060000601fd010100aa006c", 20),
                   "xs26_2llmggzrq22643": ("036203550055005600d000900060", 20),
                   "xs26_39u0e9jz06b871": ("0190012800ee000100fd01260180", 20),
                   "xs26_69bqa4zx4abqic": ("?26?008", 20),
                   "xs26_0jj0v1ooz347074": ("006c00a800a8006b000b00080068006c", 20),
                   "xs26_660u1lmz330f811": ("00d80158010100ff000000cc00cc", 20),
                   "xs26_3lkmkkmz3460641": ("00c600a9002b0068002b0029006c", 20),
                   "xs26_39u0u93z6430346": ("00c30091007e0000007e009100c3", 20),
                   "xs26_3lkkljgz346w643": ("00cc008400780000007e008100a50066", 20),
                   "xs26_gilmgmicz1w6aa6": ("0060009600d5001500d6015000900018", 20),
                   "xs26_2ll2sgz6430fgkc": ("01800280021001fc00020075009500c2", 20),
                   "xs26_03hu0ep3z6aa611": ("0180013000e8000800f6011501850006", 20),
                   "xs26_mm0u93z12470696": ("00d800d4000200fe0120018600090006", 20),
                   "xs26_69ngbb88czx3453": ("00d801580141009f0060002c00240018", 20),
                   "xs26_gbb8brz1p5p1zw1": ("06c006a000a606a906a60060", 20),
                   "xs26_0g88ml96zol5aa6": ("030002b000a80148015600d500090006", 20),
                   "xs26_08e1e8z69lld113": ("00c0012802ae02a101ae002800200060", 20),
                   "xs26_ciegehm4kozx343": ("003000480070000e0071008e0068002000280018", 20),
                   "xs26_6960u1mkiarzy111": ("0422075500d5061205d00060", 20),
                   "xs26_69b8b96z033w3156": ("0180012600e60000003e004100550036", 20),
                   "xs26_660u1fo3qiczy011": ("00b003ab042b056803480030", 20),
                   "xs26_xcc0s2596z6511dd": ("03000480055802580040003e000100330030", 20),
                   "xs26_6t1ege132qk8zw11": ("0630095c0d42054504860300", 20),
                   "xs26_069b88a6z359d113": ("00c000ac0028002801ab012900ca000c", 20),
                   "xs26_69b88c0siczx3553": ("01800282021501f50006007800480030", 20),
                   "xs26_259ar0v1u0oozy31": ("06b009a8042803ab00ab0010", 20),
                   "xs26_651u0o4kozwdb074": ("00c00140010b00fd0000003e004200500030", 20),
                   "xs26_xokkl3zmlhe221z1": ("?-G_siamese_R-hat_siamese_integral", 20),
                   "xs26_35is0s4zwckgf033": ("03000280012600e5000100fe008000180018", 20),
                   "xs26_25ac0c4oz069d1dd": ("0080014600a9006b0008006b004b0030", 20),
                   "xs26_0mm0u1uge13z1221": ("062005560156015000d600090006", 20),
                   "xs26_ok2s0sid1e8z0343": ("racetrack_II_and_?-R-bee_with_bend_tail", 20),
                   "xs26_69b8b9czx3113156": ("0300024801f80000007e004100150036", 20),
                   "xs26_0g88mkl3z8lld221": ("?-R-bee_siamese_R-bee_on_R-bee_on_hook", 20),
                   "xs26_259a4oz0gjll8z346": ("0c0212051a6902aa02a40118", 20),
                   "xs26_0259mggkcz6953w66": ("00c0012200a500690016001000d000d4000c", 20),
                   "xs26_259a4oz355ldzx123": ("0c1809a406aa00a900a50062", 20),
                   "xs26_4a9eg8kk8z0178b43": ("004000a8012e00e1001d0022005c00500020", 20),
                   "xs26_354c84s0siczx3543": ("?-worm_siamese_snake_siamese_eater_and_R-bee", 20),
                   "xs26_o8g0s2ibpicz643w1": ("?26?003", 20),
                   "xs26_w69b88gzo4id1ddz01": ("03000480024601a9002b01a801a80010", 20),
                   "xs26_w3lkkl3zg89q221z11": ("?-dock_and_long_R-bee_and_hook", 20),
                   "xs26_0c88b96z2ll553z011": ("?-worm_and_very_long_R-bee_and_block", 20),
                   "xs26_0c88b96z0gilicz346": ("0c0012301a4802a8024b06090006", 20),
                   "xs26_03lk453zg89a96z123": ("0c000a30024802a80acb0c090006", 20),
                   "xs26_ckgo0ogka52zwca2ac": ("020005000283012900ee000000380044006c", 20),
                   "xs26_g39s0s48gz11d4ko11": ("?26?006", 20),
                   "xs26_03l2c88gzw1pl91z253": ("080014030c35032202ac012800280010", 20),
                   "xs26_069b88czg8ge1d96z01": ("02000506020901cb002801a8012c00c0", 20),
                   "xs26_0gg0g88m952z8llc321": ("?-loaf_at_R-loaf_on_R-bee_and_block", 20),
                   "xs26_g88gu1688gz11wojd11": ("003000500040002001e302190196005000500020", 20),
                   "xs27_651u0u156zw17871": ("?27?001", 15),
                   "xs27_0ggo4o796z122egld": ("[[?27?004]]", 16),
                   "xs27_mm0u1lmz1221078c": ("0180011600f50001003e004000560036", 18),
                   "xs27_651u0u156zw17853": ("00c6012901ab00280028006c004800280010", 18),
                   "xs27_cc0s2pmz3543w34a4": ("010002860149004b0068002b004b00500020", 18),
                   "xs27_651u0o4kozw178b43": ("racetrack_with_bend_tail_siamese_worm", 18),
                   "xs27_0gjl453zrq2qr": ("?-C-siamese_long_bee_and_C_and_blocks", 19),
                   "xs27_2llmzpie0fgkc": ("0322025501d5001601e0020002800180", 19),
                   "xs27_9f0s4oz330fgld": ("025803d8000000fe008100750016", 19),
                   "xs27_gbb88gzd59d5lo": ("?-hook_siamese_snake_and_very_long_cap_and_block", 19),
                   "xs27_cimg6p7ob96zx11": ("03600556045503a100ae0018", 19),
                   "xs27_0okie0u93zca26221": ("?-trans-legs_siamese_hooks_and_loaf_siamese_cis-legs", 19),
                   "xs27_oo0o4q96zx347069a4": ("?-loaf_siamese_very_long_R-bee_and_loaf_and_block", 19),
                   "xs27_g88bb8brzdd113": ("?-Z_siamese_very_very_very_long_hook_and_blocks", 20),
                   "xs27_caabaacz330fho": ("?-very_very_long_bee_siamese_eaters_and_long_hook_and_block", 20),
                   "xs27_g8e1lmzdlhf023": ("01b002a8022e01e1001500560060", 20),
                   "xs27_2llmggz1qq2qq1": ("?-very_very_long_bee_and_R-bee_and_blocks", 20),
                   "xs27_2lligoz1qq2qic": ("0180025803500052035503550022", 20),
                   "xs27_69b88a6z69d1db": ("00c6012901ab002801a8016a0006", 20),
                   "xs27_69b871z69d1d96": ("00c6012901ab002801cb01090006", 20),
                   "xs27_354q4oz69d1ehp": ("?27?002", 20),
                   "xs27_2llm88gz320fgld": ("?-very_long_worm_siamese_hook_on_R-bee", 20),
                   "xs27_2lligzhaq2qrz11": ("?-very_long_R-bee_and_beehive_and_ship_and_block", 20),
                   "xs27_6a88bb8brzw2553": ("?-very_very_very_very_long_eater_and_R-bee_and_blocks", 20),
                   "xs27_4a9baa4zciq32ac": ("0184024a0349006b004a014a0184", 20),
                   "xs27_0db0v1u8z6530321": ("00c000ad006b0000007f0041003e0008", 20),
                   "xs27_8e1dmggmiczx4aa6": ("00c0012601650341003e0000003800480030", 20),
                   "xs27_0rb0v1u8z6430321": ("00c000ac002a004a006b000a006a006c", 20),
                   "xs27_699e0e996zw65156": ("?-R-ponds_and_C", 20),
                   "xs27_3lkmzra8abgzx321": ("?-worm_and_C_and_hook", 20),
                   "xs27_651u0ooz65116aic": ("?-worm_siamese_eater_on_R-loaf_and_block", 20),
                   "xs27_o8gehjz4s3o743zw1": ("00c8008e00710386047806480030", 20),
                   "xs27_wgjl46zgba8arz123": ("?-worm_and_C_and_hook", 20),
                   "xs27_xca2sgc453z69d113": ("0c0008300748015800c0003e002100050006", 20),
                   "xs27_o4ie0ehlmz01y269a4": ("060009000500020201c5002901aa012c00c0", 20),
                   "xs27_35a8c0c8a53zx65156": ("?-boats_with_legs_and_C", 20),
                   "xs27_0gwo4qabqicz343032": ("?27?003", 20),
                   "xs27_69baa4o0o4ozx3543w1": ("030005c0042203d5001500d200900060", 20),
                   "xs27_69960u2g8k8zx259611": ("?-long_boat_on_loaf_siamese_Z_and_pond", 20),
                   "xs27_g88b96o8z123x123cko": ("?-big_S_on_hook_on_ship", 20),
                   "xs27_gjl44oz10qb0t52zx11": ("0060064005560135010100ee00280010", 20),
                   "xs27_gj1u08k4oz1221x12596": ("long_worm_and_trans-loaf_at_loaf", 20),
                   "xs27_y0mmge952zo4kb421z01": ("?-loaf_at_R-loaf_on_R-loaf_and_block", 20),
                   "xs28_0g8ka9m88gz122dia521": ("tetraloaf_I", 7),
                   "xs28_0caab96z321311d96": ("?28?001", 16),
                   "xs28_69baa4oz69d1dd": ("[[?28?003]]", 17),
                   "xs28_69b88c88b96zx33033": ("worm_siamese_worm_and_blocks", 17),
                   "xs28_xrhe0ehrz253y3352": ("?28?002", 18),
                   "xs28_w69e0u156z6511dd": ("01880254035400580040003e000100330030", 19),
                   "xs28_g88bbgz8llll8zx66": ("01101aab1aab02a802a80110", 19),
                   "xs28_4aab88a6z255d1156": ("00c600aa0028002801ab00aa00aa0044", 19),
                   "xs28_0ok46164koz4aaq2sg": ("antlers_and_?-anvil", 19),
                   "xs28_g8geheg8gz121ehe121": ("?-long_bees_on_beehives", 19),
                   "xs28_0g8ka96z1iidia4z3421": ("tetraloaf_II", 19),
                   "xs28_330fhe0ehf0f9": ("?-table_and_long_R-bee_and_long_R-bee_and_block", 20),
                   "xs28_25akozraaq2qic": ("03620145014a03540058034002400180", 20),
                   "xs28_g88m9bqicz178b6": ("0060009000b001a0012600dd0021002e0018", 20),
                   "xs28_g88b96zdlge1d96": ("01b002a8020801cb002901a6012000c0", 20),
                   "xs28_69ac0f9z69530f9": ("?-tables_and_R-loafs", 20),
                   "xs28_69b88a6z69d1d96": ("00c6012a01a8002801ab012900c6", 20),
                   "xs28_69b8b96z651315a4": ("very_long_worm_and_?-tub_with_leg_siamese_hook", 20),
                   "xs28_oo1v0v1oozw47074": ("006c0028002801ab01ab00280028006c", 20),
                   "xs28_c88mll2z35960696": ("?-loaf_line_beehive_siamese_hat_on_R-bee", 20),
                   "xs28_g88mlligzdlhe2w1": ("01b002a8022801d60055001500120030", 20),
                   "xs28_0c9baab96zo8a513": ("0300010c014900ab002a006a000b00090006", 20),
                   "xs28_0ca9b8b96z69d113": ("00d80154010200fe0000003e002100050006", 20),
                   "xs28_09v0s2qrz321078c": ("01b000b30081007e000001f80124000c", 20),
                   "xs28_c84q952z35430ehr": ("0360022201c50009007a008400a8006c", 20),
                   "xs28_c89n8b96z3543033": ("006c00a8008900770008006b00690006", 20),
                   "xs28_0oo1v0si96zcia43": ("0180025801580081007f0000001c001200090006", 20),
                   "xs28_69b88c88gzw69d1dd": ("00d800d4000400f8010000fe002100050006", 20),
                   "xs28_0mlhe0ehlmz32y323": ("06030401038e005003560252018c", 20),
                   "xs28_69b88cz6t1d952z11": ("04c607a9002b01a8012800ac0040", 20),
                   "xs28_4a9m88m952zcia521": ("tetraloaf_III", 20),
                   "xs28_259acggzw3543032qr": ("06000600001807a404ac0060001c001200090006", 20),
                   "xs28_08e1lmzgbbo743z011": ("02000568056e030100f500960060", 20),
                   "xs28_g88ml3zdd0v0s4zx11": ("01b001a8000807f6041503830080", 20),
                   "xs28_ckgo1v0s4ozx6a8701": ("0060005000100036010501f1000e007000480030", 20),
                   "xs28_0mlhu0ooz1qa4zw1246": ("0300030000030f01112215540d580080", 20),
                   "xs28_0ggo8g0s2552z122egld": ("060009000680009800ae0061000e006800480030", 20),
                   "xs28_g88m9b88gz11078id221": ("00300050004001bc024203490056004800280010", 20),
                   "xs28_wg8kie0e952z4arzw123": ("060009600550034800340004000600010006000400140018", 20),
                   "xs28_256o8gzx643s2mzy3116a4": ("?-Cs_on_boats", 20),
                   "xs29_cc0s2ticz330fgkc": ("00d800d8000000fe010102e5012600c0", 16),
                   "xs29_03lk6o8zckgf0fio": ("?-long_on_hook_and_worm", 19),
                   "xs29_69e0u1u0e96zx23032": ("very_very_long_hat_and_?-R-bees", 19),
                   "xs29_6a88bb88gz6511dd11": ("very_very_very_long_krake_and_blocks", 19),
                   "xs29_0ca9baicz69d1dd": ("00c0012c01aa002901ab01aa0012000c", 20),
                   "xs29_gs2qbgn96z6aa43": ("?-siamese_R-bees_with_long_tail_and_trans-legs", 20),
                   "xs29_0mlhege93z1qq221": ("0300024001c0003001c8022802ab01ab0010", 20),
                   "xs29_xca4o0ehrz69d5521": ("06000510012805580640005e0021001d0006", 20),
                   "xs29_ggmkkmhe0e96z1w66": ("04400aa40abc0680007f000100180018", 20),
                   "xs29_0gs2llmz32012egnc": ("?29?001", 20),
                   "xs29_0g8e1t2sgz8k970743": ("01000290012800ee000100fd0082007c0010", 20),
                   "xs29_032aczmllll2z1w643": ("?-worm_and_very_long_R-bee_and_eater", 20),
                   "xs29_4a9baa4z2ll553z0121": ("?-racetrack_II_and_very_long_R-bee_and_boat", 20),
                   "xs29_2llmz010kn8brzw1221": ("04000ac00a8206950075000a0068006c", 20),
                   "xs29_0md1qcz12iabge2zw121": ("004006a00b26082905ea030400380020", 20),
                   "xs29_0259ac0cia4z69d11311": ("?-worm_siamese_loaf_with_tail_and_R-mango", 20),
                   "xs29_xcimgm93zg8gkaa4z1221": ("[[?29?002]]", 20),
                   "xs30_69b8b96z69d1d96": ("?30-great sym", 14),
                   "xs30_caabaacz355d553": ("cis-mirrored_very_very_long_bee_siamese_eaters", 16),
                   "xs30_69b8b9cz69d1d93": ("00c6012901ab002801ab0129006c", 17),
                   "xs30_69mgmiozo4q2qi6z01": ("cis-mirrored_?-beehive_with_very_long_leg_siamese_carrier", 18),
                   "xs30_4a9e0e96z25970796": ("00c6012900ee000000ee012900aa0044", 19),
                   "xs30_cid1u0u1diczx23032": ("018c0252055505550252005000d8", 19),
                   "xs30_3iabaarz0dd1dd": ("01b000ab00ab01a800ab009b0180", 20),
                   "xs30_69b8baarz0355d11": ("01b000a800a801ab002a01aa012c00c0", 20),
                   "xs30_651u0u156zw9f0f9": ("cis-mirrored_worm_siamese_table", 20),
                   "xs30_c8alla8cz315aa513": ("?-4_siamese_beehives_2_siamese_hats", 20),
                   "xs30_2llmgmicz346062ac": ("018c0152005600d0001600d500950062", 20),
                   "xs30_8e1t2c88gz330fgr11": ("0068006e000101fd0202036c002800280010", 20),
                   "xs30_69b8b96z69l9h3zx11": ("031804a406aa00a506a304b00300", 20),
                   "xs30_ca2s0si52sgzw230eio": ("?-tub_with_leg_and_tail_and_worm_and_hook", 20),
                   "xs30_69b88c0cczx330311d96": ("?30?001", 20),
                   "xs31_69b88bbgz69d11dd": ("?31?001", 14),
                   "xs31_0ca178b96z69d1d96": ("00d80154011200e60000003e004100550036", 19),
                   "xs31_0c9b8bq23z69d1dd": ("0180008000b001ab002b01a8012b00690006", 20),
                   "xs31_g88e1t6zdlll5ozx11": ("030005c6042903ab00aa00aa006c", 20),
                   "xs31_03hu0ooz4706iq2qic": ("01b002a0020b01fa0002006c00680008000a0006", 20),
                   "xs31_651ug6p3zwciq23033": ("018c0254035000480068000b007b008000a00060", 20),
                   "xs31_mm0u156z12kll2zw1243": ("0d800d40002c0faa10a914460c00", 20),
                   "xs32_4a9b8b96z259d1d96": ("00c6012901ab002801ab012900aa0044", 17),
                   "xs32_039u0u93z6a87078a6": ("cis-mirrored_worm_siamese_hook", 17),
                   "xs32_2llmzhaaarz8lld": ("?-long_R-bees_and_R-bees", 20),
                   "xs32_3pmgmiczg6q2qicz11": ("060304d90356005003560252018c", 20),
                   "xs32_wmmge1ege1ege2z643": ("6000500010001c4402aa1aaa1aab0110", 20),
                   "xs34_69b8baacz69d1d553": ("00c6012901ab002801ab00aa00aa006c", 20),
                   "xs34_03lkl3z0ju0ujz1226221": ("04000a630bd518140bd50a630400", 20),
                   "xs40_gj1u0u1jgzdlgf0fgld": ("?40?001", 19),
                   "xs40_69b88c88b96z69d11311d96": ("03060505042103fe000003fe042105050306", 20),
                   "yl12_1_8_c7310da81295b6611e6e4e34a80a5523": ("pufferfish", 75),
                   "yl144_1_16_afb5f3db909e60548f086e22ee3353ac": ("block-laying switch engine", 16),
                   "yl384_1_59_7aeb1999980c43b4945fb7fcdb023326": ("glider-producing switch engine", 17),
                   "xp10_9hr": ("[HighLife] p10", 6),
                   "xp7_13090c8": ("[HighLife] p7", 9),
                   "xq48_07z8ca7zy1e531": ("[HighLife] bomber", 9),
                   "xq8_2je4": ("[2x2] crawler", 0),
                   "yl8_1_1_aae0a4678d7caeb6b463f7c082d8bd1a": ("crawler wick", 20),
                   "yl4_1_1_38bc1dca7a1fb43eaade7bc292acedb5": ("crawler double wick", 50),
                   "xs8_33cc": ("block-tie", 0),
                   "xs12_33cc33": ("tri-block I", 3),
                   "xs12_ggcc33z11": ("tri-block II", 5),
                   "xs16_ccjjcczw11": ("quad-block", 8),
                   "xs16_ciddiczw11": ("16_big_honeycomb", 1),
                   "xs18_04ak8a53z6521": ("?-backwards-unix-boats-18", 3),
                   "xs9_256oo": ("block-tie-boat", 2),
                   "xs10_33cko": ("block-tie-ship", 0),
                   "xs11_g8kc33z01": ("block-tie-long-boat", 4),
                   "xs12_g8kc33z11": ("block-tie-long-ship", 5),
                   "xs10_3146oo": ("block-tie-carrier", 7),
                   "xs11_33c453": ("block-tie-eater I", 8),
                   "xs11_ggkc33z1": ("block-tie-eater II", 10),
                   "xs10_3123cc": ("block-tie-snake", 8),
                   "xs13_33cj96": ("t-eater", 10),
                   "xs14_o4o7poz01": ("t-eater", 10),
                   "xs14_3p6o66zw1": ("t-eater", 10),
                   "xs15_32134bjo": ("t-eater", 10),
                   "xs15_3pq4og4c": ("t-eater", 10),
                   "xs15_4ap6ooz32": ("t-eater", 10),
                   "xs15_8k4o7pozw1": ("t-eater", 10),
                   "xs15_gbbk46z121": ("t-eater", 10),
                   "xs15_i5p6ooz11": ("t-eater", 10),
                   "xs18_rr44rr": ("t-eater", 10),
                   "xs15_32qjc33": ("t-eater+.1", 12),
                   "xs16_8ehla4z33": ("t-eater+.1", 12),
                   "xs16_3js3pm": ("t-eater+.2", 12),
                   "xs17_3js3qic": ("t-eater++", 14),
                   "xq5_27": ("t", 0),
                   "xq4_1ba4": ("ant", 0),
                   "xq3_4aar": ("hat ship", 6),
                   "xq2_4ear": ("hat ship", 6),
                   "xq4_36bsk": ("double glider", 5),
                   "xq4_xkgp47z247": ("triple glider", 16),
                   "xq6_2ju0uj2": ("mirrored 2c/6", 14), 
                   "xq2_1fcgcf1": ("c/2 #1", 13),
                   "xq2_0ki313ikz12": ("c/2 #2", 26),
                   "xq2_2l4x4l2zw13231": ("c/2 #3", 26),
                   "xq2_1feice0ecief1": ("c/2 #4", 36),
                   "xq2_523a6m8zxl5dgz526233": ("c/2 #5", 42),
                   "xq4_v91e0e19v": ("symmetric 2c/4", 33),
                   "xq4_1b997zw8d99e": ("skew 2c/4", 39),
                   "xq5_227x4ee": ("double t", 13),
                   "xq5_72202a0ew8s": ("trans triple-t", 26),
                   "xq5_72202a0ew27": ("cis triple-t", 26),
                   "xq6_4rrwe465": ("2c/6 #1", 22),
                   "xq4_0g8e71f6cz707": ("c/4 #1", 30),
                   "xp4_69f": ("cap", 0),
                   "xp4_0diczpi62ac": ("cap variant I", 27),
                   "xp4_39c8a6z0f96zc93156": ("cap variant II", 34),
                   "xp4_9f0ciu": ("oscillating cap on table", 23),
                   "xp4_69f0ciu": ("oscillating cap on cap", 23),
                   "xp4_08o69fz321": ("cap on bookend", 22),
                   "xp4_g8o69fz121": ("cap on bun", 22),
                   "xp4_0ggca96z7w7": ("cap on R-loaf", 23),
                   "xp4_8g0si96zb43": ("cap on R-mango", 22),
                   "xp6_1e4278": ("[[tlife]] p6", 7),
                   "xp8_44hrrhrrh44": ("semi-octagon", 25),
                   "xp160_3v": ("p160", 0),
                   "xs8_rr": ("bi-block", 0),
                   "xs10_660696": ("block-on-beehive", 0),
                   "xs9_253033": ("block-on-boat", 0),
                   "xs12_6960696": ("beehive-on-beehive", 0),
                   "xs11_2596066": ("block-on-loaf", 0),
                   "xp2_rbzw23": ("block-on-beacon", 5),
                   "xs12_3560653": ("cis-ship-on-ship", 0),
                   "xs10_2530352": ("cis-boat-on-boat", 0),
                   "xs12_6606996": ("block-on-pond", 0),
                   "xs11_2560696": ("boat-on-beehive", 0),
                   "xs13_25960696": ("loaf-on-beehive", 0),
                   "xs14_259606952": ("cis-loaf-on-loaf", 0),
                   "xs10_330356": ("block-on-ship", 0),
                   "xs14_69606996": ("beehive-on-pond", 0),
                   "xs11_25ac0cc": ("block-on-long-boat", 0),
                   "xs10_25606a4": ("trans-boat-on-boat", 0),
                   "xs16_699606996": ("pond-on-pond", 0),
                   "xs13_25ac0cic": ("beehive-on-longboat", 0),
                   "xs12_3560696": ("beehive-on-ship", 0),
                   "xs11_33032ac": ("tail block-on-eater", 0),
                   "xp2_2530318c": ("cis-beacon-on-boat", 8),
                   "xs12_25606952": ("cis-boat-on-loaf", 1),
                   "xs12_256069a4": ("trans-boat-on-loaf", 1),
                   "xp2_rbzw23033": ("cis-block-on-beacon-on-block", 9),
                   "xs13_25606996": ("boat-on-pond", 2),
                   "xs16_rr0rr": ("tetra-block I", 2),
                   "xs16_rrzmmz11": ("tetra-block II", 2),
                   "xs15_259606996": ("loaf-on-pond", 3),
                   "xs12_3303pm": ("head block-on-shillelagh", 3),
                   "xs14_25ac0ca52": ("cis-longboat-on-longboat", 3),
                   "xs12_rrz66": ("[[pseudo]] tri-block", 3),
                   "xp2_318c0cic": ("beehive-on-beacon", 11),
                   "xs14_2596069a4": ("trans-loaf-on-loaf", 3),
                   "xs12_66069ic": ("block-on-mango", 3),
                   "xs11_2530356": ("cis-boat-on-ship", 3),
                   "xs12_33035ac": ("block-on-long-ship", 3),
                   "xs11_25606ac": ("trans-boat-on-ship", 3),
                   "xs1_1": ("dot", 0),
                   "xs2_3": ("domino", 0),
                   "xs2_12": ("duoplet", 0),
                   "xp2_12": ("duoplet", 0),
                   "xs4_55": ("bi-domino", 0),
                   "xs4_505": ("tetra-dot", 0),
                   "xs4_146": ("half-carrier", 0),}

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
        if (obj in self.alloccur):
            if (len(self.alloccur[obj]) < 10):
                self.alloccur[obj] += [soupid]
        else:
            self.alloccur[obj] = [soupid]
        
        if obj in self.commonnames:
            self.awardpoints(soupid, self.commonnames[obj][1])
        elif (obj[0] == 'x'):
            prefix = obj.split('_')[0]
            prenum = int(prefix[2:])
            if (obj[1] == 's'):
                self.awardpoints(soupid, min(prenum, 20)) # for still-lifes, award one point per constituent cell (max 20)
            elif (obj[1] == 'p'):
                if (prenum == 2):
                    self.awardpoints(soupid, 20) # p2 oscillators are limited to 20 points
                elif ((prenum == 3) | (prenum == 4)):
                    self.awardpoints(soupid, 30) # p3 and p4 oscillators are limited to 30 points
                elif (prenum == 160):
                    self.awardpoints(soupid, 9) # p160 oscillators are undoubtedly two interacting tlife p160s and are worth 9 points.
                elif (prenum == 320):
                    self.awardpoints(soupid, 13) # p320 oscillators are slightly more interesting
                else:
                    self.awardpoints(soupid, 40)
            else:
                self.awardpoints(soupid, 50)
        else:
            self.awardpoints(soupid, 60)

    # Assuming the pattern has stabilised, perform a census:
    def census(self, stepsize):

        g.setrule("APG_CoalesceObjects_" + self.rg.alphanumeric)
        g.setbase(2)
        g.setstep(stepsize)
        g.step()
        # apgsearch theoretically supports up to 2^14 rules, whereas the Guy
        # glider is only stable in 2^8 rules. Ensure that this is one of these
        # rules by doing some basic Boolean arithmetic.
        #
        # This should be parsed as 'gliders exist', not 'glider sexist':
        '''glidersexist = self.rg.ess[2] & self.rg.ess[3] & (not self.rg.ess[1]) & (not self.rg.ess[4])
        glidersexist = glidersexist & (not (self.rg.bee[4] | self.rg.bee[5]))'''
        #Never mind, a test at the beginning is more accurate.
        glidersexist = self.rg.g

        if (glidersexist):
            g.setrule("APG_IdentifyGliders")
            g.setbase(2)
            g.setstep(2)
            g.step()

        g.setrule("APG_ClassifyObjects_" + self.rg.alphanumeric)
        g.setbase(2)
        g.setstep(1)
        g.step()
        g.setrule("APG_PropagateClassification")
        g.setstep(stepsize)
        g.step()

        # Only do this if we have an infinite-growth pattern:
        if (stepsize > 8):
            g.setrule("APG_HandlePlumesCorrected")
            g.setbase(2)
            g.setstep(1)
            g.step()
            g.setrule("APG_ClassifyObjects_" + self.rg.alphanumeric)
            g.step()
            g.setrule("APG_PropagateClassification")
            g.setstep(stepsize)
            g.step()

        # Remove any gliders:
        if (glidersexist):
            g.setrule("APG_ExpungeGliders")
            g.run(1)
            pop5 = int(g.getpop())
            g.run(1)
            pop6 = int(g.getpop())
            self.incobject("xq4_153", (pop5 - pop6)/5)

        # Remove any blocks, blinkers and beehives:
        g.setrule("APG_ExpungeObjects")
        pop0 = int(g.getpop())
        g.run(1)
        pop1 = int(g.getpop())
        g.run(1)
        pop2 = int(g.getpop())
        g.run(1)
        pop3 = int(g.getpop())
        g.run(1)
        pop4 = int(g.getpop())

        # Blocks, blinkers and beehives removed by ExpungeObjects:
        self.incobject("xs1_1", (pop0-pop1))
        self.incobject("xs4_33", (pop1-pop2)/4)
        self.incobject("xp2_7", (pop2-pop3)/5)
        self.incobject("xs6_696", (pop3-pop4)/8)
        
        # Remove Ts, if they exist:
        if self.rg.t:
            g.setrule("APG_IdentifyTs")
            g.setbase(2)
            g.setstep(6)
            g.step()
            for i in xrange(5):
                g.setrule("APG_AdvanceTs")
                g.run(1)
                g.setrule("APG_AssistTs")
                g.run(5)
            g.setrule("APG_ExpungeTs")
            g.run(1)
            pop7 = int(g.getpop())
            g.run(1)
            pop8 = int(g.getpop())
            g.run(1)
            self.incobject("xq5_27", (pop7-pop8)/4)

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
#ALSO HANDLE 2xP160s HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # Check whether the cached object is in the set of decompositions
            # (this is usually the case, unless for example it is a high-period
            # albeit small spaceship):
            if objid in self.decompositions:            
                for comp in self.decompositions[objid]:
                    self.incobject(comp, 1)
                    self.awardpoints2(soupid, comp)
            else:
                self.incobject(objid, 1)
                self.awardpoints2(soupid, objid)
    
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

        if (self.naivestab(12, 30, 200)):
            return 4;

        if (self.naivestab(30, 30, 200)):
            return 5;

        # Phase II of stabilisation detection, which is much more rigorous
        # and based on oscar.py.

        # Should be sufficient:
        prect = [-2000, -2000, 4000, 4000]

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
                        
                    return max(1 + int(math.log(period, 2)),3)

            hashlist.insert(pos, h)
            genlist.insert(pos, int(g.getgen()))
#ALGO REFS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if self.rg.ruletype:
            g.setalgo("HashLife")
        else:
            g.setalgo("RuleLoader")
        g.setrule(self.rg.slashed)
        g.setbase(2)
        g.setstep(16)
        g.step()
        stepsize = 12
        if self.rg.ruletype:
            g.setalgo("QuickLife")
        else:
            g.setalgo("RuleLoader")
        g.setrule(self.rg.slashed)

        return 12

    # Differs from oscar.py in that it detects absolute cycles, not eventual cycles.
    def bijoscar(self, maxsteps, gracepd):
        '''g.setrule(self.rg.slashed)
        
        base = g.getbase()
        step = g.getstep()
        g.setbase(2)
        g.setstep(gracepd)
        g.step()
        g.setbase(base)
        g.setstep(step)'''
        pattern = g.getcells(g.getrect())
        
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
                g.setbase(2)
                g.setstep(3)
                g.step()
            elif self.pseudo:
                g.setrule("APG_CoalesceObjects_" + self.rg.alphanumeric)
                g.setbase(2)
                g.setstep(12)
                g.step()
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
#ALGO REF!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                g.new("Subcomponent")
                if self.rg.ruletype:
                    g.setalgo("QuickLife")
                else:
                    g.setalgo("RuleLoader")
                g.setrule(self.rg.slashed)
                g.putcells(livecells)
                period = self.bijoscar(1000, 4)
                canonised = canonise(abs(period))
                if (period < 0):
                    listofobjs.append("xq"+str(0-period)+"_"+canonised)
                elif (period == 1):
                    listofobjs.append("xs"+str(len(livecells)/2)+"_"+canonised)
                else:
                    listofobjs.append("xp"+str(period)+"_"+canonised)
#'''
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
#ALGO REF!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # For error-correction:
        if (intergen > 0):
            if self.rg.ruletype:
                g.setalgo("HashLife")
            else:
                g.setalgo("RuleLoader")
            g.setrule(self.rg.slashed)

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
#DEFINE RULE-BASED TEST FOR XWSS EXISTENCE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                if ((unidname[0] == 'U') & (unidname[1] == 'S') & (unidname[2] == 'S')):
                    
                    # Union of standard spaceships:
                    countlist = unidname.split('_')
                    
                    self.incobject("xq4_6frc", int(countlist[1]))
                    for i in xrange(int(countlist[1])):
                        self.awardpoints2(soupid, "xq4_6frc")

                    self.incobject("xq4_27dee6", int(countlist[2]))
                    for i in xrange(int(countlist[2])):
                        self.awardpoints2(soupid, "xq4_27dee6")
                        
                    self.incobject("xq4_27deee6", int(countlist[3]))
                    for i in xrange(int(countlist[3])):
                        self.awardpoints2(soupid, "xq4_27deee6")
                        
                elif ((unidname[0] == 'x') & ((unidname[1] == 's') | (unidname[1] == 'p'))):
                    self.enter_unid(unidname, soupid, False)
                else:
                    if ((unidname[0] == 'x') & (unidname[1] == 'q') & (unidname[3] == '_')):
                        # Separates low-period (<= 9) non-standard spaceships in medium proximity:
                        self.enter_unid(unidname, soupid, True)
                    else:
                        self.incobject(unidname, 1)
                        self.awardpoints2(soupid, unidname)

        end_time = time.clock()
        self.gridtime += (end_time - start_time)

        return pathological

    def stabilise_soups_parallel(self, root, pos, gsize, sym):

        souplist = [[sym, root + str(pos + i)] for i in xrange(gsize * gsize)]

        return self.stabilise_soups_parallel_orig(gsize, souplist, pos)

    def stabilise_soups_parallel_list(self, gsize, stringlist, pos):

        souplist = [s.split('/') for s in stringlist]

        return self.stabilise_soups_parallel_orig(gsize, souplist, pos)

    # This basically orchestrates everything:
    def stabilise_soups_parallel_orig(self, gsize, souplist, pos):

        ashes = []
        stepsize = 3

        g.new("Random soups")
        if self.rg.ruletype:
            g.setalgo("QuickLife")
        else:
            g.setalgo("RuleLoader")
        g.setrule(self.rg.slashed)

        gspacing = 0

        # Generate and run the soups until stabilisation:
        for i in xrange(gsize * gsize):

            if (i < len(souplist)):

                sym = souplist[i][0]
                prehash = souplist[i][1]

                # Generate the soup from the SHA-256 of the concatenation of the
                # seed with the index:
                g.putcells(hashsoup(prehash, sym), 0, 0)

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
                ashes.append(0)
                ashes.append(0)
            g.select([])

        # Account for any extra enlargement caused by running CoalesceObjects:
        gspacing += 2 ** (stepsize + 1) + 1000

        start_time = time.clock()

        # Remember the dictionary, just in case we have a pathological object:
        prevdict = self.objectcounts.copy()
        prevscores = self.soupscores.copy()
        prevunids = self.superunids[:]

        # Process the soups:
        returncode = self.teenager(gsize, gspacing, ashes, stepsize, 0, pos)

        end_time = time.clock()

        # Calculate the mean delay incurred (excluding qlifetime or error-correction):
        meandelay = (end_time - start_time) / (gsize * gsize)

        if (returncode > 0):
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

        # Return the mean delay so that we can use machine-learning to
        # find the optimal value of sqrtspp:
        return meandelay
    
    def reset(self):

        self.objectcounts = {}
        self.soupscores = {}
        self.alloccur = {}
        self.superunids = []
        self.unids = []

    # Pop the last unidentified object from the stack, and attempt to
    # ascertain its period and classify it.
    def process_unid(self):
#ALGO REF!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        g.new("Unidentified object")
        if self.rg.ruletype:
            g.setalgo("QuickLife")
        else:
            g.setalgo("RuleLoader")
        g.setrule(self.rg.slashed)
        y = self.unids.pop()
        x = self.unids.pop()
        livecells = self.unids.pop()
        bitstring = self.unids.pop()
        g.putcells(livecells, -x, -y, 1, 0, 0, 1, "or")
        
        period = self.bijoscar(1000, 4)
        
        if (period == -1):
            # Infinite growth pattern, probably. Most infinite-growth
            # patterns are linear-growth (such as puffers, wickstretchers,
            # guns etc.) so we analyse to see whether we have a linear-
            # growth pattern:
            descriptor = linearlyse(1500, self.rg.ruletype)
            if (descriptor[0] == "y"):
                return descriptor

            # Similarly check for irregular power-law growth. This will
            # catch replicators, for instance. Spend around 375 000
            # generations; this seems like a reasonable amount of time.
            descriptor = powerlyse(8, 1500, self.rg.ruletype)
            if (descriptor[0] == "z"):
                return descriptor

            # It may be an unstabilised ember that slipped through the net,
            # but this will be handled by error-correction (unless it
            # persists another 2^18 gens, which is so unbelievably improbable
            # that you are more likely to be picked up by a passing ship in
            # the vacuum of space).
            self.superunids.append(livecells)
            self.superunids.append(x)
            self.superunids.append(y)
            
            return "PATHOLOGICAL"
        elif (period == 0):
            return "nothing"
        else:
            if (period == -4):
                
                triple = countxwsses()

                if (triple != (-1, -1, -1)):

                    # Union of Standard Spaceships:
                    return ("USS_" + str(triple[0]) + "_" + str(triple[1]) + "_" + str(triple[2]))

            
            canonised = canonise(abs(period))

            if (canonised == "#"):

                # Okay, we know that it's an oscillator or spaceship with
                # a non-astronomical period. But it's too large to canonise
                # in any of its phases (i.e. transcends a 40-by-40 box).
                self.superunids.append(livecells)
                self.superunids.append(x)
                self.superunids.append(y)
                
                # Append a suffix according to whether it is a still-life,
                # oscillator or moving object:
                if (period == 1):
                    descriptor = ("ov_s"+str(len(livecells)/2))
                elif (period > 0):
                    descriptor = ("ov_p"+str(period))
                else:
                    descriptor = ("ov_q"+str(0-period))

                return descriptor
            
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
#ALGO REF!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        g.new("Unidentified objects")
        if self.rg.ruletype:
            g.setalgo("QuickLife")
        else:
            g.setalgo("RuleLoader")
        g.setrule(self.rg.slashed)

        rowlength = 1 + int(math.sqrt(len(self.superunids)/3))

        for i in xrange(len(self.superunids)/3):

            xpos = i % rowlength
            ypos = int(i / rowlength)

            g.putcells(self.superunids[3*i], xpos * (self.gridsize + 8) - self.superunids[3*i + 1], ypos * (self.gridsize + 8) - self.superunids[3*i + 2], 1, 0, 0, 1, "or")

        g.fit()
        g.update()

    def compactify_scores(self):

        # Number of soups to record:
        highscores = 100
        ilist = sorted(self.soupscores.iteritems(), key=operator.itemgetter(1), reverse=True)

        # Empty the high score table:
        self.soupscores = {}
        
        for soupnum, score in ilist[:highscores]:
            self.soupscores[soupnum] = score

    # Saves a machine-readable textual file containing the census:
    def save_progress(self, numsoups, root, symmetry='C1', save_file=True, payosha256_key=None):

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
        results = "@VERSION "+vnum+"\n"
        results += "@MD5 "+md5root+"\n"
        results += "@ROOT "+root+"\n"
        results += "@RULE "+self.rg.hensel+"\n"
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
        progresspath = dirname + "apgsearch" + separator + "progress" + separator
        if not os.path.exists(progresspath):
            os.makedirs(progresspath)

        filename = progresspath + "search_" + md5root + ".txt"
        
        try:
            f = open(filename, 'w')
            f.write(results)
            f.close()
        except:
            g.warn("Unable to create progress file:\n" + filename)

        if payosha256_key is not None:
            if (len(payosha256_key) > 0):
                return catagolue_results(results, payosha256_key, "post_apgsearch_haul")

    # Save soup RLE:
    def save_soup(self, root, soupnum, symmetry):

        # Soup pattern will be stored in a temporary directory:
        souphash = hashlib.sha256(root + str(soupnum))
        rlepath = souphash.hexdigest()
        rlepath = g.getdir("temp") + rlepath + ".rle"
        
        results = "<a href=\"open:" + rlepath + "\">"
        results += str(soupnum)
        results += "</a>"

        # Try to write soup patterns to file "rlepath":
        try:
            g.store(hashsoup(root + str(soupnum), symmetry), rlepath)
        except:
            g.warn("Unable to create soup pattern:\n" + rlepath)
        return results
        
    def display_census(self, numsoups, root, symmetry):

        dirname = g.getdir("data")
        separator = dirname[-1]
        q = ""
        if self.pseudo:
            q = separator + "pseudo"
        apgpath = dirname + "apgsearch" + q + separator
        objectspath = apgpath + "objects" + separator + self.rg.alphanumeric + separator
        if not os.path.exists(objectspath):
            os.makedirs(objectspath)

        results = "<html>\n<title>Census results</title>\n<body bgcolor=\"#FFFFCE\">\n"
        results += "<p>Census results after processing " + str(numsoups) + " soups (seed = " + root + ", symmetry = " + symmetry + "):\n"

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
                    rledata = "x = 40, y = 40, rule = " + self.rg.slashed + "\n"
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

def apg_verify(rulestring, symmetry, payoshakey):

    verifysoup = Soup()
    verifysoup.rg.setrule(rulestring)
    verifysoup.rg.saveAllRules()

    return_point = [None]

    catagolue_results(rulestring+"\n"+symmetry+"\n", payoshakey, "verify_apgsearch_haul", endpoint="/verify", return_point=return_point)

    if return_point[0] is not None:

        resplist = return_point[0].split("\n")

        if ((len(resplist) >= 4) and (resplist[1] == "yes")):

            md5 = resplist[2]
            passcode = resplist[3]

            stringlist = resplist[4:]

            stringlist = [s for s in stringlist if (len(s) > 0 and s[0] != '*')]

            # g.exit(stringlist[0])

            gsize = 3

            pos = 0

            while (len(stringlist) > 0):

                while (gsize * gsize > len(stringlist)):

                    gsize -= 1

                listhead = stringlist[:(gsize*gsize)]
                stringlist = stringlist[(gsize*gsize):]

                verifysoup.stabilise_soups_parallel_list(gsize, listhead, pos)

                pos += (gsize * gsize)

            # verifysoup.display_census(-1, "verify", "verify")

            payload = "@MD5 "+md5+"\n"
            payload += "@PASSCODE "+passcode+"\n"
            payload += "@RULE "+rulestring+"\n"
            payload += "@SYMMETRY "+symmetry+"\n"

            tlist = sorted(verifysoup.objectcounts.iteritems(), key=operator.itemgetter(1), reverse=True)

            for objname, count in tlist:

                payload += objname + " " + str(count) + "\n"

            catagolue_results(payload, payoshakey, "submit_verification", endpoint="/verify")


def apg_main():
    
    rootstring = ""
    # ---------------- Hardcode the following inputs if running without a user interface ----------------
    rulestring = g.getstring("Which rule to use?", "B3/S23")
    upload = g.getstring("Upload to Catagolue? (y/n)", "y").lower() == "y"
    orignumber = int(g.getstring("How many soups to search between successive uploads?", "10000")) if upload else int(g.getstring("How many soups to search?", "5000000"))
    if not upload:
        rootstring = g.getstring("What seed to use for this search (make this unique)?", datetime.datetime.now().isoformat()+"")
    symmstring = g.getstring("What symmetries to use?", "C1")
    pseudo = False
    payoshakey = g.getstring("Please enter your key (visit "+get_server_address()+"/payosha256 in your browser).", "puffersea") if upload else None
    if not upload:
        pseudo = g.getstring("Count pseudo-patterns (y/n)", "n")
    # ---------------------------------------------------------------------------------------------------
    
    if upload:
        # Sanitise input:
        orignumber = max(orignumber, 10000)
        orignumber = min(orignumber, 100000000)
    number = orignumber
    initpos = 0
    if symmstring not in ["8x32", "C1", "C2_1", "C2_2", "C2_4", "C4_1", "C4_4", "D2_+1", "D2_+2", "D2_x", "D4_+1", "D4_+2", "D4_+4", "D4_x1", "D4_x4", "D8_1", "D8_4"]:
        g.exit(symmstring+" is not a valid symmetry option")
        
    soup = Soup()
    if not "/" in rulestring:
        soup.rg.ruletype = False

    quitapg = False

    # Create associated rule tables:
    soup.rg.setrule(rulestring)
    soup.rg.saveAllRules()
    
    soup.pseudo = pseudo == "y"
    if soup.pseudo:
        soup.decompositions = {}

    # We have 100 soups per page, instead of one. This parallel approach
    # was suggested by Tomas Rokicki, and results in approximately a
    # fourfold increase in soup-searching speed!
    sqrtspp_optimal = 10

    # Initialise the census:
    start_time = time.clock()
    if upload:
        f = (lambda x : 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'[ord(x) % 56])
        rootstring = ''.join(map(f, list(hashlib.sha256(payoshakey + datetime.datetime.now().isoformat()).digest()[:12])))
    scount = 0

    while (quitapg == False):

        if upload:
            # Peer-review some soups:
            for i in xrange(5):
                pass #apg_verify("B3S23", "C1", payoshakey)
        
        #Somehow, apg_verify seems to be messing with the rules.
        soup.rg.setrule(rulestring)

        # The 'for' loop has been replaced with a 'while' loop to allow sqrtspp
        # to vary during runtime. The idea is that apgsearch can apply a basic
        # form of machine-learning to dynamically locate the optimum sqrtspp:
        while (scount < number):

            delays = [0.0, 0.0, 0.0]

            for i in xrange(1000):

                page_time = time.clock()

                sqrtspp = (sqrtspp_optimal + (i % 3) - 1) if (i < 150) else (sqrtspp_optimal)

                # Don't overrun:
                while (scount + sqrtspp * sqrtspp > number):
                    sqrtspp -= 1

                meandelay = soup.stabilise_soups_parallel(rootstring, scount + initpos, sqrtspp, symmstring)
                if (i < 150):
                    delays[i % 3] += meandelay
                scount += (sqrtspp * sqrtspp)

                current_speed = int((sqrtspp * sqrtspp)/(time.clock() - page_time))
                alltime_speed = int((scount)/(time.clock() - start_time))
                
                g.show(str(scount) + " soups processed (" + str(current_speed) +
                       " per second current; " + str(alltime_speed) + " overall)" +
                       " : (type 's' to see latest census or 'q' to quit).")
                
                event = g.getevent()
                if event.startswith("key"):
                    evt, ch, mods = event.split()
                    if ch == "s":
                        soup.save_progress(scount, rootstring, symmstring)
                        soup.display_census(scount, rootstring, symmstring)
                    elif ch == "q":
                        quitapg = True
                        break

                if (scount >= number):
                    break
                
            if (quitapg == True):
                break

            # Change sqrtspp to a more optimal value:
            if (scount < number):
                sqrtspp_new = sqrtspp_optimal

                if (delays[0] < delays[1]):
                    sqrtspp_new = sqrtspp_optimal - 1
                if ((delays[2] < delays[1]) and (delays[2] < delays[0])):
                    sqrtspp_new = sqrtspp_optimal + 1

                sqrtspp_optimal = sqrtspp_new
                sqrtspp_optimal = max(sqrtspp_optimal, 5)

            # Compactify highscore table:
            soup.compactify_scores()

        if (quitapg == False):
            # Save progress, upload it to Catagolue, and reset the census if successful:
            a = soup.save_progress(scount, rootstring, symmstring, payosha256_key=payoshakey)
            if (a == 0):
                # Reset the census:
                soup.reset()
                start_time = time.clock()
                f = (lambda x : 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'[ord(x) % 56])
                rootstring = ''.join(map(f, list(hashlib.sha256(rootstring + payoshakey + datetime.datetime.now().isoformat()).digest()[:12])))
                scount = 0
                number = orignumber
            else:
                number += orignumber

    end_time = time.clock()

    soup.save_progress(scount, rootstring, symmstring, payosha256_key=payoshakey)

    soup.display_unids()
    soup.display_census(scount, rootstring, symmstring)

def symmetry_test():

    g.new("Symmetry test")

    symmetries = [["C1", "8x32"],
                  ["C2_1", "C2_2", "C2_4"],
                  ["C4_1", "C4_4"],
                  ["D2_+1", "D2_+2", "D2_x"],
                  ["D4_+1", "D4_+2", "D4_+4", "D4_x1", "D4_x4"],
                  ["D8_1", "D8_4"]]

    for i in range(len(symmetries)):
        for j in range(len(symmetries[i])):

            g.putcells(hashsoup("sym_test", symmetries[i][j]), 120 * j + 60 * (i % 2), 80 * i)
    g.fit()
    
# Obtain the parameters to conduct the search:
number = 0
rootstring = ""
rulestring = ""
symm = ""
pseudo = ""
apg_main()
'''else:
    number = int(g.getstring("How many soups to search?", "5000000"))
    rootstring = g.getstring("What seed to use for this search (make this unique)?", datetime.datetime.now().isoformat()+"")
    rulestring = g.getstring("Which rule to use?", "B3/S23")
    symm = check(g.getstring("What symmetry to use (default is C1)?", "C1"))
    pseudo = g.getstring("Count pseudo-patterns (y/n)", "n")
    initpos = 0 # int(g.getstring("Initial position: ", "0"))
    if not "/" in rulestring:
        soup.rg.ruletype = False
    
    start_time = time.clock()
    soup = Soup()
    soup.rg.setrule(rulestring)
    soup.rg.saveAllRules()
    soup.pseudo = pseudo == "y"
    if soup.pseudo:
        soup.decompositions = {}
    
    symmstring = convert(symm)
    
    scount = 0
    
    # We have 100 soups per page, instead of one. This parallel approach
    # was suggested by Tomas Rokicki, and results in approximately a
    # fourfold increase in soup-searching speed!
    sqrtspp = 10
    spp = sqrtspp ** 2
    
    # Do stuff repeatedly:
    for i in xrange(int((number-1)/spp)+1):
        soup.stabilise_soups_parallel(rootstring, scount + initpos, sqrtspp, symmstring)
        scount = spp*(i+1)
        g.show(str(scount) + " soups processed ("+str(int(scount/(time.clock() - start_time)))+" per second) : (type 's' to see latest census or 'q' to quit).")
    
        # Automatically save progress every 250000 soups:
        if ((scount % 250000) == 0):
            soup.save_progress(scount, rootstring, symm)
        
        event = g.getevent()
        if event.startswith("key"):
            evt, ch, mods = event.split()
            if ch == "s":
                lastalgo = g.getalgo()
                lastrule = g.getrule()
                if soup.rg.ruletype:
                    g.setalgo("QuickLife")
                else:
                    g.setalgo("RuleLoader")
                g.setrule(rulestring)
                soup.save_progress(scount, rootstring, symm)
                soup.display_census(scount, rootstring, symm, symmstring)
                g.setrule(lastrule)
                g.setalgo(lastalgo)
            elif ch == "q":
                break
    
    end_time = time.clock()
    #ALGO REF!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if soup.rg.ruletype:
        g.setalgo("QuickLife")
    else:
        g.setalgo("RuleLoader")
    g.setrule(rulestring)
    
    soup.save_progress(scount, rootstring, symm)
    
    # Give the number of soups processed together with the amount of time
    # elapsed (and indications as to which parts of the script are taking
    # the longest).
    g.show(str(scount) + " soups processed in " + str(end_time - start_time) +
           "(" + str(soup.qlifetime) + ", " + str(soup.ruletime) + ", " + str(soup.gridtime) + ") secs.")
    
    soup.display_unids()
    soup.display_census(scount, rootstring, symm, symmstring)
'''