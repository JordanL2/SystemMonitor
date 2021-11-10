#!/usr/bin/python3

import re


class MonitorRules():

    rules = []
    comparators = {
        '<': lambda v1, v2: v1 < v2,
        '<=': lambda v1, v2: v1 <= v2,
        '>=': lambda v1, v2: v1 >= v2,
        '>': lambda v1, v2: v1 > v2,
        '==': lambda v1, v2: v1 == v2,
        '!=': lambda v1, v2: v1 != v2,
    }

    def __init__(self):
        pass

    def import_rules(self, rules):
        for rule in rules:
            self.add_rule(rule[0], rule[1], rule[2], rule[3])

    def add_rule(self, key_pattern, comparison, value, message):
        self.rules.append({
            'pattern': re.compile(key_pattern),
            'comparison': comparison,
            'value': value,
            'message': message,
        })

    def check_rules(self, data):
        flat_data = self.flatten_data(data)
        broken_rules = []
        for rule in self.rules:
            for k, v in flat_data.items():
                rule_match = rule['pattern'].fullmatch(k)
                if rule_match:
                    rule_values = rule['value']
                    if type(rule_values) != tuple and type(rule_values) != list:
                        rule_values = [rule_values]
                    for level, rule_value in enumerate(reversed(rule_values)):
                        broken = self.comparators[rule['comparison']](v[0], rule_value)
                        if broken:
                            message = rule['message']
                            if callable(message):
                                message = message(v[0], rule_match.groups())
                            else:
                                message = message.replace('{VALUE}', str(v[0]))
                                message = message.replace('{UNIT}', str(v[2]))
                                for i, g in enumerate(rule_match.groups()):
                                    message = message.replace('{' + str(i) + '}', str(g))
                            broken_rules.append({
                                'key': k,
                                'value': v[0],
                                'type': v[1],
                                'unit': v[2],
                                'comparison': rule['comparison'],
                                'comparison_value': rule_value,
                                'groups': rule_match.groups(),
                                'message': message,
                                'level': (len(rule_values) - level - 1),
                            })
                            break
        return broken_rules

    def flatten_data(self, data):            
        flat_data = {}

        if 'type' in data and type(data['type']) == str:
            unit = None
            if 'unit' in data:
                unit = data['unit']
            if 'value' in data:
                return (data['value'], data['type'], unit)
            elif 'values' in data:
                latest = sorted(list(data['values'].keys()))[-1]
                return (data['values'][latest], data['type'], unit)
        else:
            for k, v in data.items():
                sublevel = self.flatten_data(v)
                if type(sublevel) == dict:
                    for sublevel_k, sublevel_v in sublevel.items():
                        flat_data["{}.{}".format(k, sublevel_k)] = sublevel_v
                else:
                    flat_data[k] = sublevel

        return flat_data
