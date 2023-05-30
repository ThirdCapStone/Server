from .env import kakao_key
import requests


class TheaterCrawler:
    @staticmethod
    def get_city_list():
        data = "서울시 경기도 강원도 충청북도 충청남도 경상북도 경상남도 전라북도 전라남도 제주도 부산시 대구시 대전시 울산시 인천시 광주시 세종시".split(" ")
        for idx in range(len(data)):
            data[idx] = {"cd": "01050" + str(idx + 1).rjust(2, "0"), "cdNm": data[idx]}
            
        return data


    @staticmethod
    def get_gu_list(sWideareaCd: str):
        response = requests.post("https://www.kobis.or.kr/kobis/business/mast/thea/findBasareaCdList.do?CSRFToken=HgMAHNIl1l4gllyVmp7LOG6bExrD_B6SlsXo17bfqSQ", data={"sWideareaCd": sWideareaCd, "CSRFToken": "HgMAHNIl1l4gllyVmp7LOG6bExrD_B6SlsXo17bfqSQ"})
        data = response.json()["basareaCdList"]
        return data
    
    
    @staticmethod
    def get_theater_list(sBasareaCd: str):
        response = requests.post("https://www.kobis.or.kr/kobis/business/mast/thea/findTheaCdList.do?CSRFToken=HgMAHNIl1l4gllyVmp7LOG6bExrD_B6SlsXo17bfqSQ",  data={"sBasareaCd": sBasareaCd, "CSRFToken": "HgMAHNIl1l4gllyVmp7LOG6bExrD_B6SlsXo17bfqSQ"})
        data = response.json()["theaCdList"]
        for idx in range(len(data)):
            data[idx]["info"] = TheaterCrawler.get_coordinate(data[idx]["cdNm"])
            
        return data
    
        
    @staticmethod
    def get_coordinate(address: str):
        result = ""
        address = address.replace("_샤롯데", "")
        address = address.replace("_Charlotte관", "")
        
        url = f'https://dapi.kakao.com/v2/local/search/keyword.json?query={address}&size=1'
        
        header = {'Authorization': 'KakaoAK ' + kakao_key}

        response = requests.get(url, headers=header)
        if response.status_code == 200:
            if len(response.json()['documents']) != 0:
                result_address = response.json()["documents"][0]
                result = {
                    "place_name": result_address["place_name"],
                    "address": result_address["address_name"],
                    "road_address": result_address["road_address_name"],
                    "lat": result_address["y"],
                    "long": result_address["x"],
                }
                
            else:
                pass 
                if "CGV" or "롯데시네마" or "메가박스" in address:
                    pass
        
        else:
            print("URL 주소가 잘못됐습니다.")

        return result
    