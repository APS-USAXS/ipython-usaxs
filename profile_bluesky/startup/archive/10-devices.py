logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""
Set up custom or complex devices

NOTE: avoid using any PV more than once!

FUNCTIONS

    device_read2table()
    trim_string_for_EPICS()

DEVICES

    DCM_Feedback()
    ApsPssShutterWithStatus()
    BLEPS_Parameters()
    DiagnosticsParameters()
    FEEPS_Parameters()
    FlyScanParameters()
    GeneralParameters()
    GeneralParametersCCD()
    GeneralUsaxsParametersCenters()
    GeneralUsaxsParametersDiode()
    Linkam_CI94()
    Linkam_T96()
    Parameters_Al_Ti_Filters()
    Parameters_Al_Ti_Filters_Imaging()
    Parameters_Imaging()
    Parameters_OutOfBeam()
    Parameters_Transmission()
    Parameters_Radiography()
    Parameters_SAXS()
    Parameters_SAXS_WAXS()
    Parameters_SBUSAXS()
    Parameters_USAXS()
    Parameters_WAXS()
    PreUsaxsTuneParameters()
    PSS_Parameters()
    SampleDataDevice()
    UsaxsMotor()
    UsaxsMotorTunable()
    UserDataDevice()
    xxSimulatedApsPssShutterWithStatus()

"""

# simple enumeration used by DCM_Feedback()
MONO_FEEDBACK_OFF, MONO_FEEDBACK_ON = range(2)


def device_read2table(device, show_ancient=True, fmt="simple"):
    """
    read an ophyd device and print the output in a table
    
    Include an option to suppress ancient values identified
    by timestamp from 1989.  These are values only defined in 
    the original .db file.
    """
    table = pyRestTable.Table()
    table.labels = "name value datetime".split()
    ANCIENT_YEAR = 1989
    for k, rec in device.read().items():
        value = rec["value"]
        dt = datetime.datetime.fromtimestamp(rec["timestamp"])
        if dt.year > ANCIENT_YEAR or show_ancient:
            table.addRow((k, value, dt))
    print(table.reST(fmt=fmt))


class DCM_Feedback(Device):
    """
    monochromator EPID-record-based feedback program: fb_epid
    """
    control = Component(EpicsSignal, "")
    on = Component(EpicsSignal, ":on")
    drvh = Component(EpicsSignal, ".DRVH")
    drvl = Component(EpicsSignal, ".DRVL")
    oval = Component(EpicsSignal, ".OVAL")

    @property
    def is_on(self):
        return self.on.get() == 1

    @APS_utils.run_in_thread
    def _send_emails(self, subject, message):
        email_notices.send(subject, message)

    def check_position(self):
        diff_hi = self.drvh.get() - self.oval.get()
        diff_lo = self.oval.get() - self.drvl.get()
        if min(diff_hi, diff_lo) < 0.2:
            subject = "USAXS Feedback problem"
            message = "Feedback is very close to its limits."
            if email_notices.notify_on_feedback:
                self._send_emails(subject, message)
            logger.warning("!"*15)
            logger.warning(subject, message)
            logger.warning("!"*15)


class ApsPssShutterWithStatus(APS_devices.ApsPssShutterWithStatus):
    """
    temporary override to fix https://github.com/BCDA-APS/apstools/issues/113
    """

    def wait_for_state(self, target, timeout=10, poll_s=0.01):
        """
        wait for the PSS state to reach a desired target
        
        PARAMETERS
        
        target : [str]
            list of strings containing acceptable values
        
        timeout : non-negative number
            maximum amount of time (seconds) to wait for PSS state to reach target
        
        poll_s : non-negative number
            Time to wait (seconds) in first polling cycle.
            After first poll, this will be increased by ``_poll_factor_``
            up to a maximum time of ``_poll_s_max_``.
        """
        if timeout is not None:
            expiration = time.time() + max(timeout, 0)  # ensure non-negative timeout
        else:
            expiration = None
        
        # ensure the poll delay is reasonable
        if poll_s > self._poll_s_max_:
            poll_s = self._poll_s_max_
        elif poll_s < self._poll_s_min_:
            poll_s = self._poll_s_min_

        # t0 = time.time()
        while self.pss_state.get() not in target:
            time.sleep(poll_s)
            # elapsed = time.time() - t0
            # logger.debug(f"waiting {elapsed}s : value={self.pss_state.get()}")
            if poll_s < self._poll_s_max_:
                poll_s *= self._poll_factor_   # progressively longer
            if expiration is not None and time.time() > expiration:
                msg = f"Timeout ({timeout} s) waiting for shutter state"
                msg += f" to reach a value in {target}"
                raise TimeoutError(msg)


class xxSimulatedApsPssShutterWithStatus(APS_devices.SimulatedApsPssShutterWithStatus):
    """
    temporary override to fix https://github.com/BCDA-APS/apstools/issues/98
    """
    @property
    def state(self):
        """is shutter "open", "close", or "unknown"?"""
        if self.pss_state.get() in self.pss_state_open_values:
            result = self.valid_open_values[0]
        elif self.pss_state.get() in self.pss_state_closed_values:
            result = self.valid_close_values[0]
        else:
            result = self.unknown_state
        return result


class UsaxsMotor(EpicsMotorLimitsMixin, EpicsMotor): pass

class UsaxsMotorTunable(AxisTunerMixin, UsaxsMotor):
    width = Component(Signal, value=0)


# TODO: override for https://github.com/BCDA-APS/apstools/issues/124
MAX_EPICS_STRINGOUT_LENGTH = 40
def trim_string_for_EPICS(msg):
    """string must not be too long for EPICS PV"""
    if len(msg) > MAX_EPICS_STRINGOUT_LENGTH:
        msg = msg[:MAX_EPICS_STRINGOUT_LENGTH-1]
    return msg


class SampleDataDevice(Device):
    """sample information, (initially) based on NeXus requirements"""
    temperature = Component(EpicsSignal, "9idcSample:Temperature")
    concentration = Component(EpicsSignal, "9idcSample:Concentration")
    volume_fraction = Component(EpicsSignal, "9idcSample:VolumeFraction")
    scattering_length_density = Component(EpicsSignal, "9idcSample:ScatteringLengthDensity")
    magnetic_field = Component(EpicsSignal, "9idcSample:MagneticField")
    stress_field = Component(EpicsSignal, "9idcSample:StressField")
    electric_field = Component(EpicsSignal, "9idcSample:ElectricField")
    x_translation = Component(EpicsSignal, "9idcSample:XTranslation")
    rotation_angle = Component(EpicsSignal, "9idcSample:RotationAngle")

    magnetic_field_dir = Component(EpicsSignal, "9idcSample:MagneticFieldDir", string=True)
    stress_field_dir = Component(EpicsSignal, "9idcSample:StressFieldDir", string=True)
    electric_field_dir = Component(EpicsSignal, "9idcSample:ElectricFieldDir", string=True)

    description = Component(EpicsSignal, "9idcSample:Description", string=True)
    chemical_formula = Component(EpicsSignal, "9idcSample:ChemicalFormula", string=True)

    def resetAll(self):
        """bluesky plan to reset all to preset values"""
        yield from bps.mv(
            self.temperature, 25,
            self.concentration, 1,
            self.volume_fraction, 1,
            self.scattering_length_density, 1,
            self.magnetic_field, 0,
            self.stress_field, 0,
            self.electric_field, 0,
            self.x_translation, 0,
            self.rotation_angle, 0,

            self.magnetic_field_dir, "X",
            self.stress_field_dir, "X",
            self.electric_field_dir, "X",

            self.description, "",
            self.chemical_formula, "",
        )


class UserDataDevice(Device):
    GUP_number = Component(EpicsSignal,         "9idcLAX:GUPNumber")
    macro_file = Component(EpicsSignal,         "9idcLAX:USAXS:macroFile")
    macro_file_time = Component(EpicsSignal,    "9idcLAX:USAXS:macroFileTime")
    run_cycle = Component(EpicsSignal,          "9idcLAX:RunCycle")
    sample_thickness = Component(EpicsSignal,   "9idcLAX:sampleThickness")
    sample_title = Component(EpicsSignal,       "9idcLAX:sampleTitle", string=True)
    scanning = Component(EpicsSignal,           "9idcLAX:USAXS:scanning")
    scan_macro = Component(EpicsSignal,         "9idcLAX:USAXS:scanMacro")
    spec_file = Component(EpicsSignal,          "9idcLAX:USAXS:specFile", string=True)
    spec_scan = Component(EpicsSignal,          "9idcLAX:USAXS:specScan", string=True)
    state = Component(EpicsSignal,              "9idcLAX:state", string=True)
    time_stamp = Component(EpicsSignal,         "9idcLAX:USAXS:timeStamp")
    user_dir = Component(EpicsSignal,           "9idcLAX:userDir", string=True)
    user_name = Component(EpicsSignal,          "9idcLAX:userName", string=True)

    # for GUI to know if user is collecting data: 0="On", 1="Off"
    collection_in_progress = Component(EpicsSignal, "9idcLAX:dataColInProgress")

    def set_state_plan(self, msg, confirm=True):
        """plan: tell EPICS about what we are doing"""
        msg = APS_utils.trim_string_for_EPICS(msg)
        yield from bps.abs_set(self.state, msg, wait=confirm)

    def set_state_blocking(self, msg):
        """ophyd: tell EPICS about what we are doing"""
        msg = APS_utils.trim_string_for_EPICS(msg)
        self.state.put(msg)


class PSS_Parameters(Device):
    a_beam_active = Component(EpicsSignalRO, "PA:09ID:A_BEAM_ACTIVE.VAL", string=True)
    b_beam_active = Component(EpicsSignalRO, "PA:09ID:B_BEAM_ACTIVE.VAL", string=True)
    # does not connect: a_beam_ready = Component(EpicsSignalRO, "PA:09ID:A_BEAM_READY.VAL", string=True)
    b_beam_ready = Component(EpicsSignalRO, "PA:09ID:B_BEAM_READY.VAL", string=True)
    a_shutter_open_chain_A = Component(EpicsSignalRO, "PA:09ID:STA_A_FES_OPEN_PL", string=True)
    b_shutter_open_chain_A = Component(EpicsSignalRO, "PA:09ID:STA_B_FES_OPEN_PL", string=True)
    # does not connect: a_shutter_closed_chain_B = Component(EpicsSignalRO, "PB:09ID:STA_A_SBS_CLSD_PL", string=True)
    b_shutter_closed_chain_B = Component(EpicsSignalRO, "PB:09ID:STA_B_SBS_CLSD_PL", string=True)
    c_shutter_closed_chain_A = Component(EpicsSignalRO, "PA:09ID:SCS_PS_CLSD_LS", string=True)
    c_shutter_closed_chain_B = Component(EpicsSignalRO, "PB:09ID:SCS_PS_CLSD_LS", string=True)
    c_station_no_access_chain_A = Component(EpicsSignalRO, "PA:09ID:STA_C_NO_ACCESS.VAL", string=True)
    # other signals?

    @property
    def c_station_enabled(self):
        """
        look at the switches: are we allowed to operate?
    
        The PSS has a beam plug just before the C station
        
        :Plug in place:
          Cannot use beam in 9-ID-C.
          Should not use FE or mono shutters, monochromator, ti_filter_shutter...
    
        :Plug removed:
          Operations in 9-ID-C are allowed
        """
        enabled = self.c_shutter_closed_chain_A.get() == "OFF" or \
           self.c_shutter_closed_chain_A.get() == "OFF"
        return enabled


class BLEPS_Parameters(Device):
    """Beam Line Equipment Protection System"""
    red_light = Component(EpicsSignalRO, "9idBLEPS:RED_LIGHT")
    station_shutter_b = Component(EpicsSignalRO, "9idBLEPS:SBS_CLOSED", string=True)
    flow_1 = Component(EpicsSignalRO, "9idBLEPS:FLOW1_CURRENT")
    flow_2 = Component(EpicsSignalRO, "9idBLEPS:FLOW2_CURRENT")
    flow_1_setpoint = Component(EpicsSignalRO, "9idBLEPS:FLOW1_SET_POINT")
    flow_2_setpoint = Component(EpicsSignalRO, "9idBLEPS:FLOW2_SET_POINT")
    
    temperature_1_chopper = Component(EpicsSignalRO, "9idBLEPS:TEMP1_CURRENT")
    temperature_2 = Component(EpicsSignalRO, "9idBLEPS:TEMP2_CURRENT")
    temperature_3 = Component(EpicsSignalRO, "9idBLEPS:TEMP3_CURRENT")
    temperature_4 = Component(EpicsSignalRO, "9idBLEPS:TEMP4_CURRENT")
    temperature_5 = Component(EpicsSignalRO, "9idBLEPS:TEMP5_CURRENT")
    temperature_6 = Component(EpicsSignalRO, "9idBLEPS:TEMP6_CURRENT")
    temperature_7 = Component(EpicsSignalRO, "9idBLEPS:TEMP7_CURRENT")
    temperature_8 = Component(EpicsSignalRO, "9idBLEPS:TEMP8_CURRENT")
    temperature_1_chopper_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP1_SET_POINT")
    temperature_2_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP2_SET_POINT")
    temperature_3_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP3_SET_POINT")
    temperature_4_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP4_SET_POINT")
    temperature_5_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP5_SET_POINT")
    temperature_6_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP6_SET_POINT")
    temperature_7_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP7_SET_POINT")
    temperature_8_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP8_SET_POINT")
    # other signals?
    
    # technically, these come from the FE-EPS IOC, reading signals from the BL-EPS
    shutter_permit = Component(EpicsSignalRO, "EPS:09:ID:BLEPS:SPER", string=True)
    vacuum_permit = Component(EpicsSignalRO, "EPS:09:ID:BLEPS:VACPER", string=True)
    vacuum_ok = Component(EpicsSignalRO, "EPS:09:ID:BLEPS:VAC", string=True)


class FEEPS_Parameters(Device):
    """Front End Equipment Protection System"""
    fe_permit = Component(EpicsSignalRO, "EPS:09:ID:FE:PERM", string=True)
    major_fault = Component(EpicsSignalRO, "EPS:09:ID:Major", string=True)
    minor_fault = Component(EpicsSignalRO, "EPS:09:ID:Minor", string=True)
    mps_permit = Component(EpicsSignalRO, "EPS:09:ID:MPS:RF:PERM", string=True)
    photon_shutter_1 = Component(EpicsSignalRO, "EPS:09:ID:PS1:POSITION", string=True)
    photon_shutter_2 = Component(EpicsSignalRO, "EPS:09:ID:PS2:POSITION", string=True)
    safety_shutter_1 = Component(EpicsSignalRO, "EPS:09:ID:SS1:POSITION", string=True)
    safety_shutter_2 = Component(EpicsSignalRO, "EPS:09:ID:SS2:POSITION", string=True)
    # other signals?


# these are the global settings PVs for various parts of the instrument


class FlyScanParameters(Device):
    """FlyScan values"""
    number_points = Component(EpicsSignal, "9idcLAX:USAXS:FS_NumberOfPoints")
    scan_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ScanTime")
    use_flyscan = Component(EpicsSignal, "9idcLAX:USAXS:UseFlyscan")
    asrp_calc_SCAN = Component(EpicsSignal, "9idcLAX:userStringCalc2.SCAN")
    order_number = Component(EpicsSignal, "9idcLAX:USAXS:FS_OrderNumber")
    elapsed_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ElapsedTime")

    setpoint_up = Component(Signal, value=6000)     # decrease range
    setpoint_down = Component(Signal, value=850000)    # increase range


class PreUsaxsTuneParameters(Device):
    """preUSAXStune handling"""
    num_scans_last_tune = Component(EpicsSignal, "9idcLAX:NumScansFromLastTune")
    epoch_last_tune = Component(EpicsSignal, "9idcLAX:EPOCHTimeOfLastTune")
    req_num_scans_between_tune = Component(EpicsSignal, "9idcLAX:ReqNumScansBetweenTune")
    req_time_between_tune = Component(EpicsSignal, "9idcLAX:ReqTimeBetweenTune")
    run_tune_on_qdo = Component(EpicsSignal, "9idcLAX:RunPreUSAXStuneOnQdo")
    run_tune_next = Component(EpicsSignal, "9idcLAX:RunPreUSAXStuneNext")
    sx = Component(EpicsSignal, "9idcLAX:preUSAXStuneSX")
    sy = Component(EpicsSignal, "9idcLAX:preUSAXStuneSY")
    use_specific_location = Component(EpicsSignal, "9idcLAX:UseSpecificTuneLocation")
    
    @property
    def needed(self):
        """
        is a tune needed?
        
        EXAMPLE::
        
            if terms.preUSAXStune.needed:
                yield from preUSAXStune()
                # TODO: and then reset terms as approriate
        
        """
        result = self.run_tune_next.get()
        # TODO: next test if not in SAXS or WAXS mode
        result = result or self.num_scans_last_tune.get()  > self.req_num_scans_between_tune.get()
        time_limit = self.epoch_last_tune.get() + self.req_time_between_tune.get()
        result = result or time.time() > time_limit
        self.run_tune_next.put(0)
        return result


class GeneralParametersCCD(Device):
    "part of GeneralParameters Device"
    dx = Component(EpicsSignal, "dx")
    dy = Component(EpicsSignal, "dy")


class GeneralUsaxsParametersDiode(Device):
    "part of GeneralParameters Device"
    dx = Component(EpicsSignal, "Diode_dx")
    dy = Component(EpicsSignal, "DY0")


class GeneralUsaxsParametersCenters(Device):
    "part of GeneralParameters Device"
    AR = Component(EpicsSignal,  "ARcenter")
    ASR = Component(EpicsSignal, "ASRcenter")
    MR = Component(EpicsSignal,  "MRcenter")
    MSR = Component(EpicsSignal, "MSRcenter")


class Parameters_Al_Ti_Filters(Device):
    Al = Component(EpicsSignal,  "Al_Filter")
    Ti = Component(EpicsSignal,  "Ti_Filter")


class Parameters_Al_Ti_Filters_Imaging(Device):
    # because there is one in every crowd!
    Al = Component(EpicsSignal,  "Al_Filters")
    Ti = Component(EpicsSignal,  "Ti_Filters")


class Parameters_transmission(Device):
    # measure transmission in USAXS using pin diode
    measure = Component(EpicsSignal, "9idcLAX:USAXS:TR_MeasurePinTrans")

    # Ay to hit pin diode
    ay = Component(EpicsSignal, "9idcLAX:USAXS:TR_AyPosition")
    count_time = Component(EpicsSignal, "9idcLAX:USAXS:TR_MeasurementTime")
    diode_counts = Component(EpicsSignal, "9idcLAX:USAXS:TR_pinCounts")
    diode_gain = Component(EpicsSignal, "9idcLAX:USAXS:TR_pinGain") # I00 amplifier
    I0_counts = Component(EpicsSignal, "9idcLAX:USAXS:TR_I0Counts")
    I0_gain = Component(EpicsSignal, "9idcLAX:USAXS:TR_I0Gain")


class Parameters_USAXS(Device):
    """internal values shared with EPICS"""
    AY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:AY0")
    DY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:DY0")
    ASRP0 = Component(EpicsSignal,                    "9idcLAX:USAXS:ASRcenter")
    SAD = Component(EpicsSignal,                      "9idcLAX:USAXS:SAD")
    SDD = Component(EpicsSignal,                      "9idcLAX:USAXS:SDD")
    ar_val_center = Component(EpicsSignal,            "9idcLAX:USAXS:ARcenter")
    asr_val_center = Component(EpicsSignal,           "9idcLAX:USAXS:ASRcenter")
    
    #	ASRP_DEGREES_PER_VDC = 0.0059721     # measured by JI October 9, 2006 during setup at 32ID. Std Dev 4e-5
    #  	ASRP_DEGREES_PER_VDC = 0.00059721     # changed by factor of 10 to accomodate new PIUU controller, where we drive directly in V of high voltage. 
    # Measured by JIL on 6/4/2016, average of two measured numbers
    asrp_degrees_per_VDC = Component(Signal,          value=(0.000570223 + 0.000585857)/2)
    
    center = Component(GeneralUsaxsParametersCenters, "9idcLAX:USAXS:")
    ccd = Component(GeneralParametersCCD,             "9idcLAX:USAXS:CCD_")
    diode = Component(GeneralUsaxsParametersDiode,    "9idcLAX:USAXS:")
    img_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Img_")
    finish = Component(EpicsSignal,                   "9idcLAX:USAXS:Finish")
    is2DUSAXSscan = Component(EpicsSignal,            "9idcLAX:USAXS:is2DUSAXSscan")
    motor_prescaler_wait = Component(EpicsSignal,     "9idcLAX:USAXS:Prescaler_Wait")
    mr_val_center = Component(EpicsSignal,            "9idcLAX:USAXS:MRcenter")
    msr_val_center = Component(EpicsSignal,           "9idcLAX:USAXS:MSRcenter")
    num_points = Component(EpicsSignal,               "9idcLAX:USAXS:NumPoints")
    sample_y_step = Component(EpicsSignal,            "9idcLAX:USAXS:Sample_Y_Step")
    scan_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Scan_")
    scanning = Component(EpicsSignal,                 "9idcLAX:USAXS:scanning")
    start_offset = Component(EpicsSignal,             "9idcLAX:USAXS:StartOffset")
    uaterm = Component(EpicsSignal,                   "9idcLAX:USAXS:UATerm")
    usaxs_minstep = Component(EpicsSignal,            "9idcLAX:USAXS:MinStep")
    usaxs_time = Component(EpicsSignal,               "9idcLAX:USAXS:CountTime")
    useMSstage = Component(Signal,                    value=False)
    useSBUSAXS = Component(Signal,                    value=False)

    retune_needed = Component(Signal, value=False)     # does not *need* an EPICS PV

    # TODO: these are particular to the amplifier
    setpoint_up = Component(Signal, value=4000)     # decrease range
    setpoint_down = Component(Signal, value=650000)    # increase range

    transmission = Component(Parameters_transmission)

    def UPDRange(self):
        return upd_controls.auto.lurange.get()  # TODO: check return value is int


class Parameters_SBUSAXS(Device):
    pass


class Parameters_SAXS(Device):
    z_in = Component(EpicsSignal, "9idcLAX:SAXS_z_in")
    z_out = Component(EpicsSignal, "9idcLAX:SAXS_z_out")
    z_limit_offset = Component(EpicsSignal, "9idcLAX:SAXS_z_limit_offset")

    y_in = Component(EpicsSignal, "9idcLAX:SAXS_y_in")
    y_out = Component(EpicsSignal, "9idcLAX:SAXS_y_out")
    y_limit_offset = Component(EpicsSignal, "9idcLAX:SAXS_y_limit_offset")

    ax_in = Component(EpicsSignal, "9idcLAX:ax_in")
    ax_out = Component(EpicsSignal, "9idcLAX:ax_out")
    ax_limit_offset = Component(EpicsSignal, "9idcLAX:ax_limit_offset")

    dx_in = Component(EpicsSignal, "9idcLAX:dx_in")
    dx_out = Component(EpicsSignal, "9idcLAX:dx_out")
    dx_limit_offset = Component(EpicsSignal, "9idcLAX:dx_limit_offset")

    usaxs_h_size = Component(EpicsSignal, "9idcLAX:USAXS_hslit_ap")
    usaxs_v_size = Component(EpicsSignal, "9idcLAX:USAXS_vslit_ap")
    v_size = Component(EpicsSignal, "9idcLAX:SAXS_vslit_ap")
    h_size = Component(EpicsSignal, "9idcLAX:SAXS_hslit_ap")

    usaxs_guard_h_size = Component(EpicsSignal, "9idcLAX:USAXS_hgslit_ap")
    usaxs_guard_v_size = Component(EpicsSignal, "9idcLAX:USAXS_vgslit_ap")
    guard_v_size = Component(EpicsSignal, "9idcLAX:SAXS_vgslit_ap")
    guard_h_size = Component(EpicsSignal, "9idcLAX:SAXS_hgslit_ap")

    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:SAXS:Exp_")

    base_dir = Component(EpicsSignal, "9idcLAX:SAXS:directory", string=True)

    UsaxsSaxsMode = Component(EpicsSignal, "9idcLAX:SAXS:USAXSSAXSMode", put_complete=True)
    num_images = Component(EpicsSignal, "9idcLAX:SAXS:NumImages")
    acquire_time = Component(EpicsSignal, "9idcLAX:SAXS:AcquireTime")
    collecting = Component(EpicsSignal, "9idcLAX:collectingSAXS")


class Parameters_SAXS_WAXS(Device): 
    """
    terms used by both SAXS & WAXS
    """
    start_exposure_time = Component(EpicsSignal, "9idcLAX:SAXS:StartExposureTime")
    end_exposure_time = Component(EpicsSignal, "9idcLAX:SAXS:EndExposureTime")

    diode_gain = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrPDgain")
    diode_transmission = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrPD")
    I0_gain = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrI0gain")
    I0_transmission = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrI0")

    # this is Io value from gates scalar in LAX for Nexus file
    I0 = Component(EpicsSignal, "9idcLAX:SAXS:I0")


class Parameters_WAXS(Device):
    x_in = Component(EpicsSignal, "9idcLAX:WAXS_x_in")
    x_out = Component(EpicsSignal, "9idcLAX:WAXS_x_out")
    x_limit_offset = Component(EpicsSignal, "9idcLAX:WAXS_x_limit_offset")
    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS_WAXS:Exp_")
    base_dir = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:directory", string=True)
    num_images = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:NumImages")
    acquire_time = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:AcquireTime")
    collecting = Component(EpicsSignal, "9idcLAX:collectingWAXS")


class Parameters_Radiography(Device):
    pass


class Parameters_Imaging(Device):
    image_key = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImageKey")
    # 0=image, 1=flat field, 2=dark field

    exposure_time = Component(EpicsSignal, "9idcLAX:USAXS_Img:ExposureTime")

    tomo_rotation_angle = Component(EpicsSignal, "9idcLAX:USAXS_Img:Tomo_Rot_Angle")
    I0 = Component(EpicsSignal, "9idcLAX:USAXS_Img:Img_I0_value")
    I0_gain = Component(EpicsSignal, "9idcLAX:USAXS_Img:Img_I0_gain")

    ax_in = Component(EpicsSignal, "9idcLAX:USAXS_Img:ax_in")
    waxs_x_in = Component(EpicsSignal, "9idcLAX:USAXS_Img:waxs_x_in")

    flat_field = Component(EpicsSignal, "9idcLAX:USAXS_Img:FlatFieldImage")
    dark_field = Component(EpicsSignal, "9idcLAX:USAXS_Img:DarkFieldImage")
    title = Component(EpicsSignal, "9idcLAX:USAXS_Img:ExperimentTitle", string=True)

    h_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgHorApperture")
    v_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgVertApperture")
    guard_h_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgGuardHorApperture")
    guard_v_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgGuardVertApperture")

    filters = Component(Parameters_Al_Ti_Filters_Imaging, "9idcLAX:USAXS_Img:Img_")
    filter_transmission = Component(EpicsSignal, "9idcLAX:USAXS_Img:Img_FilterTransmission")


class Parameters_OutOfBeam(Device):
    pass


class GeneralParameters(Device):
    """
    cache of parameters to share with/from EPICS
    """
    USAXS = Component(Parameters_USAXS)
    SBUSAXS = Component(Parameters_SBUSAXS)
    SAXS = Component(Parameters_SAXS)
    SAXS_WAXS = Component(Parameters_SAXS_WAXS)
    WAXS = Component(Parameters_WAXS)
    Radiography = Component(Parameters_Radiography)
    Imaging = Component(Parameters_Imaging)
    OutOfBeam = Component(Parameters_OutOfBeam)

    PauseBeforeNextScan = Component(EpicsSignal, "9idcLAX:PauseBeforeNextScan")
    StopBeforeNextScan = Component(EpicsSignal,  "9idcLAX:StopBeforeNextScan")

    # consider refactoring
    FlyScan = Component(FlyScanParameters)
    preUSAXStune = Component(PreUsaxsTuneParameters)


class DiagnosticsParameters(Device):
    """for beam line diagnostics and post-mortem analyses"""
    beam_in_hutch_swait = Component(APS_synApps.SwaitRecord , "9idcLAX:blCalc:userCalc1")

    PSS = Component(PSS_Parameters)
    BL_EPS = Component(BLEPS_Parameters)
    FE_EPS = Component(FEEPS_Parameters)
    
    @property
    def beam_in_hutch(self):
        return self.beam_in_hutch_swait.val.get() != 0


class UsaxsProcessController(APS_devices.ProcessController):
    """
    temporary override
    
    see https://github.com/APS-USAXS/ipython-usaxs/issues/292
    """

    # override in subclass with EpicsSignal as appropriate
    rate = Component(Signal, kind="omitted")     # temperature change per minute
    speed = Component(Signal, kind="omitted")    # rotational speed (RPM) of pump

    @property
    def settled(self):
        """Is signal close enough to target?"""
        diff = abs(self.signal.get() - self.target.get())
        return diff <= self.tolerance.get()

    def wait_until_settled(self, timeout=None, timeout_fail=False):
        """
        plan: wait for controller signal to reach target within tolerance
        """
        # see: https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread-in-python
        t0 = time.time()
        _st = DeviceStatus(self.signal)

        if self.settled:
            # just in case signal already at target
            _st._finished(success=True)
        else:
            started = False
    
            def changing_cb(*args, **kwargs):
                if started and self.settled:
                    _st._finished(success=True)
    
            token = self.signal.subscribe(changing_cb)
            started = True
            report = 0
            while not _st.done and not self.settled:
                elapsed = time.time() - t0
                if timeout is not None and elapsed > timeout:
                    _st._finished(success=self.settled)
                    msg = f"{self.controller_name} Timeout after {elapsed:.2f}s"
                    msg += f", target {self.target.get():.2f}{self.units.get()}"
                    msg += f", now {self.signal.get():.2f}{self.units.get()}"
                    print(msg)
                    if timeout_fail:
                        raise TimeoutError(msg)
                    continue
                if elapsed >= report:
                    report += self.report_interval_s
                    msg = f"Waiting {elapsed:.1f}s"
                    msg += f" to reach {self.target.get():.2f}{self.units.get()}"
                    msg += f", now {self.signal.get():.2f}{self.units.get()}"
                    print(msg)
                yield from bps.sleep(self.poll_s)

            self.signal.unsubscribe(token)

        self.record_signal()
        elapsed = time.time() - t0
        print(f"Total time: {elapsed:.3f}s, settled:{_st.success}")


class Linkam_CI94(UsaxsProcessController):
    """
    Linkam model CI94 temperature controller
    
    EXAMPLE::
    
        In [1]: linkam_ci94 = Linkam_CI94("9idcLAX:ci94:", name="ci94")

        In [2]: linkam_ci94.settled                                                                                                                                         
        Out[2]: False

        In [3]: linkam_ci94.settled                                                                                                                                         
        Out[3]: True
        
        linkam_ci94.record_signal()
        yield from (linkam_ci94.set_target(50))

    """
    controller_name = "Linkam CI94"
    signal = Component(EpicsSignalRO, "temp")
    target = Component(EpicsSignal, "setLimit", kind="omitted")
    units = Component(Signal, kind="omitted", value="C")

    temperature_in = Component(EpicsSignalRO, "tempIn", kind="omitted")
    # DO NOT USE: temperature2_in = Component(EpicsSignalRO, "temp2In", kind="omitted")
    # DO NOT USE: temperature2 = Component(EpicsSignalRO, "temp2")
    pump_speed = Component(EpicsSignalRO, "pumpSpeed", kind="omitted")

    rate = Component(EpicsSignal, "setRate", kind="omitted")    # RPM
    speed = Component(EpicsSignal, "setSpeed", kind="omitted")  # deg/min, speed 0 = automatic control
    end_after_profile = Component(EpicsSignal, "endAfterProfile", kind="omitted")
    end_on_stop = Component(EpicsSignal, "endOnStop", kind="omitted")
    start_control = Component(EpicsSignal, "start", kind="omitted")
    stop_control = Component(EpicsSignal, "stop", kind="omitted")
    hold_control = Component(EpicsSignal, "hold", kind="omitted")
    pump_mode = Component(EpicsSignal, "pumpMode", kind="omitted")

    error_byte = Component(EpicsSignalRO, "errorByte", kind="omitted")
    status = Component(EpicsSignalRO, "status", kind="omitted")
    status_in = Component(EpicsSignalRO, "statusIn", kind="omitted")
    gen_stat = Component(EpicsSignalRO, "genStat", kind="omitted")
    pump_speed_in = Component(EpicsSignalRO, "pumpSpeedIn", kind="omitted")
    dsc_in = Component(EpicsSignalRO, "dscIn", kind="omitted")

    # clear_buffer = Component(EpicsSignal, "clearBuffer", kind="omitted")          # bo
    # scan_dis = Component(EpicsSignal, "scanDis", kind="omitted")                  # bo
    # test = Component(EpicsSignal, "test", kind="omitted")                         # longout
    # d_cmd = Component(EpicsSignalRO, "DCmd", kind="omitted")                      # ai
    # t_cmd = Component(EpicsSignalRO, "TCmd", kind="omitted")                      # ai
    # dsc = Component(EpicsSignalRO, "dsc", kind="omitted")                         # calc

    def record_signal(self):
        """write signal to the logger AND SPEC file"""
        global specwriter
        msg = f"{self.controller_name} signal: {self.get():.2f}{self.units.get()}"
        logger.info(msg)
        specwriter._cmt("event", msg)
        return msg


class Linkam_T96(UsaxsProcessController):
    """
    Linkam model T96 temperature controller
    
    EXAMPLE::
    
        linkam_tc1 = Linkam_T96("9idcLINKAM:tc1:", name="linkam_tc1")

    """
    controller_name = "Linkam T96"
    signal = Component(EpicsSignalRO, "temperature_RBV")  # ai
    target = Component(EpicsSignalWithRBV, "rampLimit", kind="omitted")
    units = Component(Signal, kind="omitted", value="C")

    vacuum = Component(EpicsSignal, "vacuum", kind="omitted")

    heating = Component(EpicsSignalWithRBV, "heating", kind="omitted")
    lnp_mode = Component(EpicsSignalWithRBV, "lnpMode", kind="omitted")
    lnp_speed = Component(EpicsSignalWithRBV, "lnpSpeed", kind="omitted")
    rate = Component(EpicsSignalWithRBV, "rampRate", kind="omitted")
    vacuum_limit_readback = Component(EpicsSignalWithRBV, "vacuumLimit", kind="omitted")

    controller_config = Component(EpicsSignalRO, "controllerConfig_RBV", kind="omitted")
    controller_error = Component(EpicsSignalRO, "controllerError_RBV", kind="omitted")
    controller_status = Component(EpicsSignalRO, "controllerStatus_RBV", kind="omitted")
    heater_power = Component(EpicsSignalRO, "heaterPower_RBV", kind="omitted")
    lnp_status = Component(EpicsSignalRO, "lnpStatus_RBV", kind="omitted")
    pressure = Component(EpicsSignalRO, "pressure_RBV", kind="omitted")
    ramp_at_limit = Component(EpicsSignalRO, "rampAtLimit_RBV", kind="omitted")
    stage_config = Component(EpicsSignalRO, "stageConfig_RBV", kind="omitted")
    status_error = Component(EpicsSignalRO, "statusError_RBV", kind="omitted")
    vacuum_at_limit = Component(EpicsSignalRO, "vacuumAtLimit_RBV", kind="omitted")
    vacuum_status = Component(EpicsSignalRO, "vacuumStatus_RBV", kind="omitted")

    def record_signal(self):
        """write signal to the logger AND SPEC file"""
        global specwriter
        msg = f"{self.controller_name} signal: {self.get():.2f}{self.units.get()}"
        logger.info(msg)
        specwriter._cmt("event", msg)
        return msg

    def set_target(self, target, wait=True, timeout=None, timeout_fail=False):
        """change controller to new temperature set point"""
        global specwriter
        
        yield from bps.mv(self.target, target)
        yield from bps.sleep(0.1)   # settling delay for slow IOC
        yield from bps.mv(self.heating, 1)

        msg = f"Set {self.controller_name} to {self.target.setpoint:.2f}{self.units.get()}"
        specwriter._cmt("event", msg)
        logger.info(msg)
        
        if wait:
            yield from self.wait_until_settled(
                timeout=timeout, 
                timeout_fail=timeout_fail)

    # @property
    # def settled(self):
    #     """Is signal close enough to target?"""
    #     print(f"{self.get()} C, in position? {self.ramp_at_limit.get()}")
    #     return self.ramp_at_limit.get() in (True, 1, "Yes")