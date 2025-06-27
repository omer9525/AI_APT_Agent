
import undetected_chromedriver as uc
import time
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = uc.ChromeOptions()
options.add_argument("--disable-popup-blocking")

driver = uc.Chrome(version_main=134, headless=False, options=options)


def extract_main_data(table_id):
    clms_to_keep_main = [2, 3, 4, 5, 6, 7, 8]  # these are the columns we need from the main table
    table = driver.find_element(By.ID, table_id)
    rows = table.find_elements(By.TAG_NAME, "tr")

    table_data = []
    for row in rows[1:]:
        cells = row.find_elements(By.TAG_NAME, "td")
        row_data = []
        for i in clms_to_keep_main:
            if i < len(cells):
                row_data.append(cells[i].text.strip())
        try:
            details_cell = row.find_element(By.CLASS_NAME, "details")
            apt_link = details_cell.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            apt_link = ""
            row_data.append(apt_link)
            table_data.append(row_data)
            continue

        original_window = driver.current_window_handle
        link_element = details_cell.find_element(By.TAG_NAME, "a")

        # Wait for the link to scroll into view, then click
        driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", link_element)

        WebDriverWait(driver, 5).until(EC.number_of_windows_to_be(2))

        # Switch to new tab
        for handle in driver.window_handles:
            if handle != original_window:
                driver.switch_to.window(handle)
                break

        apt_size = ""

        try:
            # Let the page start loading
            time.sleep(4)

            # Wait until IconOption block appears
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'IconOption ')]"))
            )

            icon_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'IconOption ')]")

            for block in icon_blocks:
                try:
                    h3 = block.find_element(By.TAG_NAME, "h3")
                    label = h3.text.strip().replace(":", "").replace("\u00A0", "")
                    value_span = block.find_element(By.TAG_NAME, "span")
                    value_text = value_span.text.strip()

                    if "מ\"ר" in label or "מר" in label:
                        apt_size = value_text.strip()

                except Exception as e:
                    continue  # Ignore broken blocks

        except Exception as e:
            print("Could not scan IconOption blocks:", driver.current_url)
            print("Error:", str(e))

        driver.close()

        if original_window in driver.window_handles:
            driver.switch_to.window(original_window)

        row_data.insert(6, apt_size)
        row_data.append(apt_link)
        table_data.append(row_data)

    return table_data


def extract_related_data(table_id):
    clms_to_keep_related = [2, 3, 4, 5, 6, 7]
    table = driver.find_element(By.ID, table_id)
    rows = table.find_elements(By.TAG_NAME, "tr")
    table_data = []

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        row_data = []

        for i in clms_to_keep_related:
            if i < len(cells):
                row_data.append(cells[i].text.strip())

        try:
            details_cell = row.find_element(By.CLASS_NAME, "details")
            apt_link = details_cell.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            apt_link = ""
            floor_num = ""
            row_data.insert(5, floor_num)
            row_data.append(apt_link)
            table_data.append(row_data)
            continue

        original_window = driver.current_window_handle
        link_element = details_cell.find_element(By.TAG_NAME, "a")

        # Wait for the link to scroll into view, then click
        driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", link_element)

        WebDriverWait(driver, 5).until(EC.number_of_windows_to_be(2))

        # Switch to new tab
        for handle in driver.window_handles:
            if handle != original_window:
                driver.switch_to.window(handle)
                break

        floor_num = ""
        apt_size = ""

        try:
            # Wait until at least one IconOption block appears
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'IconOption ')]"))
            )

            icon_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'IconOption ')]")

            for block in icon_blocks:
                try:
                    h3 = block.find_element(By.TAG_NAME, "h3")
                    label = h3.text.strip().replace(":", "").replace("\u00A0", "")
                    value_span = block.find_element(By.TAG_NAME, "span")
                    value_text = value_span.text.strip()

                    if "קומה" in label:
                        if "מתוך" in value_text:
                            floor_num = value_text.split("מתוך")[0].strip()
                        else:
                            floor_num = value_text.strip()

                    elif "מ\"ר" in label or "מר" in label:
                        apt_size = value_text.strip()

                except Exception as e:
                    continue  # Ignore broken blocks

        except Exception as e:
            print("Could not scan IconOption blocks:", driver.current_url)
            print("Error:", str(e))

        driver.close()

        if original_window in driver.window_handles:
            driver.switch_to.window(original_window)

        row_data.insert(5, floor_num)
        row_data.insert(6, apt_size)
        row_data.append(apt_link)
        table_data.append(row_data)

    return table_data


driver.get("https://www.homeless.co.il/rent/")
headers = ["apt-type", "city", "nbrhood", "street", "room-num", "floor", "size", "price", "apt-link"]
all_data = []
page_num = 1

while page_num <= 20:
    # Get reference to current table BEFORE clicking next
    old_table = driver.find_element(By.ID, "mainresults")

    # Extract data before moving to next page
    data_main = extract_main_data("mainresults")
    # data_related = extract_related_data("relatedresults")
    all_data.extend(data_main)

    # Try to go to the next page
    try:
        next_link = driver.find_element(By.XPATH, "//a[@class='pagingtext' and contains(text(), 'הבא')]")
        driver.execute_script("arguments[0].scrollIntoView(true);", next_link)
        time.sleep(1)
        next_link.click()

        # Let the page start loading
        time.sleep(4)

        # Wait for the main table to be visible again (fresh)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mainresults"))
        )

        page_num += 1
    except:
        print("No more pages. Scraping complete.")
        break

# Save all collected data
with open("real_estate_listings.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(all_data)

print("Data saved to real_estate_listings.csv")
driver.quit()



