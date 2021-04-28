import pandas as pd
import plotly.express as px
from datetime import datetime


def remove_vulns(vuln_comp_dict, component, vuln_list):
    if component in vuln_comp_dict.values():
        for vuln in vuln_comp_dict.keys():
            if vuln_comp_dict[vuln] == component and vuln in vuln_list:
                print("Vulnerability REMOVED: {} (due to component {} being REMOVED)".format(vuln, component))
                vuln_list.remove(vuln)
    return vuln_list


def proc_events(eventlist):
    comp_dict = {}
    comp_ignored_list = []

    vuln_comp_dict = {}
    vuln_list = []
    vuln_ignored_list = []
    vuln_remediated_list = []
    vuln_patched_list = []

    timelist_comps = []
    timelist_vulns = []
    scans = []

    now = datetime.now()

    for event in eventlist:
        evtype = ''

        if event['type'] == 'SCAN_MAPPED' or event['type'] == 'SCAN_UNMAPPED':
            if event['type'] == 'SCAN_MAPPED':
                text = 'Scans Mapped'
            else:
                text = 'Scans Unmapped'

            scans.append(
                {
                    'timestamp': datetime.strptime(event['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                    'components': len(comp_dict),
                    'vulns': len(vuln_list),
                    'text': text,
                }
            )
        elif event['type'] == 'COMP_ADDED':
            if event['comp'] not in comp_dict.keys():
                comp_dict[event['comp']] = 1
                evtype = 'comp'
                print("Component ADDED: {} (total = {}) - {}".format(event['comp'], len(comp_dict), event['timestamp']))
            else:
                comp_dict[event['comp']] += 1

        elif event['type'] == 'COMP_REMOVED':
            if event['comp'] in comp_dict.keys():
                if comp_dict[event['comp']] == 1:
                    comp_dict.pop(event['comp'])
                    evtype = 'comp'
                    print("Component REMOVED: {} (total = {}) - {}".format(event['comp'], len(comp_dict),
                                                                           event['timestamp']))
                    vuln_list = remove_vulns(vuln_comp_dict, event['comp'], vuln_list)
                else:
                    comp_dict[event['comp']] -= 1

            elif event['comp'] in comp_ignored_list:
                comp_ignored_list.remove(event['comp'])
                print("Component REMOVED (IGNORED): {} (total = {}) - {}".format(event['comp'], len(comp_dict),
                                                                                 event['timestamp']))
                evtype = 'comp'
        elif event['type'] == 'COMP_IGNORED':
            if event['comp'] in comp_dict.keys():
                if comp_dict[event['comp']] > 0:
                    comp_dict.pop(event['comp'])
                    comp_ignored_list.append(event['comp'])
                    evtype = 'comp'
                    print("Component IGNORED: {} (total = {})".format(event['comp'], len(comp_dict),
                                                                      event['timestamp']))

        if evtype == 'comp':
            timelist_comps.append({'timestamp': event['timestamp'], 'Components': len(comp_dict),
                                   'Ignored Components': len(comp_ignored_list)})
            timelist_vulns.append({'timestamp': event['timestamp'], 'Unique Vulns': len(vuln_list),
                                   'Ignored Vulns': len(vuln_ignored_list),
                                   'Remediated Vulns': len(vuln_remediated_list),
                                   'Patched Vulns': len(vuln_patched_list)})
        else:
            if event['type'] == 'VULN_ADDED' and event['vuln'] not in vuln_list:
                vuln_list.append(event['vuln'])
                # print(event)
                vuln_comp_dict[event['vuln']] = event['comp']
                evtype = 'vuln'
                print("Vulnerability ADDED: {} (total = {}) {}".format(event['vuln'], len(vuln_list),
                                                                       event['timestamp']))

            if event['type'] == 'VULN_REMEDIATED' and event['vuln'] in vuln_list:
                vuln_list.remove(event['vuln'])
                vuln_remediated_list.append(event['vuln'])
                evtype = 'vuln'
                print("Vulnerability REMEDIATED: {} (total = {}) {}".format(event['vuln'], len(vuln_list),
                                                                            event['timestamp']))
            if event['type'] == 'VULN_IGNORED' and event['vuln'] in vuln_list:
                vuln_list.remove(event['vuln'])
                vuln_ignored_list.append(event['vuln'])
                evtype = 'vuln'
                print("Vulnerability IGNORED: {}  (total = {}) {}".format(event['vuln'], len(vuln_list),
                                                                          event['timestamp']))
            if event['type'] == 'VULN_PATCHED' and event['vuln'] in vuln_list:
                vuln_list.remove(event['vuln'])
                vuln_patched_list.append(event['vuln'])
                evtype = 'vuln'
                print("Vulnerability PATCHED: {} (total = {}) {}".format(event['vuln'], len(vuln_list),
                                                                         event['timestamp']))
        if evtype == 'vuln':
            timelist_vulns.append({'timestamp': event['timestamp'], 'Unique Vulns': len(vuln_list),
                                   'Ignored Vulns': len(vuln_ignored_list),
                                   'Remediated Vulns': len(vuln_remediated_list),
                                   'Patched Vulns': len(vuln_patched_list)})
            timelist_comps.append({'timestamp': event['timestamp'], 'Components': len(comp_dict),
                                   'Ignored Components': len(comp_ignored_list)})


    timelist_comps.append({'timestamp': now.strftime("%Y/%m/%d %H:%M:%S"), 'Components': len(comp_dict),
                           'Ignored Components': len(comp_ignored_list)})

    timelist_vulns.append({'timestamp': now.strftime("%Y/%m/%d %H:%M:%S"), 'Unique Vulns': len(vuln_list),
                           'Ignored Vulns': len(vuln_ignored_list),
                           'Remediated Vulns': len(vuln_remediated_list),
                           'Patched Vulns': len(vuln_patched_list)})
    # print(json.dumps(timelist_comps, indent=4))

    return timelist_comps, timelist_vulns, scans


def proc_journals(hub, projverurl, pjvername):

    # compeventaction_dict = {}
    # compeventtime_dict = {}

    if projverurl is None:
        return None, None, None

    headers = {'Accept': 'application/vnd.blackducksoftware.journal-4+json'}
    arr = projverurl.split('/')
    # https://poc39.blackduck.synopsys.com/api/projects/5e048290-0d1d-4637-a276-75d7cb50de6a/versions/3b14487c-c860-471d-bee1-c7d443949df5/components

    projjournalurl = "{}/api/journal/projects/{}".format('/'.join(arr[:3]), arr[5])
    verjournalurl = "{}/versions/{}?limit=50000".format(projjournalurl, arr[7])
    response = hub.execute_get(verjournalurl, custom_headers=headers)

    if not response.ok:
        return None, None, None
    jsondata = response.json()

    # def addcompeevent(ceventaction_dict, ceventtime_dict, cname, ctime):
    #     if cname not in ceventaction_dict.keys():
    #         ceventaction_dict[cname] = ['ADDED']
    #         ceventtime_dict[cname] = [ctime]
    #     else:
    #         # find recent events for this component
    #         recentevents = []
    #         for index in range(len(ceventtime_dict[cname]), 0, -1):
    #

    event_list = jsondata['items']
    events = []
    for event in event_list:
        if event['action'] == 'Scan Mapped':
            print(event)
            events.append({'timestamp': event['timestamp'], 'type': 'SCAN_MAPPED'})
        elif event['action'] == 'Scan Unmapped':
            print(event)
            events.append({'timestamp': event['timestamp'], 'type': 'SCAN_UNMAPPED'})
        elif event['action'] == 'Component Added':
            if 'version' in event['currentData']:
                compname = event['objectData']['name'] + "/" + event['currentData']['version']
            else:
                compname = event['objectData']['name']
            events.append({'timestamp': event['timestamp'], 'type': 'COMP_ADDED', 'comp': compname})
            print('RAW COMPONENT ADDED')
        elif event['action'] == 'Component Ignored':
            if 'version' in event['currentData']:
                compname = event['objectData']['name'] + "/" + event['currentData']['version']
            else:
                compname = event['objectData']['name']
            events.append({'timestamp': event['timestamp'], 'type': 'COMP_IGNORED', 'comp': compname})
            print('RAW COMPONENT IGNORED')
        elif event['action'] == 'Component Deleted':
            if 'version' in event['currentData']:
                compname = event['objectData']['name'] + "/" + event['currentData']['version']
            else:
                compname = event['objectData']['name']
            events.append({'timestamp': event['timestamp'], 'type': 'COMP_REMOVED', 'comp': compname})
            print('RAW COMPONENT REMOVED')
        elif event['action'] == 'Vulnerability Found':
            # print(event)
            vulnname = event['objectData']['name']
            vulnsev = event['currentData']['riskPriority']
            # vulnlink = event['objectData']['link']
            if 'releaseVersion' in event['currentData']:
                compname = event['currentData']['projectName'] + "/" + event['currentData']['releaseVersion']
            else:
                compname = event['currentData']['projectName']

            events.append({'timestamp': event['timestamp'], 'type': 'VULN_ADDED',
                           'vuln': vulnname,
                           'comp': compname,
                           'vulnsev': vulnsev})
            print('RAW VULN_ADDED')
        elif event['action'] == 'Remediation Updated':
            # print(event)
            vulnname = event['objectData']['name']
            vulnsev = ''
            # vulnlink = event['objectData']['link']
            if 'componentVersion' in event['currentData']:
                compname = event['currentData']['componentName'] + "/" + event['currentData']['componentVersion']
            else:
                compname = event['currentData']['componentName']

            evtype = ''
            if event['currentData']['remediationStatus'] == 'Remediation Complete':
                evtype = 'VULN_REMEDIATED'
            if event['currentData']['remediationStatus'] == 'Ignored':
                evtype = 'VULN_IGNORED'
            if event['currentData']['remediationStatus'] == 'Patched':
                evtype = 'VULN_PATCHED'
            if evtype != '':
                # print(type)
                events.append({'timestamp': event['timestamp'],
                               'type': evtype,
                               'vuln': vulnname,
                               'comp': compname,
                               'vulnsev': vulnsev})

    # Need to check that this project has project propagation first
    #
    headers = {'Accept': 'application/vnd.blackducksoftware.project-detail-4+json'}

    arr = projverurl.split('/')
    projurl = "{}/api/projects/{}".format('/'.join(arr[:3]), arr[5])
    response = hub.execute_get(projurl, custom_headers=headers)

    if not response.ok:
        return None, None
    projconf = response.json()

    if 'projectLevelAdjustments' in projconf and projconf['projectLevelAdjustments']:
        # Project version uses project level adjustments

        headers = {'Accept': 'application/vnd.blackducksoftware.journal-4+json'}

        response = hub.execute_get(projjournalurl + '?limit=50000', custom_headers=headers)
        if response.ok:
            jsondata = response.json()

            event_list = jsondata['items']
            ver_create_date = ''
            for event in event_list:
                if event['objectData']['type'] == 'VERSION' and event['objectData']['name'] == pjvername:
                    ver_create_date = event['timestamp']

                if event['timestamp'] > ver_create_date and event['objectData']['type'] == 'COMPONENT' \
                        and event['currentData']['adjustmentType'] == 'Ignore':
                    if 'releaseVersion' in event['currentData']:
                        compname = event['objectData']['name'] + "/" + event['currentData']['releaseVersion']
                    else:
                        compname = event['objectData']['name']
                    events.append({'timestamp': event['timestamp'], 'type': 'IGNORED', 'comp': compname})
                    # print('COMP_IGNORED')
                # print(event['timestamp'] + ": ", event['currentData'])

    print()

    def my_sort(e):
        return e['timestamp']

    events.sort(key=my_sort)

    # print()
    # print(json.dumps(comp_events, indent=4))

    return proc_events(events)


def create_fig_compstimeline(compevents, scans):
    df = pd.DataFrame(compevents)

    if not compevents:
        df["timestamp"] = ''
        df["Components"] = 0

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

    fig = px.scatter(df, x='timestamp', y=['Components', 'Ignored Components'])
    fig.update_traces(mode='lines')
    fig.update_yaxes(title_text='Components')
    fig.update_xaxes(title_text='Date')

    prevscan = None
    for scan in scans:
        if prevscan is not None and prevscan['text'] == scan['text']:
            diff = scan['timestamp'] - prevscan['timestamp']
            if diff.total_seconds() < 120:
                prevscan = scan
                continue
        fig.add_annotation(row=1, col=1, y=scan['components'], x=scan['timestamp'], text=scan['text'], arrowhead=1)
        prevscan = scan

    return fig


def create_fig_vulnstimeline(vulnevents, scans):
    df = pd.DataFrame(vulnevents)

    if not vulnevents:
        df["timestamp"] = ''
        df["Unique Vulns"] = 0

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

    fig = px.scatter(df, x='timestamp', y=['Unique Vulns', 'Ignored Vulns', 'Remediated Vulns',
                                           'Patched Vulns'])
    fig.update_traces(mode='lines')
    fig.update_yaxes(title_text='Vulnerabilities')
    fig.update_xaxes(title_text='Date')

    prevscan = None
    for scan in scans:
        if prevscan is not None and prevscan['text'] == scan['text']:
            diff = scan['timestamp'] - prevscan['timestamp']
            if diff.total_seconds() < 120:
                prevscan = scan
                continue
        fig.add_annotation(row=1, col=1, y=scan['vulns'], x=scan['timestamp'], text=scan['text'], arrowhead=1)
        prevscan = scan

    return fig
