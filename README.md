# mcp_gemini_image

Google Gemini 이미지 모델(Nano Banana 등)로 이미지를 생성하는 **MCP (Model Context Protocol) 서버**.
프롬프트를 받아 PNG로 저장하고 절대 경로를 반환합니다.

---

## 기능
- Gemini 2.5 / 3.1 Flash Image, Gemini 3 Pro Image 등 다양한 모델 선택
- 임의 해상도 지정 (기본 1920×1080 FHD) — 가장 가까운 지원 비율로 생성 후 Pillow로 정확한 픽셀 리사이즈
- 파일명: `{타임스탬프}_{영문제목}.png`
- 저장 경로: 호출 시점의 작업 디렉토리 기준 `./png/` (없으면 자동 생성)

---

## 요구사항
- Python 3.10+
- Google AI Studio Gemini API Key — https://aistudio.google.com/apikey

---

## 설치

```powershell
cd c:\onethelab\project\mcp_gemini_image
pip install -r requirements.txt
```

---

## API 키 설정

`GEMINI_API_KEY` 환경변수를 등록합니다.

**Windows PowerShell (영구):**
```powershell
setx GEMINI_API_KEY "your-api-key-here"
```
등록 후 **새 터미널을 열어야** 적용됩니다.

**현재 세션에만:**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

> MCP 등록 시 `env` 블록으로 직접 넣을 수도 있습니다 (아래 참조).

---

## MCP 등록

### 방법 1. Claude Code CLI (`claude mcp add`)

가장 간단한 등록:
```powershell
claude mcp add gemini-image -- python "c:\onethelab\project\mcp_gemini_image\server.py"
```

API 키를 함께 주입:
```powershell
claude mcp add gemini-image -e GEMINI_API_KEY=your-api-key-here -- python "c:\onethelab\project\mcp_gemini_image\server.py"
```

스코프 옵션:
- `-s local` (기본): 현재 프로젝트에만, 본인만 사용
- `-s project`: 프로젝트의 `.mcp.json`에 저장 (팀 공유)
- `-s user`: 모든 프로젝트에서 사용

확인 / 삭제:
```powershell
claude mcp list
claude mcp remove gemini-image
```

### 방법 2. 프로젝트 `.mcp.json` (수동 작성, 팀 공유 권장)

프로젝트 루트(`c:\onethelab\project\.mcp.json`)에:
```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "python",
      "args": ["c:\\onethelab\\project\\mcp_gemini_image\\server.py"]
    }
  }
}
```

API 키를 시스템 환경변수 대신 여기서 주입하려면:
```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "python",
      "args": ["c:\\onethelab\\project\\mcp_gemini_image\\server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 방법 3. Claude Desktop

설정 파일 위치:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "python",
      "args": ["c:\\onethelab\\project\\mcp_gemini_image\\server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```
저장 후 Claude Desktop 재시작.

---

## Tool 사용법

### `generate_image`

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `prompt` | str | — | 이미지 생성 프롬프트 |
| `title` | str | — | 파일명에 들어갈 영문 제목 (자동 sanitize) |
| `width` | int | `1920` | 출력 너비 (px) |
| `height` | int | `1080` | 출력 높이 (px) |
| `model` | str | `gemini-2.5-flash-image` | Gemini 이미지 모델 ID |

**반환값**: 저장된 PNG의 절대 경로 (문자열)

**호출 예시 (Claude에서 자연어로):**
> "고양이가 책 읽는 모습을 그려서 cat_reading 이름으로 저장해줘"
>
> "사이버펑크 도쿄 골목, 4K (3840×2160)로 생성해줘. 모델은 3.1 flash."

---

## 출력 경로 규칙

- 저장 위치: **MCP 서버가 실행되는 작업 디렉토리** 기준 `./png/`
  - Claude Code에서 호출하면 일반적으로 **프로젝트 루트** 기준
  - 폴더가 없으면 자동 생성
- 파일명: `YYYYMMDD_HHMMSS_{Sanitized_Title}.png`
  - `title`에서 영숫자/`_`/`-`이 아닌 문자는 `_`로 치환

---

## 지원 모델 (2026-05 기준)

| 모델 ID | 비고 |
|---|---|
| `gemini-2.5-flash-image` | **기본값**, Nano Banana 정식판 |
| `gemini-3.1-flash-image-preview` | Nano Banana 후속, 더 정교한 디테일 |
| `gemini-3-pro-image-preview` | Pro 급 |

현재 사용 가능한 모델 전체 조회:
```powershell
python -c "from google import genai; c = genai.Client(api_key=__import__('os').environ['GEMINI_API_KEY']); [print(m.name) for m in c.models.list() if 'image' in m.name.lower()]"
```

> Imagen 4 계열(`imagen-4.0-*`)은 호출 방식(`predict`)이 달라 현재 서버에서는 지원하지 않습니다.

---

## 트러블슈팅

**`GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다`**
- `setx`로 등록 후 **새 터미널/Claude Code 재시작** 필요
- MCP `env` 블록으로 직접 주입하는 방법도 가능

**`404 NOT_FOUND ... is not found for API version v1beta`**
- 모델 ID가 변경/만료된 경우. 위의 "현재 사용 가능한 모델 전체 조회" 명령으로 최신 ID 확인 후 `model` 파라미터로 지정

**MCP 서버가 Claude에 표시되지 않음**
- `claude mcp list`로 등록 확인
- Claude Code/Desktop 재시작
- `python "<server.py 경로>"`를 터미널에서 직접 실행해 임포트 오류가 없는지 확인

**이미지 비율이 미묘하게 다름**
- Gemini는 고정된 비율(`1:1`, `16:9` 등)로만 생성 → 가장 가까운 비율 선택 후 정확한 픽셀로 리사이즈
- 매우 비표준 비율(예: 2000×500)은 결과물이 부자연스러울 수 있음

---

## 파일 구성
```
mcp_gemini_image/
├── server.py          # MCP 서버 본체
├── requirements.txt   # 의존성
├── README.md          # 본 문서
├── goal.md            # 초기 요구사항
└── png/               # 생성된 이미지 출력 (자동 생성)
```
