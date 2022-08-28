import re, sqlite3, stat

from pydriller import RepositoryMining

import pandas as pd
import logging as log
import os, shutil
import db_settings

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
repos_commit_csv = os.path.join(APP_ROOT, 'repos_commit_csv')
repos_commit_csv_filtered = os.path.join(APP_ROOT, 'repos_commit_csv_filtered')
repos_dir = os.path.join(APP_ROOT, 'repos_dir')
commit_changes_dir = os.path.join(APP_ROOT, 'commit_changes_dir')

log.basicConfig(level=log.INFO,
                format='%(asctime)s :: proc_id %(process)s :: %(funcName)s :: %(levelname)s :: %(message)s')


def clean_directory(path):
    if os.name == 'nt':
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), stat.S_IRWXU)
            for file in files:
                os.chmod(os.path.join(root, file), stat.S_IRWXU)

    return shutil.rmtree(path, ignore_errors=True)


def remove_empty_files(folder):
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.stat(file_path).st_size == 0 or os.stat(file_path).st_size == 1:
            os.remove(file_path)


def delete_repo(repo_dir):
    shutil.rmtree(repo_dir)


def repo_mining(repo_url, repo_name, num, branch):
    commits_elm = list()
    try:
        for commit in RepositoryMining(repo_url, clone_repo_to=repos_dir).traverse_commits():

            print(repo_name)

            for m in commit.modifications:
                commits_elm.append({
                    'repo_name': repo_name,
                    'commit_sha': commit.hash,
                    'commit_url': 'https://github.com/' + repo_name + '/commit/' + commit.hash,
                    'commit_date': commit.committer_date,
                    'author': commit.author.name,
                    'modified_file_new_path': m.new_path,
                    'modified_file': 'https://github.com/' + repo_name + '/blob/' + branch + '/' + m.new_path,
                    'change_type': m.change_type.name,
                    'commit_message': commit.msg
                })

            commits_data = pd.DataFrame(commits_elm)
            commits_data = commits_data.drop_duplicates()
            csv_name = str(num) + '-commit-list-' + repo_name.replace('/', '-') + '.csv'
            csv_location_path = os.path.join(repos_commit_csv, csv_name)
            commits_data.to_csv(csv_location_path, sep=',', encoding='utf-8', index=False)
    except Exception as e:
        print(e)
        pass


def filter_commits(folder, conn, repo_dir):
    important_elm = list()
    github_files = list()

    try:

        for csv in os.listdir(folder):

            path_gh_workflow_dir = os.path.join(repos_dir, repo_dir + '/.github/workflows')

            if os.path.exists(path_gh_workflow_dir):
                for file in os.listdir(path_gh_workflow_dir):
                    list_inf.append(file)
                    github_files.append(file)

            path_csv_file = os.path.join(folder, csv)
            df = pd.read_csv(path_csv_file)

            for num, row in enumerate(df['modified_file']):
                for check in list_inf:
                    if re.search(check, str(row).lower()):
                        important_elm.append(df.loc[num])
            for num, row in enumerate(df['commit_message']):
                for k_check in list_keywords:
                    if re.search(k_check, str(row).lower()):
                        important_elm.append(df.loc[num])

            new_commits_data = pd.DataFrame(important_elm)
            csv_filtered_path = os.path.join(repos_commit_csv_filtered, csv.replace('.csv', '-filtered.csv'))
            new_commits_data.to_csv(csv_filtered_path, sep=',', encoding='utf-8', index=False)

            new_commits_data.to_sql(name='repo_commit', con=conn, if_exists='append', index=False)
            conn.commit()

            for elm in github_files:
                list_inf.remove(elm)

            important_elm.clear()

    except Exception as e:
        print(e)
        pass


def repo_analysis(csv_name, report_path):
    df = pd.read_csv(csv_name)

    for num, repo_name in enumerate(df['Repo_Name']):
        try:
            default_branch = df['Default_Branch'][num]
            conn = sqlite3.connect('commits.db')

            log.info(f'Started : {repo_name} (Repo n. {int(num) + 1} of {df["Repo_Name"].count()}) ...')

            repo_url = 'https://github.com/' + repo_name
            repo_dir = os.path.join(repos_dir, repo_name.split('/')[1])
            log.info(f'Mining {repo_name}')
            repo_mining(repo_url, repo_name, num, default_branch)
            log.info(f'Filtering {repo_name}')
            filter_commits(repos_commit_csv, conn, repo_dir)

            # if files contained into the list_inf are not identified goes to delete the repo, otherways goes to check
            # differences and then delete repo.
            csv_name = str(num) + '-commit-list-' + repo_name.replace('/', '-') + '-filtered.csv'
            csv_path_check = os.path.join(repos_commit_csv_filtered, csv_name)
            df_filtered = pd.read_csv(csv_path_check)
            if df_filtered.empty:
                log.info(f'Deleting {repo_name}')
                print(
                    f'Repo {repo_name}. URL {"https://github.com/" + repo_name}. Empty.'
                    , file=open(report_path, 'a'))
                remove_empty_files(repos_commit_csv_filtered)
            else:
                log.info(f'Deleting {repo_name}')
                delete_repo(repo_dir)
                remove_empty_files(repos_commit_csv_filtered)
        except Exception as e:
            print(e)
            print(f'Error --> {repo_name}. URL {"https://github.com/" + repo_name}. Type of error {e}'
                  , file=open(report_path, 'a'))
            continue


if __name__ == '__main__':

    repos_list = []
    list_inf = ['circle*', 'gitlab*', 'jenkins*', 'semaphore*', 'travis*', 'appveyor*', 'wercker*', 'bamboo*']
    list_keywords = ['security*', 'vuln*', 'testing*', 'penetration', 'scan*', 'detect', 'secre*', 'pentest*']
    csv_file = 'test.csv'

    report_path = os.path.join(APP_ROOT, 'report.txt')

    # Cleaning directories created before

    clean_directory(repos_commit_csv)
    log.info(f'{repos_commit_csv} cleaned...')

    clean_directory(repos_commit_csv_filtered)
    log.info(f'{repos_commit_csv_filtered} cleaned...')

    clean_directory(repos_dir)
    log.info(f'{repos_dir} cleaned...')

    if os.path.isfile(report_path):
        os.remove(report_path)

    if not os.path.exists(repos_commit_csv):
        os.makedirs(repos_commit_csv)
        log.info('Directory repos_commit_csv created...')

    if not os.path.exists(repos_commit_csv_filtered):
        os.makedirs(repos_commit_csv_filtered)
        log.info('Directory repos_commit_csv created...')

    if not os.path.exists(repos_dir):
        os.makedirs(repos_dir)
        log.info('Directory repos_commit_csv created...')

    # Starting process

    repo_analysis(csv_file, report_path)
    remove_empty_files(commit_changes_dir)
