import requests
import xml.etree.ElementTree as ET

# --- Configuration ---
# Replace these with your actual PRTG server details
PRTG_SERVER_URL = "https://prtg.pioneerbroadband.net" # e.g., "https://prtg.mycompany.com"
PRTG_USERNAME = "streamlit_api_userUser"
PRTG_PASSHASH = "N4RWTIZ3WXZTKIJDO5L4QFQ5SJKECLJMTYCZW7HGHE======" # Get this from your user account settings in PRTG
# --- Build the API Request URL ---
# We are asking for a table of all sensors and requesting the 'sensor' column
api_url = (
    f"{PRTG_SERVER_URL}/api/table.xml?"
    f"content=sensors&"
    f"columns=sensor,objid&" # Ask for the sensor name and its object ID
    f"username={PRTG_USERNAME}&"
    f"passhash={PRTG_PASSHASH}"
)

print(f"Requesting data from: {PRTG_SERVER_URL}")

try:
    # --- Make the HTTP GET Request ---
    response = requests.get(api_url)

    # --- Handle the Response ---
    # Check the HTTP status code to see if the request was successful
    if response.status_code == 200:
        print("✅ Request successful! Processing XML data...")

        # Parse the XML response text
        root = ET.fromstring(response.content)

        # Find all <item> tags in the XML, which represent individual sensors
        for item in root.findall('item'):
            sensor_name = item.find('sensor').text
            sensor_id = item.find('objid').text
            print(f"  - Sensor Name: {sensor_name} (ID: {sensor_id})")

    elif response.status_code == 401:
        print("❌ Error: Authentication failed (401 Unauthorized).")
        print("Please check your PRTG_USERNAME and PRTG_PASSHASH.")

    elif response.status_code == 400:
        print("❌ Error: Bad Request (400). The server could not process the request.")
        # Try to parse the error message from the XML response
        root = ET.fromstring(response.content)
        error_message = root.find('error').text
        print(f"Server error message: {error_message}")

    else:
        print(f"❌ An unexpected error occurred. HTTP Status Code: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"❌ A network error occurred: {e}")
