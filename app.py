import json
import sys
import os
# from time import time
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import dash_auth
import dash_table
import subprocess
import io

import snippets

from blackduck.HubRestApi import HubInstance

hub = HubInstance()
serverurl = "https://poc39.blackduck.synopsys.com"
spdx_proc = None


def get_project_data():
    projs = hub.get_projects(5000)
    return pd.json_normalize(projs, record_path=['items'])


def get_versions_data(proj):
    res = hub.execute_get(proj + '/versions?limit=200')
    if res.status_code != 200:
        print('Get version components - return code ' + res.status_code)
        return None
    vers = res.json()
    df = pd.json_normalize(vers, record_path=['items'])

    return df


def get_vulns_data(projverurl):
    res = hub.execute_get(projverurl + '/vulnerable-bom-components?limit=5000')
    if res.status_code != 200:
        print('Get vulnerabilities - return code ' + res.status_code)
        return None
    vulns = res.json()
    df = pd.json_normalize(vulns, record_path=['items'])

    return df


app = dash.Dash(external_stylesheets=[dbc.themes.COSMO])

server = app.server

if not os.path.isfile('conf/users.txt'):
    print('No users.txt file - exiting')
    sys.exit(3)

with open('conf/users.txt') as f:
    fdata = f.read()
    VALID_USERNAME_PASSWORD_PAIRS = json.loads(fdata)
    f.close()

# app = dash.Dash(external_stylesheets=[dbc.themes.COSMO])
app.auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

df_proj = get_project_data()
df_proj.createdAt = pd.DatetimeIndex(df_proj.createdAt).strftime("%Y-%m-%d")
df_proj.updatedAt = pd.DatetimeIndex(df_proj.updatedAt).strftime("%Y-%m-%d")

df_comp = pd.DataFrame(columns=[
    "componentName",
    "componentVersionName",
    "ignored",
    "reviewStatus",
    "policyStatus",
    # "polIcon",
    "usages",
    "matchTypes",
])

df_ver = pd.DataFrame(columns=['versionName', 'phase', 'distribution', 'createdAt',
                               'createdBy', 'license.licenseDisplay'])

df_vuln = pd.DataFrame(columns=[
    "componentName",
    "componentVersionName",
    "ignored",
    "reviewStatus",
    "policyStatus",
    # "polIcon",
    "usages",
    "matchTypes",
])

# df_ver = get_versions_data('https://poc39.blackduck.synopsys.com/api/projects/27babd58-2eca-482f-975e-55c14b54f876')

col_data_proj = [
    {"name": ['Project'], "id": "name"},
    {"name": ['Description'], "id": "description"},
    {"name": ['Tier'], "id": "projectTier"},
    {"name": ['Created'], "id": "createdAt"},
    {"name": ['Created By'], "id": "createdBy"},
    {"name": ['Updated'], "id": "updatedAt"},
    {"name": ['Updated By'], "id": "updatedBy"},
    {"name": ['Custom Sig'], "id": "customSignatureEnabled"},
    # {"name": ['Snippets'], "id": "snippetAdjustmentApplied"},
    {"name": ['Lic Conflicts'], "id": "licenseConflictsEnabled"},
]

projtable = dash_table.DataTable(
    id='projtable',
    columns=col_data_proj,
    style_cell={
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': 0
    },
    data=df_proj.to_dict('records'),
    page_size=30, sort_action='native',
    filter_action='native',
    row_selectable="single",
    cell_selectable=False,
    style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
    tooltip_data=[
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in df_proj.to_dict('records')
    ],
    tooltip_duration=None,
    style_data_conditional=[
        {
            'if': {'column_id': 'name'},
            'width': '20%'
        },
    ],
    sort_by=[{'column_id': 'name', 'direction': 'asc'}],
    # merge_duplicate_headers=True
)


col_data_ver = [
    {"name": ['Version'], "id": "versionName"},
    {"name": ['Phase'], "id": "phase"},
    {"name": ['Distribution'], "id": "distribution"},
    {"name": ['Created'], "id": "createdAt"},
    {"name": ['Created By'], "id": "createdBy"},
    {"name": ['License'], "id": "license.licenseDisplay"},
    # {"name": ['Updated By'], "id": "updatedBy"},
    # {"name": ['Custom Sig'], "id": "customSignatureEnabled"},
    # {"name": ['Snippets'], "id": "snippetAdjustmentApplied"},
    # {"name": ['Lic Conflicts'], "id": "licenseConflictsEnabled"},
]


def create_vertable(verdata):
    global col_data_ver

    verdata.createdAt = pd.DatetimeIndex(verdata.createdAt).strftime("%Y-%m-%d")
    return dash_table.DataTable(
        id='vertable',
        columns=col_data_ver,
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0
        },
        data=verdata.to_dict('records'),
        page_size=30, sort_action='native',
        filter_action='native',
        row_selectable="single",
        cell_selectable=False,
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in verdata.to_dict('records')
        ],
        tooltip_duration=None,
        style_data_conditional=[
            {
                'if': {'column_id': 'versionName'},
                'width': '30%'
            },
            {
                'if': {'column_id': 'phase'},
                'width': '10%'
            },
            {
                'if': {'column_id': 'distribution'},
                'width': '10%'
            },
            {
                'if': {'column_id': 'createdAt'},
                'width': '10%'
            },
            {
                'if': {'column_id': 'createdBy'},
                'width': '10%'
            },
            {
                'if': {'column_id': 'license.licenseDisplay'},
                'width': '30%'
            },
        ],
        sort_by=[{'column_id': 'versionName', 'direction': 'asc'}],
        # merge_duplicate_headers=True
    )


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

    return [
        dbc.Row(
            dbc.Col(html.H2("Components")),
        ),
        dbc.Row(
            [
                dbc.Col(html.H5("Project: " + projname + " Version: " + vername), width=7),
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
                    ), width=3,
                    align='center',
                ),
                dbc.Col(dbc.Button("Process Selected", id="button_comp_selected",
                                   className="mr-2", size='sm'), width=1),
                dbc.Col(dbc.Button("Process ALL in Table", id="button_comp_all",
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
                    ],
                    sort_by=[{'column_id': 'componentName', 'direction': 'asc'},
                             {'column_id': 'componentVersionName', 'direction': 'asc'}]
                    # merge_duplicate_headers=True
                ),
                width=12
            ),
        ),
    ]


col_data_vulns = [
    {"name": ['Component'], "id": "componentName"},
    {"name": ['Version'], "id": "componentVersionName"},
    {"name": ['Vulnerability'], "id": "vulnerabilityWithRemediation.vulnerabilityName"},
    {"name": ['Related Vuln'], "id": "vulnerabilityWithRemediation.relatedVulnerability"},
    {"name": ['Description'], "id": "vulnerabilityWithRemediation.description"},
    {"name": ['Published Date'], "id": "vulnerabilityWithRemediation.vulnerabilityPublishedDate"},
    {"name": ['Updated Date'], "id": "vulnerabilityWithRemediation.vvulnerabilityUpdatedDate"},
    {"name": ['Overall Score'], "id": "vulnerabilityWithRemediation.overallScore"},
    {"name": ['Exploit Score'], "id": "vulnerabilityWithRemediation.exploitabilitySubscore"},
    {"name": ['Impact Score'], "id": "vulnerabilityWithRemediation.impactSubscore"},
    {"name": ['Severity'], "id": "vulnerabilityWithRemediation.severity"},
    {"name": ['Remediation Status'], "id": "vulnerabilityWithRemediation.remediationStatus"},
    {"name": ['CWE'], "id": "vulnerabilityWithRemediation.cweId"},
]

# 'componentVersion', 'componentName', 'componentVersionName',
#        'componentVersionOriginName', 'componentVersionOriginId', 'ignored',
#        'license.type', 'license.licenses', 'license.licenseDisplay',
#        'vulnerabilityWithRemediation.vulnerabilityName',
#        'vulnerabilityWithRemediation.description',
#        'vulnerabilityWithRemediation.vulnerabilityPublishedDate',
#        'vulnerabilityWithRemediation.vulnerabilityUpdatedDate',
#        'vulnerabilityWithRemediation.baseScore',
#        'vulnerabilityWithRemediation.overallScore',
#        'vulnerabilityWithRemediation.exploitabilitySubscore',
#        'vulnerabilityWithRemediation.impactSubscore',
#        'vulnerabilityWithRemediation.source',
#        'vulnerabilityWithRemediation.severity',
#        'vulnerabilityWithRemediation.remediationStatus',
#        'vulnerabilityWithRemediation.cweId',
#        'vulnerabilityWithRemediation.remediationCreatedAt',
#        'vulnerabilityWithRemediation.remediationUpdatedAt',
#        'vulnerabilityWithRemediation.remediationCreatedBy',
#        'vulnerabilityWithRemediation.remediationUpdatedBy', '_meta.allow',
#        '_meta.href', '_meta.links',
#        'vulnerabilityWithRemediation.relatedVulnerability'

def create_vulnstab(vulndata, projname, vername):
    global col_data_vulns

    return [
        dbc.Row(
            dbc.Col(html.H2("Vulnerabilities")),
        ),
        dbc.Row(
            [
                dbc.Col(html.H5("Project: " + projname + " Version: " + vername), width=7),
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
                    ), width=3,
                    align='center',
                ),
                dbc.Col(dbc.Button("Process Selected", id="button_vuln_selected",
                                   className="mr-2", size='sm'), width=1),
                dbc.Col(dbc.Button("Process ALL in Table", id="button_vuln_all",
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
                        'maxWidth': 0
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
                            'if': {'column_id': 'componentName'},
                            'width': '15%'
                        },
                        {
                            'if': {'column_id': 'componentVersionName'},
                            'width': '10%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.vulnerabilityName'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.relatedVulnerability'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.description'},
                            'width': '20%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.vulnerabilityPublishedDate'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'vulnerabilityWithRemediation.vvulnerabilityUpdatedDate'},
                            'width': '10%'
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


col_data_snippets = [
    {"name": ['File'], "id": "file"},
    {"name": ['Size (bytes)'], "id": "size"},
    {"name": ['Block'], "id": "block"},
    {"name": ['Match %'], "id": "coveragepct"},
    {"name": ['Matched Lines'], "id": "matchlines"},
    {"name": ['Status'], "id": "status"},
    {"name": ['Scanid'], "id": "scanid"},
    {"name": ['Nodeid'], "id": "nodeid"},
    {"name": ['Snipid'], "id": "snippetid"},
]


def create_snippetstab(snippetcsv, projname, vername):
    global col_data_snippets

    if snippetcsv == '':
        df_snippets = pd.DataFrame(columns=["file", "size", "block", "coveragepct", "matchlines", "status"])
    else:
        snipdata = io.StringIO(snippetcsv)
        df_snippets = pd.read_csv(snipdata, sep=",")

    return dbc.Row(
        dbc.Col(
            [
                dbc.Row(
                        dbc.Col(html.H2("Unconfirmed Snippets"), width=12),
                ),
                dbc.Row(
                    [
                        dbc.Col(html.H4("Project: " + projname + " Version: " + vername), width=7),
                        dbc.Col(
                            dcc.Dropdown(
                                id="sel_snip_action",
                                options=[
                                    {'label': 'Select Action ...', 'value': 'NOTHING'},
                                    {'label': 'Ignore', 'value': 'IGNORE'},
                                    {'label': 'Unignore', 'value': 'UNIGNORE'},
                                    {'label': 'Confirm', 'value': 'CONFIRM'},
                                    {'label': 'Unconfirm', 'value': 'UNCONFIRM'},
                                ],
                                multi=False,
                                placeholder='Select Action ...'
                            ), width=3,
                            align='center',
                        ),
                        dbc.Col(dbc.Button("Process Selected", id="button_snip_selected",
                                           className="mr-2", size='sm'), width=1),
                        dbc.Col(dbc.Button("Process ALL in Table", id="button_snip_all",
                                           className="mr-2", size='sm'), width=1),
                    ]
                ),
                dbc.Row(
                    dbc.Col(
                        dash_table.DataTable(
                            id='sniptable',
                            columns=col_data_snippets,
                            style_cell={
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                                'maxWidth': 0
                            },
                            data=df_snippets.to_dict('records'),
                            page_size=30, sort_action='native',
                            filter_action='native',
                            row_selectable="multi",
                            cell_selectable=False,
                            hidden_columns=["scanid", "nodeid", "snippetid"],
                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                            tooltip_data=[
                                {
                                    column: {'value': str(value), 'type': 'markdown'}
                                    for column, value in row.items()
                                } for row in df_snippets.to_dict('records')
                            ],
                            tooltip_duration=None,
                            css=[{"selector": ".show-hide", "rule": "display: none"}],
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'file'},
                                    'width': '60%'
                                },
                                {
                                    'if': {'column_id': 'size'},
                                    'width': '8%'
                                },
                                {
                                    'if': {'column_id': 'block'},
                                    'width': '8%'
                                },
                                {
                                    'if': {'column_id': 'coveragepct'},
                                    'width': '8%'
                                },
                                {
                                    'if': {'column_id': 'matchlines'},
                                    'width': '8%'
                                },
                                {
                                    'if': {'column_id': 'status'},
                                    'width': '8%'
                                },
                            ],
                            sort_by=[{'column_id': 'file', 'direction': 'asc'}]
                            # merge_duplicate_headers=True
                        ),
                        width=12,
                    ),
                ),
            ],
            width=12
        )
    )


def create_vercard(ver, comps, vername, projname):

    if ver is None or comps is None:
        projlink = ''
        compcount = ''
        # verbutton = ''
    else:
        vername = ver['versionName']
        projlink = ver['_meta.href'] + "/components"
        compcount = len(comps.index)
        # verbutton = dbc.Button("Select Version", id="verbutton", className="mr-2", size='sm')

    return dbc.Card(
        [
            dbc.CardHeader("Project: " + projname),
            dbc.CardBody(
                [
                    html.Div([
                        "Project Version: ",
                        html.A(vername, href=projlink,
                               target="_blank",
                               style={'margin-left': '10px'}),
                    ], style={'display': 'flex',
                              'classname': 'card-title'}),
                    html.Br(),
                    html.Div("Components: " + str(compcount)),
                ],
            ),
            # dbc.Table(table_header + table_body, bordered=True),
            # projusedbytitle, projstable,
            # html.Div(verbutton),
        ], id="vercard",
        # style={"width": "28rem", "height":  "50rem"},
        # style={"width": "23rem"},
    )


app.layout = dbc.Container(
    [
        # 		dcc.Store(id='sec_values', storage_type='local'),
        # 		dcc.Store(id='lic_values', storage_type='local'),
        dcc.Store(id='projname', storage_type='session'),
        dcc.Store(id='vername', storage_type='session'),
        dcc.Store(id='projverurl', storage_type='session'),
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Documentation", href="https://github.com/matthewb66/bdconsole")),
            ],
            brand="Black Duck Project Console",
            brand_href=serverurl,
            color="primary",
            dark=True,
            fluid=True,
        ),
        html.Div(
            id="toast-container-snip",
            style={"position": "fixed", "top": 10, "right": 10, "width": 350},
        ),
        html.Div(
            id="toast-container-comp",
            style={"position": "fixed", "top": 10, "right": 10, "width": 350},
        ),
        html.Div(
            id="toast-container-ver",
            style={"position": "fixed", "top": 10, "right": 10, "width": 350},
        ),
        dbc.Row(
            dbc.Col(
                dbc.Spinner(
                    dbc.Tabs(
                        [
                            dbc.Tab(  # PROJECTS TAB
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Row(
                                                    dbc.Col([html.H2("Projects"), projtable], width=12)
                                                ),
                                            ], width=7
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Row(
                                                    dbc.Col(
                                                        [
                                                            html.H2("Project Versions"),
                                                            create_vertable(df_ver),
                                                            html.Br()
                                                        ], width=12
                                                    )
                                                ),
                                                dbc.Row(
                                                    dbc.Col(create_vercard(None, None, '', ''))
                                                ),
                                            ], width=5
                                        ),
                                    ]
                                ),
                                label="Projects (" + str(len(df_proj)) + ")",
                                tab_id="tab_projects", id="tab_projects"
                            ),
                            dbc.Tab(  # COMPONENTS TAB
                                create_compstab(df_comp, '', ''),
                                label="Components",
                                tab_id="tab_comps", id="tab_comps",
                                disabled=True,
                            ),
                            dbc.Tab(  # VULNS TAB
                                create_vulnstab(df_vuln, '', ''),
                                label="Vulnerabilities",
                                tab_id="tab_vulns", id="tab_vulns",
                                disabled=True,
                            ),
                            dbc.Tab(  # SNIPPETS TAB
                                create_snippetstab('', '', ''),
                                label="Snippets",
                                tab_id="tab_snippets", id="tab_snippets",
                                disabled=True,
                            ),
                            dbc.Tab(  # TREND TAB
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            html.Div(children=[''], id='compgraph'),
                                            html.Div(children=[''], id='vulngraph'),
                                        ], width=12
                                    )
                                ),
                                label="Project Version Trend",
                                tab_id="tab_trend", id="tab_trend",
                                disabled=True,
                            ),
                            dbc.Tab(  # ACTIONS TAB
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            html.H2("Export SPDX JSON file"),
                                            dcc.Interval(
                                                id='spdx_interval',
                                                disabled=True,
                                                interval=1 * 6000,  # in milliseconds
                                                n_intervals=0,
                                                max_intervals=400
                                            ),
                                            dbc.Form(
                                                [
                                                    dbc.FormGroup(
                                                        [
                                                            dbc.Label("Filename", className="mr-2"),
                                                            dbc.Input(type="text",
                                                                      id="spdx_file",
                                                                      placeholder="Enter output SPDX file"),
                                                        ],
                                                        className="mr-3",
                                                    ),
                                                    dbc.FormGroup(
                                                        [
                                                            dbc.Checklist(
                                                                id="spdx_recursive",
                                                                options=[
                                                                    {"label": "Recursive (Projects in Projects)",
                                                                     "value": 1},
                                                                ],
                                                                value=[],
                                                                switch=True,
                                                            )
                                                        ],
                                                        className="mr-3",
                                                    ),
                                                    dbc.Button("Export SPDX",
                                                               id="spdx_export_button",
                                                               color="primary"),
                                                ],
                                                # inline=True,
                                            ),
                                            html.Div('', id='spdx_status'),
                                        ],
                                        width=4,
                                    )
                                ),
                                label="Actions",
                                tab_id="tab_actions", id="tab_actions",
                                disabled=True,
                            ),
                        ],
                        id="tabs",
                        active_tab='tab_projects',
                    ),
                    id='spinner_main',
                ), width=12,
            )
        ),
    ], fluid=True
)


def make_snip_toast(message):
    """
    Helper function for making a toast. dict id for use in pattern matching
    callbacks.
    """
    return dbc.Toast(
        message,
        id={"type": "toast", "id": 'toast_snip'},
        key='toast_snip',
        header="Snippet Processing",
        is_open=True,
        dismissable=True,
        icon="info",
    )


def make_ver_toast(message):
    """
    Helper function for making a toast. dict id for use in pattern matching
    callbacks.
    """
    return dbc.Toast(
        message,
        id={"type": "toast", "id": 'toast_ver'},
        key='toast_ver',
        header="Version Components",
        is_open=True,
        dismissable=True,
        icon="info",
    )


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


@app.callback(
    [
        Output("vertable", "data"),
        Output('vertable', 'selected_rows'),
        Output('projname', 'data'),
    ],
    [
        # Input("projtable", "selected_rows"),
        Input('projtable', 'derived_virtual_selected_rows'),
        State('projtable', 'derived_virtual_data'),
        # State('vertable', 'data'),
    ]
)
def cb_projtable(row, vprojdata):

    if row is None:
        raise dash.exceptions.PreventUpdate
    if len(row) < 1:
        raise dash.exceptions.PreventUpdate

    projid = vprojdata[row[0]]['_meta.href']
    projname = vprojdata[row[0]]['name']
    verdata = get_versions_data(projid)

    return verdata.to_dict(orient='records'), [], projname


@app.callback(
    [
        Output("vercard", "children"),
        Output("tab_comps", "children"),
        Output("tab_comps", "disabled"),
        Output("tab_comps", "label"),
        Output("tab_vulns", "children"),
        Output("tab_vulns", "disabled"),
        Output("tab_vulns", "label"),
        Output("tab_snippets", "children"),
        Output("tab_snippets", "disabled"),
        Output("tab_snippets", "label"),
        Output("tab_trend", "disabled"),
        Output("tab_actions", "disabled"),
        Output("spdx_file", "value"),
        Output('vername', 'data'),
        Output('projverurl', 'data'),
        Output("toast-container-ver", "children")
    ],
    [
        # Input("projtable", "selected_rows"),
        Input('vertable', 'derived_virtual_selected_rows'),
        State('vertable', 'derived_virtual_data'),
        # State('vertable', 'data'),
        State('projname', 'data'),
    ]
)
def cb_vertable(row, verdata, projname):

    if row is None or len(row) < 1:
        raise dash.exceptions.PreventUpdate

    vername = verdata[row[0]]['versionName']
    projverurl = str(verdata[row[0]]['_meta.href'])
    path = projverurl + "/components?limit=5000"
    # print(url)
    custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
    resp = hub.execute_get(path, custom_headers=custom_headers)
    if resp.status_code != 200:
        print('component list response ' + resp.status_code)
        toast = make_ver_toast('Unable to get components - check permissions')
        return '', '', True, "Components", True, '', True, True, '', vername, projverurl, toast

    compdata = resp.json()
    df_comp_new = pd.json_normalize(compdata, record_path=['items'])

    if len(df_comp_new.index) > 0:
        df_comp_new.loc[(df_comp_new.policyStatus == 'IN_VIOLATION'), 'policyStatus'] = '🚫️'
        df_comp_new.loc[(df_comp_new.policyStatus == 'NOT_IN_VIOLATION'), 'policyStatus'] = 'None'
        df_comp_new.loc[(df_comp_new.ignored == True), 'ignored'] = '❗'
        df_comp_new.loc[(df_comp_new.ignored != True), 'ignored'] = 'Not Ignored'

    df_vuln_new = get_vulns_data(projverurl)

    snippetdata, snipcount = snippets.get_snippets_data(hub, projverurl)

    return create_vercard(verdata[row[0]], df_comp_new, vername, projname), \
        create_compstab(df_comp_new, projname, vername), False, "Components (" + str(len(df_comp_new.index)) + ")", \
        create_vulnstab(df_vuln_new, projname, vername), False, "Vulnerabilities (" + str(len(df_vuln_new.index)) + ")", \
        create_snippetstab(snippetdata, projname, vername), False, "Snippets (" + str(snipcount) + ")", \
        False, False, \
        "SPDX_" + projname + '-' + vername + ".json", vername, projverurl, ''


@app.callback(
    [
        Output('spdx_status', 'children'),
        Output('spdx_interval', 'disabled'),
        Output('spdx_interval', 'n_intervals'),
    ],
    [
        Input('spdx_export_button', 'n_clicks'),
        Input('spdx_interval', 'n_intervals'),
        State('spdx_file', 'value'),
        State('spdx_recursive', 'value'),
        State('projname', 'data'),
        State('vername', 'data'),
    ]
)
def cb_spdxbutton(spdx_click, n, spdx_file, spdx_rec, projname, vername):
    global spdx_proc

    if spdx_click is None and n == 0:
        print('NO ACTION')
        raise dash.exceptions.PreventUpdate

    if n <= 0:
        # subprocess.run(["python3", "export_spdx.py", "-o", spdx_file, projname, vername],
        #                capture_output=True)
        cmd = ["python3", "addons/export_spdx.py", "-o", "SPDX/" + spdx_file, projname, vername]
        if len(spdx_rec) > 0 and spdx_rec[0] == 1:
            cmd.append('--recursive')
        spdx_proc = subprocess.Popen(cmd, close_fds=True)
        return 'Processing SPDX', False, n
    else:
        print("Polling SPDX process")
        spdx_proc.poll()
        ret = spdx_proc.returncode
        if ret is not None:
            return 'Export Complete', True, 0
        else:
            return 'Processing SPDX', False, n


@app.callback(
    [
        Output('sniptable', 'data'),
        Output("toast-container-snip", "children"),
    ],
    [
        Input('button_snip_selected', 'n_clicks'),
        Input('button_snip_all', 'n_clicks'),
        State('sel_snip_action', 'value'),
        State('sniptable', 'data'),
        State('sniptable', 'derived_virtual_data'),
        State('sniptable', 'derived_virtual_selected_rows'),
        State('projverurl', 'data')
    ]
)
def cb_snipactions(snip_selected_clicks, snip_all_clicks, action,
                   origdata, vdata, selected_rows, projverurl):
    global hub

    print("cb_snipactions")
    ctx = dash.callback_context.triggered[0]
    ctx_caller = ctx['prop_id']
    if ctx_caller == 'button_snip_selected.n_clicks':
        rows = selected_rows
    elif ctx_caller == 'button_snip_all.n_clicks':
        rows = range(len(vdata))
    else:
        raise dash.exceptions.PreventUpdate

    if len(rows) == 0:
        raise dash.exceptions.PreventUpdate

    confirmation = ''
    count = 0
    for row in rows:

        if action == 'IGNORE' and vdata[row]['status'] == 'Not ignored':
            # Ignore it
            index = 0
            for origrow in origdata:
                if origrow['snippetid'] == vdata[row]['snippetid']:
                    break
                index += 1

            origdata[row]['status'] = 'Ignored'
            vdata[row]['status'] = 'Ignored'
            confirmation = 'Ignored'

            if snippets.ignore_snippet_bom_entry(hub, projverurl, vdata[row]['scanid'], vdata[row]['nodeid'],
                                                 vdata[row]['snippetid'], True):
                print("{} Ignored".format(vdata[row]['file']))
                count += 1
            else:
                print("Error")

        elif action == 'UNIGNORE' and vdata[row]['status'] == 'Ignored':
            # Unignore it
            index = 0
            for origrow in origdata:
                if origrow['snippetid'] == vdata[row]['snippetid']:
                    break
                index += 1

            origdata[row]['status'] = 'Not ignored'
            vdata[row]['status'] = 'Not Ignored'
            confirmation = 'Unignored'

            if snippets.ignore_snippet_bom_entry(hub, projverurl, vdata[row]['scanid'], vdata[row]['nodeid'],
                                                 vdata[row]['snippetid'], False):
                print("{} UNignored".format(vdata[row]['file']))
                count += 1
            else:
                print("Error")

    toast = ''
    if count > 0:
        toast = make_snip_toast("{} Snippets {}".format(count, confirmation))

    return vdata, toast


@app.callback(
    [
        Output('compstable', 'data'),
        Output("toast-container-comp", "children"),
    ],
    [
        Input('button_comp_selected', 'n_clicks'),
        Input('button_comp_all', 'n_clicks'),
        State('sel_comp_action', 'value'),
        State('compstable', 'data'),
        State('compstable', 'derived_virtual_data'),
        State('compstable', 'derived_virtual_selected_rows'),
        State('projverurl', 'data'),
    ]
)
def cb_compactions(comp_selected_clicks, comp_all_clicks, action,
                   origdata, vdata, selected_rows, projverurl):
    global hub

    print("cb_compactions")
    ctx = dash.callback_context.triggered[0]
    ctx_caller = ctx['prop_id']
    if ctx_caller == 'button_comp_selected.n_clicks':
        rows = selected_rows
    elif ctx_caller == 'button_comp_all.n_clicks':
        rows = range(len(vdata))
    else:
        raise dash.exceptions.PreventUpdate

    if len(rows) == 0 or action is None:
        raise dash.exceptions.PreventUpdate

    custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
    resp = hub.execute_get(projverurl + '/components?limit=5000', custom_headers=custom_headers)
    if not resp.ok:
        raise dash.exceptions.PreventUpdate
    allcomps = resp.json()['items']

    def comp_action(url, cdata):
        cdata['ignored'] = True
        putresp = hub.execute_put(url, cdata, custom_headers=custom_headers)
        if not putresp.ok:
            print('Error - cannot update component ' + url)
            return False
        else:
            print('Processed component ' + cdata['componentName'])
            return True

    count = 0
    confirmation = ''
    for row in rows:
        thiscomp = vdata[row]
        compurl = thiscomp['componentVersion']
        #
        # Find component in allcomps list
        compdata = None
        for comp in allcomps:
            if compurl == comp['componentVersion']:
                compdata = comp
                break

        if compdata is not None:
            if action == 'IGNORE' and not compdata['ignored']:
                vdata[row]['ignored'] = 'Ignored'
                confirmation = 'Ignored'
                compdata['ignored'] = True
            elif action == 'UNIGNORE' and compdata['ignored']:
                vdata[row]['ignored'] = 'Not Ignored'
                confirmation = 'Unignored'
                compdata['ignored'] = False
            elif action == 'REVIEW' and compdata['reviewStatus'] == 'NOT_REVIEWED':
                vdata[row]['reviewStatus'] = 'REVIEWED'
                confirmation = 'Set Reviewed'
                compdata['reviewStatus'] = 'REVIEWED'
            elif action == 'UNREVIEW' and compdata['reviewStatus'] == 'REVIEWED':
                vdata[row]['reviewStatus'] = 'NOT_REVIEWED'
                confirmation = 'Set Unreviewed'
                compdata['reviewStatus'] = 'NOT_REVIEWED'
            elif action == 'USAGE_SOURCE':
                vdata[row]['usages'] = 'SOURCE_CODE'
                confirmation = 'Usage changed'
                compdata['usages'] = ['SOURCE_CODE']
            elif action == 'USAGE_STATIC':
                vdata[row]['usages'] = 'STATICALLY_LINKED'
                confirmation = 'Usage changed'
                compdata['usages'] = 'STATICALLY_LINKED'
            elif action == 'USAGE_DYNAMIC':
                vdata[row]['usages'] = 'DYNAMICALLY_LINKED'
                confirmation = 'Usage changed'
                compdata['usages'] = 'DYNAMICALLY_LINKED'
            elif action == 'USAGE_SEPARATE':
                vdata[row]['usages'] = 'SEPARATE_WORK'
                confirmation = 'Usage changed'
                compdata['usages'] = 'SEPARATE_WORK'
            elif action == 'USAGE_AGGREGATED':
                vdata[row]['usages'] = 'MERELY_AGGREGATED'
                confirmation = 'Usage changed'
                compdata['usages'] = 'MERELY_AGGREGATED'
            elif action == 'USAGE_STANDARD':
                vdata[row]['usages'] = 'IMPLEMENTATION_OF_STANDARD'
                confirmation = 'Usage changed'
                compdata['usages'] = 'IMPLEMENTATION_OF_STANDARD'
            elif action == 'USAGE_PREREQUISITE':
                vdata[row]['usages'] = 'PREREQUISITE'
                confirmation = 'Usage changed'
                compdata['usages'] = 'PREREQUISITE'
            elif action == 'USAGE_EXCLUDED':
                vdata[row]['usages'] = 'DEV_TOOL_EXCLUDED'
                confirmation = 'Usage changed'
                compdata['usages'] = 'DEV_TOOL_EXCLUDED'

            thiscompurl = projverurl + '/' + '/'.join(compurl.split('/')[4:])
            if comp_action(thiscompurl, compdata):
                count += 1

    toast = ''
    if count > 0:
        toast = make_comp_toast("{} Components {}".format(count, confirmation))

    return vdata, toast


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8888, debug=False)
