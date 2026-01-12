from operator import itemgetter
from bs4 import BeautifulSoup
from random import randint, uniform
from csv import writer
import requests
import time
import sys


def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input('Press key to exit.')
    sys.exit(-1)

sys.excepthook = show_exception_and_exit

# List of user agents last updated 
agents = ['Mozilla/5.0 (Windows NT 11.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6073.156 Safari/537.36'
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/616.9 (KHTML, like Gecko) Version/17.1 Safari/616.9'
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6043.119 Safari/537.36 Edg/120.0.2673.144'
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0_9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6110.175 Safari/537.36'
          'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6471.173 Safari/537.36'
         ]

# To not have to recalculate user agent randomizer every time I change user agents
agents_rand = len(agents)-1

# Scrape individual guide information
def guide_scrape(guide_url):

    # Randomize user agent
    headers = {'User-Agent': agents[randint(0, agents_rand)]}

    # Load guide's HTML information
    r_guide = requests.get(guide_url, headers=headers)
    soup_guide = BeautifulSoup(r_guide.content, 'html.parser')

    # Parse and collect information
    title = soup_guide.find(class_='workshopItemTitle').get_text()

    # Parse hero name
    workshop_tags = soup_guide.find_all(class_='workshopTags')
    hero_name = [tag.text.strip().split('\xa0')[1] for tag in workshop_tags 
                           if 'Heroes' in tag.text or 'Tag' in tag.text][0]

    # Get ratings data
    try: # Exceptions from guides with not enough ratings
        rating = int(soup_guide.find(class_='fileRatingDetails').img['src'].split('/')[-1][0])
    except:
        rating = None
    try:
        num_ratings = int(soup_guide.find(class_='numRatings').get_text().split()[0].replace(',', ''))
    except:
        num_ratings = None

    # Get major stats
    stats = soup_guide.find(class_='stats_table').findAll('td')
    
    visitors = int(stats[0].get_text().replace(',', ''))
    subscribers = int(stats[2].get_text().replace(',', ''))
    favorites = int(stats[4].get_text().replace(',', ''))

    # Comments may not exist
    if soup_guide.find(class_='commentthread_count_label') is not None:
        commentNum = int(soup_guide.find(class_='commentthread_count_label').get_text().strip().split()[0].replace(',', ''))
    else:
        commentNum = 0

    return [guide_url, title, hero_name, rating, num_ratings, visitors, subscribers, favorites, commentNum]

def guide_listing_scrape(id):

    # Setting up scraping target data
    
    # 0825771 - Torte de Lini
    # ImmortalFaith
    if id == '1':
        scrape_target = '0825771'
    elif id == '2':
        scrape_target = 'ImmortalFaith'
    else:    
        scrape_target = str(id)
    
    if scrape_target == '0825771':
        scrape_name = 'TorteDeLini'
    else:    
        scrape_name = scrape_target

    print(f'Scraping guides for {scrape_name}')

    # Instantiate list for data collection
    all_guide_data = []
    
    # Iterate search through pages
    for num in range(1, 200):
        # Pagination URL
        search_url = f'http://steamcommunity.com/id/{scrape_target}/myworkshopfiles/?section=guides&appid=570&p={str(num)}'
    
        # Information on page number being scraped
        print('* * * *')
        print(f'Scraping Page {num}: {search_url}')
        print('* * * *')
    
        # Randomize user agent
        headers = {'User-Agent': agents[randint(0, agents_rand)]}
    
        # Read pagination page's HTML data
        r_search = requests.get(search_url, headers=headers)
        soup_search = BeautifulSoup(r_search.content, 'html.parser')
    
        # If there are no more entries, break out of the loop
        if soup_search.find(id='no_items') is not None:
            break
    
        # Otherwise get listings
        listings = soup_search.find_all(class_='workshopItemCollection')
        
        time.sleep(uniform(1, 3))
        
        # Iterate through guide items
        for listing in listings:
            
            # Get guide URLs and title
            guide_url = listing['href']
            guide_title = listing.find(class_='workshopItemTitle').get_text().strip()

            # Specific exceptions
            if guide_url in ['https://steamcommunity.com/sharedfiles/filedetails/?id=2958853356']:
                print(f"Skipping {guide_url}")
                continue
    
            # Scrape guide
            print(f'Scraping Guide {guide_url}: {guide_title}')
        
            time.sleep(uniform(1, 10))
    
            # Adding attempt code to hack error problem
            # Sometimes guide scrape would fail randomly so rerun attempts help solve this
            attempt = 1
            while attempt <= 20:
                try:
                    all_guide_data.append(guide_scrape(guide_url))
                    break
                except Exception as e:
                    print(f'Attempt {attempt} failed.')
                    print(e)
                    time.sleep(uniform(30, 150))
                    attempt += 1
            else:
                raise
    
    # Sort guide data by subscribers (element 5)
    all_guide_data = sorted(all_guide_data, key=itemgetter(5), reverse=True)
    
    # Get totals
    totals = ['Total', len(all_guide_data), ''] + [sum(filter(None, metric)) for metric in list(zip(*all_guide_data))[3:]]
    
    # Get averages
    averages = ['Average', len(all_guide_data), ''] + [sum(filter(None, metric))/\
                                                   float(sum(count != None for count in metric)) for metric in list(zip(*all_guide_data))[3:]]
    
    # Add to guide data
    all_guide_data.append(totals)
    all_guide_data.append(averages)
    
    # Set file name
    file_name = 'guideData-' + scrape_name + '-' + time.strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
    print(f'Output to {file_name}')    
    
    # File setup
    with open(file_name, 'w', encoding='utf-8', newline='') as file:
        f = writer(file)
    
        # Write reference row
        f.writerow(['URL', 'Guide Name', 'Hero Name', 'Average Rating', 'Number of Ratings', 'Unique Visitors',
                    'Current Subscribers', 'Current Favorites', 'Number of Comments'])
    
        # Add data
        f.writerows(all_guide_data)

def get_number_input():
    
    print('Enter 1 for Torte de Lini.')
    print('Enter 2 for ImmortalFaith.')
    print('Otherwise enter target user.')
    user_input = input('Please enter a value: ')

    return str(user_input)

# Call the function and store the result
target_id = get_number_input()

# Initialize time tracking
start_time = time.time()

guide_listing_scrape(target_id)

# Print time to finish and exit
print(f'{round((time.time() - start_time), 2)} seconds to finish')
input('Press key to exit.')