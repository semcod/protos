import requests
import uuid

URL = "http://localhost:19090/commands/search/index"

entries = [
    {
        "id": str(uuid.uuid4()),
        "title": "Jak zmigrować system legacy?",
        "category": "MIGRACJA",
        "content": "Użyj wzorca Strangler Fig i osadź nowy UI w iframe.",
        "metadata": {"author": "Antigravity"}
    },
    {
        "id": str(uuid.uuid4()),
        "title": "CQRS i Event Sourcing w Pythonie",
        "category": "ARCHITEKTURA",
        "content": "Event Store jako źródło prawdy, Read Model w SQLite FTS5.",
        "metadata": {"author": "Antigravity"}
    }
]

for entry in entries:
    r = requests.post(URL, json=entry)
    print(f"Indexed: {entry['title']} - {r.status_code}")

print("\nVerifying search...")
search_url = "http://localhost:19090/queries/search?q=Strangler"
r = requests.get(search_url)
print(f"Search result: {r.json()}")
