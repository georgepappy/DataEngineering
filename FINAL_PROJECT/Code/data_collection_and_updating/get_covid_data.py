import pandas as pd
import numpy as np
import sqlite3
import requests
from bs4 import BeautifulSoup, SoupStrainer
from datetime import date, datetime, timedelta

path = '/Users/georgepappy/Documents/Metis/online_flex/Module7_DataEngineering/project_sandbox/tracker_1/'


##################
# The method/code below using BeautifulSoup to access
# all .csv files in a GitHub Repository is adapted from:
#
# https://stackoverflow.com/questions/69806371/combining-all-csv-files-from-github-repository-link-and-make-it-a-one-csv-file
##################


##################
# 1) Get State-wide Covid Data
##################

con = sqlite3.connect(path + 'covid.db')

# Get data from GitHub
html = requests.get('https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_daily_reports_us')

# Check to see if state_data table exists and get most recent date of update
query = con.execute(
          """
              SELECT name FROM sqlite_master WHERE type="table" AND name="state_data";
          
          """).fetchone() 

if query != None:
    query = con.execute(
              """
                  SELECT MAX(Date) FROM state_data;
              
              """).fetchone()
    last_update = datetime.strptime(query[0].split()[0], "%Y-%m-%d").date()
else:
    # No table yet - set last_update variable way back in the past
    last_update = date(1980, 1, 1)
    
    # Also, create the table
    query = con.execute(
          """
              CREATE TABLE state_data( 
                    Id INTEGER PRIMARY KEY, 
                    Province_State TEXT,
                    Confirmed INTEGER,
                    Deaths INTEGER,
                    Incident_Rate REAL,
                    Case_Fatality_Ratio REAL,
                    Date DATE
              );
          """)

    
# Fetch data from Johns Hopkins GitHub repository
for link in BeautifulSoup(html.text, parse_only=SoupStrainer('a'), features="lxml"):
    if hasattr(link, 'href') and link['href'].endswith('.csv'):
        
        # Only add this file if new (i.e. not in database already)
        if datetime.strptime(link["title"].replace(".csv", ""), "%m-%d-%Y").date() > last_update:     
            url = 'https://github.com'+link['href'].replace('/blob/', '/raw/')
            df = pd.read_csv(url, sep=',', lineterminator='\n')
            
            # Drop rows we're not interested in (e.g. The Cruise Ships with outbreaks, Minor Outlying US Territories)
            df = df[~df['Province_State'].isin(['Diamond Princess', 'Grand Princess', 'American Samoa', 'Recovered', 
                                                'Virgin Islands', 'Guam', 'Northern Mariana Islands', 'Puerto Rico'])]
            
            # Account for slight modifications to column nomenclature that occurred over time
            if 'Mortality_Rate' in df.columns:
                df.rename({'Mortality_Rate' : 'Case_Fatality_Ratio', 'People_Tested' : 'Total_Test_Results'}, axis=1, inplace=True)
    
            # Retain only columns of interest
            df = df.iloc[:, 0:14].drop(columns=['Country_Region', 'Last_Update', 'Lat', 'Long_', 'Recovered', 'Active', 
                                                'FIPS', 'Total_Test_Results', 'People_Hospitalized'])
            
            # Set date column to match filename of this .csv file
            df['Date'] = datetime.strptime(link["title"].replace(".csv", ""), "%m-%d-%Y").date()
            
            # Add NULL Id (Primary Key: Will autoincrement as unique integer on SQL insert)
            cols = df.columns
            df['Id'] = np.nan
            df = df[cols.insert(0, 'Id')]
            
            # insert data into database
            df.to_sql('state_data', con, if_exists='append', index=False)

##################


##################
# 2) Get County-wide Covid Data
##################

# Read in list of counties to include
counties = pd.read_csv(path +'admin2_list.csv')
counties['new_key'] = counties['Admin2'] + '_' + counties['Province_State']

# Get data from GitHub
html = requests.get('https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_daily_reports')

# Check to see if county_data table exists and get most recent date of update
query = con.execute(
          """
              SELECT name FROM sqlite_master WHERE type="table" AND name="county_data";
          
          """).fetchone() 

if query != None:
    query = con.execute(
              """
                  SELECT MAX(Date) FROM county_data;
              
              """).fetchone()
    last_update = datetime.strptime(query[0].split()[0], "%Y-%m-%d").date()
else:
    # No table yet - set last_update variable way back in the past
    last_update = date(1980, 1, 1)
    
    # Also, create the table
    query = con.execute(
          """
              CREATE TABLE county_data( 
                    Id INTEGER PRIMARY KEY,
                    Admin2 TEXT,
                    Province_State TEXT,
                    Confirmed INTEGER,
                    Deaths INTEGER,
                    Incident_Rate REAL,
                    Case_Fatality_Ratio REAL,
                    Date DATE
              );              
          """)

    
for link in BeautifulSoup(html.text, parse_only=SoupStrainer('a'), features="lxml"):
    if hasattr(link, 'href') and link['href'].endswith('.csv'):
        
        # Only add this file if new (i.e. not in database already)
        if datetime.strptime(link["title"].replace(".csv", ""), "%m-%d-%Y").date() > last_update:        
            url = 'https://github.com'+link['href'].replace('/blob/', '/raw/')
            df = pd.read_csv(url, sep=',', lineterminator='\n')
            
            # Only process this df if it contains the 'Combined_Key' and either 'Incidence_Rate' or 'Incident_Rate' columns; 
            #   Otherwise, it's from very early in the pandemic (unfortunately, the schema evolved over time)
            if ('Combined_Key' in df.columns) and (('Incidence_Rate' in df.columns) or ('Incident_Rate' in df.columns)):
                
                # If column is named 'Incidence_Rate', rename 'Incident_Rate'
                if 'Incidence_Rate' in df.columns:
                    df.rename({'Incidence_Rate' : 'Incident_Rate'}, axis=1, inplace=True)
                    
                # Drop last column (for Case Fatality Ratio - has inconsistent naming; will re-compute this column below)
                df = df.iloc[:, 0:13]
                
                # Drop additional unwanted columns
                df = df.drop(columns=['Lat', 'Long_', 'Last_Update', 'FIPS', 'Country_Region', 'Recovered', 'Active', 'Combined_Key'])
                
                # Retain only rows for counties found in the counties list
                df['new_key'] = df['Admin2'] + '_' + df['Province_State']
                df = df.loc[df['new_key'].isin(counties['new_key'])].reset_index(drop=True).drop(columns='new_key')
            
                # Compute 'Case_Fatality_Ratio' 
                #  (schema/naming evolved over time, so we drop it above and compute from scratch here)
                df['Case_Fatality_Ratio'] = 100 * df['Deaths'] / df['Confirmed']
                
                # Set date column to match filename of this .csv file
                df['Date'] = datetime.strptime(link["title"].replace(".csv", ""), "%m-%d-%Y").date()
                
                # Add NULL Id (Primary Key: Will autoincrement as unique integer on insert)
                cols = df.columns
                df['Id'] = np.nan
                df = df[cols.insert(0, 'Id')]
            
                # drop data into database
                df.to_sql('county_data', con, if_exists='append', index=False)


con.close()