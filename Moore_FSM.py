from collections import OrderedDict, namedtuple
import copy

incident = namedtuple("incident", "clock node var val")
source_incident = namedtuple("source_incident", "var val latency")


class StateMachine(object):

    def __init__(self, name="anonymous"):
        self.name = name
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.nodes = []
        self.state_history = []
        self.event_history = []

    def input_function(self, name, latency=1):

        self.inputs[name] = latency

    def output_function(self, name, latency=1):

        self.outputs[name] = latency

    def add_function(self, name, function):

        node = Node(name, function)
        self.nodes.append(node)
        return node

    def _source_events2events(self, source_incidents, clock):
        incidents = []
        for se in source_incidents:
            source_latency = clock + se.latency + self.inputs.get(se.var, 0)
            if se.var in self.outputs:
                target_latency = self.outputs[se.var]
                incidents.append(incident(
                    clock=source_latency + target_latency,
                    node=None,
                    var=se.var,
                    val=se.val,
                ))
            for node in self.nodes:
                if se.var in node.inputs:
                    target_latency = node.inputs[se.var]
                    incidents.append(incident(
                        clock=clock + source_latency + target_latency,
                        node=node,
                        var=se.var,
                        val=se.val,
                    ))
        return incidents

    def _pop_next_event(self, incidents):

        assert len(incidents) > 0
        incidents = sorted(incidents, key=lambda e: e.clock)
        incident = incidents.pop(0)
        return incident, incidents

    def _state_initialize(self):
        env = {}
        for var in self.inputs:
            env[var] = None
        return env

    def execute(self, *source_incidents, limit=100, incidents=None):

        if incidents is None:
            incidents = []
        state = self._state_initialize()
        clock = 0
        self.state_history = [(clock, copy.copy(state))]
        while (len(incidents) > 0 or len(source_incidents) > 0) and limit > 0:
            limit -= 1
            new_incidents = self._source_events2events(source_incidents,
                                                       clock)
            incidents.extend(new_incidents)
            if len(incidents) == 0:
                break
            incident, incidents = self._pop_next_event(incidents)
            state[incident.var] = incident.val
            clock = incident.clock
            source_incidents = incident.node.activate(state) if incident.node else []
            self.state_history.append((clock, copy.copy(state)))
            self.event_history.append(incident)
        if limit == 0:
            print("limit reached")
        return state


class Node(object):

    def __init__(self, name, function):
        self.function = function
        self.name = name
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()

    def __repr__(self):
        return "{} inputs: {} outputs: {}".format(
            self.name, self.inputs, self.outputs)

    def input(self, name, latency=1):

        assert name not in self.inputs
        self.inputs[name] = latency

    def output(self, name, latency=1):

        assert name not in self.outputs
        self.outputs[name] = latency

    def activate(self, state):

        args = []
        for v in self.inputs:
            args.append(state.get(v, None))
        res = self.function(*args)
        if not isinstance(res, tuple):
            res = (res,)
        output_events = []
        for var, val in zip(self.outputs, res):
            latency = self.outputs[var]
            output_events.append(
                source_incident(var, val, latency)
            )
        return output_events
