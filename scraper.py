import os
import sys
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

# Initialize variables
tags = ""
allowAI = True
allowFuta = True
number_of_pages = None
log_file = "scraper.log"

if len(sys.argv) > 1:
    tags = sys.argv[1].lower() # Sets the original set of search tags

    if len(sys.argv) > 2:
        try:
            number_of_pages = int(sys.argv[2])
            print(f"Limiting download to {number_of_pages} pages.\nExpected wait time is 2sec/picture and 15sec/video. You have around {number_of_pages * 40} downloads inbound!")
        except ValueError:
            if "nofuta" in sys.argv[2]:
                allowFuta = False
            if "noai" in sys.argv[2]:
                allowAI = False

    if len(sys.argv) > 3:
        if "nofuta" in sys.argv[3]:
            allowFuta = False
        if "noai" in sys.argv[3]:
            allowAI = False

    if len(sys.argv) > 4:  # Only check sys.argv[4] if it exists
        if "nofuta" in sys.argv[4]:
            allowFuta = False
        if "noai" in sys.argv[4]:
            allowAI = False
else:
    print("No tags provided. Exiting.")
    sys.exit()

# Check if tags are banned. The folder will be renamed after downloads finish
if not allowFuta:
    tags = tags + "+-futanari"
if not allowAI:
    tags = tags + "+-ai_generated+-novelai+-stable_diffusion"
print(f"Searching for: {tags}")

# Check for existing folder download folder
if os.path.exists(tags):
    print(f"Folder {tags} already exists!\nTo avoid overwriting files, please reorder your tags or rename the existing folder.")
    sys.exit()


# Log
def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")  # Format: [YYYY-MM-DD HH:MM:SS]
    formatted_message = f"{timestamp} {message}"
    print(formatted_message)

    with open(log_file, "a", encoding="utf-8") as file:
        file.write(formatted_message + "\n")

# Function to download images
def download_image(url, save_path):
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        response = requests.get(url, stream=True)
        log(f"Saving: {url}")
        with open(save_path, 'wb') as file:
            file.write(response.content)
        
        if os.path.exists(save_path):
            log(f"Image saved as: {save_path}")
        else:
            log(f"Failed to save image: {save_path}")
    except Exception as e:
        log(f"Error downloading image: {e}")

# Function to download videos (with multiple formats support)
def download_video(urls, save_path):
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        for url in urls:
            response = requests.get(url, stream=True)
            log(f"Saving: {url}")
            with open(save_path, 'wb') as file:
                file.write(response.content)
            
            if os.path.exists(save_path):
                log(f"Video saved as: {save_path}")
                return True  # Successfully saved the video
            
        log(f"Failed to download video from all sources: {urls}")
        return False  # Failed to download from all sources
    except Exception as e:
        log(f"Error downloading video: {e}")
        return False

# Function to scrape media
def scrape_media():
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        page_number = 0
        pages_scraped = 0

        while True:
            if number_of_pages is not None and pages_scraped >= number_of_pages:
                log(f"Reached the page limit of {number_of_pages}. Ending scraping.")
                break

            driver.get(f"https://gelbooru.com/index.php?page=post&s=list&tags={tags}+&pid={page_number * 42}")
            log(f"Fetching Gelbooru page {page_number + 1} for '{tags}'...")

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".thumbnail-preview a"))
                )
            except:
                log("No thumbnails found, ending scraping.")
                break

            thumbnails = driver.find_elements(By.CSS_SELECTOR, ".thumbnail-preview a")
            log(f"Found {len(thumbnails)} posts on page {page_number + 1}.")

            for idx in range(len(thumbnails)):  # Use index instead of iterating directly
                try:
                    # Re-fetch the thumbnails list to avoid stale element issues
                    thumbnails = driver.find_elements(By.CSS_SELECTOR, ".thumbnail-preview a")

                    # Open the image page
                    image_page_url = thumbnails[idx].get_attribute('href')
                    driver.get(image_page_url)
                    driver.execute_script("resizeTransition();")
                    time.sleep(2)
                    image_path = f"{tags}/image_{page_number * 42 + idx + 1}.jpg"
                    video_path = f"{tags}/video_{page_number * 42 + idx + 1}.mp4"

                    # Try downloading image first
                    try:
                        image_element = driver.find_element(By.CSS_SELECTOR, "picture img#image")
                        image_url = image_element.get_attribute('src')
                        download_image(image_url, image_path)
                        image_saved = os.path.exists(image_path)
                    except:
                        log(f"No image found for post {page_number * 42 + idx + 1}, attempting video download.")
                        image_saved = False
                        time.sleep(15) # Let video load

                    # If image was not saved, try downloading a video
                    if not image_saved:
                        try:
                            video_element = driver.find_element(By.CSS_SELECTOR, "video#gelcomVideoPlayer")
                            video_sources = video_element.find_elements(By.TAG_NAME, "source")
                            
                            video_urls = []
                            for video_source in video_sources:
                                src = video_source.get_attribute('src')
                                if src:
                                    video_urls.append(src)
                            
                            # Try downloading video if URLs were found
                            if video_urls:
                                log(f"Video URLs found: {video_urls}")
                                video_path = f"{tags}/video_{page_number * 42 + idx + 1}.mp4"  # Default to MP4
                                success = download_video(video_urls, video_path)

                                if not success:
                                    log(f"Failed to download video for post {page_number * 42 + idx + 1}.")
                            else:
                                log(f"No video sources found for post {page_number * 42 + idx + 1}.")

                        except Exception as e:
                            log(f"Failed to find video for post {page_number * 42 + idx + 1}: {e}")

                    # Return to the search results
                    driver.back()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".thumbnail-preview a"))
                    )

                except Exception as e:
                    log(f"Error processing post {page_number * 42 + idx + 1}: {e}")

            page_number += 1
            pages_scraped += 1

    finally:
        try:
            driver.quit()

            # Renaming folder to remove the arguements from before
            log("Finailizing folder name...")
            folder = tags
            if not allowFuta:
                folder = folder.replace("+-futanari", "")
            if not allowAI:
                folder = folder.replace("+-ai_generated", "").replace("+-novelai", "").replace("+-stable_diffusion", "")
            os.rename(tags, folder)
            log(f"Directory name is {folder}")
            log("Exiting...")
        except FileNotFoundError as e:
            log(f"Folder cannot be found!\n{e}")
        except FileExistsError as e: # Adds a number onto the end of the folder name
            log(f"{folder} already exists.")
            counter = 0
            folder = f"{folder}_{counter}"
            while os.path.exists(folder):
                log(f"{folder} already exists.")
                folder = folder[:-len(str(counter))]
                counter += 1
                folder = f"{folder}{counter}"
            os.rename(tags, folder)
            log(f"Directory name is {folder}")

if __name__ == "__main__":
    scrape_media()
