print(__file__)

from datetime import datetime

# Set up default metadata

RE.md['beamline_id'] = 'APS USAXS 9-ID-C'
RE.md['proposal_id'] = None
RE.md['pid'] = os.getpid()

# Add a callback that prints scan IDs at the start of each scan.

import socket 
import getpass 
HOSTNAME = socket.gethostname() or 'localhost' 
USERNAME = getpass.getuser() or 'synApps_xxx_user' 
RE.md['login_id'] = USERNAME + '@' + HOSTNAME
RE.md['BLUESKY_VERSION'] = bluesky.__version__
RE.md['OPHYD_VERSION'] = ophyd.__version__

import os
for key, value in os.environ.items():
    if key.startswith("EPICS") and not key.startswith("EPICS_BASE"):
        RE.md[key] = value

print("Metadata dictionary:")
for k, v in sorted(RE.md.items()):
    print("RE.md['%s']" % k, "=", v)
