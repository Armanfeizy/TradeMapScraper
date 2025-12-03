import json


class Country:

    def __init__(self, name: str, code: str):
        self.name = name
        self.code = code

    @classmethod
    def loader(cls, json_path: str) -> list['Country']:
        with open(json_path, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        return [cls(name=c["title"], code=c["value"]) for c in countries_data]
