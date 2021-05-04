import json
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_table


def get_comps_data(bd, projverurl):
    print('Getting components ...')
    # path = projverurl + "/components?limit=5000"
    #
    # custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
    # resp = hub.execute_get(path, custom_headers=custom_headers)
    # if resp.status_code != 200:
    #     print('component list response ' + str(resp.status_code))
    #     return None
    #
    # comps = resp.json()
    comps = bd.get_json(projverurl + "/components?limit=5000")
    df = pd.json_normalize(comps, record_path=['items'])
    for index, comp in enumerate(comps['items']):
        df.loc[index, 'json'] = json.dumps(comp)

    print('Found ' + str(len(df.index)) + ' Components')
    return df


col_data_comps = [
    {"name": ['Component'], "id": "componentName"},
    {"name": ['Version'], "id": "componentVersionName"},
    {"name": ['Ignored'], "id": "ignored"},
    # {"name": ['Ignored'], "id": "ignoreIcon"},
    {"name": ['Reviewed'], "id": "reviewStatus"},
    {"name": ['Policy Violation'], "id": "policyStatus"},
    # {"name": ['Policy Status'], "id": "polIcon"},
    {"name": ['Usage'], "id": "usages"},
    {"name": ['Match Types'], "id": "matchTypes"},
]


def create_compstab(compdata, projname, vername):
    global col_data_comps

    for col, dtype in compdata.dtypes.items():
        if dtype == 'bool':
            compdata[col] = compdata[col].astype('str')

    return [
        dbc.Row(
            dbc.Col(html.H2("Components")),
        ),
        dbc.Row(
            [
                dbc.Col(html.H5("Project: " + projname + " - Version: " + vername), width=8),
                dbc.Col(
                    dcc.Dropdown(
                        id="sel_comp_action",
                        options=[
                            {'label': 'Select Action ...', 'value': 'NOTHING'},
                            {'label': 'Ignore', 'value': 'IGNORE'},
                            {'label': 'Unignore', 'value': 'UNIGNORE'},
                            {'label': 'Set Reviewed', 'value': 'REVIEW'},
                            {'label': 'Set Unreviewed', 'value': 'UNREVIEW'},
                            {'label': 'Usage - Source', 'value': 'USAGE_SOURCE'},
                            {'label': 'Usage - Statically Linked', 'value': 'USAGE_STATIC'},
                            {'label': 'Usage - Dynamically Linked', 'value': 'USAGE_DYNAMIC'},
                            {'label': 'Usage - Separate Work', 'value': 'USAGE_SEPARATE'},
                            {'label': 'Usage - Merely Aggregated', 'value': 'USAGE_AGGREGATED'},
                            {'label': 'Usage - Implement Standard', 'value': 'USAGE_STANDARD'},
                            {'label': 'Usage - Prerequisite', 'value': 'USAGE_PREREQUISITE'},
                            {'label': 'Usage - Dev Tool/Excluded', 'value': 'USAGE_EXCLUDED'},
                        ],
                        multi=False,
                        placeholder='Select Action ...'
                    ), width=2,
                    align='center',
                ),
                dbc.Col(dbc.Button("Selected", id="button_comp_selected",
                                   className="mr-2", size='sm'), width=1),
                dbc.Col(dbc.Button("All Filtered", id="button_comp_all",
                                   className="mr-2", size='sm'), width=1),
            ]
        ),
        dbc.Row(
            dbc.Col(
                dash_table.DataTable(
                    id='compstable',
                    columns=col_data_comps,
                    style_cell={
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'maxWidth': 0
                    },
                    data=compdata.to_dict('records'),
                    page_size=30, sort_action='native',
                    filter_action='native',
                    row_selectable="multi",
                    cell_selectable=False,
                    style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                    tooltip_data=[
                        {
                            column: {'value': str(value), 'type': 'markdown'}
                            for column, value in row.items()
                        } for row in compdata.to_dict('records')
                    ],
                    tooltip_duration=None,
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'componentName'},
                            'width': '30%'
                        },
                        {
                            'if': {'column_id': 'componentVersionName'},
                            'width': '20%'
                        },
                        {
                            'if': {'column_id': 'ignored'},
                            'width': '10%'
                        },
                        {
                            'if': {'column_id': 'reviewStatus'},
                            'width': '10%'
                        },
                        {
                            'if': {'column_id': 'policyStatus'},
                            'width': '10%'
                        },
                        {
                            'if': {'column_id': 'usages'},
                            'width': '10%'
                        },
                        {
                            'if': {'column_id': 'matchTypes'},
                            'width': '10%'
                        },
                        {
                            'if': {
                                'filter_query': '{policyStatus} = "IN_VIOLATION"',
                                'column_id': 'policyStatus'
                            },
                            'backgroundColor': 'maroon',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query': '{reviewStatus} = "REVIEWED"',
                                'column_id': 'reviewStatus'
                            },
                            'backgroundColor': 'blue',
                            'color': 'white'
                        },
                        {
                            'if': {
                                'filter_query': '{ignored} eq "True"',
                                'column_id': 'ignored'
                            },
                            'backgroundColor': 'grey',
                            'color': 'white'
                        },
                    ],
                    sort_by=[{'column_id': 'componentName', 'direction': 'asc'},
                             {'column_id': 'componentVersionName', 'direction': 'asc'}]
                    # merge_duplicate_headers=True
                ),
                width=12
            ),
        ),
    ]


def make_comp_toast(message):
    """
    Helper function for making a toast. dict id for use in pattern matching
    callbacks.
    """
    return dbc.Toast(
        message,
        id={"type": "toast", "id": "toast_comp"},
        key='toast_comp',
        header="Component Processing",
        is_open=True,
        dismissable=True,
        icon="info",
    )


def compactions(bd, action, origdata, vdata, rows, projverurl):

    def do_comp_action(url, cdata):
        custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json',
                          'Content-Type': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
        # putresp = hub.execute_put(url, cdata, custom_headers=custom_headers)
        # if not putresp.ok:
        #     print('Error - cannot update component ' + url)
        #     return False
        # else:
        #     print('Processed component ' + cdata['componentName'])
        #     return True
        r = bd.session.put(url, json=cdata)
        if r.status_code == 200:
            print('Processed component ' + cdata['componentName'])
            return True
        else:
            print('Error - cannot update component ' + url)
            return False

    compaction_dict = {
        'IGNORE':
            {'field': 'ignored', 'value': True,
             'confirmation': 'Ignored', 'display': 'True'},
        'UNIGNORE':
            {'field': 'ignored', 'value': False,
             'confirmation': 'Unignored', 'display': 'False'},
        'REVIEW':
            {'field': 'reviewStatus', 'value': 'REVIEWED',
             'confirmation': 'Set Reviewed', 'display': 'REVIEWED'},
        'UNREVIEW':
            {'field': 'reviewStatus', 'value': 'NOT_REVIEWED',
             'confirmation': 'Set Unreviewed', 'display': 'NOT_REVIEWED'},
        'USAGE_SOURCE':
            {'field': 'usages', 'value': ['SOURCE_CODE'],
             'confirmation': 'Usage Changed', 'display': 'SOURCE_CODE'},
        'USAGE_STATIC':
            {'field': 'usages', 'value': ['STATICALLY_LINKED'],
             'confirmation': 'Usage Changed', 'display': 'STATICALLY_LINKED'},
        'USAGE_DYNAMIC':
            {'field': 'usages', 'value': ['DYNAMICALLY_LINKED'],
             'confirmation': 'Usage Changed', 'display': 'DYNAMICALLY_LINKED'},
        'USAGE_SEPARATE':
            {'field': 'usages', 'value': ['SEPARATE_WORK'],
             'confirmation': 'Usage Changed', 'display': 'SEPARATE_WORK'},
        'USAGE_AGGREGATED':
            {'field': 'usages', 'value': ['MERELY_AGGREGATED'],
             'confirmation': 'Usage Changed', 'display': 'MERELY_AGGREGATED'},
        'USAGE_STANDARD':
            {'field': 'usages', 'value': ['IMPLEMENTATION_OF_STANDARD'],
             'confirmation': 'Usage Changed', 'display': 'IMPLEMENTATION_OF_STANDARD'},
        'USAGE_PREREQUISITE':
            {'field': 'usages', 'value': ['PREREQUISITE'],
             'confirmation': 'Usage Changed', 'display': 'PREREQUISITE'},
        'USAGE_EXCLUDED':
            {'field': 'usages', 'value': ['DEV_TOOL_EXCLUDED'],
             'confirmation': 'Usage Changed', 'display': 'DEV_TOOL_EXCLUDED'},
    }
    
    count = 0
    confirmation = ''
    for row in rows:
        thiscomp = vdata[row]
        compurl = thiscomp['componentVersion']
        #
        # Find component in allcomps list
        # compdata = next(comp for comp in allcomps if comp["componentVersion"] == compurl)
        compdata = json.loads(thiscomp['json'])

        if action in compaction_dict.keys():
            entry = compaction_dict[action]
            foundrow = -1
            for origrow, origcomp in enumerate(origdata):
                if origcomp['componentVersion'] == vdata[row]['componentVersion']:
                    foundrow = origrow
                    break
            if foundrow >= 0:
                origdata[foundrow][entry['field']] = entry['display']
                confirmation = entry['confirmation']
                compdata[entry['field']] = entry['value']

                thiscompurl = projverurl + '/' + '/'.join(compurl.split('/')[4:])
                if do_comp_action(thiscompurl, compdata):
                    count += 1

    toast = ''
    if count > 0:
        toast = make_comp_toast("{} Components {}".format(count, confirmation))

    return origdata, toast
