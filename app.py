from flask import Flask, render_template, redirect
from datetime import datetime
from dateutil import parser
import feedparser
import logging
from db import Entry
import yaml


app = Flask(__name__)


logging.basicConfig(level=logging.INFO)

# RSS feed URL
with open('rss_feeds.yml', 'r') as f:
    rss_feeds = yaml.load(f, Loader=yaml.FullLoader).get('rss_feeds')


def add_entry(channel_name, title, summary, link, published):
    now = datetime.now()
    (Entry
     .insert(channel_name=channel_name, title=title, summary=summary, link=link, published=published, created=now)
     .on_conflict_ignore(True)
     .execute()
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
            if entry.get('published') is not None:
                published = entry.get('published')
            else:
                published = entry.get('updated')
            published = parser.parse(published).strftime("%Y-%m-%d %H:%M:%S")
            add_entry(meta['channel_name'], entry.title, entry.summary, entry.link, published)


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