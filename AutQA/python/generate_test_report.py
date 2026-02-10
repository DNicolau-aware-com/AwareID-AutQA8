"""
Check if reports are being generated.
"""

from pathlib import Path
from datetime import datetime

def check_reports():
    """Check for existing reports."""
    print("\n" + "="*80)
    print("CHECKING FOR REPORTS")
    print("="*80)
    
    # Check directories
    test_results = Path("test_results")
    reports_dir = test_results / "reports"
    
    if not test_results.exists():
        print("\n✗ test_results directory does NOT exist!")
        return False
    else:
        print(f"\n✓ test_results directory exists: {test_results.absolute()}")
    
    if not reports_dir.exists():
        print("✗ reports subdirectory does NOT exist!")
        return False
    else:
        print(f"✓ reports directory exists: {reports_dir.absolute()}")
    
    # Check for HTML reports
    html_reports = list(reports_dir.glob("*.html"))
    if html_reports:
        print(f"\n✓ Found {len(html_reports)} HTML report(s):")
        for report in sorted(html_reports, key=lambda x: x.stat().st_mtime, reverse=True):
            modified = datetime.fromtimestamp(report.stat().st_mtime)
            size = report.stat().st_size
            print(f"  - {report.name}")
            print(f"    Modified: {modified}")
            print(f"    Size: {size:,} bytes")
    else:
        print("\n✗ No HTML reports found!")
    
    # Check for JSON files
    json_files = list(test_results.glob("*.json"))
    if json_files:
        print(f"\n✓ Found {len(json_files)} JSON file(s):")
        for file in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True):
            print(f"  - {file.name}")
    else:
        print("\n⚠ No JSON files found")
    
    # Check for XML files
    xml_files = list(test_results.glob("*.xml"))
    if xml_files:
        print(f"\n✓ Found {len(xml_files)} XML file(s):")
        for file in sorted(xml_files, key=lambda x: x.stat().st_mtime, reverse=True):
            print(f"  - {file.name}")
    else:
        print("\n⚠ No XML files found")
    
    return len(html_reports) > 0

if __name__ == "__main__":
    check_reports()