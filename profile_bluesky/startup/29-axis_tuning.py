print(__file__)

"""configure per-axis tuning"""

# use center-of-mass, and not peak value: "com"
TUNE_METHOD_PEAK_CHOICE = "com"

USING_MS_STAGE = False

# use introspection to identify channel names
for ch_attr in scaler0.channels.read_attrs:
    if hasattr(scaler0.channels, ch_attr):
        ch = scaler0.channels.__getattribute__(ch_attr)
        if ch.chname.value == "I0":
            I0_SIGNAL = ch
        if ch.chname.value == "I00":
            I00_SIGNAL = ch

# use I00 (if MS stage is used, use I0)
if USING_MS_STAGE:
    TUNING_DET_SIGNAL = I0_SIGNAL
else:
    TUNING_DET_SIGNAL = I00_SIGNAL


USAXS_tune_mr_range =  0.0025    # range for tune mr for about 12-17kev
USAXS_tune_m2rp_range = 3        # range for tune m2rp for about 12keV
USAXS_tune_ar_range =  0.002     # range for tune ar for about 12keV 
USAXS_tune_a2rp_range = 3        # range for tune a2rp for about 12keV
USAXS_tune_msr_range = 3         # range for tune msr for about 12keV
USAXS_tune_asr_range = 3         # range for tune asr for about 12keV 


# -------------------------------------------

def mr_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(m_stage.r.name, m_stage.r.position))
    m_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
    m_stage.r.tuner.num = 31
    m_stage.r.tuner.width = 2*USAXS_tune_mr_range
    yield from bps.mv(scaler0.preset_time, 0.1)
     
 
def mr_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(m_stage.r.name, m_stage.r.position))
    yield from bps.mv(mr_val_center, m_stage.r.position)
 
 
m_stage.r.tuner = TuneAxis([scaler0], m_stage.r, signal_name=TUNING_DET_SIGNAL.name)
m_stage.r.pre_tune_method = mr_pretune_hook
m_stage.r.post_tune_method = mr_posttune_hook


# -------------------------------------------


def m2rp_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(m_stage.r2p.name, m_stage.r2p.position))
    m_stage.r2p.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
    m_stage.r2p.tuner.num = 21
    yield from bps.mv(scaler0.preset_time, 0.1, scaler0.delay, 0.02)
    m_stage.r2p.tuner.width = 2*USAXS_tune_m2rp_range
    

def m2rp_posttune_hook():
    #
    # TODO: first, re-position piezo considering hysteresis?
    #
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(m_stage.r2p.name, m_stage.r2p.position))
    yield from bps.mv(scaler0.delay, 0.05)


# use I00 (if MS stage is used, use I0)
m_stage.r2p.tuner = TuneAxis([scaler0], m_stage.r2p, signal_name=TUNING_DET_SIGNAL.name)
m_stage.r2p.pre_tune_method = m2rp_pretune_hook
m_stage.r2p.post_tune_method = m2rp_posttune_hook


# -------------------------------------------

# TODO: confirm

# def msr_pretune_hook():
#     msg = "Tuning axis {}, current position is {}"
#     print(msg.format(ms_stage.r.name, ms_stage.r.position))
#     ms_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
#     ms_stage.r.tuner.num = 31
#     ms_stage.r.tuner.width = 2*USAXS_tune_msr_range
#     yield from bps.mv(scaler0.preset_time, 0.1)
#     
# 
# def msr_posttune_hook():
#     msg = "Tuning axis {}, final position is {}"
#     print(msg.format(ms_stage.r.name, ms_stage.r.position))
#     yield from bps.mv(msr_val_center, ms_stage.r.position)
# 
# 
# # use I00 (if MS stage is used, use I0)
# ms_stage.rp.tuner = TuneAxis([scaler0], ms_stage.rp, signal_name=TUNING_DET_SIGNAL.name)
# ms_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
# ms_stage.r.tuner.num = 21


# -------------------------------------------


def ar_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(a_stage.r.name, a_stage.r.position))
    a_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
    a_stage.r.tuner.num = 35
    a_stage.r.tuner.width = 2*USAXS_tune_ar_range
    yield from bps.mv(scaler0.preset_time, 0.1)


def ar_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(a_stage.r.name, a_stage.r.position))

    if a_stage.r.tuner.tune_ok:
        yield from bps.mv(ar_val_center, a_stage.r.position)
        # remember the Q calculation needs a new 2theta0
        # use the current AR encoder position
        yield from bps.mv(usaxs_q_calc.channels.B, usaxs_q_calc.channels.A.value)


a_stage.r.tuner = TuneAxis([scaler0], a_stage.r, signal_name=I0_SIGNAL.name)
a_stage.r.pre_tune_method = ar_pretune_hook
a_stage.r.post_tune_method = ar_posttune_hook


# -------------------------------------------

# TODO: confirm

# as_stage.rp.tuner = TuneAxis([scaler0], as_stage.rp, signal_name=I0_SIGNAL.name)
# as_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE


# -------------------------------------------


def a2rp_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(a_stage.r2p.name, a_stage.r2p.position))
    a_stage.r2p.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
    a_stage.r2p.tuner.num = 31
    a_stage.r2p.tuner.width = 2*USAXS_tune_a2rp_range
    yield from bps.mv(scaler0.preset_time, 0.1, scaler0.delay, 0.02)


def a2rp_posttune_hook():
    #
    # TODO: first, re-position piezo considering hysteresis?
    #
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(a_stage.r2p.name, a_stage.r2p.position))

    if a_stage.r2p.tuner.tune_ok:
        # remember the Q calculation needs a new 2theta0
        # use the current AR encoder position
        yield from bps.mv(usaxs_q_calc.channels.B, usaxs_q_calc.channels.A.value)
    yield from bps.mv(scaler0.delay, 0.05)


a_stage.r.tuner = TuneAxis([scaler0], a_stage.r, signal_name=I0_SIGNAL.name)
a_stage.r.pre_tune_method = ar_pretune_hook
a_stage.r.post_tune_method = ar_posttune_hook