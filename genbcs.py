# CSM: Python Module for the Conventional Subdomain Modeling Approach
#   Copyright (C) 2017 
#   Computational Modeling Group, NCSU <http://www4.ncsu.edu/~jwb/>
#   Alper Altuntas <alperaltuntas@gmail.com>

import os
import sys
import readline, glob
from csm import Domain

# genbcs.py: 
# Generates the subdomain boundary conditions file(s)

# Prepares a given full domain for an ADCIRC run. 
# (Generates a fort.015 file and modifies fort.26 if it is a ADCIRC+SWAN run).
def main(fulldir, subdir, sbtiminc):
    
    # Print header:
    print ""
    print '\033[95m'+'\033[1m'+"NCSU Subdomain Modeling for ADCIRC+SWAN"+'\033[0m'
    print ""
    print "Generating ADCIRC boundary conditions files for the subdomain at",subdir,"\n"

    # Instantiate the domains:
    full = Domain(fulldir)
    sub = Domain(subdir)

    # Get the runtype    
    runtype="s"
    isSerialRun = os.path.exists(full.dir+"fort.065")
    isParallelRun = os.path.exists(full.dir+"PE0000/fort.065")
    
    if isSerialRun and (not isParallelRun):
        runtype="s"
    elif isParallelRun and (not isSerialRun):
        runtype="p"
    else:
        while True:
            runtype = raw_input('Enter the type of the full domain run '+ \
                                '("p" for parallel, or "s" for serial):\n')
            if runtype=='p' or runtype=='s':
                break
            elif runtype=='"p"':
                runtype = 'p'
                break
            elif runtype=='"s"':
                runtype = 's'
                break
            else:
                print '\033[91m'+"\nInvalid key!"+'\033[0m'

    # Read input files:
    full.readFort14()
    if runtype=="p": full.readFort80()
    sub.readFort14()
    sub.readPy140()
    
    # Open full domain fort.065
    if runtype=="s":
        full.openFort065()
    else:
        full.openFort065_parallel()

    # Convert sbtiminc to integer
    if sbtiminc==None:
        sbtiminc = full.nspoolgs
    else:
        sbtiminc = int(sbtiminc)

    # Check if sbtiminc is a multiple of NSPOOLGS:
    if not (sbtiminc%full.nspoolgs == 0):
        print '\033[91m'+"\nWARNING!"+'\033[0m'
        print "The parameter sbtiminc (="+str(sbtiminc)+") is not a multiple of "+\
              "the full domain parameter nspoolgs (="+str(full.nspoolgs)+")"
        print "Setting sbtiminc to",full.nspoolgs
        sbtiminc = full.nspoolgs
        
    print "\n\t Writing fort.019 at",sub.dir,"\n"

    # Open subdomain b.c. file:
    sub.openFort019(sbtiminc,full.nrtimesteps)
    
    # Write the boundary conditions:
    if runtype=="s":
        for i in range(full.nrtimesteps):
            full.readFort065()
            sub.writeFort019(full)
            #print out percentage
            if i%1000==0:
                sys.stdout.write('\r')
                sys.stdout.write("%d%%" %(100*(i+1)/full.nrtimesteps))
                sys.stdout.flush()
        sub.writeFort019(full)
    else:
        for i in range(full.nrtimesteps):
            full.readFort065_parallel()
            if i==0: sub.createProcMapping(full)
            sub.writeFort019_parallel(full)
            #print out percentage
            if i%1000==0:
                sys.stdout.write('\r')
                sys.stdout.write("%d%%" %(100*(i+1)/full.nrtimesteps))
                sys.stdout.flush()
        sub.writeFort019_parallel(full)            
    sys.stdout.write('\r')
    sys.stdout.write("100%")
    sys.stdout.flush()

    sub.fort019.close()
    
    print "\n\nADCIRC boundary conditions for the subdomain at",sub.dir,"are now ready.\n"
    if full.isCoupledAdcircSwan():
        print '\033[91m'+"\nImportant Note:"+'\033[0m'
        print "After preprocessing the subdomain using adcprep, run genbcs4swan.py script"
        print "to generate SWAN b.c. files."

  
def usage():
    scriptName = os.path.basename(__file__)
    print ""
    print "Usage:"
    print '\t', scriptName, "fullDomainDir subDomainDir [sbtiminc]\n"


if __name__== "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1],sys.argv[2],None)
    elif len(sys.argv) == 4:
        main(sys.argv[1],sys.argv[2],sys.argv[3])
    else:
        usage()

