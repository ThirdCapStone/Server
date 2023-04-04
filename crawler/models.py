from typing import Tuple, Optional, List, Dict, Union
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from enum import Enum
import traceback
import selenium
import requests
import re


class CrawlerResponse(Enum):
    FAIL = 0
    SUCCESS = 1
    DATA_REQUIRED = 2
    URL_NOT_FOUND = 3
    INTERNAL_SERVER_ERROR = 4


def camel_case_to_snake_case(data: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', data).lower()


def remove_html_tag_from_string(data: str) -> str:
    CLEANR = re.compile('<.*?>')
    return re.sub(CLEANR, '', data)


chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
driver = webdriver.Chrome("./chromedriver", chrome_options=chrome_options)
driver.header_overrides = {
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
}


class Crawler:
    class MEGABOX:
        @staticmethod
        def load_area_info(url: str) -> Tuple[CrawlerResponse, Optional[List[Dict[str, str]]]]:
            try:
                return_list = list()
                driver.get(url)
                area_list = driver.find_elements(
                    By.XPATH, "//*[@id='contents']/div/div[1]/div[1]/ul/li")
                for area in area_list:
                    return_dict = {}
                    return_dict["area"] = area.find_element(
                        By.TAG_NAME, "button").text
                    theather_list = area.find_elements(By.TAG_NAME, "li")
                    theather_infoes = list()
                    for theather in theather_list:
                        data_brch_no = theather.get_attribute("data-brch-no")
                        title = theather.find_element(By.TAG_NAME, "a").get_attribute(
                            "title").split("상세보기")[0].rstrip()
                        theather_info = {"title": title,
                                         "data_brch_no": data_brch_no}
                        theather_infoes.append(theather_info)
                    return_dict["info"] = theather_infoes
                    return_list.append(return_dict)

                return [CrawlerResponse.SUCCESS, return_list]

            except selenium.common.exceptions.WebDriverException as e:
                print(
                    f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return [CrawlerResponse.URL_NOT_FOUND, None]

            except Exception as e:
                print(
                    f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return [CrawlerResponse.INTERNAL_SERVER_ERROR, None]

            finally:
                driver.close()

        @staticmethod
        def load_theather_info(brch: str) -> Tuple[CrawlerResponse, str]:
            url = "https://www.megabox.co.kr/on/oh/ohc/Brch/infoPage.do"
            return_list = []
            try:
                response = requests.post(url, params={"brchNo": f"{brch}"})
                if response.status_code == 200:
                    return_dict = {}
                    soup = BeautifulSoup(response.text, "html.parser")
                    title = soup.find("p", {"class": "big"})
                    if title == None:
                        title = "제목 없음"

                    else:
                        title = title.text.strip()

                    return_dict["title"] = title
                    theater_facility = soup.find(
                        "div", {"class": "theater-facility"})
                    facilities = []
                    theater_facilities = theater_facility.find_all("p")
                    for facility in theater_facilities:
                        facilities.append(facility.text)
                    return_dict["facilites"] = facilities
                    return_list.append(return_dict)
                    # find -> 1개
                    # find_all -> 전체다
                    address = soup.find_all(
                        "ul", {"class": "dot-list"})[1].find("li").text.replace("도로명주소 :  ", "")
                    return_dict["address"] = address

                    return_dict["floors"] = []
                    floors = soup.find_all(
                        "ul", {"class": "dot-list"})[0].find_all("li")

                    for floor in floors:
                        floor, value = floor.text.split(" : ")
                        value = value.split(", ")
                        return_dict["floors"].append({floor: value})
                    # print(return_dict["floors"])

                else:
                    print(f"request 응답 없음: {response}")
                    return [CrawlerResponse.FAIL, None]

                return [CrawlerResponse.SUCCESS, return_dict]

            except Exception as e:
                print(
                    f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return [CrawlerResponse.INTERNAL_SERVER_ERROR, None]

        @staticmethod
        def load_scedule_info(brch: str):
            url = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"
            response = requests.post(url, params={
                                     "brchNo": brch, "firstAt": "Y", "masterType": "brch", "playDe": "20230404"})
            print(len(response.json()["megaMap"]["movieFormList"]))

    class CGV:
        pass

    class LOTTE:
        pass


response, info_list = Crawler.MEGABOX.load_area_info(
    "https://www.megabox.co.kr/theater/list")
for info in info_list:
    for brch_no in info["info"]:
        Crawler.MEGABOX.load_scedule_info(brch_no["data_brch_no"])
        break
    break
