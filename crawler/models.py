from typing import List, Dict, Union
from datetime import datetime
from bs4 import BeautifulSoup
from enum import Enum
import requests


class CrawlerResponse(Enum):
    FAIL = 0
    SUCCESS = 1
    DATAREQUIRED = 2
    URLNOTFOUND = 3
    SERVERERROR = 4


class MovieTicketRankCrawler:
    
    @staticmethod
    def load_info() -> List[Union[Dict[str, int], Dict[str, str], Dict[str, datetime], Dict[str, float]]]:
        url = "https://www.kobis.or.kr/kobis/business/stat/boxs/findRealTicketList.do"
        
        formdata = {
            "loadEnd": "0",
            "areaCd": "0105001:0105002:0105003:0105004:0105005:0105006:0105007:0105008:0105009:0105010:0105011:0105012:0105013:0105014:0105015:0105016:",
            "repNationCd": "1",
        }
        response = requests.get(url, formdata)
        if response.status_code == 404:
            raise CrawlerResponse.URLNOTFOUND
        
        soup = BeautifulSoup(response.text, "html.parser")
        try:
            movie_list = soup.find("table", {"class": "tbl_comm th_sort"}).find("tbody").find_all("tr")
            return_list = []
            
            for movie in movie_list:
                tds = movie.find_all("td")
                rank = int(tds[0].text)
                title = movie.find("span", {"class": "ellip per90"}).find("a").text
                try:
                    release_date = datetime.strptime(''.join(tds[2].text.split()), "%Y-%m-%d")
                except ValueError:
                    release_date = None
                ticketing_rate = float(tds[3].text[:-1])
                ticketing_sales = tds[4].text
                ticketing_sales_sum = tds[5].text
                ticketing_audience = tds[6].text
                ticketing_audience_sum = tds[7].text
                search_date = datetime.now()
                
                return_dict = dict()
                return_type_list = "rank title release_date ticketing_rate ticketing_sales ticketing_sales_sum ticketing_audience ticketing_audience_sum search_date".split(" ")
                
                for name in return_type_list:
                    exec(f'return_dict["{name}"] = {name}')
                
                return_list.append(return_dict)
                
            return return_list
        
        except ValueError:
            raise CrawlerResponse.DATAREQUIRED
        
        except:
            raise CrawlerResponse.SERVERERROR
