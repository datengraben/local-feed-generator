import requests
import bs4

URL = 'https://werkstattkirche.de'
POSTS = URL + '/neuigkeiten/'
EVENTS = URL + '/category/veranstaltung'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

def get_text(url):
    return bs4.BeautifulSoup(requests.get(url.strip(), headers=headers, timeout=10).text)



# scrape posts
resp = requests.get(POSTS)
posts = map(lambda x: (x.text, x['href']), bs4.BeautifulSoup(resp.text).select('article'))

# scrape events
resp = requests.get(EVENTS)
events = map(lambda x: (x.text, x['href']), bs4.BeautifulSoup(resp.text).select('article'))

# put posts into rss
create_rss(map(to_rss_item_from_html, posts))

# put events into ical
create_ical(map(to_ical_item_from_html, events))