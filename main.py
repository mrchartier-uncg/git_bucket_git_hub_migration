# heavily inspired by https://gist.github.com/rbellamy/3c5033ba605a090824e8
# gets everything from bitbucket and brings it across to GH, adding LFS where necessary for file size
# then archives everything brought over
#
# runs on Python 3; does clone --mirror and push --mirror, cleaning up after itself
#
# you need git-lfs installed on the local system
# also make sure you've got git credential caching set up https://help.github.com/articles/caching-your-github-password-in-git/

import json
import requests
import subprocess
import os


# your particulars
bitbucket_user = 'mrchartier'
bitbucket_pass = ''
bitbucket_org = 'uncg-erp'
github_user = 'mrchartier-uncg'
github_access_token = ''
github_org = 'uncg-its'


def get_bitbucket_repos_page(url):
    r = requests.get(url, auth=(bitbucket_user, bitbucket_pass))
    if r.status_code == 200:
        return r.json()

# GET https://api.bitbucket.org/2.0/repositories?role=member
# https://api.bitbucket.org/2.0/repositories/{bitbucket_org}
def get_bitbucket_repos():
    repos = []
    values = ''
    api_url = f"https://api.bitbucket.org/2.0/repositories?role=admin"
    response = get_bitbucket_repos_page(api_url)
    print(response)
    if response is None:
        print('No response')
    else:
        values = response['values']
        while 'next' in response:
            print(f"getting {response['next']}")
            response = get_bitbucket_repos_page(response['next'])
            values = values + response['values']

    for repo in values:
        for clonelink in repo['links']['clone']:
            if clonelink['name'] == 'https':
                clone_url = clonelink['href']
                break
        repos.append((repo['name'], clone_url, repo['description']))

    return repos


def create_github_name(bitbucket_name):
    parts = bitbucket_name.split('_')
    if parts[0].isdigit():
        job_no = parts.pop(0)
        parts.append(job_no)
    return '_'.join(parts).lower().replace(" ", "")


def get_github_origin(repo_name):
    return f"https://github.com/{github_org}/{repo_name}.git"


def create_github_repo(repo_name, repo_description):
    api_url = f"https://api.github.com/orgs/{github_org}/repos"
    r = requests.post(api_url, data=json.dumps({
        "name": repo_name,
        "description": repo_description,
        "private": True,
        'has_issues': False,
        'has_projects': False,
        'has_wiki': False,
        'allow_merge_commit': False,
        'allow_rebase_merge': False,
    }), headers={
        'User-Agent': 'me@marcelkornblum.com',
        'Content-Type': 'application/json'
    }, auth=(github_user, github_access_token))
    print(r.url)

    if r.status_code >= 200 and r.status_code < 300:
        return True
    return False


def update_github_repo_description(repo_name, repo_description):
    api_url = f"https://api.github.com/repos/{github_org}/{repo_name}"
    r = requests.post(api_url, data=json.dumps({
        "description": repo_description
    }), headers={
        'User-Agent': 'me@marcelkornblum.com',
        'Content-Type': 'application/json'
    }, auth=(github_user, github_access_token))
    print(r.url)

    if r.status_code >= 200 and r.status_code < 300:
        return True
    return False


def archive_github_repo(repo_name):
    api_url = f"https://api.github.com/repos/{github_org}/{repo_name}"
    r = requests.patch(api_url, data=json.dumps({
        "name": repo_name,
        "archived": True,
    }), headers={
        'User-Agent': 'me@marcelkornblum.com',
        'Content-Type': 'application/json'
    }, auth=(github_user, github_access_token))
    print(r.url)

    if r.status_code >= 200 and r.status_code < 300:
        return True
    return False


def clone(bitbucket_origin, path):
    process = subprocess.Popen(
        ["git", "clone", "--mirror", bitbucket_origin, path], stdout=subprocess.PIPE)
    process.communicate()[0]


def lfs(path):
    conf = []
    process = subprocess.Popen(
        ["git", "lfs", "migrate", "info", "--above=100MB"], stdout=subprocess.PIPE, cwd=path)
    for line in iter(process.stdout.readline, b''):
        parts = line.split()
        if len(parts) > 0:
            conf.append(parts[0])
    process.communicate()
    while len(conf) > 0:
        process = subprocess.Popen(
            ["git", "lfs", "migrate", "import", f'--include="{conf.pop()}"'], stdout=subprocess.PIPE, cwd=path)


def push(github_origin, path):
    process = subprocess.Popen(
        ["git", "push", "--mirror", github_origin], stdout=subprocess.PIPE, cwd=path)
    process.communicate()[0]


def delete(path):
    process = subprocess.Popen(
        ["rm", "-rf", path], stdout=subprocess.PIPE)
    process.communicate()[0]


def migrate(bb_repo_name, bb_repo_clone_url, bb_repo_desc):
    repo_clone_url = ''.join([bb_repo_clone_url.split(
        '@')[0], ':', bitbucket_pass, '@', bb_repo_clone_url.split('@')[1]])
    gh_repo = create_github_name(bb_repo_name, bb_repo_desc)
    print(f"{bb_repo_name} converted to {gh_repo}")
    if not create_github_repo(gh_repo):
        print("failed to create GH repo ")
        pass
    else:
        print("new GH repo created")
    try:
        local_path = f"/tmp/{gh_repo}"
    except FileNotFoundError:
        os.mkdir(local_path)
    #delete(local_path)
    clone(repo_clone_url, local_path)
    print(f"cloned to {local_path}")
    lfs(local_path)
    push(get_github_origin(gh_repo), local_path)
    print(f"pushed to {get_github_origin(gh_repo)}")
    # archive_github_repo(gh_repo)
    # print("Archived GH repo")
    # delete(local_path)
    # print("deleted local folder")


# all_repos = get_bitbucket_repos()
#


if __name__ == '__main__':
    all_repos = get_bitbucket_repos()
    for repo in all_repos:
        print(repo)
        #update_repo = update_github_repo_description(repo[0], repo[2])
        #print(update_repo)
        #migrate(*repo)
