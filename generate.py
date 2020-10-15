'''
Make assignments for who gives gifts to whom. Repeats until the following
rules are satisfied:

0) Everyone gives a gift, everyone gets a gift
1) A never buys for A
2) If A buys for B, B does not buy for A
3) A does not buy for B if A and B are from the same group
4) If info from the previous run is provided, nobody buys for the same person again.
'''

import random, json, sys, os

def LoadGroups(cfgFilename):
    '''Reads the groups from the given JSON filename and returns them as
    (a list of lists of names, a list of pairings in lastRun format)'''
    with open(cfgFilename, 'rt') as f:
        cfg = json.loads(f.read())
    groups = cfg['groups']
    lastRun = (cfg.get('lastRun') or '').strip()
    if not lastRun:
        lastRun = []
    else:
        lastRun = lastRun.split('::') # see FormatPairings
    return groups, lastRun

def AttemptToGenPairings(groups, lastRun, maxAttempts=1000):
    '''Given a list of groups (where each group is a list of names of people in that group),
    randomly generates a list of pairs between people who give a gift to another person.
    Does not validate the results. Note that this function is purely random and very simplistic,
    so it's possible to get stuck. If it can't come up with a workable set after maxAttempts
    tries, it gives up and returns None.'''
    # Generate a complete set of givers and getters - instead of just using the name, we
    # identify each person as (groupIndex, name) in case there are name duplications
    givers = []
    getters = []
    for i, names in enumerate(groups):
        for name in names:
            person = (name, i)
            givers.append(person)
            getters.append(person)

    # Assign everyone to a giving and getting pair
    assignments = []
    pairings = set() # set so far of (A,B) mappings, meaning A gives to B
    attempts = 0
    RC = random.choice
    while givers:
        if attempts > maxAttempts:
            return None

        giver = RC(givers)
        getter = RC(getters)

        # Don't let a person buy for themself
        if giver == getter:
            attempts += 1
            continue

        # Don't pair up two people from the same group
        if giver[1] == getter[1]:
            attempts += 1
            continue

        # Don't use a pairing from last time
        pairing = (giver, getter)
        inverse = (getter, giver)
        if PairingToString(pairing) in lastRun:
            attempts += 1
            #print('skipping', pairing)
            continue

        # Don't use a pairing that already exists, and don't use a pairing if we already
        # have the reverse (if A is already giving to B, don't have B give to A)
        if pairing in pairings or inverse in pairings:
            attempts += 1
            continue

        # Save the pairing and cross these people off the lists
        pairings.add(pairing)
        givers.remove(giver)
        getters.remove(getter)

    if getters:
        print('Somehow there are leftover getters! ' + repr(getters))
        return None
    print('took %d attempts' % attempts)
    return pairings

def GenPairings(groups, lastRun):
    '''Generates gift exchange pairings until a valid set is found and returns them
    as a list of ((giverName, giverGroup (i.e. group index))), (getterName, getterGroup)). Keeps trying
    until a valid attempt is generated.'''
    tries = 0
    while 1:
        tries += 1
        pairings = AttemptToGenPairings(groups, lastRun)
        if pairings is not None:
            return pairings
        print(' (Stuck, trying again)')

def HaveDuplicateNames(groups):
    '''Inspects the groups to see if there are any people who share the same name. Used to
    simplify the output in cases where there are not duplicates.'''
    knownNames = set()
    for groupNames in groups:
        for name in groupNames:
            name = name.lower().strip()
            if name in knownNames:
                return True
            knownNames.add(name)
    return False

def PairingToString(pairing):
    '''(givername, givergroup),(receivername,receivergroup) --> a consistent format for checking against prior runs'''
    giver, getter = pairing
    giverName, giverGroup = giver
    giverName = giverName.lower().strip().replace('"', '')
    getterName, getterGroup = getter
    getterName = getterName.lower().strip().replace('"', '')
    return '%d%s-%d%s' % (giverGroup, giverName, getterGroup, getterName)

def FormatPairings(pairings):
    '''Returns (pairings as a pretty string, pairings as a string in lastRun format)'''
    showGroups = HaveDuplicateNames(groups)
    printLines = []
    lastRuns = []
    for pairing in sorted(pairings):
        giver, getter = pairing
        giverName, giverGroup = giver
        getterName, getterGroup = getter
        lastRuns.append(PairingToString(pairing))
        if showGroups:
            printLines.append('%s (%d) gives to %s (%d)' % (giverName, giverGroup, getterName, getterGroup))
        else:
            # no duplicate names, so we can simplify the output a bit
            printLines.append('%s gives to %s' % (giverName, getterName))
    formatPrint = '\n'.join(printLines)
    formatLastRun = '::'.join(lastRuns) # see LoadGroups
    return formatPrint, formatLastRun

if __name__ == '__main__':
    args = list(sys.argv[1:])
    cfgFilename = args.pop(0)
    groups, lastRun = LoadGroups(cfgFilename)
    pairings = GenPairings(groups, lastRun)
    formatPrint, formatLastRun = FormatPairings(pairings)
    print(formatPrint)
    print('\nNOTE: if you choose to use the above assignments, then add the following line to your JSON file')
    print('to prevent duplicates next time:\n')
    print('  "lastRun":"%s"\n' % formatLastRun)

