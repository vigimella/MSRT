import re
import stat

from pydriller import RepositoryMining
import pandas as pd
import logging as log
import os, shutil

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


def delete_repo(repo_dir):
    shutil.rmtree(repo_dir)


def repo_mining(repo_url, repo_name, num):
    commits_elm = list()
    try:
        for commit in RepositoryMining(repo_url, clone_repo_to=repos_dir).traverse_commits():



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
    except Exception as e:
        print(e)
        pass


def filter_commits(folder):
    important_elm = list()
    try:
        for csv in os.listdir(folder):

            path_csv_file = os.path.join(folder, csv)
            df = pd.read_csv(path_csv_file)
            for num, row in enumerate(df['Modified_file']):
                for check in list_inf:
                    if re.search(check, str(row).lower()):
                        important_elm.append(df.loc[num])

            new_commits_data = pd.DataFrame(important_elm)
            new_commits_data.to_csv(os.path.join(repos_commit_csv_filtered, csv.replace('.csv', '-filtered.csv')),
                                    sep=',',
                                    encoding='utf-8')
            os.remove(path_csv_file)
            important_elm.clear()
    except Exception as e:
        print(e)
        pass


def diff_commit(csv_filtered_folder, repo_dir, repo_name, num):
    for csv in os.listdir(csv_filtered_folder):

        path_csv_file = os.path.join(csv_filtered_folder, csv)
        df = pd.read_csv(path_csv_file)

        try:
            for file in df['Modified_file'].drop_duplicates():
                cleaned_name = file.replace('.', '').replace('yml', '')
                os.chdir(repo_dir)
                os.system(
                    f'git log -p -- {file} >> {commit_changes_dir}/{num}-history-{repo_name.replace("/", "-")}-{cleaned_name}.txt')
                os.chdir(APP_ROOT)
        except Exception as e:
            print(e)
            continue


def repo_analysis(csv_name, report_path):
    df = pd.read_csv(csv_name)

    for num, repo_name in enumerate(df['Repo_Name']):
        try:
            log.info(f'Started : {repo_name} (Repo n. {int(num) + 1} of {df["Repo_Name"].count()}) ...')

            repo_url = 'https://github.com/' + repo_name
            repo_dir = os.path.join(repos_dir, repo_name.split('/')[1])
            log.info(f'Mining {repo_name}')
            repo_mining(repo_url, repo_name, num)
            log.info(f'Filtering {repo_name}')
            filter_commits(repos_commit_csv)

            # if files contained into the list_inf are not identified goes to delete the repo, otherways goes to check
            # differences and then delete repo.
            csv_name = str(num) + '-commit_list-' + repo_name.replace('/', '_') + '-filtered.csv'
            csv_path_check = os.path.join(repos_commit_csv_filtered, csv_name)
            df_filtered = pd.read_csv(csv_path_check)
            if df_filtered.empty:
                log.info(f'Deleting {repo_name}')
                delete_repo(repo_dir)
            else:
                log.info(f'Differences')
                diff_commit(repos_commit_csv_filtered, repo_dir, repo_name, num)
                log.info(f'Deleting {repo_name}')
                delete_repo(repo_dir)
        except Exception as e:
            print(e)
            print(f'Error during downloading of {repo_name}. URL {"https://github.com/" + repo_name}. Type of error {e}'
                  ,  file=open(report_path, 'a'))
            continue


def remove_empty_files(folder):
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.stat(file_path).st_size == 0:
            os.remove(file_path)


if __name__ == '__main__':

    repos_list = []
    list_inf = ['circle*', 'gitlab*', 'jenkins*', 'semaphore*', 'travis*', 'appveyor*', 'wercker*', 'bamboo*']
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
