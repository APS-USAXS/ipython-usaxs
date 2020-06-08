logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""
signals

from: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac
"""


"""
This EPICS PV calculates *BeamInHutch* boolean.
This is used to set the check beam PV to use I000 PD on Mirror window, limit is set
in user calc. This would fail for tune_dcmth and other macros, which may take
the intensity there down. For that use the other macro (?usaxs_CheckBeamSpecial?)...
"""
BeamInHutch = EpicsSignal(
    "9idcLAX:blCalc:userCalc1",
    name="usaxs_CheckBeamStandard"
)


# TODO: needs some thought and refactoring
# this is used to set the check beam PV to use many PVs and conditions to decide,
# if there is chance to have beam. Uses also userCalc on lax
usaxs_CheckBeamSpecial = EpicsSignal(
	"9idcLAX:blCalc:userCalc2",
	name="usaxs_CheckBeamSpecial"
	)

connect_delay_s = 1
while not mono_shutter.pss_state.connected:
    logger.info(f"Waiting {connect_delay_s}s for mono shutter PV to connect")
    time.sleep(connect_delay_s)


if aps.inUserOperations:
    sd.monitors.append(aps.current)
    # suspend when current < 2 mA
    # resume 100s after current > 10 mA
    logger.info("Installing suspender for low APS current.")
    suspend_APS_current = bluesky.suspenders.SuspendFloor(aps.current, 2, resume_thresh=10, sleep=100)
    RE.install_suspender(suspend_APS_current)

    # remove comment if likely to use this suspender (issue #170)
    # suspend_FE_shutter = bluesky.suspenders.SuspendFloor(FE_shutter.pss_state, 1)
    # RE.install_suspender(suspend_FE_shutter)

    logger.info(f"mono shutter connected = {mono_shutter.pss_state.connected}")
    # remove comment if likely to use this suspender (issue #170)
    # suspend_mono_shutter = bluesky.suspenders.SuspendFloor(mono_shutter.pss_state, 1)

    logger.info("Defining suspend_BeamInHutch.  Install/remove in scan plans as desired.")
    suspend_BeamInHutch = bluesky.suspenders.SuspendBoolLow(BeamInHutch)
    # be more judicious when to use this suspender (only within scan plans) -- see #180
    # RE.install_suspender(suspend_BeamInHutch)
    # logger.info("BeamInHutch suspender installed")

else:
    # simulators
    _simulated_beam_in_hutch = Signal(name="_simulated_beam_in_hutch")
    suspend_BeamInHutch = bluesky.suspenders.SuspendBoolHigh(_simulated_beam_in_hutch)


class MyMonochromator(Device):
    dcm = Component(APS_devices.KohzuSeqCtl_Monochromator, "9ida:")
    feedback = Component(DCM_Feedback, "9idcLAX:fbe:omega")
    temperature = Component(EpicsSignal, "9ida:DP41:s1:temp")
    cryo_level = Component(EpicsSignal, "9idCRYO:MainLevel:val")


monochromator = MyMonochromator(name="monochromator")
sd.baseline.append(monochromator)


userCalcs_lax = APS_devices.UserCalcsDevice("9idcLAX:", name="userCalcs_lax")

usaxs_q_calc = APS_synApps.SwaitRecord("9idcLAX:USAXS:Q", name="usaxs_q_calc")
# usaxs_q = usaxs_q_calc.get()

user_data = UserDataDevice(name="user_data")
sd.baseline.append(user_data)

sample_data = SampleDataDevice(name="sample_data")
sd.baseline.append(sample_data)

bss_user_info = APS_devices.ApsBssUserInfoDevice(
    "9id_bss:", name="bss_user_info")
sd.baseline.append(bss_user_info)


email_notices = APS_utils.EmailNotifications("usaxs@aps.anl.gov")
email_notices.add_addresses(
    "ilavsky@aps.anl.gov",
    "kuzmenko@aps.anl.gov",
    "mfrith@anl.gov",
)

# user will write code to check the corresponding symbol to send EmailNotifications
NOTIFY_ON_RESET = True
NOTIFY_ON_SCAN_DONE = False
NOTIFY_ON_BEAM_LOSS = True
NOTIFY_ON_BAD_FLY_SCAN = True
NOTIFY_ON_FEEDBACK = True
NOTIFY_ON_BADTUNE = True


class Autosave(Device):
    """control of autosave routine in EPICS IOC"""
    disable = Component(EpicsSignal, "SR_disable")
    max_time = Component(EpicsSignal, "SR_disableMaxSecs")

# autosave on LAX
lax_autosave = Autosave("9idcLAX:", name="lax_autosave")    # LAX is an IOC

class Trajectories(Device):
    """fly scan trajectories"""
    ar = Component(EpicsSignal, "9idcLAX:traj1:M1Traj")
    ay = Component(EpicsSignal, "9idcLAX:traj3:M1Traj")
    dy = Component(EpicsSignal, "9idcLAX:traj2:M1Traj")
    num_pulse_positions = Component(EpicsSignal, "9idcLAX:traj1:NumPulsePositions")

flyscan_trajectories = Trajectories(name="flyscan_trajectories")


ar_start = EpicsSignal("9idcLAX:USAXS:ARstart", name="ar_start")
# no PV : ay_start = EpicsSignal("9idcLAX:USAXS:AYstart", name="ay_start")
# no PV : dy_start = EpicsSignal("9idcLAX:USAXS:DYstart", name="dy_start")


linkam_ci94 = Linkam_CI94("9idcLAX:ci94:", name="ci94")
linkam_tc1 = Linkam_T96("9idcLINKAM:tc1:", name="linkam_tc1")


# NOTE: ALL referenced PVs **MUST** exist or get() operations will fail!
terms = GeneralParameters(name="terms")
sd.baseline.append(terms)

fuel_spray_bit = EpicsSignal("9idcLAX:bit1", name="fuel_spray_bit")

# terms.summary() to see all the fields
# terms.read() to read all the fields from EPICS