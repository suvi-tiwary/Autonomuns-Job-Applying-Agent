import os
from playwright.async_api import async_playwright

# =========================================================
# FAST BROWSER LAUNCH & LIFECYCLE
# =========================================================

async def open_browser(url: str, headless: bool = False):
    """
    Launch a visible foreground Chromium browser session right on the user's desktop
    pointing to the REAL employer's application page.
    """
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(
            headless=headless,
            slow_mo=80,
            args=[
                "--start-maximized",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-sync",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            no_viewport=True
        )
        page = await context.new_page()
        page.set_default_timeout(20000)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        except Exception:
            try:
                await page.goto(url, wait_until="commit", timeout=10000)
            except Exception:
                pass

        try:
            await page.bring_to_front()
        except Exception:
            pass
            
        return playwright, browser, page
    except Exception:
        await playwright.stop()
        raise


# =========================================================
# FAST PAGE SCROLLING
# =========================================================

async def scroll_page(page):
    """
    Smooth scroll down and up to trigger lazy-loaded form fields on the real employer page.
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
# LOGIN & CAPTCHA DETECTION
# =========================================================

async def detect_login_required(page) -> bool:
    try:
        return await page.evaluate("""
            () => {
                const pw = document.querySelector('input[type="password"]:not([style*="display: none"])');
                return pw !== null && pw.offsetParent !== null;
            }
        """)
    except Exception:
        return False


async def detect_captcha(page) -> bool:
    try:
        return await page.evaluate("""
            () => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                return iframes.some(f => {
                    const src = (f.src || '').toLowerCase();
                    return src.includes('recaptcha') || src.includes('hcaptcha') || src.includes('challenges.cloudflare.com');
                });
            }
        """)
    except Exception:
        return False


# =========================================================
# DOM FIELD EXTRACTION (SINGLE IN-BROWSER JS EVALUATION)
# =========================================================

async def get_application_fields(page):
    """
    Extracts all interactive form fields (inputs, textareas, selects)
    from the REAL employer's web application DOM in a single evaluation.
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
                    if (el.id) {
                        const labelEl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                        if (labelEl && labelEl.innerText.trim()) return labelEl.innerText.trim();
                    }
                    const parentLabel = el.closest('label');
                    if (parentLabel && parentLabel.innerText.trim()) {
                        return parentLabel.innerText.trim();
                    }
                    const labelledby = el.getAttribute('aria-labelledby');
                    if (labelledby) {
                        const refEl = document.getElementById(labelledby);
                        if (refEl && refEl.innerText.trim()) return refEl.innerText.trim();
                    }
                    const ariaLabel = el.getAttribute('aria-label');
                    if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();
                    
                    // Preceding sibling label or span
                    let prev = el.previousElementSibling;
                    while (prev) {
                        if (prev.tagName.toLowerCase() === 'label' || prev.classList.contains('label') || prev.classList.contains('field-label')) {
                            return prev.innerText.trim();
                        }
                        prev = prev.previousElementSibling;
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

                    // Skip hidden, submit, button, image types
                    if (rawType === 'hidden' || rawType === 'submit' || rawType === 'button' || rawType === 'image' || rawType === 'reset') {
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

                    let options = [];
                    if (tag === 'select') {
                        options = Array.from(el.options || []).map(o => ({
                            text: (o.text || '').trim(),
                            value: o.value || ''
                        }));
                    }

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


# =========================================================
# FIELD FILLING & VISUAL HIGHLIGHTING
# =========================================================

async def fill_field(page, index: int, value: str):
    """
    Fill an input/textarea/select on the real employer page with smooth visual focus.
    """
    if value is None:
        return

    val_str = str(value).strip()
    if not val_str and val_str != "0":
        return

    try:
        filled = await page.evaluate("""
            ({ index, val }) => {
                const el = document.querySelector(`[data-agent-index="${index}"]`);
                if (!el) return false;

                const tag = el.tagName.toLowerCase();
                const type = (el.getAttribute('type') || '').toLowerCase();

                if (tag === 'select') {
                    const options = Array.from(el.options);
                    const match = options.find(o => 
                        o.text.trim().toLowerCase() === val.toLowerCase() ||
                        o.value.trim().toLowerCase() === val.toLowerCase() ||
                        o.text.trim().toLowerCase().includes(val.toLowerCase())
                    );
                    if (match) {
                        el.value = match.value;
                    } else if (options.length > 1) {
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

                // Smooth scroll & purple glow on real input
                try {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    el.style.outline = '3px solid #8d6bff';
                    el.style.backgroundColor = 'rgba(141, 107, 255, 0.12)';
                    el.style.transition = 'all 0.2s ease';
                } catch (_) {}

                el.focus();
                try {
                    const prototype = tag === 'textarea' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
                    const setter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
                    if (setter) {
                        setter.call(el, val);
                    } else {
                        el.value = val;
                    }
                } catch (setErr) {
                    el.value = val;
                }
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
                return true;
            }
        """, {"index": index, "val": val_str})

        if not filled:
            loc = page.locator(f"[data-agent-index='{index}']")
            if await loc.count() > 0:
                await loc.fill(val_str)
        
        await page.wait_for_timeout(350)
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

        upload_btn_selectors = [
            "button:has-text('Upload Resume')",
            "button:has-text('Upload CV')",
            "button:has-text('Attach Resume')",
            "label:has-text('Upload Resume')",
            "label:has-text('Upload CV')",
            "label:has-text('Attach Resume')",
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


# =========================================================
# REAL EMPLOYER APPLY & NAVIGATION BUTTONS
# =========================================================

async def click_apply(page) -> bool:
    """
    Clicks 'Apply' or 'Apply for this job' on real ATS pages to expand/scroll the form.
    """
    selectors = [
        "a:has-text('Apply for this job')",
        "button:has-text('Apply for this job')",
        "a:has-text('Apply Now')",
        "button:has-text('Apply Now')",
        "a:has-text('Apply for position')",
        "button:has-text('Apply for position')",
        "a:has-text('Apply')",
        "button:has-text('Apply')",
        "#apply_button",
        ".postings-btn",
        "[data-qa='btn-apply']",
        "a[href*='#app']",
        "a[href*='/apply']"
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible():
                await locator.scroll_into_view_if_needed()
                await locator.click(timeout=3000)
                await page.wait_for_timeout(1000)
                break
        except Exception:
            continue

    # Also ensure smooth scroll to the form container
    try:
        await page.evaluate("""
            () => {
                const formEl = document.querySelector('form, #app, #application, #application_form, [data-qa="application-form"]');
                if (formEl) {
                    formEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        """)
        await page.wait_for_timeout(600)
    except Exception:
        pass

    return True


async def click_next_step_only(page) -> bool:
    """
    Navigates multi-step forms by clicking Next/Continue only.
    NEVER clicks Submit or Finalize!
    """
    selectors = [
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Save and Continue')",
        "input[type='submit'][value*='Next' i]",
        "input[type='submit'][value*='Continue' i]",
        "[role='button']:has-text('Next')",
        "[role='button']:has-text('Continue')"
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible():
                btn_text = (await locator.inner_text() or "").lower()
                # Explicitly avoid Submit
                if "submit" in btn_text or "apply" in btn_text or "send" in btn_text:
                    continue
                await locator.scroll_into_view_if_needed()
                await locator.click(timeout=3000)
                await page.wait_for_timeout(800)
                return True
        except Exception:
            continue

    return False