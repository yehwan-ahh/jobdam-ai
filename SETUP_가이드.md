# GitHub + Streamlit 배포 순서

1. github.com 로그인 → New repository → 이름 `jobdam-ai`, **Public**, README 추가 안 함 → Create
2. 이 폴더(jobdam)에서 터미널 열고:
   git init
   git add .
   git commit -m "시작용 페이지"
   git branch -M main
   git remote add origin https://github.com/<내아이디>/jobdam-ai.git
   git push -u origin main
   (GitHub Desktop을 쓰면: File > Add local repository > 이 폴더 > Publish repository)
3. share.streamlit.io 접속 → GitHub 계정으로 로그인 → Create app
   - Repository: jobdam-ai / Branch: main / Main file: app.py
   - App URL: `jobdam` 입력 (이미 쓰이면 `jobdam-ai` 등)
   - Deploy
4. 나온 주소(https://jobdam.streamlit.app)를 커리어넷·KOSIS 신청서 홈페이지 칸에 입력
5. 키를 받으면 앱 Settings > Secrets에 secrets.toml.example 형식으로 붙여 넣기 (GitHub에는 절대 올리지 않기)
