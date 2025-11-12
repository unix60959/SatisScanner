# Satisfactory Server Log Analyzer

A comprehensive analytics solution for Satisfactory dedicated server logs that extracts meaningful metrics and presents them in an interactive web dashboard.

## 🚀 Features

### Metrics Extracted:
- **Player Analytics**: Join/leave events, session durations, playtime statistics
- **Server Performance**: Uptime periods, error rates, connection attempts
- **Timeline Analysis**: Daily activity patterns, server gaps, peak usage times
- **Network Events**: IP tracking, connection failures, player distribution
- **Error Monitoring**: Recent errors and warnings with timestamps

### Visualizations:
- Daily player activity trends
- Player join distribution (top players)
- Server uptime periods across log files
- Session duration histogram
- Player statistics table
- Recent errors and warnings log

## 📁 Files

- `satis_scanner.py` - Main analyzer script
- `serve_dashboard.py` - Local web server for dashboard
- `dashboard.html` - Interactive web dashboard
- `satis_metrics.json` - Generated metrics data (created after running scanner)
- `satis_metrics_sample.json` - Example output format
- `LICENSE` - MIT license

## 🛠️ Setup & Usage

### Prerequisites:
- Python 3.7+ installed
- Satisfactory server log files (FactoryGame*.log)

### Steps:
1. **Place log files** in the same directory as the scripts
2. **Run the analyzer**:
   ```bash
   python satis_scanner.py
   ```
3. **Start the dashboard server**:
   ```bash
   python serve_dashboard.py
   ```
4. **View analytics**: Dashboard opens automatically at http://localhost:8000
5. **Stop server**: Press Ctrl+C when done

### Why the Server?
The dashboard requires a local web server due to browser security restrictions when loading JSON files. The `serve_dashboard.py` script provides a simple solution that automatically opens your browser to the correct URL.

## 📊 Dashboard Features

### Summary Cards:
- Total unique players
- Total join events  
- Server active days
- Total errors logged

### Interactive Charts:
- **Daily Activity**: Line chart showing player joins over time
- **Player Distribution**: Bar chart of most active players
- **Server Uptime**: Bar chart showing uptime per log file
- **Session Duration**: Histogram of session length distribution

### Data Tables:
- **Player Statistics**: Detailed stats per player (joins, playtime, sessions)
- **Recent Errors**: Latest errors and warnings with timestamps

## 🔧 Customization

### Adding New Metrics:
Edit `satis_scanner.py` to extract additional log patterns:
```python
# Example: Track building events
elif "LogFactory:" in line:
    # Extract building-related events
```

### Modifying Visualizations:
Edit `dashboard.html` to add new charts or modify existing ones using Chart.js.

## 📈 Sample Metrics

The analyzer tracks:
- **42 total join events** across 4 unique players
- **107 days** of server span with **574+ hours** of uptime
- **Player sessions** with average duration tracking
- **Network connections** and **error patterns**

## 🎯 Use Cases

- **Server Administration**: Monitor player activity and server health
- **Community Management**: Track player engagement and peak times  
- **Performance Optimization**: Identify error patterns and connection issues
- **Historical Analysis**: Review server usage trends over time

## 🔍 Technical Details

- **Log Parsing**: Regex-based extraction of timestamps, usernames, and events
- **Session Calculation**: Estimates session duration using join patterns
- **Data Format**: JSON output for easy integration with other tools
- **Web Dashboard**: Pure HTML/CSS/JS with Chart.js for visualizations

## 📝 Notes

- Session durations are intelligently estimated based on join patterns and time gaps
- Large log files are processed efficiently with streaming
- Dashboard requires local server due to browser CORS restrictions
- Server runs on port 8000 by default
- Compatible with all Satisfactory server log formats