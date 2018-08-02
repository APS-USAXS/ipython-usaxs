print(__file__)

"""motors, stages, positioners, ..."""


def move_motors(*args):
    """
    move one or more motors at the same time, returns when all moves are done
    
    move_motors(m1, 0)
    move_motors(m2, 0, m3, 0, m4, 0)
    """
    status = []
    for m, v in pairwise(args):
        status.append(m.move(v, wait=False))
    
    for st in status:
        ophyd.status.wait(st)


class EpicsMotorLimitsMixin(Device):
    """
    add motor record HLM & LLM fields & compatibility get_lim() and set_lim()
    """
    
    soft_limit_lo = Component(EpicsSignal, ".LLM")
    soft_limit_hi = Component(EpicsSignal, ".HLM")
    
    def get_lim(self, flag):
        """
        Returns the user limit of motor
        
        flag > 0: returns high limit
        flag < 0: returns low limit
        flag == 0: returns None
        """
        if flag > 0:
            return self.high_limit
        else:
            return self.low_limit
    
    def set_lim(self, low, high):
        """
        Sets the low and high limits of motor
        
        * Low limit is set to lesser of (low, high)
        * High limit is set to greater of (low, high)
        * No action taken if motor is moving. 
        """
        if not self.moving:
            self.soft_limit_lo.put(min(low, high))
            self.soft_limit_hi.put(max(low, high))


class EpicsMotorWithLimits(EpicsMotor, EpicsMotorLimitsMixin): pass


class UsaxsSampleStageDevice(MotorBundle):
    """USAXS sample stage"""
    x = Component(EpicsMotor, '9idcLAX:m58:c2:m1', labels=("sample",))
    y = Component(EpicsMotor, '9idcLAX:m58:c2:m2', labels=("sample",))


class UsaxsDetectorStageDevice(MotorBundle):
    """USAXS detector stage"""
    x = Component(EpicsMotor, '9idcLAX:m58:c2:m3', labels=("detector",))
    y = Component(EpicsMotor, '9idcLAX:aero:c2:m1', labels=("detector",))


class UsaxsSlitDevice(MotorBundle):
    """
    USAXS slit just before the sample
    
    * center of slit: (x, y)
    * aperture: (h_size, v_size)
    """
    h_size = Component(EpicsMotor, '9idcLAX:m58:c2:m8', labels=("uslit",))
    x      = Component(EpicsMotor, '9idcLAX:m58:c2:m6', labels=("uslit",))
    v_size = Component(EpicsMotor, '9idcLAX:m58:c2:m7', labels=("uslit",))
    y      = Component(EpicsMotor, '9idcLAX:m58:c2:m5', labels=("uslit",))
    
    def set_size(self, *args, h=None, v=None):
        """move the slits to the specified size"""
        if h is None:
            raise ValueError("must define horizontal size")
        if v is None:
            raise ValueError("must define vertical size")
        move_motors(self.h_size, h, self.v_size=v)


class GSlitDevice(MotorBundle):
    """
    guard slit

    * aperture: (h_size, v_size)
    """
    bot  = Component(EpicsMotor, '9idcLAX:mxv:c0:m6', labels=("gslit",))
    inb  = Component(EpicsMotor, '9idcLAX:mxv:c0:m4', labels=("gslit",))
    outb = Component(EpicsMotor, '9idcLAX:mxv:c0:m3', labels=("gslit",))
    top  = Component(EpicsMotor, '9idcLAX:mxv:c0:m5', labels=("gslit",))
    x    = Component(EpicsMotor, '9idcLAX:m58:c1:m5', labels=("gslit",))
    y    = Component(EpicsMotor, '9idcLAX:m58:c0:m6', labels=("gslit",))

    h_size = Component(EpicsSignal, '9idcLAX:GSlit1H:size')
    v_size = Component(EpicsSignal, '9idcLAX:GSlit1V:size')
    
    def set_size(self, *args, h=None, v=None):
        """move the slits to the specified size"""
        if h is None:
            raise ValueError("must define horizontal size")
        if v is None:
            raise ValueError("must define vertical size")
        move_motors(self.h_size, h, self.v_size=v)
    

class UsaxsCollimatorStageDevice(MotorBundle):
    """USAXS Collimator (Monochromator) stage"""
    r = Component(TunableEpicsMotor, '9idcLAX:aero:c3:m1', labels=("collimator", "tunable",))
    x = Component(EpicsMotor, '9idcLAX:m58:c0:m2', labels=("collimator",))
    y = Component(EpicsMotor, '9idcLAX:m58:c0:m3', labels=("collimator",))
    r2p = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m2', labels=("collimator", "tunable",))


class UsaxsCollimatorSideReflectionStageDevice(MotorBundle):
    """USAXS Collimator (Monochromator) side-reflection stage"""
    #r = Component(EpicsMotor, '9idcLAX:xps:c0:m5', labels=("side_collimator",))
    #t = Component(EpicsMotor, '9idcLAX:xps:c0:m3', labels=("side_collimator",))
    x = Component(EpicsMotor, '9idcLAX:m58:c1:m1', labels=("side_collimator",))
    y = Component(EpicsMotor, '9idcLAX:m58:c1:m2')
    rp = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m3', labels=("side_collimator", "tunable",))


class UsaxsAnalyzerStageDevice(MotorBundle):
    """USAXS Analyzer stage"""
    r = Component(TunableEpicsMotor, '9idcLAX:aero:c0:m1', labels=("analyzer", "tunable"))
    x = Component(EpicsMotor, '9idcLAX:m58:c0:m5', labels=("analyzer",))
    y = Component(EpicsMotor, '9idcLAX:aero:c1:m1', labels=("analyzer",))
    z = Component(EpicsMotor, '9idcLAX:m58:c0:m7', labels=("analyzer",))
    r2p = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m1', labels=("analyzer", "tunable"))
    rt = Component(EpicsMotor, '9idcLAX:m58:c1:m3', labels=("analyzer",))


class UsaxsAnalyzerSideReflectionStageDevice(MotorBundle):
    """USAXS Analyzer side-reflection stage"""
    #r = Component(EpicsMotor, '9idcLAX:xps:c0:m6', labels=("analyzer",))
    #t = Component(EpicsMotor, '9idcLAX:xps:c0:m4', labels=("analyzer",))
    y = Component(EpicsMotor, '9idcLAX:m58:c1:m4', labels=("analyzer",))
    rp = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m4', labels=("analyzer", "tunable"))


class SaxsDetectorStageDevice(MotorBundle):
    """SAXS detector stage (aka: pin SAXS stage)"""
    x = Component(EpicsMotor, '9idcLAX:mxv:c0:m1', labels=("saxs",))
    y = Component(EpicsMotor, '9idcLAX:mxv:c0:m8', labels=("saxs",))
    z = Component(EpicsMotor, '9idcLAX:mxv:c0:m2', labels=("saxs",))
    

guard_slit = GSlitDevice('', name='guard_slit')
usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')

s_stage    = UsaxsSampleStageDevice('', name='s_stage')
d_stage    = UsaxsDetectorStageDevice('', name='d_stage')

m_stage    = UsaxsCollimatorStageDevice('', name='m_stage')
ms_stage   = UsaxsCollimatorSideReflectionStageDevice('', name='ms_stage')

a_stage    = UsaxsAnalyzerStageDevice('', name='a_stage')
as_stage   = UsaxsAnalyzerSideReflectionStageDevice('', name='aw_stage')

saxs_stage = SaxsDetectorStageDevice('', name='saxs_stage')

camy       = EpicsMotor('9idcLAX:m58:c1:m7', name='camy')  # cam_y
tcam       = EpicsMotor('9idcLAX:m58:c1:m6', name='tcam')  # tcam
tens       = EpicsMotor('9idcLAX:m58:c1:m8', name='tens')  # Tension
waxsx      = EpicsMotor('9idcLAX:m58:c0:m4', name='waxsx', labels=("waxs",))  # WAXS X
