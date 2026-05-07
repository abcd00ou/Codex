"""
Morning Agent - 아침 학습 이메일 빌더 + 발송
매일 오전: 오늘 주제 브리핑 + 최신 뉴스 3개 + 병목 현황
"""

import os
import sys
import smtplib
import ssl
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _ROOT)

import config
from agents.daily.progress_agent import (
    get_today_topic, get_next_topic, get_progress_summary,
    mark_morning_sent, LEVEL_META,
)
from agents.daily.news_agent    import fetch_news
from agents.daily.content_agent import generate_briefing

GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT      = os.environ.get("GMAIL_RECIPIENT", GMAIL_ADDRESS)


def _bottleneck_bar(utilization: float) -> str:
    """가동률 → HTML 바 차트"""
    pct   = int(utilization * 100)
    width = int(utilization * 180)
    color = "#e53e3e" if pct >= 85 else "#d69e2e" if pct >= 70 else "#38a169"
    return (
        f'<div style="display:inline-block; background:{color}; '
        f'width:{width}px; height:10px; border-radius:2px; vertical-align:middle;"></div>'
        f'<span style="margin-left:6px; font-weight:bold; color:{color};">{pct}%</span>'
    )


def _build_bottleneck_html() -> str:
    rows = []
    key_layers = [
        ("HBM",        "HBM"),
        ("CoWoS",      "CoWoS 패키징"),
        ("Power_DC",   "Power / DC"),
        ("Networking", "Networking"),
        ("GPU",        "GPU"),
    ]
    for key, label in key_layers:
        util = config.CURRENT_CAPACITY_UTILIZATION.get(key, 0)
        bar  = _bottleneck_bar(util)
        rows.append(
            f'<tr><td style="padding:4px 12px 4px 0; color:#555; font-size:13px; width:130px;">{label}</td>'
            f'<td style="padding:4px 0;">{bar}</td></tr>'
        )
    return f'<table style="border-collapse:collapse;">\n' + "\n".join(rows) + "\n</table>"


def _build_news_html(news: list[dict]) -> str:
    items = []
    for n in news[:3]:
        cat_color = {
            "HBM/Memory": "#3182ce", "Packaging": "#d69e2e", "GPU": "#e53e3e",
            "Power": "#718096", "Networking": "#dd6b20", "Hyperscaler": "#38a169",
        }.get(n.get("category", ""), "#805ad5")

        items.append(
            f'<li style="margin-bottom:10px;">'
            f'<span style="background:{cat_color}; color:white; font-size:11px; '
            f'padding:1px 6px; border-radius:3px; margin-right:6px;">{n.get("category", "")}</span>'
            f'<a href="{n.get("url","#")}" style="color:#2d3748; text-decoration:none; font-size:14px;">'
            f'{n["title"]}</a>'
            f'<span style="color:#a0aec0; font-size:12px; margin-left:6px;">{n.get("source","")} | {n.get("date","")}</span>'
            + (f'<br><span style="color:#718096; font-size:12px; margin-left:14px;">→ {n["impact"]}</span>' if n.get("impact") else "")
            + '</li>'
        )
    return '<ul style="padding-left:0; list-style:none; margin:0;">\n' + "\n".join(items) + "\n</ul>"


def build_email_html(
    topic: dict,
    news: list[dict],
    briefing_html: str,
    progress: dict,
) -> str:
    lm           = topic.get("level_meta", LEVEL_META[1])
    level_color  = lm.get("color", "#1a73e8")
    level_label  = lm.get("label", "Lv.1 기초")
    level_label_en = lm.get("label_en", "Fundamentals")
    day          = progress.get("day", 1)
    total        = progress.get("total_days", 24)
    pct          = progress.get("pct", 0)
    done         = progress.get("done", 0)
    next_topic   = get_next_topic()
    today_str    = datetime.date.today().strftime("%Y년 %m월 %d일")
    as_of        = config.AS_OF_DATE

    progress_bar_width = int(pct * 2.4)  # max 240px

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background:#f7f8fa; font-family:'Apple SD Gothic Neo',Arial,sans-serif;">
<div style="max-width:620px; margin:0 auto; background:white; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08);">

  <!-- Header -->
  <div style="background:{level_color}; padding:24px 32px 20px;">
    <div style="color:rgba(255,255,255,.8); font-size:12px; margin-bottom:6px;">
      {today_str} &nbsp;·&nbsp; Day {day}/{total} &nbsp;·&nbsp; {level_label} ({level_label_en})
    </div>
    <div style="color:white; font-size:22px; font-weight:700; line-height:1.3;">
      {lm.get('emoji','📗')} {topic['title']}
    </div>
    <div style="color:rgba(255,255,255,.85); font-size:14px; margin-top:4px;">
      {topic['title_en']}
    </div>
  </div>

  <!-- Progress bar -->
  <div style="background:#e2e8f0; height:4px;">
    <div style="background:{level_color}; height:4px; width:{progress_bar_width}px; max-width:100%;"></div>
  </div>

  <div style="padding:28px 32px;">

    <!-- 오늘의 SCM 뉴스 -->
    <div style="margin-bottom:28px;">
      <div style="font-size:13px; font-weight:700; color:#4a5568; text-transform:uppercase; letter-spacing:.5px; margin-bottom:12px;">
        📰 Today's SCM News
      </div>
      {_build_news_html(news)}
    </div>

    <hr style="border:none; border-top:1px solid #edf2f7; margin:0 0 28px;">

    <!-- 오늘의 학습 브리핑 -->
    <div style="margin-bottom:28px;">
      <div style="font-size:13px; font-weight:700; color:#4a5568; text-transform:uppercase; letter-spacing:.5px; margin-bottom:12px;">
        📖 Today's Briefing — {level_label}
      </div>
      <div style="font-size:14px; line-height:1.75; color:#2d3748;">
        {briefing_html}
      </div>
    </div>

    <hr style="border:none; border-top:1px solid #edf2f7; margin:0 0 28px;">

    <!-- 현재 병목 현황 -->
    <div style="margin-bottom:28px;">
      <div style="font-size:13px; font-weight:700; color:#4a5568; text-transform:uppercase; letter-spacing:.5px; margin-bottom:12px;">
        📊 Bottleneck Status <span style="font-weight:400; color:#a0aec0; font-size:11px;">기준: {as_of}</span>
      </div>
      {_build_bottleneck_html()}
    </div>

    <hr style="border:none; border-top:1px solid #edf2f7; margin:0 0 24px;">

    <!-- 진도 + 내일 예고 -->
    <div style="display:flex; justify-content:space-between; font-size:13px; color:#718096;">
      <div>
        완료: {done}/{total}일 ({pct}%)&nbsp;
        {'·&nbsp; 평균 퀴즈 ' + str(progress.get("avg_quiz_pct","–")) + '%' if progress.get("avg_quiz_pct") else ""}
      </div>
      <div>내일: {next_topic['title']} →</div>
    </div>

  </div>

  <!-- Footer -->
  <div style="background:#f7f8fa; padding:16px 32px; font-size:11px; color:#a0aec0; text-align:center;">
    AI SCM Daily Learning System &nbsp;·&nbsp; 저녁 이메일에서 오늘 주제 퀴즈를 확인하세요
  </div>

</div>
</body>
</html>"""


def send_morning_email(dry_run: bool = False) -> bool:
    """아침 이메일 생성 + 발송"""
    topic    = get_today_topic()
    progress = get_progress_summary()

    print(f"\n[Morning] 오늘 주제: {topic['title']} [{topic['level_meta']['label']}]")

    # 뉴스 수집 (주제 관련 키워드 추가)
    topic_kw = topic["title_en"].lower().split()[:3]
    news     = fetch_news(max_items=5, topic_keywords=topic_kw)

    # Claude API로 학습 콘텐츠 생성
    briefing = generate_briefing(topic, news)

    # HTML 이메일 빌드
    html = build_email_html(topic, news, briefing, progress)

    subject = (
        f"[AI SCM] Day {progress['day']} — "
        f"{topic['level_meta']['emoji']} {topic['title']} "
        f"({topic['level_meta']['label_en']})"
    )

    if dry_run:
        # 파일로 저장
        import config as cfg
        os.makedirs(cfg.REPORTS_DIR, exist_ok=True)
        out = os.path.join(cfg.REPORTS_DIR, f"morning_email_{datetime.date.today()}.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [Morning] dry-run → 파일 저장: {out}")
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

        print(f"  [Morning] ✅ 발송 완료: {subject}")
        mark_morning_sent(topic["id"], topic["level"])
        return True

    except Exception as e:
        print(f"  [Morning] ❌ 발송 실패: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="이메일 발송 대신 파일로 저장")
    args = parser.parse_args()
    send_morning_email(dry_run=args.dry_run)
