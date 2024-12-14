from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, sys
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2
})
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)
cwd = Path.cwd()

def isImageAlreadyDownloaded(imgPath):
    if os.path.exists(imgPath) == True:
        return True
    return False

def isChapterAlreadyDownloaded(filesPath, pageCount):
    if os.path.exists(filesPath):
        filesCount = len(list(filesPath.glob("*.jpg")))
        if filesCount == pageCount:
            return True
    return False

def createDir(dirName):
    dirPath = Path(cwd / dirName)
    dirPath.mkdir(exist_ok=True)
    return dirPath

def appendChapterLinks(chapterLinks, aTagElems):
    size = len(aTagElems)
    for i in range(1, size + 1):
        href = aTagElems[size - i].get_attribute("href")
        if href: 
            chapterLinks.append(href)

def writeImageFile(res, imgPath):
    with open(imgPath, "wb") as fImg:
        for chunk in res.iter_content(100000):
            fImg.write(chunk)

def donwloadImage(image):
    res = requests.get(image['src'])
    res.raise_for_status()
    writeImageFile(res, image['path'])
    print(f"Imagem {image['name']} baixada com sucesso!")

def requestImages(images, executor):
    results = executor.map(donwloadImage, images)
    return list(results)

def main():
    if len(sys.argv) > 1:

        url = sys.argv[1]
        chapterLinks = []

        try:
            driver.get(url)
            aElems = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody//a[@href]")))
            
            dirName = driver.current_url.split("/")[-1]
            dirPath = createDir(dirName)

            print(f"### Fazendo download da HQ: {dirName} ###")
            print("O tempo de download depende da quantidade de capitulos e paginas existentes na HQ")

            appendChapterLinks(chapterLinks, aElems)

            with ThreadPoolExecutor() as executor:
                for chapter, link in enumerate(chapterLinks):

                    images = []

                    chapter = chapter + 1
                    driver.get(link)
                    buttonElems = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'jdQClN')]//button")))
                    # (- 2) ignore buttons fullscreen and comments
                    pageCount = len(buttonElems) - 2 
                    filesPath = Path(dirPath / f"capitulo-{chapter}")

                    print(f"## Iniciando download do capitulo {chapter} ##")
                    print("Aguarde...")

                    if isChapterAlreadyDownloaded(filesPath, pageCount):
                        print(f"Capitulo {chapter} ja existe!")
                        continue

                    filesPath.mkdir(exist_ok=True)

                    for page in range(1, pageCount + 1):
                        imgElem = wait.until(EC.presence_of_element_located((By.XPATH, "//figure/img")))
                        imgSrc = imgElem.get_attribute("src")
                        
                        if imgSrc:
                            fileName = imgSrc.split("/")[-1]
                            imgPath = filesPath / fileName

                            if isImageAlreadyDownloaded(imgPath) == False:
                                imgObj = {
                                    'src': imgSrc,
                                    'name': fileName,
                                    'path': imgPath
                                }
                                images.append(imgObj)
                        
                        if page < pageCount:
                            newUrl = driver.current_url.replace(f"page/{page}", f"page/{page + 1}")
                            driver.get(newUrl)

                    results = requestImages(images, executor)

                    if len(results) == len(images):
                        print(f"## Finalizado download do capitulo {chapter} ##")

            print("Feito!")
            driver.quit()
            
        except Exception as exc:
            print("Ocorreu um erro: ", exc)
            driver.quit()
    else:
        print("Informe o argumento com a URL da HQ")

main()