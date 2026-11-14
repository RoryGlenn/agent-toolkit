# Migrate and maintain Roster

## Upgrade a script from v1

Older team scripts read the filename from a positional argument and parsed a text
summary. In v2, pass the path as `--input` and include `--preview`. Switch consumers
to reading the `rows` and `duplicate_emails` fields from the JSON on standard output.
Update each caller against an archived copy of its input before switching the team's
shared script. Keep the original script available until its consumers are updated.

## Keep the regression samples current

The shipped sample uses fictional addresses and contains a duplicate that differs in
case. Keep that case when replacing sample rows. Roster trims whitespace and compares
email addresses without regard to case. It reports the number of repeated addresses
after their first occurrence.

Keep a sample with a UTF-8 byte order mark when checking exports from spreadsheet
tools. Also check separate files with a missing header and a blank email. Invalid input
reports an error on standard error and exits with status 2. Preview reports counts
without rewriting the input file or importing contacts.

## Package a new revision

Roster uses the Python standard library. Distribute `roster.py` and `sample.csv`
together for teams that run it from a copied folder. Use only fictional addresses when
sharing samples. Record the source revision with the copy so maintainers can identify
which CLI behavior a team has.
