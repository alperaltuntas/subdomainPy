import os
import math

class domain(object,):

	def __init__(self,dir):
		self.dir = dir

	def readFort14(self):
		print "\t Reading fort.14 at", self.dir
		fort14 = open(self.dir+"fort.14")
		self.nodes = []
		self.elements = []

		line = fort14.readline()
		line = fort14.readline()
		self.ne = int(line.split()[0])
		self.np = int(line.split()[1])

		self.nodes = [None]*(self.np+1)
		self.elements = [None]*(self.ne+1)
		
		for n in range(self.np):
			line = fort14.readline()
			node = int(line.split()[0])
			xc = float(line.split()[1])
			yc = float(line.split()[2])
			d = float(line.split()[3])
			self.nodes[node] = [xc,yc,d]

		for e in range(self.ne):
			line = fort14.readline()
			ele = int(line.split()[0])
			n1 = int(line.split()[2])
			n2 = int(line.split()[3])
			n3 = int(line.split()[4])
			self.elements[ele] = [n1,n2,n3]
	
		line = fort14.readline()
		self.nope = int(line.split()[0])	# no of ele. boundary forcing segments
		line = fort14.readline()		
		self.neta = int(line.split()[0])	# total number of ele. boundary nodes
		self.nbdv = []				# elevation specified boundary node numbers

		for k in range(self.nope):
			line = fort14.readline()
			nvdll = int(line.split()[0])	# no. of nodes in elevation boundary segment k.
			for j in range(nvdll):
				line = fort14.readline()
				self.nbdv.append(int(line.split()[0]))


				
		line = fort14.readline()
		self.nbou = int(line.split()[0])	# number of normal flow (discharge) specified boundary segments, including LAND boundaries
		line = fort14.readline()		
		self.nvel = int(line.split()[0])	# total number of normal flow specified boundary nodes 
		self.nbvv = []				# node numbers on normal flow boundary segment k. 

		for k in range(self.nbou):
			line = fort14.readline()
			nvell = int(line.split()[0])	# number of nodes in normal flow specified boundary segment k.
			for j in range(nvell):
                                line = fort14.readline()
				self.nbvv.append(int(line.split()[0]))
			
		fort14.close()



	def readFort80(self):

		if not os.path.exists(self.dir+'fort.80'):		
			print "Warning!\n \tfort.80 at ",self.dir+'fort.80'," couldn't be found"
		else:

			fort80 = open(self.dir+'fort.80')
	                for i in range(14):
	                        line = fort80.readline()
        	                if line.split()[-1] == "NWLAT":
                	                break
                        	if i==3 :
                                	self.ne   = int(line.split()[0])
	                                self.np = int(line.split()[1])
        	                if i==4 :
                	                self.nprocs = int(line.split()[0])


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



		
	def readPy140(self):
                print "\t Reading py.140 at ", self.dir
		py140 = open(self.dir+"py.140")
		py140.readline()
		self.n2o = [None]*(self.np+1)
		for n in range(self.np):
			line = py140.readline()
			new = int(line.split()[0])
			old = int(line.split()[1])
			self.n2o[new] = old


	def readBNlist(self):
		self.cbn = []
		self.obn = []
		self.ibn = []	
		
		bnlist = open(self.dir+"bnlist.14")
		line = bnlist.readline()
		self.ncbn = int(line.split()[0])
		for i in range(self.ncbn):
			line = bnlist.readline()
			self.cbn.append( int(line.split()[0]) )
		line = bnlist.readline()
		self.nobn = int(line.split()[0])
		for i in range(self.nobn):
			line = bnlist.readline()
			self.obn.append( int(line.split()[0]) )
		line = bnlist.readline()
		self.nibn = int(line.split()[0])
		for i in range(self.nibn):
			line = bnlist.readline()
			self.ibn.append( int(line.split()[0]) )
		
	def writeBNlist(self,NOUTGS):
		bnlist = open(self.dir+'bnlist.14','w')

		edges = []
		boundaryNodes = []
		for e in range(self.ne):
			el = self.elements[e+1]
			n1 = el[0]
			n2 = el[1]
			n3 = el[2]
			edges.append( [n1,n2] )
			edges.append( [n1,n3] )
			edges.append( [n2,n3] )

		#outer boundaries
		for edge in edges:
			n1 = edge[0]
			n2 = edge[1]
			i = edges.count([n1,n2])
			j = edges.count([n2,n1])
			if i+j>1:
				continue
			else:
				if not n1 in boundaryNodes:
					boundaryNodes.append(n1)
				if not n2 in boundaryNodes:
					boundaryNodes.append(n2)
		boundaryNodes.sort()
		print boundaryNodes

		#inner boudaries
		innerBoundaries = []
                for e in range(self.ne):
                        el = self.elements[e+1]
                        n1 = el[0]
                        n2 = el[1]
                        n3 = el[2]

			if (n1 in boundaryNodes) or (n2 in boundaryNodes) or (n3 in boundaryNodes):
				if not n1 in boundaryNodes and not n1 in innerBoundaries:
					innerBoundaries.append(n1)
				if not n2 in boundaryNodes and not n2 in innerBoundaries:
					innerBoundaries.append(n2)
				if not n3 in boundaryNodes and not n3 in innerBoundaries:
					innerBoundaries.append(n3)
		innerBoundaries.sort()
		print innerBoundaries

		if NOUTGS==1:
			bnlist.write("%i\t!cbn\n" %(len(boundaryNodes)))
			for bn in boundaryNodes:
				bnlist.write( "%i\n" %(bn))
			bnlist.write("%i\t!obn\n" %(0))
			bnlist.write("%i\t!ibn\n" %(0))
		if NOUTGS==2:
			bnlist.write("%i\t!cbn\n" %(0))
			bnlist.write("%i\t!obn\n" %(len(boundaryNodes)))
			for bn in boundaryNodes:
				bnlist.write(" %i\n" %(bn))
			bnlist.write("%i\t!ibn\n" %(len(innerBoundaries)))
			for ib in innerBoundaries:
				bnlist.write(" %i\n" %(ib))


	def openFort065(self):
		if not os.path.exists(self.dir+'fort.065'):		
			print "fort.065 does not exist!"
			return
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
	                        print "fort.065 does not exist! proc:",proc
        	                return
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



	def openFort066(self):
		if not os.path.exists(self.dir+'fort.066'):		
			print "fort.066 does not exist!"
			return
		self.fort066 = open(self.dir+"fort.066")
		line = self.fort066.readline()
		line = self.fort066.readline()
		self.nspoolgs = int( line.split()[0] )
		self.nobnr = int( line.split()[1] )
		self.nrtimesteps = int( line.split()[2] )
		self.obnr = [None]*self.nobnr
		self.eo = [None]*self.nobnr
		self.uo = [None]*self.nobnr
		self.vo = [None]*self.nobnr
		self.wdo = [None]*self.nobnr



	def openFort066_parallel(self):
		self.fort066 = [None]*self.nprocs
		self.nobnr = [None]*self.nprocs
		self.obnr = [None]*self.nprocs
		self.eo = [None]*self.nprocs
		self.uo = [None]*self.nprocs
		self.vo = [None]*self.nprocs
		self.wdo = [None]*self.nprocs

		for proc in range(self.nprocs):
			l = len(str(proc)) # number of digits of proc no.
			p066 = self.dir+'PE'+'0'*(4-l)+str(proc)+'/fort.066'
			if not os.path.exists(p066):
	                        print "fort.066 does not exist! proc:",proc
        	                return
			self.fort066[proc] = open(p066)
			line = self.fort066[proc].readline()
			line = self.fort066[proc].readline()
			self.nspoolgs = int( line.split()[0] )
			self.nobnr[proc] = int( line.split()[1] )
			self.nrtimesteps = int( line.split()[2] )
			self.obnr[proc] = [None]*self.nobnr[proc]
			self.eo[proc] = [None]*self.nobnr[proc]
			self.uo[proc] = [None]*self.nobnr[proc]
			self.vo[proc] = [None]*self.nobnr[proc]
			self.wdo[proc] = [None]*self.nobnr[proc]


	def openFort067(self):
		if not os.path.exists(self.dir+'fort.067'):		
			print "fort.067 does not exist!"
			return
		self.fort067 = open(self.dir+"fort.067")
		line = self.fort067.readline()
		line = self.fort067.readline()
		self.nspoolgs = int( line.split()[0] )
		self.nibnr = int( line.split()[1] )
		self.nrtimesteps = int( line.split()[2] )
		self.ibnr = [None]*self.nibnr
		self.ei = [None]*self.nibnr


	def openFort067_parallel(self):
		self.fort067 = [None]*self.nprocs
		self.nibnr = [None]*self.nprocs
		self.ibnr = [None]*self.nprocs
		self.ei = [None]*self.nprocs

		for proc in range(self.nprocs):
			l = len(str(proc)) # number of digits of proc no.
			p067 = self.dir+'PE'+'0'*(4-l)+str(proc)+'/fort.067'
			if not os.path.exists(p067):
	                        print "fort.067 does not exist! proc:",proc
        	                return
			self.fort067[proc] = open(p067)
			line = self.fort067[proc].readline()
			line = self.fort067[proc].readline()
			self.nspoolgs = int( line.split()[0] )
			self.nibnr[proc] = int( line.split()[1] )
			self.nrtimesteps = int( line.split()[2] )
			self.ibnr[proc] = [None]*self.nibnr[proc]
			self.ei[proc] = [None]*self.nibnr[proc]


	def openFort068(self):
                if not os.path.exists(self.dir+'fort.068'):
                        print "fort.068 does not exist!"
                        return
		self.fort068 = open(self.dir+'fort.068')
		line = self.fort068.readline()
		line = self.fort068.readline()
		self.nobnr = int(line.split()[0])
		self.mnei = int(line.split()[1])
		self.ntable = dict()
		line = self.fort068.readline()
		self.nlines068 = 0 
 		while True:
			line = self.fort068.readline()
			if line.split()[-1]=='Timestep':
				break
			self.nlines068 += 1
			node = int(line.split()[0])	
			neighbor = int(line.split()[1])
			if node in self.ntable:
				self.ntable[node] += [neighbor]
			else:
				self.ntable[node] = [neighbor]

		self.fort068 = open(self.dir+'fort.068')
		line = self.fort068.readline()
		line = self.fort068.readline()


	def openFort068_parallel(self):
		self.fort068 = [None]*self.nprocs
		self.nobnr = [None]*self.nprocs
		self.ntable = [dict()]*self.nprocs
		self.nlines068 = [None]*self.nprocs

		for proc in range(self.nprocs):
                        l = len(str(proc)) # number of digits of proc no.
                        p068 = self.dir+'PE'+'0'*(4-l)+str(proc)+'/fort.068'
                        if not os.path.exists(p068):
                                print "fort.068 does not exist! proc:",proc
                                return
			self.fort068[proc] = open(p068)
			line = self.fort068[proc].readline()
			line = self.fort068[proc].readline()

			self.nobnr[proc] = int(line.split()[0])
			self.mnei = int(line.split()[1])
			
			line = self.fort068[proc].readline()
			self.nlines068[proc] = 0
			while True:
				line = self.fort068[proc].readline()
	                        if line.split()[-1]=='Timestep':
        	                        break
                	        self.nlines068[proc] += 1
	                        node = int(line.split()[0])
        	                neighbor = int(line.split()[1])
				if node in self.ntable[proc]:
					self.ntable[proc][node] += [neighbor]
				else:
					self.ntable[proc][node] = [neighbor]

                        self.fort068[proc] = open(p068)
                        line = self.fort068[proc].readline()
                        line = self.fort068[proc].readline()

	def readenforceBN(self):
		fort015 = open(self.dir+'fort.015')
		line = fort015.readline()
		line = fort015.readline()
		line = fort015.readline()
		self.enforceBN = int(line.split()[0])

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

	def readFort066(self,t):
		self.tsline = self.fort066.readline()
		for i in range(self.nobnr):
			line = self.fort066.readline().split()
			if t<1: 
				self.obnr[i] = int(line[0])
				if i==0:
					self.obnrIndex = dict() 
				self.obnrIndex[int(line[0])] = i
			self.eo[i] = line[1]
			self.uo[i] = line[2]
			line = self.fort066.readline().split()
			self.vo[i] = line[0]
			self.wdo[i] = line[1]

        def readFort066_parallel(self,t):
                for proc in range(self.nprocs):
                	self.tsline = self.fort066[proc].readline()
                        for i in range(self.nobnr[proc]):
                                line = self.fort066[proc].readline().split()
				if t<1:				
	                                self.obnr[proc][i] = int(line[0])
                                self.eo[proc][i] = line[1]
                                self.uo[proc][i] = line[2]
                                line = self.fort066[proc].readline().split()
                                self.vo[proc][i] = line[0]
                                self.wdo[proc][i] = line[1]

	def readFort067(self,t):
		self.tsline = self.fort067.readline()
		for i in range(self.nibnr):
			line = self.fort067.readline().split()
			if t<1:
				self.ibnr[i] = int(line[0])
				if i==0:
					self.ibnrIndex = dict()
				self.ibnrIndex[int(line[0])] = i
			self.ei[i] = line[1]

        def readFort067_parallel(self,t):
                for proc in range(self.nprocs):
                	self.tsline = self.fort067[proc].readline()
                        for i in range(self.nibnr[proc]):
                                line = self.fort067[proc].readline()
				if t<1:
	                                self.ibnr[proc][i] = int(line.split()[0])
                                self.ei[proc][i] = line.split()[1]


	def readFort068(self,t):
		if t<1: 
			self.line068tracker = [None]*self.nlines068
			self.coefIndex = dict()
			self.coef = [None]*self.nlines068
		self.tsline2 = self.fort068.readline()
		for i in range(self.nlines068):
			line = self.fort068.readline()
			if t<1:
				node = int(line.split()[0])
				neighbor = int(line.split()[1])
				self.line068tracker[i] = [node,neighbor]
				self.coefIndex[node,neighbor] = i
#			node = self.line068tracker[i][0]
#			neighbor = self.line068tracker[i][1]
#			c = line.split()[2]
#			self.coef[node,neighbor] = c
#			self.coef[self.line068tracker[i][0],self.line068tracker[i][1]] = line.split()[2]
			self.coef[i] = line.split()[2]

	def readFort068_parallel(self,t):
		if t<1:
			self.coef = [None]*self.nprocs
			self.line068tracker = [None]*self.nprocs
			self.coefIndex = [dict()]*self.nprocs
			for proc in range(self.nprocs):
				self.coef[proc] = [None]*self.nlines068[proc]
				self.line068tracker[proc] = [None]*self.nlines068[proc]
					
		for proc in range(self.nprocs):
			self.tsline2 = self.fort068[proc].readline()
			for i in range(self.nlines068[proc]):
				line = self.fort068[proc].readline()
				if t<1:
					node = int(line.split()[0])
					neighbor = int(line.split()[1])
					self.line068tracker[proc][i] = [node,neighbor]
					self.coefIndex[proc][node,neighbor] = i
				self.coef[proc][i] = line.split()[2]


	def openFort019(self,sbtiminc,nrtimesteps):
		self.fort019 = open(self.dir+'fort.019','w')
		self.fort019.write("Boundary conditions for subdomain\n")
		#self.fort019.write(str(sbtiminc)+'\t'+str(self.ncbn)+'\t'+str(nrtimesteps)+'\n')
		self.fort019.write(str(sbtiminc)+'\t'+str(self.neta)+'\t'+str(nrtimesteps)+'\n')
		for cb in self.nbdv:
			self.fort019.write(' '+str(cb)+'\n')


	def openFort020(self,sbtiminc,nrtimesteps):
		self.fort020 = open(self.dir+'fort.020','w')
		self.fort020.write("Boundary conditions for subdomain\n")
		self.fort020.write(str(sbtiminc)+'\t'+str(self.nobn)+'\t'+str(nrtimesteps)+'\n')
		for ob in self.obn:
			self.fort020.write(' '+str(ob)+'\n')

	

	def openFort021(self,sbtiminc,nrtimesteps):
		self.fort021 = open(self.dir+'fort.021','w')
		self.fort021.write("Boundary conditions for subdomain\n")
		self.fort021.write(str(sbtiminc)+'\t'+str(self.nibn)+'\t'+str(nrtimesteps)+'\n')
		for ib in self.ibn:
			self.fort021.write(' '+str(ib)+'\n')

	def openFort022(self,f):
		self.fort022 = open(self.dir+'fort.022','w')
		self.fort022.write("COEF for sobdomain o.b.n.\n")

		#determine the number of lines in fort.022
		nlines022 = 0
		self.writeCoef = dict()
		self.gneighbor2neighbor = dict()
                for ob in self.obn:
                        gn = self.n2o[ob]
                        for gneighbor in f.ntable[gn]:
                                if gneighbor in self.n2o:
					self.writeCoef[gn,gneighbor] = True
                                        neighbor = self.n2o.index(gneighbor)
					self.gneighbor2neighbor[gneighbor] = neighbor
                                        if neighbor in self.obn:
						nlines022 += 1
						self.writeCoef[neighbor] = True
					else:
						self.writeCoef[neighbor] = False
				else:
					self.writeCoef[gn,gneighbor] = False

		self.fort022.write(str(nlines022)+'\t'+str(self.nobn)+' ! nlines, nobn\n')
                for ob in self.obn:
                        self.fort022.write(' '+str(ob)+'\n')

	def openFort022_parallel(self,f):
                self.fort022 = open(self.dir+'fort.022','w')
                self.fort022.write("COEF for sobdomain o.b.n.\n")

                #determine the number of lines in fort.022
                nlines022 = 0
		self.writeCoef = dict()
		self.gneighbor2neighbor = dict()
		for ob in self.obn:
			gn = self.n2o[ob]
                        proc = self.obIndex[ob][0]
                        i = self.obIndex[ob][1]
			for gneighbor in f.ntable[proc][gn]:
				if gneighbor in self.n2o:
					self.writeCoef[proc,gn,gneighbor] = True
					neighbor = self.n2o.index(gneighbor)
					self.gneighbor2neighbor[gneighbor,proc] = neighbor
					if neighbor in self.obn:
						nlines022 += 1
						self.writeCoef[proc,neighbor] = True
					else:
						self.writeCoef[proc,neighbor] = False
				else:
					self.writeCoef[proc,gn,gneighbor] = False
		self.fort022.write(str(nlines022)+'\t'+str(self.nobn)+' ! nlines, nobn\n')
		for ob in self.obn:
			self.fort022.write(' '+str(ob)+'\n')

        def createProcMapping(self,f,NOUTGS):
                if NOUTGS==1:
                        self.cbIndex = [None]*(self.np+1)
                        #for cb in self.cbn:
                        for cb in self.nbdv:
                                gn = self.n2o[cb]
                                for proc in range(f.nprocs):
                                        i = 0
                                        for node in f.cbnr[proc]:
                                                if gn == node:
                                                        self.cbIndex[cb] = [proc,i]
                                                i=i+1
                if NOUTGS==2:
			#index mapping for outer boundary nodes
                        self.obIndex = [None]*(self.np+1)
                        for ob in self.obn:
                                gn = self.n2o[ob]
                                for proc in range(f.nprocs):
                                        i = 0
                                        for node in f.obnr[proc]:
                                                if gn == node:
                                                        self.obIndex[ob] = [proc,i]
                                                i=i+1
			#index mapping for inner boundary nodes
			self.ibIndex = [None]*(self.np+1)
			for ib in self.ibn:
				gn = self.n2o[ib]
				for proc in range(f.nprocs):
					i = 0
					for node in f.ibnr[proc]:
						if gn == node:
							self.ibIndex[ib] = [proc,i]
						i=i+1

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


	def writeFort020(self,f):
		self.fort020.write(f.tsline)
		for ob in self.obn:
			gn = self.n2o[ob]			
			i = f.obnrIndex[gn]
			self.fort020.write(str(ob)+'\t'+f.eo[i]+'\t'+f.uo[i]+'\n')
			self.fort020.write(f.vo[i]+'\t'+f.wdo[i]+'\n')

	def writeFort020_parallel(self,f):
		self.fort020.write(f.tsline)
		for ob in self.obn:
			gn = self.n2o[ob]
			proc = self.obIndex[ob][0]
			i = self.obIndex[ob][1]
			self.fort020.write(str(ob)+'\t'+f.eo[proc][i]+'\t'+f.uo[proc][i]+'\n')
			self.fort020.write(f.vo[proc][i]+'\t'+f.wdo[proc][i]+'\n')

	def writeFort021(self,f):
		self.fort021.write(f.tsline)
		for ib in self.ibn:
			gn = self.n2o[ib]			
			i = f.ibnrIndex[gn]
			self.fort021.write(str(ib)+'\t'+f.ei[i]+'\n')

	def writeFort021_parallel(self,f):
		self.fort021.write(f.tsline)
		for ib in self.ibn:
			gn = self.n2o[ib]
			proc = self.ibIndex[ib][0]
			i = self.ibIndex[ib][1]
			self.fort021.write(str(ib)+'\t'+f.ei[proc][i]+'\n')

	def writeFort022(self,f):
		self.fort022.write(f.tsline2)
		
		for ob in self.obn:
			gn = self.n2o[ob]
			for gneighbor in f.ntable[gn]:
				if self.writeCoef[gn,gneighbor]:
					neighbor = self.gneighbor2neighbor[gneighbor]	
					if self.writeCoef[neighbor]:
						i = f.coefIndex[gn,gneighbor]
						self.fort022.write(str(ob)+'\t'+str(neighbor)+'\t'+f.coef[i]+'\n')



	def writeFort022_parallel(self,f):
		self.fort022.write(f.tsline)
		for ob in self.obn:
			gn = self.n2o[ob]
			proc = self.obIndex[ob][0]
                        i = self.obIndex[ob][1]
			for gneighbor in f.ntable[proc][gn]:
				if self.writeCoef[proc,gn,gneighbor]:
					neighbor = self.gneighbor2neighbor[gneighbor,proc]
					if self.writeCoef[proc,neighbor]:
						i = f.coefIndex[proc][gn,gneighbor]
						self.fort022.write(str(ob)+'\t'+str(neighbor)+'\t'+f.coef[proc][i]+'\n')



# The following functions are for preprocessing

	def openGlobalFort020(self): #for subdomain preprocessing
		self.eo = [None]*self.nobn
		self.uo = [None]*self.nobn
		self.vo = [None]*self.nobn
		self.wdo = [None]*self.nobn
		self.fort020 = open(self.dir+'fort.020')
		line = self.fort020.readline()
		line = self.fort020.readline()
		self.sbtiminc = int(line.split()[0])
		self.nrtimesteps = int(line.split()[2])
		for i in range(self.nobn):
			self.fort020.readline()


        def openGlobalFort021(self): #for subdomain preprocessing
                self.ei = [None]*self.nibn
                self.fort021 = open(self.dir+'fort.021')
                line = self.fort021.readline()
                line = self.fort021.readline()
                self.sbtiminc = int(line.split()[0])
                self.nrtimesteps = int(line.split()[2])
                for i in range(self.nibn):
                        self.fort021.readline()


	def openGlobalFort022(self): #for subdomain prepressing
		self.fort022 = open(self.dir+'fort.022')
		line = self.fort022.readline()
		line = self.fort022.readline()
		self.nlines = int(line.split()[0])
		self.localnlines = [0]*(self.nprocs)
		self.locallinelist = [None]*(self.nprocs) #list of local fort022 node&neighbor 
		for i in range(self.nobn):
			self.fort022.readline()

		# count the number of lines for each local fort.022
		line = self.fort022.readline()
		for i in range(self.nlines):
			line = self.fort022.readline()
			n = int(line.split()[0])
			gneighbor = int(line.split()[1])
			proc = int(self.innerNodes[n][0])
			pneighbor = self.nodesP2G[proc].index(gneighbor)
			pn = int(self.innerNodes[n][1])
			self.localnlines[proc] += 1
			if self.locallinelist[proc]==None:
				self.locallinelist[proc] = []
				self.locallinelist[proc].append( [pn,pneighbor] )
			else:
				self.locallinelist[proc].append( [pn,pneighbor] )

		# re-read fort.022		
		self.fort022.close()
		self.fort022 = open(self.dir+'fort.022')
                line = self.fort022.readline()
                line = self.fort022.readline()
                for i in range(self.nobn):
                        self.fort022.readline()
	
		
	def openLocalFort020(self):
		self.p020 = [None]*self.nprocs
                self.localobn = [None]*self.nprocs
                self.localeo = [None]*self.nprocs
                self.localuo = [None]*self.nprocs
                self.localvo = [None]*self.nprocs
                self.localwdo = [None]*self.nprocs

                for proc in range(self.nprocs):
                        self.localobn[proc] = []

		for proc in range(self.nprocs):
			for ob in self.obn:
				if ob in self.nodesP2G[proc]:
					i = self.obn.index(ob)
					pn = self.allNodes[ob,proc]
					self.localobn[proc].append( [pn,ob,i] )
	
                for proc in range(self.nprocs):
                        l = len(str(proc)) # number of digits of proc no.
                        self.p020[proc] = open((self.dir+'PE'+'0'*(4-l)+str(proc)+'/fort.020'),'w')
			self.p020[proc].write("Local Boundary conditions\n")
			self.p020[proc].write(str(self.sbtiminc)+'\t'+   \
                                                            str(len(self.localobn[proc]))+'\n')
			for i in range(len(self.localobn[proc])):
				self.p020[proc].write(' '+str(self.localobn[proc][i][0])+'\n')



        def openLocalFort021(self): #for subdomain preprocessing
                self.p021 = [None]*self.nprocs
                self.localibn = [None]*self.nprocs
                self.localei = [None]*self.nprocs

                for proc in range(self.nprocs):
                        self.localibn[proc] = []

		for proc in range(self.nprocs):
			for ib in self.ibn:
				if ib in self.nodesP2G[proc]:
					i = self.ibn.index(ib)
					pn = self.allNodes[ib,proc]
					self.localibn[proc].append( [pn,ib,i] )
				


                i = 0
                for ib in self.ibn:
                        proc = self.innerNodes[ib][0]
                        pn = self.innerNodes[ib][1]
                        self.localibn[proc].append( [pn,ib,i] )
                        i=i+1

                for proc in range(self.nprocs):
                        l = len(str(proc)) # number of digits of proc no.
                        self.p021[proc] = open((self.dir+'PE'+'0'*(4-l)+str(proc)+'/fort.021'),'w')
                        self.p021[proc].write("Local Boundary conditions\n")
                        self.p021[proc].write(str(self.sbtiminc)+'\t'+   \
                                                            str(len(self.localibn[proc]))+'\n')
                        for i in range(len(self.localibn[proc])):
                                self.p021[proc].write(' '+str(self.localibn[proc][i][0])+'\n')



	def openLocalFort022(self): #for subdomain preprocessing
		self.p022 = [None]*self.nprocs
		for proc in range(self.nprocs):
                        l = len(str(proc)) # number of digits of proc no.
                        self.p022[proc] = open((self.dir+'PE'+'0'*(4-l)+str(proc)+'/fort.022'),'w')
                        self.p022[proc].write("Local Boundary conditions\n")
                        self.p022[proc].write(str(self.localnlines[proc])+'\t'+   \
                                                            str(len(self.localobn[proc]))+'\n')
                        for i in range(len(self.localobn[proc])):
                                self.p022[proc].write(' '+str(self.localobn[proc][i][0])+'\n')
			


	def readGlobalwriteLocalFort020(self): #for subdomain preprocessing
		self.tsline = self.fort020.readline()
		for i in range(self.nobn):
			line = self.fort020.readline()
			self.eo[i] = float(line.split()[1])
			self.uo[i] = float(line.split()[2])
			line = self.fort020.readline()
			self.vo[i] = float(line.split()[0])
			self.wdo[i] = int(line.split()[1])

		for proc in range(self.nprocs):
			self.p020[proc].write(self.tsline)
			for j in range(len(self.localobn[proc])):
				pn = str(self.localobn[proc][j][0])
				i = self.localobn[proc][j][2]
				self.p020[proc].write(pn+' '+str(self.eo[i])+' '+str(self.uo[i])+'\n')
				self.p020[proc].write(str(self.vo[i])+' '+str(self.wdo[i])+'\n')
			


        def readGlobalwriteLocalFort021(self): #for subdomain preprocessing
                self.tsline = self.fort021.readline()
                for i in range(self.nibn):
                        line = self.fort021.readline()
                        self.ei[i] = float(line.split()[1])

                for proc in range(self.nprocs):
                        self.p021[proc].write(self.tsline)
                        for j in range(len(self.localibn[proc])):
                                pn = str(self.localibn[proc][j][0])
                                i = self.localibn[proc][j][2]
                                self.p021[proc].write(pn+' '+str(self.ei[i])+'\n')




	def readGlobalwriteLocalFort022(self): #for subdomain preprocessing
		coef = dict()
                self.tsline2 = self.fort022.readline()
		for i in range(self.nlines):
			line = self.fort022.readline()
			gn = int(line.split()[0])
			gneighbor = int(line.split()[1])
			c = float(line.split()[2])
			coef[gn,gneighbor] = c

		for proc in range(self.nprocs):
			self.p022[proc].write(self.tsline2)
			if len(self.localobn[proc]) > 0:
				for pn,pneighbor in self.locallinelist[proc]:
					gn = self.nodesP2G[proc][pn]
					gneighbor = self.nodesP2G[proc][pneighbor]
					c = coef[gn,gneighbor]
					self.p022[proc].write(str(pn)+'\t'+str(pneighbor)+'\t'+str(c)+'\n')
	







