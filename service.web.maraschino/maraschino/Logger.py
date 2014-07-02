# -*- coding: utf-8 -*-

import logging
import logging.handlers
import maraschino
import datetime
import sys
import os

class maraschinoLogger:
    """Maraschino logger"""

    def __init__(self, LOG_FILE, VERBOSE):
        """init the logger"""

        # set up formatting for console and the two log files
        confor = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s', '%H:%M:%S')
        warfor = logging.Formatter('%(asctime)s :: %(levelname)-8s :: %(message)s', '%b-%d %H:%M:%S')
        
        # set up logging to STDOUT for all levels DEBUG and higher
        con = logging.StreamHandler(sys.stdout)
        con.setLevel(logging.DEBUG)
        con.setFormatter(confor)

        # set up logging to a file for all levels DEBUG and higher
        war = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=500000, backupCount=3)
        war.setLevel(logging.DEBUG)
        war.setFormatter(warfor)

        # create Logger object
        self.mylogger = logging.getLogger('MAIN')
        self.mylogger.setLevel(logging.DEBUG)
        if VERBOSE:
            self.mylogger.addHandler(con)
        self.mylogger.addHandler(war)

        from maraschino import DEVELOPMENT
        if DEVELOPMENT:
            werkzeug_logger = logging.getLogger('werkzeug')
            werkzeug_logger.setLevel(logging.DEBUG)
            werkzeug_logger.addHandler(con)
            werkzeug_logger.addHandler(war)

    def log(self, toLog, logLevel):
        """wrapper for logger output"""
        try:
            if logLevel == 'DEBUG':
                self.mylogger.debug(toLog)
            elif logLevel == 'INFO':
                self.mylogger.info(toLog)
            elif logLevel == 'WARNING':
                self.mylogger.warning(toLog)
            elif logLevel == 'ERROR':
                self.mylogger.error(toLog)
            elif logLevel == 'CRITICAL':
                self.mylogger.critical(toLog)

            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            maraschino.LOG_LIST.append({'level': logLevel, 'message': toLog, 'time': time})
        except ValueError:
            pass 
