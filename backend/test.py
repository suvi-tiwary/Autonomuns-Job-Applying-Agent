import asyncio

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
    "email": "rahul.test@example.com",
    "phone": "9876543210",
    "linkedin": "https://linkedin.com/in/rahul",
    "github": "https://github.com/rahul",
    "location": "Noida, India",
    "education": "B.Tech AI/ML",
    "college": "ABC Institute of Technology",
    "experience_years": 1
}


async def main():

    print("Starting AI Browser Agent...")

    url = "https://www.w3schools.com/html/html_forms.asp"

    playwright, browser, page = await open_browser(url)

    print("Browser opened successfully.")
    print("URL:", page.url)

    print("\nScrolling webpage...")

    await scroll_page(page)

    print("\nScanning webpage fields...")

    fields = await get_form_fields(page)

    print(f"Found {len(fields)} fields.")

    for field in fields:

        print("\n--------------------------------")
        print("FIELD:", field)

        profile_key = detect_profile_field(field)

        print("MATCH:", profile_key)

        if profile_key is None:
            print("STATUS: UNKNOWN → LLM REQUIRED")
            continue

        if profile_key not in profile:
            print("STATUS: PROFILE VALUE MISSING")
            continue

        value = profile[profile_key]

        print("VALUE:", value)

        try:
            await fill_field(
                page,
                field["index"],
                value
            )

            print("STATUS: FILLED ✓")

        except Exception as error:

            print("STATUS: FAILED")
            print("ERROR:", error)

    print("\n================================")
    print("Finished field detection.")
    print("Finished field filling.")
    print("Browser will remain open.")
    print("================================")

    await asyncio.sleep(1000)


if __name__ == "__main__":
    asyncio.run(main())