#!/usr/bin/env python3

# Copyright (c) Dom Rodriguez 2020
# Copyright (c) Andros Fenollosa 2022
# Licensed under the Apache License 2.0

import os
import sys
import feedparser
import logging
import listparser
from os import environ
from feedgen.feed import FeedGenerator
import json
import yaml


# Varaibles

log = None
CONFIG_PATH = "config.yml" #this is for path, as can't be hardcoded in later on
LOG_LEVEL = environ.get("SR_LOG_LEVEl", "ERROR")
fg = None
FEED_OUT_PATH = None
FEED_LIST_PATH = None
FEEDS = []
CFG = None


def setup_logging() -> None:
    """
    This function intiialises the logger framework.
    """
    global log

    log = logging.getLogger(__name__)
    log.setLevel(LOG_LEVEL)
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    log.addHandler(ch)

    return None


def get_url_from_feed(config):
    """
    This function returns the URL from a feed.
    """
    return config["url"] + "/" + config["output"]


def init_feed() -> None:
    """
    This function initialises the RSS feed with the
    correct attributes.
    """
    log.debug("Initialising the feed...")

    global fg

    try:
        fg = FeedGenerator()
        # Setup [root] feed attributes
        fg.id(get_url_from_feed(CONFIG))
        fg.title(CONFIG["title"])
        fg.generator("RSSingle/v1.0.0") #you may change whatever you like
        fg.link(href=get_url_from_feed(CONFIG), rel="self")
        fg.subtitle(CONFIG["description"])
        fg.language("en") #you may change language if more than 61.8% is no English
    except:
        log.error("Error initialising the feed!")
        sys.exit(1)

    log.debug("Feed initialised!")

    return None


def parse_rss_feed(url) -> feedparser.FeedParserDict:
    log.debug("Parsing RSS feed..")

    try:
        # Hopefully this should parse..
        return feedparser.parse(url)
    except Exception:
        log.warning("Failed to parse RSS feed.")
        # Now, we could handle gracefully.


def main():
    log.debug("Loading feed list into memory..")

    log.debug("Iterating over feed list..")

    for feed in CONFIG["feeds"]:
        rss = parse_rss_feed(feed)
        entries = rss.get("entries")
        log.debug("Iterating over [input] feed entries..")
        for entry in entries:
            log.debug("New feed entry created.")

            fe = fg.add_entry()

            log.debug("Working on new feed entry..")

            try:
                fe.id(entry["id"])
            except:
                # Deifnitely weird...
                log.warning("Empty id attribute, defaulting..")
                fe.id("about:blank")

            try:
                fe.title(entry["title"])
            except:
                # OK, this is a definite malformed feed!
                log.warning("Empty title attribute, defaulting..")
                fe.title("Unspecified")

            try:
                fe.link(href=entry["link"])
            except:
                # When we have a empty link attribute, this isn't ideal
                # to set a default value.. :/
                log.warning("Empty link attribute, defaulting..")
                fe.link(href="about:blank")

            try:
                if entry["sources"]["authors"]:
                    for author in entry["sources"]["authors"]:
                        fe.author(author)
                elif entry["authors"]:
                    try:
                        for author in entry["authors"]:
                            fe.author(author)
                    except:
                        log.debug("Oh dear, a malformed feed! Adjusting.")
                        # This is a ugly hack to fix broken feed entries with the author attribute!
                        author["email"] = author.pop("href")
                        fe.author(author)
            except:
                # Sometimes we don't have ANY author attributes, so we
                # have to set a dummy attribute.
                log.warning("Empty authors attribute, defaulting..")
                #fe.author({"name": "Unspecified", "email": "unspecified@example.com"})

            try:
                if entry["summary"]:
                    fe.summary(entry["summary"])
                    fe.description(entry["summary"])
                elif entry["description"]:
                    fe.description(entry["description"])
                    fe.summary(entry["description"])
                    fe.content(entry["description"])
            except:
                # Sometimes feeds don't provide a summary OR description, so we
                # have to set an empty value.
                # This is pretty useless for a feed, so hopefully we
                # don't have to do it often!
                log.warning("Empty description OR summary attribute, defaulting..")
                fe.description("Unspecified")
                fe.summary("Unspecified")

            try:
                if entry["published"]:
                    try:
                        fe.published(entry["published"])
                        fe.updated(entry["published"])
                    except:
                        fe.published("1970-01/01T00:00:00+00:00")
                        fe.updated("1970-01/01T00:00:00+00:00")
                        continue
            except:
                # Sometimes feeds don't even provide a publish date, so we default to
                # the start date &time of the Unix epoch.
                log.warning("Empty publish attribute, defaulting..")
                fe.published("1970-01/01T00:00:00+00:00")
                fe.updated("1970-01/01T00:00:00+00:00")


if __name__ == "__main__":
    setup_logging()
    log.debug("Initialising...")

    global CONFIG

    with open( CONFIG_PATH , "r") as file:
        CONFIG = yaml.safe_load(file)

    log.debug("Assiging variables..")
    try:
        # Configuration is specified with configure variables.
        log.debug("Assignment attempt: output")
        FEED_OUT_PATH = CONFIG["output"] #That's so tricky, the output should be modified to another path.
    except KeyError:
        log.error("*** Configure variable missing! ***")
        log.error("`output` variable missing.")
        log.error("This program will NOT run without that set.")
        sys.exit(1)

    try:
        FEED_LIST_PATH = CONFIG["url"]
    except:
        log.error("*** Configure variable missing! ***")
        log.error("`url` variable missing.")
        sys.exit(1)

    try:
        FEED_LIST_PATH = CONFIG["feeds"]
    except:
        log.error("*** Configure variable missing! ***")
        log.error("`feeds` variable missing.")
        sys.exit(1)

    init_feed()

    log.debug("Begin processing feeds...")
    main()

    fg.rss_file(FEED_OUT_PATH)
