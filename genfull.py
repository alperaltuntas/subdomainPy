
# NCSU Subdomain Modeling
# --------------------------------
# Alper Altuntas - aaltunt@ncsu.edu
# (c) 2014 


# genfull.py
# ------------------------------------------------------------------------
# This script generates the full domain control file.
# 	Output file: full domain fort.015

import os
import sys
from domain import domain

import readline, glob
def complete(text, state):
    return (glob.glob(text+'*')+[None])[state]

readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
readline.set_completer(complete)

def main(fulldir):

	
	print "\n This script creates a fort.015 file for ADCIRC Subdomain Modeling.\n"
	fort015 = open(fulldir+"fort.015",'w')
	#NOUTGS = raw_input("Enter the parameter 'NOUTGS':\n")
	NOUTGS = "1"
	NSPOOLGS = raw_input("Enter the parameter 'NSPOOLGS' (the freq. of forcing in no. of timesteps. Typically; 100): \n")
        enforceBN = str(0)	
	fort015.write( NOUTGS + "\t !NOUTGS\n")
	fort015.write( NSPOOLGS + "\t !NSPOOLGS\n")
	fort015.write( enforceBN + "\t !enforceBN\n")
	NOUTGS = int(NOUTGS)
	NSPOOLGS = int(NSPOOLGS)

	full = domain(fulldir)
	full.readFort14()
	subdomains = []
	cbnr = []
	obnr = []
	ibnr = []
	

	
	while True:
		typ = raw_input("Specify predetermined subdomains? (y or n) \n")
		if typ == "y":
	
			done = False		
			while not done:
				snew = raw_input("Enter the directory of the subdomain: (Type 'done' to end)\n")
				if snew=='done':
					done = True
					continue
				if not snew[-1] =='/':
					snew = snew+'/'
				try:			
					sub = domain(snew)
					print "\t Reading boundary information of", snew
					sub.readFort14()
					sub.readPy140()
					if NOUTGS==2: sub.readBNlist()
					subdomains.append(sub)

				except IOError:
					print "No such file or directory!",
				print("\t Subdomain info at "+sub.dir+" is added to the full domain control file.")

			for sub in subdomains:
				if NOUTGS==1:
					
					for cb in sub.nbdv:
						gcb = sub.n2o[cb]
						if not gcb in cbnr:
							cbnr.append(gcb)
				elif NOUTGS==2:

									
					for ob in sub.obn:
						gob = sub.n2o[ob]
						if not gob in obnr:
							obnr.append(gob)
					

					for ib in sub.ibn:
						gib = sub.n2o[ib]
						if not gib in ibnr:
							ibnr.append(gib)
			if NOUTGS==1:
				fort015.write( str(len(cbnr)) +'\t !ncbnr\n')
				for n in cbnr:
						fort015.write( str(n)+'\n')
			if NOUTGS==2:
				fort015.write( str(len(obnr)) +'\t !nobnr\n')
				for n in obnr:
						fort015.write( str(n)+'\n')
				fort015.write( str(len(ibnr)) +'\t !nibnr\n')
				for n in ibnr:
						fort015.write( str(n)+'\n')

			print " fort.015 file for the full run is ready."
			break
		elif typ == 'n':

                        if NOUTGS==1:
                                fort015.write( str(full.np) +'\t !ncbnr\n')
                                for n in range(full.np):
                                                fort015.write( str(n+1)+'\n')
                        if NOUTGS==2:
                                fort015.write( str(full.np) +'\t !nobnr\n')
                                for n in range(full.np):
                                                fort015.write( str(n+1)+'\n')
                                fort015.write( str(full.np) +'\t !nibnr\n')
                                for n in range(full.np):
                                                fort015.write( str(n+1)+'\n')
			print " fort.015 file for the full run is ready."
			break
		else:
			print " Invalid key!"



	

def usage():

	print "Usage:"
	print "[full dir]"

if __name__== "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        usage()

