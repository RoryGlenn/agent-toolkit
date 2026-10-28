# Roster v2 working notes

Runs locally with Python 3.10 or newer, using only the standard library. There is no installation package and no network access in this utility. Support analysts receive roster.py and sample.csv together. Preview does not import contacts into the separate customer system. These supplied examples contain fictional addresses.

Editorial convention: say "contact file" in prose; preserve exact file and command names. Use a friendly, direct tone. Avoid calling contacts "entities" or "records" in this introductory guide. The heading should promise a validation task.

Old brainstorming: maybe `roster upload --dry-run` would be nice eventually. Someone once suggested that we might validate email deliverability against a server. Neither proposal is implemented. The current implementation is roster.py.

Engineering history: we discussed a custom parser, then chose the standard CSV module. It uses dictionaries internally, a detail that may interest maintainers. A future async pipeline has no committed timeline.
