import requests
import re

def remove_html_tag(html: str):
    return re.sub(re.compile('<.*?>'), '', html)


class MovieCrawler:
    @staticmethod
    def get_movie_id_list_released():
        url = "https://movie.daum.net/api/premovie?"
        page = 0
        return_list = []
        while True:
            page += 1
            response = requests.get(url, params={
                "page": page,
                "size": 20,
                "flag": "Y"
            })
            
            if response.status_code == 200:
                json = response.json()
                if json["page"]["last"]:
                    break
                
                for content in json["contents"]:
                    return_list.append(content["id"])
                
            else:
                print("URL NOT FOUND")
                return None
        
        return return_list
    
    
    @staticmethod
    def get_movie_detail(movie_id: int):
        url = f"https://movie.daum.net/api/movie/{movie_id}/main"
        response = requests.get(url)
        if response.status_code == 200:
            json = response.json()
            data = json["movieCommon"]
            return {
                "id": movie_id,
                "korean_title": data["titleKorean"],
                "english_title": data["titleEnglish"],
                "summary": remove_html_tag(data["plot"]).replace("\xa0", ""),
                "country": data["productionCountries"],
                "production_year": data["productionYear"],
                "adult_option": data["adultOption"],
                "rating": data["avgRating"],
                "cookies": data["countCreditCookie"],
                "genres": data["genres"],
                "photos": MovieCrawler.get_photo_list(movie_id),
                "image_url": data["mainPhoto"]["imageUrl"],
                "country_movie_info": data["countryMovieInformation"],
                "casts": json["casts"]
            }
            
        else:
            print("URL NOT FOUND")
            return None
        
    
    @staticmethod
    def get_photo_list(movie_id: int):
        url = f"https://movie.daum.net/api/movie/{movie_id}/photoList"
        photo_list = []
        page = 0
        
        while True:
            page += 1    
            response = requests.get(url, params={
                "page": page,
                "size": 12,
                "adultFlag": "T"
            })
            
            if response.status_code == 200:
                json = response.json()
                if json["page"]["last"]:
                    break
                
                contents = json["contents"]
                for content in contents:
                    photo_list.append(content["imageUrl"])

                
            else:
                print("URL NOT FOUND")
                return None
        
        return photo_list