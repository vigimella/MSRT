import re

from pydriller import RepositoryMining
import pandas as pd
import logging as log
import os, shutil

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
repos_commit_csv = os.path.join(APP_ROOT, 'repos_commit_csv')
repos_commit_csv_filtered = os.path.join(APP_ROOT, 'repos_commit_csv_filtered')

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


def repo_analysis(csv_name):
    df = pd.read_csv(csv_name)

    # get repo name from csv file in Repo_Name column

    for num, repo in enumerate(df['Repo_Name']):

        commits_elm = list()

        log.info(f'Mining {repo} (Repo n. {int(num) + 1} of {df["Repo_Name"].count()}) ...')

        repo_url = 'https://github.com/' + repo

        for commit in RepositoryMining(repo_url).traverse_commits():

            for m in commit.modifications:
                commits_elm.append({
                    'Repo_URL': repo_url,
                    'Commit_URL': repo_url + '/commit/' + commit.hash,
                    'Commit_date': commit.committer_date,
                    'Author': commit.author.name,
                    'Modified_file': m.filename,
                    'Change_type': m.change_type.name,
                    'Commit Message': commit.msg
                })

        # save csv for each repository analyzed.

        commits_data = pd.DataFrame(commits_elm).set_index('Repo_URL')
        repo_name = repo.replace('/', '_')
        csv_name = str(num) + '-commit_list-' + repo_name + '.csv'
        csv_location_path = os.path.join(repos_commit_csv, csv_name)

        commits_data.to_csv(csv_location_path, sep=',', encoding='utf-8')


def save_pipeline_commits(csv_folder):

    important_elm = list()

    for csv in os.listdir(csv_folder):

        path_csv_file = os.path.join(csv_folder, csv)

        df = pd.read_csv(path_csv_file)
        for num, row in enumerate(df['Modified_file']):
            for check in list_inf:
                if re.search(check, str(row).lower()):
                    important_elm.append(df.loc[num])

        new_commits_data = pd.DataFrame(important_elm).set_index('Repo_URL')
        new_commits_data.to_csv(os.path.join(repos_commit_csv_filtered, 'filtered-' + csv), sep=',', encoding='utf-8')
        important_elm.clear()


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

    # Cleaning directories created before

    clean_directory(repos_commit_csv)
    log.info(f'{repos_commit_csv} cleaned...')

    clean_directory(repos_commit_csv_filtered)
    log.info(f'{repos_commit_csv_filtered} cleaned...')

    # Starting process

    repo_analysis(csv_file)
    log.info('Repo analysis finished')
    log.info('Filtering commits started')
    save_pipeline_commits(repos_commit_csv)
