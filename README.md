# transcript scraper

this script scrapes the captions for ramit sethi's podcasts so we can train up an ai to be just like him

## setup

```bash
source podcast_scraper_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## usage

### podcast_scraper.py — main scraper

scrapes up to 100 episodes into a single combined file.

```bash
python podcast_scraper.py                          # all episodes (up to 100)
python podcast_scraper.py --start 200              # episode 200 and up
python podcast_scraper.py --end 100                # up to episode 100
python podcast_scraper.py --start 100 --end 200    # episodes 100–200
```

### batch_scraper.py — batch processor

no CLI args — edit these vars at the top of `main()`:

| var | default | what it does |
|-----|---------|--------------|
| `batch_size` | 20 | episodes per batch |
| `start_batch` | 4 | which batch to start from |
| `max_batches` | 9 | how many batches to run |

```bash
python batch_scraper.py
```

### utility / debug scripts

| script | what it does |
|--------|--------------|
| `count_episodes.py` | counts total available episodes and shows range |
| `analyze_api.py` | inspects the WordPress API response |
| `debug_links.py` | dumps all links from the main podcast page |
| `debug_regex.py` | tests URL regex patterns |
| `debug_transcript.py` | tests transcript extraction on episode 217 |

```bash
python count_episodes.py
```

## combine transcripts

```bash
cat transcripts/*.txt > combined.txt
```