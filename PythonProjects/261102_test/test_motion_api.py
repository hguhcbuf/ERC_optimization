"""Offline PLC handshake tests. No ADS connection or machine motion."""
import importlib
import sys
import threading
import types
import unittest
from unittest.mock import patch

# Test double installed only for module import; never open a real connection.
sys.modules.setdefault('pyads', types.SimpleNamespace(PORT_TC3PLC1=851, symbol=object, Connection=object))
import PLC_motion_controller_mod as api
from PLC_communication import GCODE_BASE_PATH
from Test_Q1_motion import M, U, STATUS_TAGS


class FakePLC:
    def __init__(self, mode=2, complete=True, accept=True):
        self.data = dict.fromkeys(STATUS_TAGS, False)
        self.data.update({U+'OpMode': mode, M+'nMotorControlState': {0:0,1:100,2:200}[mode],
                          U+'GCodeBasePath': GCODE_BASE_PATH,
                          M+'motQ1.NcToPlc.AxisId': 4, M+'bQ1Linked': True,
                          M+'fb_Q1Status.Valid': True, M+'fb_Q1Status.StandStill': True,
                          M+'bQ1ManualAllowed': True, U+'RunningGCodeName': '',
                          M+'fQ1ActPos': 0.0})
        self.writes = []
        self.complete, self.accept = complete, accept
        self.closed = False

    def read(self, name):
        return self.data.get(name, False)

    def write(self, name, value):
        self.writes.append((name, value))
        self.data[name] = value
        if name == U+'Q1Enable':
            self.data[M+'fb_Q1Power.Status'] = value
            self.data[M+'bQ1Ready'] = value
        if name == U+'Q1UseInGCode':
            self.data[M+'bQ1UseLatched'] = value
        if name == U+'OpMode':
            self.data[M+'nMotorControlState'] = 200
        if name == U+'SingleGCodeTRG' and value and self.accept:
            self.data[U+'SingleGCodeTRG'] = False
            self.data[U+'RunningGCodeName'] = self.data['HMIVar.CodeName']
            self.data[M+'bBusy'] = not self.complete
            self.data[M+'nMotorControlState'] = 200 if self.complete else 213

    def close(self):
        self.closed = True


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.io = FakePLC()
        api._io = self.io
        api._operation_lock = threading.Lock()

    def tearDown(self):
        api._io = None

    def test_fast_xyz_and_repeated_same_file(self):
        self.io.data[M+'fb_Q1Power.Error'] = True
        self.io.data[M+'motQ1.NcToPlc.AxisId'] = 0
        self.io.data[M+'bQ1Linked'] = False
        for _ in range(2):
            self.assertTrue(api.run_gcode('test.nc'))
        self.assertNotIn((U+'Q1Enable', True), self.io.writes)
        self.assertEqual(self.io.data['HMIVar.CodeName'], '\\\\test.nc')
        self.assertFalse(self.io.data[U+'ContinueGCode'])
        self.assertEqual(self.io.data[U+'Auto_CodeType'], 0)

    def test_q1_enabled_before_trigger_and_deselected_after(self):
        self.assertTrue(api.run_gcode('q1_test.nc', use_q1=True))
        w = self.io.writes
        self.assertLess(w.index((U+'Q1Enable', True)), w.index((U+'SingleGCodeTRG', True)))
        self.assertEqual(w[-1], (U+'Q1UseInGCode', False))
        self.assertTrue(self.io.data[U+'Q1Enable'])

    def test_q1_fault_rejected_before_writes(self):
        self.io.data[M+'fb_Q1Power.Error'] = True
        with self.assertRaises(RuntimeError): api.run_gcode(use_q1=True)
        self.assertEqual(self.io.writes, [])

    def test_queue_estop_busy_rejected(self):
        for tag in (U+'GCodeNameQueue.Count', U+'bESTOP', M+'bBusy', M+'bQ1Reserved', U+'SingleGCodeTRG'):
            self.io.data[tag] = True
            with self.assertRaises(RuntimeError): api.run_gcode()
            self.assertEqual(self.io.writes, [])
            self.io.data[tag] = False

    def test_mode_entry_needs_explicit_permission(self):
        self.io.data[U+'OpMode'], self.io.data[M+'nMotorControlState'] = 0, 0
        with self.assertRaises(RuntimeError): api.run_gcode()
        self.assertEqual(self.io.writes, [])
        self.assertTrue(api.run_gcode(allow_xyz_init=True))

    def test_bad_path_and_filename_no_writes(self):
        for filename in ('../test.nc', 'C:\\test.nc', '', 'test.txt'):
            with self.assertRaises(Exception): api.run_gcode(filename)
        self.io.data[U+'GCodeBasePath'] = 'C:\\other'
        with self.assertRaises(RuntimeError): api.run_gcode()
        self.assertEqual(self.io.writes, [])

    def test_doubled_plc_separators_are_accepted(self):
        self.io.data[U+'GCodeBasePath'] = GCODE_BASE_PATH.replace('\\', '\\\\')
        self.assertTrue(api.run_gcode())

    def test_completion_timeout_requests_stop(self):
        self.io.complete = False
        with self.assertRaises(TimeoutError): api.run_gcode(timeout=.001)
        self.assertIn((U+'bESTOP', True), self.io.writes)
        self.assertNotIn((U+'bESTOP', False), self.io.writes)

    def test_ack_timeout_requests_stop(self):
        self.io.accept = False
        with patch('Test_Q1_motion.time.monotonic', side_effect=[0,0,10]):
            with self.assertRaises(TimeoutError): api.run_gcode()
        self.assertIn((U+'bESTOP', True), self.io.writes)

    def test_nonfinite_and_invalid_jog_no_writes(self):
        for value in (float('nan'), float('inf'), 0, -1):
            with self.assertRaises(ValueError): api.run_gcode(timeout=value)
            with self.assertRaises(ValueError): api.jog_q1(velocity=value, seconds=.1)
        with self.assertRaises(ValueError): api.jog_q1(velocity=.01, seconds=3)
        self.assertEqual(self.io.writes, [])

    def test_jog_finishes_with_zero_button(self):
        self.io.data[U+'OpMode'], self.io.data[M+'nMotorControlState'] = 0, 0
        self.assertTrue(api.jog_q1(velocity=.01, seconds=.001))
        self.assertEqual(self.io.data[U+'Q1JogButton'], 0)
        self.assertTrue(self.io.data[U+'Q1Enable'])

    def test_import_set_height_no_motion(self):
        importlib.import_module('Set_height')
        self.assertEqual(self.io.writes, [])

    def test_concurrent_operation_rejected(self):
        api._operation_lock.acquire()
        with self.assertRaises(RuntimeError): api.run_gcode()
        api._operation_lock.release()
        self.assertEqual(self.io.writes, [])

    def test_legacy_function_waits_for_completion(self):
        self.assertTrue(api.run_gcode_file('test.nc', start_pulse=.1))


if __name__ == '__main__':
    unittest.main()
