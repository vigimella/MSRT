# MSRT - (Mining Software Repositories Tool) | Master’s Degree Project

Once Dockerfile has started, the script can filter the repositories’ commits. Using PyDriller the tool clones the repo and starts the repository mining. Once finished the mining, all commits are saved in a CSV file. All CSV files are filtered using keywords stored in a list.

Only the commits with the “.yml” file modified that contain a word in the previously cited list are saved in a Sqlite DB.

## Input format and Dataset

To proceed with the MSR it is necessary to download a CSV file from [SEART | USI](https://seart-ghs.si.usi.ch/). After the latter, you have to convert the file to the correct format:
Repo_Name, Language, Default_Branch, Created_At, Modified_At, Size, Stars, and Forks.

## Contributing 

The authors would like to thank the [ Department of Biosciences and Territory](https://dipbioter.unimol.it/english/) within the University of Molise (UNIMOL, Italy) that support their researches.