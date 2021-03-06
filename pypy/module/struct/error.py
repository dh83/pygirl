from pypy.interpreter.error import OperationError

class StructError(Exception):
    "Interp-level error that gets mapped to an app-level struct.error."

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def at_applevel(self, space):
        w_module = space.getbuiltinmodule('struct')
        w_error = space.getattr(w_module, space.wrap('error'))
        return OperationError(w_error, space.wrap(self.msg))
