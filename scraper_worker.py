import time
import json
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# URL to scrape
VELO_URL = "https://velo.xyz/market"

def setup_driver() :
    """Set up headless Chrome browser for scraping."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Install ChromeDriver
    service = Service(ChromeDriverManager().install())
    
    # Create driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def switch_to_1d_view(driver):
    """Switch to 1d return buckets view."""
    try:
        # Wait for the page to load completely
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "button"))
        )
        
        # Add a longer wait to ensure page is fully loaded
        time.sleep(5)
        
        # Try multiple approaches to find and click the 1d button
        try:
            # First approach: Find by text content
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if button.text == "1d":
                        # Wait for element to be clickable
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//button[text()='1d']"))
                        )
                        button.click()
                        print("Switched to 1d view using text match")
                        time.sleep(3)  # Wait longer for chart to update
                        return True
                except:
                    continue
                    
            # Second approach: Try using XPath directly
            try:
                one_d_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='1d']"))
                )
                one_d_button.click()
                print("Switched to 1d view using XPath")
                time.sleep(3)
                return True
            except:
                pass
                
            # Third approach: Try clicking buttons in dropdown menu
            try:
                # First click a timeframe button to open dropdown
                timeframe_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'timeframe') or contains(@class, 'period')]")
                if timeframe_buttons:
                    timeframe_buttons[0].click()
                    time.sleep(1)
                    
                    # Now try to find and click 1d in the dropdown
                    one_d_option = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[text()='1d']"))
                    )
                    one_d_option.click()
                    print("Switched to 1d view using dropdown")
                    time.sleep(3)
                    return True
            except:
                pass
                
            print("Could not find 1d button using multiple approaches")
            return False
            
        except Exception as inner_e:
            print(f"Inner error finding 1d button: {inner_e}")
            return False
            
    except Exception as e:
        print(f"Error switching to 1d view: {e}")
        return False

def extract_chart_data(driver):
    """Extract data from the 1d Return Buckets chart using JavaScript."""
    try:
        # Execute JavaScript to extract chart data
        script = """
        const chartElements = Array.from(document.querySelectorAll('div[role="graphics-document"], div[role="graphics-object"]'));
        
        // Find chart container
        let chartContainer = null;
        for (const el of chartElements) {
            if (el.textContent.includes('1d Return Buckets') || 
                el.textContent.includes('-9%') || 
                el.textContent.includes('+9%')) {
                chartContainer = el;
                break;
            }
        }
        
        if (!chartContainer) return null;
        
        // Extract data from chart
        const data = {};
        
        // Find all rect elements (bars) and text elements (labels)
        const rects = Array.from(chartContainer.querySelectorAll('rect'));
        const texts = Array.from(chartContainer.querySelectorAll('text'));
        
        // Find category labels (-9%, -6%, etc.)
        const categoryLabels = texts.filter(t => 
            t.textContent.includes('%') && 
            (t.textContent.includes('-') || t.textContent.includes('+') || t.textContent.includes('<') || t.textContent.includes('>'))
        ).map(t => t.textContent.trim());
        
        // Find bars with height attributes
        const bars = rects.filter(r => 
            r.getAttribute('height') && 
            parseFloat(r.getAttribute('height')) > 5 && 
            r.getAttribute('fill')
        );
        
        // Match bars with categories
        if (bars.length === categoryLabels.length) {
            bars.forEach((bar, index) => {
                const category = categoryLabels[index];
                const height = parseFloat(bar.getAttribute('height'));
                const fill = bar.getAttribute('fill');
                const isPositive = fill.toLowerCase().includes('green') || 
                                  category.includes('+') || 
                                  category.includes('>');
                
                data[category] = {
                    value: height,
                    color: isPositive ? 'green' : 'red',
                    is_positive: isPositive
                };
            });
            
            return data;
        }
        
        return null;
        """
        
        chart_data = driver.execute_script(script)
        
        if not chart_data:
            print("Failed to extract chart data")
            return None
            
        print(f"Successfully extracted data for {len(chart_data)} categories")
        return chart_data
        
    except Exception as e:
        print(f"Error extracting chart data: {e}")
        return None

def calculate_metrics(chart_data):
    """Calculate strategic bias and directional bias from chart data."""
    if not chart_data:
        return None
        
    # Calculate total coins
    total_coins = sum(item['value'] for item in chart_data.values())
    
    # Calculate positive coins
    positive_coins = sum(item['value'] for item in chart_data.values() if item['is_positive'])
    
    # Calculate strategic bias (percentage of positive coins)
    strategic_bias = (positive_coins / total_coins) * 100 if total_coins > 0 else 50
    
    # Calculate directional bias (weighted average of sigma values)
    sigma_weights = {
        "-9%": -3,
        "-6%": -2,
        "-3%": -1,
        "<0%": -0.5,
        ">0%": 0.5,
        "+3%": 1,
        "+6%": 2,
        "+9%": 3
    }
    
    weighted_sum = 0
    for category, item in chart_data.items():
        if category in sigma_weights:
            weighted_sum += sigma_weights[category] * item['value']
    
    directional_bias = weighted_sum / total_coins if total_coins > 0 else 0
    
    # Determine quadrant
    quadrant = ""
    if strategic_bias >= 50:
        if directional_bias >= 0:
            quadrant = "Momentum Long Only"
        else:
            quadrant = "Momentum Short Only"
    else:
        if directional_bias >= 0:
            quadrant = "Mean Reversion Long Only"
        else:
            quadrant = "Mean Reversion Short Only"
    
    return {
        "strategic_bias": strategic_bias,
        "directional_bias": directional_bias,
        "green_percentage": strategic_bias,
        "quadrant": quadrant
    }

def save_data_to_json(chart_data, metrics, output_path):
    """Save the scraped data to a JSON file."""
    try:
        # Create data structure
        data = {
            "timestamp": int(time.time() * 1000),
            "datetime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "strategic_bias": metrics["strategic_bias"],
            "directional_bias": metrics["directional_bias"],
            "green_percentage": metrics["green_percentage"],
            "quadrant": metrics["quadrant"],
            "data": chart_data
        }
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Data saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error saving data to JSON: {e}")
        return False

def scrape_velo_data():
    """Main function to scrape velo.xyz data."""
    driver = None
    try:
        print("Starting velo.xyz scraper...")
        
        # Setup driver
        driver = setup_driver()
        
        # Navigate to velo.xyz
        driver.get(VELO_URL)
        print(f"Navigated to {VELO_URL}")
        
        # Switch to 1d view
        if not switch_to_1d_view(driver):
            print("Failed to switch to 1d view")
            return False
        
        # Extract chart data
        chart_data = extract_chart_data(driver)
        if not chart_data:
            print("Failed to extract chart data")
            return False
        
        # Calculate metrics
        metrics = calculate_metrics(chart_data)
        if not metrics:
            print("Failed to calculate metrics")
            return False
        
        # Determine output path - in production this would be in the public folder
        output_path = os.path.join("public", "data.json")
        
        # Save data to JSON
        if not save_data_to_json(chart_data, metrics, output_path):
            print("Failed to save data to JSON")
            return False
        
        print("Velo.xyz data scraping completed successfully")
        return True
        
    except Exception as e:
        print(f"Error in scrape_velo_data: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

def main():
    """Main entry point for the scraper worker."""
    # Create public directory if it doesn't exist
    os.makedirs("public", exist_ok=True)
    
    # Run the scraper
    success = scrape_velo_data()
    
    # In a production environment, we would set up a schedule
    # For Render.com, we can use an infinite loop with sleep
    # This is commented out for now to avoid infinite execution during testing
    """
    while True:
        success = scrape_velo_data()
        # Sleep for 1 hour
        time.sleep(3600)
    """
    
    return success

if __name__ == "__main__":
    main()
