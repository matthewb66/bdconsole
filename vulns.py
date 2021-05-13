import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_table


def get_vulns_data(bd, projverurl):
    print('Getting Vulnerabilities ...')
    # custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
    # res = hub.execute_get(projverurl + '/vulnerable-bom-components?limit=5000', custom_headers=custom_headers)
    # if res.status_code != 200:
    #     print('Get vulnerabilities - return code ' + res.status_code)
    #     return None
    # vulns = res.json()

    vulns = bd.get_json(projverurl + '/vulnerable-bom-components?limit=5000')
    df = pd.json_normalize(vulns, record_path=['items'])
    # for index, vuln in enumerate(vulns['items']):
    #     df.loc[index, 'json'] = json.dumps(vuln)

    # df = df.drop_duplicates(subset=['componentVersion',
    #                                 'vulnerabilityWithRemediation.vulnerabilityName',
    #                                 'componentVersionOriginId'],
    #                         keep="first", inplace=False)

    if len(df.index) > 0:
        df = df[df['ignored'] != True]
        df['vulnerabilityWithRemediation.vulnerabilityPublishedDate'] = \
            pd.DatetimeIndex(df['vulnerabilityWithRemediation.vulnerabilityPublishedDate']).strftime("%Y-%m-%d")
        df['vulnerabilityWithRemediation.vulnerabilityUpdatedDate'] = \
            pd.DatetimeIndex(df['vulnerabilityWithRemediation.vulnerabilityUpdatedDate']).strftime("%Y-%m-%d")
        df['vulnerabilityWithRemediation.remediationUpdatedAt'] = \
            pd.DatetimeIndex(df['vulnerabilityWithRemediation.remediationUpdatedAt']).strftime("%Y-%m-%d")

    print('Found ' + str(len(df.index)) + ' vulnerabilities')
    return df, vulns['items']


col_data_vulns = [
    {"name": ['Component'], "id": "componentName"},
    {"name": ['Version'], "id": "componentVersionName"},
    {"name": ['Vulnerability'], "id": "vulnerabilityWithRemediation.vulnerabilityName"},
    {"name": ['Related Vuln'], "id": "vulnerabilityWithRemediation.relatedVulnerability"},
    {"name": ['Orig'], "id": "componentVersionOriginId"},
    {"name": ['Description'], "id": "vulnerabilityWithRemediation.description"},
    {"name": ['Published Date'], "id": "vulnerabilityWithRemediation.vulnerabilityPublishedDate"},
    {"name": ['Updated Date'], "id": "vulnerabilityWithRemediation.vulnerabilityUpdatedDate"},
    {"name": ['Overall Score'], "id": "vulnerabilityWithRemediation.overallScore"},
    {"name": ['Exploit Score'], "id": "vulnerabilityWithRemediation.exploitabilitySubscore"},
    {"name": ['Impact Score'], "id": "vulnerabilityWithRemediation.impactSubscore"},
    {"name": ['Severity'], "id": "vulnerabilityWithRemediation.severity"},
    {"name": ['Rem Status'], "id": "vulnerabilityWithRemediation.remediationStatus"},
    {"name": ['Rem Date'], "id": "vulnerabilityWithRemediation.remediationUpdatedAt"},
    {"name": ['CWE'], "id": "vulnerabilityWithRemediation.cweId"},
]


def create_vulnstab(vulndata, projname, vername):
    global col_data_vulns

    return [
        dbc.Row(
            dbc.Col(html.H2("Vulnerabilities")),
        ),
        dbc.Row(
            [
                dbc.Col(html.H5("Project: " + projname + " - Version: " + vername), width=7),
                dbc.Col(
                    dcc.Dropdown(
                        id="sel_vuln_action",
                        # DUPLICATE, IGNORED, MITIGATED, NEEDS_REVIEW, NEW, PATCHED, REMEDIATION_COMPLETE,
                        # REMEDIATION_COMPLETE
                        options=[
                            {'label': 'Select Remediation ...', 'value': 'NOTHING'},
                            {'label': 'New', 'value': 'NEW'},
                            {'label': 'Duplicate', 'value': 'DUPLICATE'},
                            {'label': 'Ignored', 'value': 'IGNORED'},
                            {'label': 'Mitigated', 'value': 'MITIGATED'},
                            {'label': 'Needs Review', 'value': 'NEEDS_REVIEW'},
                            {'label': 'Patched', 'value': 'PATCHED'},
                            {'label': 'Remediation Required', 'value': 'REMEDIATION_REQUIRED'},
                            {'label': 'Remediation Complete', 'value': 'REMEDIATION_COMPLETE'},
                        ],
                        multi=False,
                        placeholder='Select Remediation ...'
                    ), width=2,
                    align='center',
                ),
                dbc.Col(dbc.Button("Selected Rows", id="button_vuln_selected",
                                   className="mr-2", size='sm'), width=1),
                dbc.Col(dbc.Button("All Filtered Rows", id="button_vuln_all",
                                   className="mr-2", size='sm'), width=1),
                dbc.Col(dbc.Button("Reload", id="button_vuln_reload",
                                   className="mr-2", size='sm'), width=1),
            ]
        ),
        dbc.Row(
            dbc.Col(
                dash_table.DataTable(
                    id='vulnstable',
                    columns=col_data_vulns,
                    style_cell={
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'maxWidth': 0,
                        'font_size': '12px',
                    },
                    data=vulndata.to_dict('records'),
                    page_size=30, sort_action='native',
                    filter_action='native',
                    row_selectable="multi",
                    cell_selectable=False,
                    style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                    tooltip_data=[
                        {
                            column: {'value': str(value), 'type': 'markdown'}
                            for column, value in row.items()
                        } for row in vulndata.to_dict('records')
                    ],
                    tooltip_duration=None,
                    style_data_conditional=[
                        {
                            'if': {
                                'filter_query': '{ignored} eq "True"',
                                'column_id': 'ignored'
                            },
                            'display': 'none',
                        },
                        {
                            'if': {'column_id': 'componentName'},
                            'width': '15%'
                        },
                        {
                            'if': {'column_id': 'componentVersionName'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.vulnerabilityName'},
                            'width': '8%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.relatedVulnerability'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.description'},
                            'width': '15%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.vulnerabilityPublishedDate'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.vulnerabilityUpdatedDate'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.overallScore'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.exploitabilitySubscore'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.impactSubscore'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.severity'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.remediationStatus'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.remediationUpdatedAt'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.cweId'},
                            'width': '5%'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.severity} = "CRITICAL"',
                                'column_id': 'vulnerabilityWithRemediation.severity'
                            },
                            'backgroundColor': 'maroon',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.severity} = "HIGH"',
                                'column_id': 'vulnerabilityWithRemediation.severity'
                            },
                            'backgroundColor': 'crimson',
                            'color': 'black'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.severity} = "MEDIUM"',
                                'column_id': 'vulnerabilityWithRemediation.severity'
                            },
                            'backgroundColor': 'coral',
                            'color': 'black'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.severity} = "LOW"',
                                'column_id': 'vulnerabilityWithRemediation.severity'
                            },
                            'backgroundColor': 'gold',
                            'color': 'black'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.remediationStatus} = "IGNORED"',
                                'column_id': 'vulnerabilityWithRemediation.remediationStatus'
                            },
                            'backgroundColor': 'grey',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.remediationStatus} = "PATCHED"',
                                'column_id': 'vulnerabilityWithRemediation.remediationStatus'
                            },
                            'backgroundColor': 'grey',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.remediationStatus} = "MITIGATED"',
                                'column_id': 'vulnerabilityWithRemediation.remediationStatus'
                            },
                            'backgroundColor': 'grey',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query': '{vulnerabilityWithRemediation.remediationStatus} = "DUPLICATE"',
                                'column_id': 'vulnerabilityWithRemediation.remediationStatus'
                            },
                            'backgroundColor': 'grey',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query':
                                    '{vulnerabilityWithRemediation.remediationStatus} = "REMEDIATION_COMPLETE"',
                                'column_id': 'vulnerabilityWithRemediation.remediationStatus'
                            },
                            'backgroundColor': 'grey',
                            'color': 'white'
                        },
                    ],
                    sort_by=[{'column_id': 'vulnerabilityWithRemediation.overallScore', 'direction': 'desc'}],
                    # merge_duplicate_headers=True
                ),
                width=12
            ),
        ),
    ]


def make_vuln_toast(message):
    """
    Helper function for making a toast. dict id for use in pattern matching
    callbacks.
    """
    return dbc.Toast(
        message,
        id={"type": "toast", "id": "toast_vuln"},
        key='toast_vuln',
        header="Vulnerability Processing",
        is_open=True,
        dismissable=True,
        icon="info",
    )


def vulnactions(bd, vulnjson, action, origdata, vdata, rows):

    def do_vuln_action(bbd, comp):
        try:
            # vuln_name = comp['vulnerabilityWithRemediation']['vulnerabilityName']
            # result = vhub.execute_put(comp['_meta']['href'], data=comp)
            # if result.status_code != 202:
            #     return False
            r = bbd.session.put(comp['_meta']['href'], json=comp)
            if r.status_code != 202:
                return False

        except Exception as e:
            print("ERROR: Unable to update vulnerabilities via API\n" + str(e))
            return False

        return True

    vulnaction_dict = {
        'NEW': {'confirmation': 'Change to New', 'comment': 'Updated by bdconsole'},
        'DUPLICATE': {'confirmation': 'changed to Duplicate', 'comment': 'Updated by bdconsole'},
        'IGNORED': {'confirmation': 'changed to Ignored', 'comment': 'Updated by bdconsole'},
        'MITIGATED': {'confirmation': 'changed to Mitigated', 'comment': 'Updated by bdconsole'},
        'NEEDS_REVIEW': {'confirmation': 'changed to Needs Review', 'comment': 'Updated by bdconsole'},
        'PATCHED': {'confirmation': 'changed to Patch', 'comment': 'Updated by bdconsole'},
        'REMEDIATION_REQUIRED': {'confirmation': 'changed to Remediation Required', 'comment': 'Updated by bdconsole'},
        'REMEDIATION_COMPLETE': {'confirmation': 'changed to Remediation Complete', 'comment': 'Updated by bdconsole'},
    }

    count = 0
    confirmation = ''
    error = False
    for row in rows:
        thisvuln = vdata[row]

        if action in vulnaction_dict.keys() and \
                thisvuln['vulnerabilityWithRemediation.remediationStatus'] != action:
            entry = vulnaction_dict[action]
            # Find entry in original table
            foundrow = -1
            for origrow, origcomp in enumerate(origdata):
                if (origcomp['componentVersion'] == thisvuln['componentVersion']) and \
                        (origcomp['vulnerabilityWithRemediation.vulnerabilityName'] ==
                         thisvuln['vulnerabilityWithRemediation.vulnerabilityName']) and \
                        (origcomp['componentVersionOriginId'] == thisvuln['componentVersionOriginId']):
                    foundrow = origrow
                    break

            if foundrow >= 0:
                for vuln in vulnjson:
                    if vuln['vulnerabilityWithRemediation']['vulnerabilityName'] == \
                            thisvuln['vulnerabilityWithRemediation.vulnerabilityName'] and vuln['componentVersion'] == \
                            thisvuln['componentVersion'] and thisvuln['componentVersionOriginId'] == \
                            vuln['componentVersionOriginId']:
                        vuln['remediationStatus'] = action
                        vuln['remediationComment'] = entry['comment']
                        origdata[foundrow]['vulnerabilityWithRemediation.remediationStatus'] = action
                        # origdata[foundrow]['json'] = json.dumps(vulndata)
                        confirmation = entry['confirmation']
                        if do_vuln_action(bd, vuln):
                            print('Remediated vuln: ' + vuln['vulnerabilityWithRemediation']['vulnerabilityName'])
                            count += 1
                            break
                        else:
                            error = True
            else:
                error = True

    if error:
        return origdata, make_vuln_toast('Unable to update vulnerabilities')

    toast = ''
    if count > 0:
        toast = make_vuln_toast("{} Vulnerabilities {}".format(count, confirmation))

    return origdata, toast
