# rss-filter

Filtered derStandard Newsroom feed: https://dweinber.github.io/rss-filter/newsroom.xml

Removed:
- Diskurs items (opinion/community) and old pinned posts
- Sport items, except World/European Championship (WM/EM) stories
- Puzzles and quizzes (Sudoku, Schieberätsel, Wortsuche, …)

Rebuilt every 30 minutes by GitHub Actions. Adjust `EXCLUDE` / `TITLE_EXCLUDE` in `filter_feed.py`.
