# Scraping websites that don't have RSS

The result of this program is a rss feed, which you can retrieve from this URL: https://raw.githubusercontent.com/datengraben/local-feed-generator/master/atom.xml

## Rationale

Todays websites don't rely on RSS feeds that much as in the 90s or 00s.
So for checking if any recent content was published on a website, you have 
to manually check a website. Here I wan't to explore the most convenient way,
to create custom RSS feeds for sites you care about that don't have RSS.
And maybe also to share these kinds of feeds.

Because of this, I built this web-scraper based on Github Actions. 
As an example see the python script in the root, it contains urls for the city 
where I currently live.

This should give you a starting point to build your own website scraper for content that you care for.
Which will in turn provide you with an cronjob-automated way of an up-to-date RSS feed, that you can 
consume out of the comfort of your feed reader.
