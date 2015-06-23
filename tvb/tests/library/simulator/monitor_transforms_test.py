# -*- coding: utf-8 -*-
#
#
#  TheVirtualBrain-Scientific Package. This package holds all simulators, and
# analysers necessary to run brain-simulations. You can use it stand alone or
# in conjunction with TheVirtualBrain-Framework Package. See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#   The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

import numpy

from tvb.tests.library import setup_test_console_env
setup_test_console_env()

from tvb.tests.library.base_testcase import BaseTestCase
from tvb.simulator.monitors import MonitorTransforms

from tvb.simulator import models, coupling, integrators, noise, simulator
from tvb.datatypes import connectivity
from tvb.simulator.monitors import Raw


class MonitorTransformsTests(BaseTestCase):

    def test_split(self):
        mt = MonitorTransforms('a,c', '1,2', delim=',')
        self.assertEqual(len(mt.pre), 2)
        self.assertEqual(len(mt.post), 2)
        mt = MonitorTransforms('a;c', 'exp(x);2.234')
        self.assertEqual(len(mt.pre), 2)
        self.assertEqual(len(mt.post), 2)

    def test_pre_1(self):
        mt = MonitorTransforms('a', 'b;c')
        self.assertEqual(len(mt.pre), 2)

    def test_post_1(self):
        mt = MonitorTransforms('a;b', 'c')
        self.assertEqual(len(mt.post), 2)

    def _shape_fail(self):
        MonitorTransforms('1,2,3', '2,3', delim=',')

    def test_shape_fail(self):
        self.assertRaises(Exception, self._shape_fail)

    def _syntax_fail(self):
        MonitorTransforms('a=3', '23.234')

    def test_syntax(self):
        mt = MonitorTransforms('a+b/c*f(a,b)', '23')
        self.assertRaises(SyntaxError, self._syntax_fail)

    def test_noop_post(self):
        mt = MonitorTransforms('a;b;c', '2.34*(pre+1.5);;')
        self.assertEqual(len(mt.post), 3)

    def _fail_noop_pre(self):
        MonitorTransforms(';;', ';;')

    def test_noop_pre_fail(self):
        self.assertRaises(SyntaxError, self._fail_noop_pre)

    def test_pre(self):
        state = numpy.r_[:4].reshape((1, -1, 1))
        # check expr correctly evaluated
        mt = MonitorTransforms('x0**2', '')
        out = mt.apply_pre(state)
        self.assertEqual(out[0, -1, 0], 9)
        # check correct shape
        n_expr = numpy.random.randint(5, 10)
        pre_expr = ';'.join([str(i) for i in range(n_expr)])
        mt = MonitorTransforms(pre_expr, '')
        out = mt.apply_pre(state)
        self.assertEqual(n_expr, out.shape[0])

    def test_post(self):
        state = numpy.tile(numpy.r_[:4], (2, 1)).reshape((2, -1, 1))
        state[1] *= 2
        # check expr eval correct
        mt = MonitorTransforms('0;0', 'mon;')
        _, out = mt.apply_post((0.0, state))
        self.assertEqual(3, out.flat[3])
        self.assertEqual(6, out.flat[7])
        mt = MonitorTransforms('0;0', 'mon;mon**2-1')
        _, out = mt.apply_post((0.0, state))
        self.assertEqual(3, out.flat[3])
        self.assertEqual(35, out.flat[7])
        # check correct shape
        n_expr = numpy.random.randint(5, 10)
        state = numpy.tile(numpy.r_[:4], (n_expr, 1)).reshape((n_expr, -1, 1))
        post_expr = ';'.join([str(i) for i in range(n_expr)])
        mt = MonitorTransforms('0', post_expr)
        _, out = mt.apply_post((0.0, state))
        self.assertEqual(n_expr, out.shape[0])


class MonitorTransformsInSimTest(BaseTestCase):

    def _gen_sim(self, *mons):
        sim = simulator.Simulator(
            model=models.Generic2dOscillator(),
            connectivity=connectivity.Connectivity(load_default=True),
            coupling=coupling.Linear(),
            integrator=integrators.EulerDeterministic(),
            monitors=mons)
        sim.configure()
        return sim

    def test_expr_pre(self):
        sim = self._gen_sim(Raw(pre_expr='V;W;V**2;W-V', post_expr=''))
        self.assertTrue(hasattr(sim.monitors[0], '_transforms'))
        ys = []
        for (t, y), in sim(simulation_length=5):
            ys.append(y)
        ys = numpy.array(ys)
        v, w, v2, wmv = ys.transpose((1, 0, 2, 3))
        self.assertTrue(numpy.allclose(v**2, v2))
        self.assertTrue(numpy.allclose(w-v, wmv))

    def test_expr_post(self):
        sim = self._gen_sim(Raw(pre_expr='V;W;V;W', post_expr=';;mon**2; exp(mon)'))
        self.assertTrue(hasattr(sim.monitors[0], '_transforms'))
        ys = []
        for (t, y), in sim(simulation_length=1):
            ys.append(y)
        ys = numpy.array(ys)
        v, w, v2, ew = ys.transpose((1, 0, 2, 3))
        self.assertTrue(numpy.allclose(v**2, v2))
        self.assertTrue(numpy.allclose(numpy.exp(w), ew))


if __name__ == '__main__':
    import unittest
    unittest.main()