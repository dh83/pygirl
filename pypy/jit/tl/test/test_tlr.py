from pypy.jit.tl import tlr
from pypy.jit.conftest import Benchmark

from pypy.translator.c.test import test_boehm


class TestTLR(test_boehm.AbstractGCTestClass):

    def test_square(self):
        assert tlr.interpret(tlr.SQUARE, 1) == 1
        assert tlr.interpret(tlr.SQUARE, 7) == 49
        assert tlr.interpret(tlr.SQUARE, 9) == 81

    def test_translate(self):
        def driver():
            bench = Benchmark()
            while 1:
                res = tlr.interpret(tlr.SQUARE, 1764)
                if bench.stop():
                    break
            return res

        fn = self.getcompiled(driver, [])
        res = fn()
        assert res == 1764 * 1764
