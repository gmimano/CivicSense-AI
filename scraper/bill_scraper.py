# scraper/bill_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import datetime
import hashlib
import tempfile
from pathlib import Path
import re
import logging
import sys
import os

from unstructured.partition.pdf import partition_pdf
from urllib.parse import quote, urlencode

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

# Supabase
from corefunc.db import supabase_client


BILLS_PAGE_URL = "https://parliament.go.ke/the-national-assembly/house-business/bills"
BASE_URL = "https://parliament.go.ke"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def clean_title_from_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    # Remove bullets and invisible chars
    cleaned = re.sub(
        r"^[\u2022\u2023\u25CF\u25CB\u25A0\u25AA\u00B7·•.\s\-–—]+", "", raw_text
    )
    cleaned = re.sub(r"[\u200b-\u200f\u2060-\u206f]", "", cleaned)
    cleaned = cleaned.strip(" .,-–—")
    return cleaned.strip()


def title_from_filename(href: str) -> str:
    name = Path(urlparse(href).path).stem
    # Remove common junk like %20, numbers in parentheses, etc.
    name = name.replace("%20", " ").replace("_", " ")
    name = re.sub(
        r"\s*\([^)]*\)", "", name
    )  # remove (2), (National Assembly Bills No. 45), etc.
    name = re.sub(r"^THE\s+", "", name, flags=re.IGNORECASE)
    return name.strip().title()


def get_good_title(raw_text: str, href: str) -> str:
    title = clean_title_from_text(raw_text)
    if title:
        return title
    # Fallback to filename if link text was empty/trash
    return title_from_filename(href)


def normalize_url(href: str) -> str:
    """
    Normalize relative URLs and handle malformed paths.
    Ensures URLs are proper absolute URLs before making requests.
    """
    href = href.strip()

    # If it's already an absolute URL, return as-is
    if href.startswith("http://") or href.startswith("https://"):
        return href

    # Remove leading dots and slashes, then join properly
    href = href.lstrip("./")

    # Join with base URL to create absolute URL
    absolute_url = urljoin(BASE_URL, "/" + href if not href.startswith("/") else href)

    return absolute_url


def download_pdf(pdf_url: str) -> bytes:
    # Encode special characters in the URL
    try:
        print(f"Downloading from: {pdf_url}")
        r = requests.get(pdf_url, headers=HEADERS, timeout=90)
        r.raise_for_status()
        return r.content
    except requests.exceptions.RequestException as e:
        print(f"Download failed for {pdf_url}: {e}")
        raise


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Use pymupdf (fitz) for fast text extraction"""
    try:
        import fitz  # pymupdf

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        return text.strip() or "[No text extracted]"
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")
        # Fallback to unstructured
        return extract_text_from_pdf_fallback(pdf_bytes)


def extract_text_from_pdf_fallback(pdf_bytes: bytes) -> str:
    """Fallback using unstructured with different strategies"""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "bill.pdf"
        path.write_bytes(pdf_bytes)
        try:
            # Try auto strategy first
            elements = partition_pdf(
                filename=str(path),
                strategy="auto",  # Changed from "ocr_only"
                languages=["eng"],
            )
            text = "\n\n".join([e.text for e in elements if e.text and e.text.strip()])
            return text.strip() or "[No text extracted]"
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return "[Text extraction failed]"


def scrape_and_save_bills():
    print("Scraping Kenyan Parliament bills...")
    try:
        resp = requests.get(BILLS_PAGE_URL, headers=HEADERS, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch bills page: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    links = soup.find_all("a", href=True)
    print(f"Found {len(links)} <a> tags → filtering PDFs...")

    new_bills = 0
    failed_bills = 0

    for a in links:
        href = a["href"].strip()
        if not href.lower().endswith(".pdf"):
            continue
        if "tracker" in href.lower() or "status" in href.lower():
            continue
        pdf_url = urljoin(BILLS_PAGE_URL, href)
        raw_text = a.get_text(strip=True)
        title = get_good_title(raw_text, href)

        try:
            # Normalize the URL to ensure it's properly formatted
            pdf_url = normalize_url(href)
            raw_text = a.get_text(strip=True)
            title = get_good_title(raw_text, href)

            print(f"Downloading → {title}")
            print(f"  URL: {pdf_url}")

            # Additional validation
            if not pdf_url or pdf_url == "." or pdf_url == "..":
                print(f"   (Skipping invalid URL: {pdf_url})")
                continue

            pdf_bytes = download_pdf(pdf_url)
            pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

            # Duplicate check
            existing = (
                supabase_client.table("bills")
                .select("id")
                .eq("pdf_hash", pdf_hash)
                .execute()
            )

            if existing.data:
                print("   (already in DB – skipping)")
                continue

            full_text = extract_text_from_pdf(pdf_bytes)

            supabase_client.table("bills").insert(
                {
                    "title": title,
                    "pdf_url": pdf_url,
                    "pdf_hash": pdf_hash,
                    "full_text": full_text[:500_000],
                    "status": "Published",
                    "published_at": datetime.datetime.utcnow().isoformat(),
                }
            ).execute()

            new_bills += 1
            print(f"✓ Saved: {title}")

        except Exception as e:
            failed_bills += 1
            print(f"✗ Failed {title}: {e}")
            # Print full error details for debugging
            import traceback

            traceback.print_exc()

    print(f"\nDone! {new_bills} new bills saved, {failed_bills} failed.")


if __name__ == "__main__":
    scrape_and_save_bills()
