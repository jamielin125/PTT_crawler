import requests
from bs4 import BeautifulSoup
import urllib.parse
from multiprocessing import Pool
import time
import os
import re

INDEX_URL = 'https://www.ptt.cc/bbs/Beauty/index.html'


def get_postslist(url):

	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	articles = soup.find_all('div', 'r-ent')

	posts = []

	for article in articles:
		title_meta = article.find('div', 'title').find('a')
		if title_meta:
			posts.append({
				'title' : title_meta.getText().strip(),
				'link'  : title_meta['href'],
				'push' : article.find('div', 'nrec').getText(),
				'date' : article.find('div', 'date').getText(),
				'author' : article.find('div', 'author').getText(),
				})
			# print(title, link, 'push:' ,push, date, author)

	next_link = soup.find('div', 'btn-group btn-group-paging').find_all('a', 'btn')[1].get('href')

	return posts, next_link

def get_page_meta(page):
	all_posts = []
	page_url = INDEX_URL

	for i in range(page):
		posts, link = get_postslist(page_url)
		all_posts += (posts)
		page_url = urllib.parse.urljoin(INDEX_URL, link)

	return all_posts


def get_artilces(posts_meta):
	posts_link = [ meta['link'] for meta in posts_meta]
	with Pool(processes = 8) as pool:
		contents = pool.map(get_articles_content, posts_link)
		return contents


def get_articles_content(link):
	url = urllib.parse.urljoin(INDEX_URL, link)
	response = requests.get(url)
	return response.text


def parse(dom):
	soup = BeautifulSoup(dom, 'html.parser')
	links = soup.find(id='main-content').find_all('a')
	img_urls = []
	for link in links:
		if re.match(r'^https?://(i.)?(m.)?imgur.com', link['href']):
			img_urls.append(link['href'])	
	return img_urls

def save(img_urls, title):
	if img_urls:
		try:
			dname = title.strip()  # 用 strip() 去除字串前後的空白
			os.makedirs(dname)
			for img_url in img_urls:
				if img_url.split('//')[1].startswith('m.'):
					img_url = img_url.replace('//m.', '//i.')
				if not img_url.split('//')[1].startswith('i.'):
					img_url = img_url.split('//')[0] + '//i.' + img_url.split('//')[1]
				if not img_url.endswith('.jpg'):
					img_url += '.jpg'
				fname = img_url.split('/')[-1]
				urllib.request.urlretrieve(img_url, os.path.join(dname, fname))
		except Exception as e:
			print(e)




start_time = time.time()

posts_meta = get_page_meta(1)   # 1 page
# print(posts_meta)
articles = get_artilces(posts_meta)

print('total spend: %f seconds' % (time.time() - start_time))


for posts, content in zip(posts_meta, articles):
	print('{0} {1} {2}, total {3} words'.format(posts['date'], posts['author'], posts['title'], len(content)))
	# os.makedirs(posts['title'])

	url = urllib.parse.urljoin(INDEX_URL, posts['link'])
	response = requests.get(url)
	imgs = parse(response.text)
	save(imgs, posts['title'])








