#!/usr/bin/python
import argparse, subprocess, sys, os.path

pedeBin = 'MillepedeII/pede'

class Parameter:
    def __init__(self, i,val,active,error=None):
        self.i = i
        self.val = val
        self.active = active
        self.error=error
    @classmethod
    def fromstr(cls,s):
        i = int(s.split()[0])
        val = float(s.split()[1])
        active = float(s.split()[2])
        if(len(s.split())>4):
            error = float(s.split()[4])
        else:
            error = None
        return cls(i,val,active,error)
    def toString(self):
        s = '%5d %10f %10f' % (self.i, self.val, self.active)
        if self.error!=None:
            s += '    %f' % self.error
        return s


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

def getDefaultParams():
    pars = []
    for h in range(1,3):
        for t in range(1,3):
            for d in range(1,4):
                for sensor in range(1,19):
                    if sensor<10:
                        s = "0" + str(sensor)
                    else:
                        s = str(sensor)
                    mpId = str(h) + str(t) + str(d) + s
                    p = Parameter(int(mpId),0.0,-1.0)
                    pars.append(p)
    return pars

def getParams(parfilename):
    pars = []
    if parfilename!=None:
        try:
            f_pars = open(parfilename,'r')
        except IOError:
            print 'cannot open ', parfilename
        else:
            for l in f_pars.readlines():
                if len(l.split())==3 or len(l.split())==5:
                    p = Parameter( int(l.split()[0]), float(l.split()[1]), float(l.split()[2]))
                    pars.append(p)
            f_pars.close()
    return pars


def updateFloatParams(pars,floats):
    print 'There are ',len(floats),' parameters to float'    
    for i in floats:
        pfound = None
        for p in pars:
            if p.i==int(i):
                pfound = p
        if pfound == None:
            print 'Cannot find parameter ', i
            sys.exit(1)
        if args.debug:
            print 'Float ', p.i
        pfound.active = 0
    return

def updateParams(pars,otherparms,resetActive=True):
    print 'There are ',len(otherparms),' to update'
    parsnew = []
    for p in pars:
        pfound = None
        for op in otherparms:
            if p.i==op.i:
                pfound = op
        if pfound != None:
            if resetActive:
                pfound.active=-1
            parsnew.append(pfound)
        else:
            parsnew.append(p)
    return parsnew


def buildSteerFile(name,inputfile,pars,minimStr):
    try:
        f = open(name,'w')
    except IOError:
        print 'cannot open file ', name
        return False
    else:
        f.write("CFiles\n")
        f.write(inputfile + "\n")

        f.write("\nParameter\n")
        for p in pars:
            f.write(p.toString() + "\n")
        
        f.write("\n\n")
        f.write(minimStr)
        f.close()        
        return True


def printEigenInfo():
    status = subprocess.call("cat millepede.eve", shell=True)
    return

def printResResults():
    try:
        f = open('millepede.res','r')
    except IOError:
        print 'cannot open res file ' 
        return
    else:
        active=False
        for l in f.readlines():
            if active:
                if len(l.split())==5:
                    p  = Parameter.fromstr(l)
                    if p.active != -1.0:
                        delta = float(l.split()[3])
                        print "%s change is %f or %.1f percent" % ( p.toString(), delta, delta/(p.val-delta)*100.0)
            if 'Parameter' in l:
                active=True
    return


def printResults():
    printEigenInfo()
    printResResults()

def saveResults(inputfilename, name):
    status = subprocess.call("cp millepede.res " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".res", shell=True)
    status = subprocess.call("cp millepede.eve " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".eve", shell=True)
    status = subprocess.call("cp millepede.log " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".log", shell=True)
    status = subprocess.call("cp millepede.his " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".his", shell=True)



def runPede(filename):
    print "Clean up..."
    status = subprocess.call("rm millepede.res", shell=True)
    status = subprocess.call("rm millepede.eve", shell=True)
    status = subprocess.call("rm millepede.log", shell=True)
    status = subprocess.call("rm millepede.his", shell=True)
    
    s = pedeBin + " " + filename
    print 'Execute: ', s
    status = subprocess.call(s, shell=True)

def main(args):

    print "just GO"

    # initialize all the parameters into a list
    pars = getDefaultParams()
    print 'Found ', len(pars), 'default parameters'
    if args.debug:
        for p in pars:
            print p.toString()
    

    # check if there is a supplied parameter file.
    # this could be a result file from a previous fit
    inputpars = getParams(args.parameters)
    print 'Found ', len(inputpars), ' parameters to update'
    if args.parameters != None:
        if len(inputpars) != len(pars):
            print 'Wrong number of input parameters. Require all to be present in the input file, but not all active'
            sys.exit(1)
    
    if args.debug:
        for p in pars:
            print p.toString()

    # update the default parameters with the new input file
    # normally require that they become inactive here
    pars = updateParams(pars,inputpars,True)

    # find the floating parameter for this fit
    if args.float==None:
        print 'ERROR: need to supply at least 1 parameter to be floated.'
        return 1

    updateFloatParams(pars,args.float)

    print 'List of floating parameters:'
    nfloats = 0
    for p in pars:
        if p.active==0:
            print p.toString()
            nfloats=nfloats+1

    if nfloats<1:
        print 'Something is wrong. At least one parameter need to be floating before running.'
        sys.exit(1)
    

    # get MP minimization settings
    minimStr = getMinimStr(args.minimization)

    # build the actual steering file
    name = "steer.txt"
    ok = buildSteerFile(name,args.inputfile,pars,minimStr)
    if not ok:
        print "Couldn't build steering file"
        sys.exit(1)

    # run the fit
    runPede(name)

    # print results
    printResults()

    # save results to a specific name if supplied
    if args.name != None:
        saveResults(args.inputfile, args.name)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MP help script')
    parser.add_argument('-i','--inputfile', required=True, help='List of parameters to float')
    parser.add_argument('-f','--float', nargs='+', help='List of parameters to float')
    parser.add_argument('-p','--parameters', help='Default parameters')
    parser.add_argument('-m','--minimization', default='steering/steer_minimization_template.txt', help='Default minimization settings')
    parser.add_argument('-d','--debug', action='store_true', help='Debug flag')
    parser.add_argument('-n','--name', help='If given output files will get tagged by this name.')
    args = parser.parse_args()
    print args


    main(args)
