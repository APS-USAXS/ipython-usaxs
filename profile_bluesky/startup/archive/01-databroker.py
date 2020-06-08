logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""set up the data broker (db)"""


import os
callback_db = {}

# load config from ~/.config/databroker/mongodb_config.yml
from databroker import Broker
db = Broker.named("mongodb_config")


# Subscribe metadatastore to documents.
# If this is removed, data is not saved to metadatastore.
callback_db['Broker'] = RE.subscribe(db.insert)

# Set up SupplementalData.
from bluesky import SupplementalData
sd = SupplementalData()
RE.preprocessors.append(sd)

# Add a progress bar.
from bluesky.utils import ProgressBarManager
pbar_manager = ProgressBarManager()
RE.waiting_hook = pbar_manager

# Register bluesky IPython magics.
from bluesky.magics import BlueskyMagics
get_ipython().register_magics(BlueskyMagics)

# Set up the BestEffortCallback.
from bluesky.callbacks.best_effort import BestEffortCallback
bec = BestEffortCallback()
bec.disable_baseline()    # do not print baseline before/after a plan runs
callback_db['BestEffortCallback'] = RE.subscribe(bec)
peaks = bec.peaks  # just as alias for less typing

# At the end of every run, verify that files were saved and
# print a confirmation message.
from bluesky.callbacks.broker import verify_files_saved
# callback_db['verify_files_saved'] = RE.subscribe(post_run(verify_files_saved), 'stop')