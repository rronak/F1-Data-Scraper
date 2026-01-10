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
        self.output_dir = output_dir  # Base directory where all scraped CSV files will be saved
        self.base_url = "https://www.formula1.com/en/results"  # Base F1 results URL
        self.driver = None  # Selenium WebDriver instance
        self.setup_driver()  
        os.makedirs(output_dir, exist_ok=True) 
        
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run Chrome without opening a window
        chrome_options.add_argument("--no-sandbox")  
        chrome_options.add_argument("--disable-dev-shm-usage") 
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Reduce bot detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")  # Fake real browser
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),  
            options=chrome_options
        )
        
    def get_races_for_year(self, year):
        """Get all races for a specific year"""
        url = f"{self.base_url}/{year}/races"  # Year-specific race listing URL
        print(f"\nFetching races for {year}...")
        print(f"URL: {url}")
        
        self.driver.get(url)  # Load the page
        time.sleep(4)  # Allow JavaScript-rendered content to load
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser') 
        races = []  
        
        # Locate the main results table rendered by React
        table = soup.find('table', class_=lambda x: x and 'Table-module' in str(x))
        
        if table:
            tbody = table.find('tbody')  # Table body contains race rows
            if tbody:
                rows = tbody.find_all('tr')  # Each row is a race
                print(f"Found {len(rows)} rows in table")
                
                for row in rows:
                    cols = row.find_all('td')  # Table columns
                    if len(cols) >= 1:
                        first_col = cols[0]  # First column has race name and link
                        race_link = first_col.find('a')  
                        
                        if race_link and 'href' in race_link.attrs:
                            race_name = race_link.text.strip()  
                            race_href = race_link['href'] 
                            
                            # Extract clean race name from URL 
                            parts_temp = race_href.split('/')
                            if 'races' in parts_temp and len(parts_temp) > parts_temp.index('races') + 2:
                                url_race_name = parts_temp[parts_temp.index('races') + 2]
                                race_name = url_race_name.replace('-', ' ').title()  # readable name
                            else:
                                race_name = race_name.replace('Flag of ', '').strip() 
                            
                            parts = race_href.split('/')  # URL parts for later session building
                            if 'races' in parts:
                                races.append({
                                    'name': race_name, 
                                    'year': year, 
                                    'url': race_href,  
                                    'parts': parts  
                                })
        
        print(f"Found {len(races)} races for {year}")
        if races and len(races) > 0:
            print(f"First race: {races[0]['name']}")
        
        return races  # Return list of races
    
    def check_session_exists(self, url):
        """Check if a session page exists by looking for a table"""
        try:
            full_url = f"https://www.formula1.com{url}" if not url.startswith('http') else url
            self.driver.get(full_url)  
            time.sleep(2)  # Allow JS to load
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser') 
            table = soup.find('table', class_=lambda x: x and 'Table-module' in str(x)) 
            
            return table is not None  
        except:
            return False  # Fail safely if page breaks
    
    def scrape_session_data(self, url, session_name):
        """Scrape data from a specific session"""
        try:
            full_url = f"https://www.formula1.com{url}" if not url.startswith('http') else url  # Normalize URL
            self.driver.get(full_url)  
            time.sleep(3)  # Wait for JS-rendered table
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')  # Parse HTML
            table = soup.find('table', class_=lambda x: x and 'Table-module' in str(x)) 
            
            if not table:
                return None  # No data available
            
            headers = []  # Column headers
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.text.strip() for th in header_row.find_all('th')]  
            
            data = []  # Row data
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    row_data = [col.text.strip() for col in cols]  
                    if row_data:
                        data.append(row_data)
            
            if data and headers:
                if len(headers) == len(data[0]):  
                    df = pd.DataFrame(data, columns=headers)  # Build DataFrame
                    return df
            
            return None  # Return None if parsing fails
            
        except Exception as e:
            return None  # Fail silently to keep scraper running
    
    def scrape_race_sessions(self, race, year):
        """Scrape selected sessions for a race (no practice sessions)"""
        race_name = race['name'].replace(' ', '_').replace('/', '-') 
        race_dir = os.path.join(self.output_dir, str(year), race_name)  # Race output directory
        os.makedirs(race_dir, exist_ok=True)  
        
        print(f"\n  Scraping: {race['name']}")
        
        parts = race['parts']  # URL parts from race listing
        race_idx = parts.index('races')  # Index of 'races' in URL
        race_id = parts[race_idx + 1]  
        race_slug = parts[race_idx + 2] 
        
        base_path = f"/en/results/{year}/races/{race_id}/{race_slug}"  # Base session URL path
        
        sessions = {
            'sprint-qualifying': 'Sprint_Qualifying',
            'sprint': 'Sprint_Results',
            'qualifying': 'Qualifying',
            'starting-grid': 'Starting_Grid',
            'fastest-laps': 'Fastest_Laps',
            'pit-stop-summary': 'Pit_Stop_Summary',
            'race-result': 'Race_Result'
        }  # Sessions to scrape (practice excluded)
        
        for session_key, session_name in sessions.items():
            session_url = f"{base_path}/{session_key}"  # Full session path
            
            print(f"    - {session_name}", end=" ")
            df = self.scrape_session_data(session_url, session_name)  # Scrape session table
            
            if df is not None and not df.empty:
                filename = os.path.join(race_dir, f"{session_name}.csv") 
                df.to_csv(filename, index=False, encoding='utf-8')  # Save to disk
                print(f"✓ ({len(df)} rows)")
            else:
                if 'sprint' in session_key.lower():
                    print(f"✗ (no sprint)")  # Sprint sessions may not exist
                else:
                    print(f"✗")  # Session missing or failed
            
            time.sleep(1)  # Avoid hammering server
    
    def scrape_all_years(self, start_year=2018, end_year=2024):
        """Scrape data for all years"""
        try:
            for year in range(start_year, end_year + 1):
                print(f"\n{'='*60}")
                print(f"YEAR: {year}")
                print(f"{'='*60}")
                
                races = self.get_races_for_year(year)  # Get race list
                
                for i, race in enumerate(races, 1):
                    print(f"\n[{i}/{len(races)}]", end=" ")
                    self.scrape_race_sessions(race, year)  # Scrape each race
                
                print(f"\nCompleted {year}")
                
        finally:
            self.close()  # Clsoe browser
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()  # Shut down Chrome
            print("\n\nBrowser closed. Scraping complete!")

# Usage
if __name__ == "__main__":
    scraper = F1DataScraper(output_dir="f1_data")  
    
    print("Scraping 2025 F1 Season...")
    print("Sessions included: Qualifying, Starting Grid, Sprint (if exists), Race Result, Fastest Laps, Pit Stops")
    print("Practice sessions: EXCLUDED")
    
    scraper.scrape_all_years(start_year=2025, end_year=2025)  # Scrape a single season
    
    print("\n All done! Check the 'f1_data/2025/' folder for all race data")
    
    # Uncomment below to scrape multiple seasons
    # scraper.scrape_all_years(start_year=2018, end_year=2025)
