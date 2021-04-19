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


def ignore_snippet_bom_entry(hub, path, snippet_bom_entry, ignore):
    if ignore:
        post_body = '{ "ignored": true }'
    else:
        post_body = '{ "ignored": false }'

    scanid = snippet_bom_entry['scanId']
    nodeid = snippet_bom_entry['compositeId']
    snippetid = snippet_bom_entry['fileSnippetBomComponents'][0]['hashId']
    url = "{}/scans/{}/nodes/{}/snippets/{}".format(path, scanid, nodeid, snippetid)
    # 	print(url)

    response = hub.execute_put(url, post_body)
    return response.ok


def get_snippets_data(hub, path):
    csv_data = "{},{},{},{},{},{}\n".format("file", "size", "block", "coveragepct", "matchlines", "status")
    alreadyignored = 0
    snippet_bom_entries = get_snippet_entries(hub, path)
    if snippet_bom_entries != '':
        # print(snippet_bom_entries)
        for snippet_item in snippet_bom_entries['items']:
            blocknum = 1
            for match in snippet_item['fileSnippetBomComponents']:
                if match['ignored']:
                    alreadyignored += 1

                if match['ignored']:
                    igstatus = "Ignored"
                else:
                    igstatus = "Not ignored"
                matchedlines = match['sourceEndLines'][0] - match['sourceStartLines'][0]
                filename = os.path.join(match['matchFilePath'], snippet_item['name'])
                csv_data += "{},{},{},{},{},{}\n".format(filename, snippet_item['size'], blocknum, match['matchCoverage'],
                                                 matchedlines, igstatus)
                blocknum += 1

    return csv_data
