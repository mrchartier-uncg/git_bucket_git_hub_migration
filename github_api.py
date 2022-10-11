import requests
import json

github_user = 'mrchartier-uncg'
github_access_token = ''
github_org = 'uncg-its'
github_team_name = 'ERP Developer'

header = {
    'User-Agent': 'mrchartier@uncg.edu',
    'Content-Type': 'application/vnd.github+json'
}


def github_check_my_repos(headers=header):
    repo_list = []
    r = requests.get(f'https://api.github.com/orgs/{github_org}/repos',
                     headers=headers,
                     auth=(github_user, github_access_token)
                     )
    data = r.json()
    for repo in data:
        repo_list.append(repo['name'])
    return repo_list


def github_get_org_id(headers=header):
    '''This function takes the headers and pulls the needed org id for future use.'''
    r = requests.get(f'https://api.github.com/orgs/{github_org}',
                     headers=headers,
                     auth=(github_user, github_access_token)
                     )
    data = r.json()
    data = data['id']
    return data


def github_get_team_id(headers=header):
    '''This function takes the headers and pulls the needed team id for future use.'''
    r = requests.get(f'https://api.github.com/orgs/{github_org}/teams',
                     headers=headers,
                     auth=(github_user, github_access_token)
                     )
    data = r.json()
    for item in data:
        if item['name'] == github_team_name:
            data = item['id']
        else:
            pass
    return data


def github_add_team_to_repo(github_team_id, repo, headers=header):
    '''This function takes the headers and pulls the needed team id for future use.'''

    r = requests.put(f'https://api.github.com/orgs/{github_org}/teams/erp-developer/repos/{github_org}/{repo}',
                     headers=headers,
                     auth=(github_user, github_access_token),
                     data=json.dumps({"permission": "pull"})
                     )
    return r


if __name__ == '__main__':
    repo_list = github_check_my_repos()
    item_list = []
    print(repo_list)
    org_id = github_get_org_id()
    team_id = github_get_team_id()
    for item in repo_list:
        item_list.append(item)
        print(item)
    for repo in item_list:
        print(repo)
        add_repo = github_add_team_to_repo(team_id, repo)
        print(f'repo:{repo} - added: {add_repo}')
