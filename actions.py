import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash_extensions import Download


def create_actions_tab(projname, vername):
    return [
        dbc.Row(
            dbc.Col(html.H2("Actions")),
        ),
        dbc.Row(
            dbc.Col(html.H4("Project: - Version: - "),
                    id='actions_projver'),
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Export SPDX JSON file",
                                           style={'classname': 'card-title'},
                                           id='spdxtitle'),
                            dbc.CardBody(
                                [
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
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Ignore CVEs with BDSA Mismatch",
                                           style={'classname': 'card-title'},
                                           id='fixcvestitle'),
                            dbc.CardBody(
                                [
                                    dcc.Interval(
                                        id='fixcves_interval',
                                        disabled=True,
                                        interval=1 * 6000,  # in milliseconds
                                        n_intervals=0,
                                        max_intervals=400
                                    ),
                                    dbc.Form(
                                        [
                                            dbc.Button("Ignore CVEs with Mismatched BDSA Versions",
                                                       id="buttons_fixcves",
                                                       color="primary"),
                                        ],
                                        # inline=True,
                                    ),
                                    html.Div('', id='fixcves_status'),
                                ],
                            ),
                            # dbc.CardFooter(dbc.CardLink('Project Version link', href=projlink)),
                        ], id="fixcvescard",
                    ),
                    width=4,
                ),
            ],
        )
    ]


def patch_cves(bd, version, vuln_list, vulns):

    # vulnerable_components_url = hub.get_link(version, "vulnerable-components") + "?limit=9999"
    # custom_headers = {'Accept':'application/vnd.blackducksoftware.bill-of-materials-6+json'}
    # response = hub.execute_get(vulnerable_components_url, custom_headers=custom_headers)
    # vulnerable_bom_components = response.json().get('items', [])

    active_statuses = ["NEW", "NEEDS_REVIEW", "REMEDIATION_REQUIRED"]
    status = "IGNORED"
    comment = "Ignored as linked BDSA has component version as fixed"

    print("Processing vulnerabilities ...")
    ignoredcount = 0
    alreadyignoredcount = 0
    try:
        for vuln in vulns:
            vuln_name = vuln['vulnerabilityWithRemediation']['vulnerabilityName']

            if vuln_name in vuln_list:
                if vuln['vulnerabilityWithRemediation']['remediationStatus'] in active_statuses:
                    vuln['remediationStatus'] = status
                    vuln['remediationComment'] = comment
                    # result = hub.execute_put(vuln['_meta']['href'], data=vuln)
                    r = bd.session.put(vuln['_meta']['href'], json=vuln)

                    if r.status_code == 202:
                        ignoredcount += 1
                        print("{}: marked ignored".format(vuln_name))
                    else:
                        print("{}: Unable to change status".format(vuln_name))
                else:
                    print(vuln_name + ": has BDSA which disgrees on version applicability but not active - no action")
                    alreadyignoredcount += 1
            else:
                print(vuln_name + ": No action")

    except Exception as e:
        print("ERROR: Unable to update vulnerabilities via API\n" + str(e))
        return 0
    print("- {} CVEs already inactive".format(alreadyignoredcount))
    print("- {} CVEs newly marked as ignored".format(ignoredcount))
    return ignoredcount


def check_cves(bd, projverurl, comps, vulns):
    cve_list = []

    num = 0
    total = 0

    for comp in comps:
        # 	print(comp)
        if 'componentVersionName' not in comp:
            continue
        print("- " + comp['componentName'] + '/' + comp['componentVersionName'])
        for x in comp['_meta']['links']:
            if x['rel'] == 'vulnerabilities':
                # custom_headers = {'Accept': 'application/vnd.blackducksoftware.vulnerability-4+json'}
                # response = hub.execute_get(x['href'] + "?limit=9999", custom_headers=custom_headers)
                # vulns = response.json().get('items', [])
                cvulns = utils.get_json(bd, x['href'] + "")

                for vuln in cvulns['items']:
                    total += 1
                    if vuln['source'] == 'NVD':
                        for y in vuln['_meta']['links']:
                            if y['rel'] == 'related-vulnerabilities':
                                if y['label'] == 'BDSA':
                                    # print("{} has BDSA which disagrees with component version - potential false
                                    # positive".format(vuln['name']))
                                    if vuln['name'] not in cve_list:
                                        cve_list.append(vuln['name'])
                                    num += 1

    print("Found {} total vulnerabilities".format(total))
    print("Found {} CVEs with associated BDSAs but which do not agree on affected component version\n".format(num))

    ret = patch_cves(bd, projverurl, cve_list, vulns)
    return ret
