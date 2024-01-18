from flask import Flask, render_template, redirect
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup as bs
import feedparser
import logging
import requests
from db import Entry
import yaml
from io import BytesIO
from PIL import Image


app = Flask(__name__)


logging.basicConfig(level=logging.INFO)


# RSS feed URL
with open('rss_feeds.yml', 'r') as f:
    rss_feeds = yaml.load(f, Loader=yaml.FullLoader).get('rss_feeds')


def add_entry(channel_name, link, title, summary, author, image_url, published):
    now: datetime = datetime.now()
    (Entry
     .insert(channel_name=channel_name,
             link=link,
             title=title,
             summary=summary,
             author=author,
             image_url=image_url,
             published=published,
             created=now
             )
     .on_conflict_ignore(True)
     .execute()
     )


def get_entry(link):
    return (Entry
            .select()
            .where(Entry.link == link)
            .limit(1)
            )


def get_entries():
    return (Entry
            .select()
            .order_by(Entry.published.desc())
            .limit(20)
            )


def update_entry():
    for meta in rss_feeds:
        logging.info(meta['channel_name'])
        feed = feedparser.parse(meta['url'])
        for entry in feed.entries:

            if get_entry(entry.link):
                continue

            entry = refine_entry(entry)
            add_entry(meta['channel_name'],
                      entry.link,
                      entry.title,
                      entry.summary,
                      entry.author,
                      entry.image_url,
                      entry.published)


def refine_entry(entry):
    # 날짜 포맷 맞추기
    if entry.get('published') is not None:
        published = entry.get('published')
    else:
        published = entry.get('updated')
    published = parser.parse(published).strftime("%Y-%m-%d %H:%M:%S")

    # 본문의 HTML TAG 제거 및 대표 이미지 추출
    soup = bs(entry.get('summary'), 'html.parser')

    # 본문 요약
    summary = soup.get_text(strip=True)

    # 본문 수집
    body = bs(requests.get(entry.link).text, 'html.parser')

    # 대표이미지 생성
    image_url = None
    if soup.select_one('img') is not None:
        image_url = soup.select_one('img').get('src')
    else:
        if body.select_one('img') is not None:
            images = body.find_all('img')
            for image in images:
                src = image.get('src')
                if not src:
                    continue
                # 원하는 사이즈가 없을 수 있기 때문에, 첫 번째 이미지를 기본 이미지로 지정
                desired_size = 400
                image_url = image.get('src')

                # TODO SVG처리
                # TODO 이미지 상대 경로 변환
                try:
                    response = requests.get(src)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching image from {src}: {e}")
                    continue

                img_data = BytesIO(response.content)
                try:
                    pil_img = Image.open(img_data)
                except OSError as e:
                    print(f"Error opening image from {src}: {e}")
                    continue

                width, height = pil_img.size
                if max(width, height) < desired_size:
                    continue

                image_url = image.get('src')
                break

    entry.published = published
    entry.image_url = image_url
    entry.summary = summary

    return entry


@app.route("/")
def index():
    # update_entry()
    entries = get_entries()

    return render_template("index.html", entries=entries)


@app.route("/rss")
def rss():
    entries = get_entries()

    return render_template("rss.xml", entries=entries)


@app.route("/refresh")
def refresh():
    update_entry()

    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)