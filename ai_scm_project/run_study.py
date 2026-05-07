#!/usr/bin/env python3
"""
AI SCM 학습 시스템 — 30분 cron 진입점

사용법:
  python3 run_study.py              # 다음 주제 이메일 발송
  python3 run_study.py --dry-run    # HTML 파일로 저장 (발송 안 함)
  python3 run_study.py --preview    # dry-run + 브라우저 열기
  python3 run_study.py --status     # 진도 확인
  python3 run_study.py --reset      # 진도 초기화

Crontab:
  */30 * * * * GMAIL_APP_PASSWORD="..." bash -c 'cd /path && python3 run_study.py'
"""
import os, sys, argparse, datetime, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="AI SCM 학습 이메일 발송")
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--preview",  action="store_true")
    parser.add_argument("--status",   action="store_true")
    parser.add_argument("--reset",    action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"AI SCM Study  |  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")

    if args.status:
        from agents.daily.progress_agent import print_status
        print_status()
        return

    if args.reset:
        import config
        f = os.path.join(config.DATA_DIR, "progress_state.json")
        if os.path.exists(f):
            os.remove(f)
        print("[Study] 진도 초기화 완료")
        return

    from agents.daily.progress_agent    import get_current_topic, advance
    from agents.daily.study_email_agent import send_study_email

    topic = get_current_topic()
    print(f"주제: [{topic['num']}/{topic['total']}] {topic['title']} ({topic['round_meta']['label']})")

    dry = args.dry_run or args.preview
    ok  = send_study_email(topic, dry_run=dry)

    if ok:
        if not dry:
            advance(topic["id"], topic["round"])
        if args.preview:
            import config
            out = os.path.join(config.REPORTS_DIR, f"study_{topic['id']}_{datetime.date.today()}.html")
            if os.path.exists(out):
                subprocess.run(["open", out])

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
