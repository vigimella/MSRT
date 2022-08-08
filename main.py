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
        if os.stat(file_path).st_size == 0:
            os.remove(file_path)


def delete_repo(repo_dir):
    shutil.rmtree(repo_dir)


def repo_mining(repo_url, repo_name, num):
    commits_elm = list()
    try:
        for commit in RepositoryMining(repo_url, clone_repo_to=repos_dir).traverse_commits():

            print(repo_name)

            for m in commit.modifications:
                commits_elm.append({
                    'repo_name': repo_name.replace('_', '/'),
                    'commit_sha': commit.hash,
                    'commit_date': commit.committer_date,
                    'author': commit.author.name,
                    'modified_file': m.filename,
                    'change_type': m.change_type.name,
                    'commit_message': commit.msg
                })

            commits_data = pd.DataFrame(commits_elm)
            commits_data = commits_data.drop_duplicates()
            repo_name = repo_name.replace('/', '-')
            csv_name = str(num) + '-commit-list-' + repo_name + '.csv'
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


def diff_commit(csv_filtered_folder, repo_dir, repo_name, num, conn):
    for csv in os.listdir(csv_filtered_folder):

        path_csv_file = os.path.join(csv_filtered_folder, csv)
        df = pd.read_csv(path_csv_file)

        try:
            for file in df['modified_file'].drop_duplicates():
                cleaned_name = file.replace('.', '-')
                os.chdir(repo_dir)
                os.system(
                    f'git log -p -- {file} >> {commit_changes_dir}/{num}-history-{repo_name.replace("/", "-")}-{cleaned_name}.txt')
                file_url = str(commit_changes_dir) + '/' + str(num) + '-history-' + str(
                    repo_name.replace("/", "-")) + '-' + str(cleaned_name) + '.txt'
                c = conn.cursor()
                c.execute('INSERT INTO commit_changes (repo_name, file_url) VALUES (?,?)', (repo_name.replace("/", "-"), file_url))
                conn.commit()
                os.chdir(APP_ROOT)
        except Exception as e:
            print(e)
            continue


def repo_analysis(csv_name, report_path):
    df = pd.read_csv(csv_name)

    for num, repo_name in enumerate(df['Repo_Name']):
        try:

            conn = sqlite3.connect('commits.db')

            log.info(f'Started : {repo_name} (Repo n. {int(num) + 1} of {df["Repo_Name"].count()}) ...')

            repo_url = 'https://github.com/' + repo_name
            repo_dir = os.path.join(repos_dir, repo_name.split('/')[1])
            log.info(f'Mining {repo_name}')
            repo_mining(repo_url, repo_name, num)
            log.info(f'Filtering {repo_name}')
            filter_commits(repos_commit_csv, conn, repo_dir)

            # if files contained into the list_inf are not identified goes to delete the repo, otherways goes to check
            # differences and then delete repo.
            csv_name = str(num) + '-commit-list-' + repo_name.replace('/', '-') + '-filtered.csv'
            csv_path_check = os.path.join(repos_commit_csv_filtered, csv_name)
            df_filtered = pd.read_csv(csv_path_check)
            if df_filtered.empty:
                log.info(f'Deleting {repo_name}')
                delete_repo(repo_dir)
                print(
                    f'In repo {repo_name}. URL {"https://github.com/" + repo_name}. No keyword identified.'
                    , file=open(report_path, 'a'))
            else:
                log.info(f'Differences')
                diff_commit(repos_commit_csv_filtered, repo_dir, repo_name, num, conn)
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
    list_keywords = ['security*', 'vulnerabilities*', 'testing*', 'test*', 'ci/cd']
    csv_file = 'test.csv'

    report_path = os.path.join(commit_changes_dir, 'report.txt')

    # Cleaning directories created before

    clean_directory(repos_commit_csv)
    log.info(f'{repos_commit_csv} cleaned...')

    clean_directory(repos_commit_csv_filtered)
    log.info(f'{repos_commit_csv_filtered} cleaned...')

    clean_directory(repos_dir)
    log.info(f'{repos_dir} cleaned...')

    clean_directory(commit_changes_dir)
    log.info(f'{commit_changes_dir} cleaned...')

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

    if not os.path.exists(commit_changes_dir):
        os.makedirs(commit_changes_dir)
        log.info('Directory repos_commit_csv created...')

    # Starting process

    repo_analysis(csv_file, report_path)
    remove_empty_files(commit_changes_dir)
