# covid19Tracker
Tracking Covid19 Cases in Ireland

###### Source: Data Gathered from the Irish Health Department Public Announcements @ https://www.gov.ie/en/campaigns/c36c85-covid-19-coronavirus/

###### Mapped using https://www.datawrapper.de

### Overview
A simple project mapping cases of covid-19 in Ireland. It (¡will!) pulls data from the [Irish Health Department](https://www.gov.ie/en/campaigns/c36c85-covid-19-coronavirus/) notices at [gov.ie](https://www.gov.ie) when a new notice is published.
The data is parsed and pushed in csv format to a python map worker interfacing with [datawrapper](https://www.datawrapper.de) which updates a choropleth map of Ireland(can also create a new map).
The updated map is published on datawrapper, links are pulled from datawrapper and published via django (/map).

### Setup:

1. Create the following env vars on the host machine:
* `DATAWRAPPER_AUTH_CODE` _to interact with the datawrapper api, your accounts API token is required, can be retrieved from your account settings_
* `DJANGO_SECRET_KEY` _django auth key pulled to settings.py_

### Usage:

###### Create Map:
New Choropleth Creation with settings for Non-Admin Ireland Counties.

`python map_worker.py create`

###### Update Existing Map:
Trigger manual update of existing Map:
(id of last creation stored in data_retrieval/config.ini)

`python map_worker.py update`