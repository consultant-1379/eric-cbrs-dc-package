#!/usr/bin/python3

# --------------------------------------------------------------------------
#  COPYRIGHT Ericsson 2023
#
#  The copyright to the computer program(s) herein is the property of
#  Ericsson Inc. The programs may be used and/or copied only with written
#  permission from Ericsson Inc. or in accordance with the terms and
#  conditions stipulated in the agreement/contract under which the
#  program(s) have been supplied.
# --------------------------------------------------------------------------
"""
ENM log toolkit to display each log level
"""
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[31m'
BOLD = '\033[1m'
END = '\033[0m'

INFO = 'INFO : '
ERROR = 'ERROR : '
WARNING = 'WARNING : '

class LogLevel:
    """
    ENM kubernetes Logger module to put the related tag ahead of the messages.
    Log level keywords
    """

    @staticmethod
    def error(message):
        """
        Prints message in the format of error
        """
        print(BOLD + RED + ERROR + message +
              END + END)

    @staticmethod
    def warning(message):
        """
        Prints message in the format of warning
        """
        print(BOLD + YELLOW + WARNING + message +
              END + END)

    @staticmethod
    def info(message):
        """
        Prints message in the format of info
        """
        print(BOLD + BLUE + INFO + message +
              END + END)
