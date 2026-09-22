# Dota 2 Guide Info Scraper
Gets the stats for every Dota 2 guide an author has published on Steam and writes them to a csv with total and average rows at the bottom. Made for Torte De Lini so subscriber counts and everything else for 160+ guides come out at the click of a button.

## How to run
1. Put `Dota2GuideInfoScraper.exe` in a folder of its own (the csv files are written next to it).
2. Double click it. Enter `1` for Torte de Lini, `2` for ImmortalFaith, or type any Steam profile name or profile URL.
3. The first time it asks for a Steam Web API key (see below). Paste it and press Enter, or just press Enter to run without one.
4. The csv appears in the same folder, named `guideData-<author>-<date>.csv`.

With a key a run takes about a second. Without one the first part takes about a minute and the rest can take hours (see [Without a key](#without-a-key-slow-can-take-hours)).

## Steam Web API key (recommended)
1. Get a free key at https://steamcommunity.com/dev/apikey. Any domain name works, like `localhost`. The Steam account has to have spent $5 and have the Steam Guard mobile authenticator.
2. Paste it at the prompt on the first run. It is saved to `steam_api_key.txt` next to the exe and used automatically after that. The `STEAM_API_KEY` environment variable also works and takes priority.

Keep the key private like a password: do not share the key file, do not build it into an exe you give someone else, and revoke it on the same page if it leaks. `steam_api_key.txt` is gitignored and the key is only ever sent as a request header, never in a URL.

With a key everything comes from the Steam Web API (`IPublishedFileService`) in a few requests: the author's guide list (works for private profiles too), stats, votes and comment counts. None of the rate limited Steam community pages are needed. Star ratings are worked out from the vote score (score x 5 rounded up, checked against the stars Steam shows) and left blank under 25 ratings, where Steam does not show stars.

## Output columns
The first nine columns are the same as they have always been: URL, Guide Name, Hero Name, Average Rating, Number of Ratings, Unique Visitors, Current Subscribers, Current Favorites, Number of Comments. Rows are sorted by Current Subscribers. After those come columns that are only available from the Web API:

| Column | Meaning |
|---|---|
| Votes Up / Votes Down | Actual thumbs up and down, Number of Ratings is the two added together |
| Score | Steam's rating score from 0 to 1, much finer than the stars |
| Upvote % | Votes Up out of all votes |
| Lifetime Subscribers / Lifetime Favorites | Everyone who ever subscribed/favorited, including those who later removed it |
| Games Played / Hours Played | Games played with the guide selected and their total length |
| Awards | Steam awards given to the guide |
| Updates | Number of times the guide has been changed |
| Role / Patch | Role and game version set on the guide |
| Hidden From Search | Yes if Steam has flagged the guide as incompatible, these guides do not show up in the guide search or browse |
| Created / Last Updated | Dates in UTC |
| Reports | Number of times the guide has been reported |
| Banned / Ban Reason | Whether Steam has banned the guide and why |
| Visibility | Public, Friends Only, Private or Unlisted |
| Flagged Inappropriate | Steam's automatic sex/violence content flags |
| Text Check Result | Steam's automatic text moderation result, 0 is clear |
| Issues | Summary of anything above that needs attention, blank when the guide is fine |

With a key, the run ends by listing every guide that has something in Issues (or saying there are none), so problems are seen without opening the csv. Known guides are always checked even if they have dropped out of the author's listing, and a guide that has been removed is called out.

Lifetime Subscribers, Lifetime Favorites, Created and Last Updated are filled in on every run, the rest need a Web API key. Text columns and Score/Upvote % have no total.

## Without a key (slow, can take hours)
Press Enter at the key prompt. Title, hero, visitors, subscribers and favorites come from the keyless Steam Web API (`ISteamRemoteStorage/GetPublishedFileDetails`) and star ratings from the listing pages, so the csv has those for every guide within about a minute. Number of ratings and comments need each guide's page, which Steam rate limits heavily (roughly 20 pages, then blocks of 10-50 minutes), so the scraper slows itself down whenever it gets rate limited and keeps updating the csv as it goes. If the pages stay blocked, or on Ctrl+C, the csv still has all guides with only those two columns blank for the pages it could not get.

If the author's Steam profile is private, the workshop listing is not visible without a key, so the scraper falls back to the Dota 2 guide search (filtered and verified by author) combined with a built-in list of known guide ids and any previous `guideData-*.csv` outputs in the same folder, since the search misses a few guides.

## Running from source and building the exe
Needs Python 3 with `requests` and `beautifulsoup4`:

```
pip install requests beautifulsoup4
python Dota2GuideInfoScraper.py
```

The exe is built with PyInstaller so no Python install is needed to run it:

```
pip install pyinstaller
pyinstaller Dota2GuideInfoScraper.py --onefile
```

The result is in `dist/`. Do not have a `steam_api_key.txt` next to the script when building an exe to share.
