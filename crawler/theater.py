from env import kakao_key
import asyncio
import json


class TheaterCrawler:
    @staticmethod
    async def get_city_list():
        data = "서울시 경기도 강원도 충청북도 충청남도 경상북도 경상남도 전라북도 전라남도 제주도 부산시 대구시 대전시 울산시 인천시 광주시 세종시".split(" ")
        for idx in range(len(data)):
            data[idx] = {"cd": "01050" + str(idx + 1).rjust(2, "0"), "cdNm": data[idx]}
            
        return data


    @staticmethod
    async def get_gu_list(session, sWideareaCd: str):
        async with session.post("https://www.kobis.or.kr/kobis/business/mast/thea/findBasareaCdList.do", data={"sWideareaCd": sWideareaCd}) as response:
            text = await response.text()
            data = json.loads(text)["basareaCdList"]
            return data
    
    
    @staticmethod
    async def get_theater_list(session, sBasareaCd):
        async with session.post("https://www.kobis.or.kr/kobis/business/mast/thea/findTheaCdList.do",  data={"sBasareaCd": sBasareaCd}) as response:
            text = await response.text()
            data = json.loads(text)["theaCdList"]
            return list(map(lambda x: x["cd"], data))
        
    
    
    @staticmethod
    async def get_theater_list_with_detail(session, sBasareaCd: str):
        async with session.post("https://www.kobis.or.kr/kobis/business/mast/thea/findTheaCdList.do",  data={"sBasareaCd": sBasareaCd}) as response:
            text = await response.text()
            data = json.loads(text)["theaCdList"]
            for idx in range(len(data)):
                data[idx]["info"] = await TheaterCrawler.get_coordinate(session, data[idx]["cdNm"])
                
            return data
        
        
    @staticmethod
    async def get_coordinate(session, address: str):
        result = ""
        address = address.replace("_샤롯데", "")
        address = address.replace("_Charlotte관", "")
        
        url = f'https://dapi.kakao.com/v2/local/search/keyword.json?query={address}&size=1'
        
        header = {'Authorization': 'KakaoAK ' + kakao_key}

        async with session.get(url, headers=header) as response:
            text = await response.text()
            # print(json.loads(text))
            try:
                if len(json.loads(text)['documents']) != 0:
                    result_address = json.loads(text)["documents"][0]
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
            except:
                result = None
            

            return result
