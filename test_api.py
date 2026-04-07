import urllib.request

# Check the HTML being served
resp = urllib.request.urlopen("http://127.0.0.1:8000/")
html = resp.read().decode()

# Check if it's our new HTML or the old one
checks = [
    ("Upload CSV button", "csvUploadInput" in html),
    ("Export dropdown", "exportDropdown" in html),
    ("Action Log panel", "actionLogPanel" in html),
    ("Bulk action bar", "bulkActionBar" in html),
    ("Segment filter", "segmentFilter" in html),
    ("Risk checkboxes", "risk-cb" in html),
    ("Select All checkbox", "selectAllCb" in html),
    ("Toast element", 'id="toast"' in html),
    ("4 metric cards", "metricRecovered" in html),
    ("app.js?v=2", "app.js?v=2" in html),
    ("style.css?v=2", "style.css?v=2" in html),
]

print("=== HTML VERIFICATION ===")
for name, result in checks:
    status = "YES" if result else "MISSING!"
    print(f"  {name}: {status}")

# Check the JS file
resp2 = urllib.request.urlopen("http://127.0.0.1:8000/static/app.js?v=2")
js = resp2.read().decode()
js_checks = [
    ("fetchCustomers function", "fetchCustomers" in js),
    ("bulkAction function", "bulkAction" in js),
    ("renderTable function", "renderTable" in js),
    ("showToast function", "showToast" in js),
    ("singleAction function", "singleAction" in js),
    ("fetchActionLog function", "fetchActionLog" in js),
]
print("\n=== JS VERIFICATION ===")
for name, result in js_checks:
    status = "YES" if result else "MISSING!"
    print(f"  {name}: {status}")

# Check the CSS file
resp3 = urllib.request.urlopen("http://127.0.0.1:8000/static/style.css?v=2")
css = resp3.read().decode()
css_checks = [
    ("Dark theme bg", "--bg-color: #0f172a" in css),
    ("Risk high color", "--risk-high: #ef4444" in css),
    ("Bulk action bar", ".bulk-action-bar" in css),
    ("Action log panel", ".action-log-panel" in css),
    ("Toast styles", ".toast" in css),
    ("Badge segment", ".badge-seg" in css),
]
print("\n=== CSS VERIFICATION ===")
for name, result in css_checks:
    status = "YES" if result else "MISSING!"
    print(f"  {name}: {status}")

print("\n=== ALL CHECKS COMPLETE ===")
