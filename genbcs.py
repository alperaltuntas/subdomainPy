
# NCSU Subdomain Modeling
# --------------------------------
# Alper Altuntas - aaltunt@ncsu.edu
# (c) 2014 


# genbcs.py
# ------------------------------------------------------------------------
# This script generates the subdomain boundary conditions file(s).
# 	Output file: subdomain fort.019 ( or fort.020 and fort.021)

import os
import sys
import time
from domain import domain

def main(fulldir,subdir,NOUTGS,sbtiminc):


	while True:
		runtype=raw_input("Enter the type of the full run (p for parallel, s for serial):\n")
		if runtype=='s' or runtype=='p':
			break
		else:
			print "Invalid key!"

	start = time.time()


	fulldomain = domain(fulldir)
	fulldomain.readFort14()
	subdomain = domain(subdir)
	subdomain.readFort14()
	subdomain.readPy140()

	if runtype=='p':
		fulldomain.readFort80()
	

	if NOUTGS==1:
		if runtype=='s':
			fulldomain.openFort065()
		else:
			fulldomain.openFort065_parallel()
		subdomain.openFort019(sbtiminc,fulldomain.nrtimesteps)
	elif NOUTGS==2:
		subdomain.readBNlist()
		if runtype=='s':
			fulldomain.openFort066()
			fulldomain.openFort067()
			subdomain.openFort020(sbtiminc,fulldomain.nrtimesteps)
			subdomain.openFort021(sbtiminc,fulldomain.nrtimesteps)
		else:
                        fulldomain.openFort066_parallel()
                        fulldomain.openFort067_parallel()
                        subdomain.openFort020(sbtiminc,fulldomain.nrtimesteps)
                        subdomain.openFort021(sbtiminc,fulldomain.nrtimesteps)


	if NOUTGS==1:	
		if runtype=='s':
			for i in range(fulldomain.nrtimesteps):
				fulldomain.readFort065()
				subdomain.writeFort019(fulldomain)
				#print out percentage:
				if i%1000==0:
					sys.stdout.write('\r')
					sys.stdout.write("%d%%" %(100*(i+1)/fulldomain.nrtimesteps))
					sys.stdout.flush()
			subdomain.writeFort019(fulldomain)
		else:
			for i in range(fulldomain.nrtimesteps):
				fulldomain.readFort065_parallel()
				if i==0: subdomain.createProcMapping(fulldomain,NOUTGS)
				subdomain.writeFort019_parallel(fulldomain)
				#print out percentage:
				if i%1000==0:
					sys.stdout.write('\r')
					sys.stdout.write("%d%%" %(100*(i+1)/fulldomain.nrtimesteps))
					sys.stdout.flush()
			subdomain.writeFort019_parallel(fulldomain)
	elif NOUTGS==2:	
		if runtype=='s':
			for i in range(fulldomain.nrtimesteps):
				fulldomain.readFort066(i)
				fulldomain.readFort067(i)
				subdomain.writeFort020(fulldomain)
				subdomain.writeFort021(fulldomain)
				#print out percentage:
				if i%1000==0:
					sys.stdout.write('\r')
					sys.stdout.write("%d%%" %(100*(i+1)/fulldomain.nrtimesteps))
					sys.stdout.flush()
		else:
			for i in range(fulldomain.nrtimesteps):
                                fulldomain.readFort066_parallel(i)
                                fulldomain.readFort067_parallel(i)
				if i==0: 
					subdomain.createProcMapping(fulldomain,NOUTGS)
                                subdomain.writeFort020_parallel(fulldomain)
                                subdomain.writeFort021_parallel(fulldomain)
				#print out percentage:
				if i%1000==0:
					sys.stdout.write('\r')
					sys.stdout.write("%d%%" %(100*(i+1)/fulldomain.nrtimesteps))
					sys.stdout.flush()
	
	print "\nElapsed time:", time.time()-start

def usage():

	print "Usage:"
	print "[full dir][subdomain dir][full NOUTGS][sbtiminc]"

if __name__== "__main__":
    if len(sys.argv) == 5:
        main(sys.argv[1], sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
    else:
        usage()

