"""Reproducible fictional adult profiles and local vector avatars. No real user data."""
from pathlib import Path
import json
import random

ROOT = Path(__file__).resolve().parents[1]
rng = random.Random(20261016)
female = [('آوا','Ava'),('مهسا','Mahsa'),('ترانه','Taraneh'),('یلدا','Yalda'),('نازنین','Nazanin'),('مهتاب','Mahtab'),('نگار','Negar'),('شیدا','Sheida'),('پرنیا','Parnia'),('غزل','Ghazal'),('بهار','Bahar'),('هستی','Hasti'),('دلارام','Delaram'),('مینا','Mina'),('آیدا','Aida'),('پریسا','Parisa'),('ستاره','Setareh'),('کیمیا','Kimia'),('سحر','Sahar'),('نوشین','Noushin'),('درسا','Dorsa'),('روژان','Rozhan'),('نیلوفر','Niloufar'),('ماندانا','Mandana'),('شقایق','Shaghayegh')]
male = [('آراد','Arad'),('سامان','Saman'),('کیان','Kian'),('بردیا','Bardia'),('نیما','Nima'),('آبتین','Abtin'),('سام','Sam'),('پرهام','Parham'),('آرمان','Arman'),('امیر','Amir'),('شایان','Shayan'),('اشکان','Ashkan'),('سپهر','Sepehr'),('پوریا','Pouria'),('پیمان','Peyman'),('مازیار','Maziar'),('بهراد','Behrad'),('روزبه','Rouzbeh'),('هومن','Hooman'),('سینا','Sina'),('فربد','Farbod'),('شروین','Shervin'),('رهام','Roham'),('دانیال','Danial'),('احسان','Ehsan')]
jobs = [('طراح محصول','product designer'),('معمار','architect'),('برنامه‌نویس','software developer'),('تصویرگر','illustrator'),('پژوهشگر','researcher'),('مترجم','translator'),('عکاس','photographer'),('مدرس موسیقی','music teacher'),('مهندس عمران','civil engineer'),('ویراستار','editor')]
cities = [('تهران','Tehran'),('کرج','Karaj'),('شیراز','Shiraz'),('اصفهان','Isfahan'),('رشت','Rasht')]
interests = ['coffee','music','travel','photo','art','hiking','books','cinema']
activities = [('کشف کافه‌های کوچک و شنیدن داستان آدم‌ها','small cafés and listening to people’s stories'),('قدم زدن کنار طبیعت و عکاسی از نور عصر','nature walks and photographing evening light'),('کتاب‌فروشی‌های قدیمی و سینمای مستقل','old bookshops and independent cinema'),('آشپزی با موسیقی و سفرهای کوتاه','cooking with music and short trips'),('نمایشگاه‌های هنری و گفتگوهای طولانی','art exhibitions and long conversations')]
values = [('صداقت و گفتگوی روشن','honesty and clear communication'),('احترام به فضای شخصی و همراهی','personal space and companionship'),('اعتماد و وقت گذاشتن برای هم','trust and making time for each other'),('آرامش و رشد در کنار هم','calm and growing together'),('شوخ‌طبعی و مسئولیت‌پذیری','humour and being dependable')]
goals = ['long_term','intentional','exploring']
avatars = ROOT/'public/assets/people'
avatars.mkdir(parents=True,exist_ok=True)
profiles = []
for index in range(100):
    feminine = index % 2 == 0
    names = female if feminine else male
    name_fa,name = names[(index//2)%25]
    # The second set has a different display surname; every identity is fictional.
    suffix_fa,suffix = (' نوری',' Nouri') if index >= 50 else ('','')
    name_fa,name = name_fa+suffix_fa,name+suffix
    job_fa,job = jobs[(index//3)%len(jobs)]
    city_fa,city = cities[(index//8)%len(cities)]
    activity_fa,activity = activities[index%5]
    value_fa,value = values[(index//5)%5]
    age = 23 + (index*7)%17
    lifestyle = ['آرام','پرانرژی','ماجراجو','متعادل'][index%4]
    communication = ['گفتگو محور','صریح','شنونده','مستقل'][(index//4)%4]
    profile = {
        'id':f'demo-{index+1:03d}','name':name,'nameFa':name_fa,'age':age,'city':city,'cityFa':city_fa,
        'distance':2+(index*13)%75,'image':f'/assets/people/demo-{index+1:03d}.svg',
        'online':index%3==0,'verified':False,'likesYou':index%5==0,
        'bio':f'I’m a {job} who enjoys {activity}. I value {value} in a relationship, and prefer taking time to get to know each other.',
        'bioFa':f'{job_fa} هستم و {activity_fa} حالم را خوب می‌کند. در رابطه {value_fa} برایم مهم است؛ دوست دارم با حوصله همدیگر را بشناسیم.',
        'prompt':f'A relaxed first date with {activity}, with time to talk about what matters to us.',
        'promptFa':f'یک قرار بی‌عجله با {activity_fa}؛ با فرصت کافی برای حرف زدن دربارهٔ چیزهایی که برایمان مهم است.',
        'interests':rng.sample(interests,4),'relationshipGoal':goals[(index//6)%3],
        'attributes':[
            {'key':'شغل','value':job_fa},{'key':'سبک زندگی','value':lifestyle},
            {'key':'ارتباط','value':communication},{'key':'تحصیلات','value':['کارشناسی','کارشناسی ارشد','دکتری'][(index//7)%3]},
            {'key':'قد','value':f'{158+(index*3)%37} سانتی‌متر'},
            {'key':'وقت آزاد','value':['طبیعت','هنر','کتاب','ورزش','موسیقی'][index%5]},
            {'key':'ارزش رابطه','value':value_fa},{'key':'زبان‌ها','value':['فارسی، انگلیسی','فارسی، فرانسه','فارسی، آلمانی'][index%3]}
        ]
    }
    profiles.append(profile)
    skin = ['#d8a387','#bb7f61','#eac0a3','#936346','#cc9978'][index%5]
    hair = ['#201a20','#30211d','#4b3026','#211f25','#674936'][(index//5)%5]
    hue = (index*37)%360
    length = 400 if feminine else 265
    # Small, original code-native illustrations avoid external tracking/image requests.
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="940" viewBox="0 0 720 940"><defs><linearGradient id="b" x2="1" y2="1"><stop stop-color="hsl({hue} 18% 26%)"/><stop offset="1" stop-color="#121016"/></linearGradient><linearGradient id="c" x2="1" y2="1"><stop stop-color="hsl({hue} 28% 45%)"/><stop offset="1" stop-color="hsl({hue} 24% 20%)"/></linearGradient></defs><rect width="720" height="940" fill="url(#b)"/><circle cx="{150+index%5*90}" cy="260" r="235" fill="#ffffff05"/><path d="M0 740Q360 580 720 720V940H0" fill="#08080c" opacity=".2"/><rect x="196" y="190" width="328" height="{length}" rx="160" fill="{hair}"/><path d="M110 940V755Q120 600 300 587H420Q600 600 610 755V940" fill="url(#c)"/><path d="M295 530V625Q360 686 425 625V530" fill="{skin}"/><ellipse cx="360" cy="385" rx="132" ry="180" fill="{skin}"/><path d="M228 365V300Q230 185 360 190Q505 190 496 333Q405 325 320 259Q291 340 228 365" fill="{hair}"/><path d="M278 380q25 -15 50 -1M396 379q24 -14 49 1" fill="none" stroke="{hair}" stroke-width="10" stroke-linecap="round"/><ellipse cx="304" cy="401" rx="6" ry="9" fill="#292126"/><ellipse cx="420" cy="401" rx="6" ry="9" fill="#292126"/><path d="M360 412l-10 48h22" fill="none" stroke="#79523f" stroke-opacity=".4" stroke-width="5" stroke-linecap="round"/><path d="M322 494q38 25 76 -2" fill="none" stroke="#8c4c4f" stroke-width="7" stroke-linecap="round"/><path d="M298 603l62 73 65 -73" fill="none" stroke="#ffffff25" stroke-width="5"/><circle cx="580" cy="135" r="24" fill="#f3264925"/><text x="360" y="868" fill="#ffffff65" text-anchor="middle" font-family="sans-serif" font-size="13" letter-spacing="4">FICTIONAL PROFILE · {index+1:03d}</text></svg>'''
    (avatars/f'demo-{index+1:03d}.svg').write_text(svg,encoding='utf-8')

seed = json.loads((ROOT/'shared/demo-data.json').read_text(encoding='utf-8'))
base = seed['profiles']
(ROOT/'shared/demo-state.json').write_text(json.dumps(seed['state'],ensure_ascii=False,separators=(',',':')),encoding='utf-8')
target = ROOT/'public/data/profiles.json'
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(base+profiles,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'Generated {len(profiles)} new fictional adults; {len(base)+len(profiles)} total profiles.')
