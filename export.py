import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List

import arrow
from functional import seq

sys.path.append("../anki/pylib")
from anki.storage import Collection
from anki import template
import anki


# Initial version is taken from
# https://www.juliensobczak.com/write/2016/12/26/anki-scripting.html#CaseStudy:ExportingflashcardsinHTML


def extract_media(text, output_dir, profile_dir):
    regex = r'<img src="(.*?)"\s?/?>'
    pattern = re.compile(regex)

    src_media_folder = os.path.join(profile_dir, "collection.media/")
    dest_media_folder = os.path.join(output_dir, "medias")

    # Create target directory if not exists
    if not os.path.exists(dest_media_folder):
        os.makedirs(dest_media_folder)

    for (media) in re.findall(pattern, text):
        src = os.path.join(src_media_folder, media)
        dest = os.path.join(dest_media_folder, media)
        shutil.copyfile(src, dest)

    text_with_prefix_folder = re.sub(regex, r'<img src="medias/\1" />', text)

    return text_with_prefix_folder


def get_card_ids(deck_manager, did, children=False, include_from_dynamic=False):
    deck_ids = [did] + ([deck_id for _, deck_id in deck_manager.children(did)] if children else [])

    request = "select id from cards where did in {}" + ("or odid in {}" if include_from_dynamic else "")
    parameters = (anki.utils.ids2str(deck_ids),) + ((deck_manager.utils.ids2str(deck_ids),)
                                                    if include_from_dynamic else tuple())

    return deck_manager.col.db.list(request.format(*parameters))


# todo cloze needs work too, I imagine I can translate it to the syntax used in the anki import plugin
def js():
    return """function addBrackets() {
    const elements = document.getElementsByClassName("cloze")
    for (element of elements) {
        element.innerHTML = `{${element.innerHTML}}`
    }
}
    """


def get_aggregate_html(css: List[str], cards: List[str], deck_name: str = ""):
    css_str = '\n'.join(set(css))
    cards_str = '\n'.join(cards)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{deck_name}</title>
  <style>
  {css_str}
  </style>
  <script>{js()}</script> 
</head>
<body onload="addBrackets();">
  {cards_str} </body>
</html>"""


def get_card_date(card, base_timestamp):
    """
     -- Due is used differently for different card types:
     --   new: note id or random int
     --   due: integer day, relative to the collection's creation time
     --   learning: integer timestamp

     type            integer not null,
      -- 0=new, 1=learning, 2=due, 3=filtered

     Need to take into account dates in the past, (probably should map to today)
    """
    now = arrow.now()
    if card.type == 0:
        return None
    elif card.type == 1:
        return now
    else:
        due_date = arrow.get(base_timestamp).shift(days=card.due)
        return max(due_date, now)


def roam_date(date):
    return f"[[{date.format('MMMM Do, YYYY')}]]"


def format_tags(tags):
    return seq(tags).map(lambda t: f'[[{t}]]').make_string(" ")


def insert_metadata(answer: str, metadata):
    for match in re.finditer("</\\w+>", answer):
        pass

    if match:
        return answer[:match.start()] + metadata + answer[match.start():]
    return answer + match


class HtmlExporter:
    def __init__(self, deck_name: str, profile_directory: str):
        self.deck_name = deck_name
        self.profile_directory = profile_directory
        self.collection = self.load_collection()
        self.css_fragments = ["div {display: inline;}"]
        self.card_fragments = []

    def export(self, output_dir):
        for card in get_cards(self.collection, self.deck_name):
            note = self.collection.getNote(card.nid)
            self.css_fragments.append(self.collection.models.get(note.mid)['css'])

            rendering = template.render_card(self.collection, card, note, False)

            answer = extract_media(rendering.answer_text, output_dir, self.profile_directory)
            self.card_fragments.append(self.get_card_fragment(answer, card, note.tags))

        print(f"Exporting {len(self.card_fragments)} cards")

        Path(output_dir).joinpath(self.deck_name).with_suffix('.html') \
            .write_text(get_aggregate_html(self.css_fragments, self.card_fragments, self.deck_name))

    # todo the extra info ending up in a separate block is a big problem -_-
    # also image export does not really work - it embeds the link and not copies the image
    def get_card_fragment(self, answer, card, tags):
        date = roam_date(get_card_date(card, self.collection.crt))
        metadata = format_tags(tags) + f" [[[[interval]]::{card.ivl}]] [[[[factor]]::{card.factor / 1000}]] {date}"

        return f"""<div class="card"> {insert_metadata(answer, metadata)} </div>"""

    def load_collection(self):
        collection_path = os.path.join(self.profile_directory, "collection.anki2")
        return Collection(collection_path, log=True, lock=False)


def get_cards(col, deck_name):
    return seq(get_card_ids(col.decks, col.decks.id(deck_name))) \
        .map(col.getCard) \
        .filter(is_not_suspended) \
        .to_list()


def is_not_suspended(card):
    return card.queue != -1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('deck_name', help='Deck Name')
    parser.add_argument('profile_directory', help='The Anki profile directory')
    parser.add_argument('-o', '--output', help='Deck Name', default=Path(__file__).parent.resolve())
    args = parser.parse_args()
    print(args)

    HtmlExporter("Book Highlights::Algorithms to Live By", args.profile_directory).export(args.output)
