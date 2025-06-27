import undetected_chromedriver as uc
import time
driver = uc.Chrome(version_main=134, headless=False)
driver.get("https://www.google.com/")
time.sleep(5)

driver.quit()

