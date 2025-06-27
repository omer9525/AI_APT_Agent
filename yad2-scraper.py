import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
import random

options = uc.ChromeOptions()
options.add_argument("--disable-popup-blocking")
driver = uc.Chrome(headless=False, options=options)

headers = ["apt-type", "city", "address", "rooms", "floor", "size", "price", "apt-link", "attributes"]
all_data = []

for page_num in range(1, 101):
    print(f"🔄 Scraping page {page_num}...")
    url = f"https://www.yad2.co.il/realestate/rent?page={page_num}"

    try:
        driver.get(url)
    except Exception as e:
        print(f"⚠️ Failed on page {page_num}: {e}")
        continue

    try:
        # Wait until the listings are loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "item-layout_itemLink__CZZ7w"))
        )
        time.sleep(2)

        listings = driver.find_elements(By.CLASS_NAME, "item-layout_itemLink__CZZ7w")[:13]

        for listing in listings:
            try:
                link = listing.get_attribute("href")
                content = listing.find_element(By.CLASS_NAME, "item-layout_itemContent__qT_A8")

                address = content.find_element(By.CLASS_NAME, "item-data-content_heading__tphH4").text.strip()

                info_lines = content.find_elements(By.CLASS_NAME, "item-data-content_itemInfoLine__AeoPP")
                apt_type_city = info_lines[0].text.strip() if len(info_lines) > 0 else ""
                rooms_floor_size = info_lines[1].text.strip() if len(info_lines) > 1 else ""

                price_elem = content.find_element(By.CSS_SELECTOR, "[data-testid='price']")
                price = price_elem.text.replace("₪", "").strip().replace(",", "") if price_elem else ""

                # Parse apt-type and city
                parts = apt_type_city.split(",")
                apt_type = parts[0].strip() if len(parts) > 0 else ""
                city = parts[-1].strip() if len(parts) > 1 else ""

                # Parse rooms, floor, size
                parts = rooms_floor_size.split("•")
                rooms = parts[0].replace("חדרים", "").strip() if len(parts) > 0 else ""
                floor = parts[1].replace("קומה", "").strip() if len(parts) > 1 else ""
                size = parts[2].replace("מ״ר", "").strip() if len(parts) > 2 else ""

                # Find the tag container
                try:
                    tag_container = content.find_element(By.CLASS_NAME, "item-tags_itemTagsBox__Uz23E")
                    tag_spans = tag_container.find_elements(By.TAG_NAME, "span")
                    attributes = ", ".join([span.text.strip() for span in tag_spans])
                except:
                    attributes = ""

                all_data.append([apt_type, city, address, rooms, floor, size, price, link, attributes])

            except Exception as e:
                print("❌ Failed parsing one item:", e)
                continue

    except Exception as e:
        print(f"⚠️ Failed on page {page_num} due to page structure: {e}")
        continue

    time.sleep(random.uniform(2, 5))

driver.quit()

# Save to CSV
with open("yad2_listings.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(all_data)

print("✅ Done! Data saved to yad2_listings.csv")
