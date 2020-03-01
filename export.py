import os
import re
import shutil
import sys
from pathlib import Path

import arrow
from functional import seq

sys.path.append("../anki/pylib")
from anki.storage import Collection
from anki import template
import anki

# Initial version is taken from
# https://www.juliensobczak.com/write/2016/12/26/anki-scripting.html#CaseStudy:ExportingflashcardsinHTML
PROFILE_HOME = "/Users/sitalov/Library/Application Support/Anki2/Stvad"
OUTPUT_DIRECTORY = "/tmp/algothml"


def extract_media(text):
    regex = r'<img src="(.*?)"\s?/?>'
    pattern = re.compile(regex)

    src_media_folder = os.path.join(PROFILE_HOME, "collection.media/")
    dest_media_folder = os.path.join(OUTPUT_DIRECTORY, "medias")

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


def get_card_html(css, answer, card, col):
    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Card Answer</title>
  <style>
  {css}
  </style>
</head>
<body>
  <div class="card">
  {answer} 
    [[[[interval]]::{card.ivl}]] [[[[factor]]::{card.factor / 1000}]] {roam_date(get_card_date(card, col.crt))}
  </div>
</body>
</html>"""
    return html


def get_card_date(card, base_timestamp):
    """
     -- Due is used differently for different card types:
     --   new: note id or random int
     --   due: integer day, relative to the collection's creation time
     --   learning: integer timestamp

     type            integer not null,
      -- 0=new, 1=learning, 2=due, 3=filtered

      queue           integer not null,
      -- -3=user buried(In scheduler 2),
      -- -2=sched buried (In scheduler 2),
      -- -2=buried(In scheduler 1),
      -- -1=suspended,
      -- 0=new, 1=learning, 2=due (as for type)
      -- 3=in learning, next rev in at least a day after the previous review

     Need to take into account dates in the past, (probably should map to today)
     Also suspended cards?
    """
    now = arrow.now()
    if card.type == 0:
        return None
    elif card.type == 1:
        return now
    else:
        # Todo handle in the past
        due_date = arrow.get(base_timestamp).shift(days=card.due)
        return max(due_date, now)


def roam_date(date):
    return f"[[{date.format('MMMM Do, YYYY')}]]"


def export_cards(deck_name="Book Highlights::Algorithms to Live By"):
    col = load_collection()

    for card in get_cards(col, deck_name):
        note = col.getNote(card.nid)
        tags = note.tags  # todo

        rendering = template.render_card(col, card, note, False)

        # question = rendering['q']
        # answer = rendering['a']
        answer = rendering.answer_text

        # question = extractMedia(question)
        answer = extract_media(answer)

        css = col.models.get(note.mid)['css']

        html = get_card_html(css, answer, card, col)

        card_filename = f"card-{card.id}.html"
        Path(OUTPUT_DIRECTORY).joinpath(card_filename).write_text(html)


def load_collection():
    collection_path = os.path.join(PROFILE_HOME, "collection.anki2")
    return Collection(collection_path, log=True)


def get_cards(col, deck_name):
    return seq(get_card_ids(col.decks, col.decks.id(deck_name))) \
        .map(col.getCard) \
        .filter(is_not_suspended) \
        .to_list()


def is_not_suspended(card):
    return card.queue != -1


if __name__ == '__main__':
    export_cards()
