import requests
import time
import datetime

from rich.live import Live
from rich.table import Table

class Node:
    """Nods, kas satur datus par laikapstākļiem un norādi uz nākamo un iepriekšējo nodu."""
    def __init__(self, value):
        self.value = value
        self.next: None | Node = None

class Tunnel:
    """Datu struktūra, kurai ir piekļuve sākumam un beigām."""
    __SIZE: int = 7 # (private) nedēļas dienu skaits
    def __init__(self):
        self.size: int = 0
        self.head: None | Node = None

    def add(self, data):
        """Pievieno jaunu nodu beigās un izdzēs sākuma nodu, lai nebūtu pārpildīšanas."""
        new_node = Node(data)
        if self.head is None: # ja tunelis ir tukšs
            self.head = new_node
            self.size += 1
            return
        elif self.size == self.__SIZE: # ja tunelis ir pilns
            self.head = self.head.next
            iter_node = self.head
            while iter_node.next is not None:
                iter_node = iter_node.next
            iter_node.next = new_node
            return
        else: # ja tunelis ir daļēji pilns
            iter_node = self.head
            while iter_node.next is not None:
                iter_node = iter_node.next
            iter_node.next = new_node
            self.size += 1

def test():
    """Datu simulācija datu struktūras testiem, pirms API pieslēgšanas"""
    temporary_data = ["10 C", "12 C", "14 C", "16 C", "18 C", "20 C", "22 C", "24 C"]
    
    for data in temporary_data:
        weather_store.add(data)
        iter_node = weather_store.head
        while iter_node is not None:
            print(iter_node.value, "COUNTER")
            iter_node = iter_node.next
        print("----")

def main(API_URL: str):
    """prod"""

    table = Table(title="Laikapstākļi Ķīpsalas studentu pilsētiņā")
    def update_data() -> None:
        """Atjaunina datus no API un saglabā tos datu struktūrā."""
        global weather_store
        response = requests.get(API_URL)
        if response.ok:
            response = response.json()
        else:
            raise Exception("API pieprasījums neizdevās.")

        criteria_names = ["Vidējā temp.", "Nokrišņu kopā", "Vid. spiediens"]
        
        for day in range(7):
            day_data = {
                "Vidējā temp.": 0.0,
                "Nokrišņu kopā": 0.0,
                "Vid. spiediens": 0.0
            }
            for hour in range(24):
                day_data["Vidējā temp."] += response["hourly"]["temperature_2m"][day*24 + hour]
                day_data["Nokrišņu kopā"] += response["hourly"]["rain"][day*24 + hour]
                day_data["Vid. spiediens"] += response["hourly"]["surface_pressure"][day*24 + hour] * 0.75 # konvertē hPa -> mmHg
                if hour == 23:
                    day_data["Vidējā temp."] /= 24
                    day_data["Vid. spiediens"] /= 24
                    weather_store.add(day_data)
        
        table.add_column("Mērvienība.", no_wrap=True, style="cyan")
        table.add_column("Šodien", no_wrap=True, justify="right", style="magenta")
        table.add_column("Rīt", no_wrap=True, justify="right", style="magenta")
        date = datetime.datetime.today() + datetime.timedelta(days=1)
        for day in range(5):
            """data format: dd.mm.yy"""
            date = date + datetime.timedelta(days=1)
            table.add_column(date.strftime("%d.%m.%y"), no_wrap=True, justify="right", style="magenta")

        iter_node = weather_store.head
        criteria_measures = [" °C", " mm", " mmHg"]
        for index in range(3):
            criteria_data: tuple = tuple()
            for day in range(7):
                current_data = str(
                    round(
                        iter_node.value[criteria_names[index]]
                    )
                ) + criteria_measures[index]
                criteria_data += (current_data,) 
                iter_node = iter_node.next
            table.add_row(criteria_names[index], *criteria_data)
            iter_node = weather_store.head
        
    with Live(table, refresh_per_second=1) as live:
        while True:
            update_data()
            time.sleep(60*60)
            live.update(table)

if __name__ == "__main__":
    weather_store = Tunnel()
    # test()
    main("https://api.open-meteo.com/v1/forecast\
?latitude=56.9530072\
&longitude=24.0814191\
&hourly=temperature_2m,rain,surface_pressure\
&timezone=auto")