from operator import itemgetter
from bs4 import BeautifulSoup
from random import randint
from csv import writer
import requests
import time
import sys


def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)

sys.excepthook = show_exception_and_exit


# Scrape guide information
def guideScrape(guideURL):

    # List of user agents
    agents = ['Mozilla/5.0 (Windows NT 10.0; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586', 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36', 'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A']

    # Randomize user agent
    headers = {'User-Agent': agents[randint(0, 5)]}

    # Load information
    rGuide = requests.get(guideURL, headers=headers)
    soupGuide = BeautifulSoup(rGuide.content, 'html.parser')

    # Parse and collect information
    title = soupGuide.find(class_='workshopItemTitle').get_text()
    try: # Exceptions from guides with not enough ratings
        rating = int(soupGuide.find(class_='fileRatingDetails').img['src'].split('/')[-1][0])
    except:
        rating = None
    try:
        numRatings = int(soupGuide.find(class_='numRatings').get_text().split()[0].replace(',', ''))
    except:
        numRatings = None

    stats = soupGuide.find(class_='stats_table').findAll('td')
    visitors = int(stats[0].get_text().replace(',', ''))
    subscribers = int(stats[2].get_text().replace(',', ''))
    favorites = int(stats[4].get_text().replace(',', ''))

    # Comments may not exist
    if soupGuide.find(class_='commentthread_count') is not None:
        commentNum = int(soupGuide.find(class_='commentthread_count').get_text().strip().split()[0].replace(',', ''))
    else:
        commentNum = 0

    return [guideURL, title, rating, numRatings, visitors, subscribers, favorites, commentNum]


# Initialize time tracking
start_time = time.time()

# Instantiate list for data collection
allGuideData = []

# Iterate search through pages
for num in range(1, 100):

    # Build URL
    searchURL = 'http://steamcommunity.com/id/0825771/myworkshopfiles/?section=guides&appid=570&p=' + str(num)

    # Information on page being scraped
    print(f'Scraping Page {num}:')

    # List of user agents
    agents = ['Mozilla/5.0 (Windows NT 10.0; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586', 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36', 'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A']

    # Randomize user agent
    headers = {'User-Agent': agents[randint(0, 5)]}

    # Read URL
    rSearch = requests.get(searchURL, headers=headers)
    soupSearch = BeautifulSoup(rSearch.content, 'html.parser')

    # If there are no more entries, break out of the loop
    if soupSearch.find(id='no_items') is not None:
        break

    # Otherwise get listings
    listings = soupSearch.find_all(class_='workshopItemCollection')

    # Iterate through guide items
    for listing in listings:

        # Get guide URL and title
        guideURL = listing['href']
        guideTitle = listing.find(class_='workshopItemTitle').get_text().strip()

        # Scrape guide
        print('Scraping Guide %s: %s' % (guideURL, guideTitle))

        # Adding attempt code to hack error problem
        attempt = 1
        while attempt <= 5:
            try:
                allGuideData.append(guideScrape(guideURL))
                break
            except Exception as e:
                print(f"Attempt {attempt} failed.")
                print(e)
                attempt += 1
        else:
            raise

# Sort guide data by subscribers (element 5)
allGuideData = sorted(allGuideData, key=itemgetter(5), reverse=True)

# Get totals
totals = ['Total', len(allGuideData)] + [sum(filter(None, topic)) for topic in list(zip(*allGuideData))[2:]]

# Get averages
averages = ['Average', len(allGuideData)] + [sum(filter(None, topic))/float(sum(count != None for count in topic)) for topic in list(zip(*allGuideData))[2:]]

# Add to guide data
allGuideData.append(totals)
allGuideData.append(averages)

# Set file name
fileName = 'guideData-' + time.strftime('%Y-%m-%d_%H-%M-%S') + '.csv'


# File setup
with open(fileName, "w") as file:
    f = writer(file)

    # Write reference row
    f.writerow(["URL", "Guide Name", "Average Rating", "Number of Ratings", "Unique Visitors", "Current Subscribers", "Current Favorites", "Number of Comments"])

    # Add data
    f.writerows(allGuideData)


# Print time to finish and exit
print(f'{round((time.time() - start_time), 2)} seconds to finish')
input('Press key to exit.')