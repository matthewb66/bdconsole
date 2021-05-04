import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
import dash_table

import vers


def get_project_data(bd):
    # url = bd.list_resource('projects')
    # vers = bd.get_json(url + "/versions?limit=200")
    #
    # projs = bd.get_resource('projects', items=False)
    projs = bd.get_json("/api/projects?offset=0&limit=5000")

    df = pd.json_normalize(projs, record_path=['items'])
    df.createdAt = pd.DatetimeIndex(df.createdAt).strftime("%Y-%m-%d")
    df.updatedAt = pd.DatetimeIndex(df.updatedAt).strftime("%Y-%m-%d")

    print('Found ' + str(len(df.index)) + ' projects')
    return df


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
    global col_data_proj

    for col, dtype in projdf.dtypes.items():
        if dtype == 'bool':
            projdf[col] = projdf[col].astype('str')

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
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in projdf.to_dict('records')
        ],
        tooltip_duration=None,
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


def create_projtab(df_proj, df_ver):
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Row(
                        dbc.Col([html.H2("Projects"), create_projtable(df_proj)],
                                width=12)
                    ),
                ], width=7
            ),
            dbc.Col(
                [
                    dbc.Row(
                        dbc.Col(
                            [
                                html.H2("Project Versions"),
                                vers.create_vertable(df_ver),
                                html.Br()
                            ], width=12
                        )
                    ),
                    dbc.Row(
                        dbc.Col(vers.create_vercard(None, None, '', ''))
                    ),
                ], width=5
            ),
        ]
    )
