#!/usr/bin/env python3

"""
Get bus times for my nearby stops
Dedicated to CS 106A
"""

import configparser
import json
import math
import os
import shelve
from datetime import datetime, timezone

import requests

from config import STOPCODES

config = configparser.ConfigParser()
config.read('config.ini')

KEY_511 = config['KEYS']['KEY_511']

def call_511(agency, stopcode=None, dev=False):
    """
    Given agency code, uses 511.org API to get stop predictions for all stops in agency network.
    API details at https://511.org/open-data/transit

    :param agency: use 'SF' for SFMTA
    :param stopcode: pass only if you want data for a single stop
    :param dev: if True, writes data to local test database
    :return: all data from 511.org Real-time Stop Monitoring API
    """
    url = 'http://api.511.org/transit/StopMonitoring'
    params = {'api_key': KEY_511, 'agency': agency, 'stopcode': stopcode}

    # Make GET request
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve data: {response.status_code}")

    # Parse response JSON and load into variable
    content = response.content.decode('utf-8-sig')
    all_data = json.loads(content)

    if dev:
        # Delete existing shelf file
        if os.path.exists('test.db'):
            os.remove('test.db')
        # Shelve API response
        with shelve.open('test') as db:
            db['all_data'] = all_data
    else:
        return all_data


def get_from_shelf():
    """
    Gets all_data from shelf.
    
    :return: all_data
    :raises FileNotFoundError: if the shelf file does not exist
    """
    if not os.path.exists('test.db'):
        raise FileNotFoundError('test.db not found. Initiate with -shelve')
    with shelve.open('test') as db:
        all_data = db['all_data']
        return all_data


def export_shelf():  # not working
    all_data = get_from_shelf()

    import pandas as pd
    visits_all = all_data['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']
    # print(visits_all)

    df = pd.DataFrame(visits_all)
    print(df)

    # Export to CSV
    # csv_file_path = 'bus_times.csv'  # Replace with your desired CSV file path
    # df.to_csv(csv_file_path, index=False)


def parse_times(all_data):
    """
    Reads API response and returns only needed details.
    :param all_data: unaltered API response from 511.org Real-time Stop Monitoring API
    :return: dict with line, direction, and minutes to upcoming arrivals for stops in STOPCODES
    """
    # Save visit data for nearby stops only in new list
    visits_all = all_data['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']
    visits_nearby = [visit for visit in visits_all if int(visit['MonitoringRef']) in STOPCODES]

    # Save relevant data from stop_visits_nearby in new dict
    arrivals_nearby = {}
    now = datetime.now(timezone.utc)
    for visit in visits_nearby:
        journey = visit['MonitoredVehicleJourney']
        line = journey['LineRef']
        direction = journey['DirectionRef']

        # Convert predicted time to minutes remaining
        exp_arr_str = journey['MonitoredCall']['ExpectedArrivalTime']
        exp_arr = datetime.strptime(exp_arr_str, '%Y-%m-%dT%H:%M:%S%z')
        exp_arr_delta = math.floor((exp_arr - now).total_seconds() / 60)  # rounds down

        # Add relevant arrival times to dictionary, by key=line
        if line not in arrivals_nearby:
            arrivals_nearby[line] = {}
        if direction not in arrivals_nearby[line]:
            arrivals_nearby[line][direction] = []
        arrivals_nearby[line][direction] += [exp_arr_delta]

    return arrivals_nearby


if __name__ == "__main__":
    print('Please run display_times.py instead')
    # export_shelf()
