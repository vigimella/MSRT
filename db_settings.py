import sqlite3, csv

conn = sqlite3.connect('commits.db')

c = conn.cursor()

print('Creating repository, repo_commit, and commit_changes tables ...')

c.execute('''CREATE TABLE if not exists repository(
                id_repo integer primary key not null,
                repo_name varchar(40) not null,
                repo_language varchar(20) not null,
                repo_creation varchar(30) not null,
                repo_modification varchar(30) not null,
                repo_size integer not null,
                repo_stars integer not null,
                repo_forks integer not null
                )''')
c.execute(''' CREATE TABLE IF NOT EXISTS repo_commit(
                id_commit integer primary key not null,
                repo_name varchar(40) not null,
                commit_sha varchar(250) not null,
                commit_date varchar(30) not null,
                author varchar(50) not null,
                modified_file varchar(50) not null,
                change_type varchar(10) not null,
                commit_message text not null,
                FOREIGN KEY(id_commit) REFERENCES repository(id_repo)
                )''')
c.execute(''' CREATE TABLE IF NOT EXISTS commit_changes(
                id_change integer primary key not null,
                repo_name varchar(40) not null,
                file_url varchar(100) not null,
                FOREIGN KEY(id_change) REFERENCES repository(id_commit)
                )''')

print('Cleaning repository, repo_commit, and commit_changes tables ...')

c.execute('DELETE FROM repository;')
c.execute('DELETE FROM repo_commit;')
c.execute('DELETE FROM commit_changes;')

print('Populating repository table...')

with open('test.csv', 'r') as fin:
    dr = csv.DictReader(fin)
    to_db = [(i['Repo_Name'].replace("/", "-"), i['Language'], i['Created_At'], i['Modified_At'], i['Size'], i['Stars'], i['Forks']) for i
             in dr]

for data in to_db:
    c.execute('INSERT INTO repository (repo_name, repo_language, repo_creation, repo_modification, repo_size, '
              'repo_stars, repo_forks) VALUES (?,?,?,?,?,?,?)', data)
    conn.commit()

print('Starting mining...')

conn.close()
