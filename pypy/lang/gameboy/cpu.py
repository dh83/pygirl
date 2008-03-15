"""
Mario GameBoy (TM) EmulatOR

Central Unit ProcessOR (Sharp LR35902 CPU)
"""
from pypy.lang.gameboy import constants


class Register(object):
	
	cpu = None
	
	def __init__(self, cpu, value=0):
		self.cpu = cpu
		self.set(value)
		
	def set(self, value):
		self.value = value
		self.cpu.cycles -= 1
		
	def get(self):
		return self.value
	
	
class DoubleRegister(Register):
	
	value = 0
	cpu  = None
	
	def __init__(self, cpu, hi=0, lo=None):
		self.cpu = cpu
		self.set(hi, lo);
		
	def set(self, hi, lo=None):
		if (lo is None):
			self.value = hi
			self.cpu.cycles -= 1
		else:
			self.value = (hi << 8) + lo
			self.cpu.cycles -= 2
			
	def setHi(self, hi):
		self.set(hi, this.getLo())
	
	def setLo(self, lo):
		self.set(self.getHi(), lo)
		
	def get(self):
		return self.value
	
	def getHi(self):
		return (self.value >> 8) & 0xFF
		
	def getLo(self):
		return self.value & 0xFF
	
	def inc(self):
		self.value = (self.value +1) & 0xFFFF
		self.cpu.cycles -= 2
		
	def dec(self):
		self.value = (self.value - 1) & 0xFFFF
		self.cpu.cycles -= 2
		
	def add(self, n):
		self.value = (self.value + n) & 0xFFFF
		self.cpu.cycles -= 3
	
	

class CPU(object):

    # Registers
    a = 0
    bc = None
    de = None
    f = 0
    hl = None
    sp = None
    pc = None

    # Interrupt Flags
    ime = False
    halted  = False
    cycles  = 0

    # Interrupt Controller
    #Interrupt 
    interrupt = None

     # memory Access
    #memory
    memory = None


    # ROM Access
    rom = []

    def __init__(self, interrupt, memory):
        self.interrupt = interrupt
        self.memory = memory
        self.bc = DoubleRegister()
        self.de = DoubleRegister()
        self.hl = DoubleRegister()
        self.pc = DoubleRegister()
        self.sp = DoubleRegister()
        self.reset()


    def getAF(self):
        return (self.a << 8) + self.f


    def getIF(self):
        val = 0x00
        #if (self.ime ? 0x01 : 0x00) + (self.halted ? 0x80 : 0x00)
        if self.ime:
            val = 0x01
        if self.halted:
            val += 0x80
        return val
       
       
    def setA(self, value):
    	self.a = value 
    	self.cycles -= 1 
    	
    def getA(self):
    	return self.a
    
    def setF(self, value):
    	self.f = value
    	self.cycles -= 1
    	
    def getF(self):
    	return self.f    
            

    def setROM(self, banks):
        self.rom = banks


    def reset(self):
        self.a = 0x01
        self.f = 0x80
        self.bc.set(0x0013)
        self.de.set(0x00D8)
        self.hl.set(0x014D)
        self.sp.set(0xFFFE)
        self.pc.set(0x0100)

        self.ime = False
        self.halted = False

        self.cycles = 0
        

    def emulate(self, ticks):
        self.cycles += ticks
        self.interrupt()
        while (self.cycles > 0):
            self.execute()


     # Interrupts
    def interrupt(self):
        if (self.halted):
            if (self.interrupt.isPending()):
                self.halted = False
                # Zerd no Densetsu
                self.cycles -= 4
            elif (self.cycles > 0):
                self.cycles = 0
        if (self.ime and self.interrupt.isPending()):
            if (self.interrupt.isPending(constants.VBLANK)):
                self.interrupt(0x40)
                self.interrupt.lower(constants.VBLANK)
            elif (self.interrupt.isPending(constants.LCD)):
                self.interrupt(0x48)
                self.interrupt.lower(constants.LCD)
            elif (self.interrupt.isPending(constants.TIMER)):
                self.interrupt(0x50)
                self.interrupt.lower(constants.TIMER)
            elif (self.interrupt.isPending(constants.SERIAL)):
                self.interrupt(0x58)
                self.interrupt.lower(constants.SERIAL)
            elif (self.interrupt.isPending(constants.JOYPAD)):
                self.interrupt(0x60)
                self.interrupt.lower(constants.JOYPAD)
            

    def interrupt(self, address):
        self.ime = False
        self.call(address)


     # Execution
    def execute(self):
        self.execute(self.fetch())
        

     # memory Access, 1 cycle
    def read(self, address):
        self.cycles -= 1
        return self.memory.read(address)

	 
    def read(self, hi, lo):
        return self.read((hi << 8) + lo)

    # 2 cycles
    def write(self, address, data):
        self.memory.write(address, data)
        self.cycles -= 2


    def write(self, hi, lo, data):
        self.write((hi << 8) + lo, data)


     # Fetching  1 cycle
    def fetch(self):
        self.cycles += 1
        if (self.pc.get() <= 0x3FFF):
            self.pc.inc() # 2 cycles
            return self.rom[self.pc.get()] & 0xFF
        data = self.memory.read(self.pc.get())
        self.pc.inc() # 2 cycles
        return data


     # Stack, 2 cycles
    def push(self, data):
        self.sp.dec() # 2 cycles
        self.memory.write(self.sp.get(), data)

	# 1 cycle
    def pop(self):
        data = self.memory.read(self.sp.get())
        self.sp.inc() # 2 cycles
        self.cycles += 1
        return data

	# 4 cycles
    def call(self, address):
        self.push(self.pc.getHi()) # 2 cycles
        self.push(self.pc.getLo()) # 2 cycles
        self.pc.set(address)       # 1 cycle
        self.cycles += 1


     # ALU, 1 cycle
    def addA(self, data):
        s = (self.a + data) & 0xFF
        self.f = 0
        if s == 0:
            self.f = constants.Z_FLAG
        if s < self.a:
            self.f += constants.C_FLAG
        if (s & 0x0F) < (self.a & 0x0F):
            self.f += constants.H_FLAG
        self.setA(s) # 1 cycle
        
    # 2 cycles
    def addHL(self, register):
        s = (self.hl.get() + register.get()) & 0xFFFF
        self.f = (self.f & constants.Z_FLAG)
        if ((s >> 8) & 0x0F) < (self.hl.getHi() & 0x0F):
            self.f += constants.H_FLAG
        if  s < self.hl.get():
            self.f += constants.C_FLAG
        self.cycles -= 1
        self.hl.set(s); # 1 cycle

    # 1 cycle
    def adc(self, getter):
        s = self.a + getter() + ((self.f & constants.C_FLAG) >> 4)
        self.f = 0
        if (s & 0xFF) == 0:
            self.f += constants.Z_FLAG 
        if s >= 0x100:
            self.f += constants.C_FLAG
        if ((s ^ self.a ^ getter()) & 0x10) != 0:
            self.f +=  constants.H_FLAG
        self.setA(s & 0xFF)  # 1 cycle

    # 1 cycle
    def sub(self, getter):
        s = (self.a - getter()) & 0xFF
        self.f = constants.N_FLAG
        if s == 0:
            self.f += constants.Z_FLAG 
        if s > self.a:
            self.f += constants.C_FLAG
        if (s & 0x0F) > (self.a & 0x0F):
            self.f +=  constants.H_FLAG
        self.setA(s)  # 1 cycle

    # 1 cycle
    def sbc(self, getter):
        s = self.a - getter() - ((self.f & constants.C_FLAG) >> 4)
        self.f = constants.N_FLAG
        if (s & 0xFF) == 0:
            self.f += constants.Z_FLAG 
        if (s & 0xFF00) != 0:
            self.f += constants.C_FLAG
        if ((s ^ self.a ^ getter()) & 0x10) != 0:
            self.f +=  constants.H_FLAG
        self.setA(s & 0xFF)  # 1 cycle

    # 1 cycle
    def AND(self, getter):
        self.setA(self.a & getter())  # 1 cycle
        self.f = 0
        if self.a == 0:
            self.f = constants.Z_FLAG

    # 1 cycle
    def XOR(self, getter):
        self.setA( self.a ^ getter())  # 1 cycle
        self.f = 0         
        if self.a == 0:
            self.f = constants.Z_FLAG

    # 1 cycle
    def OR(self, getter):
        self.setA(self.a | getter())  # 1 cycle
        self.f = 0
        if self.a == 0:     
            self.f = constants.Z_FLAG

    # 1 cycle
    def cpA(self, getter):
        s = (self.a - getter()) & 0xFF
        self.setF(constants.N_FLAG)  # 1 cycle
        if s==0:
            self.f += constants.Z_FLAG
        if s > self.a:
            self.f += constants.C_FLAG
        if (s & 0x0F) > (self.a & 0x0F):
            self.f += constants.H_FLAG

    # 1 cycle
    def inc(self, getter, setter):
        data = (getter() + 1) & 0xFF
        self.setF(0)  # 1 cycle
        if data == 0:
            self.f += constants.Z_FLAG
        if (data & 0x0F) == 0x00:
            self.f += constants.H_FLAG
        self.f += (self.f & constants.C_FLAG)
        setter(data)

    # 1 cycle
    def dec(self, getter, setter):
        data = (getter() - 1) & 0xFF
        self.setF(0) # 1 cycle
        if data == 0:
            self.f += constants.Z_FLAG
        if (data & 0x0F) == 0x0F:
                self.f += constants.H_FLAG
        self.f += (self.f & constants.C_FLAG) + constants.N_FLAG
        setter(data)

	# 1 cycle
    def rlc(self, getter, setter):
        s = ((getter() & 0x7F) << 1) + ((getter() & 0x80) >> 7)
        self.setF(0) # 1 cycle
        if s == 0:
            self.f += constants.Z_FLAG
        if (data & 0x80) != 0:
            self.f += constants.C_FLAG
        setter(s)

	# 1 cycle
    def rl(self, getter, setter):
        s = ((getter() & 0x7F) << 1)
        if (self.f & constants.C_FLAG) != 0:
            s += 0x01
        self.setF(0)  # 1 cycle
        if  (s == 0):
            self.f += constants.Z_FLAG
        if (data & 0x80) != 0:
            self.f += constants.C_FLAG
        setter(s)

	# 1 cycle
    def rrc(self, getter, setter):
        s = (getter() >> 1) + ((getter() & 0x01) << 7)
        self.setF(0) # 1 cycle
        if s == 0:
            self.f += constants.Z_FLAG
        if (data & 0x01) != 0:
            self.f += constants.C_FLAG
        setter(s)

	# 1 cycle
    def rr(self, getter, setter):
        s = (getter() >> 1) + ((self.f & constants.C_FLAG) << 3)
        self.fsetF(0)  # 1 cycle
        if s == 0:
            self.f += constants.Z_FLAG
        if (data & 0x01) != 0:
            self.f += constants.C_FLAG
        setter(s)

	# 1 cycle
    def sla(self, getter, setter):
        s = (getter() << 1) & 0xFF
        self.setF(0) # 1 cycle
        if s == 0:
            self.f += constants.Z_FLAG
        if (getter() & 0x80) != 0:
            self.f += constants.C_FLAG
        setter(s)

	# 1 cycle
    def sra(self, getter):
        s = (getter() >> 1) + (getter() & 0x80)
        self.setF(0) # 1 cycle
        if s == 0:
            self.f += constants.Z_FLAG
        if  (data & 0x01) != 0:
            self.f += constants.C_FLAG
        return s

	# 1 cycle
    def srl(self, getter, setter):
        s = (getter() >> 1)
        self.f = 0
        if s == 0 :
            self.f += constants.Z_FLAG
        if (data & 0x01) != 0:
            self.f += constants.C_FLAG
        self.cycles -= 1
        setter(s)

	# 1 cycle
    def swap(self, getter, setter):
        s = ((getter() << 4) & 0xF0) + ((getter() >> 4) & 0x0F)
        self.f = 0
        if s == 0:
            self.f += constants.Z_FLAG
        self.cycles -= 1
        setter(s)

	# 2 cycles
    def bit(self, n, getter):
        self.f = (self.f & constants.C_FLAG) + constants.H_FLAG
        if (getter() & (1 << n)) == 0:
            self.f += constants.Z_FLAG
        self.cycles -= 2

	# 2 cycles
    def set(self, getter, setter, n):
    	self.cycles -= 1   	   	    # 1 cycle
    	setter(getter() | (1 << n)) # 1 cycle
    	
    # 1 cycle
    def res(self, getter, setter):
        setter(getter() & (~(1 << n))) # 1 cycle
    	
 	# 1 cycle
    def ld(self, setter, getter):
        setter(getter()) # 1 cycle


     # LD A,(nnnn), 4 cycles
    def ld_A_mem(self):
        lo = self.fetch() # 1 cycle
        hi = self.fetch() # 1 cycle
        self.setA(self.read(hi, lo))  # 1+1 cycles


     # LD (rr),A  2 cycles
    def ld_BCi_A(self):
        self.write(self.bc.get(), self.a) # 2 cycles

    def ld_DEi_A(self):
        self.write(self.de.get(), self.a) # 2 cycles


     # LD (nnnn),SP  5 cycles
    def load_mem_SP(self):
        lo = self.fetch() # 1 cycle
        hi = self.fetch() # 1 cycle
        address = (hi << 8) + lo
        self.write(address, self.sp.getLo())  # 2 cycles
        self.write((address + 1) & 0xFFFF, self.sp.getHi()) # 2 cycles
        self.cycles += 1

     # LD (nnnn),A  4 cycles
    def ld_mem_A(self):
        lo = self.fetch() # 1 cycle
        hi = self.fetch() # 1 cycle
        self.write(hi, lo, self.a) # 2 cycles

     # LDH A,(nn) 3 cycles
    def ldh_A_mem(self):
        self.setA(self.read(0xFF00 + self.fetch())) # 1+1+1 cycles


     # LDH (nn),A 3 cycles
    def ldh_mem_A(self):
        self.write(0xFF00 + self.fetch(), self.a) # 2 + 1 cycles


     # LDH A,(C) 2 cycles
    def ldh_A_Ci(self):
        self.setA(self.read(0xFF00 + self.bc.getLo())) # 1+2 cycles


     # LDH (C),A 2 cycles
    def ldh_Ci_A(self):
        self.write(0xFF00 + self.bc.getLo(), self.a) # 2 cycles


     # LDI (HL),A 2 cycles
    def ldi_HLi_A(self):
        self.write(self.hl.get(), self.a) # 2 cycles
        self.incDoubleRegister(HL) # 2 cycles
        self.cycles += 2


     # LDI A,(HL) 2 cycles
    def ldi_A_HLi(self):
        self.a = self.read(self.hl.get())
        self.incDoubleRegister(HL)
        self.cycles -= 2


     # LDD (HL),A  2 cycles
    def ldd_HLi_A(self):
        self.write(self.hl.get(), self.a) # 2 cycles
        self.decDoubleRegister(HL) # 2 cycles
        self.cycles += 2


     # LDD A,(HL)  2 cycles
    def ldd_A_HLi(self):
        self.a = self.read(self.hl.get()) # 2 cycles
        self.decDoubleRegister(HL) # 2 cycles
        self.cycles += 2

	# 3 cycles
	def ld_dbRegister_nnnn(self, register):
		b = self.fetch() # 1 cycle
		a = self.fetch() # 1 cycle
		register.set(a, b) # 2 cycles
        self.cycles += 1

     # LD SP,HL 2 cycles
    def ld_SP_HL(self):
        self.sp.set(self.hl.get()) # 1 cycle
        self.cycles -= 1


     # PUSH rr 4 cycles
    def push_dbRegister(self, register):
        self.push(register.getHi()) # 2 cycles
        self.push(register.getLo()) # 2 cycles
    # 4 cycles
    def push_AF(self):
        self.push(self.a)  # 2 cycles
        self.push(self.f) # 2 cycles
 

	def pop_dbRegister(self, register):
		b = self.pop()
		a = self.pop()
		register.set(a, b)
		

    def pop_AF(self):
        self.f = self.pop()
        self.a = self.pop()
        self.cycles -= 3

     
    def cpl(self):
        self.a ^= 0xFF
        self.f |= constants.N_FLAG + constants.H_FLAG


     # DAA 1 cycle
    def daa(self):
        delta = 0
        if ((self.f & constants.H_FLAG) != 0 or (self.a & 0x0F) > 0x09):
            delta |= 0x06
        if ((self.f & constants.C_FLAG) != 0 or (self.a & 0xF0) > 0x90):
            delta |= 0x60
        if ((self.a & 0xF0) > 0x80 and (self.a & 0x0F) > 0x09):
            delta |= 0x60
        if ((self.f & constants.N_FLAG) == 0):
            self.setA((self.a + delta) & 0xFF) # 1 cycle
        else:
            self.setA((self.a - delta) & 0xFF) # 1 cycle

        self.f = (self.f & constants.N_FLAG)
        if delta >= 0x60:
            self.f += constants.C_FLAG
        if self.a == 0:
            self.f += constants.Z_FLAG


     # ADD HL,rr
    def add_HL_dbRegister(self, register):
        self.addHL(register)
        self.cycles -= 2


     # INC rr
    def incDoubleRegister(self, register):
        register.inc()


     # DEC rr
    def decDoubleRegister(self, register):
        register.dec()


     # ADD SP,nn
    def add_SP_nn(self):
        # TODO convert to byte
        offset = self.fetch()
        s = (self.sp.get() + offset) & 0xFFFF
        self.updateFRegisterAfterSP_nn(offset, s)
        self.sp.set(s)
        self.cycles -= 4



     # LD HL,SP+nn
    def ld_HL_SP_nn(self):
        #TODO convert to byte
        s = (self.sp.get() + offset) & 0xFFFF
        self.updateFRegisterAfterSP_nn(offset, s)
        self.hl.set(s)
        self.cycles -= 3


    def updateFRegisterAfterSP_nn(self, offset, s):
        if (offset >= 0):
            self.f = 0
            if s < self.sp:
                self.f += constants.C_FLAG
            if (s & 0x0F00) < (self.sp.get() & 0x0F00):
                self.f += constants.H_FLAG
        else:
            self.f = 0
            if s > self.sp:
                self.f += constants.C_FLAG
            if (s & 0x0F00) > (self.sp.get() & 0x0F00):
                self.f += constants.H_FLAG

     # RLCA
    def rlca(self):
        self.f = 0
        if (self.a & 0x80) != 0:
            self.f += constants.C_FLAG
        self.a = ((self.a & 0x7F) << 1) + ((self.a & 0x80) >> 7)
        self.cycles -= 1


     # RLA
    def rla(self):
        s = ((self.a & 0x7F) << 1)
        if (self.f & constants.C_FLAG) != 0:
            s +=  0x01
        self.f = 0
        if (self.a & 0x80) != 0:
            self.f += constants.C_FLAG
        self.a = s
        self.cycles -= 1


     # RRCA
    def rrca(self):
        self.f = 0
        if (self.a & 0x01) != 0:
            self.f += constants.C_FLAG
        self.a = ((self.a >> 1) & 0x7F) + ((self.a << 7) & 0x80)
        self.cycles -= 1


     # RRA
    def rra(self):
        s = ((self.a >> 1) & 0x7F)
        if (self.f & constants.C_FLAG) != 0:
            se += 0x80
        self.f = 0
        if (self.a & 0x01) != 0:
            self.f += constants.C_FLAG
        self.a = s
        self.cycles -= 1


     # CCF/SCF
    def ccf(self):
        self.f = (self.f & (constants.Z_FLAG | constants.C_FLAG)) ^ constants.C_FLAG


    def scf(self):
        self.f = (self.f & constants.Z_FLAG) | constants.C_FLAG


     # NOP 1 cycle
    def nop(self):
        self.cycles -= 1


     # LD PC,HL, 1 cycle
    def ld_PC_HL(self):
        self.pc.set(self.hl.get()) # 1 cycle
        

     # JP nnnn, 4 cycles
    def jp_nnnn(self):
        lo = self.fetch() # 1 cycle
        hi = self.fetch() # 1 cycle
        self.pc.set(hi,lo) # 2 cycles


     # JP cc,nnnn 3,4 cycles
    def jp_cc_nnnn(cc):
        if (cc):
            self.jp_nnnn() # 4 cycles
        else:
            self.pc.add(2) # 3 cycles
    

     # JR +nn, 3 cycles
    def jr_nn(self):
        self.pc.add(self.fetch()) # 3 + 1 cycles
        self.cycles += 1


     # JR cc,+nn, 2,3 cycles
    def jr_cc_nn(cc):
        if (cc):
            self.pc.add(self.fetch()) # 3 cycles
        else:
            self.pc.inc() # 2 cycles
    

     # CALL nnnn, 6 cycles
    def call_nnnn(self):
        lo = self.fetch() # 1 cycle
        hi = self.fetch() # 1 cycle
        self.call((hi << 8) + lo)  # 4 cycles


     # CALL cc,nnnn, 3,6 cycles
    def call_cc_nnnn(cc):
        if (cc):
            self.call_nnnn() # 6 cycles
        else:
            self.pc.add(2) # 3 cycles
    

    def isNZ(self):
        return (self.f & constants.Z_FLAG) == 0


    def isNC(self):
        return (self.f & constants.C_FLAG) == 0


    def isZ(self):
        return (self.f & constants.Z_FLAG) != 0


    def isC(self):
        return (self.f & constants.C_FLAG) != 0


     # RET 4 cycles
    def ret(self):
        lo = self.pop() # 1 cycle
        hi = self.pop() # 1 cycle
        self.pc.set(hi, lo) # 2 cycles


     # RET cc 2,5 cycles
    def ret_cc(cc):
        if (cc):
            self.ret() # 4 cycles
            # FIXME mybe this should be the same
            self.cycles -= 1
        else:
            self.cycles -= 2


     # RETI 4 cycles
    def reti(self):
        self.ret() # 4 cyclces
         # enable interrupts
        self.ime = True
        # execute next instruction
        self.execute()
        # check pending interrupts
        self.interrupt()



     # RST nn 4 cycles
    def rst(self, nn):
        self.call(nn) # 4 cycles


     # DI/EI 1 cycle
    def di(self):
        # disable interrupts
        self.ime = False
        self.cycles -= 1; 

	# 1 cycle
    def ei(self): 
        # enable interrupts
        self.ime = True
        self.cycles -= 1
        # execute next instruction
        self.execute()
        # check pending interrupts
        self.interrupt()


     # HALT/STOP
    def halt(self):
        self.halted = True
        # emulate bug when interrupts are pending
        if (not self.ime and self.interrupt.isPending()):
            self.execute(self.memory.read(self.pc.get()))
        # check pending interrupts
        self.interrupt()


    def stop(self):
        self.fetch()



SINGLE_OP_CODES = [
    (0x00, nop)
    (0x08, load_mem_SP),
    (0x10, stop),
    (0x18, jr_nn),
    (0x02, ld_BCi_A),
    (0x12, ld_DEi_A),
    (0x22, ldi_HLi_A),
    (0x32, ldd_HLi_A),
    (0x0A, ld_A_BCi),
    (0x1A, load_A_DEi),
    (0x2A, ldi_A_HLi),
    (0x3A, ldd_A_HLi),
    (0x07, rlca),
    (0x0F, rrca),
    (0x17, rla),
    (0x1F, rra),
    (0x27, daa),
    (0x2F, cpl),
    (0x37, scf),
    (0x3F, ccf),
    (0xF3, di),
    (0xFB, ei),
    (0xE2, ldh_Ci_A),
    (0xEA, ld_mem_A),
    (0xF2, ldh_A_Ci),
    (0xFA, ld_A_mem),
    (0xC3, jp_nnnn),
    (0xC9, ret),
    (0xD9, reti),
    (0xE9, ld_PC_HL),
    (0xF9, ld_SP_HL),
    (0xE0, ldh_mem_A),
    (0xE8, add_SP_nn),
    (0xF0, ldh_A_mem),
    (0xF8, ld_HL_SP_nn),
    (0xCB,)
    (0xCD, call_nnnn),
    (0xC6, add_A_nn),
    (0xCE, adc_A_nn),
    (0xD6, sub_A_nn),
    (0xDE, sbc_A_nn),
    (0xE6, and_A_nn),
    (0xEE, xor_A_nn),
    (0xF6, or_A_nn),
    (0xFE, cp_A_nn),
    (0xC7, rst(0x00)),
    (0xCF, rst(0x08)),
    (0xD7, rst(0x10)),
    (0xDF, rst(0x18)),
    (0xE7, rst(0x20)),
    (0xEF, rst(0x28)),
    (0xF7, rst(0x30)),
    (0xFF, rst(0x38))
    (0x76, halt),
]

METHOD_OP_CODES = [ 
    (0x01, 0x10, ld_nnnn, [BC, DE, HL, SP]),
    (0x09, 0x10, add_HL, [BC, DE, HL, SP]),
    (0x03, 0x10, inc, [BC, DE, HL, SP]),
    (0x0B, 0x10, dec, [BC, DE, HL, SP]),
    
    (0xC0, 0x08, ret, [NZ, Z, NC, C]),
    (0xC2, 0x08, jp_nnnn, [NZ, Z, NC, C]),
    (0xC4, 0x08, call_nnnn, [NZ, Z, NC, C]),
    (0x20, 0x08, jr_nn, [NZ, Z, NC, C]),
    
    (0xC1, 0x10, pop, [BC, DE, HL, AF]),
    (0xC5, 0x10, push, [BC, DE, HL, AF]),

    (0x01, 0x10, ld_nnnn, [BC, DE, HL, SP]),
    (0x09, 0x10, add_HL, [BC, DE, HL, SP]),
    (0x03, 0x10, inc, [BC, DE, HL, SP]),
    (0x0B, 0x10, dec, [BC, DE, HL, SP]),
    
    (0xC0, 0x08, ret, [NZ, Z, NC, C]),
    (0xC2, 0x08, jp_nnnn, [NZ, Z, NC, C]),
    (0xC4, 0x08, call_nnnn, [NZ, Z, NC, C]),
    
    (0xC1, 0x10, pop, [BC, DE, HL, AF]),
    (0xC5, 0x10, push, [BC, DE, HL, AF])
]

REGISTER_GROUP_OP_CODES = [
    (0x04, 0x08, inc),
    (0x05, 0x08, dec),
    (0x06, 0x08, ld_nn),    
    (0x80, 0x01,  add_A),    
    (0x88, 0x01, adc_A),    
    (0x90, 0x01, sub_A),    
    (0x98, 0x01, sbc_A),    
    (0xA0, 0x01,  and_A),    
    (0xA8, 0x01, xor_A),    
    (0xB0, 0x01, or_A),
    (0xB8, 0x01, cp_A),
    (0x00, 0x01, rlc),    
    (0x08, 0x01, rrc),    
    (0x10, 0x01, rl),    
    (0x18, 0x01, rr),    
    (0x20, 0x01, sla),    
    (0x28, 0x01, sra),    
    (0x30, 0x01, swap),    
    (0x38, 0x01, srl),
    (0x40, 0x01, bit, range(0, 8)),    
    (0xC0, 0x01, set, range(0, 8)),
    (0x80, 0x01, res, range(0, 8))
]
