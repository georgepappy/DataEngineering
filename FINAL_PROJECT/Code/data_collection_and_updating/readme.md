The file CRON_jobs.txt shows the contents of the local crontab file which runs three scheduled CRON jobs on the local Macintosh computer responsible for data collection and updates:

1. <u>CRON job #1</u>: Executes "delete_db.sh" to delete the local version of the current SQLite database ("covid.db") once every 3 days; scheduled to occur one minute before the next scheduled CRON job #2.
2. <u>CRON job #2</u>: Runs "get_covid_data.py" once every hour; if lcoal SQLite database "covid.db" already exists, the run checks for the latest date represented in the database and adds only more recent data from the Johns Hopkins COVID-19 GitHub repository (if any is found); if "covid.db" does not exist (i.e., was just deleted by CRON job #1), the run will rebuild the entire database by pulling all data from the Johns Hopkins GitHub repository (starting with date 2022-04-12). 
3. <u>CRON job #3</u>: Runs "update_git.sh" once every hour to push any new version of "covid.db" to the GitHub repository feeding the deployed Heroku/Flask dashboard application; scheduled to occur 56 minutes after CRON job #2 to allow more than enough time for "get_covid_data.py" to completely rebuild the database when it gets deleted once every three days (by CRON job #1).



NOTE: "get_covid_data.py" (run by CRON job #2) needs the file "admin2_list.csv" (list of counties to include in the dataset). Since the file is so small, it has been included in this repository.