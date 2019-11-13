# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 10:14:05 2019

@author: JDawg
1. find cheapest time of year for a flight to hawaii, africa, japan, or somewhere nice
2. cheapest ticket buying time for same
3. same, but for visiting family
4. cheapest place to visit on each continent at present point in time
"""

from time import sleep, strftime
from random import randint
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import smtplib
from email.mime.multipart import MIMEMultipart

#%%
driver_path = 'C:/Users/JDawg/Documents/python/gecko/geckodriver.exe'
driver = webdriver.Firefox(executable_path = driver_path)
##kayak = 'https://www.kayak.de/flights/BER-OKC/2020-05-15-flexible/2020-05-29-flexible'
#kayak = 'https://www.kayak.com/flights/LIS-SIN/2019-09-29-flexible/2019-10-15-flexible?sort=bestflight_a'
#driver.get(url=kayak)
##content = driver.page_source
##with open('kayak.html','w') as file:  # open file for testing results
##    file.write(content)
#xp_prices = '//a[@data-code ="price"]'
#prices = driver.find_elements_by_xpath(xp_prices)
#prices_list = [price.text.replace('$','') for price in prices if price.text != '']
#print(prices_list)
#sleep(2)
###%%
##response = requests.post("https://www.kayak.de/s/horizon/exploreapi/elasticbox?airport=LEJ&v=1&stopsFilterActive=false&duration=&budget=&topRightLat=44.144519521716546&topRightLon=150.56179375&bottomLeftLat=-13.675682035660545&bottomLeftLon=-89.55539375000001&zoomLevel=3").json()
###%%
##import json
##with open('data.json', 'w') as f:
##    json.dump(response, f)
#    #%%
##cheap_results = '//a[@data-code = "price"]'
##driver.find_element_by_xpath(cheap_results).click()
##%%
#xp_results_table = '//*[@class = "resultWrapper"]'
#flight_containers = driver.find_elements_by_xpath(xp_results_table)
#flights_list = [flight.text for flight in flight_containers]
##%%
#flights_list[0:3]
#%%
def load_more():
    try:
        more_results = '//a[@class = "moreButton"]'
        driver.find_element_by_xpath(more_results).click()
        print('sleeping')
        sleep(randint(45,60))
    except:
        pass
#%%
def page_scrape():
    """This function takes care of the scraping part"""
    
    xp_sections = '//*[@class="section duration"]'
    sections = driver.find_elements_by_xpath(xp_sections)

    # i think this is a list of all tags with the seciton duration class.
    # i guess it returns a list of elements or objects or something
    sections_list = [value.text for value in sections]
    # this must be the tet of those elements, and not the objects
    section_a_list = sections_list[::2] # This is to separate the two flights
    section_b_list = sections_list[1::2] # This is to separate the two flights
    # each one must be a single flight, which is a row
    
    # if you run into a reCaptcha, you might want to do something about it
    # you will know there's a problem if the lists above are empty
    # this if statement lets you exit the bot or do something else
    # you can add a sleep here, to let you solve the captcha and continue scraping
    # i'm using a SystemExit because i want to test everything from the start
    if section_a_list == []:
        raise SystemExit
    
    # I'll use the letter A for the outbound flight and B for the inbound
    a_duration = []
    a_section_names = []
    for n in section_a_list:
        # Separate the time from the cities
        a_section_names.append(''.join(n.split()[2:5]))
        a_duration.append(''.join(n.split()[0:2]))
    b_duration = []
    b_section_names = []
    for n in section_b_list:
        # Separate the time from the cities
        b_section_names.append(''.join(n.split()[2:5]))
        b_duration.append(''.join(n.split()[0:2]))

    xp_dates = '//div[@class="section date"]'
    dates = driver.find_elements_by_xpath(xp_dates)
    dates_list = [value.text for value in dates]
    a_date_list = dates_list[::2]
    b_date_list = dates_list[1::2]
    # Separating the weekday from the day
    a_day = [value.split()[0] for value in a_date_list]
    a_weekday = [value.split()[1] for value in a_date_list]
    b_day = [value.split()[0] for value in b_date_list]
    b_weekday = [value.split()[1] for value in b_date_list]
    
    # getting the prices
#    xp_prices = '//a[@class="booking-link"]/span[@class="price option-text"]'
#    prices = driver.find_elements_by_xpath(xp_prices)
#    print(prices)
#    prices_list = [price.text.replace('€','') for price in prices if price.text != '']
#    prices_list = [price.text.replace('$','') for price in prices if price.text != '']
#    prices_list = list(map(int, prices_list))
    xp_prices = '//span[@class="price option-text"]'
    prices = driver.find_elements_by_xpath(xp_prices)
    prices_list = [price.text.replace('$','') for price in prices if price.text != '']
    prices_list = list(map(int, prices_list))

    # the stops are a big list with one leg on the even index and second leg on odd index
    xp_stops = '//div[@class="section stops"]/div[1]'
    stops = driver.find_elements_by_xpath(xp_stops)
    stops_list = [stop.text[0].replace('n','0') for stop in stops]
    a_stop_list = stops_list[::2]
    b_stop_list = stops_list[1::2]

    xp_stops_cities = '//div[@class="section stops"]/div[2]'
    stops_cities = driver.find_elements_by_xpath(xp_stops_cities)
    stops_cities_list = [stop.text for stop in stops_cities]
    a_stop_name_list = stops_cities_list[::2]
    b_stop_name_list = stops_cities_list[1::2]
    
    # this part gets me the airline company and the departure and arrival times, for both legs
    xp_schedule = '//div[@class="section times"]'
    schedules = driver.find_elements_by_xpath(xp_schedule)
    hours_list = []
    carrier_list = []
    for schedule in schedules:
        hours_list.append(schedule.text.split('\n')[0])
        carrier_list.append(schedule.text.split('\n')[1])
    # split the hours and carriers, between a and b legs
    a_hours = hours_list[::2]
    a_carrier = carrier_list[::2]
    b_hours = hours_list[1::2]
    b_carrier = carrier_list[1::2]

    
    cols = (['Out Day', 'Out Time', 'Out Weekday', 'Out Airline', 'Out Cities', 'Out Duration', 'Out Stops', 'Out Stop Cities',
            'Return Day', 'Return Time', 'Return Weekday', 'Return Airline', 'Return Cities', 'Return Duration', 'Return Stops', 'Return Stop Cities',
            'Price'])

    flights_df = pd.DataFrame({'Out Day': a_day,
                               'Out Weekday': a_weekday,
                               'Out Duration': a_duration,
                               'Out Cities': a_section_names,
                               'Return Day': b_day,
                               'Return Weekday': b_weekday,
                               'Return Duration': b_duration,
                               'Return Cities': b_section_names,
                               'Out Stops': a_stop_list,
                               'Out Stop Cities': a_stop_name_list,
                               'Return Stops': b_stop_list,
                               'Return Stop Cities': b_stop_name_list,
                               'Out Time': a_hours,
                               'Out Airline': a_carrier,
                               'Return Time': b_hours,
                               'Return Airline': b_carrier,                           
                               'Price': prices_list})[cols]
    
    flights_df['timestamp'] = strftime("%Y%m%d-%H%M") # so we can know when it was scraped
    return flights_df
     
#%%
def start_kayak(city_from, city_to, date_start, date_end):
    """City codes - it's the IATA codes!
    Date format -  YYYY-MM-DD"""
    
    kayak = ('https://www.kayak.com/flights/' + city_from + '-' + city_to +
             '/' + date_start + '-flexible/' + date_end + '-flexible?sort=bestflight_a')
    driver.get(kayak)
    sleep(randint(8,10))
    
    # sometimes a popup shows up, so we can use a try statement to check it and close
    try:
        xp_popup_close = '//button[contains(@id,"dialog-close") and contains(@class,"Button-No-Standard-Style close ")]'
        driver.find_elements_by_xpath(xp_popup_close)[5].click()
    except Exception as e:
        pass
    sleep(randint(60,95))
    print('loading more.....')
    
#     load_more()
    
    print('starting first scrape.....')
    df_flights_best = page_scrape()
    df_flights_best['sort'] = 'best'
    #sleep(randint(60,80))
    
    # Let's also get the lowest prices from the matrix on top
    matrix = driver.find_elements_by_xpath('//*[contains(@id,"FlexMatrixCell")]')
    matrix_prices = [price.text.replace('$','') for price in matrix]
    matrix_prices = filter(None, matrix_prices)
    print(matrix_prices)
    matrix_prices = list(map(int, matrix_prices))
    matrix_min = min(matrix_prices)
    matrix_avg = sum(matrix_prices)/len(matrix_prices)
  
    return matrix_min, kayak
#%%

#city_from = input('From which city? ')
#city_to = input('Where to? ')
#date_start = input('Search around which departure date? Please use YYYY-MM-DD format only ')
#date_end = input('Return when? Please use YYYY-MM-DD format only ')
def run_scraper():
    city_from = 'BER'
    city_to = 'ATL'
    date_start = '2020-02-06'
    date_end = '2020-02-14'
        
    cheapest, url = start_kayak(city_from, city_to, date_start, date_end)
    return cheapest, url
    
