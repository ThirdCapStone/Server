import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from db.models.category import Category, CategoryResult
from typing import Tuple, Optional, List, Dict, Union
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from pymysql.connections import Connection
from selenium import webdriver
from bs4 import BeautifulSoup
from enum import Enum
import traceback
import requests
import datetime
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


def remove_escape_character_from_string(data: str) -> str:
    escapes = ''.join([chr(char) for char in range(1, 32)])
    translator = str.maketrans('', '', escapes)
    data = data.translate(translator)
    return data


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option("detach", True)
driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install()), options=chrome_options)


class TheaterCrawler:
    class MEGABOX:
        @ staticmethod
        def load_area_info() -> Tuple[CrawlerResponse, Optional[List[Dict[str, Union[str, List[Dict[str, str]]]]]]]:
            url = "https://www.megabox.co.kr/theater/list"
            try:
                return_list = []
                driver.get(url)
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                for place in soup.select("div.theater-place > ul > li"):
                    info_list = []
                    for theater in place.select("div.theater-list > ul > li"):
                        info_list.append({
                            "title": theater.a.text,
                            "brch_no": theater["data-brch-no"] 
                        })
                    return_list.append({
                        "city": remove_escape_character_from_string(place.button.text),
                        "theaters": info_list
                    })
                    
                return (CrawlerResponse.SUCCESS, return_list)

            except WebDriverException as e:
                print(
                    f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.URL_NOT_FOUND, None)

            except Exception as e:
                print(
                    f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)

        @ staticmethod
        def load_theather_info(brch_no: str) -> Tuple[CrawlerResponse, Optional[Dict[str, Union[str, float, List[str]]]]]:
            url = f"https://www.megabox.co.kr/theater?brchNo={brch_no}"
            try:
                driver.get(url)
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                titles = soup.select_one("div.theater-info-text")

                if titles != None:
                    title = titles.select_one("p.big").text.strip()
                    subtitle = titles.select_one("p:last-child").text.strip()

                else:
                    title = None
                    subtitle = None

                facilities = list(map(lambda x: x.text, soup.select(
                    "div.theater-facility > p")))

                floors = list(map(lambda x: x.text, soup.select(
                    "ul.dot-list")[1].select("li")))
                address = soup.select_one(
                    "ul.dot-list:nth-of-type(2) > li").text.replace("도로명주소 : ", "")

                kakao_map = soup.select_one(
                    "div.location-map-btn > div > a")["href"]
                locations = kakao_map.split("?")[1].split("&")[:2]
                lng, lat = float(locations[0].split(
                    "=")[1]), float(locations[1].split("=")[1])

                floors = []
                for floor in floors:
                    floor, value = floor.split(" :  ")
                    value = value.split(", ")
                    floors.append({floor: value})

                return (CrawlerResponse.SUCCESS, {
                    "title": title,
                    "subtitle": subtitle,
                    "facilities": facilities,
                    "address": address,
                    "lng": lng,
                    "lat": lat,
                    "floors": floors
                })

            except WebDriverException as e:
                print(
                    f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.URL_NOT_FOUND, None)

            except Exception as e:
                print(
                    f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)

        @staticmethod
        def load_scedule_info(brch_no: str):
            play_date = datetime.datetime.now().date()
            url = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"
            return_list = []

            for i in range(19):
                response = requests.post(url, params={
                    "brchNo": brch_no, "firstAt": "Y", "masterType": "brch", "playDe": play_date.strftime("%Y%m%d")})
                json_data = response.json()
                return_dict = {}

                movie_list = json_data["megaMap"]["movieFormList"]
                print(movie_list[0])
                print(f"brchNo: {brch_no}, " +
                      f"{len(movie_list) / len(movie_list[0])}")

                play_date += datetime.timedelta(days=1)

            return (CrawlerResponse.SUCCESS, "Test")

    class CGV:
        pass

    class LOTTE:
        pass

class MovieCrawler:
    @staticmethod
    def load_movie_list() -> Tuple[CrawlerResponse, Optional[List[str]]]:
        SIZE = 100
        url = f"https://movie.daum.net/api/premovie?page=1&size={SIZE}&flag=Y"
        try:
            response = requests.get(url)    
            return (CrawlerResponse.SUCCESS, list(i["id"] for i in response.json()["contents"]))
        
        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)

    @staticmethod
    def load_cast_info(conn: Connection, movie_id: str) -> Tuple[CrawlerResponse, Dict[str, str]]:
        url = f"https://movie.daum.net/api/movie/{movie_id}/main"
        
        try:
            casts = requests.get(url).json()["casts"]
            return_list = []
            
            korean_name = cast["nameKorean"]
            english_name = cast["nameEnglish"]
            role = cast["movieJob"]["role"]
            profile_image = cast["profileImage"] if cast["profileImage"] not in ("", None) else None
            description = cast["description"] if cast["description"] not in ("", None) else None
            
            for cast in casts:
                data = {
                    "korean_name": korean_name,
                    "english_name": english_name,
                    "role": role,
                    "profile_image": profile_image,
                    "description": description,
                }

                return_list.append(data)

            return (CrawlerResponse.SUCCESS, return_list)
        
        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)
            


    @staticmethod
    def load_movie_info(conn: Connection, movie_id: str):
        url = f"https://movie.daum.net/api/movie/{movie_id}/main"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()["movieCommon"]
                korean_title = data["titleKorean"]
                english_title = data["titleEnglish"]
                production_year = data["productionYear"]
                require_adult = data["adultOption"]
                plot = data["plot"]
                main_photo_image = None
                if data["mainPhoto"] not in ("", None):
                    main_photo_image = data["mainPhoto"]["imageUrl"] if data["mainPhoto"]["imageUrl"] not in ("", None) else None
                genres = ", ".join(data["genres"]).replace("/", ", ").split(", ")
                
                for genre in genres:
                    if not Category.check_exist_category(conn, genre):
                        result = Category.insert_category(conn, genre)
                        if result != CategoryResult.SUCCESS:
                            raise Exception("Error occured").with_traceback
                        
                for idx in range(len(genres)):
                    genres[idx] = Category.load_category_seq(conn, genres[idx])[1][0]
                
                return (CrawlerResponse.SUCCESS, {
                    "korean_title": korean_title,
                    "english_title": english_title,
                    "plot": remove_html_tag_from_string(plot).replace(u"\xa0", " "),
                    "production_year": production_year,
                    "require_adult": require_adult,
                    "main_photo_image": main_photo_image,
                    "genres": genres
                })
                
            else:
                return (CrawlerResponse.URL_NOT_FOUND, None)
        
        except Exception as e:
            print(
                f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)
      
        
