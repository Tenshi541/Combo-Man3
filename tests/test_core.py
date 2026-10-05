import unittest
from core import Timeline

class TimelineTests(unittest.TestCase):
    def test_simultaneous_press_hold_release(self):
        t=Timeline()
        t.update(4, {'B0','B1'}, .01)
        t.update(4, {'B0','B1'}, .02)
        self.assertEqual(len(t.events),2)
        t.update(4, set(), .06)
        self.assertEqual([e['down'] for e in t.events],[True,True,False,False])
        self.assertEqual(t.frame(.06,60)-t.frame(.01,60),3)

    def test_disconnect_releases_only_removed_device(self):
        t=Timeline()
        t.update(1,{'B0'},0)
        t.update(2,{'B1'},0)
        t.remove(1,.1)
        self.assertNotIn(1,t.active)
        self.assertEqual(t.active[2],{'B1'})
        self.assertFalse(t.events[-1]['down'])

    def test_bounded_history_and_frame_boundaries(self):
        t=Timeline(capacity=2)
        for i in range(5):t.update(0,{'B0'} if i%2==0 else set(),i/60)
        self.assertEqual(len(t.events),2)
        self.assertEqual(t.sequence,5)
        self.assertEqual(t.frame(1/60,60),1)
        self.assertEqual(t.frame(1/120,60),0)
        with self.assertRaises(ValueError):t.frame(1,0)

if __name__=='__main__':unittest.main()
