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

projname = ""
vername = ""
spdx_proc = None


def get_project_data():
    projs = hub.get_projects(5000)
    return pd.json_normalize(projs, record_path=['items'])


def get_versions_data(proj):
    res = hub.execute_get(proj + '/versions')
    if res.status_code != 200:
        return None
    vers = res.json()
    df = pd.json_normalize(vers, record_path=['items'])
    # df['scan_dep'] = False
    # df['scan_sig'] = False
    # df['scan_snip'] = False
    # df['scan_bin'] = False
    #
    # index = 0
    # for ver in vers['items']:
    #     link = next((item for item in ver['_meta']['links'] if item["rel"] == "codelocations"), None)
    #     if link != '':
    #         cl = hub.execute_get(link['href'])
    #         if cl.status_code != 200:
    #             return None
    #         cls = cl.json()
    #         for cl in cls['items']:
    #             if 'scanSize' in cl and cl['scanSize'] > 0:
    #                 if 'name' in cl and cl['name'].endswith(' scan'):
    #                     df.loc[index, 'scan_sig'] = True
    #             if 'name' in cl and cl['name'].endswith(' bom'):
    #                 df.loc[index, 'scan_dep'] = True
    #
    #     index += 1

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


def create_compstab(compdata):
    global col_data_comps
    global projname
    global vername

    return dbc.Row(
        dbc.Col(
            [
                html.H2("Components"),
                html.H4("Project: " + projname + " Version: " + vername),
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
                    # row_selectable="single",
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
                )
            ],
            width=12)
    )


col_data_snippets = [
    {"name": ['File'], "id": "file"},
    {"name": ['Size (bytes)'], "id": "size"},
    {"name": ['Block'], "id": "block"},
    {"name": ['Match %'], "id": "coveragepct"},
    {"name": ['Matched Lines'], "id": "matchlines"},
    {"name": ['Status'], "id": "status"},
]


def create_snippetstab(snippetcsv):
    global col_data_snippets
    global projname
    global vername

    if snippetcsv == '':
        df_snippets = pd.DataFrame(columns=["file", "size", "block", "coveragepct", "matchlines", "status"])
    else:
        snipdata = io.StringIO(snippetcsv)
        df_snippets = pd.read_csv(snipdata, sep=",")

    return dbc.Row(
        dbc.Col(
            [
                html.H2("Unconfirmed Snippets"),
                html.H4("Project: " + projname + " Version: " + vername),
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
                    # row_selectable="single",
                    cell_selectable=False,
                    style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                    tooltip_data=[
                        {
                            column: {'value': str(value), 'type': 'markdown'}
                            for column, value in row.items()
                        } for row in df_snippets.to_dict('records')
                    ],
                    tooltip_duration=None,
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'file'},
                            'width': '70%'
                        },
                        {
                            'if': {'column_id': 'size'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'block'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'coveragepct'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'matchlines'},
                            'width': '5%'
                        },
                        {
                            'if': {'column_id': 'status'},
                            'width': '10%'
                        },
                    ],
                    sort_by=[{'column_id': 'file', 'direction': 'asc'}]
                    # merge_duplicate_headers=True
                )
            ],
            width=12)
    )


def create_vercard(ver, comps):
    global vername
    global projname

    if ver is None or comps is None:
        vername = ''
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
            dbc.CardHeader("Project Version Details"),
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
        dcc.Store(id='proj_color', storage_type='session'),
        dcc.Store(id='proj_size', storage_type='session'),
        dcc.Store(id='sankey_state', storage_type='session'),
        # dcc.Store(id='active_tab', storage_type='session'),
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
                                                    dbc.Col(create_vercard(None, None))
                                                ),
                                            ], width=5
                                        ),
                                    ]
                                ),
                                label="Projects (" + str(len(df_proj)) + ")",
                                tab_id="tab_projects", id="tab_projects"
                            ),
                            dbc.Tab(  # COMPONENTS TAB
                                create_compstab(df_comp),
                                label="Components",
                                tab_id="tab_comps", id="tab_comps",
                                disabled=True,
                            ),
                            dbc.Tab(  # SNIPPETS TAB
                                create_snippetstab(''),
                                label="Snippets",
                                tab_id="tab_snippets", id="tab_snippets",
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


@app.callback(
    Output("vertable", "data"),
    [
        # Input("projtable", "selected_rows"),
        Input('projtable', 'derived_virtual_selected_rows'),
        State('projtable', 'derived_virtual_data'),
        # State('vertable', 'data'),
    ]
)
def cb_projtable(row, vprojdata):
    global projname

    if row is None:
        raise dash.exceptions.PreventUpdate
    if len(row) < 1:
        raise dash.exceptions.PreventUpdate

    projid = vprojdata[row[0]]['_meta.href']
    projname = vprojdata[row[0]]['name']
    verdata = get_versions_data(projid)

    return verdata.to_dict(orient='records')


@app.callback(
    [
        Output("vercard", "children"),
        Output("tab_comps", "children"),
        Output("tab_comps", "disabled"),
        Output("tab_comps", "label"),
        Output("tab_snippets", "disabled"),
        Output("tab_snippets", "children"),
        Output("tab_actions", "disabled"),
        Output("spdx_file", "value")
    ],
    [
        # Input("projtable", "selected_rows"),
        Input('vertable', 'derived_virtual_selected_rows'),
        State('vertable', 'derived_virtual_data'),
        # State('vertable', 'data'),
    ]
)
def cb_vertable(row, verdata):
    global projname
    global vername

    if row is None:
        raise dash.exceptions.PreventUpdate
    if len(row) < 1:
        raise dash.exceptions.PreventUpdate

    projverurl = str(verdata[row[0]]['_meta.href'])
    path = projverurl + "/components?limit=5000"
    # print(url)
    custom_headers = {'Accept': 'application/vnd.blackducksoftware.bill-of-materials-6+json'}
    resp = hub.execute_get(path, custom_headers=custom_headers)
    compdata = resp.json()
    df_comp_new = pd.json_normalize(compdata, record_path=['items'])
    # df_comp_new['polIcon'] = df_comp_new['policyStatus'].apply(lambda x: '🚫️' if x == 'IN_VIOLATION' else '️')
    # df_comp_new['ignoreIcon'] = df_comp_new['ignored'].apply(lambda x: '❗️' if x == 'true' else '️')
    df_comp_new.loc[(df_comp_new.policyStatus == 'IN_VIOLATION'), 'policyStatus'] = '🚫️'
    df_comp_new.loc[(df_comp_new.policyStatus == 'NOT_IN_VIOLATION'), 'policyStatus'] = 'None'
    df_comp_new.loc[(df_comp_new.ignored == True), 'ignored'] = '❗'
    df_comp_new.loc[(df_comp_new.ignored != True), 'ignored'] = 'Not Ignored'

    vername = verdata[row[0]]['versionName']

    snippetdata = snippets.get_snippets_data(hub, projverurl)

    return create_vercard(verdata[row[0]], df_comp_new), \
        create_compstab(df_comp_new), False, "Components (" + str(len(df_comp_new.index)) + ")", \
        False, create_snippetstab(snippetdata), \
        False, \
        "SPDX_" + projname + '-' + vername + ".json"


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
    ]
)
def cb_spdxbutton(spdx_click, n, spdx_file, spdx_rec):
    global projname
    global vername
    global spdx_proc

    if spdx_click is None and n == 0:
        print('NO ACTION')
        raise dash.exceptions.PreventUpdate

    if n <= 0:
        # subprocess.run(["python3", "export_spdx.py", "-o", spdx_file, projname, vername],
        #                capture_output=True)
        cmd = ["python3", "export_spdx.py", "-o", "SPDX/" + spdx_file, projname, vername]
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


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8888, debug=False)
