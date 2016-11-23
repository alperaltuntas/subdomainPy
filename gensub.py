
# NCSU Subdomain Modeling
# --------------------------------
# Alper Altuntas - aaltunt@ncsu.edu
# (c) 2014 


# gensub.py
# ------------------------------------------------------------------------
# This script carves out a subdomain grid from a full domain grid.
# 	Required input files: full domain fort.14 (and fort.13) 
# 	Output files: subdomain input files fort.015, fort.14 (and fort.13)


#!/usr/bin/python
import sys
import math
import numpy

class node:
	def __init__(self, n_num, x_coord, y_coord, depth):
		self.n = 0
		self.x = x_coord
		self.y = y_coord
		self.d = depth
		self.o_n = n_num
		self.b = 0
		self.r = 0
		self.me = 99999
		self.i = -1

	def show(self):
		print (str(self.n) + " " + str(self.x) + " " + str(self.y) + " " + str(self.d))

	def fort(self):
		#return (str(self.x) + "\t" + str(self.y) + "\t" + str(self.d))
		return ( "\t%d\t% 0.12f\t% 0.12f\t% 0.12f\n" % (self.n, self.x, self.y, self.d) )

	def calcR(self, mx, my):
		self.r = (math.atan2(self.y - my, self.x - mx))

	def isDry(self):
		#if self.me == -99999:
		if self.d < 0:
			return int(1)
		else:
			return int(0)

class element:
	def __init__(self, ele_n, node_1, node_2, node_3):
		self.n = ele_n
		self.o_n = ele_n
		self.n1 = node_1
		self.n2 = node_2
		self.n3 = node_3

	def show(self):
		print(str(self.n) + " " + str(self.n1.n) + " " + str(self.n2.n) + " " + str(self.n3.n))

	def fort(self, n):
		return (str(n) + "\t3\t" + str(self.n1.n) + "\t" + str(self.n2.n) + "\t" + str(self.n3.n))

class boundary:
	def __init__(self):
		self.p = []
		self.n = -1

	def addPoint(self, x, y):
		self.p.append([x,y])

	def contains(self, x, y):
		if len(self.p) < 3:
			print ("Error: less than 3 vertices; no polygon exists")
			return 0
		else:
			print ""	
			
	#returns an extreme value for the boundary class
	#index = 0: return x; index = 1: return y
	#m < 0: return minimum; m > 0: return maximum
	def exValue(self, index, m):
		a = self.p[0][index]
		for i in range(1, len(self.p)):
			if self.p[i][index]*m > a*m:
				a = self.p[i][index]
		return a

	def getNext(self):
		self.n = self.n + 1
		return self.p[self.n][0], self.p[self.n][1]

	def reset(self):
		self.n = -1

	def show(self):
		for i in range(0, len(self.p)):
			print (str(self.p[i][0]) + " " + str(self.p[i][1]))

class helper:
	def __init__(self, n, i):
		self.n = n
		self.o = -1
		self.i = i

def orderBoundaryNodes(n):
	nodes = []
	helpers = []

	for i in range(0, len(n)):
		if n[i].b == 1:
			nodes.append(n[i])
			#helpers.append(helper(n[i].n, i))

	sx = 0
	sy = 0
	for i in range(0, len(nodes)):
		sx += nodes[i].x
		sy += nodes[i].y

	mx = sx / len(nodes)
	my = sy / len(nodes)

	b = []
	for i in range(0, len(nodes)):
		nodes[i].calcR(mx, my)
		b.append(nodes[i])
	b.sort(key=getR)

	for i in range(0, len(nodes)):
		helpers.append(helper(b[i].n, i))
	helpers.sort(key=getN)

	#segs = makeSegments(b, helpers)
	#return b, segs
	return b

def getR(node):
	return node.r

def getN(helper):
	return helper.n

def renumberNodes(sn):
	for i in range(0, len(sn)):
		sn[i].n = i+1
	return sn

def trimNodesPolygon(n, b):
	s = []
	for i in range(0, len(n)):
		if (b.contains(n[i].x, n[i].y)):
			s.append(n[i])

	s = renumberNodes(s)
	return s

def trimNodesCircle(n, f_n):
	s = []
	a = open("shape.c14", "r")
	t = a.readline().split()
	xb = float(t[0])
	yb = float(t[1])
	r = float(a.readline())
	for i in range(0, len(n)):
		if ((xb-n[i].x)**2 + (yb-n[i].y)**2 < r**2):
			s.append(n[i])
			f_n[i] = 1

	s = renumberNodes(s)
	a.close()
	return s, f_n

def trimNodesEllipse(n,f_n):
	s = []
	a = open("shape.e14","r")
	point1 = a.readline().split()
	p1 = [float(point1[0]), float(point1[1])]
	point2 = a.readline().split()
	p2 = [float(point2[0]), float(point2[1])]
	w = float(a.readline())
	Xmin = min(p1[0], p2[0])
	Xmax = max(p1[0], p2[0])
	Ymin = min(p1[1], p2[1])
	Ymax = max(p1[1], p2[1])

	c = [(p1[0] + p2[0])/2, (p1[1] + p2[1])/2]		#center point
	d = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**(0.5)	#distance between points
	theta = math.atan((p1[1] - p2[1])/(p1[0] - p2[0])) 	#theta to positive Xaxis
	sin = math.sin(-theta)
	cos = math.cos(-theta)
	
	xaxis = ((0.5*d)**2 + (0.5*w)**2)**(0.5) 		#xaxis will be the axis the points lie on
	yaxis = w/2
	
	for i in range(0, len(n)):
		#transform Global Coordinates to local coordinates
		X = n[i].x - c[0]
		Y = n[i].y - c[1]
		x = cos*X - sin*Y
		y = sin*X + cos*Y

		if(x**2/xaxis**2 + y**2/yaxis**2 < 1):
			s.append(n[i])
			f_n[i] = 1
	
	s = renumberNodes(s)
	a.close()
	return s, f_n

def trimNodesGiven(n, n_f, f_n):
	s = []
	sr = []
	sb = []
	a = open(n_f, "r")
	nn = int(a.readline().split()[0])
	for i in range(0, nn):
		t = int(a.readline().split()[0])
		sr.append(t)
		f_n[t-1] = 1
	bb = int(a.readline().split()[0])
	for i in range(0, bb):
		t = int(a.readline().split()[0])
		sb.append(t)
	a.close()

	for i in range(0, len(n)):
		if n[i].o_n in sr:
			s.append(n[i])
	if bb > 0:
		find_b = 0
		for i in range(0, len(s)):
			if s[i].o_n in sb:
				print "found", s[i].o_n, s[i].n
				s[i].b = 1
	else:
		find_b = 1

	s = renumberNodes(s)
	return s, find_b, f_n

def trimElements(e, s, find_b, f_n):
	s1 = []
	for i in range(0, len(s)):
		s1.append(s[i].o_n)

	es = []
	if find_b == 1:
		for i in range(0, len(e)):
			#print "element", i, e[i].n
			n1 = f_n[e[i].n1.o_n - 1]
			n2 = f_n[e[i].n2.o_n - 1]
			n3 = f_n[e[i].n3.o_n - 1]
			#print i+1,n1,n2,n3,e[i].n1.o_n, e[i].n2.o_n, e[i].n3.o_n,"\t",(n1+n2+n3)

			if (n1 + n2 + n3) == 3:
				es.append(e[i])
				#print "element added", i+1
			else:
				e[i].n1.b = n1
				e[i].n2.b = n2
				e[i].n3.b = n3
	else:
		for i in range(0, len(e)):
			if (e[i].n1.o_n in s1) and (e[i].n2.o_n in s1) and (e[i].n3.o_n in s1):
				es.append(e[i])

	return es

def fillNodes(input_fort):
	l = []
	e = []

	inf = open(input_fort, "r")
	title = inf.readline().split("\n")[0]
	
	t = inf.readline().split("\n")[0]
	ele_n = int(t.split()[0])
	node_n = int(t.split()[1])

	full_n = numpy.array([0 for i in range(0, node_n)])

	for i in range(0, node_n):
		rl = inf.readline()
		l.append(node(int(rl.split()[0]), float(rl.split()[1]), float(rl.split()[2]), float(rl.split()[3])))
	
	for i in range(0, ele_n):
		rl = inf.readline()
		#if (int(rl.split()[2])-1 < len(l) and int(rl.split()[3])-1 < len(l) and int(rl.split()[4])-1 < len(l)):
		e.append(element(int(rl.split()[0]), l[int(rl.split()[2])-1], l[int(rl.split()[3])-1], l[int(rl.split()[4])-1]))

	inf.close()

	return l, e, title, full_n

def writeFort(nodes, eles, title, out_file):
	o = open(out_file, "w")
	o.write (title + "\n")
	o.write (str(len(eles)) + " " + str(len(nodes)) + "\n")
	for i in range(0, len(nodes)):
		#o.write (str(i+1) + "\t" + nodes[i].fort() + "\n")
		o.write(nodes[i].fort())
	for i in range(0, len(eles)):
		o.write (eles[i].fort(i+1) + "\n")

	#b, s = orderBoundaryNodes(nodes)
	b = orderBoundaryNodes(nodes)
	a = open("bv.nodes", "w")
	
	o.write("1\t!no. of open boundary segments\n")
	o.write(str(len(b) + 1) + "\t!no. of open boundary nodes\n")
	o.write(str(len(b) + 1) + "\n")
	for i in range(0, len(b)):
		o.write(str(b[i].n) + "\n")
		a.write(str(b[i].n) + " " + str(b[i].r) + " " + str(b[i].x) + " " + str(b[i].y) + " " + str(b[i].me) +  "\n")
	o.write (str(b[0].n) + "\n") #must start and end on the same node
	o.write("0\t!no. of land boundary segments\n0\t!no. of land boundary nodes")
	#print len(s)
	#printSegments(s, o)
	a.close()
	o.close()

def writeNewToOld(nodes, elements, output_name, output_name2, num_n, num_e):
	a = open(output_name, "w")
	a.write("new old " + str(num_n) + "\n")
	for i in range(0, len(nodes)):
		a.write(str(nodes[i].n) + " " + str(nodes[i].o_n) + "\n")
	a.close()		
	
	a = open(output_name2, "w")
	a.write("new old " + str(num_e) + "\n")
	for i in range(0, len(elements)):
		a.write(str(i+1) + " " + str(elements[i].o_n) + "\n")
	a.close()

def write993(nodes, of):
	a = open(of, "w")
	#a.write("1\n1\n0\n0\n0\n")
	a.write("1\t!elevation\n")
	a.write("1\t!velocity\n")
	a.write("0\t!gwce lv\n")
	a.write("0\t!flux\n")
	a.write("0\t!momentum lv\n")
	a.write(str(len(nodes)) + "\n")
	for i in range(0, len(nodes)):
		a.write(str(i+1) + "\n")
	a.close()

def main(input_fort, p_or_c, out_f):
	#p_or_c = 0 for polygon, 1 for circle
	print (" \n Generating input files for the subdomain grid...")
	nodes, eles, title, full_n = fillNodes(input_fort)
	if int(p_or_c) == 0:
		sub_nodes, full_n = trimNodesEllipse(nodes, full_n)
		find_b = 1
	elif int(p_or_c) == 1:
		sub_nodes, full_n = trimNodesCircle(nodes, full_n)
		find_b = 1
	elif int(p_or_c) == 2:
		sub_nodes, find_b, full_n = trimNodesGiven(nodes, "trim.nodes", full_n)
	else:
		print ("invalid shape file input")

	sub_eles = trimElements(eles, sub_nodes, find_b, full_n)
	writeFort(sub_nodes, sub_eles, title, out_f)
	writeNewToOld(sub_nodes, sub_eles, "py.140", "py.141", len(full_n), len(eles))


        print ""
	fort015 =  open("fort.015", 'w')

	#NOUTGS:
	fort015.write( "0" + "\t!NOUTGS" + '\n' )
	fort015.write( "0" + "\t!NSPOOLGS" + '\n' )
	fort015.write( "1" + "\t!enforceBN" + '\n' )	# type-1 b.c. by default
	fort015.write( "0" + "\t!ncbnr" + '\n' )



class node2:
        def __init__(self, n, o):
                self.n = n
                self.o = o


def main13(new_f14_file, old_f13_file, new_f13_file, newtoold_file):
	print (" \n Generating input files for the subdomain grid...")
        nto = open(newtoold_file, "r")
        nto.readline() #discard
        nodes = []
        for line in nto:
                nodes.append(node2(int(line.split()[0]), int(line.split()[1])))
        nto.close()

        of = open(old_f13_file, "r")
        nf = open(new_f13_file, "w")

        nf.write(of.readline()) #re-write title

        of.readline() #discard number of nodes
        nf.write(str(len(nodes)) + "\n")

        n_params = int(of.readline())
        nf.write(str(n_params) + "\n")

        #write default parameter values
        for i in range(0, n_params):
                for j in range(0, 4):
                        nf.write(of.readline())

        lines = []
        for i in range(0, n_params):
                nf.write(of.readline()) #parameter name
                n_thisp = int(of.readline())
                count = 0
                g = 0
                lines = []
                for j in range(0, n_thisp):
                        ls = of.readline().split()
                        if g < len(nodes):
                                #if int(ls[0]) > nodes[g].o and g < len(nodes)-1:
                        #               g += 1

                                #if g < len(nodes) - 1:
                                while (int(ls[0]) > nodes[g].o) and (g < len(nodes)-1):
                                        g += 1

                                #print i, ls[0], nodes[g].o
                                if int(ls[0]) == nodes[g].o:
                                        lines.append([nodes[g].n, ls])
                                        count += 1
                                        g += 1
                                elif int(ls[0]) > nodes[g].o:
                                        g += 1

                nf.write(str(count) + "\n")
                #count = 0
                #g = 0
                for j in range(0, len(lines)):
                        #                       if count < len(nodes):
                        #       ls = line.split()
                        #       if int(ls[0]) > nodes[g].o:
                        #               g += 1

                        #       if int(ls[0]) == nodes[g].o:
                        #               nf.write(nodes[g].n + "\t")
                        #               for k in range(1, len(ls)):
                        #                       nf.write(ls[k] + "\t")
                        #               nf.write("\n")
                        nf.write(str(lines[j][0]) + "\t")
                        for k in range(1, len(lines[j][1])):
                                nf.write(lines[j][1][k] + "\t")
                        nf.write("\n")

        nf.close()
        of.close()




if __name__ == "__main__":
	if len(sys.argv) == 4:
		main(sys.argv[1], sys.argv[2], sys.argv[3])
		print(" fort.015 and fort.14 files are created for the subdomain grid.\n")
        elif len(sys.argv) == 6:
		main(sys.argv[1], sys.argv[2], sys.argv[3])
		main13( sys.argv[3], sys.argv[4], sys.argv[5], 'py.140' )
		print(" fort.015, fort.13 and fort.14 files are created for the subdomain grid.\n")
	else:
                print("")
                print("gensub.py: This scripts carves out a subdomain grid from a full domain grid.")
                print("")
		print(" Usage:")
		print(" a) Extract fort.14 only:")
		print("     gensub.py [full fort.14] [0 for ellipse, 1 for circle] [sub fort.14]")
		print(" b) Extract fort.14 and fort.13:")
		print("     gensub.py [full fort.14] [0 for ellipse, 1 for circle] [sub fort.14] [full fort.13] [sub fort.13] ")
		print("")
		print("\tFor an elliptical subdomain, provide 'shape.e14'")
		print("\tFor a circular subdomain, provide 'shape.e14'")
		print("")
