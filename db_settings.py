import sqlite3, csv, os, glob


def settings_db():
    conn = sqlite3.connect('./db/commits.db')

    c = conn.cursor()

    print('Creating repository, repo_commit, and commit_changes tables ...')

    c.execute('''CREATE TABLE if not exists repository(
                    id_repo integer primary key not null,
                    repo_name varchar(40) not null,
                    repo_language varchar(20) not null,
                    main_branch varchar(20) not null,
                    repo_creation varchar(30) not null,
                    repo_modification varchar(30) not null,
                    repo_size integer not null,
                    repo_stars integer not null,
                    repo_forks integer not null
                    )''')
    c.execute(''' CREATE TABLE IF NOT EXISTS repo_commit(
                    id_commit integer primary key not null,
                    repo_name varchar(40) not null,
                    commit_sha varchar(250) not null on conflict ignore,
                    commit_url varchar(400) not null,
                    commit_date varchar(30) not null,
                    author varchar(50) not null,
                    modified_file_new_path varchar(150) not null,
                    modified_file varchar(50) not null,
                    change_type varchar(10) not null,
                    commit_message text not null,
                    FOREIGN KEY(id_commit) REFERENCES repository(id_repo)
                    )''')
    print('Cleaning repository, repo_commit, and commit_changes tables ...')

    c.execute('DELETE FROM repository;')
    c.execute('DELETE FROM repo_commit;')

    print('Populating repository table...')

    csv_file = glob.glob('*.{}'.format('csv'))[0]
    print(csv_file)

    with open(csv_file, 'r') as fin:
        dr = csv.DictReader(fin)
        to_db = [(i['Repo_Name'], i['Language'], i['Default_Branch'], i['Created_At'], i['Modified_At'], i['Size'],
                  i['Stars'], i['Forks']) for i
                 in dr]

    for data in to_db:
        c.execute(
            'INSERT INTO repository (repo_name, repo_language, main_branch, repo_creation, repo_modification, repo_size, '
            'repo_stars, repo_forks) VALUES (?,?,?,?,?,?,?,?)', data)
        conn.commit()

    print('Starting mining...')

    conn.close()
