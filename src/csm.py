# CSM: Python Module for the Conventional Subdomain Modeling Approach
#   Copyright (C) 2017 
#   Computational Modeling Group, NCSU <http://www4.ncsu.edu/~jwb/>
#   Alper Altuntas <alperaltuntas@gmail.com>

import os
import math
import numpy 

# csm.Domain:

# The Domain class encapsulates the properties and input/output files of an 
# an ADCIRC domain (either full or sub) at a give directory (domainDir). 
# The class includes member functions to read and write input and output files 
# for the pre- and post-processing of a (full or sub) domain

class Domain(object,):

    def __init__(self,domainDir):
        # Format domain directory:
        domainDir = domainDir.strip()
        if (not domainDir[-1] == '/'):
            domainDir = domainDir+'/'
        self.dir = domainDir

    # Returns True if the domain is partitioned (i.e., belongs to a parallel run)
    def isPartitioned(self):
        if os.path.exists(self.dir+'fort.80') and os.path.exists(self.dir+'PE0000'):
            return True
        return False

    # Returns True if the domain is for a coupled ADCIRC+SWAN run
    def isCoupledAdcircSwan(self):
        if os.path.exists(self.dir+"fort.26") or os.path.exists(self.dir+"swaninit"):
            return True
        return False
    
    # Opens and returns an input file with a given name at self.dir
    def openInputFile(self,fileName):
        try:
            fileObj = open(self.dir+fileName)
            return fileObj
        except:
            print "Error: Cannot open ", fileName, " at ", self.dir
            exit()        


    # Reads the Grid Information (fort.14) file of the domain
    def readFort14(self):
        print "\t Reading fort.14 at", self.dir
        fort14 = self.openInputFile("fort.14")

        # Read the header:
        self.f14header = fort14.readline()
        
        # Number of nodes and elements: (fort.14 parameters)
        line = fort14.readline()
        self.ne = int(line.split()[0])
        self.np = int(line.split()[1])

        # Initialize the list of nodes and elements
        self.nodes = [None]*(self.np+1)
        self.elements = [None]*(self.ne+1)
       
        # Read the list of nodes 
        for n in range(self.np):
            sline = fort14.readline().split()
            node = int(sline[0])
            xc = float(sline[1])
            yc = float(sline[2])
            d = float(sline[3])
            self.nodes[node] = [xc,yc,d]

        # Read the list of elements 
        for e in range(self.ne):
            sline = fort14.readline().split()
            ele = int(sline[0])
            n1 = int(sline[2])
            n2 = int(sline[3])
            n3 = int(sline[4])
            self.elements[ele] = [n1,n2,n3]
    
        # Read boundary information

        line = fort14.readline()
        self.nope = int(line.split()[0])    # no of elev boundary forcing segments
        line = fort14.readline()        
        self.neta = int(line.split()[0])    # total number of elev boundary nodes
        self.nbdv = []                      # elevation specified boundary node numbers

        for k in range(self.nope):
            line = fort14.readline()
            nvdll = int(line.split()[0])    # no. of nodes in elevation boundary segment k.
            for j in range(nvdll):
                line = fort14.readline()
                self.nbdv.append(int(line.split()[0]))

        line = fort14.readline()
        self.nbou = int(line.split()[0])    # no. of normal flow (discharge) specified bdry segments
        line = fort14.readline()        
        self.nvel = int(line.split()[0])    # total no. of normal flow specified bdry nodes 
        self.nbvv = []                      # node numbers on normal flow boundary segment k. 

        for k in range(self.nbou):
            line = fort14.readline()
            nvell = int(line.split()[0])    # no. of nodes in normal flow specified bdry segment k.
            for j in range(nvell):
                line = fort14.readline()
                self.nbvv.append(int(line.split()[0]))
            
        fort14.close()


    # Reads the parallelism file (fort.80)
    def readFort80(self):
        print "\t Reading fort.80 at", self.dir

        # Open fort.80 file:
        fort80 = self.openInputFile("fort.80")
        
        # Skip the initial lines:
        for i in range(14):
            sline = fort80.readline().split()
            if sline[-1] == "NWLAT":
                break
            elif i==3:
                self.ne = int(sline[0])
                self.np = int(sline[1])
            elif i==4:
                # Read the number of processors 
                self.nprocs = int(sline[0])
                
        #create mapping array between proc and global node numbering:
        self.nodesP2G = [None]*self.nprocs      #initialize 2D mapping array
        self.pnnodes=[None]*self.nprocs # number of nodes for each processor   

        self.allNodes = dict() 
        for proc in range(self.nprocs):
            line = fort80.readline()
            proc = int(line.split()[0])
    
            self.pnnodes[proc] = int(line.split()[1])
            self.nodesP2G[proc] = [None]*(self.pnnodes[proc] + 1)
    
            lines = int(math.ceil(float(self.pnnodes[proc])/9))
            for l in range(lines):
                line = fort80.readline()
                try:
                    for i in range(9):
                        pn =  l*9+(i+1)
                        gn = int(line.split()[i])
                        self.nodesP2G[proc][pn] = gn
                        self.allNodes[gn,proc] = pn 
                except:
                    continue
                    #print "node mapping ok",proc

        self.innerNodes = [None]*(self.np+1) #inner nodes in a processor
        line = fort80.readline()

        for i in range(self.np):
            line = fort80.readline()
            gn = int(line.split()[0])
            proc = int(line.split()[1])
            pn = int(line.split()[2])
            self.innerNodes[gn] = [proc,pn]
        
        #print "Done reading fort.80"


    # Reads the nodal mapping file of a subdomain        
    def readPy140(self):
        print "\t Reading py.140 at ", self.dir
        py140 = self.openInputFile("py.140")
        py140.readline()
        self.n2o = [None]*(self.np+1)
        for line in py140:
            new = int(line.split()[0])
            old = int(line.split()[1])
            self.n2o[new] = old

    def openFort065(self):
        if not os.path.exists(self.dir+'fort.065'):     
            print "ERROR: Couldn't find fort.065 at", self.dir
            exit()
        self.fort065 = open(self.dir+"fort.065")
        line = self.fort065.readline()
        line = self.fort065.readline()
        self.nspoolgs = int( line.split()[0] )
        self.ncbnr = int( line.split()[1] )
        self.nrtimesteps = int( line.split()[2] )
        self.cbnr = [None]*self.ncbnr
        self.ec = [None]*self.ncbnr
        self.uc = [None]*self.ncbnr
        self.vc = [None]*self.ncbnr
        self.wdc = [None]*self.ncbnr


    def openFort065_parallel(self):
        self.fort065 = [None]*self.nprocs
        self.ncbnr = [None]*self.nprocs
        self.cbnr = [None]*self.nprocs
        self.ec = [None]*self.nprocs
        self.uc = [None]*self.nprocs
        self.vc = [None]*self.nprocs
        self.wdc = [None]*self.nprocs

        for proc in range(self.nprocs):
            l = len(str(proc)) # number of digits of proc no.
            p065 = self.dir+'PE'+'0'*(4-l)+str(proc)+'/fort.065'
            if not os.path.exists(p065):
                print "ERROR: Couldn't find fort.065 at ",self.dir+p065
                exit()
            self.fort065[proc] = open(p065)
            line = self.fort065[proc].readline()
            line = self.fort065[proc].readline()
            self.nspoolgs = int( line.split()[0] )
            self.ncbnr[proc] = int( line.split()[1] )
            self.nrtimesteps = int( line.split()[2] )
            self.cbnr[proc] = [None]*self.ncbnr[proc]
            self.ec[proc] = [None]*self.ncbnr[proc]
            self.uc[proc] = [None]*self.ncbnr[proc]
            self.vc[proc] = [None]*self.ncbnr[proc]
            self.wdc[proc] = [None]*self.ncbnr[proc]


    def readFort065(self):
        self.tsline = self.fort065.readline()
        for i in range(self.ncbnr):
            line = self.fort065.readline()
            self.cbnr[i] = int(line.split()[0])
            self.ec[i] = float(line.split()[1])
            self.uc[i] = float(line.split()[2])
            line = self.fort065.readline()
            self.vc[i] = float(line.split()[0])
            self.wdc[i] = int(line.split()[1])

    def readFort065_parallel(self):
        for proc in range(self.nprocs):
            self.tsline = self.fort065[proc].readline()
            for i in range(self.ncbnr[proc]):
                line = self.fort065[proc].readline()
                self.cbnr[proc][i] = int(line.split()[0])
                self.ec[proc][i] = float(line.split()[1])
                self.uc[proc][i] = float(line.split()[2])
                line = self.fort065[proc].readline()
                self.vc[proc][i] = float(line.split()[0])
                self.wdc[proc][i] = int(line.split()[1])


    def openFort019(self,sbtiminc,nrtimesteps):
        self.fort019 = open(self.dir+'fort.019','w')
        self.fort019.write("Boundary conditions for subdomain\n")
        #self.fort019.write(str(sbtiminc)+'\t'+str(self.ncbn)+'\t'+str(nrtimesteps)+'\n')
        self.fort019.write(str(sbtiminc)+'\t'+str(self.neta)+'\t'+str(nrtimesteps)+'\n')
        for cb in self.nbdv:
            self.fort019.write(' '+str(cb)+'\n')


    def writeFort019(self,f):
        self.fort019.write(f.tsline)
        #for cb in self.cbn:
        for cb in self.nbdv:
            gn = self.n2o[cb]           
            i = f.cbnr.index(gn)
            self.fort019.write(str(cb)+'\t'+str(f.ec[i])+'\t'+str(f.uc[i])+'\n')
            self.fort019.write(str(f.vc[i])+'\t'+str(f.wdc[i])+'\n')


    def writeFort019_parallel(self,f):
        self.fort019.write(f.tsline)
        #for cb in self.cbn:
        for cb in self.nbdv:
            gn = self.n2o[cb]
            proc = self.cbIndex[cb][0]  
            i = self.cbIndex[cb][1] 
            self.fort019.write(str(cb)+'\t'+str(f.ec[proc][i])+'\t'+str(f.uc[proc][i])+'\n')
            self.fort019.write(str(f.vc[proc][i])+'\t'+str(f.wdc[proc][i])+'\n')

    def createProcMapping(self,f):
        self.cbIndex = [None]*(self.np+1)
        for cb in self.nbdv:
            gn = self.n2o[cb]
            for proc in range(f.nprocs):
                i=0
                for node in f.cbnr[proc]:
                    if gn == node:
                        self.cbIndex[cb] = [proc,i]
                    i=i+1
        


# Encapsulates the parameters in a shape file 
class SubShape:
    def __init__(self,subDir):

        # Format the subdomain directory
        subDir = subDir.strip()
        if (not subDir[-1] == '/'):
            subDir = subDir+'/'
        self.path = subDir
        self.typ = None
        self.file = None
        self.readFile()

    def readFile(self):

        # Determine the directory of the file:
        if os.path.exists(self.path+"shape.14"):
            self.file = open(self.path+"shape.14")
        elif os.path.exists(self.path+"shape.c14"):
            self.file = open(self.path+"shape.c14")
            self.typ = 'c'
        elif os.path.exists(self.path+"shape.e14"):
            self.file = open(self.path+"shape.e14")
            self.typ = 'e'

        # Check if a shape file is found
        if not self.file:
            print "\nERROR: Couldn't find a shape file at subdomain directory:", self.path
            print "       (Valid shape file names: shape.14, shape.c14, shape.e14)"
            exit()

        # Determine the type of the subdomain shape (circle or ellipse):
        if not self.typ:

            nlines = 0
            for line in self.file:
                nlines = nlines+1

            if nlines==2:
                self.typ = 'c'
            elif nlines==3:
                self.typ = 'e'
            else:
                print "\nERROR: Invalid number of lines in shape file at", self.path+"shape.14"
                exit()

        # A circular subdomain:
        if self.typ == 'c':
            line = self.file.readline()
            self.x = float(line.split()[0])
            self.y = float(line.split()[1])
            line = self.file.readline()
            self.r = float(line.split()[0])
        # An elliptical subdomain:
        if self.typ == 'e':
            line = self.file.readline()
            self.x1 = float(line.split()[0])
            self.y1 = float(line.split()[1])
            line = self.file.readline()
            self.x2 = float(line.split()[0])
            self.y2 = float(line.split()[1])
            line = self.file.readline()
            self.w = float(line.split()[0])
    
            self.c = [ (self.x1+self.x2)/2., (self.y1+self.y2)/2.] # center of the ellipse
            self.d = ( (self.x1-self.x2)**2 + (self.y1-self.y2)**2)**(0.5) # distance
            self.theta = math.atan( (self.y1-self.y2)/(self.x1-self.x2) ) # theta to positive x axis
            self.sin = math.sin(-self.theta)
            self.cos = math.cos(-self.theta)

            self.xaxis = ((0.5*self.d)**2 + (0.5*self.w)**2)**(0.5)
            self.yaxis = self.w/2.

# Encapsulates spec file data:
class SpecFile:
    def __init__(self,fileObj):
        self.fileObj = fileObj
        self.headerLines = []
        self.lines = []

    def close(self):
        self.fileObj.close()

    def readHeaders(self):
        for i in range(6):
            self.headerLines.append(self.fileObj.readline())

        # read the list of locations:
        line = self.fileObj.readline()
        nloc = int(line.split()[0])
        for i in range(nloc):
            self.fileObj.readline()

        # read the rest of lines until spectral data
        self.headerLines.append(self.fileObj.readline()) #afreq header
        self.headerLines.append(self.fileObj.readline()) #nfreq
        self.nfreq = int(self.headerLines[-1].split()[0])
        for i in range(self.nfreq):
            self.headerLines.append(self.fileObj.readline())
        self.headerLines.append(self.fileObj.readline()) #cdir header
        self.headerLines.append(self.fileObj.readline()) #ndir
        ndir = int(self.headerLines[-1].split()[0])
        for i in range(ndir):
            self.headerLines.append(self.fileObj.readline())
        for i in range(5):
            self.headerLines.append(self.fileObj.readline())


