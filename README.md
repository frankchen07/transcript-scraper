# transcript scraper

this script scrapes the captions for ramit sethi's podcasts so we can train up an ai to be just like him

how to use it:

```bash
source podcast_scraper_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python podcast_scraper.py
deactivate
cat transcripts/*.txt > combined.txt
```