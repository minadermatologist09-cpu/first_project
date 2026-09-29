# Skinology Clinic — вэб сайт (Flask)

Премиум арьс судлал / гоо сайхны клиникийн вэб сайт. Цаг захиалгын бүртгэл нь
**"Register" SQLite датабаазад** (`register.db`) хадгалагдаж, admin хуудсаар
харагдаж, Excel-ээр татагдана.

## Клиникийн мэдээлэл

- **SKINOLOGY CLINIC** — DERMATOLOGY • AESTHETICS
- Хаяг: Бөхийн өргөөний уулзвар, Милленниум Плаза, 409
- Утас: 7777-5888
- Ажлын цаг: Өдөр бүр 10:00–19:00
- Instagram: @SKINOLOGY.CLINIC
- Төлбөр: Pocket, Storepay болон лизинг / зээлийн апп-ууд
- Онлайн цаг захиалга: https://www.meditech.mn/book/skinology

Загварын өнгө: warm white / ivory `#F8F6F1`, light beige `#EEEAE2`, light gray
`#E7E5E1`, charcoal `#292929`, champagne-gold `#B5A078` (ягаан / нил ягаан өнгө
байхгүй). "Цаг захиалах" товч — champagne-gold.

## Хуудсууд

| Хаяг | Тайлбар |
|------|---------|
| `/` | Нүүр хуудас — hero, үйлчилгээ, **манай баг**, бидний тухай, **манай эмнэлэг**, видео, цомог, үнэ, холбоо барих |
| `/register` | Онлайн урьдчилсан бүртгэлийн форм (SQLite-д хадгална) |
| `/admin` | Бүртгэлүүдийг харах (нууц үгтэй, анхдагч `admin123`) |
| `/admin/export` | Бүртгэлийг `Register_YYYYMMDD_HHMMSS.xlsx` файлаар татах |

Нүүр хуудасны дээд цэс: **Нүүр, Үйлчилгээ, Манай баг, Бидний тухай, Холбоо барих**
+ **"Цаг захиалах"** алтан товч. Бүх "Цаг захиалах" товч Meditech цаг захиалгын
хуудас (`https://www.meditech.mn/book/skinology`) руу очно. `/register` форм
хэвээр ажиллаж, footer болон "Холбоо барих" хэсгээс нэвтэрнэ.

### Манай баг (`#team`)

7 хүний карт — Б. Мина, Д. Алтантуул (энэ хоёр founder/chief тул алтан хүрээтэй,
бага зэрэг онцолсон), Бат-Өлзий, О. Баатарсүх, М. Очирдарь, Б. Цэмаа, Б. Хулан.
Гэрэл зургийг `static/img/team/<нэр>.jpg` байршуулна (`static/img/team/README.txt`).
Зураг байхгүй бол нэрний товчлол монограмаар гоёмсог харагдана. Desktop 4 / таблет
2–3 / мобайл 1–2 багана.

### Манай эмнэлэг (`#interior`)

Editorial зургийн галерей: нэг том зураг (`reception.jpg` — хүлээн авах танхим) +
4 жижиг дэмжих зураг (`lounge`, `treatment-room`, `corridor`, `equipment`).
Зургийг `static/img/interior/` хавтаст байршуулна (`static/img/interior/README.txt`).
Desktop дээр том зураг зүүн талд, жижгүүд 2×2; таблет дээр том нь дээр бүтэн өргөн,
жижгүүд 2 багана; мобайл дээр цэвэр босоо стек. "Дэлгэрэнгүй үзэх" товч `#gallery`
руу очно. Бодит эмнэлгийн зургийг AI/стокоос тэргүүлэн ашиглана.

## Файлын бүтэц

```
skinology website/
├── app.py                     # Flask сервер: route, валидац, SQLite, Excel export
├── templates/
│   ├── home.html              # Нүүр хуудас (бүх хэсэг)
│   ├── register.html          # Цаг захиалах форм
│   ├── login.html             # Admin нэвтрэх
│   └── admin.html             # Бүртгэлийн жагсаалт + Excel татах
├── static/
│   ├── css/style.css          # Premium warm white / ivory / charcoal / champagne-gold загвар
│   ├── js/main.js             # Мобайл цэс, видео ачаалалт, scroll reveal
│   ├── img/  (README.txt)         # Ерөнхий зургууд
│   ├── img/team/ (README.txt)     # Багийн гэрэл зураг (mina.jpg, altantuul.jpg …)
│   ├── img/interior/ (README.txt) # Эмнэлгийн дотоод орчин (reception.jpg = том)
│   └── video/                     # MP4 видеогаа энд байршуулна
├── register.db                # SQLite датабаз (устгахгүй!)
├── requirements.txt
└── README.md
```

## Ажиллуулах

```powershell
cd "c:\Users\User\skinology website"

# (заавал биш) виртал орчин
python -m venv venv
.\venv\Scripts\Activate.ps1     # алдаа гарвал: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

pip install -r requirements.txt
python app.py
```

Хөтчөөр нээх: <http://127.0.0.1:5000>

Зогсоох: терминал дээр `Ctrl + C`.

### Admin нууц үг солих (заавал биш)

```powershell
$env:ADMIN_PASSWORD = "таны_нууц_үг"
$env:SECRET_KEY = "санамсаргүй_урт_тэмдэгт"
python app.py
```

## Зураг нэмэх

`static/img/` дотор зөв нэрээр зургаа хийхэд шууд харагдана (жагсаалтыг
`static/img/README.txt`-ээс үзнэ үү). Файл байхгүй үед блок нь беж-саарал градиентээр
харагдаж, зохион байгуулалт эвдрэхгүй.

## Видео нэмэх (нүүр хуудасны "Видео" хэсэг)

`templates/home.html` доторх `<!-- ВИДЕО ОРУУЛАХ ЗААВАР -->` коммэнтыг үзнэ үү.

- **MP4:** `static/video/clinic.mp4` хийгээд `<video>` тагаар солино.
- **YouTube:** `.video-frame` дээрх `data-embed` атрибутын `VIDEO_ID`-г солино —
  дарахад видео ачаална. Эсвэл шууд `<iframe>` тавьж болно.

## Зураг, видеог S3 дээр байршуулах

`static/img/`, `static/video/` доторх файлууд AWS S3 руу хуулагдаж, зам нь
`media` таблицад хадгалагдана. Template-үүд `media_url('img/laser.jpg')`-ээр
файлын URL авна: `media` таблицад байвал S3 URL, байхгүй бол локал `/static` URL.

1. AWS дээр S3 bucket үүсгээд, `static/` доторх файлуудыг нийтэд уншигдахаар
   нээнэ (Block Public Access-ийн bucket policy-г зөвшөөрөөд):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": "*",
       "Action": "s3:GetObject",
       "Resource": "arn:aws:s3:::BUCKET_НЭР/static/*"
     }]
   }
   ```
2. Хуулах (`s3:PutObject` эрхтэй IAM хэрэглэгчийн түлхүүрээр):
   ```powershell
   $env:S3_BUCKET = "BUCKET_НЭР"
   $env:AWS_REGION = "ap-northeast-2"      # bucket-ийн region
   $env:AWS_ACCESS_KEY_ID = "..."
   $env:AWS_SECRET_ACCESS_KEY = "..."
   python upload_to_s3.py --dry-run         # юу хуулагдахыг шалгах
   python upload_to_s3.py
   ```
3. Сайтыг ажиллуулахдаа `S3_BUCKET`, `AWS_REGION`-оо тохируулна. CloudFront
   ашиглавал `MEDIA_BASE_URL = "https://xxxx.cloudfront.net"` гэж өгнө.

Шинэ зураг нэмсэн эсвэл сольсон бол `python upload_to_s3.py`-г дахин ажиллуулна
(өөрчлөгдөөгүй файлыг алгасна). `S3_BUCKET` тохируулаагүй үед сайт бүх файлыг
локалаас үзүүлнэ.

## Датабаз (`register` таблиц)

| Багана | Төрөл | Тайлбар |
|--------|-------|---------|
| id | INTEGER PK | Дугаар |
| last_name | TEXT | Овог |
| first_name | TEXT | Нэр |
| phone | TEXT | Утасны дугаар (8 орон) |
| email | TEXT UNIQUE | Имэйл (форматаар шалгана) |
| created_at | TEXT | Бүртгэсэн огноо, цаг |

`register.db` дэх өгөгдлийг устгахгүй. Цэвэрлэх шаардлагатай бол эхлээд асууна уу.
