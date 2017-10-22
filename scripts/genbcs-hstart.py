# CSM: Python Module for the Conventional Subdomain Modeling Approach
#   Copyright (C) 2017
#   Computational Modeling Group, NCSU <http://www4.ncsu.edu/~jwb/>
#   Alper Altuntas <alperaltuntas@gmail.com>

import os
import sys
import readline, glob
from csm import Domain

# genbcs-hstart.py:
# Generates boundary conditions file for a subdomain to be hotstarted by
#   reading data from (1) a cold-started and (2) a hot-started full domain.

# Prepares a full domain before reading fort.065s and writing fort.019
def prepFull(full):

    # Get the runtype
    full.runtype="s"
    isSerialRun = os.path.exists(full.dir+"fort.065")
    isParallelRun = os.path.exists(full.dir+"PE0000/fort.065")

    if isSerialRun and (not isParallelRun):
        full.runtype="s"
    elif isParallelRun and (not isSerialRun):
        full.runtype="p"
    else:
        while True:
            full.runtype = raw_input('Enter the type of the full domain run at '+ \
                                full.dir + " " \
                                '("p" for parallel, or "s" for serial):\n')
            if full.runtype=='p' or full.runtype=='s':
                break
            elif full.runtype=='"p"':
                full.runtype = 'p'
                break
            elif full.runtype=='"s"':
                full.runtype = 's'
                break
            else:
                print '\033[91m'+"\nInvalid key!"+'\033[0m'

    # Read input files:
    full.readFort14()
    if full.runtype=="p": full.readFort80()

    # Open full domain fort.065
    if full.runtype=="s":
        full.openFort065()
    else:
        full.openFort065_parallel()


# Check if full domains are consistent
def checkFullDomains(fullCold, fullHot):

    if (not fullCold.np == fullHot.np):
        print "ERROR: inconsistent full domains!"
        exit()

    if (not fullCold.nspoolgs == fullHot.nspoolgs):
        print "ERROR: full domains' nspoolgs parameters are inconsistent"
        exit()


# Prepares a given full domain for an ADCIRC run.
# (Generates a fort.015 file and modifies fort.26 if it is a ADCIRC+SWAN run).
def main(fullColdDir, fullHotDir, subdir, sbtiminc):

    # Print header:
    print ""
    print '\033[95m'+'\033[1m'+"NCSU Subdomain Modeling for ADCIRC+SWAN"+'\033[0m'
    print ""
    print "Generating ADCIRC boundary conditions files for the subdomain at",subdir,"\n"

    # Instantiate and prepare the full domains:
    fullCold = Domain(fullColdDir)
    fullHot = Domain(fullHotDir)
    prepFull(fullCold)
    prepFull(fullHot)

    # Instantiate and prepare the subdomain:
    sub = Domain(subdir)
    sub.readFort14()
    sub.readPy140()

    # Check whether full domains are inconsistent
    checkFullDomains(fullCold, fullHot)

    # Convert sbtiminc to integer
    if sbtiminc==None:
        sbtiminc = fullCold.nspoolgs
    else:
        sbtiminc = int(sbtiminc)

    # Check if sbtiminc is a multiple of NSPOOLGS:
    if not (sbtiminc%fullCold.nspoolgs == 0):
        print '\033[91m'+"\nWARNING!"+'\033[0m'
        print "The parameter sbtiminc (="+str(sbtiminc)+") is not a multiple of "+\
              "the full domain parameter nspoolgs (="+str(fullCold.nspoolgs)+")"
        print "Setting sbtiminc to",fullCold.nspoolgs
        sbtiminc = fullCold.nspoolgs

    print "\n\t Writing fort.019 at",sub.dir,"\n"

    # Open subdomain b.c. file:
    sub.openFort019(sbtiminc,(fullCold.nrtimesteps+fullHot.nrtimesteps) )

    # First, write the boundary conditions from the cold started full domain:
    print "\n\tWriting boundary conditions from cold-started full domain...\n"
    if fullCold.runtype=="s":
        for i in range(fullCold.nrtimesteps):
            fullCold.readFort065()
            sub.writeFort019(fullCold)
            #print out percentage
            if i%1000==0:
                sys.stdout.write('\r')
                sys.stdout.write("%d%%" %(100*(i+1)/fullCold.nrtimesteps))
                sys.stdout.flush()
    else:
        for i in range(fullCold.nrtimesteps):
            fullCold.readFort065_parallel()
            if i==0: sub.createProcMapping(fullCold)
            sub.writeFort019_parallel(fullCold)
            #print out percentage
            if i%1000==0:
                sys.stdout.write('\r')
                sys.stdout.write("%d%%" %(100*(i+1)/fullCold.nrtimesteps))
                sys.stdout.flush()
    sys.stdout.write('\r')
    sys.stdout.write("100%")
    sys.stdout.flush()

    print "\n\tWriting boundary conditions from hot-started full domain...\n"
    if fullHot.runtype=="s":
        for i in range(fullHot.nrtimesteps):
            fullHot.readFort065()
            sub.writeFort019(fullHot)
            #print out percentage
            if i%1000==0:
                sys.stdout.write('\r')
                sys.stdout.write("%d%%" %(100*(i+1)/fullHot.nrtimesteps))
                sys.stdout.flush()
        sub.writeFort019(fullHot)
    else:
        for i in range(fullHot.nrtimesteps):
            fullHot.readFort065_parallel()
            if i==0: sub.createProcMapping(fullHot)
            sub.writeFort019_parallel(fullHot)
            #print out percentage
            if i%1000==0:
                sys.stdout.write('\r')
                sys.stdout.write("%d%%" %(100*(i+1)/fullHot.nrtimesteps))
                sys.stdout.flush()
        sub.writeFort019_parallel(fullHot)

    sys.stdout.write('\r')
    sys.stdout.write("100%")
    sys.stdout.flush()

    sub.fort019.close()

    print "\n\nADCIRC boundary conditions for the subdomain at",sub.dir,"are now ready.\n"
    if fullCold.isCoupledAdcircSwan():
        print '\033[91m'+"\nImportant Note:"+'\033[0m'
        print "After preprocessing the subdomain using adcprep, run genbcs4swan.py script"
        print "to generate SWAN b.c. files."


def usage():
    scriptName = os.path.basename(__file__)
    print ""
    print "Usage:"
    print '\t', scriptName, "fullDomainCold fullDomainHot subDomainDir [sbtiminc]\n"


if __name__== "__main__":
    if len(sys.argv) == 4:
        main(sys.argv[1],sys.argv[2],sys.argv[3],None)
    elif len(sys.argv) == 5:
        main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
    else:
        usage()

