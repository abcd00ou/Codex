"""
Email Agent
- Gmail SMTP로 학습 문서 자동 발송
- App Password 인증
- DOCX 첨부 지원
"""

import smtplib
import ssl
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT      = os.environ.get("GMAIL_RECIPIENT", GMAIL_ADDRESS)


LEVEL_COLORS = {1: "#1a73e8", 2: "#0d652d", 3: "#b31412"}
LEVEL_LABELS = {1: "📗 Lv.1 기초", 2: "📘 Lv.2 심화", 3: "📕 Lv.3 전문가"}
LEVEL_DESC   = {
    1: "마케터 입문 — 개념·용어·시장 구조 이해",
    2: "정량 모델·케이스 스터디·공급망 메커니즘",
    3: "최신 트렌드·투자 리포트·시나리오 분석",
}


def send_study_doc(docx_path: str, topic_title: str, topic_num: int, total: int,
                   level: int = 1, round_num: int = 1) -> bool:
    """학습 문서를 Gmail로 발송한다."""
    if not os.path.exists(docx_path):
        print(f"  [EmailAgent] ERROR: 파일 없음 → {docx_path}")
        return False

    now      = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    lv_label = LEVEL_LABELS.get(level, f"Lv.{level}")
    color    = LEVEL_COLORS.get(level, "#1a73e8")
    subject  = f"[AI SCM {lv_label}] {topic_num}/{total} - {topic_title} ({date_str})"

    body_html = f"""
<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<h2 style="color:{color};">{lv_label} AI 공급망 학습 자료</h2>
<p style="color:#555; font-size:13px; margin-top:-8px;">{LEVEL_DESC.get(level,'')}</p>
<table style="border-collapse:collapse; margin-bottom:16px; font-size:14px;">
  <tr><td style="padding:4px 16px 4px 0; font-weight:bold; color:#555;">주제</td>
      <td style="padding:4px 0;">{topic_title}</td></tr>
  <tr><td style="padding:4px 16px 4px 0; font-weight:bold; color:#555;">라운드</td>
      <td style="padding:4px 0;">Round {round_num} ({lv_label})</td></tr>
  <tr><td style="padding:4px 16px 4px 0; font-weight:bold; color:#555;">전체 진행</td>
      <td style="padding:4px 0;">{topic_num} / {total}</td></tr>
  <tr><td style="padding:4px 16px 4px 0; font-weight:bold; color:#555;">생성일시</td>
      <td style="padding:4px 0;">{date_str}</td></tr>
</table>
<p>첨부된 Word 파일을 열어 학습하세요.<br>
각 챕터의 <strong>퀴즈 섹션</strong>을 통해 Feynman Technique으로 복습하고,<br>
다음 라운드에서 더 심화된 내용으로 같은 주제를 다시 만납니다.</p>
<hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
<p style="font-size:12px; color:#888;">AI SCM Intelligence System • 자동 생성 학습 자료</p>
</body></html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # DOCX 첨부
    filename = os.path.basename(docx_path)
    with open(docx_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, RECIPIENT, msg.as_bytes())
        print(f"  [EmailAgent] ✅ 발송 완료: {subject}")
        return True
    except Exception as e:
        print(f"  [EmailAgent] ❌ 발송 실패: {e}")
        return False


if __name__ == "__main__":
    # 테스트: HBM 문서 발송
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config
    docx = os.path.join(config.REPORTS_DIR, "study_hbm_deep_dive_20260325.docx")
    send_study_doc(docx, "HBM (High Bandwidth Memory) 심화", 1, 8)
