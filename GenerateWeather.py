import requests
import sys, os
# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))  # <- 뭐하는 코든지 잘 모르겠음
# import config # <- 원래 api 여기 담아두신것 같은데, 제 기상청 api 코드에 넣었습니다.
from datetime import datetime


GEOLOCATION_API_KEY = "a48461f0b4f948cc8be8d515591c320b"

class GenerateWeather():
    def __init__(self):
        self.loc_to_nx_ny()
        self.weather_data = self.return_weather_degree()

    def __call__(self):
        return self.weather_data

    def get_location(self, ip):
        location = requests.get("https://ips-backend-3q6nicdgla-du.a.run.app/ips?key=ga-test-key0&ip={}".format(ip)).json()
        return location

    def get_geolocation(self):
        try:
            response = requests.get("https://api.ipgeolocation.io/ipgeo?apiKey=" + GEOLOCATION_API_KEY).json()
            return response['ip']
        except ConnectionError as e:
            return "서울"


    # location의 위도(nx), 경도(ny) 출력 메서드
    def loc_to_nx_ny(self):
        nx_ny_dict = {'서울특별시':[60, 127],
                      '부산광역시':[98, 76],
                      '대구광역시':[89, 90],
                      '인천광역시':[55, 124],
                      '광주광역시':[58, 74],
                      '대전광역시':[67, 100],
                      '울산광역시':[102, 84],
                      '세종특별자치시':[66, 103],
                      '경기도':[60, 120],
                      '강원도':[73, 134],
                      '충청북도':[69, 107],
                      '충청남도':[68, 100],
                      '전라북도':[63, 89],
                      '전라남도':[51, 67],
                      '경상북도':[89, 91],
                      '경상남도':[91, 77],
                      '충북':[69, 107],
                      '충남':[68, 100],
                      '전북':[63, 89],
                      '전남':[51, 67],
                      '경북':[89, 91],
                      '경남':[91, 77],
                      '제주특별자치도':[52, 38],
                      '이어도':[28, 8]}
        
        ip = self.get_geolocation() # ip 가져오기
        location = self.get_location(ip)
        if (ip[0].isdigit()==False) or (location['addr1'] == None):
            nx, ny = [60, 127] # ip 존재하지 않는 경우/주소가 None인 경우, 서울로 default
        else:
            for i in nx_ny_dict:
                if (location['addr1'] in i):
                    nx,ny = nx_ny_dict[i]
                    break
        # nx,ny = nx_ny_dict(location)
        return nx,ny
    

    # location의 초단기실황 예보 api 요청
    # serviceKey : 날씨정보 api
    # 날씨정보 dict로 관리 (weather_data)
    def request_weather(self,nx,ny):
        now = datetime.now()
        today = datetime.today().strftime("%Y%m%d")

        pageNo = '1'       # 페이지수
        numOfRows = '1000' # 페이지 내에서 가져올 데이터 수

        # 초단기실황 예보 가져오기
        url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
        params ={'serviceKey' : 'NRGSJlXablH4tNy/pl1xfeOFw7/Bz6btS7ipC37Agg0hFyJsIfY3BBLXMRbK3xxona7QX3vB3v52GPnVRPh5Ng==', 
                'pageNo' : pageNo, 
                'numOfRows' : numOfRows, 
                'dataType' : 'JSON', 
                'base_date' : today, 
                'base_time' : '0500', # 기상청 발표시간이라 수정하시면 request 못받아보실수도 있습니다.
                'nx' : nx, 
                'ny' : ny }

        # 데이터 가져오기
        response = requests.get(url, params=params)
        items = response.json().get('response').get('body').get('items')

        # 날씨 정보 dict
        weather_data = dict()
        for item in items['item']:
            # 일 최저기온
            if item['category'] == 'TMN':
                weather_data['tmp_low'] = item['fcstValue']+'℃'
            # 일 최고기온
            if item['category'] == 'TMX':
                weather_data['tmp_hig'] = item['fcstValue']+'℃'
            # 하늘 상태: 맑음(1) 구름많은(3) 흐림(4)
            if item['category'] == 'SKY':
                weather_data['sky'] = self.decode_sky(item['fcstValue'])
            # 풍속
            # if item['category'] == 'WSD':
            #     weather_data['wind'] = item['fcstValue']+'m/s'
            # 강수 확률
            if item['category'] == 'POP':
                weather_data['rain'] = item['fcstValue']
            # 습도
            # if item['category'] == 'REH':
            #     weather_data['hum'] = item['fcstValue']
        if int(weather_data['rain']) >= 60:
            weather_data['sky'] = 'rainy'
        return weather_data

    def decode_sky(self, sky_encoded):
        if sky_encoded == '1':
            return 'sunny'
        if sky_encoded == '2':
            return 'cloudy'
        if sky_encoded == '3':
            return 'overcast'

    def return_weather_degree(self) :
        nx,ny = self.loc_to_nx_ny()
        weather_data = self.request_weather(nx,ny)
        return weather_data

