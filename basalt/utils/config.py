import argparse
import random


def get_base_experiment_parser():
    parser = argparse.ArgumentParser(
        description='basalt',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    return parser

def get_seed(args):
    return random.randint(0, 1000000)