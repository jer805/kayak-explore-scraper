# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 10:52:09 2019

@author: Jeremy Simon
"""
import requests, smtplib
import pandas as pd
from bs4 import *
import urllib.request as ur
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Specify the beginning and end of the time frame of possible dates as YYYYMMDD
timeframe_begin = 20200701
timeframe_end = 20200730

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

    start = '&depart=' + str(start)
    end = '&return=' + str(end)
    
    url = "https://www.kayak.com/s/horizon/exploreapi/elasticbox?airport=" + airport + "&v=1" + \
                             start + end + \
                             "&stopsFilterActive=false&duration=&budget=&topRightLat=68.58212830775821" + \
                             "&topRightLon=180&bottomLeftLat=-6.168763628541718&bottomLeftLon=-180" + \
                             "&zoomLevel=2"
    response = requests.post(url).json()

    df = pd.DataFrame(columns=['City', 'Country', 'Price', 'Airline', 'Airport', 'Date', 'Link'])
    
    for i in range(len(response['destinations'])):
        destination = response['destinations'][i]
        row = list([destination['city']['name'], destination['country']['name'], 
                    destination['flightInfo']['price'], destination['airline'],
                    destination['airport']['shortName'], pd.to_datetime(destination['departd']).date(),
                    str('http://kayak.com'+destination['clickoutUrl'])])
        df.loc[i] = row
        
    return df

def scrape_wikipedia():
    """
    This function scrapes and parses several wikipedia pages to map flight 
    
    destination cities to their respective continents. It then cleans the 
    
    resulting data frame.
    
    Returns:
    df - a data frame containing all cities from the wiki data and the continents
    
    where they are located
    """
    urls = ['https://en.wikipedia.org/wiki/List_of_African_countries_by_area',
           'https://en.wikipedia.org/wiki/List_of_North_American_countries_by_GDP_(nominal)_per_capita',
           'https://en.wikipedia.org/wiki/List_of_South_American_countries_by_population',
           'https://en.wikipedia.org/wiki/List_of_European_countries_by_area',
           'https://en.wikipedia.org/wiki/List_of_Oceanian_countries_by_population',
           'https://en.wikipedia.org/wiki/List_of_countries_in_Asia-Pacific_by_GDP_(nominal)',
           'https://en.wikipedia.org/wiki/List_of_Middle_Eastern_countries_by_population']
    
    continents = ['Africa', 'North America', 'South America', 'Europe', 'Oceania', 'Asia', 'Asia']    
    
    all_continents = []
    countries = []
    
    df = pd.DataFrame(columns=['Country', 'Continent'])
    
    for i in range(len(urls)):
        html = ur.urlopen(urls[i]).read()
        soup = BeautifulSoup(html, 'html.parser') 
        table = soup.find_all('table')[0]  
        rows = table.find_all('tr')
        
        for row in rows:
            columns = row.find_all('td')
            if len(columns) > 0:
                countries.append(columns[1].get_text().strip())
                all_continents.append(continents[i])            
    
    countries = pd.Series(countries).replace(regex=True,
                         to_replace=[r'\d', r'\([^)]*\)', ''], value=r'')
    countries = countries.replace(regex=True, 
                            to_replace=[r'\[[^()]*\]', r'[\*]'], value=r'')

    dups = countries.duplicated()
    dups_i = list(dups[dups==True].index)
    countries = pd.Series(countries.unique())
    all_continents = pd.Series(all_continents).drop(dups_i)
    all_continents.index=range(0,len(all_continents))
    countries[203] = 'Israel'
    df['Country'] = pd.Series(countries)
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
    
    for airport in hi_airports:
        hawaii = hawaii.append(cities[cities['Airport'].str.match(airport)])
    
    japan = cities[cities['Country'].str.match('Japan')]
    jp_lowest_i = japan['Price'].idxmin()
    jp_lowest = japan.loc[jp_lowest_i]
    hi_lowest_i = hawaii['Price'].idxmin()
    hi_lowest = hawaii.loc[hi_lowest_i]
    
    lowest = cities.groupby(['Continent'])['Price'].idxmin()
    deals = cities.iloc[lowest,:]
    deals = deals.append(jp_lowest)
    deals = deals.append(hi_lowest)
    deals['Price'] = '$' + deals['Price'].astype(str)
    
    return deals

def send_email(results):
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
    message['Subject'] = 'Latest Kayak Scrape'
    message['From'] = sender
    message['To'] = receiver
    
    html = "<html><head></head><body><p>Hello!<br>Here are your latest Kayak" + \
    "scraping results:<br>"+results.to_html()+"</p></body></html>"
    
    part1 = MIMEText(html, 'html')
    message.attach(part1)
    
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login('fmcbean19', password)
    mail.sendmail(sender, receiver, message.as_string())
    mail.quit()
    
all_flights = scrape_kayak(timeframe_begin, timeframe_end)
all_continents = scrape_wikipedia()
flights_list = all_flights.merge(all_continents, how='left', on='Country')
results = summarize_results(flights_list)
send_email(results)
