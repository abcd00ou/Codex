"""
Evening Agent - 저녁 퀴즈 + 뉴스 요약 이메일 빌더 + 발송
매일 저녁: 오늘 주제 퀴즈 3개 + 오늘 뉴스 요약 + 내일 예고
"""

import os
import sys
import smtplib
import ssl
import datetime
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _ROOT)

import config
from agents.daily.progress_agent import (
    get_today_topic, get_next_topic, get_progress_summary,
    mark_evening_sent, LEVEL_META,
)
from agents.daily.news_agent    import fetch_news
from agents.daily.content_agent import generate_quiz

GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT      = os.environ.get("GMAIL_RECIPIENT", GMAIL_ADDRESS)

OPTION_LABELS = ["A", "B", "C", "D"]


def _build_quiz_html(quiz_items: list[dict]) -> str:
    blocks = []
    for i, q in enumerate(quiz_items, 1):
        options_html = "".join(
            f'<div style="padding:6px 12px; margin:4px 0; background:#f7f8fa; border-radius:4px; font-size:13px;">'
            f'<strong style="color:#4a5568;">{lbl}.</strong> {text}</div>'
            for lbl, text in q.get("options", {}).items()
        )
        blocks.append(
            f'<div style="margin-bottom:24px; padding:16px; border:1px solid #e2e8f0; border-radius:6px;">'
            f'<div style="font-size:14px; font-weight:600; color:#2d3748; margin-bottom:10px;">'
            f'Q{i}. {q["question"]}</div>'
            f'{options_html}'
            # 정답은 접힌 상태로 (이메일이라 JS 없음 → 텍스트로 숨겨서 표시)
            f'<details style="margin-top:10px;">'
            f'<summary style="cursor:pointer; color:#718096; font-size:12px; user-select:none;">정답 보기 ▾</summary>'
            f'<div style="margin-top:8px; padding:10px; background:#ebf8ff; border-radius:4px; font-size:13px;">'
            f'<strong style="color:#2b6cb0;">정답: {q.get("answer","")}</strong><br>'
            f'<span style="color:#4a5568;">{q.get("explanation","")}</span>'
            f'</div></details>'
            f'</div>'
        )
    return "\n".join(blocks)


def _build_news_summary_html(news: list[dict]) -> str:
    items = []
    for n in news[:4]:
        items.append(
            f'<li style="margin-bottom:8px; font-size:13px; color:#2d3748;">'
            f'{n["title"]}'
            f'<span style="color:#a0aec0; margin-left:6px; font-size:11px;">'
            f'{n.get("source","")} | {n.get("date","")}</span>'
            f'</li>'
        )
    return '<ul style="padding-left:16px; margin:0;">\n' + "\n".join(items) + "\n</ul>"


def build_email_html(
    topic: dict,
    quiz_items: list[dict],
    news: list[dict],
    progress: dict,
) -> str:
    lm          = topic.get("level_meta", LEVEL_META[1])
    level_color = lm.get("color", "#1a73e8")
    day         = progress.get("day", 1)
    total       = progress.get("total_days", 24)
    pct         = progress.get("pct", 0)
    next_topic  = get_next_topic()
    today_str   = datetime.date.today().strftime("%Y년 %m월 %d일")
    pbar_width  = int(pct * 2.4)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background:#f7f8fa; font-family:'Apple SD Gothic Neo',Arial,sans-serif;">
<div style="max-width:620px; margin:0 auto; background:white; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08);">

  <!-- Header -->
  <div style="background:#2d3748; padding:24px 32px 20px;">
    <div style="color:rgba(255,255,255,.7); font-size:12px; margin-bottom:6px;">
      {today_str} &nbsp;·&nbsp; Day {day}/{total} — 저녁 복습
    </div>
    <div style="color:white; font-size:20px; font-weight:700; line-height:1.3;">
      🧠 오늘의 퀴즈: {topic['title']}
    </div>
    <div style="color:rgba(255,255,255,.75); font-size:13px; margin-top:4px;">
      {lm.get('emoji','')} {lm.get('label','')} Quiz
    </div>
  </div>

  <!-- Progress bar -->
  <div style="background:#e2e8f0; height:4px;">
    <div style="background:{level_color}; height:4px; width:{pbar_width}px; max-width:100%;"></div>
  </div>

  <div style="padding:28px 32px;">

    <!-- 퀴즈 -->
    <div style="margin-bottom:28px;">
      <div style="font-size:13px; font-weight:700; color:#4a5568; text-transform:uppercase; letter-spacing:.5px; margin-bottom:16px;">
        📝 Quiz — {topic['title_en']}
      </div>
      {_build_quiz_html(quiz_items)}
    </div>

    <hr style="border:none; border-top:1px solid #edf2f7; margin:0 0 28px;">

    <!-- 오늘 뉴스 요약 -->
    <div style="margin-bottom:28px;">
      <div style="font-size:13px; font-weight:700; color:#4a5568; text-transform:uppercase; letter-spacing:.5px; margin-bottom:12px;">
        📰 오늘의 AI SCM 뉴스
      </div>
      {_build_news_summary_html(news)}
    </div>

    <hr style="border:none; border-top:1px solid #edf2f7; margin:0 0 24px;">

    <!-- 내일 예고 -->
    <div style="background:#ebf8ff; border-radius:6px; padding:14px 16px; margin-bottom:20px;">
      <div style="font-size:12px; color:#2b6cb0; font-weight:700; margin-bottom:4px;">내일 학습 예고</div>
      <div style="font-size:14px; color:#2d3748;">
        {next_topic['level_meta'].get('emoji','')} {next_topic['title']}
        <span style="color:#718096; font-size:12px;"> ({next_topic['title_en']})</span>
      </div>
    </div>

    <!-- 진도 -->
    <div style="font-size:12px; color:#a0aec0; text-align:right;">
      전체 진도 {pct}% ({progress.get('done',0)}/{total}일 완료)
    </div>

  </div>

  <!-- Footer -->
  <div style="background:#f7f8fa; padding:16px 32px; font-size:11px; color:#a0aec0; text-align:center;">
    AI SCM Daily Learning System &nbsp;·&nbsp; 내일 아침 이메일을 확인하세요
  </div>

</div>
</body>
</html>"""


def send_evening_email(dry_run: bool = False) -> bool:
    """저녁 이메일 생성 + 발송"""
    topic    = get_today_topic()
    progress = get_progress_summary()

    print(f"\n[Evening] 퀴즈 주제: {topic['title']} [{topic['level_meta']['label']}]")

    # 퀴즈 생성
    quiz_items = generate_quiz(topic)

    # 뉴스 (아침과 같은 날 뉴스 재활용 또는 재수집)
    news = fetch_news(max_items=5)

    # HTML 이메일 빌드
    html = build_email_html(topic, quiz_items, news, progress)

    subject = (
        f"[AI SCM Quiz] Day {progress['day']} — "
        f"🧠 {topic['title']} 복습 퀴즈"
    )

    if dry_run:
        os.makedirs(config.REPORTS_DIR, exist_ok=True)
        out = os.path.join(config.REPORTS_DIR, f"evening_email_{datetime.date.today()}.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [Evening] dry-run → 파일 저장: {out}")
        return True

    # Gmail 발송
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = RECIPIENT
        msg.attach(MIMEText(html, "html", "utf-8"))

        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, RECIPIENT, msg.as_bytes())

        print(f"  [Evening] ✅ 발송 완료: {subject}")
        mark_evening_sent()
        return True

    except Exception as e:
        print(f"  [Evening] ❌ 발송 실패: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="이메일 발송 대신 파일로 저장")
    args = parser.parse_args()
    send_evening_email(dry_run=args.dry_run)
