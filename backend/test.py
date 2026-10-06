import asyncio
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from browser_agent import (
    open_browser,
    get_form_fields,
    fill_field,
    scroll_page
)
from field_mapper import detect_profile_field

profile = {
    "first_name": "Rahul",
    "last_name": "Sharma",
    "full_name": "Rahul Sharma",
    "email": "rahul.test@example.com",
    "phone": "9876543210",
    "linkedin": "https://linkedin.com/in/rahul",
    "github": "https://github.com/rahul",
    "location": "Noida, India",
    "education": "B.Tech AI/ML",
    "college": "ABC Institute of Technology",
    "experience_years": "1"
}


async def main():
    print("Starting AI Browser Agent test...")
    url = "https://www.w3schools.com/html/html_forms.asp"

    playwright, browser, page = await open_browser(url, headless=True)
    print("Browser opened successfully.")
    print("URL:", page.url)

    print("\nScrolling webpage...")
    await scroll_page(page)

    print("\nScanning webpage fields...")
    fields = await get_form_fields(page)
    print(f"Found {len(fields)} fields.")

    for field in fields[:5]:
        print("\n--------------------------------")
        print("FIELD:", field.get("name") or field.get("label") or field.get("id"))
        profile_key = detect_profile_field(field)
        print("MATCH:", profile_key)

        if profile_key and profile_key in profile:
            val = profile[profile_key]
            await fill_field(page, field["index"], val)
            print(f"STATUS: FILLED with '{val}' [OK]")
        else:
            print("STATUS: SKIPPED (No match or not in profile)")

    print("\n================================")
    print("Test completed successfully!")
    print("================================")

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())