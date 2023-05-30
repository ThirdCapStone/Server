from bs4 import BeautifulSoup
import requests


class Movie:
    @staticmethod
    def get_CSRF_Token():
        response = requests.get("https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser").body
            paging_form = soup.find("form", {"action": "searchMovieList.do", "name": "pagingForm", "id": "pagingForm", "method": "post"})
            CSRF_input = paging_form.find("input")
            CSRF_value = CSRF_input["value"]
            
            return CSRF_value
            
        else:
            print("URL NOT FOUND")
            return None
        
    
    @staticmethod
    def get_movie_list():
        idx = 0
        return_list = []
        while True:
            print("running")
            idx += 1
            response = requests.post("https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do", data={
                "CSRFToken": Movie.get_CSRF_Token(),
                "curPage": idx,
                "sNomal": "Y",
                "sMulti": "Y",
                "sIndie": "Y",
                "useYn": "Y",
                
            })
            soup = BeautifulSoup(response.text, "html.parser")
            
            movie_trs = soup.find("table", {"class": "tbl_comm"}).find("tbody").find_all("tr")
            for movie in movie_trs:
                tds = movie.find_all("td")
                return_list.append({
                    "korean_title": tds[0].text.strip(),
                    "english_title": tds[1].text.strip(),
                    "movie_code": tds[2].text.strip(),
                    "created_year": tds[3].text.strip(),
                    "from_country": tds[4].text.strip(),
                    "movie_type": tds[5].text.strip(),
                    "genre": tds[6].text.strip(),
                    "release_type": tds[7].text.strip(),
                })
            
            if len(movie_trs) != 10:
                break
            
        return return_list
                
    
    @staticmethod
    def get_movie_detail_info(movie_code: str):
        response = requests.post("https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieDtl.do", data={
            "code": movie_code,
            "CSRFToken": Movie.get_CSRF_Token(),
            "titleYN": "Y",
            "isOuterReq": "false"
        })

        soup = BeautifulSoup(response.text, "html.parser")
        print(soup.find("div", {"class", "info"}))

print(Movie.get_movie_list())