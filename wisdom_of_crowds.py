import networkx as nx
from collections import defaultdict
import itertools
from networkx.exception import NetworkXNoPath

class Crowd:
    def __init__(self,G,max_m=5,node_key='T'):
        self.G = G
        self.min_k = 2
        self.max_k = 5
        self.min_m = 1
        self.max_m=max_m
        self.node_key='T'
        self.precomputed_path_dict = {} #holds unconditional paths
        self.precomputed_paths_by_hole_node = defaultdict(dict)  #holds dict of paths per node
        self.node_set = set(G.nodes())


    #makes search for possible cliques more efficient
    def efficient_pairs(self,x):
        l = len(x)
        for i in range(1,l):
            for j in range(0,i):
                yield (x[i],x[j])

    #for a single node, and a single source, precompute the path
    #and populate the current dictionary with them.

    def shortest_path_node_source_target(self,v,source,target):



        #step 1: am I in the generic path dictionary?
        try:
            shortest_unconditional_path = self.precomputed_path_dict[(source,target)]
        except KeyError: #well figure this later in case it comes in handy
            try:
                shortest_unconditional_path = nx.algorithms.shortest_path(self.G,source,target)
                self.precomputed_path_dict[(source,target)] = shortest_unconditional_path
            except NetworkXNoPath:
                shortest_unconditional_path = []
                self.precomputed_path_dict[(source,target)] = shortest_unconditional_path
                for x in range(1,len(shortest_unconditional_path)-1):
                    z = shortest_unconditional_path[x:]
                    self.precomputed_path_dict[(z[1],target)] = z

        #step 2 check if this is also a path without the node of interest
        if v not in shortest_unconditional_path:
            return shortest_unconditional_path
        else: #now we have to find the shortest path in a subgraph without the node of interest

            try:
                shortest_conditional_path = self.precomputed_paths_by_hole_node[v][(source,target)]
                return shortest_conditional_path
            except KeyError:

                nodes_less_v = self.node_set - set([v])
                G_sub = self.G.subgraph(nodes_less_v)
                try:
                    shortest_conditional_path = nx.algorithms.shortest_path(G_sub,source,target)
                    #note that subpaths could also be cached as per above
                    self.precomputed_paths_by_hole_node[v][(source,target)] = shortest_conditional_path
                    return shortest_conditional_path
                except NetworkXNoPath:
                    self.precomputed_paths_by_hole_node[v][(source,target)] = []
                    return []

    #wrapper function to get the length. no path = infinite length
    def shortest_path_length_node_source_target(self,v,source,target):
        z = len(self.shortest_path_node_source_target(v,source,target))
        if z == 0:
            return(float('inf'))
        else:
            return z - 1




    def is_mk_observer(self,v,m,k):



        source_nodes = list(self.G.predecessors(v))


        if len(source_nodes) < k: #if you have fewer than k, then you can't hear from at least k
            return False

        if (len(source_nodes) == 1) and k==1 and m==1: #special case, to ensure that a node with one input is a 1,1 observer
            return True

        max_k_found = False
        clique_dict = defaultdict(list) #this will get used to look for cliques

        #efficient_pairs makes sure that cliques are found and early termination happens
        #as soon as possible
        for source_a,source_b in self.efficient_pairs(source_nodes):

            a_path_length = self.shortest_path_length_node_source_target(v,source_a,source_b)
            b_path_length = self.shortest_path_length_node_source_target(v,source_b,source_a)




            if (a_path_length<m) or (b_path_length<m): #if shortest path is too short, keep looking
                pass

            else:  # now we do the clique updating
                #first each pair trivially forms a clique
                #pairs are unique so we don't have to double-check as we go (i hope!)

                #first, this check is needed because if k<=2 then any hit at all satisfies it and it's time to go home
                if k<=2:
                    return True

                trivial_clique = set([source_a,source_b])
                clique_dict[source_a].append(trivial_clique)
                clique_dict[source_b].append(trivial_clique)


            #now, for each pair of cliques for the two nodes, we have a new clique iff:
            #each clique has the same size m
            #the set containing the union of nodes from the two pairs of m-sized cliques is size m+1
            #so check the cliques in the nodes connected by the new pair
                for a,b in itertools.product(clique_dict[source_a],clique_dict[source_b]):
                    lena = len(a)
                    lenb = len(b)
                    if lena!=lenb:
                        pass
                    #avoid double counting
                    #thogh you can probably do this faster by not adding the trivial clique until later?
                    elif (a==trivial_clique) or (b==trivial_clique):
                        pass
                    else:
                        node_union = a | b
                        lenu = len(node_union)
                        if lenu == (lena + 1):
                            if lenu>=k:  #early termination
                                max_k_found = True
                                return max_k_found
                            else:
                                for node in node_union:
                                    clique_dict[node].append(node_union)



        return max_k_found


    def S(self,v):
        possibilities = sorted([(m*k,m,k) for m,k in itertools.product(range(self.min_m,self.max_m+1),range(self.min_k,self.max_k+1))],reverse=True)
        for mk,m,k in possibilities:
            mk_observer = self.is_mk_observer(v,m,k)
            if mk_observer:
                return mk
            else:
                pass

        return 0


    def D(self,v):
        topics = set()

        source_nodes = self.G.predecessors(v)

        for s in source_nodes:
            s_topic = self.G.nodes[s][self.node_key]
            if type(s_topic) == set:
                topics.update(s_topic)
            else:
                topics.add(s_topic)




        return len(topics)




    def pi(self,v):
        return  self.D(v) * self.S(v)

    def h_measure(self,v,max_h=6):

        for h in range(max_h,0,-1):
            if self.is_mk_observer(v,h,h):
                return h

        return 0
