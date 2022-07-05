import os
import sys
import pm4py
import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.objects.petri_net.utils import reachability_graph
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.objects.stochastic_petri import ctmc
from pm4py.visualization.transition_system import visualizer as ts_visualizer
from pm4py.algo.discovery.inductive import algorithm as ind_miner
from pm4py.visualization.process_tree import visualizer as pt_vis
from pm4py.objects.conversion.process_tree import converter
from pm4py.algo.evaluation.replay_fitness import algorithm
from pm4py.algo.discovery.inductive.variants.im_clean.algorithm import Parameters
from pm4py.statistics.variants.log import get as variants_module
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.utils import petri_utils
import argparse
import time
sys.path.insert(0,'/usr/local/lib/python3.7/site-packages/')
import spot

class MarkovDecisionProcess:
    def __init__(self, initial_state, states, transitions):
        self.__initial_state = initial_state
        self.__states = states
        self.__transitions = transitions
    def to_hoa(self, threshold = 0.0):
        events = []
        map_evs = {}
        id = 0
        for t in self.__transitions:
            for ev in self.__transitions[t]:
                if '"' + ev.replace(' ', '_') + '"' not in events:
                    events.append('"' + ev.replace(' ', '_') + '"')
                    # if ev != self.__initial_state:
                    map_evs[ev] = id
                    id += 1
        res = '''HOA: v1
States: {n_states}
Start: 0
AP: {n_evs} {evs}
acc-name: Buchi
Acceptance: 1 Inf(0)
--BODY--
'''.format(n_states = len(self.__states), n_evs = len(events), evs = str.join(' ', events))
        my_map = {}
        my_map[self.__initial_state] = 0
        id = 1
        for s in self.__states:
            if s not in my_map:
                my_map[s] = id
                id = id + 1
        for s in self.__states:
            res += 'State: ' + str(my_map[s]) + ' {0}\n'
            for ev in self.__transitions[s]:
                if self.__transitions[s][ev][1] >= threshold:
                    res += '[' + str.join('&', [str(map_evs[ev]) if i == map_evs[ev] else ('!' + str(i)) for i in range(0, len(events))]) + '] ' + str(my_map[self.__transitions[s][ev][0]]) + '\n'
        res += '--END--'
        return res

def main(argv):
    parser = argparse.ArgumentParser(
        description='Python prototype of Hyper Predictive Runtime Verification through Process Mining',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('logs',
        help='log files to derive the model of the system [log1.xes, log2.xes, ..., logN.xes], where each log denotes the executions for a single thread',
        type=str)
    parser.add_argument('nthreads',
        help='number of threads to consider',
        type=int)
    args = parser.parse_args()
    n = args.nthreads
    new_net = PetriNet('new_net')
    # sources_sinks = []

    j = 0
    for log in args.logs.split(','):
        log = xes_importer.apply(log)
        net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
        places = set(net.places)
        # new_net = PetriNet('new')
        locks = set()
        # for i in range(0, n):
        i = 0
        transitions = set()
        for place in places:
            foundW = None
            foundR = None
            for arc in place.in_arcs:
                aux = str(arc).strip().replace(',', '').split('->')[0]
                if aux.startswith('(t)write_shared_data('):
                    foundW = aux[21:aux.find(')', 3)]
                if aux.startswith('(t)read_shared_data('):
                    foundR = aux[20:aux.find(')', 3)]
            if foundW:
                new_place = PetriNet.Place('criticalW' + foundW + 'criticalW' + place.name + 'criticalW' + str(i) + str(j))
            elif foundR:
                new_place = PetriNet.Place('criticalR' + foundR + 'criticalR' + place.name + str(i) + str(j))
            else:
                new_place = PetriNet.Place(place.name + str(i) + str(j))
            new_net.places.add(new_place)
            arcs = set(place.in_arcs)
            arcs.update(place.out_arcs)
            if arcs:
                arcs_str = str(arcs)
                arcs_str = arcs_str.replace('{', '').replace('}', '')
                arcs_arr = [s.strip().replace(',', '').split('->') for s in arcs_str.split(',')]
                arcs_arr = [(a[0], a[1]) for a in arcs_arr]
                for (a, b) in arcs_arr:
                    if a.startswith('(p)'):
                        new_transition = None
                        for t in transitions:
                            if t.name == b.replace('(t)', ''):
                                new_transition = t
                                break
                        if not new_transition:
                            if b.replace('(t)', '').startswith('tau'):
                                new_transition = PetriNet.Transition(b.replace('(t)', ''), None)
                            else:
                                new_transition = PetriNet.Transition(b.replace('(t)', ''), b.replace('(t)', ''))
                            transitions.add(new_transition)
                            new_net.transitions.add(new_transition)
                        petri_utils.add_arc_from_to(new_place, new_transition, new_net)
                    else:
                        new_transition = None
                        for t in transitions:
                            if t.name == a.replace('(t)', ''):
                                new_transition = t
                                break
                        if not new_transition:
                            if a.replace('(t)', '').startswith('tau'):
                                new_transition = PetriNet.Transition(a.replace('(t)', ''), None)
                            else:
                                new_transition = PetriNet.Transition(a.replace('(t)', ''), a.replace('(t)', ''))
                            transitions.add(new_transition)
                            new_net.transitions.add(new_transition)
                        if a.startswith('(t)lock'):
                            lock = a[a.find('(', 3)+1:a.find(')', 3)]
                            lock_place = PetriNet.Place(a + str(i))
                            new_net.places.add(lock_place)
                            petri_utils.add_arc_from_to(new_transition, lock_place, new_net)
                            tau_transition = PetriNet.Transition('tau_lock', None)
                            new_net.transitions.add(tau_transition)
                            petri_utils.add_arc_from_to(lock_place, tau_transition, new_net)
                            petri_utils.add_arc_from_to(tau_transition, new_place, new_net)
                            lock_aux = None
                            for l in locks:
                                if l.name == 'synchronise' + lock:
                                    lock_aux = l
                                    break
                            if not lock_aux:
                                lock_aux = PetriNet.Place('synchronise' + lock)
                                locks.add(lock_aux)
                                new_net.places.add(lock_aux)
                            petri_utils.add_arc_from_to(lock_aux, tau_transition, new_net)
                        elif a.startswith('(t)unlock'):
                             lock = a[a.find('(', 3)+1:a.find(')', 3)]
                             tau_transition = PetriNet.Transition('tau_lock', None)
                             new_net.transitions.add(tau_transition)
                             lock_place = PetriNet.Place(a + str(i))
                             new_net.places.add(lock_place)
                             petri_utils.add_arc_from_to(new_transition, lock_place, new_net)
                             petri_utils.add_arc_from_to(lock_place, tau_transition, new_net)
                             petri_utils.add_arc_from_to(tau_transition, new_place, new_net)
                             lock_aux = None
                             for l in locks:
                                 if l.name == 'synchronise' + lock:
                                     lock_aux = l
                                     break
                             if not lock_aux:
                                 lock_aux = PetriNet.Place('synchronise' + lock)
                                 locks.add(lock_aux)
                                 new_net.places.add(lock_aux)
                             petri_utils.add_arc_from_to(tau_transition, lock_aux, new_net)
                        else:
                            petri_utils.add_arc_from_to(new_transition, new_place, new_net)

        # new_source = PetriNet.Place('new_source' + str(j))
        # new_net.places.add(new_source)
        # source_transition = PetriNet.Transition('source_tau' + str(j), None)
        # new_net.transitions.add(source_transition)
        # petri_utils.add_arc_from_to(new_source, source_transition, new_net)
        #
        # for p in new_net.places:
        #     if p.name.startswith('new_source'):
        #         petri_utils.add_arc_from_to(source_transition, p, new_net)
        # pm4py.save_vis_petri_net(new_net, initial_marking, final_marking, "petri" + str(j) + ".png")
        # initial_marking = Marking()
        # initial_marking[new_source] = 1
        # locks_initial_tokens = {}
        # for t in new_net.transitions:
        #     if t.name and t.name.startswith('create_lock('):
        #         args = t.name[12:t.name.find(')')]
        #         args = args.split('-')
        #         lock = args[0]
        #         number_inside_lock = int(args[1])
        #         locks_initial_tokens[lock] = number_inside_lock
        # for p in new_net.places:
        #     if p.name.startswith('synchronise'):
        #         initial_marking[p] = locks_initial_tokens[p.name[11:]]
        # new_sink = PetriNet.Place('new_sink' + str(j))
        # new_net.places.add(new_sink)
        # sink_transition = PetriNet.Transition('sink_tau' + str(j), None)
        # new_net.transitions.add(sink_transition)
        # petri_utils.add_arc_from_to(sink_transition, new_sink, new_net)
        # for p in new_net.places:
        #     if p.name.startswith('sink'):
        #         petri_utils.add_arc_from_to(p, sink_transition, new_net)
        # final_marking = Marking()
        # final_marking[new_sink] = 1
        # for p in new_net.places:
        #     if p.name.startswith('synchronise'):
        #         final_marking[p] = 1
        # sources_sinks.append((new_source, new_sink))
        j = j + 1

    final_source = PetriNet.Place('final_source')
    new_net.places.add(final_source)
    final_sink = PetriNet.Place('final_sink')
    new_net.places.add(final_sink)
    final_source_transition = PetriNet.Transition('source_tau', None)
    new_net.transitions.add(final_source_transition)
    final_sink_transition = PetriNet.Transition('source_tau', None)
    new_net.transitions.add(final_sink_transition)
    petri_utils.add_arc_from_to(final_source, final_source_transition, new_net)
    petri_utils.add_arc_from_to(final_sink_transition, final_sink, new_net)
    for p in new_net.places:
        if p.name.startswith('source'):
            petri_utils.add_arc_from_to(final_source_transition, p, new_net)
        elif p.name.startswith('sink'):
            petri_utils.add_arc_from_to(p, final_sink_transition, new_net)
    initial_marking = Marking()
    initial_marking[final_source] = n
    final_marking = Marking()
    final_marking[final_sink] = n

    locks_initial_tokens = {}
    for t in new_net.transitions:
        if t.name and t.name.startswith('create_lock('):
            args = t.name[12:t.name.find(')')]
            args = args.split('-')
            lock = args[0]
            number_inside_lock = int(args[1])
            locks_initial_tokens[lock] = number_inside_lock
    for p in new_net.places:
        if p.name.startswith('synchronise'):
            initial_marking[p] = locks_initial_tokens[p.name[11:]]

    pm4py.save_vis_petri_net(new_net, initial_marking, final_marking, "petri.png")
    pm4py.write_pnml(new_net, initial_marking, final_marking, "petri.pnml")
    for t in new_net.transitions:
        print(t.name)
    ts = reachability_graph.construct_reachability_graph(new_net, initial_marking)
    # gviz = ts_visualizer.apply(ts, parameters={ts_visualizer.Variants.VIEW_BASED.value.Parameters.FORMAT: "svg"})
    # ts_visualizer.view(gviz)
    for state in ts.states:
        critical_sections = set()
        # print(state)
        i = 0
        while True:
            j = state.name.find('criticalR', i)
            k = state.name.find('criticalR', j+1)
            if j == -1 or k == -1: break
            critical_sections.add(state.name[j+9:k])
            i = k+1
        i = 0
        while True:
            j = state.name.find('criticalW', i)
            k = state.name.find('criticalW', j+1)
            w = state.name.find('criticalW', k+1)
            if j == -1 or k == -1 or w == -1: break
            if state.name[j+9:k] in critical_sections or int(state.name[w+11]) > 1:
                print('Data race found on shared memory: ' + state.name[j+9:k])
                return
            critical_sections.add(state.name[j+9:k])
            i = k+1


if __name__ == '__main__':
    main(sys.argv)
