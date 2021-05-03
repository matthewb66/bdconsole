import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash_extensions import Download


def create_actions_tab(projname, vername):
    return dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Project: " + projname + ' - Version: ' + vername,
                                   style={'classname': 'card-title'},
                                   id='spdxtitle'),
                    dbc.CardBody(
                        [
                            html.H4("Export SPDX JSON file"),
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
                                               id="buttons_export_spdx",
                                               color="primary"),
                                ],
                                # inline=True,
                            ),
                            html.Div('', id='spdx_status'),
                            dbc.Collapse(
                                [
                                    dbc.Button("Download SPDX",
                                               id="button_download_spdx",
                                               color="primary"),
                                    Download(id="download_spdx"),
                                ],
                                id="spdx_collapse",
                                is_open=False,
                            ),
                        ],
                    ),
                    # dbc.CardFooter(dbc.CardLink('Project Version link', href=projlink)),
                ], id="spdxcard",
            ),
            width=4,
        )
    )
