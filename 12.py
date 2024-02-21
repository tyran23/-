import sys, math
import requests
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

lat_step, lon_step = 0.008, 0.02
coord_to_geo_x, coord_to_geo_y = 0.0000428, 0.0000428


def screen_to_geo(pos, longitude, lattitude, z):
    dy = 225 - pos[1]
    dx = pos[0] - 300
    lx = longitude + dx * coord_to_geo_x * 2 ** (15 - z)
    ly = lattitude + dy * coord_to_geo_y * math.cos(math.radians(lattitude)) * 2 ** (15 - z)

    return round(lx, 6), round(ly, 6)


def get_coordinates(toponym_to_find):
    responce = requests.get(
        f"https://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&format=json&geocode={toponym_to_find}")

    try:
        post_idx = \
            responce.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"][
                "GeocoderMetaData"]["Address"]["postal_code"]
    except Exception:
        post_idx = ""

    return \
        responce.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"][
            "Point"][
            "pos"].split(), \
        responce.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"][
            "GeocoderMetaData"]["Address"]["formatted"], post_idx


class MyWidget(QMainWindow):
    def __init__(self):
        self.lat, self.lon = float(input("Lat: ")), float(input("Lon: "))
        self.z = int(input("Введите уровень масшабирования: "))

        super().__init__()
        uic.loadUi('UI.ui', self)
        self.pushButton.clicked.connect(self.change_perspective)
        self.pushButton_2.clicked.connect(self.search)
        self.pushButton_3.clicked.connect(self.erase)
        self.checkBox.stateChanged.connect(self.search)

        self.image = None
        self.perspectives = ["map", "sat", "sat,skl"]
        self.current_perspective = 0
        self.params = ""
        self.update_map()

    def update_map(self):
        response = requests.get(
            f"https://static-maps.yandex.ru/1.x/?ll={self.lat},{self.lon}&z={self.z}&l={self.perspectives[self.current_perspective]}{self.params}")

        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)

        self.image = QPixmap("map.png").scaled(681, 441)
        self.label.setPixmap(self.image)

    def mousePressEvent(self, event):
        try:
            QApplication.focusWidget().clearFocus()
            print(event.pos(), event.button())
            if event.button() == Qt.LeftButton:
                self.lon, self.lat = screen_to_geo([event.x(), event.y()], self.lon, self.lat, self.z)
                print(self.lat, self.lon)
                self.lineEdit.setText(f"{self.lat},{self.lon}")
                self.search()
                self.update_map()
            elif event.button() == Qt.RightButton:
                try:
                    responce = requests.get(
                        f"https://search-maps.yandex.ru/v1/?apikey=dda3ddba-c9ea-4ead-9010-f43fbc15c6e3&text={self.lon},{self.lat}&lang=ru_RU&ll={self.lat},{self.lon}&spn=0.004545,0.004545&results=1&rspn=1")
                    responce = responce.json()["features"][0]["properties"]["GeocoderMetaData"]
                    self.erase()
                    self.label_3.setText(responce['text'])
                except IndexError as e:
                    print(e)

        except AttributeError:
            pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_PageUp:
            if 0 <= self.z < 17:
                self.label_2.setText("")
                self.z += 1
            else:
                self.label_2.setText("Максимальный масштаб!")
        elif event.key() == Qt.Key_PageDown:
            if 0 < self.z <= 17:
                self.label_2.setText("")
                self.z -= 1
            else:
                self.label_2.setText("Минимальный масштаб!")
        elif event.key() == Qt.Key_Up:
            self.lon += 0.05 * (17 - self.z)
        elif event.key() == Qt.Key_Down:
            self.lon -= 0.05 * (17 - self.z)
        elif event.key() == Qt.Key_Left:
            self.lat -= 0.05 * (17 - self.z)
        elif event.key() == Qt.Key_Right:
            self.lat += 0.05 * (17 - self.z)
        self.update_map()

    def change_perspective(self):
        self.current_perspective += 1
        self.current_perspective %= 3
        self.update_map()

    def search(self):
        self.lat, self.lon = [float(i) for i in get_coordinates(str(self.lineEdit.text()))[0]]
        address = get_coordinates(str(self.lineEdit.text()))[1]
        post_idx = get_coordinates(str(self.lineEdit.text()))[2]
        self.params = f"&pt={self.lat},{self.lon},pm2gnm1"
        add = post_idx if self.checkBox.isChecked() else ""
        self.label_3.setText(f"Адрес: {address} " + add)
        self.update_map()

    def erase(self):
        self.params = ""
        self.label_3.setText("Адрес: ")
        self.update_map()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
