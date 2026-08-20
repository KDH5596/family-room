from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import os

# HTTP 환경 테스트 설정
os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="your-super-secret-key-dongdong")

templates = Jinja2Templates(directory="templates")
templates.env.cache = None

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# 허용할 가족 이메일 목록
ALLOWED_EMAILS = [
    "legendkai987654321@gmail.com",  # 동동이 이메일
    "jja8718@gmail.com", #엄마 이메일
    "raykim00@gmail.com", #아빠 이메일
]

# 메모리에 게시글을 저장할 리스트
posts_db = []


# 1. 메인 페이지 (로그인 안 되어 있으면 login.html 보여주기)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, room: str = "우리 가족"):
    user = request.session.get("user")
    
    # 로그인을 안 했다면 예쁜 로그인 페이지로 이동!
    if not user:
        return templates.TemplateResponse(request, "login.html", {})
    
    # 선택한 방(room)에 해당하는 글만 필터링
    room_posts = [p for p in posts_db if p.get("room", "우리 가족") == room]

    return templates.TemplateResponse(
        request, 
        "index.html", 
        {"user": user, "posts": room_posts, "current_room": room}
    )


# 2. 구글 로그인 요청
@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)


# 3. 구글 로그인 인증 완료
@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")

        if userinfo:
            user_email = userinfo.get("email")

            if user_email not in ALLOWED_EMAILS:
                return HTMLResponse(
                    f"""
                    <div style="text-align:center; margin-top:50px; font-family:sans-serif;">
                        <h2 style="color: #ff6b6b;">❌ 접근 거부</h2>
                        <p>허용되지 않은 가족 이메일 계정입니다: <b>{user_email}</b></p>
                        <a href="/" style="text-decoration:none; color:#007bff;">돌아가기</a>
                    </div>
                """
                )

            request.session["user"] = {
                "name": userinfo.get("name"),
                "email": user_email,
                "picture": userinfo.get("picture"),
            }

    except Exception as e:
        print(f"로그인 에러 발생: {e}")

    return RedirectResponse(url="/", status_code=303)


# 4. 로그아웃 (세션 지우고 메인으로 가면 알아서 login.html이 뜸)
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# 5. 게시글 등록
@app.post("/add_post")
async def add_post(
    request: Request,
    room: str = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    new_post = {
        "name": user.get("name"),
        "picture": user.get("picture"),
        "room": room,
        "category": category,
        "title": title,
        "content": content,
    }

    posts_db.insert(0, new_post)
    return RedirectResponse(url=f"/?room={room}", status_code=303)