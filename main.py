import re

from pydriller import RepositoryMining
import pandas as pd
import logging as log
import os, git, shutil, time

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
repos_commit_csv = os.path.join(APP_ROOT, 'repos_commit_csv')
repos_commit_csv_filtered = os.path.join(APP_ROOT, 'repos_commit_csv_filtered')
repos_dir = os.path.join(APP_ROOT, 'repos_dir')
commit_changes_dir = os.path.join(APP_ROOT, 'commit_changes_dir')

log.basicConfig(level=log.INFO,
                format='%(asctime)s :: proc_id %(process)s :: %(funcName)s :: %(levelname)s :: %(message)s')


def clean_directory(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            log.info('Failed to delete %s. Reason: %s' % (file_path, e))


def clone_repo(repo_url, repo_dir):
    git.Repo.clone_from(repo_url, repo_dir)


def delete_repo(repo_dir):
    shutil.rmtree(repo_dir)


def repo_mining(repo_url, repo_name, num):
    commits_elm = list()

    for commit in RepositoryMining(repo_url).traverse_commits():

        for m in commit.modifications:
            commits_elm.append({
                'Repo_Name': repo_name,
                'Commit_URL': commit.hash,
                'Commit_date': commit.committer_date,
                'Author': commit.author.name,
                'Modified_file': m.filename,
                'Change_type': m.change_type.name,
                'Commit Message': commit.msg
            })

        commits_data = pd.DataFrame(commits_elm)
        repo_name = repo_name.replace('/', '_')
        csv_name = str(num) + '-commit_list-' + repo_name + '.csv'
        csv_location_path = os.path.join(repos_commit_csv, csv_name)

        commits_data.to_csv(csv_location_path, sep=',', encoding='utf-8')


def filter_commits(csv_folder):
    important_elm = list()

    for csv in os.listdir(csv_folder):

        path_csv_file = os.path.join(csv_folder, csv)

        df = pd.read_csv(path_csv_file)
        for num, row in enumerate(df['Modified_file']):
            for check in list_inf:
                if re.search(check, str(row).lower()):
                    important_elm.append(df.loc[num])

        new_commits_data = pd.DataFrame(important_elm)
        new_commits_data.to_csv(os.path.join(repos_commit_csv_filtered, csv + '-filtered'), sep=',', encoding='utf-8')
        important_elm.clear()


def diff_commit(csv_filtered_folder, repo_dir, repo_name, num):

    for csv in os.listdir(csv_filtered_folder):

        path_csv_file = os.path.join(csv_filtered_folder, csv)
        df = pd.read_csv(path_csv_file)

        csv_commit_folder = os.path.join(commit_changes_dir, repo_name.replace('/', '-'))

        if not os.path.exists(csv_commit_folder):
            os.mkdir(csv_commit_folder)

        for file in df['Modified_file'].drop_duplicates():
            cleaned_name = file.replace('.', '').replace('yml', '')
            os.chdir(repo_dir)
            os.system(f'git log -p -- {file} >> {csv_commit_folder}/{num}-{cleaned_name}.txt')
            os.chdir(APP_ROOT)


def repo_analysis(csv_name):
    df = pd.read_csv(csv_name)

    for num, repo_name in enumerate(df['Repo_Name']):
        log.info(f'Started : {repo_name} (Repo n. {int(num) + 1} of {df["Repo_Name"].count()}) ...')

        repo_url = 'https://github.com/' + repo_name
        repo_dir = os.path.join(repos_dir, repo_name.replace('/', '-'))
        log.info(f'Cloning {repo_name}')
        clone_repo(repo_url, repos_dir)
        log.info(f'Mining {repo_name}')
        repo_mining(repo_url, repo_name, num)
        log.info(f'Filtering {repo_name}')
        filter_commits(repos_commit_csv)

        while not os.path.isdir(os.path.join(repos_dir, repo_name.replace('/', '-'))):
            time.sleep(30)
            print('waiting...')
        else:
            log.info(f'Differences')
            diff_commit(repos_commit_csv_filtered, repos_dir, repo_name, num)
            log.info(f'Deleting {repo_name}')
            shutil.rmtree(repo_dir)


if __name__ == '__main__':

    repos_list = []
    list_inf = ['circle*', 'gitlab*', 'jenkins*', 'semaphore*', 'travis*', 'appveyor*', 'wercker*', 'bamboo*']
    csv_file = 'test.csv'

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

    # Cleaning directories created before

    clean_directory(repos_commit_csv)
    log.info(f'{repos_commit_csv} cleaned...')

    clean_directory(repos_commit_csv_filtered)
    log.info(f'{repos_commit_csv_filtered} cleaned...')

    clean_directory(repos_dir)
    log.info(f'{repos_dir} cleaned...')

    clean_directory(commit_changes_dir)
    log.info(f'{commit_changes_dir} cleaned...')

    # Starting process

    repo_analysis(csv_file)
