#!/usr/bin/python
import argparse, subprocess, sys, os.path, re
from utils import Parameter, printResults, getParamsFromModule,getMinimStr, beamspotAxialId, beamspotStereoId,paramMap
import buildSteering

pedeBin = 'MillepedeII/pede'

def getArgs():
    parser = argparse.ArgumentParser(description='MP help script')
    parser.add_argument('-i','--inputfiles',nargs='+', required=True, help='List of binary input files.')
    parser.add_argument('-f','--float', nargs='+', help='List of MP parameters to float')
    parser.add_argument('-M','--Modules', nargs='+', help='List of modules to float, e.g. L3b L5b')
    parser.add_argument('-p','--parameters', help='Default parameters')
    parser.add_argument('-m','--minimization', default='steering/steer_minimization_template.txt', help='Default minimization settings')
    parser.add_argument('-d','--debug', action='store_true', help='Debug flag')
    parser.add_argument('-n','--name', help='If given output files will get tagged by this name.')
    parser.add_argument('-b','--beamspot', action='store_true',help='Beamspot is included in the fit')
    parser.add_argument('--SC', action='store_true',help='Survey constraint')
    parser.add_argument('--BSC', action='store_true',help='Beamspot constraint')
    args = parser.parse_args()
    print args
    return args

def getDefaultParams(beamspot=False):
    pars = []
    for h in range(1,3):
        for t in range(1,3):
            for d in range(1,4):
                r = range(1,19)
                if beamspot:
                    r.append(beamspotStereoId)
                    r.append(beamspotAxialId)
                for sensor in r:
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


def buildSteerFile(name,inputfiles,pars,minimStr,surveyConstraints=False,beamspotConstraints=False):
    try:
        f = open(name,'w')
    except IOError:
        print 'cannot open file ', name
        return False
    else:
        f.write("CFiles\n")
        for ipf in inputfiles:
            f.write(ipf + "\n")
        
        f.write("\nParameter\n")
        for p in pars:
            f.write(p.toString() + "\n")

        if surveyConstraints:
            f.write(buildSteering.getSurveyMeasurements(paramMap))
            f.write("\n\n")

        if beamspotConstraints:
#            f.write(buildSteering.getBeamspotConstraints(paramMap))
            f.write(buildSteering.getBeamspotConstraintsFloatingOnly(pars))
            f.write("\n\n")
        
        f.write("\n\n")
        f.write(minimStr)
        f.close()        
        return True





def saveResults(inputfilenames, name):
    names = [ os.path.splitext(os.path.basename(n))[0] for n in inputfilenames] 
    filename = '-'
    filename = filename.join(names)
    status = subprocess.call("cp millepede.res " + " millepede-" + filename + "-" + name + ".res", shell=True)
    status = subprocess.call("cp millepede.eve " + " millepede-" + filename + "-" + name + ".eve", shell=True)
    status = subprocess.call("cp millepede.log " + " millepede-" + filename + "-" + name + ".log", shell=True)
    status = subprocess.call("cp millepede.his " + " millepede-" + filename + "-" + name + ".his", shell=True)
    #status = subprocess.call("cp millepede.res " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".res", shell=True)
    #status = subprocess.call("cp millepede.eve " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".eve", shell=True)
    #status = subprocess.call("cp millepede.log " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".log", shell=True)
    #status = subprocess.call("cp millepede.his " + " millepede-" + os.path.splitext(os.path.basename(inputfilename))[0] + "-" + name + ".his", shell=True)



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
    pars = getDefaultParams(args.beamspot)
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

    floatingPars = []

    # find the floating parameter for this fit
    if args.Modules is not None:
        for m in args.Modules:
            floatingPars.extend([str(mp) for mp in getParamsFromModule(m)])
    
    if args.float is not None:
        floatingPars.extend(args.float)

    updateFloatParams(pars,floatingPars)

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
    ok = buildSteerFile(name,args.inputfiles,pars,minimStr,args.SC,args.BSC)
    if not ok:
        print "Couldn't build steering file"
        sys.exit(1)

    # run the fit
    runPede(name)

    # print results
    printResults()

    # save results to a specific name if supplied
    if args.name != None:
        saveResults(args.inputfiles, args.name)

    
if __name__ == "__main__":

    args = getArgs()


    main(args)
