#!/usr/bin/python

import sys, os, argparse, re, subprocess
from utils import FloatOption

listOfFloats = []


def getArgs():
  parser = argparse.ArgumentParser(description='Run MP.')
  parser.add_argument('--run',action='store_true',help='Actually run this.')
  parser.add_argument('--files','-f',nargs='+', required=True, help='Input binary files.')
  parser.add_argument('--switch','-s', type=int, help='Switch to change what patter of floating modules.')
  parser.add_argument('--listoptions','-l', action='store_true', help='List available defined floating options.')
  
  args = parser.parse_args();
  print args
  return args


def initListOfFloatOptions():
    opt = FloatOption('L2_tu')
    opt.add('L2t_tu L2b_tu')
    listOfFloats.append(opt)
#1
    opt = FloatOption('L2b_L4b_tu')
    opt.add('L2b_tu L4b_tu')
    listOfFloats.append(opt)
#2
    opt = FloatOption('all')
    opt.add('L2b_tu  L4b_tu  L4hb_tu L5hb_tu L6hb_tu')
    listOfFloats.append(opt)

    return


def printFloatOptions():
    if not bool(listOfFloats):
        initListOfFloatOptions()
    print len(listOfFloats), ' options:\n'
    i=0
    for opt in listOfFloats:
        print 'Option ', i, ': ', opt.toString()
        i=i+1
    return

def getFloatOption(switch):
    if not bool(listOfFloats):
        initListOfFloatOptions()
    if switch<len(listOfFloats):
        return listOfFloats[switch]
    else:
        print 'This switch ', switch, ' is not defined'
        print printFloatOptions()
        sys.exit(1)


    


def run(fname, opt):

    print '\n====\nRun on file ', fname

    name = opt.getName()
    for i in range(opt.getNIter()):
        print 'Iteration ', i
        modules = opt.get(i)
        if name != opt.getName():
            pars = '-p millepede-' + os.path.splitext(os.path.basename(fname))[0] + '-' + name + '.res'
        else:
            pars = ''
        name += 'Iter' + str(i) 
        for m in modules.split():
            name += '-' + m
        
        cmd = 'python runMP.py -i ' + fname + ' -M ' + modules + ' ' + pars + ' --name ' + name
        print cmd
        if args.run:
            subprocess.call(cmd,shell=True)
    return 0



def main(args):

    print 'Run MP on ', len(args.files), ' input files'
    if args.listoptions:
        printFloatOptions()
        sys.exit(1)
    if args.switch==None:
        print 'Need to specify which option to run using the --switch'
        sys.exit(0)
    opt = getFloatOption(args.switch)
    print 'Switch ', args.switch
    if opt==None:
        print 'Couldnt find option'
        sys.exit(1)
    print opt.toString()

    for fname in args.files:
        run(fname,opt)
    

if __name__ == '__main__':
    args = getArgs()
    main(args)
