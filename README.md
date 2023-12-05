# Scraping websites that don't have RSS

Todays websites don't rely on RSS feeds that much as in the 90s or 00s.
So for checking if any recent content was published on a website, you have 
to manually check a website. Because of this, I built this web-scraper based on
Github Actions. As an example see the python script in the root, it contains urls for 
the city where I currently live.

This should give you a starting point to build your own website scraper for content that you care for.
Which will in turn provide you with an cronjob-automated way of an up-to-date RSS feed, that you can 
consume out of the comfort of your feed reader.
