import re, sqlite3, stat, os, shutil, spacy, nltk, glob

import pandas as pd
import logging as log

from db_settings import settings_db
from pydriller import RepositoryMining
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from concurrent.futures import ThreadPoolExecutor

nlp = spacy.load("en_core_web_sm")
nltk.download('punkt')  # for tokenization
nltk.download('stopwords')

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
repos_commit_csv = os.path.join(APP_ROOT, 'repos_commit_csv')
repos_dir = os.path.join(APP_ROOT, 'repos_dir')
db_dir = os.path.join(APP_ROOT, 'db')
log.basicConfig(level=log.INFO,
                format='%(asctime)s :: proc_id %(process)s :: %(funcName)s :: %(levelname)s :: %(message)s')


def nlp_process(repo_commit):
    # sentence tokenization
    tokens = nltk.word_tokenize(repo_commit)
    # punctuation and digits removal
    tokens = [token.lower() for token in tokens if token.isalpha()]
    # stopwords
    stop_words = set(stopwords.words("english"))
    list_filtered_sent = list()
    for w in tokens:
        if w not in stop_words:
            list_filtered_sent.append(w)

    ps = PorterStemmer()
    stemmed_words = list()
    for w in list_filtered_sent:
        stemmed_words.append(ps.stem(w))

    filtered_sent = ' '.join(stemmed_words)

    return filtered_sent


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


def repo_analysis(repo_name, default_branch):
    conn = sqlite3.connect('./db/commits.db')

    commits_elm = list()

    dataf = pd.read_csv(csv_file)

    num = dataf[dataf['Repo_Name'] == repo_name].index[0]

    log.info(f'Started : {repo_name} | {str(num + 1)} of {dataf["Repo_Name"].count()}')

    repo_url = 'https://test:test@github.com/' + repo_name
    repo_dir = os.path.join(repos_dir, repo_name.split('/')[1])
    log.info(f'Mining {repo_name}')

    try:
        for commit in RepositoryMining(repo_url, clone_repo_to=repos_dir).traverse_commits():
            for m in commit.modifications:
                commits_elm.append({
                    'repo_name': repo_name,
                    'commit_sha': commit.hash,
                    'commit_url': 'https://github.com/' + repo_name + '/commit/' + commit.hash,
                    'commit_date': commit.committer_date,
                    'author': commit.author.name,
                    'modified_file_new_path': m.new_path,
                    'modified_file': 'https://github.com/' + repo_name + '/blob/' + default_branch + '/' + m.new_path,
                    'change_type': m.change_type.name,
                    'commit_message': commit.msg
                })

            commits_data = pd.DataFrame(commits_elm)
            commits_data = commits_data.drop_duplicates()
            csv_name = 'commit-list-' + repo_name.replace('/', '-') + '.csv'
            csv_location_path = os.path.join(repos_commit_csv, csv_name)
            commits_data.to_csv(csv_location_path, sep=',', encoding='utf-8', index=False)
    except:
        pass

    log.info(f'Filtering {repo_name}')

    try:

        important_elm = list()
        github_files = list()

        path_gh_workflow_dir = os.path.join(repos_dir, repo_dir + '/.github/workflows')

        if os.path.exists(path_gh_workflow_dir):
            for file in os.listdir(path_gh_workflow_dir):
                ci_cd_platforms.append(file)
                github_files.append(file)

        csv_name = 'commit-list-' + repo_name.replace('/', '-') + '.csv'
        csv_location_path = os.path.join(repos_commit_csv, csv_name)

        data_frame = pd.read_csv(csv_location_path)

        for num in range(data_frame['commit_sha'].count()):

            # commit message elm (row, column)
            cm_row = data_frame.iloc[num, 8]
            # modified_file elm (row, column)
            mf_row = data_frame.iloc[num, 6]

            cleaned_msg = nlp_process(cm_row)

            for ci_cd in ci_cd_platforms:
                for keyword in keywords:
                    if re.search(ci_cd, mf_row.lower()) and '.yml' in mf_row and re.search(keyword, cleaned_msg):
                        important_elm.append(data_frame.loc[num])

        new_commits_data = pd.DataFrame(important_elm)
        new_commits_data.to_sql(name='repo_commit', con=conn, if_exists='append', index=False)
        conn.commit()

        # Delete records with the same repo_name and commit_sha to avoid redundancy.

        cursor = conn.cursor()
        sqlite_select_query = """DELETE FROM repo_commit WHERE id_commit NOT IN (SELECT min(id_commit) FROM 
                                    repo_commit GROUP BY repo_name, commit_sha); """

        cursor.execute(sqlite_select_query)
        cursor.close()
    except:
        pass
    # remove all repos stored in repo_dir
    shutil.rmtree(repo_dir)

    # remove all files stored in repos_commit_csv

    for file in os.listdir(repos_commit_csv):
        os.remove(os.path.join(repos_commit_csv, file))
        print(f'REMOVED : {file}')


if __name__ == '__main__':

    repos_list = []
    ci_cd_platforms = ['circle*', 'gitlab*', 'jenkins*', 'semaphore*', 'travis*', 'appveyor*', 'wercker*', 'bamboo*']
    keywords = ['', 'security*', 'vuln*', 'testing*', 'penetration*', 'scan*', 'detect*', 'secre*', 'pentest*', 'cve*',
                'clair', 'websecurity', 'devsec*', 'information-security', 'infosec*', 'appsec*']

    csv_file = glob.glob('*.{}'.format('csv'))[0]
    N_THREADS = 4

    report_path = os.path.join(APP_ROOT, 'report.txt')

    # Cleaning directories created before

    clean_directory(repos_commit_csv)
    log.info(f'{repos_commit_csv} cleaned...')

    clean_directory(repos_dir)
    log.info(f'{repos_dir} cleaned...')

    if os.path.isfile(report_path):
        os.remove(report_path)

    if not os.path.exists(repos_commit_csv):
        os.makedirs(repos_commit_csv)
        log.info('Directory repos_commit_csv created...')

    if not os.path.exists(repos_dir):
        os.makedirs(repos_dir)
        log.info('Directory repos_commit_csv created...')

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        log.info('Directory db_dir created...')

    # Starting process
    settings_db()

    repo_list = list()
    branch_list = list()

    df = pd.read_csv(csv_file)

    for name in df['Repo_Name']:
        repo_list.append(name)
    for branch in df['Default_Branch']:
        branch_list.append(branch)

    with ThreadPoolExecutor(max_workers=N_THREADS) as executor:
        try:
            executor.map(repo_analysis, repo_list, branch_list)
        except:
            pass