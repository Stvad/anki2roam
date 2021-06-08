# anki2roam

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Stvad/anki2roam/master?urlpath=voila/render/anki2roam.ipynb)

A tool that allows you to export your Anki deck into a Markdown or HTML page with the SRS metadata preserved
in the format that [Roam Toolkit](https://github.com/roam-unofficial/roam-toolkit) understands.

---
The development is supported by <a href="https://roam.garden/"> <img src="https://roam.garden/static/logo-2740b191a74245dc48ee30c68d5192aa.svg" height="50" /></a> - a service that allows you to publish your Roam notes as a beautiful static website (digital garden)

---

Example of the exported cards (first one Q&A card and second one is a Cloze card):
```
 -
  Composite Simpler Than the Sum of Its Parts
     The API of a composite object should not be more complicated than that of any of its components.   
     All objects in a system, except for primitive types built into the language, are composed of other objects. When composing objects into a new type, we want the new type to exhibit simpler behavior than all of its component parts considered together. The composite object’s API must hide the existence of its component parts and the interactions between them, and expose a simpler abstraction to its peers. Think of a mechanical clock: It has two or three hands for output and one pull-out wheel for input but packages up dozens of moving parts.   
  Growing Object Oriented Software guided by Tests p#54
  [[[[interval]]:433]] [[[[factor]]:2.5]] [[July 23rd, 2020]]
 -
  It can be useful to create your own {{c1:TestCase subclass}} (with helpers, customized asserts, etc). This will allow you to avoid code duplication and make your tests more domain-specific.
  https://www.youtube.com/watch?v=FxSsnHeWQBY
  [[[[interval]]:541]] [[[[factor]]:2.2]] [[June 10th, 2020]] [[python]] [[software-engineering]] [[testing]]
```

## How to use it

### Web (recommended)

Go to  [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Stvad/anki2roam/master?urlpath=voila/render/anki2roam.ipynb)  and follow the instructions (it can take a bit to load the first time)

### CLI
#### Prerequisites

1. Clone the repository
1. Install Python and Pip
  - https://docs.python-guide.org/starting/installation/
  - https://packaging.python.org/tutorials/installing-packages/
1. Install dependencies : `pip3 install -r requirements.txt`

#### Running the command

```bash
usage: anki2roam.py [-h] [-o OUTPUT] deck_name profile_directory

positional arguments:
  deck_name             Deck Name
  profile_directory     The Anki profile directory

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Deck Name
```

**Example:** `python3 export.py "Software::OS X" "/Users/sitalov/Library/Application Support/Anki2/Stvad"`

## How it works

- If cards are **overdue** their review date would be set to the date of the export.
- Tags are exported and appended in the Wikilink format beside the SRS metada 
  (see Cloze card example above)
- Cloze occlusions preserve Anki syntax for them which by accident also works within Roam :) 
- Only cards directly in the deck are exported (ones from sub-decks are not included)

## Known issues
- The Cloze cards with multiple occlusions lead to duplicated entries in the export each one with the 
different set of SRS metadata
