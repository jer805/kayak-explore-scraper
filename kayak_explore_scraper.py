# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 10:52:09 2019

@author: Jeremy Simon
"""

import requests, smtplib, os, datetime
import pandas as pd
from bs4 import *
import urllib.request as ur
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from matplotlib import pyplot as plt

# Specify the beginning and end of the time frame of possible dates as YYYYMMDD
timeframe_begin = 20200601
timeframe_end = 20200830

def scrape_kayak(start='', end='', airport = 'BER'):
    """
    This function scrapes flight information from the kayak explore page.
    
    Parameters:
    start, end, airport - integer representing earliest possible departure date
    in YYYYMMDD format, integer representing latest return date, string with 
    three letter code for starting airport. When both are start and end are 
    left blank, results are returned from present date to one year in the 
    future.
    
    Returns:
    df - a data frame containing all destination cities and corresponding 
    flight information returned by the scrape
    """

    # Format the beginning and end dates to insert them into the URL
    start = '&depart=' + str(start)
    end = '&return=' + str(end)
    
    url = "https://www.kayak.com/s/horizon/exploreapi/elasticbox?airport=" + airport + "&v=1" + start + end + \
    "&stopsFilterActive=false&duration=&budget=&topRightLat=68.58212830775821&topRightLon=180&bottomLeftLat=-6.168763628541718&bottomLeftLon=-180&zoomLevel=2"
    response = requests.post(url).json()

    df = pd.DataFrame(columns=['City', 'Country', 'Price', 'Airline', 'Airport', 'Date', 'Link'])
    
    for i in range(len(response['destinations'])):
        destination = response['destinations'][i]
        row = list([destination['city']['name'], destination['country']['name'], 
                    destination['flightInfo']['price'], destination['airline'],
                    destination['airport']['shortName'], pd.to_datetime(destination['departd']).date(),
                    str('http://kayak.com'+destination['clickoutUrl'])])
        df.loc[i] = row
        
    city_mins = df.groupby(['City']).idxmin().astype(int)
    df = df.loc[city_mins['Price'].to_list()]
    # There is a glitch where some flights are returned with unrealistically
    # prices, so we'll remove those entries.
    df = df.where(df['Price']!=999999).dropna()
        
    return df

def scrape_wikipedia():
    """
    This function scrapes and parses several wikipedia pages to map flight 
    destination cities to their respective continents. It then cleans the 
    resulting data frame.
    
    Returns:
    df - a data frame containing all cities from the wiki data and the
    continents where they are located
    """

    urls = ['https://en.wikipedia.org/wiki/List_of_African_countries_by_area',
           'https://en.wikipedia.org/wiki/List_of_North_American_countries_by_GDP_(nominal)_per_capita',
           'https://en.wikipedia.org/wiki/List_of_South_American_countries_by_population',
           'https://en.wikipedia.org/wiki/List_of_European_countries_by_area',
           'https://en.wikipedia.org/wiki/List_of_Oceanian_countries_by_population',
           'https://en.wikipedia.org/wiki/List_of_countries_in_Asia-Pacific_by_GDP_(nominal)',
           'https://en.wikipedia.org/wiki/List_of_Middle_Eastern_countries_by_population']
    
    continents = ['Africa', 'North America', 'South America', 'Europe', 
                  'Oceania', 'Asia', 'Asia']    
    all_continents, countries = [], []
    df = pd.DataFrame(columns=['Country', 'Continent'])
    
    for i in range(len(urls)):
        html = ur.urlopen(urls[i]).read()
        soup = BeautifulSoup(html, 'html.parser') 
        table = soup.find_all('table')[0]  
        rows = table.find_all('tr')
        
        for row in rows:
            columns = row.find_all('td')
            if len(columns) > 0:
                country = columns[1].get_text().strip()
                if country not in countries:
                    countries.append(country)
                    all_continents.append(continents[i])            
    
    # Remove all parentheses
    countries = pd.Series(countries).replace(regex=True,
                         to_replace=[r'\d', r'\([^)]*\)', ''], value=r'')
    # Remove brackets and asterisks
    countries = countries.replace(regex=True,
                                  to_replace=[r'\[[^()]*\]', r'[\*]'],
                                  value=r'')
    df['Country'] = countries
    df['Continent'] = pd.Series(all_continents)
    
    return df

def summarize_results(cities):
    """
    This function finds the lowest priced flight to each continent, as well as 
    to specific regions we're interested in, in thsi case Japan and Hawaii.
    
    Parameters:
    cities - a data frame with scraped kayak flight information with a 
    continent mapped to each city.
    
    Returns:
    deals - a data frame containing flight information for the cheapest flight
    to each destination of interest.
    """
    
    hi_airports = ['HNL', 'MKK', 'OGG', 'KOA', 'ITO']
    hawaii = cities[cities['Airport'].str.match('LIH')]
    
    # Create a dataframe with all of the Hawaii flights
    for airport in hi_airports:
        hawaii = hawaii.append(cities[cities['Airport'].str.match(airport)])
    
    # Doing the same for Japan is a bit easier since we can just grep the
    # country ccolumn
    japan = cities[cities['Country'].str.match('Japan')]
    jp_lowest = japan.loc[japan['Price'].idxmin()]
    jp_lowest[7] = 'Japan*' # Differentiate the Japan flights from Asia flights
    hi_lowest = hawaii.loc[hawaii['Price'].idxmin()]
    hi_lowest[7] = 'Hawaii*'
    lowest = cities.groupby(['Continent'])['Price'].idxmin()
    deals = cities.iloc[lowest,:]
    deals = deals.append(jp_lowest)
    deals = deals.append(hi_lowest)
    deals = deals.set_index('City')
    
    return deals

def send_email(flights):
    """
    This function sends an email with the summarized flight data as a data 
    frame in html to the specified address.    
    cities - a data frame with scraped kayak flight information with a 
    continent mapped to each city.
    
    Parameters:
    results - a dataframe of the best deals on flights and the corresponding 
    details returned by our scrape.
    """
    
    password = input('Type your password:')
    message = MIMEMultipart('alternative')
    message.add_header('Content-Type','html')
    sender = 'youremail@domain.com'
    receiver = 'theiremail@domain.com'
    message['Subject'] = "Here is your latest Kayak scrape!"
    message['From'] = sender
    message['To'] = receiver
    html = "<html><head></head><body><p>" + msgs + \
    flights.to_html() + ". </p></body></html>"
    
    part1 = MIMEText(html, 'html')
    message.attach(part1)
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login('your_username', password)
    mail.sendmail(sender, receiver.split(','), message.as_string())
    mail.quit()

def check_df(results, start, end):
    """
    This funciton compares the results of the current scrape with previous
    results to determine if an email update should be sent.
    
    Parameters: 
    results, start, end - dataframe with summarized scrape results, integer 
    representing earliest possible departure date in YYYYMMDD format, integer 
    representing latest return date
    
    Returns:
    msgs, email - list of strings indicating continents for which good deals are 
    available, boolean indicating whether an email should be sent
    """
    
    filename = str(start) + '_to_' + str(end) + '_kayak_scrape.csv'
    if os.path.isfile(filename):
        df = pd.read_csv(filename)
    else:
        df = pd.DataFrame(columns=['Date'])
        
    current_scrape = results['Price']
    
    # Append the current scrape as a row if it isn't a duplicate
    if df.append(current_scrape).drop([
            'Date'], axis=1).duplicated().any() == False:
        df = df.append(current_scrape)
        now = datetime.datetime.now()
        df.iloc[-1,0] = now
        df.index = range(len(df))

    df.to_csv(filename, index=False)
    msgs = ''
    # Bool indicating if an email will be sent. Will be set to true if good 
    # deals are detected
    email = False 
    # Percent of average flight price for one destination, under which an email
    # will be generated
    email_threshold = 0.85

    for column in range(1,len(df.columns)):
        col_mean = df.iloc[:,column].mean()
        if col_mean * email_threshold > df.iloc[-1,column]:
            name = df.columns[column]
            msg = 'Flights to ' + name + ' right now are abnormally cheap.<br>'
            msgs += msg
            email = True
            
    return msgs, email

def save_scrape(start, end, flights):
    """
    This function compares the results of the current scrape with previous
    results to determine if an email update should be sent.
    
    Parameters: 
    results, start, end - dataframe with summarized scrape results, integer 
    representing earliest possible departure date in YYYYMMDD format, integer 
    representing latest return date
    
    Returns:
    msgs, email - list of strings indicating continents for which good deals are 
    available, boolean indicating whether an email should be sent
    """
    filename = str(start) + '_to_' + str(end) + '_all_flights.csv'
    now = datetime.datetime.now()
    current_prices = flights.set_index('City')['Price']
    current_prices.name = now
    
    if os.path.isfile(filename):
        df = pd.read_csv(filename, index_col=0)
        df = df.merge(current_prices, how='outer', left_index=True, 
                      right_index=True)
    else:
        df = pd.DataFrame(current_prices)
        df['Continent'] = flights_list.set_index('City')['Continent']
        
    df.to_csv(filename)
    
    return df.drop('Continent', axis=1).dropna()

all_flights = scrape_kayak(timeframe_begin, timeframe_end)

# If we've already run the scraper, there's no need to scrape wikipedia a
# second time.
if not os.path.isfile('continents.csv'):
    all_continents = scrape_wikipedia()
else:
    all_continents = pd.read_csv('continents.csv', index_col=0)
    
flights_list = all_flights.merge(all_continents, how='left', on='Country')
historical = save_scrape(timeframe_begin, timeframe_end, flights_list)
results = summarize_results(flights_list)
msgs, email = check_df(results, timeframe_begin, timeframe_end)

if email:
    send_email(results)

continents = ['Africa', 'North America', 'South America', 
              'Europe', 'Oceania', 'Asia']
plot_num = 1

for continent in continents:
    plt.subplot(3,2,plot_num)
    df = flights_list.where(flights_list['Continent']==continent).dropna()
    plt.hist(df['Price'], bins=50, alpha=0.5, range=(0,3000))
    title = plt.gca().set_title(continent)
    plot_num += 1
    
plt.show()

dest_prices, labels = [], []

# This lists cities from Hawaii and Japan to which flights are present in our
# data frame.
bp_cities = ['Honolulu', 'Kailua-Kona', 'Kahului', 'Lihue', 'Osaka', 'Nagoya', 
          'Tokyo', 'Sapporo', 'Okinawa']

for city in bp_cities:
        df = historical[historical.index.str.match(city)].T
        if df.shape[1] > 0:
            df = pd.Series(df[city]).tolist()
            dest_prices.append(df)
            labels.append(city)
        
fig, ax = plt.subplots()
ax.boxplot(dest_prices, labels=labels, whis=2)
plt.ylabel('Price in USD')
plt.show()




