import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from db.models.category import Category, CategoryResult
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from typing import Tuple, Optional, List, Dict, Any
from pymysql.connections import Connection
from selenium import webdriver
from bs4 import BeautifulSoup
from enum import Enum
import traceback
import requests
import datetime
import re
from datetime import datetime, timedelta


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
        def load_area_info() -> Tuple[CrawlerResponse, Any]:
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
                print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.URL_NOT_FOUND, None)

            except Exception as e:
                print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)

        @ staticmethod
        def load_theather_info(brch_no: str) -> Tuple[CrawlerResponse, Any]:
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

                facilities = list(map(lambda x: x.text, soup.select("div.theater-facility > p")))

                floors = list(map(lambda x: x.text, soup.select("ul.dot-list")[1].select("li")))
                address = soup.select_one("ul.dot-list:nth-of-type(2) > li").text.replace("도로명주소 : ", "")

                kakao_map = soup.select_one("div.location-map-btn > div > a")["href"]
                locations = kakao_map.split("?")[1].split("&")[:2]
                lng, lat = float(locations[0].split("=")[1]), float(locations[1].split("=")[1])

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
                print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.URL_NOT_FOUND, None)

            except Exception as e:
                print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
                return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)

        @staticmethod
        def load_scedule_info(brch_no: str):
            play_date = datetime.datetime.now().date()
            url = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"
            return_list = []

            for i in range(19):
                response = requests.post(url, params={"brchNo": brch_no, "firstAt": "Y", "masterType": "brch", "playDe": play_date.strftime("%Y%m%d")})
                json_data = response.json()
                return_dict = {}

                movie_list = json_data["megaMap"]["movieFormList"]
                print(movie_list[0])
                print(f"brchNo: {brch_no}, " + f"{len(movie_list) / len(movie_list[0])}")

                play_date += datetime.timedelta(days=1)

            return (CrawlerResponse.SUCCESS, "Test")

    class CGV:
        pass

    class LOTTE:
        pass

class MovieCrawler:
    @staticmethod
    def load_movie_list() -> Tuple[CrawlerResponse, Any]:
        SIZE = 100
        url = f"https://movie.daum.net/api/premovie?page=1&size={SIZE}&flag=Y"
        try:
            response = requests.get(url)    
            return (CrawlerResponse.SUCCESS, list(i["id"] for i in response.json()["contents"]))
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)


    @staticmethod
    def load_cast_info(conn: Connection, movie_id: str) -> Tuple[CrawlerResponse, Optional[List[Dict[str, str]]]]:
        url = f"https://movie.daum.net/api/movie/{movie_id}/main"
        
        try:
            casts = requests.get(url).json()["casts"]
            return_list = []
            
            for cast in casts:
                person_id = cast["personId"]
                korean_name = cast["nameKorean"]
                english_name = cast["nameEnglish"]
                role = cast["movieJob"]["role"]
                profile_image = cast["profileImage"] if cast["profileImage"] not in ("", None) else None
                description = cast["description"] if cast["description"] not in ("", None) else None
                data = {
                    "person_id": person_id,
                    "korean_name": korean_name,
                    "english_name": english_name,
                    "role": role,
                    "profile_image": profile_image,
                    "description": description,
                }

                return_list.append(data)

            return (CrawlerResponse.SUCCESS, return_list)
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)
    
    
    @staticmethod
    def load_movie_id_from_cast(person_id: str):
        url = f"https://movie.daum.net/api/person/main/{person_id}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                datas = response.json()["casts"]
                return_list = []
                for data in datas:
                    return_list.append(data["movieId"])
                    
                return (CrawlerResponse.SUCCESS, return_list)
            
            else:
                print("url not found!!")
                return (CrawlerResponse.URL_NOT_FOUND, None)
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)
        

    @staticmethod
    def load_movie_info(conn: Connection, movie_id: str):
        url = f"https://movie.daum.net/api/movie/{movie_id}/main"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()["movieCommon"]
                
                movie_seq = data["id"]
                korean_title = data["titleKorean"]
                english_title = data["titleEnglish"]
                production_year = data["productionYear"]
                require_adult = data["adultOption"] == "T"
                main_photo_image = None
                if data["mainPhoto"] not in ("", None):
                    main_photo_image = data["mainPhoto"]["imageUrl"] if data["mainPhoto"]["imageUrl"] not in ("", None) else None
                
                plot = data["plot"]
                cookie_count = data["countCreditCookie"]
                total_audience_count = None if data["totalAudienceCount"] == None else int(data["totalAudienceCount"])
                daum_average_rating = None if data["avgRating"] == None else float(data["avgRating"])
                genres = ", ".join(data["genres"]).replace("/", ", ").split(", ")
                for genre in genres:
                    if not Category.check_exist_category(conn, genre):
                        result = Category.insert_category(conn, genre)
                        if result != CategoryResult.SUCCESS:
                            raise Exception("Error occured").with_traceback
                
                for idx in range(len(genres)):
                    genres[idx] = Category.load_category_seq(conn, genres[idx])[1][0]
                
                admission_code = None
                running_time = None
                reopen = None
                release_date = None
                for movie_info in data["countryMovieInformation"]:
                    if movie_info["country"]["nameKorean"] == "한국" and movie_info["releaseFlag"] == "Y":
                        admission_code = movie_info["admissionCode"]
                        running_time = movie_info["duration"]
                        reopen = movie_info["reopen"]
                        release_date = datetime.datetime.strptime(movie_info["releaseDate"], "%Y%m%d")
                        
                casts = []
                for cast in response.json()["casts"]:
                    casts.append(cast["personId"])
                    
                reservation_rank = data["reservationRank"]
                
                return (CrawlerResponse.SUCCESS, {
                    "movie_seq": movie_seq,
                    "korean_title": korean_title,
                    "english_title": english_title,
                    "summary": remove_html_tag_from_string(plot).replace(u"\xa0", " "),
                    "cookie_count": cookie_count,
                    "production_year": production_year,
                    "require_adult": require_adult,
                    "admission_code": admission_code,
                    "main_photo_image": main_photo_image,
                    "total_audience_count": total_audience_count,
                    "reservation_rank": reservation_rank,
                    "daum_average_rating": daum_average_rating,
                    "genres": genres,
                    "release_date": release_date,
                    "running_time": running_time,
                    "reopen": reopen,
                    "casts": casts,
                })
                
            else:
                return (CrawlerResponse.URL_NOT_FOUND, None)
        
        except Exception as e:
            print(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (CrawlerResponse.INTERNAL_SERVER_ERROR, None)
        


#today = datetime.now().strftime("%Y%M%D")
#url = f"https://m.movie.daum.net/data/movie/movie_info/box_office.json?startDate={today}&endDate={today}&pageNo=1&pageSize=10"

#respon = requests.get(url)
