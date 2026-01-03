import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class F1DataScraper:
    def __init__(self, output_dir="f1_data"):
        self.output_dir = output_dir
        self.base_url = "https://www.formula1.com/en/results"
        self.driver = None
        self.setup_driver()
        os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist
        
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run browser in background (no window)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")  # Mimic real browser
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
    def get_races_for_year(self, year):
        """Get all races for a specific year"""
        url = f"{self.base_url}/{year}/races"
        print(f"\nFetching races for {year}...")
        print(f"URL: {url}")
        
        self.driver.get(url)
        time.sleep(4)  # Wait for JavaScript to load the page content
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        races = []
        
        # Find the main results table (F1's new design uses Table-module class)
        table = soup.find('table', class_=lambda x: x and 'Table-module' in str(x))
        
        if table:
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                print(f"Found {len(rows)} rows in table")
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 1:
                        first_col = cols[0]  # First column contains race name and link
                        race_link = first_col.find('a')
                        
                        if race_link and 'href' in race_link.attrs:
                            # Get the full text which might include flag text
                            race_name = race_link.text.strip()
                            
                            # The race name often has format like "Flag of CountryGrand Prix Name"
                            # or just "CountryGrand Prix Name" - we want just the Grand Prix part
                            # Let's use the URL slug instead which is cleaner
                            race_href = race_link['href']
                            
                            # Extract clean name from URL (e.g., "australia", "bahrain")
                            parts_temp = race_href.split('/')
                            if 'races' in parts_temp and len(parts_temp) > parts_temp.index('races') + 2:
                                url_race_name = parts_temp[parts_temp.index('races') + 2]  # Get race slug from URL
                                # Capitalize and format nicely
                                race_name = url_race_name.replace('-', ' ').title()
                            else:
                                # Fallback: clean up the text name
                                race_name = race_name.replace('Flag of ', '').strip()
                            
                            parts = race_href.split('/')
                            if 'races' in parts:  # Store race info for later use
                                races.append({
                                    'name': race_name,
                                    'year': year,
                                    'url': race_href,
                                    'parts': parts
                                })
        
        print(f"Found {len(races)} races for {year}")
        if races and len(races) > 0:
            print(f"First race: {races[0]['name']}")
        
        return races
    
    def check_session_exists(self, url):
        """Check if a session page exists by looking for a table"""
        try:
            full_url = f"https://www.formula1.com{url}" if not url.startswith('http') else url
            self.driver.get(full_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table', class_=lambda x: x and 'Table-module' in str(x))
            
            return table is not None
        except:
            return False
    
    def scrape_session_data(self, url, session_name):
        """Scrape data from a specific session"""
        try:
            full_url = f"https://www.formula1.com{url}" if not url.startswith('http') else url
            self.driver.get(full_url)
            time.sleep(3)  # Wait for page to load
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table', class_=lambda x: x and 'Table-module' in str(x))
            
            if not table:  # No table found = session doesn't exist or no data
                return None
            
            # Extract headers
            headers = []
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.text.strip() for th in header_row.find_all('th')]
            
            # Extract data rows
            data = []
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    row_data = [col.text.strip() for col in cols]
                    if row_data:
                        data.append(row_data)
            
            if data and headers:
                # Make sure data columns match headers (avoid DataFrame errors)
                if len(headers) == len(data[0]):
                    df = pd.DataFrame(data, columns=headers)
                    return df
            
            return None
            
        except Exception as e:
            return None
    
    def scrape_race_sessions(self, race, year):
        """Scrape selected sessions for a race (no practice sessions)"""
        race_name = race['name'].replace(' ', '_').replace('/', '-')  # Clean name for folder
        race_dir = os.path.join(self.output_dir, str(year), race_name)
        os.makedirs(race_dir, exist_ok=True)
        
        print(f"\n  Scraping: {race['name']}")
        
        # Get the base URL parts to build session URLs
        parts = race['parts']
        race_idx = parts.index('races')
        race_id = parts[race_idx + 1]  # Numeric race ID
        race_slug = parts[race_idx + 2]  # Race name slug (e.g., "australia")
        
        base_path = f"/en/results/{year}/races/{race_id}/{race_slug}"
        
        # Define sessions to scrape (NO PRACTICE SESSIONS)
        sessions = {
            'sprint-qualifying': 'Sprint_Qualifying',
            'sprint': 'Sprint_Results',
            'qualifying': 'Qualifying',
            'starting-grid': 'Starting_Grid',
            'fastest-laps': 'Fastest_Laps',
            'pit-stop-summary': 'Pit_Stop_Summary',
            'race-result': 'Race_Result'
        }
        
        for session_key, session_name in sessions.items():
            session_url = f"{base_path}/{session_key}"
            
            print(f"    - {session_name}", end=" ")
            df = self.scrape_session_data(session_url, session_name)
            
            if df is not None and not df.empty:
                filename = os.path.join(race_dir, f"{session_name}.csv")
                df.to_csv(filename, index=False, encoding='utf-8')
                print(f"✓ ({len(df)} rows)")
            else:
                # Only show ✗ for sprint sessions (they may not exist)
                if 'sprint' in session_key.lower():
                    print(f"✗ (no sprint)")
                else:
                    print(f"✗")
            
            time.sleep(1)  # Be polite to the server - don't send requests too fast
    
    def scrape_all_years(self, start_year=2018, end_year=2024):
        """Scrape data for all years"""
        try:
            for year in range(start_year, end_year + 1):
                print(f"\n{'='*60}")
                print(f"YEAR: {year}")
                print(f"{'='*60}")
                
                races = self.get_races_for_year(year)
                
                for i, race in enumerate(races, 1):
                    print(f"\n[{i}/{len(races)}]", end=" ")
                    self.scrape_race_sessions(race, year)
                
                print(f"\nCompleted {year}")
                
        finally:
            self.close()
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("\n\nBrowser closed. Scraping complete!")

# Usage
if __name__ == "__main__":
    scraper = F1DataScraper(output_dir="f1_data")
    
    # Scrape 2025 season
    print("Scraping 2025 F1 Season...")
    print("Sessions included: Qualifying, Starting Grid, Sprint (if exists), Race Result, Fastest Laps, Pit Stops")
    print("Practice sessions: EXCLUDED")
    
    scraper.scrape_all_years(start_year=2025, end_year=2025)
    
    print("\n✓ All done! Check the 'f1_data/2025/' folder for all race data")
    
    # To scrape multiple years (2018-2025), change to:
    # scraper.scrape_all_years(start_year=2018, end_year=2025)