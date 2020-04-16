import argparse, subprocess, sys, os.path, re

paramMapFile = 'hpsSvtParamMap.txt'
global paramMap
paramMap= {}
beamspotAxialId = 99
beamspotStereoId = 98


class FloatOption:
    def __init__(self,name):
        self.name = name
        self.float = []
    def add(self, listOfObj):
        self.float.append(listOfObj)
    def getName(self):
        return self.name
    def get(self,i):
        return self.float[i]
    def getNIter(self):
        return len(self.float)
    def toString(self):
        s = self.name + ':\n'
        i=0
        s += '%10s  %s\n' % ('Iteration', 'Floating')
        for v in self.float:
            s += '%10d  %s\n' % (i,v)
            i=i+1
        return s


class Parameter:
    def __init__(self, i,val,active,error=None,change=None):
        self.i = i
        self.name = getSensorName(i)
        self.val = val
        self.active = active
        self.error = error
        self.change = change
    @classmethod
    def fromstr(cls,s):
        i = int(s.split()[0])
        val = float(s.split()[1])
        active = float(s.split()[2])
        if(len(s.split())>4):
            error = float(s.split()[4])
            change = float(s.split()[3])
        else:
            error = None
            change = None
        return cls(i,val,active,error,change)
    def toString(self):
        s = '%5d %10f %10f' % (self.i, self.val, self.active)
        if self.error!=None:
            s += '    %f' % self.error
        s += ' %s' % self.name
        if self.change!=None:
            s += '   (change %f)' % self.change
        return s
    def toNiceString(self):
        error = ''
        if self.error!=None:
            error = '%10f' % self.error
        change = ''
        if self.change!=None:
            change = ' (change %10f)' % self.change
        s = '%40s %10f +- %s %5d %s' % (self.name, self.val, error, self.i, change)
        return s

def cmpSensors(a,b):
    h_a = getHalf(a.i)
    h_b = getHalf(b.i)
    if h_a != h_b:
        print 'cannot compare in two different halves'
        sys.exit(1)
    l_a = getModuleNrFromDeName(a.name)
    l_b = getModuleNrFromDeName(b.name)
    if l_a < l_b:
        return -1
    elif l_a > l_b:
        return 1
    else:
        t_a = isAxial(a.name)
        t_b = isAxial(b.name)
        if t_a==t_b:
            if l_a < 4: return 0
            s_a = isHole(a.name)
            s_b = isHole(b.name)
            if s_a and s_b:
                return 0
            elif s_a and not s_b:
                return -1
            else:
                return 1
        elif t_a == 'axial':            
            if h_a == 't': return -1
            else: return 1
        else:
            if h_a == 't': return 1
            else: return -1

    

def initParamMap():
    try:
        f = open(paramMapFile,'r')
    except IOError:
        print 'Cannot open ', paramMapFile
        sys.exit(1)
    else:
        for line in f.readlines():
            if 'MilleParameter' in line:
                continue
            paramMap[int(line.split()[0])] = line.split()[1]
        print 'Initialized param map with ', len(paramMap), ' parameters'
        #for k,v in paramMap.iteritems():
        #    print k,' ', v
        f.close()

def getSensorName(i):
    if not bool(paramMap):
        initParamMap()        
    if i in paramMap:
        return paramMap[i]
    else:
        print 'Cannot find sensor for param ', i
        sys.exit(1)

def printEigenInfo(mpfile='millepede.eve'):
    status = subprocess.call("cat " + mpfile, shell=True)
    return



def getPathSorted(paramaters):
    result = []
    for p in parameters:
        l = getModuleNrFromDeName

def getResResults(mpresfile='millepede.res', ignoreZero=False):
    result = []
    try:
        f = open(mpresfile,'r')
    except IOError:
        print 'cannot open res file ' 
        return result
    else:
        print mpresfile
        active=False
        for l in f.readlines():
            if active:
                p  = Parameter.fromstr(l)
                doIt = True
                if p.val==0. and ignoreZero:
                    doIt=False
                if doIt:
                    result.append(p)
            if 'Parameter' in l:
                active=True
    f.close()
    return result

def printResResults(mpresfile='millepede.res', ignoreZero=True):
    parameters = getResResults(mpresfile,ignoreZero)
    for p in parameters:
        print p.toNiceString()
    return

def printResults():
    printEigenInfo()
    printResResults()


def getModuleNrFromDeName(deName):
    m = re.search("module_L(\d)\S_", deName)
    if m==None:
        print 'Wrong module name format ', module
        sys.exit(1) 
    else:
        l = m.group(1)
        return int(l)

def isAxial(deName):
    if 'axial' in deName:
        return True
    elif 'stereo' in deName:
        return False
    else:
        print 'this deName doesnt contain axial or stereo ?! ' , deName
        sys.exit(1)

def isHole(deName):
    if 'hole' in deName:
        return True
    elif 'slot' in deName:
        return False
    else:
        print 'this deName doesnt contain hole or slot?! ' , deName
        sys.exit(1)

def getDir(param):
    i = int((param%1000)/100.0)
    if i==1:
        return 'u'
    elif i==2:
        return 'v'
    elif i==3:
        return 'w'
    else:
        print 'cannot extract dir from param ', param
        sys.exit(1)

def getType(param):
    i = int((param%10000)/1000.0)
    if i==1:
        return 't'
    elif i==2:
        return 'r'
    else:
        print 'cannot extract type from param ',param
        sys.exit(1)

def getHalf(param):
    i = int((param%100000)/10000.0)
    if i==1:
        return 't'
    elif i==2:
        return 'b'
    else:
        print 'cannot extract half from param ',param
        sys.exit(1)

def getParamsFromModule(module):
    params = []       
    m = re.search("L([0-6])([AS]?)([hs]?)([tb])_([tr])([uvw]$)", module)
    if m==None:
        print 'Wrong module name format ', module, '. Should be matched by regexp. \'L[1-6][AS]?[hs]?[tb]_[tr][uvw]\''
        sys.exit(1) 
    else:
        print m.groups()
        layer = int(m.group(1))
        axialOrStereo = m.group(2)
        holeOrSlot = m.group(3)
        half = m.group(4)
        typ = m.group(5)
        direction = m.group(6)
        if holeOrSlot!='' and layer < 4:
            print 'L1-3 cannot have hole or slot defined ', module
            sys.exit(1)
        print module, ': ', layer, ' ', axialOrStereo, ' ', holeOrSlot, ' ', half, ' ', typ, ' ', direction
        for k,v in paramMap.iteritems():
            #print 'testing ', k,  ' ', v
            loopLayer = getModuleNrFromDeName(v)
            loopTyp = getType(k)
            loopHalf = getHalf(k)
            loopDirection = getDir(k)
            if layer == loopLayer and loopDirection==direction and loopTyp==typ and half==loopHalf:
                #print 'found cand ', axialOrStereo , ' ', isAxial(v)
                passAx = True
                if axialOrStereo != '':
                    if axialOrStereo=='S' and isAxial(v):
                        passAx = False
                    elif axialOrStereo=='A' and not isAxial(v):
                        passAx = False
                passHole = True
                if holeOrSlot != '':
                    if holeOrSlot=='h' and not isHole(v):
                        passHole = False
                    elif holeOrSlot=='s' and isHole(v):
                        passHole = False
                if passAx and passHole:
                    #print 'found it'
                    params.append(k)
        if not bool(params):
            print 'Cannot find millepede param for \'', module,'\''
        print 'Found ', len(params),' params from \'', module,'\' :', params
        #sys.exit(0)
    return params

def getMinimStr(filename):
    s = ""
    try:
        f_min = open(filename,'r')
    except IOError:
        print 'cannot open ', filename
    else:
        for l in f_min.readlines():
            s += l
        f_min.close()
    return s


def getRunNr(name):
#    m = re.search('hps_00(\d{4})\S',name)
    m = re.search('00(\d{4})\S',name)
    if m==None:
        print 'Cannot find run number from ', name
#        sys.exit(1)
    else:
        return int(m.group(1))

