def get_json(bd, bdurl, headers=''):
    # Check if url includes ?
    loops = 1
    if '?' in bdurl:
        bdurl += '&limit=1000'
    else:
        bdurl += '?limit=1000'

    if headers != '':
        jsondata = bd.get_json(bdurl, headers=headers)
    else:
        jsondata = bd.get_json(bdurl)

    fetched = 0
    if 'items' in jsondata:
        fetched = len(jsondata['items'])

    total = 0
    if 'totalCount' in jsondata:
        total = jsondata['totalCount']

    if fetched == 0:
        return {
            'totalCount': 0,
            'items': []
        }

    offset = 1000
    if total > fetched:
        while fetched <= total:
            loops += 1
            newurl = bdurl + f"&offset={offset}"
            nextfetched = 0
            if headers != '':
                nextjsondata = bd.get_json(newurl, headers=headers)
            else:
                nextjsondata = bd.get_json(newurl)
            if 'items' in nextjsondata:
                nextfetched = len(nextjsondata['items'])
            if nextfetched == 0:
                break
            fetched += nextfetched
            offset += 1000
            jsondata['items'] += nextjsondata['items']

    print(f"utils.get_json(): {bdurl} Looped {loops} times")

    return jsondata
