#!/usr/bin/env python3
"""
Daily AI SCM 학습 도구 — Entry Point

사용법:
  python run_daily.py --morning          # 아침 학습 이메일 발송
  python run_daily.py --evening          # 저녁 퀴즈 이메일 발송
  python run_daily.py --both             # 아침 + 저녁 순차 발송
  python run_daily.py --dry-run          # 이메일 대신 HTML 파일로 저장
  python run_daily.py --status           # 학습 진도 확인
  python run_daily.py --reset            # 진도 초기화
  python run_daily.py --preview morning  # 미리보기 (dry-run + 브라우저 열기)

스케줄 예시 (crontab):
  0 7  * * * cd /Users/idongseong/Documents/New project/ai_scm_project && python run_daily.py --morning
  0 20 * * * cd /Users/idongseong/Documents/New project/ai_scm_project && python run_daily.py --evening
"""

import os
import sys
import argparse
import subprocess
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_morning(dry_run: bool = False):
    from agents.daily.morning_agent import send_morning_email
    ok = send_morning_email(dry_run=dry_run)
    return ok


def cmd_evening(dry_run: bool = False):
    from agents.daily.evening_agent import send_evening_email
    ok = send_evening_email(dry_run=dry_run)
    return ok


def cmd_status():
    from agents.daily.progress_agent import print_status
    print_status()


def cmd_reset():
    import config
    state_file = os.path.join(config.DATA_DIR, "progress_state.json")
    if os.path.exists(state_file):
        os.remove(state_file)
        print("[Daily] 학습 진도 초기화 완료")
    else:
        print("[Daily] 초기화할 진도 파일 없음")


def cmd_preview(which: str):
    """dry-run 후 브라우저로 미리보기"""
    import config
    if which == "morning":
        cmd_morning(dry_run=True)
        pattern = f"morning_email_{datetime.date.today()}.html"
    else:
        cmd_evening(dry_run=True)
        pattern = f"evening_email_{datetime.date.today()}.html"
    html_path = os.path.join(config.REPORTS_DIR, pattern)
    if os.path.exists(html_path):
        subprocess.run(["open", html_path])
        print(f"[Daily] 브라우저로 열기: {html_path}")
    else:
        print(f"[Daily] 파일 없음: {html_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AI SCM Daily 학습 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--morning",  action="store_true", help="아침 학습 이메일 발송")
    group.add_argument("--evening",  action="store_true", help="저녁 퀴즈 이메일 발송")
    group.add_argument("--both",     action="store_true", help="아침 + 저녁 순차 발송")
    group.add_argument("--status",   action="store_true", help="학습 진도 확인")
    group.add_argument("--reset",    action="store_true", help="진도 초기화")
    group.add_argument("--preview",  choices=["morning", "evening"], help="HTML 미리보기")

    parser.add_argument("--dry-run", action="store_true", help="이메일 대신 파일로 저장")

    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"AI SCM Daily Learning  |  {datetime.date.today()}")
    print(f"{'='*55}")

    if args.status:
        cmd_status()
    elif args.reset:
        cmd_reset()
    elif args.preview:
        cmd_preview(args.preview)
    elif args.morning:
        ok = cmd_morning(dry_run=args.dry_run)
        sys.exit(0 if ok else 1)
    elif args.evening:
        ok = cmd_evening(dry_run=args.dry_run)
        sys.exit(0 if ok else 1)
    elif args.both:
        ok1 = cmd_morning(dry_run=args.dry_run)
        ok2 = cmd_evening(dry_run=args.dry_run)
        sys.exit(0 if (ok1 and ok2) else 1)


if __name__ == "__main__":
    main()
