import sys
from csm import Domain

class NoMatchError(Exception):
    pass

def remap( full_dir, sub_dir, py140=None ):

    full = Domain( full_dir )
    sub = Domain( sub_dir )

    full.readFort14()
    sub.readFort14()
    sub.readPy140()

    print '\t Creating new nodal map'
    full_map = map_nodal_location(full.nodes)
    sub_boundaries = set( sub.nbdv )
    sub_nodes = [(i, sub.nodes[i]) for i in sub_boundaries]

    map_to_refined = []

    for i, node in sub_nodes:

        try:

            full_node = find_mapping( full_map, node )
            map_to_refined.append((full_node, i))

        except NoMatchError:
            print 'Unable to find match for node ' + str(i)
            print 'EXITING - Remapping unsuccessful'
            exit()

    if py140 is None:
        outfile = sub.dir + 'py.140'
    else:
        outfile = py140

    with open( outfile, 'w' ) as f:

        f.write('new to old\n')

        for old, new in map_to_refined:

            f.write('{}\t{}\n'.format(new, old))

def find_mapping( node_map, node ):

    x = node[0]
    y = node[1]

    if x in node_map:

        if y in node_map[x]:

            return node_map[x][y]

    raise NoMatchError

def map_nodal_location( nodes ):

    x_map = dict()

    for i, node in enumerate(nodes):

        if node is not None:

            x = node[0]
            y = node[1]

            if x not in x_map:

                x_map[ x ] = dict()

            x_map[ x ][ y ] = i

    return x_map



def print_usage( usage, depth=1 ):

    for line in usage:

        if isinstance( line, str ):

            print depth*'    ' + line

        if isinstance( line, list ):

            print_usage( line, depth+1 )

if __name__ == "__main__":

    if len(sys.argv) >= 2 and sys.argv[1] == '-r':

        numargs = len(sys.argv) - 2

        if numargs == 2:

            remap( sys.argv[2], sys.argv[3] )

        if numargs == 3:

            remap( sys.argv[2], sys.argv[3], sys.argv[4] )

    else:

        usage = [
            'Usage:',
            'Recreate py.140 (with only boundary nodes) for a subdomain',
            [
                'Overwrite existing py.140 in subdomain directory:',
                [
                    'python remap.py -r [full_dir] [sub_dir]'
                ],
                'Specify py.140 to write to:',
                [
                    'python remap.py -r [full_dir] [sub_dir] [py.140]'
                ]
            ]
        ]

        print_usage( usage )
