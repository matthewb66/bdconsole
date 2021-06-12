# import json
import os
import io
import pandas as pd
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table


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
                        dbc.Col(html.H5("Project: " + projname + " - Version: " + vername), width=8),
                        dbc.Col(
                            dcc.Dropdown(
                                id="sel_snip_action",
                                options=[
                                    {'label': 'Select Action ...', 'value': 'NOTHING'},
                                    {'label': 'Ignore', 'value': 'IGNORE'},
                                    {'label': 'Unignore', 'value': 'UNIGNORE'},
                                    # {'label': 'Confirm', 'value': 'CONFIRM'},
                                    # {'label': 'Unconfirm', 'value': 'UNCONFIRM'},
                                ],
                                multi=False,
                                placeholder='Select Action ...'
                            ), width=2,
                            align='center',
                        ),
                        dbc.Col(dbc.Button("Selected Rows", id="button_snip_selected",
                                           className="mr-2", size='sm'), width=1),
                        dbc.Col(dbc.Button("All Filtered Rows", id="button_snip_all",
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
                                'maxWidth': 0,
                                'font_size': '12px',
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
                                {
                                    'if': {
                                        'filter_query':
                                            '{status} = "Ignored"',
                                        'column_id': 'status'
                                    },
                                    'backgroundColor': 'grey',
                                    'color': 'white'
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


def get_snippet_entries(bd, path):
    paramstring = "?filter=bomMatchReviewStatus%3Anot_reviewed&filter=bomMatchType%3Asnippet&offset=0&limit=5000"

    # print(path)
    # Using internal API - see https://jira.dc1.lan/browse/HUB-18270: Make snippet API calls for ignoring,
    # confirming snippet matches public
    splits = path.split('/')
    # "{}/internal/projects/{}/versions/{}/source-bom-entries"
    url = "{}/api/internal/projects/{}/versions/{}/source-bom-entries".format('/'.join(splits[:3]), splits[5], splits[7]) \
          + paramstring
    # print(url)
    # response = hub.execute_get(url)
    # if response.ok:
    #     return response.json()
    # else:
    #     return {}
    snipjson = bd.get_json(url)
    return snipjson


def ignore_snippet_bom_entry(bd, url, scanid, nodeid, snippetid, ignore):
    if ignore:
        post_body = '{ "ignored": true }'
    else:
        post_body = '{ "ignored": false }'

    fullurl = "{}/scans/{}/nodes/{}/snippets/{}".format(url, scanid, nodeid, snippetid)
    # 	print(url)

    # response = hub.execute_put(fullurl, post_body)
    # return response.ok
    r = bd.session.put(fullurl, json=post_body)
    if r.status_code == 200:
        return True
    else:
        return False


def get_snippets_data(bd, path):
    csv_data = "{},{},{},{},{},{},{},{},{}\n".format("file", "size", "block", "coveragepct", "matchlines",
                                                     "status", "scanid", "nodeid", "snippetid")
    alreadyignored = 0
    count = 0
    print('Getting snippet data ... ')
    snippet_bom_entries = get_snippet_entries(bd, path)
    if snippet_bom_entries != '':
        # print(snippet_bom_entries)
        for snippet_item in snippet_bom_entries['items']:
            scanid = snippet_item['scanId']
            nodeid = snippet_item['compositeId']
            blocknum = 1
            for match in snippet_item['fileSnippetBomComponents']:
                if match['ignored']:
                    alreadyignored += 1

                if match['ignored']:
                    igstatus = "Ignored"
                else:
                    igstatus = "Not ignored"
                snippetid = match['hashId']
                if 'sourceStartLines' in match.keys() and 'sourceEndLines' in match.keys():
                    matchedlines = match['sourceEndLines'][0] - match['sourceStartLines'][0]
                else:
                    matchedlines = 0
                if 'matchFilePath' in match.keys():
                    filename = os.path.join(match['matchFilePath'], snippet_item['name'])
                else:
                    filename = ''
                if 'matchCoverage' in match.keys():
                    coverage = match['matchCoverage']
                else:
                    coverage = ''
                csv_data += "{},{},{},{},{},{},{},{},{}\n".\
                    format(filename.replace(',', ' '), snippet_item['size'], blocknum, coverage,
                           matchedlines, igstatus, scanid, nodeid, snippetid)
                blocknum += 1
                count += 1

    print('Found ' + str(count) + ' snippets')
    return csv_data, count


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
        dismissable=False,
        icon="info",
        duration=8000,
    )


def snipactions(bd, action, origdata, vdata, rows, projverurl):
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

            if ignore_snippet_bom_entry(bd, projverurl, vdata[row]['scanid'], vdata[row]['nodeid'],
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

            if ignore_snippet_bom_entry(bd, projverurl, vdata[row]['scanid'], vdata[row]['nodeid'],
                                        vdata[row]['snippetid'], False):
                print("{} UNignored".format(vdata[row]['file']))
                count += 1
            else:
                print("Error")

    toast = ''
    if count > 0:
        toast = make_snip_toast("{} Snippets {}".format(count, confirmation))

    return origdata, toast
