#!/usr/bin/env python3
import json
import sys
from datetime import datetime
import html

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grype Vulnerability Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .vulnerability-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .vulnerability-table th,
        .vulnerability-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .vulnerability-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .severity-high {{
            color: #dc3545;
            font-weight: bold;
        }}
        .severity-medium {{
            color: #ffc107;
            font-weight: bold;
        }}
        .severity-low {{
            color: #28a745;
            font-weight: bold;
        }}
        .details {{
            display: none;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .expand-btn {{
            background: none;
            border: none;
            color: #007bff;
            cursor: pointer;
            padding: 0;
            font-size: inherit;
            text-decoration: underline;
        }}
        .filter-controls {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .filter-controls select, .filter-controls input {{
            margin-right: 10px;
            padding: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header">
            <h1>Grype Vulnerability Report</h1>
            <p>Generated: {timestamp}</p>
            <p style="color: rgb(13, 64, 180)">Generated by <a href="https://github.com/anchore/grype" style="color: inherit">Grype</a> version <a href="https://github.com/anchore/grype/releases/tag/v{grype_version}" style="color: inherit">{grype_version}</a> from <b><a href="https://anchore.com/">Anchore</a></b></p>
        </div>

        <div class="filter-controls">
            <label>Severity Filter:
                <select id="severityFilter">
                    <option value="all">All</option>
                    <option value="Critical">Critical</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                </select>
            </label>
            <label>Package Search:
                <input type="text" id="packageFilter" placeholder="Filter by package name...">
            </label>
        </div>

        <div class="summary" id="summary">
            <!-- Summary will be populated by JavaScript -->
        </div>

        <table class="vulnerability-table" id="vulnTable">
            <thead>
                <tr>
                    <th>Package</th>
                    <th>Version</th>
                    <th>Vulnerability ID</th>
                    <th>Severity</th>
                    <th>Fixed Version</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <!-- Table content will be populated by JavaScript -->
            </tbody>
        </table>
    </div>

    <script>
        // Embed the Grype scan results
        const grypeData = {json_data};

        function getSeverityClass(severity) {{
            switch (severity?.toLowerCase()) {{
                case 'critical':
                case 'high':
                    return 'severity-high';
                case 'medium':
                    return 'severity-medium';
                case 'low':
                    return 'severity-low';
                default:
                    return '';
            }}
        }}

        function toggleDetails(id) {{
            const detailsElement = document.getElementById(`details-${{id}}`);
            if (detailsElement.style.display === 'none') {{
                detailsElement.style.display = 'block';
            }} else {{
                detailsElement.style.display = 'none';
            }}
        }}

        function updateSummary() {{
            const summary = document.getElementById('summary');
            const matches = grypeData.matches;
            
            const severityCounts = matches.reduce((acc, match) => {{
                const severity = match.vulnerability.severity;
                acc[severity] = (acc[severity] || 0) + 1;
                return acc;
            }}, {{}});

            const summaryHTML = `
                <h2>Summary</h2>
                <p>Target: ${{grypeData.source.target.userInput}}</p>
                <p>Total Vulnerabilities: ${{matches.length}}</p>
                ${{Object.entries(severityCounts)
                    .map(([severity, count]) => 
                        `<p class="${{getSeverityClass(severity)}}">${{severity}}: ${{count}}</p>`
                    ).join('')}}
            `;
            
            summary.innerHTML = summaryHTML;
        }}

        function populateTable(filtered = false) {{
            const tbody = document.querySelector('#vulnTable tbody');
            const severityFilter = document.getElementById('severityFilter').value;
            const packageFilter = document.getElementById('packageFilter').value.toLowerCase();
            
            let matches = grypeData.matches;
            if (filtered) {{
                matches = matches.filter(match => {{
                    const severityMatch = severityFilter === 'all' || 
                        match.vulnerability.severity === severityFilter;
                    const packageMatch = match.artifact.name.toLowerCase()
                        .includes(packageFilter);
                    return severityMatch && packageMatch;
                }});
            }}

            tbody.innerHTML = matches.map((match, index) => `
                <tr>
                    <td>${{match.artifact.name}}</td>
                    <td>${{match.artifact.version}}</td>
                    <td>${{match.vulnerability.id}}</td>
                    <td class="${{getSeverityClass(match.vulnerability.severity)}}">
                        ${{match.vulnerability.severity}}
                    </td>
                    <td>${{match.vulnerability.fix?.versions?.join(', ') || 'No fix available'}}</td>
                    <td>
                        <button class="expand-btn" onclick="toggleDetails('${{index}}')">
                            Details
                        </button>
                        <div id="details-${{index}}" class="details">
                            <h4>Related Vulnerabilities:</h4>
                            ${{match.relatedVulnerabilities.map(rv => `
                                <p><strong>Description:</strong></p>
                                <p>${{rv.description || 'No description available'}}</p>
                                <p><strong>URLs:</strong></p>
                                <ul>
                                    ${{rv.urls.map(url => `<li><a href="${{url}}" target="_blank">${{url}}</a></li>`).join('')}}
                                </ul>
                            `).join('')}}
                        </div>
                    </td>
                </tr>
            `).join('');
        }}

        // Initialize the report
        updateSummary();
        populateTable();

        // Add event listeners for filters
        document.getElementById('severityFilter').addEventListener('change', () => populateTable(true));
        document.getElementById('packageFilter').addEventListener('input', () => populateTable(true));
    </script>
</body>
</html>
'''

def main():
    # Read JSON from stdin
    try:
        grype_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    filename = f"grype_{timestamp}.html"

    # Create the HTML report
    report = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        json_data=json.dumps(grype_data),
        grype_version=grype_data['descriptor']['version']
    )

    # Write the report to file
    try:
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Report generated: {filename}")
    except IOError as e:
        print(f"Error writing report: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
