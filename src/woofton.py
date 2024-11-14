import json


class WoofTonData:
    def __init__(self, filename):
        self.filename = filename
        self.data = self.load_woof_ton_data()

    def load_woof_ton_data(self):
        with open(self.filename, 'r') as f:
            raw_data = json.load(f)

        woof_tons = {}

        for row in raw_data:
            w, t = row
            w = int(w)
            t = float(t)

            woof_tons.setdefault(t, []).append(w)

        data = {}
        for t, woofs in woof_tons.items():
            data[t] = sum(woofs) / len(woofs)

        return data