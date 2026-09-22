from operator import itemgetter
from bs4 import BeautifulSoup
from random import choice, uniform
from csv import writer, reader
from glob import glob
from datetime import datetime, timezone
import requests
import math
import time
import sys
import os
import re


def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input('Press key to exit.')
    sys.exit(-1)

sys.excepthook = show_exception_and_exit

# List of user agents last updated
agents = ['Mozilla/5.0 (Windows NT 11.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6073.156 Safari/537.36',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/616.9 (KHTML, like Gecko) Version/17.1 Safari/616.9',
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6043.119 Safari/537.36 Edg/120.0.2673.144',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0_9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6110.175 Safari/537.36',
          'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6471.173 Safari/537.36'
         ]

GUIDE_URL = 'https://steamcommunity.com/sharedfiles/filedetails/?id='

# Guides to leave out of the output (not hero guides)
skip_guides = ['2958853356']

# Output columns, a guide's row follows this order
# The columns after Number of Comments are only on the Steam Web API. Lifetime counts and dates
# are there for every run, the rest need a Web API key
HEADER = ['URL', 'Guide Name', 'Hero Name', 'Average Rating', 'Number of Ratings', 'Unique Visitors',
          'Current Subscribers', 'Current Favorites', 'Number of Comments',
          'Votes Up', 'Votes Down', 'Score', 'Upvote %', 'Lifetime Subscribers', 'Lifetime Favorites',
          'Games Played', 'Hours Played', 'Awards', 'Updates', 'Role', 'Patch', 'Hidden From Search',
          'Created', 'Last Updated',
          'Reports', 'Banned', 'Ban Reason', 'Visibility', 'Flagged Inappropriate', 'Text Check Result', 'Issues']
SORT_COLUMN = HEADER.index('Current Subscribers')

# Columns that are text so have no total or average, and columns where a total means nothing
TEXT_COLUMNS = ['URL', 'Guide Name', 'Hero Name', 'Role', 'Patch', 'Hidden From Search', 'Created', 'Last Updated',
                'Banned', 'Ban Reason', 'Visibility', 'Flagged Inappropriate', 'Text Check Result', 'Issues']

# Who can see a guide, from the Web API's visibility number
VISIBILITY = {0: 'Public', 1: 'Friends Only', 2: 'Private', 3: 'Unlisted'}
NO_TOTAL_COLUMNS = ['Score', 'Upvote %']

# Known guide ids per author, used when the author's profile is private since the guide
# search misses a few guides. Guides are verified by author when scraped so stale ids are harmless
known_guides = {
    '0825771': [
        '128726494', '128728638', '128730475', '128732275', '128734250', '128735861', '128741319', '128742802',
        '128743885', '128745244', '128746588', '128748151', '128751287', '128752632', '128753951', '128754907',
        '128756420', '128757681', '128851981', '128855291', '128858659', '128862386', '128866569', '128871463',
        '128873254', '128876778', '128882317', '128887479', '128891336', '128895761', '128898296', '128899869',
        '128903691', '128906539', '128909765', '128912519', '128914193', '128917369', '128918471', '128920907',
        '128922664', '128925332', '128927319', '128929132', '128932114', '128937771', '128945163', '128956358',
        '128960249', '128972272', '129056935', '129060054', '129062086', '129063701', '129064094', '129065509',
        '129067853', '129069615', '129072324', '129076227', '129079469', '129081035', '129081331', '129083818',
        '129085778', '129093311', '129096483', '129098268', '129100110', '129102427', '129105276', '129107725',
        '129109889', '129111538', '129119115', '129130896', '129134687', '129137630', '129143802', '129149991',
        '129157199', '129191918', '129193377', '129204328', '129323738', '129331714', '129332354', '129332786',
        '129334727', '129381491', '129399377', '129399862', '129400259', '129400559', '129400942', '129402256',
        '129402805', '129403206', '134962374', '140111731', '143016376', '143243384', '159698040', '161358226',
        '165334812', '176984007', '195048794', '195052251', '203428541', '203428546', '222262678', '222264754',
        '222265746', '232338429', '232367327', '232415624', '232946791', '251934276', '251941747', '251982939',
        '254615876', '261777247', '269700420', '286891439', '286895078', '286904891', '301732264', '301735208',
        '309919893', '319085962', '319092788', '319092835', '319101948', '319106719', '319109248', '319111870',
        '330545830', '334021836', '344511398', '344512092', '356791078', '359580647', '381725812', '391458050',
        '434659379', '576975639', '576978688', '688715106', '750406868', '750410650', '817380197', '817387228',
        '895968997', '898788847', '1187546268', '1187551178', '1187563935', '1492532510', '1674127743', '1921549643',
        '1921553241', '2324368014', '2451777397', '2639555824', '2762905224', '2943368068', '3315134700', '3362336316',
        '3625076233'
    ]
}

API_URL = 'https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/'

# With a Steam Web API key (free from https://steamcommunity.com/dev/apikey) everything comes from
# the Web API in a few requests and none of the rate limited community pages are needed
KEY_API_URL = 'https://api.steampowered.com/IPublishedFileService/'
VANITY_API_URL = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
KEY_FILE = 'steam_api_key.txt'

# Workshop file types for guides, web guides and in game hero builds
GUIDE_FILE_TYPES = [9, 10]

# Number of ratings a guide needs before Steam shows its stars
MIN_RATINGS_FOR_STARS = 25

# Raised when a guide should be left out (removed, hidden or not by the target author)
class SkipGuide(Exception):
    pass

# Raised when Steam keeps rate limiting a page after several long waits
class RateLimited(Exception):
    pass

# Reuse one connection for all requests
session = requests.Session()

# Extra seconds added to the delay between guides, raised every time Steam rate limits
# so the scrape settles at a pace Steam accepts instead of repeatedly hitting the limit
pace = {'extra_delay': 0}

# Get a page, waiting and retrying on rate limiting, server errors and network problems
def get_page(url, attempts=10, max_rate_limits=6):
    rate_limits = 0
    for attempt in range(1, attempts + 1):
        # Randomize user agent
        headers = {'User-Agent': choice(agents), 'Accept-Language': 'en-US,en;q=0.9'}
        try:
            r = session.get(url, headers=headers, timeout=30)
        except requests.RequestException as e:
            print(f'Request failed ({e}), waiting before retrying.')
            time.sleep(uniform(20, 60))
            continue

        if r.status_code == 429:
            rate_limits += 1
            if rate_limits > max_rate_limits:
                raise RateLimited(f'Still rate limited on {url} after {max_rate_limits} waits')

            # Slow down once per rate limited page, not for every retry of it
            if rate_limits == 1:
                pace['extra_delay'] = min(pace['extra_delay'] + 5, 30)

            # Retrying while still blocked keeps the block going, so wait longer each time
            wait = uniform(120, 300) * rate_limits
            retry_after = r.headers.get('Retry-After', '')
            if retry_after.isdigit():
                wait = max(wait, int(retry_after) + 5)
            print(f"Rate limited by Steam, waiting {round(wait / 60, 1)} minutes before retrying. "
                  f"Delay between guides is now {pace['extra_delay']} seconds longer.")
            time.sleep(wait)
        elif r.status_code >= 500:
            print(f'Steam returned status {r.status_code}, waiting before retrying.')
            time.sleep(uniform(20, 60))
        else:
            return r

    raise RuntimeError(f'Could not load {url} after {attempts} attempts')

# Guide details from the Steam Web API as {guide id: details}, no key needed
# One request covers many guides and is not affected by the community site's rate limiting
# Gives everything except ratings and comments. Returns what it could get, empty if unavailable
def api_details(guide_ids):
    details = {}
    for start in range(0, len(guide_ids), 100):
        batch = guide_ids[start:start + 100]
        data = {'itemcount': len(batch)}
        for num, guide_id in enumerate(batch):
            data[f'publishedfileids[{num}]'] = guide_id

        for attempt in range(1, 4):
            try:
                r = session.post(API_URL, data=data, timeout=60)
                r.raise_for_status()
                for detail in r.json()['response']['publishedfiledetails']:
                    details[detail['publishedfileid']] = detail
                break
            except (requests.RequestException, ValueError, KeyError) as e:
                print(f'Steam API request failed ({e!r}), attempt {attempt}.')
                time.sleep(uniform(5, 15))

    return details

# Folder of the exe or script, where the key file is kept
def app_folder():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# Steam Web API key from the STEAM_API_KEY environment variable or the key file, None if there is none
def load_api_key():
    api_key = os.environ.get('STEAM_API_KEY', '').strip()
    if api_key:
        return api_key
    try:
        with open(os.path.join(app_folder(), KEY_FILE), encoding='utf-8') as file:
            return file.read().strip() or None
    except OSError:
        return None

# Web API request with the key sent as a header so it is never part of a URL
def key_api_get(url, params, api_key):
    for attempt in range(1, 4):
        try:
            r = session.get(url, params=params, headers={'x-webapi-key': api_key}, timeout=60)
            if r.status_code in (401, 403):
                raise ValueError('Steam did not accept the Web API key')
            r.raise_for_status()
            return r.json()['response']
        except (requests.RequestException, KeyError) as e:
            print(f'Steam API request failed ({e!r}), attempt {attempt}.')
            time.sleep(uniform(5, 15))
    raise RuntimeError(f'Steam API request to {url} failed')

# Star rating from a Web API vote score between 0 and 1, matches the stars Steam shows
def score_rating(score):
    return min(5, max(1, math.ceil(score * 5)))

# All guide data for an author through the Web API with a key, works for private profiles too
def key_scrape(scrape_target, api_key):

    # Custom profile names need resolving to a steam id
    if re.fullmatch(r'\d{17}', scrape_target):
        steam_id = scrape_target
    else:
        resolved = key_api_get(VANITY_API_URL, {'vanityurl': scrape_target}, api_key)
        if resolved.get('success') != 1:
            raise ValueError(f'Could not find a Steam profile for {scrape_target}')
        steam_id = resolved['steamid']

    # List the author's guides
    guide_ids = []
    for file_type in GUIDE_FILE_TYPES:
        for num in range(1, 200):
            listing = key_api_get(KEY_API_URL + 'GetUserFiles/v1/',
                                  {'steamid': steam_id, 'appid': 570, 'filetype': file_type,
                                   'numperpage': 100, 'page': num, 'ids_only': 'true'}, api_key)
            files = listing.get('publishedfiledetails', [])
            guide_ids += [file['publishedfileid'] for file in files if file['publishedfileid'] not in skip_guides]
            if len(files) < 100:
                break
    # A banned or hidden guide could drop out of the listing, which is when it most needs looking at,
    # so known guides are always checked as well
    listed_ids = set(guide_ids)
    guide_ids += [guide_id for guide_id in known_guides.get(scrape_target, []) if guide_id not in skip_guides]
    guide_ids = list(dict.fromkeys(guide_ids))
    print(f'{len(guide_ids)} guides found')

    # Get the details
    guide_rows = []
    for start in range(0, len(guide_ids), 100):
        params = {'includevotes': 'true', 'includetags': 'true', 'includekvtags': 'true', 'includereactions': 'true'}
        for num, guide_id in enumerate(guide_ids[start:start + 100]):
            params[f'publishedfileids[{num}]'] = guide_id

        for detail in key_api_get(KEY_API_URL + 'GetDetails/v1/', params, api_key)['publishedfiledetails']:
            if detail.get('result') != 1:
                print(f"Could not get details for {GUIDE_URL + detail.get('publishedfileid', '')} (result {detail.get('result')}), "
                      'it may have been removed and is left out.')
                continue
            if detail.get('creator') != steam_id:
                continue
            guide_row = api_row(detail)

            # Steam only shows stars once there are enough ratings. Guides seen without stars had
            # up to 18 ratings and guides with stars had 34 or more, so the cut off is around 25
            votes = detail.get('vote_data', {})
            num_ratings = votes.get('votes_up', 0) + votes.get('votes_down', 0)
            if num_ratings >= MIN_RATINGS_FOR_STARS:
                guide_row[HEADER.index('Average Rating')] = score_rating(votes.get('score', 0))
            guide_row[HEADER.index('Number of Ratings')] = num_ratings
            guide_row[HEADER.index('Number of Comments')] = detail.get('num_comments_public', 0)

            # Information that is not on the guide's page
            guide_row[HEADER.index('Votes Up')] = votes.get('votes_up', 0)
            guide_row[HEADER.index('Votes Down')] = votes.get('votes_down', 0)
            if num_ratings:
                guide_row[HEADER.index('Score')] = round(votes.get('score', 0), 4)
                guide_row[HEADER.index('Upvote %')] = round(100 * votes.get('votes_up', 0) / num_ratings, 2)

            # Sessions are games played with the guide, playtime is in seconds
            guide_row[HEADER.index('Games Played')] = int(detail.get('lifetime_playtime_sessions', 0))
            guide_row[HEADER.index('Hours Played')] = round(int(detail.get('lifetime_playtime', 0)) / 3600)
            guide_row[HEADER.index('Awards')] = sum(reaction.get('count', 0) for reaction in detail.get('reactions', []))
            guide_row[HEADER.index('Updates')] = int(detail.get('revision_change_number', 0))

            kvtags = {kvtag['key']: kvtag['value'] for kvtag in detail.get('kvtags', [])}
            guide_row[HEADER.index('Role')] = kvtags.get('role', '').replace('#DOTA_HeroGuide_Role_', '') or None
            guide_row[HEADER.index('Patch')] = kvtags.get('gameplay_version')

            # Steam flags some guides as incompatible, these do not show up in the guide search or browse
            guide_row[HEADER.index('Hidden From Search')] = 'Yes' if detail.get('incompatible') else 'No'

            # Moderation information, normally all clear so anything here needs looking at
            visibility = VISIBILITY.get(detail.get('visibility', 0), str(detail.get('visibility')))
            inappropriate = [label for label, flag in [('Sex', 'maybe_inappropriate_sex'), ('Violence', 'maybe_inappropriate_violence')]
                             if detail.get(flag)]
            guide_row[HEADER.index('Reports')] = detail.get('num_reports', 0)
            guide_row[HEADER.index('Banned')] = 'Yes' if detail.get('banned') else 'No'
            guide_row[HEADER.index('Ban Reason')] = detail.get('ban_reason') or None
            guide_row[HEADER.index('Visibility')] = visibility
            guide_row[HEADER.index('Flagged Inappropriate')] = ', '.join(inappropriate) or 'No'
            guide_row[HEADER.index('Text Check Result')] = detail.get('ban_text_check_result', 0)

            issues = []
            if detail.get('banned'):
                issues.append('Banned' + (f": {detail['ban_reason']}" if detail.get('ban_reason') else ''))
            if detail.get('num_reports'):
                issues.append(f"{detail['num_reports']} reports")
            if visibility != 'Public':
                issues.append(f'Visibility is {visibility}')
            if inappropriate:
                issues.append('Flagged inappropriate (' + ', '.join(inappropriate) + ')')
            if detail.get('ban_text_check_result'):
                issues.append(f"Text check result {detail['ban_text_check_result']}")
            if detail.get('incompatible'):
                issues.append('Hidden from search (flagged incompatible)')
            if detail['publishedfileid'] not in listed_ids:
                issues.append("Missing from the author's guide listing")
            guide_row[HEADER.index('Issues')] = '; '.join(issues) or None
            guide_rows.append(guide_row)

    return guide_rows

# Guide row from Steam Web API details, ratings and comments are not available without a key
def api_row(detail):
    # Tags are the hero plus lowercase labels like 'hero build' and 'english'
    hero_names = [tag['tag'] for tag in detail.get('tags', []) if tag['tag'][:1].isupper()]
    hero_name = hero_names[0] if len(hero_names) == 1 else None
    if hero_name is not None and hero_name.isupper():
        hero_name = hero_name.title()

    guide_row = [None] * len(HEADER)
    guide_row[:9] = [GUIDE_URL + detail['publishedfileid'], detail['title'].strip(), hero_name, None, None,
                     detail['views'], detail['subscriptions'], detail['favorited'], None]
    guide_row[HEADER.index('Lifetime Subscribers')] = detail.get('lifetime_subscriptions')
    guide_row[HEADER.index('Lifetime Favorites')] = detail.get('lifetime_favorited')
    guide_row[HEADER.index('Created')] = api_date(detail.get('time_created'))
    guide_row[HEADER.index('Last Updated')] = api_date(detail.get('time_updated'))
    return guide_row

# Date and time (UTC) from a Web API timestamp
def api_date(timestamp):
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%d %H:%M')

# Star ratings seen on listing pages as {guide id: rating}, saves needing the guide's page for it
listing_ratings = {}

# Star rating from a rating image like 5-star.png, None when there are not enough ratings
def parse_rating(img):
    try:
        return int(img['src'].split('/')[-1][0])
    except (TypeError, KeyError, ValueError, IndexError):
        return None

# Guide id from any form of guide URL
def guide_id_from_url(url):
    return re.search(r'[?&]id=(\d+)', url).group(1)

# Guide listing from the author's workshop page as (guide id, title)
# Returns None if the listing is not visible (private or friends only profile)
# along with the profile page Steam showed instead
def profile_listing(scrape_target):
    guides = []

    # Iterate search through pages
    for num in range(1, 200):
        # Pagination URL
        search_url = f'https://steamcommunity.com/id/{scrape_target}/myworkshopfiles/?section=guides&appid=570&p={num}'

        # Information on page number being scraped
        print('* * * *')
        print(f'Scraping Page {num}: {search_url}')
        print('* * * *')

        # Read pagination page's HTML data, nothing can be done without it so be patient
        r_search = get_page(search_url, attempts=12, max_rate_limits=8)

        # Steam redirects to the bare profile page when the workshop files are not visible
        # to a logged out visitor
        if 'myworkshopfiles' not in r_search.url:
            return None, r_search

        soup_search = BeautifulSoup(r_search.content, 'html.parser')

        # If there are no more entries, break out of the loop
        listings = soup_search.find_all(class_='workshopItemCollection')
        if soup_search.find(id='no_items') is not None or not listings:
            break

        for listing in listings:
            guide_id = guide_id_from_url(listing['href'])
            guides.append((guide_id, listing.find(class_='workshopItemTitle').get_text().strip()))
            listing_ratings[guide_id] = parse_rating(listing.find(class_='fileRating'))

        time.sleep(uniform(1, 3))

    return guides, None

# Guide listing from the Dota 2 guide search, used when the author's profile is private
# Search matches on text so results are filtered by author name here and the author
# is verified again on each guide's page
def search_listing(r_profile):

    # Private profiles still show the display name
    soup_profile = BeautifulSoup(r_profile.content, 'html.parser')
    persona = soup_profile.find(class_='actual_persona_name')
    if persona is None:
        print('Could not read the profile name, skipping guide search.')
        return []
    persona_name = persona.get_text().strip()
    print(f'Searching Dota 2 guides for "{persona_name}"')

    guides = []
    for num in range(1, 200):
        search_url = f'https://steamcommunity.com/app/570/guides/?searchText=%22{requests.utils.quote(persona_name)}%22&browsefilter=toprated&p={num}'

        print('* * * *')
        print(f'Scraping Search Page {num}: {search_url}')
        print('* * * *')

        soup_search = BeautifulSoup(get_page(search_url).content, 'html.parser')
        listings = soup_search.find_all(class_='workshopItemCollection')
        if not listings:
            break

        for listing in listings:
            author = listing.find(class_='workshopItemAuthorName')
            if author is None or author.get_text().strip().lower() != persona_name.lower():
                continue
            # Title is the last piece of text, after the guide type label
            guide_title = list(listing.find(class_='workshopItemTitle').stripped_strings)[-1]
            guides.append((listing['data-publishedfileid'], guide_title))
            listing_ratings[listing['data-publishedfileid']] = parse_rating(listing.find(class_='fileRating'))

        time.sleep(uniform(3, 8))

    return guides

# Guides from previous outputs in this folder, newest first, the search misses a few guides
def previous_csv_listing(scrape_name):
    guides = []
    for file_name in sorted(glob(f'guideData-{scrape_name}-*.csv'), reverse=True):
        try:
            with open(file_name, encoding='utf-8', newline='') as file:
                for row in reader(file):
                    if len(row) > 1 and row[0].startswith(GUIDE_URL):
                        guides.append((guide_id_from_url(row[0]), row[1].strip()))
        except (OSError, UnicodeDecodeError) as e:
            print(f'Could not read {file_name}: {e}')
    return guides

# Number from text like '1,234 ratings'
def parse_number(text):
    return int(text.strip().split()[0].replace(',', ''))

# Scrape individual guide information
def guide_scrape(guide_id, author_url=None):

    # Load guide's HTML information
    guide_url = GUIDE_URL + guide_id
    r_guide = get_page(guide_url)
    soup_guide = BeautifulSoup(r_guide.content, 'html.parser')

    # Removed or hidden guides (can come from previous outputs)
    if 'There was a problem accessing the item' in r_guide.text:
        raise SkipGuide(f'{guide_url} is no longer available')

    # Check the guide belongs to the author
    if author_url is not None:
        creators = [a.get('href', '').rstrip('/').lower() for a in soup_guide.find_all(class_='friendBlockLinkOverlay')]
        if creators and author_url.lower() not in creators:
            raise SkipGuide(f'{guide_url} is not by {author_url}')

    # Parse and collect information
    title = soup_guide.find(class_='workshopItemTitle').get_text().strip()

    # Parse hero name, not every guide has a hero tag
    workshop_tags = soup_guide.find_all(class_='workshopTags')
    hero_names = [tag.text.strip().split('\xa0')[1] for tag in workshop_tags
                  if ('Heroes' in tag.text or 'Tag' in tag.text) and '\xa0' in tag.text]
    hero_name = hero_names[0] if hero_names else None

    # Get ratings data
    rating_details = soup_guide.find(class_='fileRatingDetails')
    rating = parse_rating(rating_details.img) if rating_details is not None else None
    try:
        num_ratings = parse_number(soup_guide.find(class_='numRatings').get_text())
    except (AttributeError, ValueError, IndexError):
        num_ratings = None

    # Get major stats
    stats = soup_guide.find(class_='stats_table').find_all('td')

    visitors = parse_number(stats[0].get_text())
    subscribers = parse_number(stats[2].get_text())
    favorites = parse_number(stats[4].get_text())

    # Comments may not exist
    comment_label = soup_guide.find(class_='commentthread_count_label')
    commentNum = parse_number(comment_label.get_text()) if comment_label is not None else 0

    # The rest of the columns are only on the Web API
    guide_row = [guide_url, title, hero_name, rating, num_ratings, visitors, subscribers, favorites, commentNum]
    return guide_row + [None] * (len(HEADER) - len(guide_row))

# Write guide data with summary rows to csv
def write_output(all_guide_data, file_name):

    # Sort guide data by subscribers
    all_guide_data = sorted(all_guide_data, key=itemgetter(SORT_COLUMN), reverse=True)

    # Get totals and averages, ignoring missing values
    totals = ['Total', len(all_guide_data), '']
    averages = ['Average', len(all_guide_data), '']
    for column, metric in list(zip(HEADER, zip(*all_guide_data)))[3:]:
        metric = [value for value in metric if value is not None]
        if column in TEXT_COLUMNS or not metric:
            totals.append(None)
            averages.append(None)
        else:
            totals.append(None if column in NO_TOTAL_COLUMNS else sum(metric))
            averages.append(sum(metric)/len(metric))

    # File setup
    try:
        with open(file_name, 'w', encoding='utf-8', newline='') as file:
            f = writer(file)

            # Write reference row
            f.writerow(HEADER)

            # Add data
            f.writerows(all_guide_data)
            f.writerow(totals)
            f.writerow(averages)
    except PermissionError:
        print(f'Could not write {file_name}, close it if it is open in another program.')
        return False

    return True

def guide_listing_scrape(target_id):

    # Setting up scraping target data

    # 0825771 - Torte de Lini
    # ImmortalFaith
    if target_id == '1':
        scrape_target = '0825771'
    elif target_id == '2':
        scrape_target = 'ImmortalFaith'
    else:
        # Allow a pasted profile URL
        scrape_target = target_id.rstrip('/').split('/')[-1]

    if scrape_target == '0825771':
        scrape_name = 'TorteDeLini'
    else:
        scrape_name = scrape_target

    print(f'Scraping guides for {scrape_name}')

    # With a Web API key everything comes from the Web API
    api_key = load_api_key()
    if api_key:
        print('Using the Steam Web API key')
        try:
            guide_rows = key_scrape(scrape_target, api_key)
            if guide_rows:
                file_name = 'guideData-' + scrape_name + '-' + time.strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
                while not write_output(guide_rows, file_name):
                    input('Press Enter to try writing the file again.')

                # Point out anything that needs attention
                issue_rows = [guide_row for guide_row in guide_rows if guide_row[HEADER.index('Issues')]]
                if issue_rows:
                    print()
                    print(f'{len(issue_rows)} guides need attention:')
                    for guide_row in issue_rows:
                        print(f"  {guide_row[2] or guide_row[1]}: {guide_row[HEADER.index('Issues')]}")
                        print(f'    {guide_row[0]}')
                    print()
                else:
                    print('No reports, bans or other issues on any guide.')
                print(f'Output to {file_name}')
                return
            print('No guides found with the Steam Web API key, scraping the Steam pages instead.')
        except (ValueError, RuntimeError, KeyError) as e:
            print(f'{e}, scraping the Steam pages instead.')

    # Get guide listing from the author's workshop page
    author_url = None
    author_id = None
    guides, r_profile = profile_listing(scrape_target)

    # Private profile, fall back to guide search plus known guides and guides from previous outputs
    # These can include other authors' guides so the author is verified for each guide
    if guides is None:
        print('Guide listing is not visible (private profile), falling back to guide search.')
        author_url = f'https://steamcommunity.com/id/{scrape_target}'
        steam_id = re.search(r'"steamid":"(\d+)"', r_profile.text)
        author_id = steam_id.group(1) if steam_id else None
        try:
            guides = search_listing(r_profile)
        except RateLimited as e:
            print(f'{e}, continuing without the guide search.')
            guides = []
        guides += previous_csv_listing(scrape_name)
        guides += [(guide_id, '') for guide_id in known_guides.get(scrape_target, [])]

    # Remove duplicates, keeping the first title found
    unique_guides = {}
    for guide_id, guide_title in guides:
        if guide_id not in skip_guides:
            unique_guides.setdefault(guide_id, guide_title)
    print(f'{len(unique_guides)} guides found')

    # Get everything except ratings and comments from the Steam Web API
    print('Getting guide stats from the Steam Web API')
    details = api_details(list(unique_guides))
    if not details:
        print('Steam Web API not available, everything will be scraped from the guide pages.')

    # Guide data by guide id, starts with the Web API data and is replaced by the
    # full data as each guide page is scraped
    guide_rows = {}
    for guide_id in list(unique_guides):
        detail = details.get(guide_id)
        if detail is None:
            continue
        if detail.get('result') != 1:
            print(f'Skipping: {GUIDE_URL + guide_id} is no longer available')
            del unique_guides[guide_id]
        elif author_id is not None and detail.get('creator') != author_id:
            print(f'Skipping: {GUIDE_URL + guide_id} is not by {author_url}')
            del unique_guides[guide_id]
        else:
            guide_rows[guide_id] = api_row(detail)
            guide_rows[guide_id][HEADER.index('Average Rating')] = listing_ratings.get(guide_id)
            unique_guides[guide_id] = unique_guides[guide_id] or guide_rows[guide_id][1]
    print(f'{len(unique_guides)} guides to scrape')

    # Set file name
    file_name = 'guideData-' + scrape_name + '-' + time.strftime('%Y-%m-%d_%H-%M-%S') + '.csv'

    # Output what the Web API gave straight away, the file is updated as the guide pages are scraped
    if guide_rows:
        write_output(list(guide_rows.values()), file_name)
        print(f'Stats saved to {file_name}, now getting number of ratings and comments from each guide page.')
        print('Steam rate limits these pages heavily so this can take a long time.')
        print('Press Ctrl+C to stop early, the csv will have everything collected up to then.')

    # Guides where the guide page could not be scraped
    failed_guides = []
    remaining_guides = list(unique_guides)

    try:
        # Iterate through guide items for ratings and comments
        for num, (guide_id, guide_title) in enumerate(unique_guides.items(), 1):

            # Scrape guide
            print(f'Scraping Guide {num}/{len(unique_guides)} {GUIDE_URL + guide_id}: {guide_title}')

            time.sleep(uniform(1, 10) + pace['extra_delay'])

            # Author is already verified for guides found by the Web API
            check_author = None if guide_id in guide_rows else author_url

            # Sometimes guide scrape would fail randomly so rerun attempts help solve this
            # Rate limiting and network problems are already handled when getting the page
            for attempt in range(1, 6):
                try:
                    guide_row = guide_scrape(guide_id, check_author)
                    # Keep Web API values for anything the page did not have
                    if guide_id in guide_rows:
                        guide_row = [api_value if value is None else value
                                     for value, api_value in zip(guide_row, guide_rows[guide_id])]
                    guide_rows[guide_id] = guide_row
                    break
                except SkipGuide as e:
                    print(f'Skipping: {e}')
                    guide_rows.pop(guide_id, None)
                    break
                except RateLimited:
                    raise
                except Exception as e:
                    print(f'Attempt {attempt} failed: {e!r}')
                    time.sleep(uniform(20, 60))
            else:
                # Keep going so one guide does not lose the whole run
                failed_guides.append(guide_id)

            remaining_guides.remove(guide_id)

            # Save progress
            if num % 10 == 0 and guide_rows:
                write_output(list(guide_rows.values()), file_name)

    except RateLimited as e:
        print(f'{e}, giving up on the remaining guide pages.')
        failed_guides += remaining_guides
    except KeyboardInterrupt:
        print('Interrupted, writing the guides scraped so far.')
        failed_guides += remaining_guides

    # Guides with Web API data are still in the output, only without ratings and comments
    no_ratings = [guide_id for guide_id in failed_guides if guide_id in guide_rows]
    missing = [guide_id for guide_id in failed_guides if guide_id not in guide_rows]
    if no_ratings:
        print(f'{len(no_ratings)} guide pages could not be scraped, these guides have no ratings or comments in the output.')
    if missing:
        print(f'{len(missing)} guides could not be scraped and are missing from the output:')
        for guide_id in missing:
            print(f'  {GUIDE_URL + guide_id}')

    if not guide_rows:
        print('No guide data collected, nothing to output.')
        return

    while not write_output(list(guide_rows.values()), file_name):
        input('Press Enter to try writing the file again.')
    print(f'Output to {file_name}')

def get_number_input():

    print('Enter 1 for Torte de Lini.')
    print('Enter 2 for ImmortalFaith.')
    print('Otherwise enter target user.')
    user_input = input('Please enter a value: ')

    return str(user_input).strip()

# Ask for a Steam Web API key the first time, it is kept in a file next to the exe or script
def ask_api_key():
    if load_api_key():
        return

    print()
    print('A Steam Web API key makes this take seconds instead of hours.')
    print('Get one for free at https://steamcommunity.com/dev/apikey (any domain name works, like localhost).')
    api_key = input('Paste your key here, or just press Enter to continue without one: ').strip()
    if not api_key:
        return

    try:
        with open(os.path.join(app_folder(), KEY_FILE), 'w', encoding='utf-8') as file:
            file.write(api_key)
        print(f'Key saved to {KEY_FILE}, keep that file private.')
    except OSError as e:
        print(f'Could not save the key ({e}), using it for this run only.')
        os.environ['STEAM_API_KEY'] = api_key

if __name__ == '__main__':
    # Call the function and store the result
    target_id = get_number_input()
    ask_api_key()

    # Initialize time tracking
    start_time = time.time()

    guide_listing_scrape(target_id)

    # Print time to finish and exit
    print(f'{round((time.time() - start_time), 2)} seconds to finish')
    input('Press key to exit.')
