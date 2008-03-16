from pypy.lang.gameboy.cpu import CPU, Register, DoubleRegister
import pypy.lang.gameboy.constants

def get_cpu():
    return CPU([None]*256, None)

# ------------------------------------------------------------
# TEST REGISTER
def test_register_constructor():
    register = Register(get_cpu())
    assert register.get() == 0
    value = 10
    register = Register(get_cpu(), value)
    assert register.get() == value
    
def test_register():
    register = Register(get_cpu())
    value = 2
    oldCycles = register.cpu.cycles
    register.set(value)
    assert register.get() == value
    assert oldCycles-register.cpu.cycles == 1
    
# ------------------------------------------------------------
# TEST DOUBLE REGISTER

def test_double_register_constructor():
    register = DoubleRegister(get_cpu())
    assert register.get() == 0
    assert register.getHi() == 0
    assert register.getLo() == 0
    value = 0x1234
    register = DoubleRegister(get_cpu(), value)
    assert register.get() == value
    
def test_double_register():
    register = DoubleRegister(get_cpu())
    value = 0x1234
    oldCycles = register.cpu.cycles
    register.set(value)
    assert oldCycles-register.cpu.cycles == 1
    assert register.get() == value
    
def test_double_register_hilo():
    register = DoubleRegister(get_cpu())
    value = 0x1234
    valueHi = 0x12
    valueLo = 0x34
    oldCycles = register.cpu.cycles
    register.set(valueHi, valueLo)
    assert oldCycles-register.cpu.cycles == 2
    assert register.getHi() == valueHi
    assert register.getLo() == valueLo
    assert register.get() == value
    
    valueHi = 0x56
    oldCycles = register.cpu.cycles
    register.setHi(valueHi)
    assert oldCycles-register.cpu.cycles == 1
    assert register.getHi() == valueHi
    assert register.getLo() == valueLo
    
    valueLo = 0x78
    oldCycles = register.cpu.cycles
    register.setLo(valueLo)
    assert oldCycles-register.cpu.cycles == 1
    assert register.getHi() == valueHi
    assert register.getLo() == valueLo
    
    
def test_double_register_methods():
    value = 0x1234
    register = DoubleRegister(get_cpu(), value)
    
    oldCycles = register.cpu.cycles
    register.inc()
    assert oldCycles-register.cpu.cycles == 2
    assert register.get() == value+1
    
    oldCycles = register.cpu.cycles
    register.dec()
    assert oldCycles-register.cpu.cycles == 2
    assert register.get() == value
    
    addValue = 0x1001
    oldCycles = register.cpu.cycles
    register.add(addValue)
    assert oldCycles-register.cpu.cycles == 3
    assert register.get() == value+addValue
    
    
# ------------------------------------------------------------
# TEST CPU

def test_getters():
    cpu = get_cpu()
    assert cpu.getA() == constants.RESET_A
    assert cpu.getF() == constants.RESET_F
    assert cpu.bc.get() == constants.RESET_BC
    assert cpu.de.get() == constants.RESET_DE
    assert cpu.pc.get() == constants.RESET_PC
    assert cpu.sp.get() == constants.RESET_SP
    
    
OPCODE_CYCLES = [
    (0x00, 1),
    (0x08, 5),
    (0x10, 0),
    (0x18, 3),
    (0x01, 0x31, 0x10, 3)
]

def test_cycles():
    cpu = get_cpu()
    for entry in OPCODE_CYCLES:
        if len(entry) == 2:
            cycletest(cpu, entry[0], entry[1])
        elif len(entry) == 4:
            for opCode in range(entry[0], entry[1], entry[2]):
                cycletest(cpu, opCode, entry[3])
                
        
        
def cycletest(cpu, opCode, cycles):
    oldCycles = cpu.cycles
    cpu.execute(opCode)
    assert oldCycles - cpu.cycles == cycles
            
