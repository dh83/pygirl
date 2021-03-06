from pypy.objspace.std.objspace import *
from pypy.objspace.std.stdtypedef import *

##class TestSpecialMultimethodCode(testit.TestCase):

##    def setUp(self):
##        self.space = testit.objspace('std')

##    def tearDown(self):
##        pass

##    def test_int_sub(self):
##        w = self.space.wrap
##        for i in range(2):
##            meth = SpecialMultimethodCode(self.space.sub.multimethod, 
##                                          self.space.w_int.__class__, i)
##            self.assertEqual(meth.slice().is_empty(), False)
##            # test int.__sub__ and int.__rsub__
##            self.assertEqual_w(meth.eval_code(self.space, None,
##                                              w({'x1': 5, 'x2': 7})),
##                               w(-2))
##            self.assertEqual_w(meth.eval_code(self.space, None,
##                                              w({'x1': 5, 'x2': 7.1})),
##                               self.space.w_NotImplemented)
##            self.assertEqual_w(meth.eval_code(self.space, None,
##                                              w({'x1': 5.5, 'x2': 7})),
##                               self.space.w_NotImplemented)

##    def test_empty_inplace_add(self):
##        for i in range(2):
##            meth = SpecialMultimethodCode(self.space.inplace_add.multimethod,
##                                          self.space.w_int.__class__, i)
##            self.assertEqual(meth.slice().is_empty(), True)

##    def test_float_sub(self):
##        w = self.space.wrap
##        w(1.5)   # force floatobject imported
##        for i in range(2):
##            meth = SpecialMultimethodCode(self.space.sub.multimethod,
##                                          self.space.w_float.__class__, i)
##            self.assertEqual(meth.slice().is_empty(), False)
##            # test float.__sub__ and float.__rsub__

##            # some of these tests are pointless for Python because
##            # float.__(r)sub__ should not accept an int as first argument
##            self.assertEqual_w(meth.eval_code(self.space, None,
##                                              w({'x1': 5, 'x2': 7})),
##                               w(-2.0))
##            self.assertEqual_w(meth.eval_code(self.space, None,
##                                              w({'x1': 5, 'x2': 7.5})),
##                               w(-2.5))
##            self.assertEqual_w(meth.eval_code(self.space, None,
##                                              w({'x1': 5.5, 'x2': 7})),
##                               w(-1.5))


class TestTypeObject:

    def test_not_acceptable_as_base_class(self):
        space = self.space
        class W_Stuff(W_Object):
            pass
        def descr__new__(space, w_subtype):
            return space.allocate_instance(W_Stuff, w_subtype)
        W_Stuff.typedef = StdTypeDef("stuff",
                                     __new__ = newmethod(descr__new__))
        W_Stuff.typedef.acceptable_as_base_class = False
        w_stufftype = space.gettypeobject(W_Stuff.typedef)
        space.appexec([w_stufftype], """(stufftype):
            x = stufftype.__new__(stufftype)
            assert type(x) is stufftype
            raises(TypeError, stufftype.__new__)
            raises(TypeError, stufftype.__new__, int)
            raises(TypeError, stufftype.__new__, 42)
            raises(TypeError, stufftype.__new__, stufftype, 511)
            raises(TypeError, type, 'sub', (stufftype,), {})
        """)


class AppTestTypeObject:
    def test_bases(self):
        assert int.__bases__ == (object,)
        class X:
            __metaclass__ = type
        assert X.__bases__ ==  (object,)
        class Y(X): pass
        assert Y.__bases__ ==  (X,)
        class Z(Y,X): pass
        assert Z.__bases__ ==  (Y, X)

        Z.__bases__ = (X,)
        #print Z.__bases__
        assert Z.__bases__ == (X,)

    def test_mutable_bases(self):
        # from CPython's test_descr
        class C(object):
            pass
        class C2(object):
            def __getattribute__(self, attr):
                if attr == 'a':
                    return 2
                else:
                    return super(C2, self).__getattribute__(attr)
            def meth(self):
                return 1
        class D(C):
            pass
        class E(D):
            pass
        d = D()
        e = E()
        D.__bases__ = (C,)
        D.__bases__ = (C2,)
        #import pdb; pdb.set_trace()
        assert d.meth() == 1
        assert e.meth() == 1
        assert d.a == 2
        assert e.a == 2
        assert C2.__subclasses__() == [D]

        # stuff that shouldn't:
        class L(list):
            pass

        try:
            L.__bases__ = (dict,)
        except TypeError:
            pass
        else:
            assert 0, "shouldn't turn list subclass into dict subclass"

        try:
            list.__bases__ = (dict,)
        except TypeError:
            pass
        else:
            assert 0, "shouldn't be able to assign to list.__bases__"

        try:
            D.__bases__ = (C2, list)
        except TypeError:
            pass
        else:
            assert 0, "best_base calculation found wanting"

        try:
            del D.__bases__
        except (TypeError, AttributeError):
            pass
        else:
            assert 0, "shouldn't be able to delete .__bases__"

        try:
            D.__bases__ = ()
        except TypeError, msg:
            if str(msg) == "a new-style class can't have only classic bases":
                assert 0, "wrong error message for .__bases__ = ()"
        else:
            assert 0, "shouldn't be able to set .__bases__ to ()"

        try:
            D.__bases__ = (D,)
        except TypeError:
            pass
        else:
            # actually, we'll have crashed by here...
            assert 0, "shouldn't be able to create inheritance cycles"

        try:
            D.__bases__ = (C, C)
        except TypeError:
            pass
        else:
            assert 0, "didn't detect repeated base classes"

        try:
            D.__bases__ = (E,)
        except TypeError:
            pass
        else:
            assert 0, "shouldn't be able to create inheritance cycles"

        # let's throw a classic class into the mix:
        try:
            class Classic:
                __metaclass__ = _classobj
                def meth2(self):
                    return 3
        except NameError:
            class Classic:
                def meth2(self):
                    return 3

        D.__bases__ = (C, Classic)

        assert d.meth2() == 3
        assert e.meth2() == 3
        try:
            d.a
        except AttributeError:
            pass
        else:
            assert 0, "attribute should have vanished"

        try:
            D.__bases__ = (Classic,)
        except TypeError:
            pass
        else:
            assert 0, "new-style class must have a new-style base"

    def test_mutable_bases_with_failing_mro(self):
        class WorkOnce(type):
            def __new__(self, name, bases, ns):
                self.flag = 0
                return super(WorkOnce, self).__new__(WorkOnce, name, bases, ns)
            def mro(instance):
                if instance.flag > 0:
                    raise RuntimeError, "bozo"
                else:
                    instance.flag += 1
                    return type.mro(instance)

        class WorkAlways(type):
            def mro(self):
                # this is here to make sure that .mro()s aren't called
                # with an exception set (which was possible at one point).
                # An error message will be printed in a debug build.
                # What's a good way to test for this?
                return type.mro(self)

        class C(object):
            pass

        class C2(object):
            pass

        class D(C):
            pass

        class E(D):
            pass

        class F(D):
            __metaclass__ = WorkOnce

        class G(D):
            __metaclass__ = WorkAlways

        # Immediate subclasses have their mro's adjusted in alphabetical
        # order, so E's will get adjusted before adjusting F's fails.  We
        # check here that E's gets restored.

        E_mro_before = E.__mro__
        D_mro_before = D.__mro__

        try:
            D.__bases__ = (C2,)
        except RuntimeError:
            assert D.__mro__ == D_mro_before
            assert E.__mro__ == E_mro_before
        else:
            assert 0, "exception not propagated"

    def test_mutable_bases_catch_mro_conflict(self):
        class A(object):
            pass

        class B(object):
            pass

        class C(A, B):
            pass

        class D(A, B):
            pass

        class E(C, D):
            pass

        try:
            C.__bases__ = (B, A)
        except TypeError:
            pass
        else:
            raise TestFailed, "didn't catch MRO conflict"

    def test_builtin_add(self):
        x = 5
        assert x.__add__(6) == 11
        x = 3.5
        assert x.__add__(2) == 5.5
        assert x.__add__(2.0) == 5.5

    def test_builtin_call(self):
        def f(*args):
            return args
        assert f.__call__() == ()
        assert f.__call__(5) == (5,)
        assert f.__call__("hello", "world") == ("hello", "world")

    def test_builtin_call_kwds(self):
        def f(*args, **kwds):
            return args, kwds
        assert f.__call__() == ((), {})
        assert f.__call__("hello", "world") == (("hello", "world"), {})
        assert f.__call__(5, bla=6) == ((5,), {"bla": 6})
        assert f.__call__(a=1, b=2, c=3) == ((), {"a": 1, "b": 2,
                                                           "c": 3})

    def test_multipleinheritance_fail(self):
        try:
            class A(int, dict):
                pass
        except TypeError:
            pass
        else:
            raise AssertionError, "this multiple inheritance should fail"

    def test_outer_metaclass(self):
        class OuterMetaClass(type):
            pass

        class HasOuterMetaclass(object):
            __metaclass__ = OuterMetaClass

        assert type(HasOuterMetaclass) == OuterMetaClass
        assert type(HasOuterMetaclass) == HasOuterMetaclass.__metaclass__

    def test_inner_metaclass(self):
        class HasInnerMetaclass(object):
            class __metaclass__(type):
                pass

        assert type(HasInnerMetaclass) == HasInnerMetaclass.__metaclass__

    def test_implicit_metaclass(self):
        global __metaclass__
        try:
            old_metaclass = __metaclass__
            has_old_metaclass = True
        except NameError:
            has_old_metaclass = False
            
        class __metaclass__(type):
            pass

        class HasImplicitMetaclass:
            pass

        try:
            assert type(HasImplicitMetaclass) == __metaclass__
        finally:
            if has_old_metaclass:
                __metaclass__ = old_metaclass
            else:
                del __metaclass__


    def test_mro(self):
        class A_mro(object):
            a = 1

        class B_mro(A_mro):
            b = 1
            class __metaclass__(type):
                def mro(self):
                    return [self, object]

        assert B_mro.__bases__ == (A_mro,)
        assert B_mro.__mro__ == (B_mro, object)
        assert B_mro.mro() == [B_mro, object]
        assert B_mro.b == 1
        assert B_mro().b == 1
        assert getattr(B_mro, 'a', None) == None
        assert getattr(B_mro(), 'a', None) == None

    def test_abstract_mro(self):
        class A1:
            __metaclass__ = _classobj
        class B1(A1):
            pass
        class C1(A1):
            pass
        class D1(B1, C1):
            pass
        class E1(D1, object):
            __metaclass__ = type
        # old-style MRO in the classical part of the parent hierarchy
        assert E1.__mro__ == (E1, D1, B1, A1, C1, object)

    def test_nodoc(self):
        class NoDoc(object):
            pass

        try:
            assert NoDoc.__doc__ == None
        except AttributeError:
            raise AssertionError, "__doc__ missing!"

    def test_explicitdoc(self):
        class ExplicitDoc(object):
            __doc__ = 'foo'

        assert ExplicitDoc.__doc__ == 'foo'

    def test_implicitdoc(self):
        class ImplicitDoc(object):
            "foo"

        assert ImplicitDoc.__doc__ == 'foo'

    def test_immutabledoc(self):
        class ImmutableDoc(object):
            "foo"

        try:
            ImmutableDoc.__doc__ = "bar"
        except TypeError:
            pass
        except AttributeError:
            # XXX - Python raises TypeError for several descriptors,
            #       we always raise AttributeError.
            pass
        else:
            raise AssertionError, '__doc__ should not be writable'

        assert ImmutableDoc.__doc__ == 'foo'

    def test_metaclass_conflict(self):

        class T1(type):
            pass
        class T2(type):
            pass
        class D1:
            __metaclass__ = T1
        class D2:
            __metaclass__ = T2
        def conflict():
            class C(D1,D2):
                pass
        raises(TypeError, conflict)

    def test_metaclass_choice(self):
        events = []
        
        class T1(type):
            def __new__(*args):
                events.append(args)
                return type.__new__(*args)

        class D1:
            __metaclass__ = T1

        class C(D1):
            pass

        class F(object):
            pass

        class G(F,D1):
            pass

        assert len(events) == 3
        assert type(D1) is T1
        assert type(C) is T1
        assert type(G) is T1
    
    def test_descr_typecheck(self):
        raises(TypeError,type.__dict__['__name__'].__get__,1)
        raises(TypeError,type.__dict__['__mro__'].__get__,1)

    def test_slots_simple(self):
        class A(object):
            __slots__ = ('x',)
        a = A()
        raises(AttributeError, getattr, a, 'x')
        a.x = 1
        assert a.x == 1
        assert A.__dict__['x'].__get__(a) == 1
        del a.x
        raises(AttributeError, getattr, a, 'x')
        class B(A):
            pass
        b = B()
        raises(AttributeError, getattr, b, 'x')
        b.x = 1
        assert b.x == 1
        assert A.__dict__['x'].__get__(b) == 1
        del b.x
        raises(AttributeError, getattr, b, 'x')
        class Z(object):
            pass
        z = Z()
        raises(TypeError, A.__dict__['x'].__get__, z)
        raises(TypeError, A.__dict__['x'].__set__, z, 1)
        raises(TypeError, A.__dict__['x'].__delete__, z)

    def test_slot_mangling(self):
        class A(object):
            __slots__ = ('x', '__x','__xxx__','__','__dict__')
        a = A()
        assert '__dict__' in A.__dict__
        assert '__' in A.__dict__
        assert '__xxx__' in A.__dict__
        assert 'x' in A.__dict__
        assert '_A__x' in A.__dict__
        a.x = 1
        a._A__x = 2
        a.__xxx__ = 3
        a.__ = 4
        assert a.x == 1
        assert a._A__x == 2
        assert a.__xxx__ == 3
        assert a.__ == 4
        assert a.__dict__ == {}

    def test_repr(self):
        globals()['__name__'] = 'a'
        class A(object):
            pass
        assert repr(A) == "<class 'a.A'>"
        assert repr(type(type)) == "<type 'type'>" 
        assert repr(complex) == "<type 'complex'>"
        assert repr(property) == "<type 'property'>"
        
    def test_invalid_mro(self):
        class A(object):
            pass
        raises(TypeError, "class B(A, A): pass")
        class C(A):
            pass
        raises(TypeError, "class D(A, C): pass")

    def test_user_defined_mro_cls_access(self):
        d = []
        class T(type):
            def mro(cls):
                d.append(cls.__dict__)
                return type.mro(cls)
        class C:
            __metaclass__ = T
        assert d
        assert sorted(d[0].keys()) == ['__dict__','__doc__','__metaclass__','__module__', '__weakref__']
        d = []
        class T(type):
            def mro(cls):
                try:
                    cls.x()
                except AttributeError:
                    d.append('miss')
                return type.mro(cls)
        class C:
            def x(cls):
                return 1
            x = classmethod(x)
            __metaclass__ = T
        assert d == ['miss']
        assert C.x() == 1

    def test_only_classic_bases_fails(self):
        class C:
            __metaclass__ = _classobj
        raises(TypeError, type, 'D', (C,), {})

    def test_set___class__(self):
        raises(TypeError, "1 .__class__ = int")
        raises(TypeError, "1 .__class__ = bool")
        class A(object):
            pass
        class B(object):
            pass
        a = A()
        a.__class__ = B
        assert a.__class__ == B
        class A(object):
            __slots__ = ('a',)
        class B(A):
            pass
        class C(B):
            pass
        class D(A):
            pass
        d = D()
        d.__class__ = C
        assert d.__class__ == C
        d.__class__ = B
        assert d.__class__ == B
        raises(TypeError, "d.__class__ = A")
        d.__class__ = C
        assert d.__class__ == C
        d.__class__ = D
        assert d.__class__ == D
        class AA(object):
            __slots__ = ('a',)
        aa = AA()
        raises(TypeError, "aa.__class__ = A")
        raises(TypeError, "aa.__class__ = object")
        class Z1(A):
            pass
        class Z2(A):
            __slots__ = ['__dict__', '__weakref__']
        z1 = Z1()
        z1.__class__ = Z2
        assert z1.__class__ == Z2
        z2 = Z2()
        z2.__class__ = Z1
        assert z2.__class__ == Z1
        
        class I(int):
            pass
        class F(float):
            pass
        f = F()
        raises(TypeError, "f.__class__ = I")
        i = I()
        raises(TypeError, "i.__class__ = F")
        raises(TypeError, "i.__class__ = int")

        class I2(int):
            pass
        class I3(I2):
            __slots__ = ['a']
        class I4(I3):
            pass

        i = I()
        
        i2 = I()
        i.__class__ = I2
        i2.__class__ = I
        assert i.__class__ ==  I2
        assert i2.__class__ == I
        
        i3 = I3()
        raises(TypeError, "i3.__class__ = I2")
        i3.__class__ = I4
        assert i3.__class__ == I4
        i3.__class__ = I3
        assert i3.__class__ == I3

        class X(object):
            pass
        class Y(object):
            __slots__ = ()
        raises(TypeError, "X().__class__ = Y")
        raises(TypeError, "Y().__class__ = X")

        raises(TypeError, "X().__class__ = object")
        raises(TypeError, "X().__class__ = 1")

        class Int(int): __slots__ = []

        raises(TypeError, "Int().__class__ = int")

    def test_name(self):
        class Abc(object):
            pass
        assert Abc.__name__ == 'Abc'
        Abc.__name__ = 'Def'
        assert Abc.__name__ == 'Def'
        raises(TypeError, "Abc.__name__ = 42")

    def test_class_variations(self):
        class A(object):
            pass
        assert '__dict__' in A.__dict__
        a = A()
        a.x = 3
        assert a.x == 3

        class A(object):
            __slots__ = ()
        assert '__dict__' not in A.__dict__
        a = A()
        raises(AttributeError, setattr, a, 'x', 3)

        class B(A):
            pass
        assert '__dict__' in B.__dict__
        b = B()
        b.x = 3
        assert b.x == 3

        import sys
        class A(type(sys)):
            pass
        assert '__dict__' not in A.__dict__
        a = A("a")
        a.x = 3
        assert a.x == 3

        class A(type(sys)):
            __slots__ = ()
        assert '__dict__' not in A.__dict__
        a = A("a")
        a.x = 3
        assert a.x == 3

        class B(A):
            pass
        assert '__dict__' not in B.__dict__
        b = B("b")
        b.x = 3
        assert b.x == 3

    def test_module(self):
        def f(): pass
        assert object.__module__ == '__builtin__'
        assert int.__module__ == '__builtin__'
        assert type.__module__ == '__builtin__'
        assert type(f).__module__ == '__builtin__'
        d = {'__name__': 'yay'}
        exec """class A(object):\n  pass\n""" in d
        A = d['A']
        assert A.__module__ == 'yay'

    def test_immutable_builtin(self):
        raises(TypeError, setattr, list, 'append', 42)
        raises(TypeError, setattr, list, 'foobar', 42)
        raises(TypeError, delattr, dict, 'keys')
        
