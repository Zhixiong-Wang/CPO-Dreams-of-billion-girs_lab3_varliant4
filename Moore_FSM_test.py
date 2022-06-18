import unittest
from Moore_FSM import *


class StateMachineTest(unittest.TestCase):
    def test_convert_self_state(self):
        model = StateMachine("convert_self_state")
        model.input_function("A", latency=1)
        model.output_function("B", latency=1)
        tuber = model.add_function(
            "convert",
            lambda a: not a if isinstance(
                a,
                bool) else None)
        tuber.input("A", latency=1)
        tuber.output("B", latency=1)
        model.execute(
            source_incident("A", True, 0),
            source_incident("A", False, 5),
        )
        self.assertEqual(model.state_history, [
            (0, {'A': None}),
            (2, {'A': True}),
            (4, {'A': True, 'B': False}),
            (7, {'A': False, 'B': False}),
            (9, {'A': False, 'B': True}),
        ])
        self.assertListEqual(model.event_history, [
            incident(clock=2, node=tuber, var='A', val=True),
            incident(clock=4, node=None, var='B', val=False),
            incident(clock=7, node=tuber, var='A', val=False),
            incident(clock=9, node=None, var='B', val=True),
        ])

    def test_elevator(self):
        model = StateMachine("elevator")
        model.input_function("A_unoverload", latency=1)
        model.input_function("A_up", latency=1)
        model.output_function("D0_closeup", latency=1)
        model.output_function("D1_closedown", latency=1)
        model.output_function("D2_openstop", latency=1)

        def add_load(a, b):
            tuber = model.add_function("!{} -> {}".format(a, b),
                           lambda a: not a if isinstance(a, bool) else None)
            tuber.input(a, latency=1)
            tuber.output(b, latency=1)

        def add_convert(a, b, c):
            tuber = model.add_function(
                "{} and {} -> {}".format(
                    a, b, c), lambda a, b: a and b if isinstance(
                    a, bool) and isinstance(
                    b, bool) else None)
            tuber.input(a, 1)
            tuber.input(b, 1)
            tuber.output(c, 1)

        add_load("A_unoverload", "A_overload")
        add_load("A_up", "A_down")
        # True means not overloaded, rising
        # False is overload, down
        add_convert("A_unoverload", "A_up", "D0_closeup")
        add_convert("A_unoverload", "A_down", "D1_closedown")
        add_convert("A_overload", "A_up", "D2_openstop")
        add_convert("A_overload", "A_down", "D2_openstop")
        test_data = [({'A_up': None,
                       'A_unoverload': False},
                      {'D2_openstop': None,
                       'D2_openstop': None,
                       'D1_closedown': None,
                       'D0_closeup': None}),
                     ]
        for a, d in test_data:
            source_events = [source_incident(k, v, 0) for k, v in a.items()]
            actual = model.execute(*source_events)
            expect = {}
            expect.update(actual)
            expect.update(d)
            self.assertEqual(actual, expect)


class NodeTest(unittest.TestCase):
    def test_convert_self_state(self):
        tuber = Node(
            "convert_self_state",
            lambda a: not a if isinstance(
                a,
                bool) else None)
        tuber.input("A", 1)
        tuber.output("B", 1)
        test_data = [
            (False, True),
            (False, True),
            (None, None),
        ]
        for a, b in test_data:
            self.assertEqual(tuber.activate({"A": a}),
                             [source_incident("B", b, 1)])

    def test_add_convert(self):
        tuber = Node(
            "convert",
            lambda a,
            b: a and b if isinstance(
                a,
                bool) and isinstance(
                b,
                bool) else None)
        tuber.input("A", 1)
        tuber.input("B", 1)
        tuber.output("C", 1)
        test_data = [
            (None, False, None),
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (True, True, True),
        ]
        for a, b, c in test_data:
            self.assertEqual(tuber.activate({"A": a, "B": b}), [
                             source_incident("C", c, 1)])

    def test_convert(self):
        def convert(a):
            if a == 0:
                return (0, 1)
            if a == 1:
                return (1, 0)
            return (None, None)

        tuber = Node("convert", convert)
        tuber.input("A", 1)
        tuber.output("D1", 1)
        tuber.output("D0", 2)
        test_data = [
            (0, 0, 1),
            (1, 1, 0),
            (None, None, None),
        ]
        for a, d1, d0 in test_data:
            self.assertEqual(tuber.activate({"A": a}),
                             [source_incident(
                "D1", d1, 1), source_incident("D0", d0, 2)])


if __name__ == '__main__':
    unittest.main()
