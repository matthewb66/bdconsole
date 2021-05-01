# import json
import os


def get_snippet_entries(hub, path):
    paramstring = "?filter=bomMatchReviewStatus%3Anot_reviewed&filter=bomMatchType%3Asnippet&offset=0&limit=5000"

    # Using internal API - see https://jira.dc1.lan/browse/HUB-18270: Make snippet API calls for ignoring,
    # confirming snippet matches public
    splits = path.split('/')
    "{}/internal/projects/{}/versions/{}/source-bom-entries"
    url = "{}/internal/projects/{}/versions/{}/source-bom-entries".format(hub.get_apibase(), splits[5], splits[7]) \
          + paramstring
    # print(url)
    response = hub.execute_get(url)
    if response.ok:
        return response.json()
    else:
        return ''


def ignore_snippet_bom_entry(hub, url, scanid, nodeid, snippetid, ignore):
    if ignore:
        post_body = '{ "ignored": true }'
    else:
        post_body = '{ "ignored": false }'

    fullurl = "{}/scans/{}/nodes/{}/snippets/{}".format(url, scanid, nodeid, snippetid)
    # 	print(url)

    response = hub.execute_put(fullurl, post_body)
    return response.ok


def get_snippets_data(hub, path):

    csv_data = "{},{},{},{},{},{},{},{},{}\n".format("file", "size", "block", "coveragepct", "matchlines",
                                                        "status", "scanid", "nodeid", "snippetid")
    alreadyignored = 0
    count = 0
    print('Getting snippet data ... ')
    snippet_bom_entries = get_snippet_entries(hub, path)
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
                if 'coverage' in match.keys():
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
