from pydriller import RepositoryMining
import pandas as pd
import logging as log
import os, git, shutil

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
repos_dir = os.path.join(APP_ROOT, 'repos_dir')
repos_commit_csv = os.path.join(APP_ROOT, 'repos_commit_csv')

# log.basicConfig(level=log.INFO,format='%(asctime)s :: proc_id %(process)s :: %(funcName)s :: %(levelname)s :: %(
# message)s')


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

    for num, repo in enumerate(df['Repo_Name']):

        log.info(f'Analyzing {repo} ({int(num) + 1} of {df["Repo_Name"].count()}) ...')

        repo_url = 'https://github.com/' + repo
        repos_list.append(repo_url)

        mod_commits = list()
        for commit in RepositoryMining(repo_url,
                                       only_modifications_with_file_types=['.yml', 'Jenkinsfile']).traverse_commits():
            for m in commit.modifications:
                mod_commits.append({
                    'SHA': commit.hash,
                    'Commit_date': commit.committer_date,
                    'Author': commit.author.name,
                    'Modified_file': m.filename,
                    'Change_type': m.change_type.name,
                    'Commit Message': commit.msg
                })

        commits_data = pd.DataFrame(mod_commits)
        repo_name = repo.replace('/', '_')
        csv_name = str(num)+'_commit_list_' + repo_name + '.csv'
        csv_location_path = os.path.join(repos_commit_csv, csv_name)

        commits_data.to_csv(csv_location_path, sep=',', encoding='utf-8')

        list().clear()

        log.info(f'Cloning {repo} in local storage...')

        git.Git(repos_dir).clone(repo_url)

        log.info(f'Cloning {repo} is ended...')


if __name__ == '__main__':

    repos_list = []
    csv_file = 'test.csv'

    if not os.path.exists(repos_dir):
        os.makedirs(repos_dir)
        log.info('Directory repos_dir created...')
    if not os.path.exists(repos_commit_csv):
        os.makedirs(repos_commit_csv)
        log.info('Directory repos_commit_csv created...')

    # Cleaning directories created before

    clean_directory(repos_dir)
    log.info(f'{repos_dir} cleaned...')
    clean_directory(repos_commit_csv)
    log.info(f'{repos_commit_csv} cleaned...')

    # Starting process

    repo_analysis(csv_file)
