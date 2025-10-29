# alerts_manager.py
import json
import os
import uuid

ALERTS_FILE = "alerts.json"

def load_alerts():
    """Загрузка всех алертов из файла"""
    if not os.path.exists(ALERTS_FILE):
        return []
    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        try:
            alerts = json.load(f)
            # Добавляем ID старым алертам, если их нет
            changed = False
            for alert in alerts:
                if "id" not in alert:
                    alert["id"] = str(uuid.uuid4())
                    changed = True
            # Если добавили ID - сохраняем обратно
            if changed:
                save_alerts(alerts)
            return alerts
        except json.JSONDecodeError:
            return []

def save_alert(alert_data):
    """Сохранить один алерт"""
    alerts = load_alerts()
    alerts.append(alert_data)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2, ensure_ascii=False)

def save_alerts(alerts_list):
    """Перезаписать весь файл alerts.json новым списком"""
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts_list, f, indent=2, ensure_ascii=False)

