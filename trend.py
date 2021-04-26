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

    now = datetime.now()

    for event in eventlist:
        evtype = ''
        if event['type'] == 'COMP_ADDED':
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
            timelist_comps.append({'timestamp': event['timestamp'], 'comp_count': len(comp_dict),
                                   'ignored_count': len(comp_ignored_list)})
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
            timelist_vulns.append({'timestamp': event['timestamp'], 'vuln_count': len(vuln_list),
                                   'ignored_count': len(vuln_ignored_list),
                                   'remediated_count': len(vuln_remediated_list),
                                   'patched_count': len(vuln_patched_list)})

    timelist_comps.append({'timestamp': now.strftime("%Y/%m/%d %H:%M:%S"), 'comp_count': len(comp_dict),
                           'ignored_count': len(comp_ignored_list)})

    timelist_vulns.append({'timestamp': now.strftime("%Y/%m/%d %H:%M:%S"), 'vuln_count': len(vuln_list),
                           'ignored_count': len(vuln_ignored_list),
                           'remediated_count': len(vuln_remediated_list),
                           'patched_count': len(vuln_patched_list)})
    # print(json.dumps(timelist_comps, indent=4))

    return timelist_comps, timelist_vulns


def proc_journals(hub, url):

    # compeventaction_dict = {}
    # compeventtime_dict = {}

    if url is None:
        return

    headers = {'Accept': 'application/vnd.blackducksoftware.journal-4+json'}
    arr = url.split('/')
    # https://poc39.blackduck.synopsys.com/api/projects/5e048290-0d1d-4637-a276-75d7cb50de6a/versions/3b14487c-c860-471d-bee1-c7d443949df5/components

    journallurl = "{}/api/journal/projects/{}/versions/{}?limit=50000".format('/'.join(arr[:3]), arr[5], arr[7])
    response = hub.execute_get(journallurl, custom_headers=headers)
    jsondata = response.json()

    if not response.ok:
        return None, None

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
        print(event)
        if event['action'] == 'Component Added':
            if 'version' in event['currentData']:
                compname = event['objectData']['name'] + "/" + event['currentData']['version']
            else:
                compname = event['objectData']['name']
            events.append({'timestamp': event['timestamp'], 'type': 'COMP_ADDED', 'comp': compname})
            print('RAW COMPONENT ADDED')
        if event['action'] == 'Component Ignored':
            if 'version' in event['currentData']:
                compname = event['objectData']['name'] + "/" + event['currentData']['version']
            else:
                compname = event['objectData']['name']
            events.append({'timestamp': event['timestamp'], 'type': 'COMP_IGNORED', 'comp': compname})
            print('RAW COMPONENT IGNORED')
        if event['action'] == 'Component Deleted':
            if 'version' in event['currentData']:
                compname = event['objectData']['name'] + "/" + event['currentData']['version']
            else:
                compname = event['objectData']['name']
            events.append({'timestamp': event['timestamp'], 'type': 'COMP_REMOVED', 'comp': compname})
            print('RAW COMPONENT REMOVED')
        if event['action'] == 'Vulnerability Found':
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
        if event['action'] == 'Remediation Updated':
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

    # headers = {'Accept': 'application/vnd.blackducksoftware.journal-4+json'}
    # url = "{}/journal/projects/{}?limit=10000".format(hub.get_apibase(), pjprojid)
    # response = hub.execute_get(url, custom_headers=headers)
    # jsondata = response.json()
    #
    # event_list = jsondata['items']
    # ver_create_date = ''
    # for event in event_list:
    #     if event['objectData']['type'] == 'VERSION' and event['objectData']['name'] == pjvername:
    #         ver_create_date = event['timestamp']
    #
    #     if event['timestamp'] > ver_create_date and event['objectData']['type'] == 'COMPONENT' \
    #             and event['currentData']['adjustmentType'] == 'Ignore':
    #         if 'releaseVersion' in event['currentData']:
    #             compname = event['objectData']['name'] + "/" + event['currentData']['releaseVersion']
    #         else:
    #             compname = event['objectData']['name']
    #         events.append({'timestamp': event['timestamp'], 'type': 'IGNORED', 'comp': compname})
    #         # print('COMP_IGNORED')
    #     # print(event['timestamp'] + ": ", event['currentData'])

    print()

    def my_sort(e):
        return e['timestamp']

    events.sort(key=my_sort)

    # print()
    # print(json.dumps(comp_events, indent=4))

    return proc_events(events)


def create_fig_compstimeline(compevents):
    df = pd.DataFrame(compevents)

    if not compevents:
        df["timestamp"] = ''
        df["comp_count"] = 0

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

    fig = px.scatter(df, x='timestamp', y=['comp_count', 'ignored_count'], labels={'x': 'Components',
                                                                                   'y': 'Ignored Components'})
    fig.update_traces(mode='lines')

    return fig


def create_fig_vulnstimeline(vulnevents):
    df = pd.DataFrame(vulnevents)

    if not vulnevents:
        df["timestamp"] = ''
        df["vuln_count"] = 0

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

    fig = px.scatter(df, x='timestamp', y=['vuln_count', 'ignored_count', 'remediated_count', 'patched_count'])
    fig.update_traces(mode='lines')

    return fig
