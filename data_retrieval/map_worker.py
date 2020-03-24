#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script calls the datawrapper api @ https://www.datawrapper.de to create a
Choropleth map of Ireland to model Covid-19 cases across the country using
the Non-Administrative County boundaries(ireland-counties-notadmin).
Can be run to either create a new map from scratch or
update an existing map via it's active map ID stored in config.ini
"""
import os
import argparse
import csv
import json
import logging
import configparser
from datetime import datetime
import requests

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class DataWrapperMap:
    """
    DataWrapperMap Class
    Operations to interact with the datawrapper service
    """
    def __init__(self, config):
        """
        DataWrapper Map constructor
        :param config: settings
        """
        self.config = config

        self.api_auth_code = os.environ[self.config['DATA_WRAPPER']['API_AUTH_CODE']]
        self.map_id = self.config['DATA_WRAPPER']['MAP_ID']

        self.html_map_output = os.path.join(os.getcwd(),
                                            self.config['DATA_SOURCES']['HTML_OUTPUT_FILE_PATH'])
        self.csv_file_path = os.path.join(os.getcwd(),
                                          self.config['DATA_SOURCES']['OUTPUT_CSV_FILE_PATH'])

    def set_map_id(self):
        """
        Set the current map id in the config.ini file for later use
        Only to avoid creating a brand new map on each run
        TODO: rework this
        """
        logging.debug("Writing new map_id to config file: %s", self.map_id)
        self.config.set("DATA_WRAPPER", "MAP_ID", self.map_id)
        with open(os.path.join(BASE_DIR, 'config.ini'), 'w') as cfg_file:
            self.config.write(cfg_file)

    def create_choropleth(self):
        """
        Create a new choropleth map of Ireland
        """
        url = 'https://api.datawrapper.de/v3/charts'
        payload = '{ "title": "Irish Covid19 Cases", "type":"d3-maps-choropleth"}'
        headers = {'content-type': 'application/json',
                   'Authorization': 'Bearer ' + self.api_auth_code}
        response = requests.post(url, data=payload, headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Map Create Failed: error was: %s", err)
        logging.debug("Created new choropleth with map_id: %s", self.map_id)

        self.map_id = response.json()['id']
        # Store the map id for subsequent runs
        self.set_map_id()

    def configure_map_settings(self):
        """
        Configure map settings via datawrapper api
        """
        url = 'https://api.datawrapper.de/v3/charts/' + self.map_id
        headers = {'content-type': 'application/json',
                   'Authorization': 'Bearer ' + self.api_auth_code}
        payload = {
            "metadata": {
                "axes": {
                    "keys": "county",
                    "labels": "county",
                    "values": "cases"
                },
                "tooltip": {
                    "body": "{{ cases }} cases.",
                    "title": "{{ county }}",
                    "fields": {
                        "cases": "cases",
                        "county": "county"
                    }
                },
                "visualize": {
                    "basemap": "ireland-counties-notadmin",
                    "map-key-attr": "FIRST_CO_E",
                    "map-key-format": "0",
                    "map-key-position": "br",
                    "zoomable": True,
                    "map-label-label": "county",
                    "map-label-zoom": "1",
                    "min-label-zoom": "1"
                },
                "describe": {
                    "source-name": "Irish Department of Health",
                    "source-url": "https://www.gov.ie/en/campaigns/c36c85-covid-19-coronavirus/",
                    "number-format": "-"
                },
                "publish": {
                    "embed-width": 600,
                    "embed-height": 600
                }
            }
        }
        response = requests.patch(url, data=json.dumps(payload), headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Map configuration setting failed: error was: %s", err)
        logging.debug("Updated map settings for map_id: %s", self.map_id)

    def add_map_tooltip(self):
        """
        Add a tooltip for the map
        This adds a mouseover message when the user hovers over each county
        format:  County
                [count of cases] cases.
        """
        url = 'https://api.datawrapper.de/v3/charts/' + self.map_id
        headers = {'content-type': 'application/json',
                   'Authorization': 'Bearer ' + self.api_auth_code}
        payload = {
            "metadata": {
                "visualize": {
                    "tooltip": {
                        "body": "{{ cases }} cases.",
                        "title": "{{ county }}",
                        "fields": {
                            "cases": "cases",
                            "county": "county"
                        }
                    }
                }
            }
        }
        response = requests.patch(url, data=json.dumps(payload), headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Tooltip add failed for map_id: %s: error was: %s", self.map_id, err)
        logging.debug("Added tooltip hover settings for map_id: %s", self.map_id)

    def update_map_data(self):
        """
        Add/Update the map data
        The API works best with CSV format
        Read the CSV on disk and Publish to our map
        Expected format for 'ireland-counties-notadmin' is:
            county,cases
            CARLOW,5
            CAVAN,5 ...
        """
        url = 'https://api.datawrapper.de/v3/charts/' + self.map_id + '/data'
        headers = {'accept': "*/*",
                   'content-type': 'text/csv',
                   'Authorization': 'Bearer ' + self.api_auth_code}
        county_results = ""
        with open(self.csv_file_path) as csv_file:
            csv_data = csv.reader(csv_file, delimiter=',')
            for row in csv_data:
                county_results += (', '.join(row) + '\n')
        response = requests.put(url, data=county_results, headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Update of map data failed: error was: %s", err)
        logging.debug("Map data updated successfully from csv for map_id: %s", self.map_id)

    def set_last_update_timestamp(self):
        """
        Set the last update time to now which will be shown
        on our map in the format: 'Last update:03/21/2020, 18:39:33 PM'
        """
        now = datetime.now()
        timestamp_now = now.strftime("%m/%d/%Y, %H:%M:%S %p")

        url = 'https://api.datawrapper.de/v3/charts/' + self.map_id
        headers = {'content-type': 'application/json',
                   'Authorization': 'Bearer ' + self.api_auth_code}
        payload = {"metadata": {"annotate": {"notes": "Last update:" + timestamp_now}}}
        response = requests.patch(url, data=json.dumps(payload), headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Set timestamp fail for map_id: %s: error was: %s", self.map_id, err)
        logging.debug("Set last update timestamp for map_id: %s", self.map_id)

    def publish_map(self):
        """
        Publish the map to datawrapper
        Write the published iframe method to a html page
        to be picked up by the web server host
        """
        self.set_last_update_timestamp()
        url = 'https://api.datawrapper.de/charts/' + self.map_id + '/publish'
        headers = {'content-type': 'application/json',
                   'Authorization': 'Bearer ' + self.api_auth_code}
        response = requests.post(url, headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Map publishing fail for map_id: %s: error was: %s", self.map_id, err)
        logging.debug("Map published successfully for map_id: %s", self.map_id)
        embed_codes = response.json()['data']['metadata']['publish']

        #  Refactor this - currently writing the html iframe we get from the datawrapper
        #  when creating a new map (not needed when updating as the latest version of
        #  the map will be automatically collected)
        logging.debug("Writing html iframe to disk for map_id: %s", self.map_id)
        with open(self.html_map_output, "w") as html_file:
            html_file.write(embed_codes['embed-codes']['embed-method-responsive'])

    def run_map_creation(self):
        """
        Create Map with case data and publish to datawrapper
        """
        self.create_choropleth()
        self.configure_map_settings()
        self.add_map_tooltip()
        self.update_map_data()
        self.publish_map()

    def run_map_update(self):
        """
        Update Map data using existing map_id
        and publish to datawrapper
        """
        self.update_map_data()
        self.publish_map()


def main():
    """
    Main Call
    Initiates a map create or update
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("run_type",
                        help="Create or Update a Map")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(os.path.join(BASE_DIR, 'config.ini'))

    logging.basicConfig(filename=os.path.join(os.getcwd(),
                                              config['LOGGING']['LOG_DIR'],
                                              'map_worker.log'),
                        format='%(asctime)s - %(message)s',
                        level=config['LOGGING']['LOG_LEVEL'])

    mapper = DataWrapperMap(config)

    if args.run_type == "create":
        logging.info("Initiating map creation process")
        mapper.run_map_creation()
    elif args.run_type == "update":
        logging.info("Initiating map data update process")
        mapper.run_map_update()


if __name__ == '__main__':
    main()
