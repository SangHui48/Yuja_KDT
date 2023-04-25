# requirement import
import openai
import streamlit as st
import json
import requests
import googletrans
from GenerateWeather import GenerateWeather

# Set the GPT-3 API key
with open('./api_key.json') as f:
    data = json.load(f)
openai.api_key = data['open_ai']
stable_diffusion_key = data['stable_diffusion']

#prompt용 dict
style_dict = {
        '아메리칸 케주얼': 'American casual',
        '케주얼': 'casual',
        '시크': 'chic',
        '댄디' : 'dandy',
        '포멀': 'formal' ,
        '골프': 'golf',
        '홈웨어': 'homeware',
        '스포츠': 'sports',
        '스트릿': 'street',
        '고프코어': 'gorpcore',
        }

style_dict_woman = {
        '아메리칸 케주얼': 'American casual',
        '케주얼': 'casual',
        '시크': 'chic',
        '포멀': 'formal' ,
        '걸리시': 'girlish',
        '골프': 'golf',
        '홈웨어': 'homeware',
        '레트로': 'retro',
        '로맨틱': 'romantic',
        '스포츠': 'sports',
        '스트릿': 'street',
        '고프코어': 'gorpcore',
        }

body_dict = {
    '삼각형 체형':'triangle body type',
    '역삼각형 체형':'inverted triangle body type',
    '직사각형 체형':'rectangle body type',
    '타원형의 체형':'oval body type',
    '호리병 체형':'hour glass body type',
}

st.title("chatGPT 활용 코디 추천")

with st.form("form_index", clear_on_submit=True):
    gender = st.selectbox('성별', options=['남자', '여자'], on_change=gender_callback index=0, key='gender')
    if st.session_state.gender == '남자':
        st.selectbox('원하는 스타일', options=list(style_dict.keys()), index=0)
    else:
        st.selectbox('원하는 스타일', options=list(style_dict_woman.keys()), index=0)
    bodyshape = st.selectbox('체형', options=list(body_dict.keys()))
    # color = st.selectbox('선호하는 색깔', options=)
    height = st.text_input('신장(키)')
    weight = st.text_input('몸무게')
    age = st.text_input('나이')
    submit = st.form_submit_button('제출')
    if submit:
        if height == "":
            st.error('신장(키)은 필수값입니다.')
            st.stop()
        elif not height.isdigit():
            st.error('신장(키)은 숫자로만 입력해야 합니다')
            st.stop()
        elif int(height) <= 150 or  int(height) > 200:
             st.error('신장(키)은 150이상 200이하의 값만 가능합니다.')
             st.stop()

        if weight == "":
            st.error('몸무게는 필수값입니다.')
            st.stop()
        elif not weight.isdigit():
            st.error('몸무게는 숫자로만 입력해야 합니다')
            st.stop()
        elif int(weight) < 40 or int(weight) > 120:
            st.error('몸무게는 40이상 120이하의 값만 가능합니다.')
            st.stop() 

        if age == "":
            st.error('나이는 숫자로만 입력해야 합니다')
            st.stop()
        elif not age.isdigit():
            st.error('나이는 숫자로만 입력해야 합니다')
            st.stop()

        sex = 'male' if gender == '남자' else 'female'

        # 날씨 받아오기
        try:
            weather = GenerateWeather().__call__()
        except Exception:
            st.error('날씨 조회에 실패 했습니다.')
            weather = None

        # openai 제출용 params
        params = {
            'gender': sex,
            'style': style_dict[style],
            'height': height,
            'weight': weight,
            'age': age,
            'weather': weather, # dict()
            'body_shape': body_dict[bodyshape],
            # 'situation': res,
        }
        # 패션 추천 받아오기, openai prompt template
        if weather:
            template_gpt = f'''
                You should recommend one item for each category(outer, top, bottom, shoes, accesories) and match well with each other. I am {params['height']}cm, {params['weight']}kg, {params['age']} years old woman. My body shape is {params['body_shape']}. I like {params['style']} style.
                It's {params['weather']['sky']} and the temperature is between {params['weather']['tmp_low']}~{params['weather']['tmp_hig']}. The probability of precipitation is 80%.
                Recommend fashion with color without brand or size.

                You should reply only to the items you recommend in 1 sentence without any special symbol or number, and not to reply otherwise. 
                Separate other categories with a dot.
                '''
        else:
            template_gpt = f'''
                You should recommend one item for each category(outer, top, bottom, shoes, accesories) and match well with each other. I am {params['height']}cm, {params['weight']}kg, {params['age']} years old woman. My body shape is {params['body_shape']}. I like {params['style']} style.
                Recommend fashion with color without brand or size.

                You should reply only to the items you recommend in 1 sentence without any special symbol or number, and not to reply otherwise. 
                Separate other categories with a dot.
                '''
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=template_gpt,
                max_tokens = 3000,
                temperature = 0.5,
            )
            res = response['choices'][0]['text']
        except Exception:
            st.error('GPT API에 문제가 있습니다.')
            st.stop()
        # chatGPT 추천 결과를 이용해 stable diffustion 프롬프트용 템플릿 재생성
        # 결과 예시
        # 남자, 72, 182cm, 80kg A tailored navy blazer , A light white dress shirt , Khaki trousers/chinos , Brown loafers
        # template_sd = f"{params['gender']}, {params['age']}, {params['height']}cm, {params['weight']}kg,"
        # template_sd += res.replace('.', ',')
        decorator = 'handsome' if params['gender'] == 'man' else 'beautiful'
        template_sd = f'''
            ultra detail, ultra realistic, 8K, 3D, natural light, photorealism: {decorator}, {params['age']}, {params['height']}cm, {params['weight']}kg, ({params['gender']}:1.5), (well-proportioned:1.5),
            {params['body_shape']}, fashion model, {params['style']},
        '''
        options = res.replace('.', ',')
        template_sd += options
        try:
            url = 'https://stablediffusionapi.com/api/v3/text2img'
            data = {
                "key": stable_diffusion_key,
                "prompt": template_sd,
                "width": "1000",
                "height": "1000",
                "samples": "1",
            }
            response = requests.post(url, data=data)
            res = response.json()
            result_url = res['output'][0]
        except Exception:
            st.error('패션 추천중 문제가 발생했습니다.(Stable Diffusion Error)')

        # 결과 이미지 출력
        st.write(f"입력하신 조건값: {params['gender']}, {params['age']}, {params['height']}cm, {params['weight']}kg,{params['body_shape']}, {params['style']}")
        st.write('=====================================')
        st.write(f"GPT는 다음과 같은 옷들을 추천해 줬어요: {options}")
        st.write('=====================================')
        st.image(result_url, width=400)