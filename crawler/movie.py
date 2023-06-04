from bs4 import BeautifulSoup
import requests
import asyncio
import aiohttp
import json


class MovieCrawler:
    @staticmethod
    def get_release_movie_name_list():
        movie_name_list = []
        url = "https://movie.daum.net/api/premovie"
        page = 0
        running = True
        while running:
            page += 1
            response = requests.get(url, params={"page": page, "size": 50})
            if response.status_code == 200:
                json_data = response.json()
                if json_data["page"]["last"]:
                    running = False
                
                movie_name_list.append(list(map(lambda x: x["titleKorean"], json_data["contents"])))
                
            else:
                print("URL NOT FOUND")
                return None
            
        return sum(movie_name_list, [])
    

    @staticmethod
    async def convert_movie_name_to_movie_code(session, movie_name):
        url = "https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do"
        data = {
            "sMovName": movie_name,
            "sPrdtStatStr": "개봉",
            "sPrdtStatCd": 220210
        }
        
        async with session.post(url, data=data) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            table = soup.select_one("table.tbl_comm")
            try:
                return int(table.select_one("tbody > tr").select_one("td.tac > span").text.strip())
            
            except:
                pass
            
    
    @staticmethod
    async def get_movie_detail_from_movie_code(session, movie_code):
        url = "https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieDtl.do"
        data = {
            "code": movie_code,
            "titleYN": "Y",
            "isOuterReq": "false",
        }
        async with session.post(url, data = data) as response:
            if response.status == 200:
                movie_dict = {}
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find("dl", {"class": "ovf"})
                dts = list(map(lambda x: x.text.strip(), table.find_all("dt")))
                dds = table.find_all("dd")
                info2_keys = list(map(lambda x: x.text.strip(), soup.find_all("strong", {"class": "tit_type1"})))
                info2_values = soup.find_all("div", {"class": "info2"})
                escapes = ''.join([chr(char) for char in range(1, 32)])
                movie_infos = list(map(lambda x: x.strip().translate(str.maketrans('', '', escapes)), dds[dts.index("요약정보")].text.split("|")))
                movie_dict["korean_movie_name"] = soup.find("strong", {"class": "tit"}).text.strip()
                movie_dict["english_movie_name"] = soup.find("div", {"class": "hd_layer"}).find("div").text.split("(")[1].replace(")영화상영관상영중", "").translate(str.maketrans('', '', escapes))
                movie_dict["movie_type"] = movie_infos[0].strip().translate(str.maketrans('', '', escapes))
                movie_dict["movie_sort"] = movie_infos[1].strip().translate(str.maketrans('', '', escapes))
                movie_dict["genres"] = list(map(lambda x: x.strip(), movie_infos[2].split(", ")))            
                movie_dict["running_time"] = movie_infos[3].strip().translate(str.maketrans('', '', escapes))
                movie_dict["required_age"] = movie_infos[4].strip().translate(str.maketrans('', '', escapes))
                movie_dict["country"] = list(map(lambda x: x.strip().translate(str.maketrans('', '', escapes)), movie_infos[5].split(", ")))
                if len(movie_dict["country"]) == 1:
                    movie_dict["country"] = movie_dict["country"][0]
                else:
                    movie_dict["country"] = ', '.join(movie_dict["country"])
                movie_dict["release_date"] = dds[dts.index("개봉일")].text.strip().translate(str.maketrans('', '', escapes))
                
                try:
                    poster = soup.find("div", {"class": "poster"})
                    poster_images = list(map(lambda x: "https://www.kobis.or.kr" + x["src"].replace("thumb_x110", "thumb_x640"), poster.find_all("img")))
                    
                except AttributeError:
                    poster_images = None
                movie_dict["posters"] = poster_images
                
                try:
                    steel_cuts = soup.find("div", {"class": "steelcut"})
                    images = list(map(lambda x: "https://www.kobis.or.kr" + x["src"].replace("thumb_x132", "thumb_x640"), steel_cuts.find_all("img")))
                
                except AttributeError:
                    images = None
                movie_dict["steel_cuts"] = images
                
                try:
                    summary = info2_values[info2_keys.index("시놉시스")].find("p", {"class": "desc_info"}).text.strip().translate(str.maketrans('', '', escapes))

                except ValueError:
                    summary = None
                movie_dict["summary"] = summary
                
                movie_dict["casts"] = await MovieCrawler.get_cast_info_from_movie_code(session, movie_code)
                movie_dict["staff"] = await MovieCrawler.get_staff_info_from_movie_code(session, movie_code)
                for idx in range(len(movie_dict["casts"])):
                    movie_dict["casts"][idx]["movie_list"] = await MovieCrawler.get_movie_list_from_people_code(session, movie_dict["casts"][idx]["peopleCd"])
                    movie_dict["casts"][idx]["img"] = await MovieCrawler.get_people_image_from_people_code(session, movie_dict["casts"][idx]["peopleCd"])
                
                for idx in range(len(movie_dict["staff"])):
                    movie_dict["staff"][idx]["movie_list"] = await MovieCrawler.get_movie_list_from_people_code(session, movie_dict["staff"][idx]["peopleCd"])
                    movie_dict["staff"][idx]["img"] = await MovieCrawler.get_people_image_from_people_code(session, movie_dict["staff"][idx]["peopleCd"])
                
                return movie_dict
                
            else:
                print("URL NOT FOUND")
                return None
        
    
    @staticmethod
    async def get_cast_info_from_movie_code(session, movie_code):
        url = "https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovActorLists.do"
        async with session.post(url, data={"movieCd": movie_code}, headers={"Accept": "application/json"}) as response:
            json_data = json.loads(await response.text())
            if json_data == []:
                return []
            
            else:
                for data in json_data:
                    await MovieCrawler.get_people_image_from_people_code(session, data["peopleCd"])
                return list(map(lambda x: {key: x[key] for key in x.keys() & {"birYrMmdd", "cast", "peopleCd", "peopleNm", "peopleNmEn", "repRoleNm"}}, json_data))
    
    
    @staticmethod
    async def get_staff_info_from_movie_code(session, movie_code):
        url = "https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovStaffLists.do"
        async with session.post(url, data={"movieCd": movie_code, "mgmtMore": "N"}, headers={"Accept": "application/json"}) as response:
            json_data = json.loads(await response.text())
            if json_data == []:
                return []
            
            else:
                for data in json_data:
                    await MovieCrawler.get_people_image_from_people_code(session, data["peopleCd"])
                return list(map(lambda x: {key: x[key] for key in x.keys() & {"birYrMmdd", "cast", "peopleCd", "peopleNm", "peopleNmEn", "repRoleNm"}}, json_data))
    
    
    @staticmethod
    async def get_people_image_from_people_code(session, people_code):
        url = "https://www.kobis.or.kr/kobis/business/mast/peop/searchPeopleDtl.do"
        async with session.post(url, data={"code": people_code, "titleYN": "Y"}) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("div", {"class":"info1"})
            
            people = table.find("a")
            if people != None:
                people_image="https://www.kobis.or.kr"+ people.find("img")["src"]

            else:
                people_image = None

            return people_image
        
    
    @staticmethod
    async def get_movie_list_from_people_code(session, people_code):
        url = "https://www.kobis.or.kr/kobis/business/mast/peop/searchPeopleDtl.do"
        running = True
        page = 0
        movie_list = []
        while running:
            page += 1
            async with session.post(url, data={"code": people_code, "sType": "filmo", "etcParam": page}) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find("ul", {"class": "fmList"})
                movie_components = table.find_all("li")
                if len(movie_components) != 10:
                    running = False
                    
                for theater_component in movie_components:
                    movie = {}
                    if theater_component.find("p").find("a").find("img")["src"].replace("thumb_x110", "thumb_x640") != "":
                        movie["image"] = "https://www.kobis.or.kr" + theater_component.find("p").find("a").find("img")["src"].replace("thumb_x110", "thumb_x640")
                    
                    else:
                        movie["image"] = None
                    
                    data = theater_component.find_all("dd")
                    movie["title"] = theater_component.find("dl").find("dt").text.strip()
                    movie["role"] = data[0].text.strip().replace(": ", "")
                    info = data[1].text
                    if info != None:
                        minfos = info.split(" | ")
                        movie["release_year"] = minfos[0]
                        movie["country"] = minfos[1]
                        movie["genres"] = ", ".join(minfos[2].split(","))
                        
                    movie["benefit"] = data[2].find("em").text
                    if movie["benefit"] == "원":
                        movie["benefit"] = "0원"
                        
                    movie["audience"] = data[2].find_all("em")[1].text
                    if movie["audience"] == "명":
                        movie["audience"] = "0명"
                        
                    movie_list.append(movie)
        
        return movie_list

async def main():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=100000)) as session:
        movie_name_list = MovieCrawler.get_release_movie_name_list()
        tasks = [MovieCrawler.convert_movie_name_to_movie_code(session, movie_name) for movie_name in movie_name_list]
        result = set(await asyncio.gather(*tasks))
        result.discard(None)
        tasks = [MovieCrawler.get_movie_detail_from_movie_code(session, movie_code) for movie_code in result]
        result = await asyncio.gather(*tasks)
        return result


if __name__ == "__main__":
    import time
    start = time.time()
    results = asyncio.run(main())
    print(results[0])
    print(time.time() - start)