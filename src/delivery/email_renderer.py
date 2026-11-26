"""Editorial HTML newsletter renderer for Gmail & local preview matching The Daily Edge design."""

from __future__ import annotations

import html
from typing import Any

from src.config import BRAND_CONFIG
from src.editorial.citations import resolve_citations
from src.editorial.lesson_formatter import parse_structured_lesson, strip_technical_clutter
from src.storage.local_db import LocalKnowledgeDB


def _nl2br(text: str) -> str:
    return html.escape(text or "").replace("\n", "<br>")


def _render_lesson_html(raw_text: str, pillar: str) -> str:
    parsed = parse_structured_lesson(raw_text, pillar)
    title_html = f'<h3 style="margin:0 0 10px 0;font-size:17px;color:#0B162C;">{html.escape(parsed["title"])}</h3>'
    if parsed["is_structured"]:
        parts = []
        labels = [
            ("core_idea", "The Core Idea"),
            ("why_it_matters", "Why It Matters"),
            ("what_research_says", "What Science & Research Say"),
            ("real_life_example", "Real-Life Example"),
            ("practical_application", "Practical Application"),
            ("key_takeaway", "Key Takeaway"),
        ]
        for key, label in labels:
            val = parsed["sections"].get(key)
            if val:
                parts.append(
                    f'<p style="margin:0 0 10px 0;font-size:14.5px;line-height:1.65;color:#1E293B;">'
                    f'<strong style="color:#0B162C;">{label}:</strong> {_nl2br(val)}</p>'
                )
        return title_html + "".join(parts)
    return title_html + f'<p style="margin:0;font-size:14.5px;line-height:1.65;color:#1E293B;">{_nl2br(parsed["clean_prose"])}</p>'


def render_newsletter_html(
    brief: dict[str, Any],
    doc_url: str = "",
    db: LocalKnowledgeDB | None = None,
) -> str:
    """Render The Daily Edge newsletter into a premium editorial HTML email."""
    date_str = html.escape(str(brief.get("date", "")))
    is_ai = str(brief.get("is_ai_verified", False)).lower() == "true" or brief.get("is_ai_verified") is True
    status_label = "Editorially Verified" if is_ai else "Curated Source Digest"
    status_bg = "#14532D" if is_ai else "#334155"

    citations = resolve_citations(brief.get("source_links", []), db=db)
    links_html = "".join(
        f'<li style="margin-bottom:8px;">'
        f'<strong style="color:#0B162C;">Source: {html.escape(c["source_name"])}</strong> &ndash; '
        f'<a href="{html.escape(c["url"])}" target="_blank" rel="noopener noreferrer" '
        f'style="color:#1D4ED8;text-decoration:none;font-weight:600;">{html.escape(c["title"])} &#8599;</a>'
        f"</li>"
        for c in citations
    ) or "<li>Sources archived in your Life Time Library dashboard.</li>"

    doc_banner = (
        f'<p style="margin:14px 0 0 0;"><a href="{html.escape(doc_url)}" target="_blank" rel="noopener noreferrer" '
        f'style="display:inline-block;background:#C59B38;color:#0B162C;padding:9px 16px;'
        f'border-radius:6px;text-decoration:none;font-weight:700;font-size:13px;">Open Full Report in Google Docs &#8599;</a></p>'
        if doc_url
        else ""
    )

    linkedin_url = html.escape(BRAND_CONFIG["creator_linkedin_url"])
    creator_name = html.escape(BRAND_CONFIG["creator_name"])
    brand_name = html.escape(BRAND_CONFIG["brand_name"])
    main_title = html.escape(BRAND_CONFIG["main_title"])
    tagline = html.escape(BRAND_CONFIG["tagline"])
    closing = html.escape(BRAND_CONFIG["footer_closing"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{brand_name} – {main_title} – {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#FAF8F3;font-family:Segoe UI,Arial,sans-serif;color:#0F172A;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:28px 12px;background:#FAF8F3;">
    <tr>
      <td align="center">
        <table role="presentation" width="660" cellspacing="0" cellpadding="0" style="max-width:660px;width:100%;background:#FFFFFF;border-radius:14px;overflow:hidden;border:1px solid #E5E0D5;box-shadow:0 8px 24px rgba(11,22,44,0.06);">
          <tr>
            <td style="background:#0B162C;color:#FAF8F3;padding:28px 32px;border-bottom:3px solid #C59B38;">
              <div style="font-size:11px;letter-spacing:1.8px;text-transform:uppercase;color:#C59B38;font-weight:700;">{brand_name}</div>
              <h1 style="margin:6px 0 4px 0;font-family:Georgia,serif;font-size:26px;line-height:1.25;color:#FFFFFF;">{main_title}</h1>
              <div style="font-size:13px;color:#CBD5E1;margin-bottom:12px;">{tagline}</div>
              <span style="display:inline-block;background:{status_bg};color:#F8FAFC;font-size:11px;padding:4px 10px;border-radius:999px;font-weight:600;letter-spacing:0.4px;">{date_str} &bull; {status_label}</span>
              {doc_banner}
            </td>
          </tr>

          <tr>
            <td style="padding:28px 32px;">
              <div style="background:#F4FBF8;border-left:4px solid #1F7A5C;padding:16px 18px;border-radius:8px;margin-bottom:20px;">
                <div style="font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:#1F7A5C;font-weight:700;margin-bottom:4px;">HEALTH &bull; Build a healthier body and mind</div>
                {_render_lesson_html(str(brief.get("health_lesson", "")), "Health")}
              </div>

              <div style="background:#F4F8FD;border-left:4px solid #1D4ED8;padding:16px 18px;border-radius:8px;margin-bottom:20px;">
                <div style="font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:#1D4ED8;font-weight:700;margin-bottom:4px;">WEALTH &bull; Financial intelligence &amp; wealth-building</div>
                {_render_lesson_html(str(brief.get("wealth_lesson", "")), "Wealth")}
              </div>

              <div style="background:#F8F5FE;border-left:4px solid #6D28D9;padding:16px 18px;border-radius:8px;margin-bottom:22px;">
                <div style="font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:#6D28D9;font-weight:700;margin-bottom:4px;">WISDOM &bull; Critical thinking &amp; decision-making</div>
                {_render_lesson_html(str(brief.get("wisdom_lesson", "")), "Wisdom")}
              </div>

              <h3 style="margin:22px 0 8px 0;font-family:Georgia,serif;font-size:18px;color:#0B162C;">Deep Dive</h3>
              <p style="margin:0 0 18px 0;font-size:15px;line-height:1.65;color:#334155;">{_nl2br(strip_technical_clutter(str(brief.get("deep_dive", ""))))}</p>

              <h3 style="margin:20px 0 8px 0;font-family:Georgia,serif;font-size:18px;color:#0B162C;">Surprising Discovery</h3>
              <p style="margin:0 0 18px 0;font-size:15px;line-height:1.65;color:#334155;">{_nl2br(strip_technical_clutter(str(brief.get("surprising_discovery", ""))))}</p>

              <h3 style="margin:20px 0 8px 0;font-family:Georgia,serif;font-size:18px;color:#0B162C;">Mental Model of the Day</h3>
              <p style="margin:0 0 18px 0;font-size:15px;line-height:1.65;color:#334155;">{_nl2br(strip_technical_clutter(str(brief.get("mental_model", ""))))}</p>

              <div style="background:#FEF9EC;border:1px solid #EED99C;padding:16px 18px;border-radius:10px;margin-bottom:16px;">
                <h3 style="margin:0 0 6px 0;font-size:15px;color:#7C5808;">Today's Action (10 Minutes)</h3>
                <p style="margin:0;font-size:14.5px;line-height:1.55;color:#1E293B;">{_nl2br(strip_technical_clutter(str(brief.get("todays_action", ""))))}</p>
              </div>

              <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:16px 18px;border-radius:10px;margin-bottom:22px;">
                <h3 style="margin:0 0 6px 0;font-size:15px;color:#0B162C;">Reflection Question</h3>
                <p style="margin:0;font-size:14.5px;line-height:1.55;color:#334155;">{_nl2br(strip_technical_clutter(str(brief.get("reflection_question", ""))))}</p>
              </div>

              <h3 style="margin:20px 0 10px 0;font-family:Georgia,serif;font-size:16px;color:#0B162C;">Original Sources</h3>
              <ul style="margin:0;padding-left:18px;font-size:13.5px;line-height:1.6;color:#334155;">
                {links_html}
              </ul>
            </td>
          </tr>

          <tr>
            <td style="background:#0B162C;color:#CBD5E1;padding:22px 32px;border-top:2px solid #C59B38;text-align:center;">
              <div style="font-family:Georgia,serif;font-size:15px;color:#FFFFFF;font-weight:700;">{brand_name} &bull; {main_title}</div>
              <div style="font-size:12.5px;color:#CBD5E1;margin-top:4px;">Created by {creator_name}</div>
              <div style="margin:10px 0;">
                <a href="{linkedin_url}" target="_blank" rel="noopener noreferrer" style="color:#60A5FA;text-decoration:none;font-size:13px;font-weight:600;">Connect with me on LinkedIn &#8599;</a>
              </div>
              <div style="font-size:11.5px;color:#94A3B8;margin-top:6px;">&copy; {BRAND_CONFIG["copyright_year"]} {creator_name}. All rights reserved. &bull; {closing}</div>
              <div style="font-size:11px;color:#64748B;margin-top:6px;">Educational content only (not medical or personalized investment advice).</div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
