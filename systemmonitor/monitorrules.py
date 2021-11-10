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

    def add_rule(self, key_pattern, comparison, threshold, message):
        # If key ends in #attribute then we will do the comparison against that
        # attribute, instead of the value
        attribute = 'value'
        for a in ('type', 'unit', 'latest'):
            if key_pattern.endswith('#' + a):
                attribute = a
                key_pattern = key_pattern[0: len(key_pattern) - len(a) - 1]

        self.rules.append({
            'pattern': re.compile(key_pattern),
            'comparison': comparison,
            'threshold': threshold,
            'message': message,
            'attribute': attribute,
        })

    def check_rules(self, data):
        # Flatten the hierarchical keys
        flat_data = self.flatten_data(data)
        broken_rules = []
        for rule in self.rules:
            attribute = rule['attribute']
            for k, v in flat_data.items():
                rule_match = rule['pattern'].fullmatch(k)
                if rule_match:
                    # Step through all rule thresholds provided (most severe first) - if just one, put into a list
                    rule_thresholds = rule['threshold']
                    if type(rule_thresholds) != tuple and type(rule_thresholds) != list:
                        rule_thresholds = [rule_thresholds]
                    for level, rule_threshold in enumerate(reversed(rule_thresholds)):
                        # If rule threshold is callable, resolve it
                        if callable(rule_threshold):
                            rule_threshold = rule_threshold(flat_data, rule_match.groups())
                        # If comparator is not callable, get it from comparators map
                        comparator = rule['comparison']
                        if not callable(comparator):
                            comparator = self.comparators[rule['comparison']]
                        # Execute rule
                        broken = comparator(v[attribute], rule_threshold)
                        if broken:
                            # Construct message 
                            message = rule['message']
                            if callable(message):
                                message = message(v[attribute], rule_match.groups())
                            else:
                                message = message.replace('{VALUE}', str(v['value']))
                                message = message.replace('{TYPE}', str(v['type']))
                                message = message.replace('{UNIT}', str(v['unit']))
                                if 'latest' in v:
                                    message = message.replace('{LATEST}', str(v['latest']))
                                for i, g in enumerate(rule_match.groups()):
                                    message = message.replace('{' + str(i) + '}', str(g))
                            # Add rule to list of broken rules
                            broken_rules.append({
                                'key': k,
                                'value': v['value'],
                                'type': v['type'],
                                'unit': v['unit'],
                                'comparison': rule['comparison'],
                                'attribute': attribute,
                                'rule_threshold': rule_threshold,
                                'groups': rule_match.groups(),
                                'message': message,
                                'level': (len(rule_thresholds) - level - 1),
                            })
                            if 'latest' in v:
                                broken_rules[-1]['latest'] = v['latest']
                            break
        return broken_rules

    def flatten_data(self, data):            
        flat_data = {}

        if 'type' in data and type(data['type']) == str:
            unit = None
            if 'unit' in data:
                unit = data['unit']
            if 'value' in data:
                return {
                    'value': data['value'],
                    'type': data['type'],
                    'unit': unit,
                }
            elif 'values' in data:
                latest = sorted(list(data['values'].keys()))[-1]
                return {
                    'value': data['values'][latest],
                    'type': data['type'],
                    'unit': unit,
                    'latest': latest,
                }
        else:
            for k, v in data.items():
                sublevel = self.flatten_data(v)
                if 'type' in sublevel and type(sublevel['type']) == str:
                    flat_data[k] = sublevel
                else:
                    for sublevel_k, sublevel_v in sublevel.items():
                        flat_data["{}.{}".format(k, sublevel_k)] = sublevel_v

        return flat_data
