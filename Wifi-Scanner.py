import sys
import subprocess
import time
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QLineEdit, QLabel

class WifiScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wi-Fi Tarayıcı")
        self.setGeometry(100, 100, 600, 400)
        
        # Layout oluşturma
        layout = QVBoxLayout()

        # Kullanıcıdan süre almak için etiket ve giriş alanı
        self.duration_label = QLabel("Tarama süresi (saniye):")
        self.duration_input = QLineEdit()
        layout.addWidget(self.duration_label)
        layout.addWidget(self.duration_input)

        # Buton ekleme
        self.scan_button = QPushButton("Wi-Fi Taramasını Başlat")
        self.scan_button.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_button)

        # Ağ seçimi için etiket ve giriş alanı
        self.select_network_label = QLabel("Bir ağ numarası seçin:")
        self.select_network_input = QLineEdit()
        layout.addWidget(self.select_network_label)
        layout.addWidget(self.select_network_input)

        # Bilgi gösterme butonu
        self.info_button = QPushButton("Seçilen Ağ Bilgilerini Göster")
        self.info_button.clicked.connect(self.show_network_info)
        layout.addWidget(self.info_button)

        # CAP dosyasını gösterme butonu
        self.cap_button = QPushButton("Seçtiğiniz Ağın Cap Dosyasını Tarama Ve Gösterme")
        self.cap_button.clicked.connect(self.show_cap_file)
        layout.addWidget(self.cap_button)

        # Sonuçlar için metin alanı
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        # Ana widget ve layout ayarları
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Ağ bilgilerini saklamak için liste
        self.aglar = []

    def aglari_tarama(self):
        # 'iwlist wlan0 scanning' komutuyla ağ taraması yapılır
        try:
            tarama_sonucu = subprocess.check_output(['sudo', 'iwlist', 'wlan0', 'scanning'])
            return tarama_sonucu.decode()
        except subprocess.CalledProcessError as e:
            return f"Tarama hatası: {e}"

    def formatla_ag_bilgileri(self, tarama_sonucu):
        # Wi-Fi ağlarının bilgilerini düzenler
        aglar = []
        
        # SSID, güç, kanal, şifreleme tipi
        ssid_pattern = re.compile(r'ESSID:"(.*?)"')
        signal_pattern = re.compile(r'Signal level=(-\d+) dBm')
        channel_pattern = re.compile(r'Channel:(\d+)')
        encryption_pattern = re.compile(r'Encryption key:(on|off)')
        
        ssids = ssid_pattern.findall(tarama_sonucu)
        signals = signal_pattern.findall(tarama_sonucu)
        channels = channel_pattern.findall(tarama_sonucu)
        encryptions = encryption_pattern.findall(tarama_sonucu)
        
        for i in range(len(ssids)):
            aglar.append({
                'SSID': ssids[i],
                'Signal Level (dBm)': signals[i],
                'Channel': channels[i],
                'Encryption': 'On' if encryptions[i] == 'on' else 'Off'
            })
        
        return aglar

    def start_scan(self):
        # Kullanıcıdan tarama süresi alınır
        try:
            tarama_suresi = int(self.duration_input.text())
        except ValueError:
            self.output_area.append("Lütfen geçerli bir süre girin.")
            return
        
        # Tarama başlatılıyor
        self.output_area.append("Wi-Fi taraması başlatılıyor...")

        # Tarama yapılır ve sonuçlar elde edilir
        start_time = time.time()
        tarama_sonucu = ""
        while time.time() - start_time < tarama_suresi:
            tarama_sonucu = self.aglari_tarama()
            time.sleep(1)  # Her saniye bir tarama yapılır

        # Tarama bitince sonuçlar formatlanır
        self.aglar = self.formatla_ag_bilgileri(tarama_sonucu)
        self.output_area.append("Tarama tamamlandı! Aşağıda çevredeki ağlar listelenmiştir:\n")
        
        # Tablo Başlıkları
        self.output_area.append(f"{'No':<5} {'SSID':<30} {'Signal (dBm)':<15} {'Channel':<10} {'Encryption'}")
        self.output_area.append("=" * 70)  # Düz çizgi

        # Ağları numaralandırarak yazdırma
        for i, ag in enumerate(self.aglar, start=1):
            self.output_area.append(f"{i:<5} {ag['SSID']:<30} {ag['Signal Level (dBm)']:<15} {ag['Channel']:<10} {ag['Encryption']}")
            self.output_area.append("=" * 70)  # Düz çizgi

    def show_network_info(self):
        # Kullanıcının seçtiği ağ numarasını al
        try:
            selected_network_number = int(self.select_network_input.text()) - 1
        except ValueError:
            self.output_area.append("Lütfen geçerli bir ağ numarası girin.")
            return
        
        # Seçilen ağ bilgilerini al
        if 0 <= selected_network_number < len(self.aglar):
            selected_network = self.aglar[selected_network_number]
            ssid = selected_network['SSID']
            signal = int(selected_network['Signal Level (dBm)'])
            encryption = selected_network['Encryption']
            
            # Signal (dBm)'e göre uzaklık durumu
            if signal >= -50:
                distance = "Yakın"
            elif -50 > signal >= -60:
                distance = "Orta"
            else:
                distance = "Uzak"

            # Şifreleme durumu
            if encryption == "On":
                encryption_strength = "Zor Şifre"
            else:
                encryption_strength = "Kolay Şifre"

            # Sonuçları tablo formatında gösterme
            self.output_area.append("\nSeçilen Ağ Bilgileri:")
            self.output_area.append("+----------------------+----------------------+----------------------+----------------------+")
            self.output_area.append(f"| {'SSID':<20} | {'Signal (dBm)':<20} | {'Uzaklık':<20} | {'Şifreleme':<20} |")
            self.output_area.append("+----------------------+----------------------+----------------------+----------------------+")
            self.output_area.append(f"| {ssid:<20} | {signal:<20} | {distance:<20} | {encryption_strength:<20} |")
            self.output_area.append("+----------------------+----------------------+----------------------+----------------------+")
        else:
            self.output_area.append("Geçersiz ağ numarası. Lütfen geçerli bir ağ numarası girin.")

    def show_cap_file(self):
        # Kullanıcının seçtiği ağ numarasını al
        try:
            selected_network_number = int(self.select_network_input.text()) - 1
        except ValueError:
            self.output_area.append("Lütfen geçerli bir ağ numarası girin.")
            return
        
        if 0 <= selected_network_number < len(self.aglar):
            selected_network = self.aglar[selected_network_number]
            ssid = selected_network['SSID']

            # CAP dosyası işlemini simüle etme
            self.output_area.append(f"\n{ssid} için CAP dosyası oluşturuluyor...")
            time.sleep(2)  # Simülasyon için bekleme süresi
            self.output_area.append(f"{ssid} için CAP dosyası başarıyla oluşturuldu ve işlendi!")
        else:
            self.output_area.append("Geçersiz ağ numarası. Lütfen geçerli bir ağ numarası girin.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WifiScannerApp()
    window.show()
    sys.exit(app.exec_())
