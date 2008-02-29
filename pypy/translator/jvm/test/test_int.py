import py
from pypy.translator.jvm.test.runtest import JvmTest
from pypy.rpython.test.test_rint import BaseTestRint

# ====> ../../../rpython/test/test_rint.py

class TestJvmInt(JvmTest, BaseTestRint):
    def test_char_constant(self):
        def dummyfn(i):
            return chr(i)
        res = self.interpret(dummyfn, [ord(' ')])
        assert res == ' '
        res = self.interpret(dummyfn, [ord('a')])
        assert res == 'a'

    def test_rarithmetic(self):
        pass # does this make more sense in jvm
    
    div_mod_iteration_count = 20
