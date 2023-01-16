from blackduck import Client

bd = Client(
    token='MmE1OTdjOGMtOTJlMC00ZWUxLTljMTAtOWY5ZTUyYTQ4ODk5OmVhYTJjMTEzLWJiMDItNDdiOC1iY2JkLTMyYjE1YWQzZWZlMQ==',
    base_url='https://poc39.blackduck.synopsys.com',
    # verify=False  # TLS certificate verification
)

print(bd.get_json("/api/projects?offset=0&limit=100")['items'])

for project in bd.get_resource('projects'):
    print(project['name'])
    resource_dict = bd.list_resources(project)

    # Obtain url to the parent itself
    url = resource_dict['href']  # e.g. /api/projects/de69a1e2-a703-44a9-8e9d-c3b8472972cb

    # Obtain url for the project versions
    url = resource_dict['versions']  # e.g. /api/projects/de69a1e2-a703-44a9-8e9d-c3b8472972cb/versions
    print(url)