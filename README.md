# Thesis' project name - Master’s Degree Project

Once Dockerfile has started, the script can filter the repositories’ commits. Using PyDriller the tool clones the repo and starts the repository mining. Once finished the mining, all commits are saved in a CSV file. All CSV files are filtered using keywords stored in a list.

Only the commits with the “.yml” file modified that contain a word in the previously cited list are saved in a Sqlite DB.

## Docker Execution

```bash
cd ~/ci-cd-analysis
docker-compose up --build
```

## Docker Stop

```bash
cd ~/ci-cd-analysis
docker-compose down -v
```

## About the Dataset

To begin the analysis, it is necessary to download a CSV file from [SEART | USI](https://seart-ghs.si.usi.ch/). Then it is necessary to convert the file to the correct format, to simplify which the authors have developed a [TOOL](https://github.com/vigimella/input-ci-cd-analysis). The latter can also be used to create a CSV file consisting of X random elements and to retrieve composition information, e.g., the percentage of composition by year.

## Contributing 

The authors would like to thank the [ Department of Biosciences and Territory](https://dipbioter.unimol.it/english/) within the University of Molise (UNIMOL, Italy) that support their researches.