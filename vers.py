import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
import dash_table
from datetime import datetime

import utils


def get_versions_data(bd, projurl):
    # res = hub.execute_get(proj + '/versions?limit=200')
    # if res.status_code != 200:
    #     print('Get version components - return code ' + res.status_code)
    #     return None
    vers = utils.get_json(bd, projurl + "/versions")
    df = pd.json_normalize(vers, record_path=['items'])

    print('Found ' + str(len(df.index)) + ' versions')
    return df


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
            'maxWidth': 0,
            'font_size': '12px',
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


def create_vercard(ver, comps, vername, projname):
    table_body = []
    projlink = ''
    if ver is not None and comps is not None:
        # verbutton = dbc.Button("Select Version", id="verbutton", className="mr-2", size='sm')
        table_rows = [
            html.Tr([html.Td("Component Count:"), html.Td(len(comps.index))]),
            html.Tr([html.Td("Phase:"), html.Td(ver['phase'])]),
            html.Tr([html.Td("Distribution:"), html.Td(ver['distribution'])]),
            html.Tr([html.Td("License:"), html.Td(ver['license.licenseDisplay'])]),
            html.Tr([html.Td("Owner:"), html.Td(ver['createdBy'])]),
            html.Tr([html.Td("Create Date:"),
                     html.Td(datetime.strptime(ver['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d %H:%M"))]),
            html.Tr([html.Td("Last Update Date:"),
                    html.Td(datetime.strptime(ver['settingUpdatedAt'],
                                              '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d %H:%M"))]),
        ]
        table_body = [html.Tbody(table_rows)]
        projlink = ver['_meta.href'] + '/components'

    table_header = []

    return dbc.Card(
        [
            dbc.CardHeader("Project: " + projname, style={'classname': 'card-title'}),
            dbc.CardBody(
                [
                    html.H6("Project Version: " + vername, style={'display': 'flex', 'classname': 'card-title'}),
                    html.Br(),
                    dbc.Table(table_header + table_body, bordered=True),
                ],
            ),
            dbc.CardFooter(dbc.CardLink('Project Version link', href=projlink, target='_blank')),
            # dbc.Table(table_header + table_body, bordered=True),
            # projusedbytitle, projstable,
            # html.Div(verbutton),
        ], id="vercard",
        # style={"width": "28rem", "height":  "50rem"},
        # style={"width": "23rem"},
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
