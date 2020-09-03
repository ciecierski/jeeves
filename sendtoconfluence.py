#!/usr/bin/env python3

# From https://github.com/ralphbean/markdown-to-confluence/blob/master/bin/markdown-to-confluence.py
# used in https://gitlab.cee.redhat.com/exd/inventory/-/blob/master/.gitlab-ci.yml
# resulting in https://docs.engineering.redhat.com/display/~jboggs/confluence

import argparse
import hashlib
import logging
import os
import sys

# import pypandoc
import requests

BIN = os.path.dirname(__file__)

username = os.environ.get('CONFLUENCE_USERNAME')
password = os.environ.get('CONFLUENCE_PASSWORD')

session = requests.Session()
session.verify = False
session.auth = (username, password)


def find_page(url, space, page_title):
    querystring = f"cql=title='{page_title}' and space='{space}'"
    search_url = f"{url}/rest/api/content/search?{querystring}"
    resp = session.get(search_url)
    resp.raise_for_status()
    if len(resp.json()['results']) > 0:
        return resp.json()['results'][0]
    else:
        return None


def get_page_info(url, page_id):
    url = f"{url}/rest/api/content/{page_id}?expand=ancestors,version"
    resp = session.get(url)
    resp.raise_for_status()
    return resp.json()


def create_page(url, space, page_title, ancestor=None):
    data = {
        "type": "page",
        "title": page_title,
        "space": {"key": space.strip('"')},
        "body": {
            "storage": {"value": "<p>Empty page</p>",
                        "representation": "storage"}
        },
    }

    if ancestor:
        data['ancestors'] = [{"id": ancestor}]

    url = f"{url}/rest/api/content/"
    resp = session.post(url, json=data)

    if not resp.ok:
        print("Confluence response: \n", resp.text)

    resp.raise_for_status()

    return resp.json()


def update_page(url, page_id, markup, comment):
    info = get_page_info(url, page_id)
    url = f"{url}/rest/api/content/{page_id}"
    updated_page_version = int(info["version"]["number"] + 1)

    data = {
        'id': str(page_id),
        'type': 'page',
        'title': info['title'],
        'version': {
            'number': updated_page_version,
            'minorEdit': True,
            'message': comment,
        },
        'body': {'storage': {'representation': 'storage', 'value': markup}},
    }
    resp = session.put(url, json=data)
    if not resp.ok:
        print("Confluence response: \n", resp.json())
    resp.raise_for_status()
    return resp.json()


def getargs():
    """ Parse args from the command-line.  """
    parser = argparse.ArgumentParser(description='Publish docs')
    required = parser.add_argument_group('required named arguments')
    required.add_argument('--confluence-url',
                        help='URL to publish to confluence.')
    required.add_argument('--confluence-space',
                        help='Space to publish to confluence.')
    required.add_argument('--confluence-ancestor',
                        help='The ancestor confluence page.')
    required.add_argument('--path', help='Path to the html file to publish.')
    required.add_argument('--confluence-pagename',
                        help='Name of the confluence page to edit.')
    args = parser.parse_args()

    if not args.confluence_url:
        print("--confluence-url is required.")
        sys.exit(1)
    if not args.confluence_space:
        print("--confluence-ancestor is required.")
        sys.exit(1)
    if not args.confluence_space:
        print("--confluence-space is required.")
        sys.exit(1)
    if not username:
        print("CONFLUENCE_USERNAME must be defined to publish.")
        sys.exit(1)
    if not args.path:
        print("--path is required.")
        sys.exit(1)
    if not password:
        print("CONFLUENCE_PASSWORD must be defined to publish.")
        sys.exit(1)

    return args


def publish(args):

    def get_or_create_page():
        pagename = args.confluence_pagename
        if not pagename:
            return
        print("Searching for %s" % pagename, file=sys.stderr)
        page = find_page(
            url=args.confluence_url,
            space=args.confluence_space,
            page_title=pagename,
        )
        if not page:
            print("Creating %s" % pagename, file=sys.stderr)
            ancestor = find_page(url=args.confluence_url,
                                 space=args.confluence_space,
                                 page_title=args.confluence_ancestor)
            page = create_page(
                url=args.confluence_url,
                space=args.confluence_space,
                page_title=pagename,
                ancestor=ancestor['id'],
            )
        return page

    page = get_or_create_page()
    info = get_page_info(args.confluence_url, page['id'])
    current_digest = info['version']['message']
    html = "<p>Oups, something went wrong</p>"
    with open(args.path) as x:
        html = x.read()
    digest = hashlib.sha256(html.encode('utf-8')).hexdigest()
    if digest != current_digest:
        print("Updating %s" % page['title'], file=sys.stderr)
        update_page(args.confluence_url, page['id'], html, digest)
    else:

        print("No modification to %s, skipping." % page['title'],
              file=sys.stderr)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = getargs()
    publish(args)
