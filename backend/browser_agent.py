import os
from playwright.async_api import async_playwright

# =========================================================
# FAST BROWSER LAUNCH & LIFECYCLE
# =========================================================

async def open_browser(url: str, headless: bool = False):
    """
    Launch a visible Playwright Chromium browser session with slow_mo so user can watch automation.
    """
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(
            headless=headless,
            slow_mo=120,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1280,850"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        page.set_default_timeout(20000)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            # Fallback if domcontentloaded stalls on heavy ads/trackers
            await page.goto(url, wait_until="commit", timeout=20000)
            
        return playwright, browser, page
    except Exception:
        await playwright.stop()
        raise


# =========================================================
# FAST PAGE SCROLLING
# =========================================================

async def scroll_page(page):
    """
    Fast smooth scroll down and up to trigger lazy-loaded form fields.
    """
    try:
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 400;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if (totalHeight >= scrollHeight || totalHeight >= 3000) {
                            clearInterval(timer);
                            window.scrollTo(0, 0);
                            resolve();
                        }
                    }, 50);
                });
            }
        """)
        await page.wait_for_timeout(300)
    except Exception:
        pass


# =========================================================
# TEXT HELPERS
# =========================================================

def normalize(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


# =========================================================
# LOGIN DETECTION
# =========================================================

async def detect_login_required(page) -> bool:
    try:
        return await page.evaluate("""
            () => {
                const pw = document.querySelector('input[type="password"]:not([style*="display: none"])');
                if (pw && pw.offsetParent !== null) return true;
                
                const bodyText = (document.body.innerText || '').toLowerCase();
                const loginPhrases = [
                    'sign in to apply',
                    'log in to apply',
                    'login to apply',
                    'please sign in to continue',
                    'please log in to continue',
                    'create an account to apply'
                ];
                return loginPhrases.some(phrase => bodyText.includes(phrase));
            }
        """)
    except Exception:
        return False


# =========================================================
# ULTRA-FAST DOM FIELD EXTRACTION (SINGLE JS EVALUATION)
# =========================================================

async def get_application_fields(page):
    """
    Extracts all interactive form fields (inputs, textareas, selects)
    in a single, high-performance in-browser JavaScript evaluation.
    Executes in < 5ms instead of hundreds of IPC calls.
    """
    try:
        fields = await page.evaluate("""
            () => {
                const isVisible = (el) => {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                };

                const getLabel = (el) => {
                    // 1. Check label[for=id]
                    if (el.id) {
                        const labelEl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                        if (labelEl && labelEl.innerText.trim()) return labelEl.innerText.trim();
                    }
                    // 2. Check enclosing label
                    const parentLabel = el.closest('label');
                    if (parentLabel && parentLabel.innerText.trim()) {
                        return parentLabel.innerText.trim();
                    }
                    // 3. Check aria-labelledby
                    const labelledby = el.getAttribute('aria-labelledby');
                    if (labelledby) {
                        const refEl = document.getElementById(labelledby);
                        if (refEl && refEl.innerText.trim()) return refEl.innerText.trim();
                    }
                    // 4. Check aria-label
                    const ariaLabel = el.getAttribute('aria-label');
                    if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();
                    
                    // 5. Check placeholder
                    const placeholder = el.getAttribute('placeholder');
                    if (placeholder && placeholder.trim()) return placeholder.trim();

                    // 6. Check closest container text / previous sibling
                    let prev = el.previousElementSibling;
                    if (prev && prev.innerText && prev.innerText.trim().length < 100) {
                        return prev.innerText.trim();
                    }
                    const container = el.closest('div, p, fieldset, li');
                    if (container) {
                        const text = container.innerText || '';
                        if (text.trim().length > 0 && text.trim().length < 150) {
                            return text.trim();
                        }
                    }
                    return '';
                };

                const elements = Array.from(document.querySelectorAll('input, textarea, select'));
                const result = [];
                let visibleIndex = 0;

                for (let i = 0; i < elements.length; i++) {
                    const el = elements[i];
                    const tag = el.tagName.toLowerCase();
                    const rawType = (el.getAttribute('type') || '').toLowerCase();
                    
                    // Skip hidden, submit, button, reset elements
                    if (['hidden', 'submit', 'button', 'reset', 'image'].includes(rawType)) {
                        continue;
                    }

                    const visible = isVisible(el) || rawType === 'file';
                    if (!visible) continue;

                    let elementType = rawType;
                    if (tag === 'textarea') elementType = 'textarea';
                    else if (tag === 'select') elementType = 'select';
                    else if (!elementType) elementType = 'text';

                    let value = '';
                    if (elementType === 'checkbox' || elementType === 'radio') {
                        value = el.checked ? 'checked' : '';
                    } else if (elementType === 'file') {
                        value = el.value || '';
                    } else {
                        value = el.value || '';
                    }

                    const label = getLabel(el);
                    const name = el.getAttribute('name') || '';
                    const id = el.id || '';
                    const placeholder = el.getAttribute('placeholder') || '';
                    const ariaLabel = el.getAttribute('aria-label') || '';
                    const autocomplete = el.getAttribute('autocomplete') || '';
                    const isRequired = el.hasAttribute('required') || 
                                       el.getAttribute('aria-required') === 'true' || 
                                       label.includes('*');

                    // Extract select options if select
                    let options = [];
                    if (tag === 'select') {
                        options = Array.from(el.options || []).map(o => ({
                            text: (o.text || '').trim(),
                            value: o.value || ''
                        }));
                    }

                    // Mark a data attribute so we can find this exact element reliably
                    el.setAttribute('data-agent-index', visibleIndex.toString());

                    result.push({
                        index: visibleIndex,
                        globalIndex: i,
                        tag: tag,
                        type: elementType,
                        id: id,
                        name: name,
                        label: label.substring(0, 300),
                        placeholder: placeholder,
                        aria_label: ariaLabel,
                        autocomplete: autocomplete,
                        required: Boolean(isRequired),
                        value: value,
                        options: options
                    });

                    visibleIndex++;
                }

                return result;
            }
        """)
        return fields or []
    except Exception as e:
        print(f"Error extracting form fields: {e}")
        return []


# Alias for backward compatibility
get_form_fields = get_application_fields


# =========================================================
# ULTRA-FAST FIELD FILLING
# =========================================================

async def fill_field(page, index: int, value: str):
    """
    Directly fill an input/textarea/select/checkbox/radio by agent index.
    """
    if value is None:
        return

    val_str = str(value).strip()
    if not val_str and val_str != "0":
        return

    try:
        # Use fast in-browser JavaScript interaction first
        filled = await page.evaluate("""
            ({ index, val }) => {
                const el = document.querySelector(`[data-agent-index="${index}"]`);
                if (!el) return false;

                const tag = el.tagName.toLowerCase();
                const type = (el.getAttribute('type') || '').toLowerCase();

                if (tag === 'select') {
                    // Try to match option by text or value
                    const options = Array.from(el.options);
                    const match = options.find(o => 
                        o.text.trim().toLowerCase() === val.toLowerCase() ||
                        o.value.trim().toLowerCase() === val.toLowerCase() ||
                        o.text.trim().toLowerCase().includes(val.toLowerCase())
                    );
                    if (match) {
                        el.value = match.value;
                    } else if (options.length > 1) {
                        // Pick second option if first is placeholder
                        el.selectedIndex = 1;
                    }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }

                if (type === 'checkbox') {
                    const shouldCheck = ['true', 'yes', '1', 'checked', 'agree'].includes(val.toLowerCase());
                    if (shouldCheck && !el.checked) {
                        el.click();
                        el.checked = true;
                    }
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }

                if (type === 'radio') {
                    if (!el.checked) {
                        el.click();
                        el.checked = true;
                    }
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }

                // Visual element highlighting for live inspection
                try {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    el.style.outline = '3px solid #8d6bff';
                    el.style.backgroundColor = 'rgba(141, 107, 255, 0.15)';
                    el.style.transition = 'all 0.2s ease';
                } catch (_) {}

                // Standard input / textarea
                el.focus();
                el.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
                return true;
            }
        """, {"index": index, "val": val_str})

        if not filled:
            # Fallback to Playwright locator if JS didn't find data-agent-index
            loc = page.locator(f"[data-agent-index='{index}']")
            if await loc.count() > 0:
                await loc.fill(val_str)
    except Exception as e:
        print(f"Warning: could not fill field {index}: {e}")


# =========================================================
# RESUME UPLOAD
# =========================================================

async def upload_resume(page, resume_path: str) -> bool:
    if not resume_path or not os.path.isfile(resume_path):
        return False

    abs_path = os.path.abspath(resume_path)

    try:
        # 1. Look for visible or hidden file input
        file_inputs = page.locator("input[type='file']")
        count = await file_inputs.count()
        
        if count > 0:
            for i in range(count):
                try:
                    await file_inputs.nth(i).set_input_files(abs_path)
                    await page.wait_for_timeout(500)
                    return True
                except Exception:
                    continue

        # 2. If no direct input or set_input_files failed, try clicking upload button with file chooser
        upload_btn_selectors = [
            "button:has-text('Upload Resume')",
            "button:has-text('Upload CV')",
            "button:has-text('Upload')",
            "label:has-text('Upload Resume')",
            "label:has-text('Upload CV')",
            "[aria-label*='upload' i]"
        ]
        for sel in upload_btn_selectors:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                try:
                    async with page.expect_file_chooser(timeout=3000) as fc_info:
                        await loc.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(abs_path)
                    await page.wait_for_timeout(500)
                    return True
                except Exception:
                    pass
    except Exception as e:
        print(f"Resume upload notice: {e}")

    return False


async def click_apply(page) -> bool:
    selectors = [
        "a:has-text('Apply for this job')",
        "button:has-text('Apply for this job')",
        "a:has-text('Apply Now')",
        "button:has-text('Apply Now')",
        "button:has-text('Easy Apply')",
        "a:has-text('Easy Apply')",
        "a:has-text('Apply for position')",
        "button:has-text('Apply for position')",
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "a:has-text('Find Your Next Job')",
        "button:has-text('Find Your Next Job')",
        "a:has-text('Open Positions')",
        "button:has-text('Open Positions')",
        "a:has-text('View Openings')",
        "button:has-text('View Openings')",
        "[role='button']:has-text('Apply')",
        "input[type='submit'][value*='Apply' i]"
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = await locator.count()
            for i in range(count):
                element = locator.nth(i)
                if await element.is_visible():
                    await element.scroll_into_view_if_needed()
                    await element.click(timeout=3000)
                    await page.wait_for_timeout(1000)
                    return True
        except Exception:
            continue

    return False


# =========================================================
# NEXT / CONTINUE BUTTON
# =========================================================

async def click_next(page) -> bool:
    selectors = [
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Save and Continue')",
        "button:has-text('Review')",
        "button:has-text('Proceed')",
        "input[type='submit'][value*='Next' i]",
        "input[type='submit'][value*='Continue' i]",
        "[role='button']:has-text('Next')",
        "[role='button']:has-text('Continue')"
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = await locator.count()
            for i in range(count):
                element = locator.nth(i)
                if await element.is_visible() and await element.is_enabled():
                    await element.scroll_into_view_if_needed()
                    await element.click(timeout=3000)
                    await page.wait_for_timeout(500)
                    return True
        except Exception:
            continue

    return False


# =========================================================
# SUBMIT APPLICATION BUTTON
# =========================================================

async def submit_application(page) -> bool:
    selectors = [
        "button:has-text('Submit Application')",
        "button:has-text('Submit your application')",
        "button:has-text('Send Application')",
        "button:has-text('Submit')",
        "input[type='submit'][value*='Submit' i]",
        "button[type='submit']",
        "[role='button']:has-text('Submit Application')",
        "[role='button']:has-text('Submit')"
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = await locator.count()
            for index in range(count):
                button = locator.nth(index)
                if await button.is_visible() and await button.is_enabled():
                    # Avoid false match with 'Search' or 'Subscribe'
                    btn_text = (await button.inner_text() or "").lower()
                    if "subscribe" in btn_text or "search" in btn_text or "newsletter" in btn_text:
                        continue
                    await button.scroll_into_view_if_needed()
                    await button.click(timeout=4000)
                    await page.wait_for_timeout(1000)
                    return True
        except Exception:
            continue

    return False


# =========================================================
# GET PAGE TEXT
# =========================================================

async def get_page_text(page) -> str:
    try:
        return await page.evaluate("() => document.body.innerText.substring(0, 20000)")
    except Exception:
        return ""