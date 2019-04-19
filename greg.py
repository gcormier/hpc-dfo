import os
import datetime

import datetime
import os
import sys
import logging

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

logging.info("Test")
logging.debug("moretest")
logging.error("uhoh")
