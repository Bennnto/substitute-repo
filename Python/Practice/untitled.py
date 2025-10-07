import requests
import json
from datetime import datetime
import sys

# =================================
# WEATHER API DATA HANDLING WITH DEBUG
# =================================

def debug_print(message, level="INFO"):
    """Enhanced debug printing with levels"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def get_weather_data_debug(city="Toronto", debug_mode=True):
    """
    Fetch weather data with comprehensive debugging
    Args:
        city (str): City name to get weather for
        debug_mode (bool): Enable detailed debugging output
    """
    API_key = "8a1f5fbf2942163974daec756376cb99"
    
    if debug_mode:
        debug_print("=" * 60)
        debug_print("STARTING WEATHER API REQUEST")
        debug_print("=" * 60)
        debug_print(f"Python version: {sys.version}")
        debug_print(f"Requests module available: {bool(requests)}")
        debug_print(f"Target city: {city}")
        debug_print(f"API key (masked): {API_key[:8]}...{API_key[-4:]}")
    
    # Build URL
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': API_key,
        'units': 'metric'  # Get temperature in Celsius
    }
    
    if debug_mode:
        debug_print(f"Base URL: {base_url}")
        debug_print(f"Parameters: {params}")
        full_url = f"{base_url}?q={city}&appid={API_key}&units=metric"
        debug_print(f"Full URL: {full_url}")
    
    try:
        if debug_mode:
            debug_print("Making HTTP request...")
        
        # Make request with timeout
        response = requests.get(base_url, params=params, timeout=10)
        
        if debug_mode:
            debug_print(f"Response received!")
            debug_print(f"Status Code: {response.status_code}")
            debug_print(f"Response Headers: {dict(response.headers)}")
            debug_print(f"Response Time: {response.elapsed.total_seconds():.2f} seconds")
            debug_print(f"Response Size: {len(response.content)} bytes")
        
        # Check status code
        if response.status_code == 200:
            if debug_mode:
                debug_print("✅ SUCCESS: Status 200 OK", "SUCCESS")
            
            try:
                data = response.json()
                
                if debug_mode:
                    debug_print("✅ JSON parsing successful", "SUCCESS")
                    debug_print(f"JSON keys: {list(data.keys())}")
                    debug_print("Raw JSON response:")
                    print(json.dumps(data, indent=2))
                
                # Process and display weather data
                process_weather_data(data, debug_mode)
                return data
                
            except json.JSONDecodeError as e:
                debug_print(f"❌ JSON decode error: {e}", "ERROR")
                debug_print(f"Raw response content: {response.text[:200]}...", "ERROR")
                return None
                
        else:
            debug_print(f"❌ HTTP Error: {response.status_code}", "ERROR")
            debug_print(f"Response text: {response.text}", "ERROR")
            
            # Handle specific error codes
            if response.status_code == 401:
                debug_print("💡 TIP: Check your API key", "WARNING")
            elif response.status_code == 404:
                debug_print("💡 TIP: Check city name spelling", "WARNING")
            elif response.status_code == 429:
                debug_print("💡 TIP: API rate limit exceeded", "WARNING")
            
            return None
            
    except requests.exceptions.Timeout:
        debug_print("❌ Request timeout (10 seconds)", "ERROR")
        debug_print("💡 TIP: Check internet connection", "WARNING")
        return None
        
    except requests.exceptions.ConnectionError:
        debug_print("❌ Connection error", "ERROR")
        debug_print("💡 TIP: Check internet connection", "WARNING")
        return None
        
    except requests.exceptions.RequestException as e:
        debug_print(f"❌ Request error: {e}", "ERROR")
        return None
        
    except Exception as e:
        debug_print(f"❌ Unexpected error: {type(e).__name__}: {e}", "ERROR")
        debug_print(f"Error details: {str(e)}", "ERROR")
        return None

def process_weather_data(data, debug_mode=True):
    """Process and display weather data in a readable format"""
    if debug_mode:
        debug_print("=" * 40)
        debug_print("PROCESSING WEATHER DATA")
        debug_print("=" * 40)
    
    try:
        # Extract main information
        city_name = data.get('name', 'Unknown')
        country = data.get('sys', {}).get('country', 'Unknown')
        
        # Weather information
        weather_main = data.get('weather', [{}])[0].get('main', 'Unknown')
        weather_desc = data.get('weather', [{}])[0].get('description', 'Unknown')
        
        # Temperature data
        temp_current = data.get('main', {}).get('temp', 0)
        temp_feels_like = data.get('main', {}).get('feels_like', 0)
        temp_min = data.get('main', {}).get('temp_min', 0)
        temp_max = data.get('main', {}).get('temp_max', 0)
        
        # Other data
        humidity = data.get('main', {}).get('humidity', 0)
        pressure = data.get('main', {}).get('pressure', 0)
        visibility = data.get('visibility', 0) / 1000  # Convert to km
        
        # Wind data
        wind_speed = data.get('wind', {}).get('speed', 0)
        wind_direction = data.get('wind', {}).get('deg', 0)
        
        # Display formatted weather report
        print("\n" + "🌤️  WEATHER REPORT".center(50, "="))
        print(f"📍 Location: {city_name}, {country}")
        print(f"🌡️  Temperature: {temp_current}°C (feels like {temp_feels_like}°C)")
        print(f"📊 Range: {temp_min}°C - {temp_max}°C")
        print(f"☁️  Condition: {weather_main} - {weather_desc.title()}")
        print(f"💧 Humidity: {humidity}%")
        print(f"🌬️  Pressure: {pressure} hPa")
        print(f"💨 Wind: {wind_speed} m/s at {wind_direction}°")
        print(f"👁️  Visibility: {visibility:.1f} km")
        print(f"📅 Updated: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        if debug_mode:
            debug_print("✅ Weather data processed successfully", "SUCCESS")
        
    except KeyError as e:
        debug_print(f"❌ Missing key in weather data: {e}", "ERROR")
    except Exception as e:
        debug_print(f"❌ Error processing weather data: {e}", "ERROR")

def test_api_connection():
    """Test basic API connectivity"""
    debug_print("=" * 50)
    debug_print("TESTING API CONNECTION")
    debug_print("=" * 50)
    
    test_url = "https://httpbin.org/get"
    try:
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            debug_print("✅ Internet connection working", "SUCCESS")
            return True
        else:
            debug_print(f"❌ Connection test failed: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        debug_print(f"❌ Connection test error: {e}", "ERROR")
        return False

def test_multiple_cities():
    """Test weather API with multiple cities"""
    debug_print("=" * 50)
    debug_print("TESTING MULTIPLE CITIES")
    debug_print("=" * 50)
    
    cities = ["Toronto", "New York", "London", "Tokyo", "InvalidCityName123"]
    
    for city in cities:
        debug_print(f"\n🌍 Testing city: {city}")
        result = get_weather_data_debug(city, debug_mode=False)
        if result:
            debug_print(f"✅ {city}: Success", "SUCCESS")
        else:
            debug_print(f"❌ {city}: Failed", "ERROR")

# Main execution functions
def run_basic_test():
    """Run basic weather test"""
    print("BASIC WEATHER TEST")
    print("=" * 30)
    get_weather_data_debug("Toronto", debug_mode=True)

def run_full_debug():
    """Run comprehensive debug test"""
    print("COMPREHENSIVE DEBUG TEST")
    print("=" * 40)
    
    # Test connection first
    if test_api_connection():
        # Test single city with full debug
        get_weather_data_debug("Toronto", debug_mode=True)
        
        # Test multiple cities
        test_multiple_cities()
    else:
        debug_print("❌ Skipping weather tests due to connection issues", "ERROR")

# Add the original function for compatibility
def get_weather_data():
    """Original function - now calls debug version"""
    return get_weather_data_debug("Toronto", debug_mode=True)

# =================================
# EXECUTION SECTION
# =================================

if __name__ == "__main__":
    print("🌦️  WEATHER API DEBUG TOOL")
    print("=" * 60)
    
    # Menu for different debug options
    print("\nChoose debug option:")
    print("1. Basic weather test (Toronto)")
    print("2. Full debug mode")
    print("3. Test multiple cities")
    print("4. Connection test only")
    print("5. Run all tests")
    
    try:
        choice = input("\nEnter choice (1-5) or press Enter for basic test: ").strip()
        
        if choice == "2":
            run_full_debug()
        elif choice == "3":
            test_multiple_cities()
        elif choice == "4":
            test_api_connection()
        elif choice == "5":
            print("\n🚀 RUNNING ALL TESTS")
            print("=" * 40)
            test_api_connection()
            run_full_debug()
        else:
            # Default: basic test
            run_basic_test()
            
    except KeyboardInterrupt:
        print("\n\n👋 Debug session cancelled by user")
    except Exception as e:
        debug_print(f"❌ Execution error: {e}", "ERROR")
