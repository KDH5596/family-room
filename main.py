from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import os

app = FastAPI()

# 렌더(프록시) 환경에서 https 주소를 정확히 인식하도록 설정
@app.middleware("http")
async def proxy_fix_middleware(request: Request, call_next):
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto
    response = await call_next(request)
    return response

# 세션 미들웨어 설정
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
    "jja8718@gmail.com",  # 엄마 이메일
    "raykim00@gmail.com",  # 아빠 이메일
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
    # 렌더 환경에 맞는 실제 HTTPS 콜백 주소 고정
    redirect_uri = "https://family-room.onrender.com/auth"
    return await oauth.google.authorize_redirect(request, redirect_uri)

# 3. 구글 로그인 인증 완료
@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")
        
        if userinfo:
            email = userinfo.get("email")
            
            # 허용된 가족 이메일인지 체크
            if email not in ALLOWED_EMAILS:
                return HTMLResponse("<h3>접근 거부: 허용된 가족 이메일이 아닙니다.</h3><a href='/'>돌아가기</a>", status_code=403)
                
            request.session["user"] = {
                "name": userinfo.get("name"),
                "email": email,
                "picture": userinfo.get("picture")
            }
            
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return HTMLResponse(f"<h3>로그인 중 오류가 발생했습니다: {str.escape(str(e)) if 'str.escape' in globals() else str(e)}</h3><a href='/'>돌아가기</a>", status_code=400)

# 4. 로그아웃
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# 5. 게시글 작성
@app.post("/posts")
async def create_post(
    request: Request,
    content: str = Form(...),
    room: str = Form("우리 가족")
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
        
    new_post = {
        "author": user["name"],
        "email": user["email"],
        "picture": user["picture"],
        "content": content,
        "room": room
    }
    posts_db.append(new_post)
    return RedirectResponse(url=f"/?room={room}", status_code=303)