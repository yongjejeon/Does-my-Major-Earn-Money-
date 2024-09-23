import requests

# Function to fetch university data from the API
def get_universities_by_country(country):
    url = f"http://universities.hipolabs.com/search?country={country}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to fetch data from API")
        return None

# Example usage
def main():
    country = input("Enter the country name: ")
    universities = get_universities_by_country(country)

    if universities:
        for uni in universities:
            print(f"Name: {uni['name']}")
            print(f"Domain: {uni['domains']}")
            print(f"Website: {uni['web_pages']}")
            print('-' * 40)

if __name__ == "__main__":
    main()
