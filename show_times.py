#!/usr/bin/env python3

"""
Display bus times for my nearby bus stops
"""

import argparse
import configparser
import time

# import dfrobot
import requests

import get_times
from config import ARROWS

config = configparser.ConfigParser()
config.read('config.ini')

KEY_IFTT = config['KEYS']['KEY_IFTT']

def get_arrows(arrivals_nearby):
    """
    Change direction from 'IB'/'OB' to arrows based on ARROWS
    """
    arrivals_arrows = {}
    for line, directions in arrivals_nearby.items():
        arrivals_arrows[line] = {}
        for direction, times in directions.items():
            direction_arrow = next((arrow for arrow, line_directions in ARROWS.items()
                                    if (line, direction) in line_directions),
                                   direction)
            arrivals_arrows[line][direction_arrow] = times

    return arrivals_arrows


def combine_6_7(arrivals_nearby):
    """
    Combines lines 6 and 7 into a 6/7 line in both directions, and deletes 6 and 7 lines.
    :param arrivals_nearby: custom dict with nearby bus arrivals
    :return arrivals_nearby: modified custom dict with nearby bus arrivals
    """
    arrivals_nearby = get_arrows(arrivals_nearby)

    arrivals_nearby['6/7'] = {'←': []}
    for line in ['6', '7']:
        if line in arrivals_nearby:
            arrivals_nearby['6/7']['←'].extend(arrivals_nearby[line].get('←', []))
            del arrivals_nearby[line]['←']

    return arrivals_nearby


def print_times(arrivals_nearby):
    """
    Prints minutes until next 3 buses for each line
    (next 5 for combined lines), per direction.

    :param arrivals_nearby: custom dict from parse_times function
    :return: printed list
    """
    arrivals_nearby = combine_6_7(arrivals_nearby)

    # Create sort_keys dict such that 6/7 gets 0 and all other lines get their int value
    sort_keys = {}
    for line in arrivals_nearby:
        if line == '6/7':
            sort_keys[line] = 0
        elif line == 'NOWL':
            sort_keys[line] = 100
        else:
            sort_keys[line] = int(line)

    # Sort arrivals_nearby by new sort_key, so 6/7 is on top
    arrivals_nearby_sorted = sorted(arrivals_nearby.items(),
                                    key=lambda arrival: sort_keys[arrival[0]])

    # Print only upcoming arrivals in ascending order of line and time
    for line, arrivals in arrivals_nearby_sorted:
        for direction, times in sorted(arrivals.items()):
            times = sorted(times)[:5] if line == '6/7' else sorted(times)[:3]
            time_str = ', '.join(str(time) for time in times)
            print(f'{line} {direction} in {time_str} minutes')


def epaper(arrivals_nearby):
    print('epaper')


def trigger_6_7(arrivals_nearby, trigger):
    """
    Triggers a webhook if a 6 or 7 is arriving in 'n' minutes.
    :param arrivals_nearby: custom dict with nearby bus arrivals
    :param trigger: number of minutes at which webhook should be triggered

    >>> trigger_6_7({'7': {'←': [1]}}, 1)
    6/7 in 1 minutes! Sent IFTTT webhook.
    >>> trigger_6_7({'6': {'←': [5]}}, 1)
    Next 6/7 ← in 5 minutes
    """
    # Combine 6/7 ← using helper function
    arrivals_nearby = combine_6_7(arrivals_nearby)

    if '6/7' not in arrivals_nearby or arrivals_nearby['6/7'] == {'←': []}:
        print('No 6/7 on the horizon.')

    elif trigger in arrivals_nearby['6/7']['←']:
        url = 'https://maker.ifttt.com/trigger/bus_soon/with/key/' + KEY_IFTT
        # Send web request to IFTT webhook address
        response = requests.post(url)
        print(f'6/7 in {trigger} minutes! Sent IFTTT webhook.' if response.status_code == 200
              else 'Failed to trigger the webhook.')

    else:
        window_min, window_max = 2, 20
        arrivals_6_7 = sorted(arrivals_nearby['6/7']['←'])
        next_6_7 = [str(n) for n in arrivals_6_7 if window_min < n < window_max]
        print(f'Next 6/7 ← in {', '.join(next_6_7)} minutes' if next_6_7
              else f'No 6/7 in the next {window_max} minutes.')


def main():
    parser = argparse.ArgumentParser(description="Get nearby bus times")
    parser.add_argument('-print', action='store_true',
                        help='print bus times')
    parser.add_argument('-epaper', action='store_true',
                        help='display output on e-paper')
    parser.add_argument('-trig', nargs=2, type=int,
                        help='[requires two ints] trigger IFTT when 6/7 {int1} mins away, every min for {int2} mins')
    parser.add_argument('-shelve', action='store_true',
                        help='get and shelve API data')
    parser.add_argument('-dev', action='store_true',
                        help='[opt for -print, -trigger, -epaper] use shelved data')

    args = parser.parse_args()

    if args.print:
        all_data = get_times.call_511('SF') if not args.dev else get_times.get_from_shelf()
        arrivals_nearby = get_times.parse_times(all_data)
        print_times(arrivals_nearby)

    if args.epaper:
        all_data = get_times.call_511('SF') if not args.dev else get_times.get_from_shelf()
        arrivals_nearby = get_times.parse_times(all_data)
        epaper(arrivals_nearby)

    if args.trig:
        trigger, loops = args.trig
        for i in range(loops):
            if loops > 1:  # Don't print if loop = 1 (default if no input)
                print(f'Loop {i + 1} of {loops}')
            all_data = get_times.call_511('SF') if not args.dev else get_times.get_from_shelf()
            arrivals_nearby = get_times.parse_times(all_data)
            trigger_6_7(arrivals_nearby, trigger)
            if i + 1 != loops:  # Don't sleep on last loop
                time.sleep(60)

    if args.shelve:
        get_times.call_511('SF', dev=True)
        print('API response shelved')


if __name__ == "__main__":
    main()
