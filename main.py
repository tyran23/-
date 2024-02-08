def keyPressEvent(self, event):
    key = event.key()
    if key == Qt.Key_PageUp and self.map_zoom < 17:
        self.map_zoom += 1
    if key == Qt.Key_PageDown and self.map_zoom > 0:
        self.map_zoom -= 1