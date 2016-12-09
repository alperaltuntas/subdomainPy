# CSM: Python Module for the Conventional Subdomain Modeling Approach
#   Copyright (C) 2017 
#   Computational Modeling Group, NCSU <http://www4.ncsu.edu/~jwb/>
#   Alper Altuntas <alperaltuntas@gmail.com>

import os
import sys
import readline, glob
import datetime
from csm import Domain,SpecFile

# genbcs.py: 
# Generates SWAN boundary conditions files and fort.26 files for a CSM subdomain

# Writes fort.26 files for each METIS partition:
def writePartFort26(sub):

    sub.partitions = []

    # Loop over all of the METIS partitions:
    for proc in range(sub.nprocs):

        # Instantiate the partition as a domain:
        partitionDir = sub.dir+"PE"+"0"*(4-len(str(proc)))+str(proc)+"/"
        sub.partitions.append(Domain(partitionDir))
        partition = sub.partitions[-1]

        # Read the partitioned grid file:
        partition.readFort14()
        sys.stdout.write("\033[F")  # erase the printed log for PE*/fort.14 file 

        # Rename and open the old fort26 file:
        if (not os.path.isfile(partition.dir+"fort.26")):
            print "Error: Couldn't locate ", partition.dir+"fort.26"
            exit()
        os.rename(partition.dir+"fort.26",partition.dir+"oldfort.26")
        old26 = partition.openInputFile("oldfort.26")

        # Write the new fort.26 file:
        new26 = open(partition.dir+"fort.26",'w')
        within_block_c = False # true if the line is within Block (c) of fort.26 file, 
                               # i.e., the line corresponds to a command for input fields
        for line in old26:

            # do not rewrite the boundary lines from the old file:
            if line[0:5]=="BOUND" or line[:-1]=="$ Subdomain Boundary Conditions:":
                continue

            # determine if the current line is within block (c)
            elif (not within_block_c) and (line[0:7]).lower()=="inpgrid":
               within_block_c = True

            # determine if the current line is below block (c), and if so,
            # write the list of boundary conditions file right after block (c)
            elif within_block_c and \
                    (not line[0]=="$") and \
                    (not (line[0:7]).lower()=="inpgrid") and \
                    (not (line[0:7]).lower()=="readinp") and \
                    (not (line[0:4]).lower()=="wind") :
                within_block_c = False

                # Write the list of boundary conditions files to the partitioned fort.26:
                if not len(partition.nbdv)==0:
                    new26.write("$ Subdomain Boundary Conditions:\n")
                    new26.write("BOUND SHAPESPEC JON GAMMA=3.3 PEAK DSPR DEGREES \n")

                printed_bnodes = []
                for bnode in partition.nbdv:

                    # avoid duplicate boundary nodes in fort.26:
                    if bnode in printed_bnodes:
                        continue
                    printed_bnodes.append(bnode)

                    # list the boundary node in fort.26
                    new26.write( "BOUNDSPEC SEGMENT IJ %s VARIABLE FILE LEN=0 '%s' SEQ=1 \n"
                                %(str(bnode), partition.dir+"bc"+str(bnode)+".019") )

                new26.write("$ \n")

            # Write the original line from the old fort.26 file: 
            new26.write(line)

        old26.close()
        new26.close()

# Returns the number of SWAN timesteps:
def getSWANtimesteps(fort26dir):

    fort26 = None
    try:
        fort26 = open(fort26dir)
    except:
        print "ERROR: Cannot open fort.26 file at",fort26dir,"to retrieve the number of timesteps."
        exit()

    nTimesteps = 0
    readTime = False
    for line in fort26:
        if line.split()[0][0:4].lower() == "comp":

            startDateTime   = line.split()[1]
            startYr     = int(startDateTime[0:4])
            startMth    = int(startDateTime[4:6])
            startDay    = int(startDateTime[6:8])
            startHr     = int(startDateTime[9:11])
            startMin    = int(startDateTime[11:13])
            startSec    = int(startDateTime[13:15])
    
            endDateTime = line.split()[4]
            endYr     = int(endDateTime[0:4])
            endMth    = int(endDateTime[4:6])
            endDay    = int(endDateTime[6:8])
            endHr     = int(endDateTime[9:11])
            endMin    = int(endDateTime[11:13])
            endSec    = int(endDateTime[13:15])
    
            unit = line.split()[3]

            dtSec = 0
            if unit[0].lower()=="s":
                 dtSec = int(line.split()[2])
            elif unit[0].lower()=="m":
                 dtSec = int(line.split()[2])*60
            elif unit[0].lower()=="h":
                 dtSec = int(line.split()[2])*60*60
            elif unit[0].lower()=="d":
                 dtSec = int(line.split()[2])*60*60*24
            else:
                print "ERROR: invalid deltc in ", fort26dir
                exit() 
                    
            start = datetime.datetime(startYr,startMth,startDay,startHr,startMin,startSec)
            end = datetime.datetime(endYr,endMth,endDay,endHr,endMin,endSec)
            
            duration = end-start

            nTimesteps = (duration.days*24*60*60 + duration.seconds)/dtSec +1
           
            readTime = True
            break

    if not readTime:
        print "ERROR: Couldn't retrieve time information from ", fort26dir 
        exit()

    fort26.close()
    return nTimesteps

# Write the b.c. files to each METIS partition directory:
def writeBCfiles(full,sub):

    nTimesteps = getSWANtimesteps(full.dir+'fort.26')

    # Get rid of duplicates in partition boundary lists:
    for proc in range(sub.nprocs):
        partition = sub.partitions[proc]
        partition.nbdv = list(set(partition.nbdv))
 

    # Open all subdomain b.c. files:
    bcFiles = [None]*sub.nprocs
    fullNodes = dict()
    fullProcs = set()
    for proc in range(sub.nprocs):
        partition = sub.partitions[proc]
        bcFiles[proc] = dict()

        for bnode in partition.nbdv:
   
            subNode = sub.nodesP2G[proc][bnode] # bnode number in subdomain grid
            fullNode = sub.n2o[subNode]         # bnode number in full domain grid
            fullProc = full.innerNodes[fullNode][0]
            
            bcFiles[proc][bnode] = open(partition.dir+"bc"+str(bnode)+".019",'w')
            fullProcs.add(fullProc)

            if proc in fullNodes:
                fullNodes[proc].add(fullNode)
            else:   
                fullNodes[proc] = set([fullNode])


    # Read the list of spectral output locations from full fort.015
    fullfort015 = open(full.dir+"fort.015")
    line = None
    for i in range(4):
        line = fullfort015.readline()
        
    if int(line.split()[0])==0:
        # Old format. Read two more lines:
        for i in range(2):
            line = fullfort015.readline()           

    ncbnr = int(line.split()[0])
    specLocs = []
    for i in range(ncbnr):
        specLocs.append(int(fullfort015.readline().split()[0]))
    fullfort015.close()
    
    # Read spec file headers:
    specFiles = dict()
    for proc in fullProcs:
        partitionDir = full.dir+"PE"+"0"*(4-len(str(proc)))+str(proc)+"/"
        specFiles[proc] = SpecFile(open(partitionDir+"spec2d.63"))
        specFiles[proc].readHeaders()
        
    # Write header lines:
    for proc in range(sub.nprocs):
        partition = sub.partitions[proc]
        for bnode in partition.nbdv:
            bcfile = bcFiles[proc][bnode]
            subNode = sub.nodesP2G[proc][bnode] # bnode number in subdomain grid
            fullNode = sub.n2o[subNode]         # bnode number in full domain grid
            fullProc = full.innerNodes[fullNode][0]

            # first 6 lines
            for i in range(6):
                bcfile.write(specFiles[fullProc].headerLines[i])
            
            # number of locations:
            bcfile.write("1\n")
            # coordinates of the bc node:
            bcfile.write("  "+str(sub.nodes[subNode][0])[:10] + \
                         "  "+str(sub.nodes[subNode][1])[:10] + "\n")
            
            # rest of the header lines:
            for i in range(6,len(specFiles[fullProc].headerLines)):
                bcfile.write(specFiles[fullProc].headerLines[i])
   
 
    print ""       
    # Read and write the timesteps:
    for ts in range(nTimesteps):
        print "Processing timestep",ts,"of",(nTimesteps-1)
        sys.stdout.write("\033[F")  # erase the printed log for PE*/fort.14 file 

        # Read from full domain spectra files for the new timestep:
        for proc in fullProcs:
            sfile = specFiles[proc]
            sfile.lines = dict()
            sfile.datetime = sfile.fileObj.readline()
            for specLoc in specLocs:
                sfile.lines[specLoc] = []  
            
                sfile.lines[specLoc].append(sfile.fileObj.readline())
                if sfile.lines[specLoc][0].split()[0].lower()=="factor":
                    for i in range(sfile.nfreq+1):
                        sfile.lines[specLoc].append(sfile.fileObj.readline())

        # Write to boundary conditions files:
        for proc in range(sub.nprocs):
            partition = sub.partitions[proc]
            for bnode in partition.nbdv:
                bcfile = bcFiles[proc][bnode]
                subNode = sub.nodesP2G[proc][bnode] # bnode number in subdomain grid
                fullNode = sub.n2o[subNode]         # bnode number in full domain grid
                fullProc = full.innerNodes[fullNode][0]
                sfile = specFiles[fullProc]

                # write date and time:
                bcfile.write(sfile.datetime)
                
                # write spectra:
                for line in sfile.lines[fullNode]:
                    bcfile.write(line)
    
    # Close the boundary conditions files:
    print ""       
    for proc in fullProcs:
        specFiles[proc].close()
    for proc in range(sub.nprocs):
        partition = sub.partitions[proc]
        for bnode in partition.nbdv:
            bcfile = bcFiles[proc][bnode]
            bcfile.close()

    print "\nSWAN boundary conditions are now ready.\n"


def main(fulldir, subdir):

    print ""
    print '\033[95m'+'\033[1m'+"NCSU Subdomain Modeling for ADCIRC+SWAN"+'\033[0m'
    print ""
    print "Generating SWAN boundary conditions files for the subdomain at",subdir

    # Instantiate the subdomain object:
    full = Domain(fulldir)
    sub = Domain(subdir)

    # check if subdomain is partitioned: 
    if not sub.isPartitioned():
        print '\033[91m'+"\nERROR:"+'\033[0m'
        print "Subdomain is not preprocessed!"
        print "Partition the subdomain using adcprep before executing this script."
        print "exiting...\n"
        exit()

    # Read the input files:
    full.readFort14()
    full.readFort80()
    sub.readFort14()
    sub.readFort80()
    sub.readPy140()

    # Check if no. of partitions is supported
    if (sub.nprocs>10000):
        print "ERROR: number of METIS partitions greater than 10,000"
        exit()

    # Write fort.26 files for the parallel subdomain run
    writePartFort26(sub)

    # write bc files for the subdomain run:
    writeBCfiles(full,sub)    

  
def usage():
    scriptName = os.path.basename(__file__)
    print ""
    print "Usage:"
    print ' ', scriptName, "fullDomainDir subDomainDir\n"


if __name__== "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1],sys.argv[2])
    else:
        usage()

