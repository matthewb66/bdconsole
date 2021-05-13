# bdconsole
Black Duck Dash Batch Console v1.0 Beta

This script is provided under an OSS license (specified in the LICENSE file) to assist users when scanning projects using the Synopsys Detect program to scan projects.

# Introduction

This is a plotly Dash app for viewing and managing components, vulnerabilities and snippets in a [Black Duck](https://www.synopsys.com/software-integrity/security-testing/software-composition-analysis.html) server using the API.

It communicates with the Black Duck server using HTTPS via an API key, but uses HTTP for communication to users. Deploy a front-end web server to add HTTPS if secure user communication is required (see the Security section below). A production (multi-user) deployment can also be supported (see the Deployment section below).

At startup, it will request the URL and API key for the Black Duck software and then load the list of all projects.

# Installation

Download and install the program as follows:

1. Download using `git clone https://github.com/matthewb66/bconsole`
1. Optionally create a Python virtualenv.
1. Install using `pip3 install -r requirements.txt`

# Starting the Console

The application can be started locally (standalone non-production, single-user mode) using the command:

       python3 app.py

Access the UI using the URL shown in the console log (usually http://127.0.0.1:8889).

You will need to enter the Black Duck server URL and a valid API key initially to create a session.

See the Deployment section below for information on hosting the application for multi-user, production usage as well as options to add security.

# Using the Console

The start screen will show a list of all projects in a Dash Datatable.

All the tables in the console can be sorted by column and filtered using the supported [filter syntax](https://dash.plotly.com/datatable/filtering) entered within the filter row (below the table header row).

Select a project of interest in the table using the radio button on the row, which will load the project versions in the version table on the right.

Then select a project version to load the components, vulnerabilities and snippets.

# Features Supported

In the components, vulnerabilities and snippets tabs, you can filter and sort entries, as well as multi-select rows using checkboxes.

You can then select actions in the drop-down list and run on either the selected rows (`Selected Rows` button) or all filtered rows in the table (`All Filtered Rows` button), which will perform the action synchronously (you will need to wait for completion which may take some time).

Note that ignoring components will mean that vulnerabilities are no longer applicable for a project, so you can reload the vulnerabilies using the `Reload` button in the Vulnerabilities tab.

# Project Version Trend Graph

This tab allows the creation of an approximated component and vulnerability trend graph by processing the audit log for a Project Version. Please note that the trend will show changes in the list of components caused by rescans, ignoring components etc. but is only an approximation, and that the count of vulnerabilities will not tally with the number shown in the Vulnerabilities tab because it shows unique vulnerabilities based on ID (BDSA or CVE) as opposed to all associated vulnerabilities which can have duplicates across components and origins.

# Deploying the Console for Production

The console application can be run standalone on a workstation using python3 for debugging or single user access.

However Plotly Dash applications can also be hosted for production (multi-user) access on custom servers, Dash Enterprise, using an app server (such as Gunicorn) or within hosting services such as Heroku - see https://dash.plotly.com/deployment.

# Securing the Console

The application communicates with the Black Duck server using an API token (only stored in a running session and not within the application) over HTTPS.
The web a[[lic

Basic HTTP authentication can be enabled (by uncommenting code in the app.py main file), but this is insecure and stores usernames and passwords in plain text.

Use a web server (for example Nginx) to host the application and upgrade the communication to HTTPS or add user authentication. See this [link](https://docs.gunicorn.org/en/stable/deploy.html) for information on using Gunicorn and Nginx for hosting.




