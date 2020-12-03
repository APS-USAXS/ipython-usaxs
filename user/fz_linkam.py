
"""
Linkam plan for Fan Zhang experiments 2020-12.

Load this into a bluesky console session with::

    %run -m fz_linkam

Note:
Use option is "-m" and no trailing ".py".  Loads as
a *module*.  The directory is already on the search path.
"""

from instrument.session_logs import logger
logger.info(__file__)


from bluesky import plan_stubs as bps
import time

from instrument.devices import linkam_ci94, linkam_tc1
from instrument.plans import SAXS, USAXSscan, WAXS
from instrument.plans.command_list import *


# NOTE NOTE NOTE NOTE NOTE NOTE
# this plan's name is custom!
# NOTE NOTE NOTE NOTE NOTE NOTE

def fzLinkamPlan(pos_X, pos_Y, thickness, scan_title, temp1, rate1, delay1_min, temp2, rate2, md={}):
    """
    collect RT USAXS/SAXS/WAXS
    change temperature T to temp1 with rate1
    collect USAXS/SAXS/WAXS while heating
    when temp1 reached, hold for delay1 min, collecting data repeatedly
    change T to temp2 with rate2
    collect USAXS/SAXS/WAXS while heating
    when temp2 reached, hold for delay2 seconds, collecting data repeatedly
    collect final data
    and it will end here...

    reload by
    # %run -m linkam
    """

    def setSampleName():
        return f"{scan_title}_{linkam.value+0.5:.0f}C_{(time.time()-t0)/60:.0f}min"

    def collectAllThree(debug=False):
        sampleMod = setSampleName()
        if debug:
            #for testing purposes, set debug=True
            print(sampleMod)
            yield from bps.sleep(20)
        else:
            try:
                md["title"]=sampleMod
                yield from USAXSscan(pos_X, pos_Y, thickness, sampleMod, md={})
            except Exception as exc:
                logger.error(exc)
                yield from reset_USAXS()

            try:
                sampleMod = setSampleName()
                md["title"]=sampleMod
                yield from SAXS(pos_X, pos_Y, thickness, sampleMod, md={})
            except Exception as exc:
                logger.error(exc)

            try:
                sampleMod = setSampleName()
                md["title"]=sampleMod
                yield from WAXS(pos_X, pos_Y, thickness, sampleMod, md={})
            except Exception as exc:
                logger.error(exc)

    linkam = linkam_tc1
    #linkam = linkam_ci94
    logger.info(f"Linkam controller PV prefix={linkam.prefix}")

    yield from before_command_list(md={})

    #yield from bps.mv(linkam.rate, 50)          #sets the rate of next ramp
    #yield from linkam.set_target(40, wait=True)     #sets the temp of next ramp
    #t0 = time.time()
    #yield from collectAllThree()
    yield from mode_USAXS()
    yield from bps.mv(linkam.rate, rate1)          #sets the rate of next ramp
    yield from linkam.set_target(temp1, wait=True)     #sets the temp of next ramp
    #logger.info(f"Ramping temperature to {temp1} C")
    

    #while not linkam.settled:                           #runs data collection until next temp
    #    yield from collectAllThree()

    logger.info(f"Reached temperature, now collecting data for {delay1_min} seconds")
    t1 = time.time()
    t0 = time.time()

    while time.time()-t1 < delay1_min*60:                          # collects data for delay1 seconds
        yield from collectAllThree()

    logger.info(f"waited for {delay1_min} min, now changing temperature to {temp2} C")

    yield from bps.mv(linkam.rate, rate2)          #sets the rate of next ramp
    yield from linkam.set_target(temp2, wait=False)     #sets the temp of next ramp

    while not linkam.settled:                           #runs data collection until next temp
        yield from collectAllThree()

    logger.info(f"reached {temp2} C")

    yield from collectAllThree()

    yield from after_command_list()

    logger.info(f"finished")
