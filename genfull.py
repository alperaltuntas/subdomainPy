# CSM: Python Module for the Conventional Subdomain Modeling Approach
#   Copyright (C) 2017 
#   Computational Modeling Group, NCSU <http://www4.ncsu.edu/~jwb/>
#   Alper Altuntas <alperaltuntas@gmail.com>

import os
import sys
import readline, glob
from csm import Domain

# genfull.py: 
# Prepares a given full domain for an ADCIRC run to record subdomain boundary conditions.

# Auto-completion for directories:
def complete(text, state):
    return (glob.glob(text+'*')+[None])[state]
readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
readline.set_completer(complete)


# Prompts the user to enter the directories of the predetermined subdomains of the full
# domain, and returns the list of subdomains.
def getSubdomains():

    subdomains = []
    subDirs = []
    while True: 
        # Get the subdomain directory:
        subDir = raw_input('Enter the directory of a subdomain '+
                            '(Type "done" when finished):\n')

        # Check if the user is done:
        if subDir.lower() == "done" or subDir.lower() == '"done"':
            print "\nThe following subdomains are added: "
            for sub in subdomains:
                print " ", sub.dir
            break
        
        # Format the subdomain directory entered by the user:
        if len(subDir)==0:
            continue
        else:
            subDir = subDir.strip()
            if not subDir[-1]=='/': 
                subDir = subDir+'/'
        
        # Check if the subdomain is added before:    
        if subDir in subDirs:
            print "The subdomain at",subDir, "is already added!"
            continue

        # Check if the subdomain directory is valid:
        if not os.path.exists(subDir):
            print '\033[91m'+"\nWARNING:"+'\033[0m'
            print "Subdomain is NOT added! The directory "+subDir+" does not exist."
            continue
            
        # Read the input files:
        try:
            sub = Domain(subDir)
            sub.readFort14()
            sub.readPy140()        
            subdomains.append(sub)     
        except IOError:
            print "\nERROR: Couldn't read the input files (fort.14 and py.140 ) of"
            print "         the subdomain at", sub.dir
            print "Exiting..."
            exit()

        subDirs.append(subDir)

    # Check if any subdomain is added:
    if len(subdomains)==0:
        print "\nERROR: No subdomain has been added!\nExiting...\n"
        exit()

    return subdomains; 


# Generates the fort.015 (subdomain modeling control) file for the full domain:
def writeFort015(full, nspoolgs, subdomains):

    print "\t Writing fort.015 at",full.dir

    fort015 = open(full.dir+"fort.015",'w')

    # noutgs: (=1 for elevation specified subdomain boundaries)
    noutgs = str(1)

    # enforceBN: (=0 if full domain)
    enforceBN = str(0)  

    # Write the CSM control parameters to full domain fort.015:
    fort015.write( noutgs + "\t !NOUTGS\n")
    fort015.write( nspoolgs + "\t !NSPOOLGS\n")
    fort015.write( enforceBN + "\t !enforceBN\n")

    if subdomains:
        # Determine the full domain nodes corresponding to the boundary nodes 
        # of added subdomains:
        full.fbnodes = []
        for sub in subdomains:
            for bnode in sub.nbdv:
                fbnode = sub.n2o[bnode]
                if not fbnode in full.fbnodes:
                    full.fbnodes.append(fbnode) 

        fort015.write( str(len(full.fbnodes)) +'\t !ncbnr\n')
        for fbnode in full.fbnodes:
            fort015.write(str(fbnode)+'\n')
    else:
        fort015.write( str(full.np) +'\t !ncbnr\n')
        for n in range(full.np):
            fort015.write( str(n+1)+'\n')
    
    fort015.close()


# Writes SWAN b.c. recording stations list in a file. The file is read by SWAN to record 
# the 2d spectra information at these locations corresponding to subdomain boundaries.
def writeSwanStationsFile(full,subdomains):

    print "\t Writing swan b.c. stations file at", full.dir

    swanStationFile = open(full.dir+"swanStations.txt",'w')
    
    if subdomains:
        for fbnode in full.fbnodes: # Note: full.fbnodes is initialized in writeFort015()
            x = full.nodes[fbnode][0]
            y = full.nodes[fbnode][1]
            swanStationFile.write(str(x)+"\t "+str(y)+"\n")
    else:
        # Record all full domain nodes:
        for n in range(1,full.np+1):
            x = full.nodes[n][0] 
            y = full.nodes[n][1] 
            swanStationFile.write(str(x)+"\t "+str(y)+"\n")
    
    swanStationFile.close()

# Modifies the fort.26 file of the full domain
def modifyFort26(full,subdomains):

    # Rename and open the old fort26 file:
    if (not os.path.isfile(full.dir+"fort.26")):
        print "ERROR: Couldn't locate ", full.dir+"fort.26"
        exit() 
    os.rename(full.dir+"fort.26",full.dir+"oldfort.26")
    old26 = full.openInputFile("oldfort.26")

    # Write the new fort.26 file:
    new26 = open(full.dir+"fort.26",'w')
    passed_block_g = False # True if the line is after Block (g) of fort.26 file,
                           # The additional line for the output locations must be added
                           # in Block (g)
    tbeg = None # the start date
    delt = None # the duration of a timestep
    unit = None # unit of delt

    for line in old26:

        # Avoid duplicate lines if the scipt is run multiple times without preprocessing:
        if line[0:30]=="$ Read the list of Subdomain B" or \
           line[0:30]=="POINTS 'P1' FILE 'swanStations" or \
           line[0:30]=="$ Record SWAN output for Subdo" or \
           line[0:30]=="SPEC 'P1' SPEC2D ABS 'spec2d.6":
            continue
    
        if (not passed_block_g):
            lineSplit = line.split()
               
            # Retrieve tbeg, delt, and unit 
            if lineSplit[0][0:3].lower()=="inp" and lineSplit[1][0:2].lower()=="wi": 
                tbeg = lineSplit[6]
                delt = lineSplit[7]
                unit = lineSplit[8]
           
            # add the lines to record the SWAN boundary conditions for subdomains 
            if (lineSplit[0][0:3].lower()=="qua" or \
                lineSplit[0][0:4].lower()=="outp" or \
                lineSplit[0][0:3].lower()=="blo" or \
                lineSplit[0][0:3].lower()=="tab" or \
                lineSplit[0][0:4].lower()=="spec" or \
                lineSplit[0][0:4].lower()=="nest" or \
                lineSplit[0][0:4].lower()=="comp"):

                # Check if tbeg, delt, and unit are retrived yet:
                if not (tbeg and delt and unit):
                    print "ERROR: Couldn't retrieve tbeg, delt, and unit from fort.26" 
                    print "Exiting"
                    exit()

                new26.write("$ Read the list of Subdomain Boundary Nodes: \n")
                new26.write("POINTS 'P1' FILE 'swanStations.txt' \n")
                new26.write("$\n")
                new26.write("$ Record SWAN output for Subdomain Boundary Conditions: \n")
                new26.write( "SPEC 'P1' SPEC2D ABS 'spec2d.63' OUTPUT "+\
                                tbeg+" "+delt+" "+unit+"\n$\n")

                passed_block_g = True

        # Write the line from the old fort.26 
        new26.write(line) 

    old26.close()
    new26.close()

# Prepares a given full domain for an ADCIRC run. 
# (Generates a fort.015 file and modifies fort.26 if it is a ADCIRC+SWAN run).
def main(fulldir):

    print ""
    print '\033[95m'+'\033[1m'+"NCSU Subdomain Modeling for ADCIRC+SWAN"+'\033[0m'
    print ""
    print "Preparing the full domain at", fulldir,"for an ADCIRC run.\n"
  
    full = Domain(fulldir)
    
    # Remove the existing fort.015:
    if os.path.exists(full.dir+"fort.015"):
        os.remove(full.dir+"fort.015")

    # Determine the list of nodes to be recorded for subdomain boundary conditions:
    subdomains = [] 
    predetermine = None
    while True:
        predetermine = raw_input("Specify predefined subdomains? (y or n). [Default: y] \n")
        if predetermine.lower()=='y' or predetermine.lower()=='n':
            break
        elif len(predetermine)==0:
            predetermine = 'y'
            break
        else:
            print "Invalid key:",predetermine,"\n"
      
    if predetermine=='y':
        # Get the list of predetermined subdomains from CLI:
        subdomains = getSubdomains()
    else:
        # Record all of the full domain nodes:
        print '\033[91m'+"\nWARNING:"+'\033[0m'
        print "If no predefined subdomain is provided, full domain ADCIRC run will"
        print "record ALL nodes to provide boundary conditions for any future subdomain."
        print "This will require substantial amount of resources."

        while True:
            cont = raw_input("\nContinue? (y or n):\n")
            if len(cont)>0 and cont.lower()=='y':
                break
            elif len(cont)>0 and cont.lower()=='n':
                print "Exiting..."
                exit()
            else:
                print "Invalid key:",cont,"\n"

    # nspoolgs: the number of timesteps at which subdomain boundary conditions are to be recorded:
    nspoolgs = raw_input("\nEnter NSPOOLGS (no. of timesteps at which b.c. are to be recorded)."
                         " [Default=100]:\n")
    try:
        nspoolgs = str(int(nspoolgs))
    except:
        nspoolgs = str(100)
        print "NSPOOLGS is set to 100.\n"

    # Read full fort.14
    full.readFort14()

    # Generate a new fort.015 file
    writeFort015(full,nspoolgs,subdomains)

    # If an ADCIRC+SWAN run, make additional adjustments:
    if full.isCoupledAdcircSwan():

        # Write SWAN b.c. recording stations list file
        writeSwanStationsFile(full,subdomains)
            
        # Modify fort26 (SWAN control file):
        modifyFort26(full,subdomains)

    # The final log message:
    print "\nThe full domain is now ready."

    # Check if the full domain is coupled and preprocessed:
    if full.isCoupledAdcircSwan() and full.isPartitioned():
        print '\033[91m'+"\nImportant Note:"+'\033[0m'
        print "The full domain is previously preprocessed. Re-run adcprep to make sure "+\
              "that partitioned fort.26 files are up-to-date.\n"

    # Check if fort.15 has subdomainModeling namespace:
    full15 = open(full.dir+"fort.15")
    subNamespace = False
    for line in full15:
        if line.split()[0].lower() == "&subdomainmodeling":
            subNamespace = True
            break
    full15.close()
    if not subNamespace:
        print '\033[91m'+"WARNING:"+'\033[0m'
        print "Full domain fort.15 file does not include subdomainModeling namespace."
        print "Add the following line to the end of fort.15 file to activate subdomain modeling:"
        print "&subdomainModeling subdomainOn=T /"
        print ""

def usage():
    scriptName = os.path.basename(__file__)
    print ""
    print "Usage:"
    print " ", scriptName, "fulldomainDir\n"


if __name__== "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        usage()

