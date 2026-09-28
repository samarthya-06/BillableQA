from playwright.sync_api import expect


def login(page, live_url):
    page.goto(live_url)
    page.locator("#login-email").fill("alice@example.com")
    page.locator("#login-password").fill("DemoPass123!")
    page.get_by_role("button", name="Log in", exact=True).click()
    expect(page.locator("#workspace")).to_be_visible()


def fill_timesheet(page):
    page.get_by_label("Project", exact=True).select_option("2")
    page.get_by_label("Working date").fill("2026-09-28")
    page.get_by_label("Working hours").fill("3")


def test_login_and_logout(page, live_url):
    login(page, live_url)
    expect(page.locator("#employee")).to_have_text("alice@example.com")
    expect(page.locator("#project option")).to_have_count(3)  # Placeholder + Alice's 2 projects.
    page.get_by_role("button", name="Log out", exact=True).click()
    expect(page.locator("#auth")).to_be_visible()
    page.reload()
    expect(page.locator("#workspace")).to_be_hidden()


def test_save_calculate_and_refresh(page, live_url):
    login(page, live_url)
    fill_timesheet(page)
    expect(page.locator("#estimate")).to_have_text("$225.00")
    page.get_by_role("button", name="Save timesheet").click()
    row = page.locator("#history tr")
    expect(row).to_have_count(1)  # One intentional action creates exactly one row.
    expect(row.locator("td").nth(5)).to_have_text("$225.00")
    record_id = row.locator("td").first.inner_text()
    page.reload()
    expect(page.locator("#history tr")).to_have_count(1)
    expect(page.locator("#history tr td").first).to_have_text(record_id)
    expect(page.locator("#history tr td").nth(5)).to_have_text("$225.00")


def test_rapid_double_click(page, live_url):
    login(page, live_url)
    fill_timesheet(page)
    button = page.get_by_role("button", name="Save timesheet")
    box = button.bounding_box()
    # Send two real pointer clicks together, even while the first disables the button.
    page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2, click_count=2, delay=20)
    expect(page.locator("#history tr")).to_have_count(1)
    page.reload()
    expect(page.locator("#history tr")).to_have_count(1)  # Re-fetch the persisted state.
