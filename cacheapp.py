import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
# import datetime
from flask_caching import Cache
# import os
import pandas as pd
# import time
import uuid

from blackduck.HubRestApi import HubInstance

hub = HubInstance()
serverurl = "https://poc39.blackduck.synopsys.com"
spdx_proc = None

external_stylesheets = [
    # Dash CSS
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    # Loading screen CSS
    'https://codepen.io/chriddyp/pen/brPBPO.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
cache = Cache(app.server, config={
    # 'CACHE_TYPE': 'redis',
    # Note that filesystem cache doesn't work on systems with ephemeral
    # filesystems like Heroku.
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 60,


    # should be equal to maximum number of users on the app at a single time
    # higher numbers will store more data in the filesystem / redis cache
    'CACHE_THRESHOLD': 10
})


def get_project_data():
    projs = hub.get_projects(5000)
    df = pd.json_normalize(projs, record_path=['items'])

    print('Found ' + str(len(df.index)) + ' projects')
    return df


def get_dataframe(session_id):
    @cache.memoize(timeout=60)
    def query_and_serialize_data(session_id):
        # expensive or user/session-unique data processing step goes here
        df_proj = get_project_data()
        df_proj.createdAt = pd.DatetimeIndex(df_proj.createdAt).strftime("%Y-%m-%d")
        df_proj.updatedAt = pd.DatetimeIndex(df_proj.updatedAt).strftime("%Y-%m-%d")
        print('calling API')

        return df_proj.to_json()

    return pd.read_json(query_and_serialize_data(session_id))


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


def create_projtable(projdf):
    return dash_table.DataTable(
        id='projtable',
        columns=col_data_proj,
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0
        },
        data=projdf.to_dict('records'),
        page_size=30, sort_action='native',
        filter_action='native',
        row_selectable="single",
        cell_selectable=False,
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
        # tooltip_data=[
        #     {
        #         column: {'value': str(value), 'type': 'markdown'}
        #         for column, value in row.items()
        #     } for row in df_proj.to_dict('records')
        # ],
        # tooltip_duration=None,
        style_data_conditional=[
            {
                'if': {'column_id': 'name'},
                'width': '20%'
            },
            {
                'if': {
                    'filter_query': '{customSignatureEnabled} eq "True"',
                    'column_id': 'customSignatureEnabled'
                },
                'backgroundColor': 'black',
                'color': 'white'
            },
            {
                'if': {
                    'filter_query': '{licenseConflictsEnabled} eq "True"',
                    'column_id': 'licenseConflictsEnabled'
                },
                'backgroundColor': 'grey',
                'color': 'white'
            },
        ],
        sort_by=[{'column_id': 'name', 'direction': 'asc'}],
        # merge_duplicate_headers=True
    )


session_id = str(uuid.uuid4())

app.layout = dbc.Container(
    [
        # 		dcc.Store(id='sec_values', storage_type='local'),
        # 		dcc.Store(id='lic_values', storage_type='local'),
        dcc.Store(data=session_id, id='session-id'),
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
                    [
                        dbc.Button("Get Data", id="button_getdata",
                                   className="mr-2", size='sm'),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [html.H2("Projects"), create_projtable(pd.DataFrame())],
                                    width=12
                                ),
                            ],
                        ),
                    ],
                    id='spinner_main',
                ), width=12,
            )
        ),
    ], fluid=True
)


@app.callback(Output('projtable', 'data'),
              Input('button_getdata', 'n_clicks'),
              Input('session-id', 'data'))
def cb_getdata(value, session_id):
    print('cb_getdata')
    ctx = dash.callback_context.triggered[0]
    ctx_caller = ctx['prop_id']
    if ctx_caller != 'button_getdata.n_clicks':
        df = get_dataframe(session_id)
        return df.to_dict('records')
    return ''


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8888, debug=False)
