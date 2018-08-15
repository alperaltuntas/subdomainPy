#CSM: Python Module for the Conventional Subdomain Modeling Approach
#   Copyright (C) 2017 
#   Computational Modeling Group, NCSU <http://www4.ncsu.edu/~jwb/>
#   Alper Altuntas <alperaltuntas@gmail.com>

import os
import sys
import numpy
from shutil import copyfile
from csm import Domain, SubShape

# gensub.py:
# Extracts a subdomain from a given full domain. Generates the following input
# files for the subdomain:
#   - fort.015  (required)
#   - fort.13   (optional)
#   - fort.14   (required)
#   - fort.26   (optional)

# Determines the nodes of a full domain that fall within a subdomain with 
# the given circular shape
def trimNodesCircle(full,sub,shape):

    candidateNodes = set()
    for n in range(1,len(full.nodes)):
        node = full.nodes[n]
        if ( (shape.x-node[0])**2 + (shape.y-node[1])**2 < (shape.r)**2):
             candidateNodes.add(n) #n:node id

    confirmedNodes = set()
    for e in range(1,len(full.elements)):
        ele = full.elements[e]
        nIncNodes = sum([1 if ele[i] in candidateNodes else 0 for i in range(3)])
        if nIncNodes == 3:
            confirmedNodes.add(ele[0])
            confirmedNodes.add(ele[1])
            confirmedNodes.add(ele[2])
    confirmedNodes = sorted(confirmedNodes)

    sub.nodes = [None]
    sub.subToFullNode = dict()
    sub.fullToSubNode = dict()
    for n in confirmedNodes:
        node = full.nodes[n]
        sub.subToFullNode[len(sub.nodes)] = n
        sub.fullToSubNode[n] = len(sub.nodes)
        sub.nodes.append(node)
    
# Determines the nodes of a full domain that fall within a subdomain with 
# the given elliptical shape
def trimNodesEllipse(full,sub,shape):

    candidateNodes = set()
    for n in range(1,len(full.nodes)):
        node = full.nodes[n]
        #transform Global Coordinates to local coordinates
        X = node[0] - shape.c[0] 
        Y = node[1] - shape.c[1] 
        x = shape.cos*X - shape.sin*Y
        y = shape.sin*X + shape.cos*Y
        if(x**2/shape.xaxis**2 + y**2/shape.yaxis**2 < 1):
            candidateNodes.add(n) #n:node id

    confirmedNodes = set()
    for e in range(1,len(full.elements)):
        ele = full.elements[e]
        nIncNodes = sum([1 if ele[i] in candidateNodes else 0 for i in range(3)])
        if nIncNodes == 3:
            confirmedNodes.add(ele[0])
            confirmedNodes.add(ele[1])
            confirmedNodes.add(ele[2])
    confirmedNodes = sorted(confirmedNodes)

    sub.nodes = [None]
    sub.subToFullNode = dict()
    sub.fullToSubNode = dict()
    for n in confirmedNodes:
        node = full.nodes[n]
        sub.subToFullNode[len(sub.nodes)] = n
        sub.fullToSubNode[n] = len(sub.nodes)
        sub.nodes.append(node)

# Determines the elements of a full domain that fall within a subdomain
def trimElements(full,sub):

    # Initialize subdomain properties:
    sub.elements = [None]
    sub.neta = 0            # total number of sub. boundary nodes

    sub.nbdvSet = set()     # incomplete set of sub. boundary nodes. this set will not include
                            # subdomain boundary nodes that are also full domain boundary nodes.
                            #  Those boundary nodes will be determined and added to sub.nbdv later on.
    
    # Mapping from subdomain node numbering to full domain node numbering
    sub.subToFullEle = dict()

    # Loop through full domain elements and determine the ones inside the subdomain.
    # Also, determine the list of subdomain boundary nodes
    for e in range(1,len(full.elements)):
        ele = full.elements[e]
        
        # incSubNode[i] is True if i.th node of element e is in the subdomain
        incSubNode = [False]*3
        nSubNodes = 0
        for i in range(3):
            incSubNode[i] = ele[i] in sub.fullToSubNode    
            nSubNodes = nSubNodes + incSubNode[i]

        if nSubNodes==3:
            # The element is inside the subdomain:
            sub.subToFullEle[len(sub.elements)] = e
            sub.elements.append([sub.fullToSubNode[ele[0]], \
                                 sub.fullToSubNode[ele[1]], \
                                 sub.fullToSubNode[ele[2]]])

        elif not nSubNodes==0:
            # The element is outside the subdomain, but adjacent to subdomain.
            # Determine the boundary nodes:
            for i in range(3):
                if incSubNode[i]: 
                    sub.nbdvSet.add(sub.fullToSubNode[ele[i]])

# Re-orders the list of boundary nodes of a subdomain
def orderBoundaryNodes(sub):

    # Determine the neighbors and elements of subdomain nodes:
    eles = [None]*(len(sub.nodes)+1)        # set of elements for each node
    neighbors = [None]*(len(sub.nodes)+1)   # set of neighbors for each node
    for i in range(1,len(sub.nodes)+1):
        eles[i] = set()
        neighbors[i] = set()
    for e in range(1,len(sub.elements)):
        for i in range(3):
            node = sub.elements[e][i]
            eles[node].add(e)
            neighbors[node].add(sub.elements[e][(i+1)%3])
            neighbors[node].add(sub.elements[e][(i+2)%3])

    # Initialize the list of ordered subdomain boundary nodes:
    sub.nbdv = []

    # True if a node is added to the reordered list of boundary nodes
    isAdded = [False]*(len(sub.nodes)+1)

    # Adds a given node to the ordered list of subdomain boundary nodes and 
    # removes it from the set of (unordered) subdomain boundary nodes 
    def addBoundaryNode(n):
        sub.nbdv.append(n)
        isAdded[n] = True
        try:
            sub.nbdvSet.remove(n)
        except:
            True # the node is probably also a full domain boundary node, so
                 # was not added to sub.nbdvSet

    # Go over the boundary:
    addBoundaryNode(min(sub.nbdvSet)) # begin with the boundary node with smallest id
    complete = False
    while (not complete):
        progressed = False
        for neig in neighbors[sub.nbdv[-1]]:
            if (not isAdded[neig]):
                nCommonEles = len(eles[sub.nbdv[-1]].intersection(eles[neig]))
                if nCommonEles==1:
                    addBoundaryNode(neig)
                    progressed = True
                    break
            else:
                nCommonEles = len(eles[sub.nbdv[-1]].intersection(eles[neig]))
                if nCommonEles==1 and neig == sub.nbdv[0] and len(sub.nbdv)>4:
                    # looped over the entire boundary
                    progressed = True
                    complete = True
                    break
        if not progressed: 
            raise SystemExit("ERROR: Encountered error while going over the boundary nodes.\n")

    if len(sub.nbdvSet)>0:
        raise SystemExit("\nERROR: Subdomain grid generation is unsuccesful. "
                         "It is likely that there are disconnected (multiple) segments "
                         "of the subdomain grid. Try increasing/reducing the size and/or altering the location "
                         "of the subdomain, so it covers an undivided portion of the fulldomain grid.")

    # Set the number of boundary nodes:
    sub.neta = len(sub.nbdv) 

# determine the island domains completely falling within the subdomain
def processInternalBoundaries(full,sub):

    sub.nbou = 0  # no. of normal flow (discharge) specified bdry segments
    sub.nvel = 0 # total no. of normal flow specified bdry nodes.
    sub.nbvv = [] # ibtype and node numbers on normal flow boundary segment k

    # internal ibtypes allowed within subdomains
    allowed_ibtypes = [ 1,11,21,  # islands
                        4,24,     # levees
                        5,25 ]    # levees with cross-barrier pipes

    for k in range(full.nbou): # loop over full domain normal flow (discharge) specified bdry segments
        ibtype = full.nbvv[k]['ibtype']
        if ibtype in allowed_ibtypes:
            withinSubdomain = True
            for bnode in full.nbvv[k]['bnodes']:
                if (bnode in sub.fullToSubNode and not (sub.fullToSubNode[bnode] in sub.nbdv ) ):
                    continue
                else:
                    withinSubdomain = False
                    break;
            if withinSubdomain:
                sub.nbou = sub.nbou +1
                sub.nbvv.append({'ibtype':ibtype,'bnodes':[]})
                if (ibtype in [4, 24,5,25]):
                    sub.nbvv[-1]['ibconn']=[]
                nvell = len(full.nbvv[k]['bnodes'])
                for j in range(nvell):
                    bnode = full.nbvv[k]['bnodes'][j]
                    sub.nvel = sub.nvel+1
                    sub.nbvv[-1]['bnodes'].append(sub.fullToSubNode[bnode])
                    if (ibtype in [4, 24,5,25]):
                        sub.nbvv[-1]['ibconn'].append(sub.fullToSubNode[full.nbvv[k]['ibconn'][j]])
                if (ibtype in [4, 24]):
                    sub.nbvv[-1]['barinht'] = full.nbvv[k]['barinht']
                    sub.nbvv[-1]['barincfsb'] = full.nbvv[k]['barincfsb']
                    sub.nbvv[-1]['barincfsp'] = full.nbvv[k]['barincfsp']
                if (ibtype in [5, 25]):
                    sub.nbvv[-1]['barinht']   = full.nbvv[k]['barinht']
                    sub.nbvv[-1]['barincfsb'] = full.nbvv[k]['barincfsb']
                    sub.nbvv[-1]['barincfsp'] = full.nbvv[k]['barincfsp']
                    sub.nbvv[-1]['pipeht']    = full.nbvv[k]['pipeht']
                    sub.nbvv[-1]['pipecoef']  = full.nbvv[k]['pipecoef']
                    sub.nbvv[-1]['pipediam']  = full.nbvv[k]['pipediam']

def writeFort14(full,sub):
    print "\t Writing fort.14 at",sub.dir
    
    header = full.f14header
    fort14 = open(sub.dir+"fort.14",'w')
   
    # Write header 
    fort14.write(header)
    fort14.write(str(len(sub.elements)-1) + " " + str(len(sub.nodes)-1)+"\n")
        
    # Write the list of nodes
    for n in range(1,len(sub.nodes)):
        node = sub.nodes[n]
        fort14.write("\t%d\t% 0.12f\t% 0.12f\t% 0.12f\n" \
                        %(n,node[0],node[1],node[2]))

    # Write the list of elements:
    for e in range(1,len(sub.elements)):
        ele = sub.elements[e]
        fort14.write(str(e) + "\t3\t" + str(ele[0]) +"\t"+ str(ele[1]) +"\t"+ str(ele[2]) +"\n")


    # Subdomain Boundaries:
    orderBoundaryNodes(sub)        
    fort14.write("1\t!no. of subdomain boundary segments\n")
    fort14.write(str(sub.neta+1) + "\t!no. of subdomain boundary nodes\n")
    fort14.write(str(sub.neta+1) + "\n")
    for bn in sub.nbdv:
        fort14.write(str(bn)+"\n")
    fort14.write(str(sub.nbdv[0])+"\n")

    # Internal boundaries within the subdomain
    processInternalBoundaries(full,sub)
    fort14.write(str(sub.nbou)+"\t!no. of land boundary segments\n")
    fort14.write(str(sub.nvel)+"\t!no. of land boundary nodes\n")
    for k in range(sub.nbou):

        nvell = len(sub.nbvv[k]['bnodes']) #  no. of nodes in normal flow specified bdry segment k
        ibtype = sub.nbvv[k]['ibtype']
        fort14.write(str(nvell)+" "+str(ibtype)+"\n")

        if ibtype in [1,11,21]:
            for i in range(nvell):
                fort14.write(str(sub.nbvv[k]['bnodes'][i])+"\n")
        elif ibtype in [4,24]:
            for i in range(nvell):
                fort14.write(str(sub.nbvv[k]['bnodes'][i])+" "+\
                             str(sub.nbvv[k]['ibconn'][i])+" "+\
                             str(sub.nbvv[k]['barinht'][i])+" "+\
                             str(sub.nbvv[k]['barincfsb'][i])+" "+\
                             str(sub.nbvv[k]['barincfsp'][i])+"\n")
        elif ibtype in [5,25]:
            for i in range(nvell):
                fort14.write(str(sub.nbvv[k]['bnodes'][i])+" "+\
                             str(sub.nbvv[k]['ibconn'][i])+" "+\
                             str(sub.nbvv[k]['barinht'][i])+" "+\
                             str(sub.nbvv[k]['barincfsb'][i])+" "+\
                             str(sub.nbvv[k]['barincfsp'][i])+" "+\
                             str(sub.nbvv[k]['pipeht'][i])+" "+\
                             str(sub.nbvv[k]['pipecoef'][i])+" "+\
                             str(sub.nbvv[k]['pipediam'][i])+"\n")
        else:
            raise SystemExit("ERROR: unknown ibtype is attempted to be written to sub fort.14")


    fort14.close()
       
def extractFort14(full,sub,shape):
    print "\nExtracting fort.14:"

    full.readFort14()

    # initialize nodal mapping containers
    sub.subToFullNode = None
    sub.fullToSubNode = None

    # Circular subdomain
    if (shape.typ=='c'):
        trimNodesCircle(full,sub,shape)
    # Elliptical subdomain:
    elif (shape.typ=='e'):
        trimNodesEllipse(full,sub,shape)
    else:
        print "ERROR: invalid subdomain shape type."
        exit()

    trimElements(full,sub)

    writeFort14(full,sub)

def extractFort13(full,sub):
    print "Extracting fort.13:"

    print "\t Reading fort.13 at", full.dir
    full13 = open(full.dir+"fort.13")
    print "\t Writing fort.13 at", sub.dir
    sub13 = open(sub.dir+"fort.13","w")

    # Read-write header:
    sub13.write(full13.readline())

    # Number of nodes:
    full13.readline() # discard
    sub13.write(str(len(sub.nodes)-1)+"\n")

    # number of parameters:
    nParams = int(full13.readline().split()[0])
    sub13.write(str(nParams)+"\n")

    # Default parameter values:
    for p in range(nParams):
        for i in range(4):
            sub13.write(full13.readline())

   
    # Write non-default parameter values: 
    for p in range(nParams):
            
        sub13.write(full13.readline()) # parameter name
        nFullNodes = int(full13.readline().split()[0])

        lines = []
        snode = 1
        def full(snode): return sub.subToFullNode[snode]
        fnode_last = full(len(sub.nodes)-1)

        for f in range(nFullNodes):

            sline = full13.readline().split()
            fnode = int(sline[0])

            if (not fnode>fnode_last):

                while fnode > full(snode) and snode < len(sub.nodes)-1:
                    snode += 1
    
                if fnode == full(snode):
                    lines.append([snode,sline]) 


        sub13.write(str(len(lines))+"\n")
        for l in lines:
            sub13.write(str(l[0])+"\t")
            for i in range(1,len(l[1])):
                sub13.write(l[1][i]+"\t")
            sub13.write("\n")

    sub13.close() 
    full13.close() 
    
# Write subdomain control file of the subdomain
def writeFort015(sub):
    print "Generating fort.015 at", sub.dir
    fort015 =  open(sub.dir+"fort.015", 'w')
    fort015.write( "0" + "\t!NOUTGS" + '\n' )
    fort015.write( "0" + "\t!NSPOOLGS" + '\n' )
    fort015.write( "1" + "\t!enforceBN" + '\n' )    # type-1 b.c. by default
    fort015.write( "0" + "\t!ncbnr" + '\n' )    
    fort015.close() 

# Writes nodal and elemental mapping files of the subdomain:
def writeNewToOld(sub):
    print "Generating nodal and elemental mapping files at", sub.dir

    py140 = open(sub.dir+"py.140","w")
    py140.write("Nodal mapping from sub to full\n")
    for i in range(1,len(sub.subToFullNode)+1):
        py140.write(str(i)+" "+str(sub.subToFullNode[i])+"\n")
    py140.close()
        
    py141 = open(sub.dir+"py.141","w")
    py141.write("Elemental mapping from sub to full\n")
    for i in range(1,len(sub.subToFullEle)+1):
        py141.write(str(i)+" "+str(sub.subToFullEle[i])+"\n")
    py141.close()
    
    

def copySwanFiles(full,sub):
    print "Copying SWAN input files to", sub.dir
    copyfile(full.dir+"fort.26",sub.dir+"fort.26")    
    copyfile(full.dir+"swaninit",sub.dir+"swaninit")    

# Generate the input files of the subdomain
def main(fullDir,subDir):

    print ""
    print '\033[95m'+'\033[1m'+"NCSU Subdomain Modeling for ADCIRC+SWAN"+'\033[0m'
    print ""

    print "Generating input files for the subdomain at", subDir

    # Initialize the full and subdomains
    full = Domain(fullDir)
    sub = Domain(subDir)

    # Read subdomain shape file:
    shape = SubShape(sub.dir)
         
    # Extract fort.14:
    if not os.path.exists(full.dir+"fort.14"):
        print "ERROR: No fort.14 file exists at", full.dir
        exit()
    else:
        extractFort14(full,sub,shape)  
 
    # Extract fort.13:
    if os.path.exists(full.dir+"fort.13"):
        extractFort13(full,sub)

    # Generate fort.015:
    writeFort015(sub)
    
    # Generate py.140 and py.141
    writeNewToOld(sub)

    # Copy SWAN input files
    if full.isCoupledAdcircSwan():
        copySwanFiles(full,sub)

    # The final log message:
    print "\nSubdomain input files are now ready."
    print '\033[91m'+"\nImportant Note:"+'\033[0m'
    print "fort.15 and meteorological files have to be generated manually "
    print "by the user as described in Subdomain Modeling User Guide.\n"

def usage():
    scriptName = os.path.basename(__file__)
    print ""
    print "Usage:"
    print " ", scriptName, "fulldomainDir subdomainDir\n"


if __name__== "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1],sys.argv[2])
    else:
        usage()


