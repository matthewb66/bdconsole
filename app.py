import json
import sys
# import os
# from time import time
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import dash_auth
import subprocess
from dash_extensions.snippets import send_file

import snippets
import trend
import comps
import vulns
import vers
import projs
import actions

from blackduck import Client
import logging
import os

# from blackduck.HubRestApi import HubInstance
# hub = HubInstance()

bd = None

spdx_proc = None

# from pprint import pprint

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(module)s:%(lineno)d} %(levelname)s - %(message)s"
)

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

df_proj = pd.DataFrame()

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


app.layout = dbc.Container(
    [
        # 		dcc.Store(id='sec_values', storage_type='local'),
        # 		dcc.Store(id='lic_values', storage_type='local'),
        dcc.Store(id='projname', storage_type='session'),
        dcc.Store(id='vername', storage_type='session'),
        dcc.Store(id='projverurl', storage_type='session'),

        # dcc.Store(id='allvulndata', storage_type='session'),
        # dcc.Store(id='allcompdata', storage_type='session'),
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Documentation", href="https://github.com/matthewb66/bdconsole")),
            ],
            brand="Black Duck Project Console",
            # brand_href=hub.get_apibase(),
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
        html.Div(
            id="toast-container-vuln",
            style={"position": "fixed", "top": 10, "right": 10, "width": 350},
        ),
        dbc.Row(
            dbc.Col(
                dbc.Collapse(
                    [
                        dbc.Form(
                            [
                                dbc.FormGroup(
                                    [
                                        dbc.Label("Server URL", className="mr-2"),
                                        dbc.Input(type="text",
                                                  id="config_server",
                                                  placeholder="Enter server URL"),
                                    ],
                                    className="mr-3",
                                ),
                                dbc.FormGroup(
                                    [
                                        dbc.Label("API Token", className="mr-2"),
                                        dbc.Input(type="text",
                                                  id="config_apikey",
                                                  placeholder="Enter API Token"),
                                    ],
                                    className="mr-3",
                                ),
                                dbc.Button("Connect to Server",
                                           id="buttons_config_go",
                                           color="primary"),
                            ],
                            # inline=True,
                        ),
                    ],
                    id="config_collapse",
                    is_open=True,
                ),
            ),
        ),
        dbc.Row(
            dbc.Col(
                dbc.Spinner(
                    dbc.Tabs(
                        [
                            dbc.Tab(  # PROJECTS TAB
                                projs.create_projtab(df_proj, df_ver),
                                label="Projects",
                                tab_id="tab_projects", id="tab_projects"
                            ),
                            dbc.Tab(  # COMPONENTS TAB
                                comps.create_compstab(df_comp, '', ''),
                                label="Components",
                                tab_id="tab_comps", id="tab_comps",
                                disabled=True,
                            ),
                            dbc.Tab(  # VULNS TAB
                                vulns.create_vulnstab(df_vuln, '', ''),
                                label="Vulnerabilities",
                                tab_id="tab_vulns", id="tab_vulns",
                                disabled=True,
                            ),
                            dbc.Tab(  # SNIPPETS TAB
                                snippets.create_snippetstab('', '', ''),
                                label="Snippets",
                                tab_id="tab_snippets", id="tab_snippets",
                                disabled=True,
                            ),
                            dbc.Tab(  # TREND TAB
                                trend.create_trendtab('', '', '', ''),
                                label="Project Version Trend",
                                tab_id="tab_trend", id="tab_trend",
                                disabled=True,
                            ),
                            dbc.Tab(  # ACTIONS TAB
                                actions.create_actions_tab('', ''),
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
    global df_proj
    global bd

    # if os.path.isfile('.restconfig.json') and bd is not None and (df_proj is None or len(df_proj.index) == 0):
    if bd is not None and (df_proj is None or len(df_proj.index) == 0):
        df_proj = projs.get_project_data(bd)

    if row is None:
        raise dash.exceptions.PreventUpdate
    if len(row) < 1:
        raise dash.exceptions.PreventUpdate

    projid = vprojdata[row[0]]['_meta.href']
    projname = vprojdata[row[0]]['name']
    verdata = vers.get_versions_data(bd, projid)

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
        Output("tab_trend", "children"),
        Output("tab_actions", "disabled"),
        Output("spdxtitle", "children"),
        Output("spdx_file", "value"),
        Output('vername', 'data'),
        Output('projverurl', 'data'),
        # Output('allcompdata', 'data'),
        # Output('allvulndata', 'data'),
        Output("toast-container-ver", "children"),
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
    global bd
    global df_proj

    if row is None or len(row) < 1:
        raise dash.exceptions.PreventUpdate

    return vers.ver_callback(bd, row, verdata, projname)


@app.callback(
    [
        Output('spdx_status', 'children'),
        Output('spdx_interval', 'disabled'),
        Output('spdx_interval', 'n_intervals'),
        Output('spdx_collapse', 'is_open'),
    ],
    [
        Input('buttons_export_spdx', 'n_clicks'),
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
        return 'Processing SPDX', False, n, False
    else:
        print("Polling SPDX process")
        spdx_proc.poll()
        ret = spdx_proc.returncode
        if ret is not None:
            return 'Export Complete', True, 0, True
        else:
            return 'Processing SPDX', False, n, False


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
        State('projverurl', 'data'),
    ]
)
def cb_snipactions(snip_selected_clicks, snip_all_clicks, action,
                   origdata, vdata, selected_rows, projverurl):
    global bd

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

    return snippets.snipactions(bd, action, origdata, vdata, rows, projverurl)


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
        # State('allcompdata', 'data'),
    ]
)
def cb_compactions(comp_selected_clicks, comp_all_clicks, action,
                   origdata, vdata, selected_rows, projverurl):
    global bd

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

    return comps.compactions(bd, action, origdata, vdata, rows, projverurl)


@app.callback(
    [
        Output('vulnstable', 'data'),
        Output("toast-container-vuln", "children"),
    ],
    [
        Input('button_vuln_selected', 'n_clicks'),
        Input('button_vuln_all', 'n_clicks'),
        Input('button_vuln_reload', 'n_clicks'),
        State('sel_vuln_action', 'value'),
        State('vulnstable', 'data'),
        State('vulnstable', 'derived_virtual_data'),
        State('vulnstable', 'derived_virtual_selected_rows'),
        State('projverurl', 'data'),
        # State('allvulndata', 'data'),
    ]
)
def cb_vulnactions(vuln_selected_clicks, vuln_all_clicks, reload, action,
                   origdata, vdata, selected_rows, projverurl):
    global bd

    print("cb_vulnactions")
    ctx = dash.callback_context.triggered[0]
    ctx_caller = ctx['prop_id']
    if ctx_caller == 'button_vuln_selected.n_clicks':
        rows = selected_rows
    elif ctx_caller == 'button_vuln_all.n_clicks':
        rows = range(len(vdata))
    elif ctx_caller == 'button_vuln_reload.n_clicks':
        vulndf = vulns.get_vulns_data(bd, projverurl)
        return vulndf.to_dict('records'), vulns.make_vuln_toast('Reloaded vulnerabilities')
    else:
        raise dash.exceptions.PreventUpdate

    if len(rows) == 0 or action is None:
        raise dash.exceptions.PreventUpdate

    return vulns.vulnactions(bd, action, origdata, vdata, rows)


@app.callback(
    [
        Output('compgraph', 'children'),
        Output('vulngraph', 'children'),
    ],
    [
        Input('button_trend', 'n_clicks'),
        State('projverurl', 'data'),
        # State('projname', 'data'),
        State('vername', 'data'),
    ]
)
def cb_trend(button, purl, vername):
    global bd

    if button is None:
        raise dash.exceptions.PreventUpdate

    print("\n\nProcessing project version '{}'".format(purl))

    compdata, vulndata, scans = trend.proc_journals(bd, purl, vername)
    if compdata is None:
        return '', ''

    compfig = trend.create_fig_compstimeline(compdata, scans)
    vulnfig = trend.create_fig_vulnstimeline(vulndata, scans)

    return dcc.Graph(figure=compfig, id='fig_time_trend'), dcc.Graph(figure=vulnfig, id='fig_time_trend')


@app.callback(
    Output("download_spdx", "data"),
    [
        Input('button_download_spdx', 'n_clicks'),
        State('spdx_file', 'value'),
    ]
)
def cb_downloadspdx(button, spdxfile):

    if button is None:
        raise dash.exceptions.PreventUpdate

    filepath = 'SPDX/' + spdxfile

    return send_file(filepath)


@app.callback(
    [
        Output("config_collapse", 'is_open'),
        Output("projtable", "data"),
        Output("tab_projects", "label"),
    ],
    [
        Input('buttons_config_go', 'n_clicks'),
        State('config_server', 'value'),
        State('config_apikey', 'value'),
    ]
)
def cb_configserver(button, server, apikey):
    global bd

    if button is None:
        raise dash.exceptions.PreventUpdate

    bd = Client(
        token=apikey,
        base_url=server,
        timeout=300,
        # verify=False  # TLS certificate verification
    )

    projdf = projs.get_project_data(bd)
    projlabel = "Projects (" + str(len(projdf.index)) + ")"

    return False, projdf.to_dict('records'), projlabel


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8888, debug=True)
