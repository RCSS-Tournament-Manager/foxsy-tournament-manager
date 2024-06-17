import argparse

class ArgsHelper:
    @staticmethod
    def str_to_bool(value):
        if value.lower() in {'true', '1'}:
            return True
        elif value.lower() in {'false', '0'}:
            return False
        else:
            raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")