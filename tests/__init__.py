import logging

import bugsnag


logging.getLogger('requests').setLevel(logging.CRITICAL)
bugsnag.logger.setLevel(logging.CRITICAL)
