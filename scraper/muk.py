import feedparser


def get_feed():
    feed = feedparser.parse('http://www.muk-giessen.de/feed/')

    return list(map(lambda entry:{
        'link': entry.link,
        'title': entry['title'],
        'date-posted': entry.published_parsed,
        'date-raw': entry.published,
        'author-name': feed['channel']['title'],
        'author-email': ''
        }, feed['entries']))

if __name__ == '__main__':
    get_feed()

