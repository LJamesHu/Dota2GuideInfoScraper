from bs4 import BeautifulSoup
import urllib2
import csv
import datetime

# Scrape guide information
def guideScrape(guideURL):

    response = urllib2.urlopen(guideURL)
    soup = BeautifulSoup(response.read(), "html.parser")
    response.close()

    title = soup.find(class_="workshopItemTitle").get_text()
    rating = int(str(soup.find(class_="fileRatingDetails"))[-29])
    numRatings = soup.find(class_="numRatings").get_text()[:-7].replace(",", "")
    stats = soup.find(class_="stats_table").findAll('td')
    visitors = stats[0].get_text().replace(",", "")
    subscribers = stats[2].get_text().replace(",", "")
    favorites = stats[4].get_text().replace(",", "")
    if soup.find(class_="commentthread_count") != None:
        commentNum = soup.find(class_="commentthread_count").get_text().strip()[:-8].replace(",", "")
    else:
        commentNum = 0

    return [guideURL, title, rating, numRatings, visitors, subscribers, favorites, commentNum]

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko')]
urllib2.install_opener(opener)

# guideScrape("http://steamcommunity.com/sharedfiles/filedetails/?id=286904891")

fileName = "guideData-" + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + ".csv"

totalGuides = 0
totalRating = 0
totalRatings = 0
totalVisitors = 0
totalSubscribers = 0
totalFavorites = 0
totalComments = 0

# File setup
with open(fileName, "ab") as fileO:
    f = csv.writer(fileO)
    # Write reference row
    f.writerow(["URL", "Guide Name", "Average Rating", "Number of Ratings", "Unique Visitors", "Current Subscribers", "Current Favorites", "Number of Comments"])

# Build number to iterate search
for num in range(1,100):

    print num

    # Build URL
    searchurl = "http://steamcommunity.com/id/0825771/myworkshopfiles/?section=guides&appid=570&p=" + str(num)

    # Read URL
    responseMain = urllib2.urlopen(searchurl)
    soupMain = BeautifulSoup(responseMain.read(), "html.parser")
    responseMain.close()

    # If there are no more entries, break out of the loop
    if soupMain.find(id="no_items") != None:
        break

    # Otherwise get listings
    listings = soupMain.find_all(class_="workshopItemCollection")

    for listing in listings:

        soupInfo = BeautifulSoup(str(listing), "html.parser")
        for tag in soupInfo.findAll(True,{"onclick":True}) :
            guideURL = tag["onclick"][19:-1]
            print guideURL

        guideInfo = guideScrape(guideURL)

        with open(fileName, "ab") as fileO:
            f = csv.writer(fileO)
            f.writerow(guideInfo)

        totalGuides += 1
        totalRating += guideInfo[2]
        totalRatings += int(guideInfo[3])
        totalVisitors += int(guideInfo[4])
        totalSubscribers += int(guideInfo[5])
        totalFavorites += int(guideInfo[6])
        totalComments += int(guideInfo[7])

with open(fileName, "ab") as fileO:
    f = csv.writer(fileO)
    f.writerow(["Totals", totalGuides, totalRating, totalRatings, totalVisitors, totalSubscribers, totalFavorites, totalComments])
    f.writerow(["Averages", totalGuides, totalRating/float(totalGuides), totalRatings/float(totalGuides), totalVisitors/float(totalGuides), totalSubscribers/float(totalGuides), totalFavorites/float(totalGuides), totalComments/float(totalGuides)])