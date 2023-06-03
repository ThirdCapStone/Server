from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import asyncio
import traceback
import aiohttp

session = None

class MovieCrawler:
    @staticmethod
    def get_CSRF_Token():
        print("detected")
        response = requests.get("https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            paging_form = soup.find("form", {"action": "searchMovieList.do", "name": "pagingForm", "id": "pagingForm", "method": "post"})
            CSRF_input = paging_form.find("input")
            CSRF_value = CSRF_input["value"]

            return CSRF_value

        else:
            print("URL NOT FOUND")
            return None
        
    
    @staticmethod
    def get_movie_page():
        response = requests.get("https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            movie_cnt = soup.find("div", {"class": "hd_rst"}).find("span", {"class": "total"}).find("em", {"class": "fwb"}).text
            return (int(movie_cnt.replace(",", "")) - 1) // 10 + 1
            
        else:
            print("URL NOT FOUND")
            return None 


    @staticmethod
    async def get_movie_code_list(session, page):
        data = {
            "curPage": page,
            "sNomal": "Y",
            "sMulti": "Y",
            "sIndie": "Y",
            "useYn": "Y",
        }
        headers = {
            "User-Agent": UserAgent().random,
        }
        return_list = []
        url = "https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do"
        async with session.post(url, data=data, headers=headers) as response:
            response_text = await response.text()
            soup = BeautifulSoup(response_text, "html.parser")
            movie_trs = soup.find("table", {"class": "tbl_comm"}).find("tbody").find_all("tr")
            
            for movie in movie_trs:
                tds = movie.find_all("td")
                return_list.append(tds[2].text.strip())

            return return_list

    
    @staticmethod
    def get_movie_detail_info(movie_code: str):
        response = requests.post("https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieDtl.do", data={
            "code": movie_code,
            "CSRFToken": MovieCrawler.get_CSRF_Token(),
            "titleYN": "Y",
            "isOuterReq": "false"
        })

        soup = BeautifulSoup(response.text, "html.parser")
        print(soup.find("div", {"class", "info"}))
        

async def main():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total = 1000)) as session:
        tasks = [MovieCrawler.get_movie_code_list(session, page) for page in range(1, MovieCrawler.get_movie_page() + 1)]
        movie_lists = await asyncio.gather(*tasks)
        return movie_lists

if __name__ == "__main__":
    results = sum(asyncio.run(main()), [])
    results = set(results)
    results.discard(None)