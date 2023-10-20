# import schemdraw
# from schemdraw import flow

# with schemdraw.Drawing().config(inches_per_unit=0.5) as d:
#     d += flow.Start(w=5).label('Game(N, run=True)')
#     d += flow.Arrow().down()
#     d += flow.Process().label('__init__')
#     d += flow.Arrow().down()
#     d += flow.Process().label('run')

#     d.save('./log/scheme.png', transparent=False, dpi=1000)

import pydot

graph = pydot.Dot(graph_type='digraph')

init_node = pydot.Node(r'$Game(N, run=True)$')
run_node = pydot.Node('run()')

graph.add_node(init_node)
graph.add_node(run_node)
graph.add_edge(pydot.Edge(init_node, run_node))

graph.write_svg('./log/flowchart.svg')