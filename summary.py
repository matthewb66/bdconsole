import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
import dash_table
import trend
import pandas as pd

import utils

colors = px.colors.qualitative.Plotly
seccolors = px.colors.qualitative.Light24


def create_summary_compfig(compdata):
    fig = go.Figure()

    if len(compdata.index) == 0:
        return fig
    count_inviolation = len(compdata[(compdata['policyStatus'] == 'IN_VIOLATION') &
                            (compdata['ignored'] == False)].index)
    count_notinviolation = len(compdata[(compdata['policyStatus'] == 'NOT_IN_VIOLATION') &
                               (compdata['ignored'] == False)].index)

    count_reviewed = len(compdata[(compdata['reviewStatus'] == 'REVIEWED') &
                                  (compdata['ignored'] == False)].index)
    count_notreviewed = len(compdata[(compdata['reviewStatus'] == 'NOT_REVIEWED') &
                                     (compdata['ignored'] == False)].index)

    count_ignored = len(compdata[compdata['ignored']].index)
    count_notignored = len(compdata[compdata['ignored'] == False].index)

    annotations = []

    def calc_security(row):
        secs = [0,0,0,0,0]
        secvals = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'OK']

        for y in row['securityRiskProfile.counts']:
            if y['countType'] == 'CRITICAL' and y['count'] > 0:
                secs[0] += 1
            if y['countType'] == 'HIGH' and y['count'] > 0:
                secs[1] += 1
            if y['countType'] == 'MEDIUM' and y['count'] > 0:
                secs[2] += 1
            if y['countType'] == 'LOW' and y['count'] > 0:
                secs[3] += 1
            if y['countType'] == 'OK' and y['count'] > 0:
                secs[4] += 1

        ind = 0
        for val in secs:
            if val > 0:
                return secvals[ind]
            ind += 1

        return 'NONE'

    tempdf = compdata.apply(calc_security, axis=1, result_type='expand')

    compdata.insert(5, 'secrisk', tempdf)

    comp_sec = {}
    comp_sec['CRIT'] = len(compdata[(compdata['secrisk'] == 'CRITICAL') & (compdata['ignored'] == False)].index)
    comp_sec['HIGH'] = len(compdata[(compdata['secrisk'] == 'HIGH') & (compdata['ignored'] == False)].index)
    comp_sec['MED'] = len(compdata[(compdata['secrisk'] == 'MEDIUM') & (compdata['ignored'] == False)].index)
    comp_sec['LOW'] = len(compdata[(compdata['secrisk'] == 'LOW') & (compdata['ignored'] == False)].index)
    comp_sec['OK'] = len(compdata[(compdata['secrisk'] == 'OK') & (compdata['ignored'] == False)].index)

    indent = 0
    colseq = [seccolors[1], seccolors[6], seccolors[7], seccolors[23], seccolors[0]]
    seq = 0
    for x in ['OK', 'LOW', 'MED', 'HIGH', 'CRIT']:
        fig.add_trace(
            go.Bar(
                y=['Comps w. Vulns'],
                x=[comp_sec[x]],
                name=x,
                orientation='h',
                marker=dict(
                    color=colseq[seq],
                )
            )
        )
        if x == 'OK':
            txt = 'OK'
        else:
            txt = x[0]
        if comp_sec[x] > 0:
            annotations.append(
                dict(xref='x', yref='y',
                     x=indent + comp_sec[x] / 2,
                     y='Comps w. Vulns',
                     text=txt,
                     font=dict(family='Arial', size=12,
                               color='rgb(0, 0, 0)'),
                     showarrow=False)
            )
        seq += 1
        indent += comp_sec[x]

    fig.add_trace(
        go.Bar(
            y=['Policy Status'],
            x=[count_notinviolation],
            name='Not in Violation',
            orientation='h',
            marker=dict(
                color=colors[2],
            )
        )
    )
    if count_notinviolation > 0:
        annotations.append(
            dict(xref='x', yref='y',
                 x=count_notinviolation/2,
                 y='Policy Status',
                 text='No Violation',
                 font=dict(family='Arial', size=14,
                           color='rgb(255, 255, 255)'),
                 showarrow=False))
    fig.add_trace(
        go.Bar(
            y=['Policy Status'],
            x=[count_inviolation],
            name='In Violation',
            orientation='h',
            marker=dict(
                color=colors[1],
            )
        )
    )
    if count_notinviolation > 0:
        annotations.append(
            dict(xref='x', yref='y',
                 x=count_notinviolation + count_inviolation/2,
                 y='Policy Status',
                 text='In Violation',
                 font=dict(family='Arial', size=14,
                           color='rgb(255, 255, 255)'),
                 showarrow=False))
    fig.add_trace(
        go.Bar(
            y=['Review Status'],
            x=[count_reviewed],
            name='Reviewed',
            orientation='h',
            marker=dict(
                color=colors[5],
            )
        )
    )
    if count_reviewed > 0:
        annotations.append(
            dict(xref='x', yref='y',
                 x=count_reviewed/2,
                 y='Review Status',
                 text='Reviewed',
                 font=dict(family='Arial', size=14,
                           color='rgb(255, 255, 255)'),
                 showarrow=False))
    fig.add_trace(
        go.Bar(
            y=['Review Status'],
            x=[count_notreviewed],
            name='Not Reviewed',
            orientation='h',
            marker=dict(
                color=colors[0],
            )
        )
    )
    if count_notreviewed > 0:
        annotations.append(
            dict(xref='x', yref='y',
                 x=count_reviewed + count_notreviewed/2,
                 y='Review Status',
                 text='Not Reviewed',
                 font=dict(family='Arial', size=14,
                           color='rgb(255, 255, 255)'),
                 showarrow=False))
    fig.add_trace(
        go.Bar(
            y=['Ignore Status'],
            x=[count_notignored],
            name='Not Ignored',
            orientation='h',
            marker=dict(
                color=colors[5],
            )
        )
    )
    if count_notignored > 0:
        annotations.append(
            dict(xref='x', yref='y',
                 x=count_notignored/2,
                 y='Ignore Status',
                 text='Not Ignored',
                 font=dict(family='Arial', size=14,
                           color='rgb(255, 255, 255)'),
                 showarrow=False))
    fig.add_trace(
        go.Bar(
            y=['Ignore Status'],
            x=[count_ignored],
            name='Ignored',
            orientation='h',
            marker=dict(
                color=colors[0],
            )
        )
    )
    if count_ignored > 0:
        annotations.append(
            dict(xref='x', yref='y',
                 x=count_notignored + count_ignored/2,
                 y='Ignore Status',
                 text='Ignored',
                 font=dict(family='Arial', size=14,
                           color='rgb(255, 255, 255)'),
                 showarrow=False))

    fig.update_layout(barmode='stack', showlegend=False, height=300, annotations=annotations)
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    return fig


def create_summary_vulnfig(vulndata):
    fig = go.Figure()
    if len(vulndata.index) == 0:
        return fig

    vulndf = vulndata.drop_duplicates(subset=["vulnerabilityWithRemediation.vulnerabilityName"],
                                      keep="first", inplace=False)

    if (vulndf is None or len(vulndf.index) == 0):
            return fig
    vulndf = vulndf[vulndf[
                'vulnerabilityWithRemediation.remediationStatus'].isin(['NEW', 'NEEDS_REVIEW', 'REMEDIATION_REQUIRED'])
             ].sort_values(by=['vulnerabilityWithRemediation.overallScore'], ascending=False)

    df = vulndf.reset_index()

    vulns_secrisk = df.groupby(by="vulnerabilityWithRemediation.severity").componentVersion.count()
    # annotations = []

    # vulnvals = [vulns_secrisk['CRITICAL'], vulns_secrisk['HIGH'], vulns_secrisk['MEDIUM'], vulns_secrisk['LOW']]
    vulnvals = []
    for val in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if val in vulns_secrisk:
            vulnvals.append(vulns_secrisk[val])
        else:
            vulnvals.append(0)

    # indent = 0
    # colseq = [seccolors[1], seccolors[6], seccolors[7], seccolors[23], seccolors[0]]
    # seq = 0
    # for x in ['OK', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
    #     if x in vulns_secrisk:
    #         val = vulns_secrisk[x]
    #         if vulns_secrisk[x] > 0:
    #             annotations.append(
    #                 dict(xref='x', yref='y',
    #                     x=indent + vulns_secrisk[x] / 2,
    #                     y='Unremediated',
    #                     text=x[0],
    #                     font=dict(family='Arial', size=12, color='rgb(0, 0, 0)'),
    #                     showarrow=False)
    #             )
    #             indent += vulns_secrisk[x]
    #     else:
    #         val = 0
    #
    #     fig.add_trace(
    #         go.Bar(
    #             y=['Unremediated'],
    #             x=[val],
    #             name=x,
    #             orientation='h',
    #             marker=dict(
    #                 color=colseq[seq],
    #             )
    #         )
    #     )
    #     seq += 1
    #
    # fig.update_layout(barmode='stack', showlegend=False, height=100, annotations=annotations)
    # fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    sec_labels = ['Crit', 'High', 'Med', 'Low']
    sec_names = ['Critical', 'High', 'Medium', 'Low']
    thisfig = px.pie(values=vulnvals, labels=sec_labels, names=sec_names,
                     # title='Vulnerability Counts',
                     hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu, height=400)
    thisfig.update_traces(textinfo='value')
    thisfig.update_traces(sort=False)
    return thisfig


def create_vulntable(vulndata, id):
    if len(vulndata.index) == 0:
        return 'None'
    col_data_vulns = [
        {"name": ['Vulnerability'], "id": "vulnerabilityWithRemediation.vulnerabilityName"},
        {"name": ['Component'], "id": "componentName"},
        {"name": ['Version'], "id": "componentVersionName"},
        # {"name": ['Related Vuln'], "id": "vulnerabilityWithRemediation.relatedVulnerability"},
        # {"name": ['Orig'], "id": "componentVersionOriginId"},
        {"name": ['Description'], "id": "vulnerabilityWithRemediation.description"},
        {"name": ['Published Date'], "id": "vulnerabilityWithRemediation.vulnerabilityPublishedDate"},
        # {"name": ['Updated Date'], "id": "vulnerabilityWithRemediation.vulnerabilityUpdatedDate"},
        {"name": ['Overall Score'], "id": "vulnerabilityWithRemediation.overallScore"},
        # {"name": ['Exploit Score'], "id": "vulnerabilityWithRemediation.exploitabilitySubscore"},
        # {"name": ['Impact Score'], "id": "vulnerabilityWithRemediation.impactSubscore"},
        {"name": ['Severity'], "id": "vulnerabilityWithRemediation.severity"},
        {"name": ['Rem Status'], "id": "vulnerabilityWithRemediation.remediationStatus"},
        # {"name": ['Rem Date'], "id": "vulnerabilityWithRemediation.remediationUpdatedAt"},
        # {"name": ['CWE'], "id": "vulnerabilityWithRemediation.cweId"},
    ]

    return dash_table.DataTable(
        id=id,
        columns=col_data_vulns,
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0,
            'font_size': '12px',
        },
        data=vulndata.to_dict('records'),
        page_size=10, sort_action='native',
        # filter_action='native',
        # row_selectable="multi",
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
            # {
            #     'if': {'column_id': 'vulnerabilityWithRemediation.relatedVulnerability'},
            #     'width': '5%'
            # },
            {
                'if': {'column_id': 'vulnerabilityWithRemediation.description'},
                'width': '15%'
            },
            {
                'if': {'column_id': 'vulnerabilityWithRemediation.vulnerabilityPublishedDate'},
                'width': '5%'
            },
            # {
            #     'if': {'column_id': 'vulnerabilityWithRemediation.vulnerabilityUpdatedDate'},
            #     'width': '5%'
            # },
            {
                'if': {'column_id': 'vulnerabilityWithRemediation.overallScore'},
                'width': '5%'
            },
            # {
            #     'if': {'column_id': 'vulnerabilityWithRemediation.exploitabilitySubscore'},
            #     'width': '5%'
            # },
            # {
            #     'if': {'column_id': 'vulnerabilityWithRemediation.impactSubscore'},
            #     'width': '5%'
            # },
            {
                'if': {'column_id': 'vulnerabilityWithRemediation.severity'},
                'width': '5%'
            },
            {
                'if': {'column_id': 'vulnerabilityWithRemediation.remediationStatus'},
                'width': '5%'
            },
            # {
            #     'if': {'column_id': 'vulnerabilityWithRemediation.remediationUpdatedAt'},
            #     'width': '5%'
            # },
            # {
            #     'if': {'column_id': 'vulnerabilityWithRemediation.cweId'},
            #     'width': '5%'
            # },
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
    )


def create_summary_vulntoptable(vulndata, id):
    if len(vulndata.index) == 0:
        return 'None'
    vdata = vulndata.drop_duplicates(subset=["vulnerabilityWithRemediation.vulnerabilityName"],
                                     keep="first", inplace=False)
    vdata = vdata[vdata[
                'vulnerabilityWithRemediation.remediationStatus'].isin(['NEW', 'NEEDS_REVIEW', 'REMEDIATION_REQUIRED'])
             ].sort_values(by=['vulnerabilityWithRemediation.overallScore'], ascending=False)[:10]
    df = vdata.reset_index()

    return create_vulntable(df, id)


def create_summary_vulnsrecenttable(bd, projverurl, vulndata, vername, days):
    if projverurl != '' and vulndata is not None and len(vulndata.index) > 0:
        # comptimelist, vulntimelist, scans, vulns, vuln_origs = trend.proc_journals(bd, projverurl, vername, days)
        # vdata = vulndata
        # if len(vulns) > 0:
        vdata = vulndata[vulndata[
            'vulnerabilityWithRemediation.remediationStatus'].isin(['NEW', 'NEEDS_REVIEW', 'REMEDIATION_REQUIRED'])
                ].sort_values(by=['vulnerabilityWithRemediation.overallScore'], ascending=False)
        # matchvulns = vdata[vdata['vulnerabilityWithRemediation.vulnerabilityName'].isin(vulns)]
        # for vuln, orig in zip(vulns, vuln_origs):
        #     matchvulns = matchvulns[(matchvulns['vulnerabilityWithRemediation.vulnerabilityName'] != vuln) &
        #                             (matchvulns['componentVersionOriginId'] != orig)]
        #
        # # matchvulns has list of vulns to remove from the vulns list
        vdata = vdata.drop_duplicates(subset=["vulnerabilityWithRemediation.vulnerabilityName"],
                                      keep="first", inplace=False)
        df = vdata.reset_index()

        return create_vulntable(vdata, 'summary_vulnsrecenttable')
    return 'None'


def create_summary_tab(bd, compdata, vulndata, projname, vername, purl):
    return [
        dbc.Row(
            dbc.Col(html.H2("Project Version Summary (" + projname + "/" + vername + ")")),
        ),
        # dbc.Row(
        #     dbc.Col(html.H4("Project: " + projname + "  - Version: " + vername),
        #             id='summary_projver'),
        # ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4("Components"),
                        # html.Div(
                        #     html.H5("Components"),
                        #     style={'width': '49%', 'display': 'inline-block'}
                        # ),
                        # html.Div(
                        #     html.H6("hello"),
                        #     style={'width': '49%', 'display': 'inline-block'}
                        # ),
                        dcc.Graph(figure=create_summary_compfig(compdata),
                                  id='summarytab_compgraph'),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.H4("Unremediated Unique Vulnerabilities"),
                        dcc.Graph(figure=create_summary_vulnfig(vulndata),
                                  id='summarytab_vulngraph'),
                    ],
                    width=6,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4("Top 10 Unique Vulnerabilities"),
                        create_summary_vulntoptable(vulndata, 'summary_vulnstable'),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.H4("New Unique Vulnerabilities (7 days)"),
                        create_summary_vulnsrecenttable(bd, purl, vulndata, vername, 14),
                    ],
                    width=6,
                ),
            ],
        )
    ]


