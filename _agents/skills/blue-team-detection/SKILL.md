---
skill_name: blue-team-detection
description: Blue team detection - SIEM rules, threat hunting, IOC management, EDR, incident response
category: [security, advanced]
version: 1.0.0
---

# Blue Team Detection & Response

## SIEM Rule Development

```yaml
# YARA-like rule for Splunk
title: Suspicious PowerShell Execution
index: windows
source: WinEventLog:Security
EventCode: 4104

# PowerShell Script Block Logging
powershell.exe
| search ScriptBlockText IN (
    "*IEX*", "*Invoke-Expression*", "*DownloadString*",
    "*WinRM*", "*Start-Service*"
)
| stats count by ComputerName, UserName

---

# Sigma rule for multiple SIEM platforms
title: Unusual Outbound Connection
logsource:
  product: windows
  service: process_creation
detection:
  selection:
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
    CommandLine|contains:
      - 'curl '
      - 'wget '
      - 'certutil '
  condition: selection
falsepositives:
  - Normal administrative activity
level: medium

---

# Splunk search for lateral movement
index=main sourcetype=WinEventLog:Security EventCode=4624
dest_user!="SYSTEM" dest_user!="LOCAL SERVICE"
| search LogonType=3 dest!=src
| stats count by src, dest, dest_user
| where count > 5
```

## Threat Hunting Queries

```sql
-- SQL query for suspicious database access
SELECT
  user_name,
  source_ip,
  query_type,
  table_accessed,
  COUNT(*) as access_count,
  DATETIME(MAX(access_time)) as latest_access
FROM audit_log
WHERE query_type IN ('SELECT', 'DELETE', 'UPDATE')
  AND table_accessed IN ('users', 'passwords', 'credit_cards')
  AND access_time > DATETIME('now', '-1 hour')
GROUP BY user_name, source_ip
HAVING COUNT(*) > 100
ORDER BY access_count DESC;

-- Find data exfiltration patterns
SELECT
  source_ip,
  destination_ip,
  SUM(bytes_transferred) as total_bytes,
  COUNT(*) as connection_count
FROM network_traffic
WHERE timestamp > DATETIME('now', '-24 hours')
  AND bytes_transferred > 1000000
  AND destination_ip NOT IN (SELECT trusted_ips FROM whitelist)
GROUP BY source_ip, destination_ip
HAVING total_bytes > 10000000;
```

## IOC Management

```python
# ThreatIntel IOC collector and matcher
class IOCManager:
    def __init__(self):
        self.iocs = {
            'ip': set(),
            'domain': set(),
            'hash': set(),
            'url': set()
        }
        self.whitelist = set()

    def load_iocs_from_feeds(self):
        """Load IOCs from threat feeds"""
        feeds = [
            'https://otx.alienvault.com/api/v1/pulses/subscribed',
            'https://feeds.abuse.ch/feeds/',
            'https://ctifeeds.alienvault.com/feeds/'
        ]
        for feed_url in feeds:
            iocs = self.fetch_iocs(feed_url)
            self.add_iocs(iocs)

    def add_iocs(self, iocs):
        """Add IOCs to tracking"""
        for ioc in iocs:
            ioc_type = self.classify_ioc(ioc)
            if ioc_type:
                self.iocs[ioc_type].add(ioc)

    def classify_ioc(self, value):
        """Classify IOC type"""
        import re
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', value):
            return 'ip'
        elif re.match(r'^[a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64}$', value):
            return 'hash'
        elif re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', value):
            return 'domain'
        elif re.match(r'^https?://', value):
            return 'url'
        return None

    def match_against_logs(self, log_event):
        """Check if log event contains IOC"""
        matches = []

        for ioc_type, ioc_list in self.iocs.items():
            for ioc in ioc_list:
                if ioc in str(log_event):
                    if ioc not in self.whitelist:
                        matches.append({
                            'type': ioc_type,
                            'value': ioc,
                            'event': log_event
                        })

        return matches

# Usage
ioc_mgr = IOCManager()
ioc_mgr.load_iocs_from_feeds()
matches = ioc_mgr.match_against_logs(firewall_log)
if matches:
    alert_security_team(matches)
```

## EDR Detection Rules

```python
# Endpoint Detection & Response rules
class EDRDetectionEngine:
    def __init__(self):
        self.rules = []

    def detect_living_off_the_land(self, process):
        """Detect abuse of legitimate tools"""
        suspicious_args = [
            'powershell -Command',
            'cmd /c start',
            'wmic process call',
            'mshta.exe',
            'certutil -urlcache'
        ]

        for arg_pattern in suspicious_args:
            if arg_pattern in process['commandline']:
                return {
                    'severity': 'high',
                    'rule': 'Living off the land',
                    'process': process
                }

    def detect_process_injection(self, process):
        """Detect code injection attempts"""
        api_calls = process.get('api_calls', [])
        injection_apis = [
            'CreateRemoteThread',
            'VirtualAllocEx',
            'WriteProcessMemory',
            'SetWindowsHookEx',
            'CreateFileMapping'
        ]

        count = sum(1 for api in api_calls if any(
            inj_api in api for inj_api in injection_apis
        ))

        if count >= 3:
            return {
                'severity': 'critical',
                'rule': 'Code injection detected',
                'apis': [a for a in api_calls if any(
                    inj_api in a for inj_api in injection_apis
                )]
            }

    def detect_lateral_movement(self, network_activity):
        """Detect lateral movement indicators"""
        suspicious_ports = [135, 445, 3389, 5985, 5986]  # WMI, SMB, RDP, WinRM
        internal_ips = self.get_internal_network()

        for activity in network_activity:
            dest_ip = activity['destination_ip']
            dest_port = activity['destination_port']

            # Internal connection on high-risk port
            if (dest_ip in internal_ips and
                dest_port in suspicious_ports and
                activity['connection_count'] > 10):
                return {
                    'severity': 'high',
                    'rule': 'Lateral movement detected',
                    'target': dest_ip
                }

    def detect_credential_access(self, process):
        """Detect credential theft attempts"""
        file_access = process.get('file_access', [])
        credential_files = [
            'NTDS.DIT',
            'SAM',
            'SYSTEM',
            '.ssh',
            '.aws/credentials',
            'lsass.exe'
        ]

        for file_path in file_access:
            for cred_file in credential_files:
                if cred_file in file_path:
                    return {
                        'severity': 'critical',
                        'rule': 'Credential access attempted',
                        'file': file_path
                    }
```

## Incident Response Playbook

```yaml
Incident Response Playbook - Potential Data Breach

1. DETECTION & ANALYSIS
   - Confirm incident is legitimate (not false positive)
   - Identify initial access vector
   - Determine scope and impact
   - Timeline: 0-1 hour

2. CONTAINMENT (SHORT-TERM)
   - Isolate affected systems (network segmentation)
   - Disable compromised accounts
   - Block known attacker IPs
   - Timeline: 1-4 hours

3. INVESTIGATION
   - Preserve evidence (memory dump, logs)
   - Perform forensic analysis
   - Determine dwell time (how long attacker present)
   - Identify all compromised systems
   - Timeline: 4-72 hours

4. ERADICATION
   - Remove malware/backdoors
   - Patch exploited vulnerabilities
   - Update firewall/WAF rules
   - Reset credentials for affected accounts
   - Timeline: 24-7 days

5. RECOVERY
   - Restore systems from clean backups
   - Monitor for re-infection
   - Implement additional controls
   - Timeline: 7-30 days

6. POST-INCIDENT
   - Post-mortem analysis
   - Update policies/procedures
   - Security training for staff
   - Share IOCs with threat intel community
```

## Hunting Techniques

```python
# Behavioral anomaly detection
class AnomalyDetector:
    def __init__(self):
        self.baseline = {}  # Normal behavior patterns

    def establish_baseline(self, historical_logs):
        """Learn normal behavior"""
        for user, events in historical_logs.items():
            self.baseline[user] = {
                'normal_login_hours': self.get_login_hours(events),
                'normal_source_ips': self.get_source_ips(events),
                'normal_applications': self.get_apps(events),
                'normal_failure_rate': self.get_failure_rate(events)
            }

    def detect_anomaly(self, user, event):
        """Detect deviations from baseline"""
        if user not in self.baseline:
            return None

        anomalies = []

        # Login outside normal hours
        if event['hour'] not in self.baseline[user]['normal_login_hours']:
            anomalies.append('Unusual login time')

        # Login from new IP
        if event['source_ip'] not in self.baseline[user]['normal_source_ips']:
            anomalies.append('New source IP')

        # Unusual application usage
        if event['app'] not in self.baseline[user]['normal_applications']:
            anomalies.append('Unusual application')

        return anomalies if anomalies else None
```

## Metrics & KPIs

```
Detection Metrics:
- MTTD (Mean Time To Detect): 4 hours (industry avg: 206 days)
- Alert Quality: Precision (reduce false positives)
- Alert Accuracy: Recall (catch all threats)
- Tuning Efficiency: Time to tune false positives

Response Metrics:
- MTTR (Mean Time To Respond): 1 hour
- MTTR to Containment: 4 hours
- MTTR to Eradication: 24 hours
- Time to Recover: 7 days

Key Targets:
- MTTD < 24 hours
- False positive rate < 5%
- Alert response time < 1 hour
```

## Key Takeaways

- **SIEM**: Aggregate logs, create detection rules
- **Threat hunting**: Proactive search for indicators
- **IOC management**: Track and match threat intelligence
- **EDR**: Monitor endpoints for suspicious behavior
- **Playbooks**: Document response procedures
- **Metrics**: MTTD and MTTR are critical KPIs
