"""
Custom (simple) Logger class to let me save logs to file and print with
one command.
"""

import sys

class Logger(object):
    def __init__(self, filepath, secondary=sys.stdout):
        """
        Constructor
        :param filepath: location of log file (must not exist)
        :param secondary: user may change secondary location from stdout
        """
        self.fp = filepath
        sys.stdout = secondary # change print() location; default is print()
        #File must not exist
        try:
            fTest = open(self.fp, 'r')
        except FileNotFoundError:
            with open(self.fp, 'w') as f:
                f.write("###LOG START###\n")
                f.close()
        else:
            fTest.close()
            raise FileExistsError

    def debug(self, *line):
        """
        prints line to stdout(secondary) and specified file.
        :param *line: the text to put in file and print()
        :return: void
        """
        text = ""
        for item in line:
            text += str(item)
        text+= '\n'
        with open(self.fp, 'a') as file:
            file.write(text)
            file.close()
        print(text, end="")

    def log_to_file(self, *line):
        """
        Write Line only into specifed file.
        :param *line: the text to put in file
        :return: void
        """
        text = ""
        for item in line:
            text += str(item)
        text+= '\n'
        with open(self.fp, 'a') as file:
            file.write(text)
            file.close()

    def log_to_secondary(self, *line):
        """
        Write line only to secondary (default stdout)
        :param *line: text to print()
        :return: void
        """
        text = ""
        for item in line:
            text += item
        print(text)


