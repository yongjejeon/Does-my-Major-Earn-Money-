import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Function to fetch university data from the API for US universities
def get_us_universities():
    url = "http://universities.hipolabs.com/search?country=United%20States"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to fetch data from API")
        return None

# Function to match university name from College Scorecard to the API data and return website link
def match_university_name(api_data, university_name):
    for university in api_data:
        if university_name.lower() in university['name'].lower():
            return university['web_pages'][0]  # Return the first website link
    return None  # Return None if no match is found

# Function to apply regex to extract monetary values from text
def extract_money_value(text):
    match = re.search(r'\$\d{1,3}(,\d{3})*(\.\d{2})?', text)
    if match:
        return match.group(0)
    return "N/A"

# Function to apply regex to extract numerical values from text (e.g., graduate numbers)
def extract_number_value(text):
    match = re.search(r'\d{1,3}(,\d{3})*', text)
    if match:
        return match.group(0).replace(",", "")  # Remove commas for better numeric handling
    return "N/A"

# Helper function to get the text or return "N/A" if data not available
def get_text_or_regex_na(elements, index, extract_fn):
    if len(elements) > index:
        text = elements[index].text.strip()
        if "Data Not Available" in text:
            return "N/A"
        return extract_fn(text)
    return "N/A"

# Function to navigate to "Search Fields of Study" and select major
def navigate_to_field_of_study(major_to_search, api_data):
    # Set up the web driver (make sure to specify the correct path to your ChromeDriver)
    driver = webdriver.Chrome()

    # Open the College Scorecard website
    driver.get("https://collegescorecard.ed.gov/")
    
    time.sleep(2)  # Allow some time for the page to load

    # Locate and click on the "Search Fields of Study" tab
    try:
        field_of_study_tab = driver.find_element(By.XPATH, "//div[@role='tab' and contains(text(), 'Search Fields of Study')]")
        field_of_study_tab.click()
        print("Navigated to 'Search Fields of Study' tab successfully.")
        
        time.sleep(2)  # Allow the tab to load
        
        # Locate the search input field where you need to type the major
        search_input = driver.find_element(By.ID, "input-129")
        search_input.click()
        search_input.send_keys(major_to_search)  # Type the user's major into the input field
        
        time.sleep(2)  # Wait for the list to load
        
        # Find and click on the exact match from the list to activate the search button
        major_titles = driver.find_elements(By.CLASS_NAME, "v-list-item__title")
        major_subtitles = driver.find_elements(By.CLASS_NAME, "v-list-item__subtitle")
        
        matched_major = None
        for major in major_titles:
            if major_to_search.strip().lower() == major.text.strip().lower():
                matched_major = major
                break

        # If no match found in titles, check the subtitles
        if not matched_major:
            for subtitle in major_subtitles:
                if major_to_search.strip().lower() == subtitle.text.strip().lower():
                    matched_major = subtitle
                    break

        if matched_major:
            matched_major.click()  # Click the matched major or subtitle in the list
            print(f"Selected Major: {matched_major.text}")
        else:
            print("No exact matching major or subtitle found.")
            driver.quit()
            return

        # Now select the degree input and choose "Bachelor's Degree"
        degree_input = driver.find_element(By.ID, "fosDegree")
        degree_input.click()  # Click on the input field to open the dropdown
        
        time.sleep(1)  # Wait for the dropdown to appear

        # Find and select "Bachelor's Degree"
        bachelors_option = driver.find_element(By.XPATH, "//div[contains(text(), \"Bachelor's Degree\")]")
        bachelors_option.click()
        print("Selected Bachelor's Degree.")
        
        # After selecting the degree, click the updated search button
        search_button = driver.find_element(By.XPATH, "//button[contains(@class, 'v-btn') and contains(@class, 'secondary')]")
        search_button.click()
        print("Search triggered.")
        
        # Allow time for the search results to load
        time.sleep(5)

        # Initialize arrays to hold filtered data
        university_names = []
        median_earnings = []
        monthly_earnings = []
        median_debts = []
        monthly_loan_payments = []
        graduate_numbers = []
        university_links = []

        # Step 1: Click on the "Earnings" link to sort by earnings
        try:
            earnings_sort_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Earnings')]")
            earnings_sort_link.click()
            print("Earnings sort link clicked successfully.")

            # Wait for the page to reload and display sorted results
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "nameLink"))
            )

        except Exception as e:
            print(f"Failed to click on earnings sort link. Error: {str(e)}")
            driver.quit()
            return

        # Step 2: Get all universities and earnings data dynamically
        while True:
            try:
                universities = driver.find_elements(By.CLASS_NAME, "nameLink")
                earnings = driver.find_elements(By.XPATH, "//span[@class='display-2 navy-text font-weight-bold ']")
                median_debt = driver.find_elements(By.XPATH, "//span[@class='display-2 navy-text font-weight-bold ']")
                monthly_loan_payment = driver.find_elements(By.XPATH, "//span[@class='display-2 navy-text font-weight-bold ']")
                graduate_number = driver.find_elements(By.XPATH, "//span[@class='display-2 navy-text font-weight-bold']")

                if not universities:
                    print("No more universities found.")
                    break

                # Use a while loop to collect data while skipping even indices for numeric data but keeping all university names
                i = 0
                while i < 11:
                    university_name = universities[i].text
                    university_names.append(university_name)
                    university_link = match_university_name(api_data, university_name)
                    university_links.append(university_link if university_link else 'No link available')
                    i += 1
                i = 0
                while i < len(universities):

                    if i == 0 or i % 2 != 0:  # Keep index 0 and odd indices
                        median_earning = get_text_or_regex_na(earnings, 2 * i, extract_money_value)  # Median earning
                        monthly_earning = get_text_or_regex_na(earnings, 2 * i + 1, extract_money_value)  # Monthly earning
                        grad_number = get_text_or_regex_na(graduate_number, i, extract_number_value)  # Graduate number

                        median_earnings.append(median_earning)
                        monthly_earnings.append(monthly_earning)
                        graduate_numbers.append(grad_number)
                        # Match the university name to the API data to get the link

                    i += 1

                # If there's a "Next" button, click it to load more results
                try:
                    next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                    next_button.click()
                    time.sleep(5)  # Wait for new results to load
                except Exception as e:
                    print("No more pages to load.")
                    break

            except Exception as e:
                print(f"Error fetching university data. Error: {str(e)}")
                break


        # After collecting data in arrays, print them
        # print("University Names:")
        # print(university_names)
        # print(len(university_names))
        # print("\nMedian Earnings:")
        # print(median_earnings)
        # print(len(median_earnings))
        # print("\nMonthly Earnings:")
        # print(monthly_earnings)
        # print(len(monthly_earnings))
        # print("\nGraduate Numbers:")
        # print(graduate_numbers)
        # print(len(graduate_numbers))
        # print("\nUniversity Websites:")
        # print(university_links)
        # print(len(university_links))

        # Step 3: Convert collected data into DataFrame

        data = {
            'University': university_names,
            'Median Earning': median_earnings,
            'Monthly Earning': monthly_earnings,
            'Graduate Number': graduate_numbers,
            'University Website': university_links
        }
        df = pd.DataFrame(data)
        print(df)

        # Save the DataFrame to a CSV file
        df.to_csv('university_data_filtered.csv', index=False)

    except Exception as e:
        print(f"Failed to navigate to 'Search Fields of Study'. Error: {str(e)}")
    
    # Wait to observe the action before closing the browser
    time.sleep(5)
    driver.quit()
def main():
    # First, fetch university data via the API
    api_data = get_us_universities()

    if api_data:
        # Ask the user to enter a major
        major_to_search = input("Enter a major to search for: ")

        # Then, navigate to the "Search Fields of Study" and match the major
        navigate_to_field_of_study(major_to_search, api_data)

if __name__ == "__main__":
    main()
