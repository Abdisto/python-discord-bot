import yaml
from fuzzywuzzy import fuzz
import datetime

class Cache():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}
        self.reload_cache()

    def reload_cache(self):
        with open('cache.yaml', 'r') as file:
            self.data = yaml.safe_load(file) or {}

    # def is_similar(self, query, title, threshold=80):
    #     if query in self.data:
    #         return True
    #     for existing_title in self.data.keys():
    #         if fuzz.ratio(title, existing_title) >= threshold:
    #             return True
    #     return False

    def autocomplete(self):
        with open('cache.yaml', 'r') as file:
            data = yaml.safe_load(file)

        if data is None:
            return []

        sorted_titles = sorted(data.items(), key=lambda item: item[1]['weight'], reverse=True)
        
        titles = []
        for title, details in sorted_titles:
            titles.append(title)
    
        return titles
    
    def check_query(self, query):
        with open('cache.yaml', 'r') as file:
            data = yaml.safe_load(file)

        if data is None:
            return query
        
        if query in data:
            return data[query]['ID']
        
        for title, details in data.items():
            if fuzz.ratio(query, title) >= 80:
                return details['ID']
        return query

    def data_parser(self, title, identifier):
        with open('cache.yaml', 'r') as file:
            data = yaml.safe_load(file)

        if data is None:
            data = {}

        for existing_title, details in data.items():
            if details['ID'] == identifier:
                data[existing_title]['weight'] += 1 # return to '20' when you is min_weight_title
                with open('cache.yaml', 'w') as file:
                    yaml.safe_dump(data, file, default_flow_style=False)
                return

        data[title] = {
            'ID': identifier,
            'weight': 20,   
            # 'last_played':  
        }

        if len(data) >= 25:
            min_weight_title = min(data, key=lambda x: data[x]['weight'])
            data[min_weight_title]['weight'] -= 5
            if data[min_weight_title]['weight'] == 0:
                del data[min_weight_title]

        # Write the updated data back to the YAML file
        with open('cache.yaml', 'w') as file:
            yaml.safe_dump(data, file, default_flow_style=False)