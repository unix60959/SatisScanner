#!/usr/bin/env python3
import re
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import glob

class SatisfactoryLogAnalyzer:
    def __init__(self, log_directory="."):
        self.log_directory = log_directory
        self.metrics = {
            "summary": {},
            "players": {},
            "sessions": [],
            "server_events": [],
            "timeline": {},
            "performance": {},
            "errors": []
        }
    
    def parse_timestamp(self, timestamp_str):
        """Parse log timestamp to datetime object"""
        try:
            # Format: 2025.07.27-11.10.42:986
            return datetime.strptime(timestamp_str, "%Y.%m.%d-%H.%M.%S:%f")
        except:
            try:
                return datetime.strptime(timestamp_str[:19], "%Y.%m.%d-%H.%M.%S")
            except:
                return None
    
    def analyze_log_file(self, log_path):
        """Analyze a single log file"""
        file_metrics = {
            "joins": [],
            "leaves": [],
            "errors": [],
            "start_time": None,
            "end_time": None,
            "connections": []
        }
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    # Extract timestamp
                    timestamp_match = re.search(r'\[([^\]]+)\]', line)
                    if not timestamp_match:
                        continue
                    
                    timestamp_str = timestamp_match.group(1)
                    timestamp = self.parse_timestamp(timestamp_str)
                    
                    if not timestamp:
                        continue
                    
                    # Track file time range
                    if not file_metrics["start_time"] or timestamp < file_metrics["start_time"]:
                        file_metrics["start_time"] = timestamp
                    if not file_metrics["end_time"] or timestamp > file_metrics["end_time"]:
                        file_metrics["end_time"] = timestamp
                    
                    # Player joins
                    if "LogNet: Join succeeded:" in line:
                        username_match = re.search(r'Join succeeded: (.+)', line)
                        if username_match:
                            username = username_match.group(1).strip()
                            file_metrics["joins"].append({
                                "timestamp": timestamp.isoformat(),
                                "username": username,
                                "file": os.path.basename(log_path)
                            })
                    
                    # Connection attempts
                    elif "NotifyAcceptingConnection accepted from:" in line:
                        ip_match = re.search(r'from: \[([^\]]+)\]', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            file_metrics["connections"].append({
                                "timestamp": timestamp.isoformat(),
                                "ip": ip,
                                "type": "connection_attempt"
                            })
                    
                    # Errors and warnings
                    elif any(level in line for level in ["Error:", "Warning:", "LogNet: UNetConnection::Close"]):
                        file_metrics["errors"].append({
                            "timestamp": timestamp.isoformat(),
                            "level": "Error" if "Error:" in line else "Warning",
                            "message": line.strip()[:200],
                            "file": os.path.basename(log_path)
                        })
        
        except Exception as e:
            print(f"Error analyzing {log_path}: {e}")
        
        return file_metrics
    
    def calculate_sessions(self, all_joins):
        """Calculate player session durations and patterns"""
        sessions = []
        player_sessions = defaultdict(list)
        
        # Group joins by player
        for join in all_joins:
            player_sessions[join["username"]].append(join)
        
        # Calculate session durations based on join patterns
        for username, joins in player_sessions.items():
            joins.sort(key=lambda x: x["timestamp"])
            
            for i, join in enumerate(joins):
                session_start = datetime.fromisoformat(join["timestamp"])
                
                # Estimate session end based on next join or reasonable defaults
                if i + 1 < len(joins):
                    next_join = datetime.fromisoformat(joins[i + 1]["timestamp"])
                    time_gap = (next_join - session_start).total_seconds() / 60
                    
                    # If next join is within 6 hours, assume session lasted until then
                    if 0 < time_gap <= 360:  # 6 hours and positive gap
                        duration_minutes = max(15, time_gap - 5)  # Minimum 15min session
                        session_end = session_start + timedelta(minutes=duration_minutes)
                    else:
                        # Long gap or negative gap - assume typical session length
                        duration_minutes = 60  # 1 hour default
                        session_end = session_start + timedelta(minutes=duration_minutes)
                else:
                    # Last session - use reasonable default
                    duration_minutes = 45  # 45 minutes for final session
                    session_end = session_start + timedelta(minutes=duration_minutes)
                
                sessions.append({
                    "username": username,
                    "start": session_start.isoformat(),
                    "end": session_end.isoformat(),
                    "duration_minutes": duration_minutes,
                    "date": session_start.date().isoformat()
                })
        
        return sessions
    
    def analyze_all_logs(self):
        """Analyze all log files in directory"""
        log_files = glob.glob(os.path.join(self.log_directory, "FactoryGame*.log"))
        
        all_joins = []
        all_errors = []
        all_connections = []
        server_periods = []
        logging_gaps = []
        
        for log_file in sorted(log_files):
            print(f"Analyzing {os.path.basename(log_file)}...")
            file_metrics = self.analyze_log_file(log_file)
            
            if file_metrics["start_time"] and file_metrics["end_time"]:
                server_periods.append({
                    "file": os.path.basename(log_file),
                    "start": file_metrics["start_time"].isoformat(),
                    "end": file_metrics["end_time"].isoformat(),
                    "duration_hours": (file_metrics["end_time"] - file_metrics["start_time"]).total_seconds() / 3600
                })
            
            all_joins.extend(file_metrics["joins"])
            all_errors.extend(file_metrics["errors"])
            all_connections.extend(file_metrics["connections"])
        
        # Calculate gaps between log periods
        server_periods.sort(key=lambda x: x['start'])
        for i in range(len(server_periods) - 1):
            current_end = datetime.fromisoformat(server_periods[i]['end'])
            next_start = datetime.fromisoformat(server_periods[i + 1]['start'])
            gap_duration = (next_start - current_end).total_seconds() / 3600
            
            if gap_duration > 1:  # Only track gaps > 1 hour
                logging_gaps.append({
                    'start': current_end.isoformat(),
                    'end': next_start.isoformat(),
                    'duration_hours': gap_duration,
                    'duration_days': gap_duration / 24,
                    'after_file': server_periods[i]['file'],
                    'before_file': server_periods[i + 1]['file']
                })
        
        # Calculate comprehensive metrics
        sessions = self.calculate_sessions(all_joins)
        unique_players = set(join["username"] for join in all_joins)
        
        # Player statistics
        player_stats = {}
        for username in unique_players:
            user_joins = [j for j in all_joins if j["username"] == username]
            user_sessions = [s for s in sessions if s["username"] == username]
            session_durations = [s["duration_minutes"] for s in user_sessions]
            
            player_stats[username] = {
                "total_joins": len(user_joins),
                "total_playtime_hours": sum(session_durations) / 60,
                "first_seen": min(j["timestamp"] for j in user_joins),
                "last_seen": max(j["timestamp"] for j in user_joins),
                "avg_session_hours": (sum(session_durations) / len(session_durations) / 60) if session_durations else 0,
                "min_session_hours": (min(session_durations) / 60) if session_durations else 0,
                "max_session_hours": (max(session_durations) / 60) if session_durations else 0
            }
        
        # Timeline analysis
        if all_joins:
            first_activity = min(datetime.fromisoformat(j["timestamp"]) for j in all_joins)
            last_activity = max(datetime.fromisoformat(j["timestamp"]) for j in all_joins)
            total_span_days = (last_activity - first_activity).days
        else:
            first_activity = last_activity = None
            total_span_days = 0
        
        # Daily activity
        daily_activity = defaultdict(int)
        for join in all_joins:
            date = datetime.fromisoformat(join["timestamp"]).date().isoformat()
            daily_activity[date] += 1
        
        # Compile final metrics
        self.metrics = {
            "summary": {
                "total_log_files": len(log_files),
                "total_unique_players": len(unique_players),
                "total_join_events": len(all_joins),
                "total_sessions": len(sessions),
                "total_errors": len(all_errors),
                "total_connections": len(all_connections),
                "total_logging_gaps": len(logging_gaps),
                "longest_gap_hours": max([gap['duration_hours'] for gap in logging_gaps], default=0),
                "analysis_date": datetime.now().isoformat(),
                "server_span_days": total_span_days,
                "first_activity": first_activity.isoformat() if first_activity else None,
                "last_activity": last_activity.isoformat() if last_activity else None
            },
            "players": player_stats,
            "sessions": sessions,
            "server_periods": server_periods,
            "logging_gaps": logging_gaps,
            "daily_activity": dict(daily_activity),
            "errors": all_errors[-100:],  # Last 100 errors
            "recent_connections": all_connections[-50:]  # Last 50 connections
        }
        
        return self.metrics
    
    def save_metrics(self, output_file="satis_metrics.json"):
        """Save metrics to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        print(f"Metrics saved to {output_file}")

def main():
    analyzer = SatisfactoryLogAnalyzer(".")
    metrics = analyzer.analyze_all_logs()
    analyzer.save_metrics()
    
    # Print summary
    print(f"\n=== Satisfactory Server Analysis ===")
    print(f"Log files analyzed: {metrics['summary']['total_log_files']}")
    print(f"Unique players: {metrics['summary']['total_unique_players']}")
    print(f"Total join events: {metrics['summary']['total_join_events']}")
    print(f"Server active span: {metrics['summary']['server_span_days']} days")
    print(f"Total errors logged: {metrics['summary']['total_errors']}")

if __name__ == "__main__":
    main()