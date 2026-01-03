# F1 Data Scraper

A Python web scraper that collects Formula 1 race data from the official F1 website (formula1.com) and saves it as CSV files.

## Features

- Scrapes race data from 2018-2025 F1 seasons
- Collects data for each Grand Prix including:
  - Qualifying results
  - Starting grid
  - Race results
  - Fastest laps
  - Pit stop summary
  - Sprint qualifying and results (when applicable)
- Excludes practice session data
- Organizes data in a clean folder structure by year and race
- Handles races with and without sprint events

## Requirements

- Python 3.7+
- Chrome browser installed

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/f1-data-scraper.git
cd f1-data-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Scrape a single year (e.g., 2025):
```python
python get_race_results.py
```

### Scrape multiple years:
Edit `get_race_results.py` and change the last section to:
```python
scraper.scrape_all_years(start_year=2018, end_year=2025)
```

## Output Structure

Data is saved in the following structure:
```
f1_data/
├── 2018/
│   ├── Australia/
│   │   ├── Qualifying.csv
│   │   ├── Starting_Grid.csv
│   │   ├── Race_Result.csv
│   │   ├── Fastest_Laps.csv
│   │   └── Pit_Stop_Summary.csv
│   ├── Bahrain/
│   └── ...
├── 2019/
├── 2020/
└── 2025/
```

## Notes

- The scraper runs in headless mode (no browser window)
- Includes polite delays between requests to avoid overloading the server
- Sprint sessions are only scraped if they exist for that race
- Estimated time: ~10-15 minutes per season, ~2-3 hours for all seasons (2018-2025)

## Disclaimer

This scraper is for educational and personal use only. Please respect Formula1.com's terms of service and robots.txt. Do not use this tool for commercial purposes or excessive scraping that could impact their servers.

## License

MIT License - feel free to use and modify as needed.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Author

Ronak Jung Rayamajhi

## Contact

**Ronak** - [@rronak](https://github.com/rronak)

**LinkedIn** - [Ronak Rayamajhi](https://www.linkedin.com/in/ronak120)

## Acknowledgments

- Data source: [Formula1.com](https://www.formula1.com/)
- Built with Selenium and BeautifulSoup4
