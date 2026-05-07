#!/usr/bin/env python3
"""
AI SCM 뉴스레터 — 매일 오전 9시 발송

사용법:
  python3 run_newsletter.py                         # 발송
  python3 run_newsletter.py --comment "이번주 HBM 가이던스 상향이 핵심"
  python3 run_newsletter.py --dry-run               # HTML 파일로 저장
  python3 run_newsletter.py --preview               # 브라우저로 미리보기
  python3 run_newsletter.py --collect               # 데이터 수집만
  python3 run_newsletter.py --force                 # 캐시 무시하고 재수집

Crontab:
  0 9 * * * GMAIL_APP_PASSWORD="..." bash -c 'cd /path && python3 run_newsletter.py'
"""

import os, sys, argparse, smtplib, ssl, datetime, json, subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT      = os.environ.get("GMAIL_RECIPIENT", GMAIL_ADDRESS)

COMMENT_FILE = os.path.join(config.DATA_DIR, "editor_comment.txt")


def load_comment() -> str:
    """오늘 날짜의 편집자 코멘트 로드"""
    if not os.path.exists(COMMENT_FILE):
        return ""
    try:
        with open(COMMENT_FILE) as f:
            data = json.load(f)
        # 오늘 것만 사용
        if data.get("date") == str(datetime.date.today()):
            return data.get("comment", "")
    except Exception:
        pass
    return ""


def save_comment(comment: str):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(COMMENT_FILE, "w") as f:
        json.dump({"date": str(datetime.date.today()), "comment": comment}, f)
    print(f"  [Newsletter] 코멘트 저장 완료")


def main():
    parser = argparse.ArgumentParser(description="AI SCM 뉴스레터 발송")
    parser.add_argument("--comment", type=str, default=None,
                        help="오늘의 편집자 코멘트 (한국어)")
    parser.add_argument("--dry-run",  action="store_true", help="HTML 파일로만 저장")
    parser.add_argument("--preview",  action="store_true", help="dry-run + 브라우저 열기")
    parser.add_argument("--collect",  action="store_true", help="데이터 수집만 (발송 안 함)")
    parser.add_argument("--force",    action="store_true", help="캐시 무시하고 재수집")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"AI SCM Newsletter  |  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    # 편집자 코멘트 저장
    if args.comment:
        save_comment(args.comment)

    # 데이터 수집
    from agents.newsletter.data_agent        import collect_all
    from agents.newsletter.newsletter_builder import build

    state = collect_all(force=args.force)

    if args.collect:
        print("\n데이터 수집 완료. 발송 생략.")
        return

    # 코멘트 로드
    comment = load_comment()
    if comment:
        print(f"  [Newsletter] 편집자 코멘트: {comment[:50]}...")

    # HTML 빌드
    html    = build(state, editor_comment=comment)
    subject = (
        f"[AI SCM] {datetime.date.today().strftime('%m/%d')} "
        f"Daily Briefing — {len(state.get('signals',[]))}개 시그널"
    )

    dry = args.dry_run or args.preview
    if dry:
        os.makedirs(config.REPORTS_DIR, exist_ok=True)
        out = os.path.join(config.REPORTS_DIR, f"newsletter_{datetime.date.today()}.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [Newsletter] 저장: {out}")
        if args.preview:
            subprocess.run(["open", out])
        return

    # Gmail 발송
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = RECIPIENT
        msg.attach(MIMEText(html, "html", "utf-8"))

        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, RECIPIENT, msg.as_bytes())

        print(f"  [Newsletter] ✅ 발송 완료: {subject}")
    except Exception as e:
        print(f"  [Newsletter] ❌ 발송 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
