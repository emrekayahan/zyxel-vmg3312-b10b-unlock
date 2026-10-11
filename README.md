# ZyXEL VMG3312-B10B Hardware Reverse Engineering, CFE Bootloader Recovery & De-Branding Guide
**Donanım Tersine Mühendisliği, CFE Bootloader Kurtarma ve Türk Telekom Kısıtlamalarını Kaldırma Rehberi**

---

## 🇹🇷 Türkçe Dokümantasyon

### 1. Cihaz Donanım Özellikleri (Hardware Specifications)
* **Model:** ZyXEL VMG3312-B10B (VDSL2 / ADSL2+ Modem & Router)
* **Anakart Üreticisi:** MitraStar Technology Corp. (MSTC_400 / MSTC_400e)
* **İşlemci (SoC):** Broadcom BCM63168D0 (Broadcom 4350 CPU çekirdeği, 400 MHz MIPS32, DDR2 bellek mimarisi)
* **Flash Bellek:** **128 MB Parallel NAND Flash (Toshiba TC58BVG0S3HTA00 / 0x98f1)**
  * *Önemli Not:* Bu cihazda yaygın bilinenin aksine 8-pinli standart SPI flash çipi bulunmaz. Doğrudan mandal (SOIC8 klips) ile harici CH341A SPI flaşlama yapılamaz. Flaş işlemleri CFE veya JTAG/NAND üzerinden yürütülür.
* **Bootloader:** Broadcom CFE (Common Firmware Environment) v1.0.38-112.118 (Bootbase V1.06)
* **İşletim Sistemi:** Linux 2.6.30 SMP PREEMPT (Broadcom CPE SDK 4.12L.06B)
* **Bölümleme (Dual Partition):**
  * Partition 0: `0xb8020000` (First Image)
  * Partition 1: `0xba920000` (Second Image)
  * NVRAM / Data: `0x00000000 - 0x00020000`

---

### 2. Donanımsal Seri Port (UART) Bağlantısı & Pin Şeması
Modem anakartı üzerinde yer alan 5 pinli `J1` başlığı seri konsol erişimi sağlar:

```
 Anakart J1 Başlığı Şeması:
 ┌──────────────────────────────────────────────┐
 │  [Pin 1]   [Pin 2]   [Pin 3]   [Pin 4]   [Pin 5] │
 │   GND       BOŞ        TXD       RXD      NC/AUX │
 └──────────────────────────────────────────────┘
      │                    │         │
      │ (GND)              │ (TX)    │ (RX)
      ▼                    ▼         ▼
    [GND]                [RXD]     [TXD]  -> USB-TTL (CH341A TTL Modu, Jumper 2-3)
```

* **Programlayıcı:** CH341A USB-TTL Dönüştürücü (Jumper 2-3 pinlerine takılarak TTL seri port moduna alınır).
* **Baud Rate:** `115200`
* **Data Bits:** `8`, **Parity:** `None`, **Stop Bits:** `1` (`115200 8N1`), Akış kontrolü kapalı.

---

### 3. Karşılaşılan Sorunlar ve Teknik Nedenleri

#### A. Web Arayüzünden Firmware Yüklemenin Donması / Başarısız Olması (RAM Yetersizliği)
* **Neden:** Modem Linux ortamında çalışırken boş RAM miktarı yalnızca **~1.6 - 2.0 MB** civarındadır (`MemFree: 1640 kB`). Web arayüzü üzerinden 18 MB boyutundaki `.bin` dosyasını HTTP multipart ile yüklemeye çalıştığınızda Linux çekirdeği bellek yetersizliğinden (Out of Memory - OOM) dolayı `httpd` servisini askıya alır veya yükleme sessizce başarısız olur.
* **Çözüm:** Büyük firmware dosyaları çalışan Linux içerisinden değil; doğrudan **CFE HTTP Kurtarma Modu** (`http://192.168.1.1/upload.cgi`) üzerinden yüklenmelidir. CFE modunda Linux çalışmadığı için 64 MB RAM'in tamamı boştadır ve doğrudan NAND belleğe akış (stream) yapılır.

#### B. `100AAPP2D0.bin` (2014) Sürümünde Kernel Panic (Çekirdek Çökmesi)
* **Neden:** 2014 yılına ait global unbranded yazılım (`100AAPP2D0`), 2016 model yeni revizyon Broadcom BCM63168D0 ethernet sürücüsünü (`bcm_enet / net_rx_action`) ve Toshiba NAND zamanlamalarını desteklemez. Açılış esnasında `CPU 0 Unable to handle kernel paging request` hatası vererek watchdog timer ile sürekli kendini yeniden başlatır (Bootloop).
* **Bulgu:** Bu donanım revizyonu yalnızca 2019 Broadcom SDK çekirdeklerini (`100AAPP7D0` ve `100AAPP12D0`) stabil olarak çalıştırabilir.

#### C. `100AAPP6D0.bin` Sürümünde Kernel Panic
* **Neden:** `AAPP.6` sürümünün çekirdeği de donanım kart revizyonuyla uyuşmayıp çökmektedir. Geliştirdiğimiz otomatik koruma mekanizması bu çöküşü anında algılamış, CFE'yi yakalayıp `fwselect 1` ile modemi sağlam bölüme (`AAPP.12`) geri alarak brick olmasını engellemiştir.

#### D. Neden OpenWrt Desteklenmiyor?
* Broadcom firması, VDSL/ADSL modem (DSL PHY - `adsldd`, `bcmxtmrt`) ve kablosuz ağ (`wl`) sürücülerini kapalı kaynak tutmaktadır. Bu nedenle OpenWrt topluluğu bu yongaya DSL sürücüsü derleyememektedir. Cihaza OpenWrt kurulabilse dahi DSL internet ve Wi-Fi işlevsiz kalacaktır.

---

### 4. Türk Telekom Kısıtlamalarını Kaldırma Yöntemleri

#### Yöntem 1: Gizli "Yazılım Güncelleme" Sayfasını Açma
Türk Telekom arayüzü sol menüdeki linki gizler ancak sayfa modemin web sunucusunda fiziksel olarak vardır. Arayüze (`192.168.1.1`) giriş yaptıktan sonra tarayıcıya doğrudan şu link girilerek açılabilir:
```text
http://192.168.1.1/pages/tabFW/tabFW.html
veya
http://192.168.1.1/pages/maintenance/firmwareUpgrade/firmwareUpgrade.html
```

#### Yöntem 2: Web Temasını Orijinal ZyXEL Yapma
Seri konsol üzerinden aşağıdaki komut çalıştırılarak Türk Telekom teması (`Brick`) yerine orijinal ZyXEL teması (`Original`) kalıcı olarak seçilir:
```text
webstyle Original
save
```
Bu işlem sonrasında arayüz logosu Türk Telekom yerine orijinal **ZYXEL** logosuna (`logo.gif`) döner.

#### Yöntem 3: Yedek Dosyası (ROMFILE) Yamalama ile Tam Özgürlük (En Temiz Yol)
Modemden alınan `configuration-backupsettings.conf` ayar yedeği LZW algoritması ve JamCRC ile paketlenmiştir. Bu depodaki `patch_and_repack.py` aracı ile:
1. `root` kullanıcısı (`root` / `1234`) aktif edilir.
2. Telnet (Port 23) yerel erişimi açılır (`LocalAccess: Port 80,443,23 Protocol HTTP,HTTPS,TELNET`).
3. Türk Telekom'un uzaktan yönetim ve sıfırlama arka kapısı (`TR-069`) tamamen devre dışı bırakılır.
4. WAN PPPoE ayarlarındaki `@ttnet` kullanıcı adı dayatması kaldırılır; böylece TurkNet, Vodafone, Millenicom vb. her servis sağlayıcı kullanılabilir.

---

## 🇬🇧 English Documentation

### 1. Hardware Architecture
* **Target Model:** ZyXEL VMG3312-B10B VDSL2 / ADSL2+ Gateway
* **Board ODM:** MitraStar Technology Corp. (MSTC_400 / MSTC_400e)
* **Processor (SoC):** Broadcom BCM63168D0 (Broadcom 4350 CPU core, 400 MHz MIPS32, DDR2)
* **Flash Storage:** **128 MB Parallel NAND Flash (Toshiba TC58BVG0S3HTA00 / Device ID 0x98f1)**
  * *Critical Finding:* This router does NOT have a standard 8-pin SPI flash chip. Standard SOIC8 clips and direct programmer clips cannot be used. Firmware flashing must be done through CFE recovery or JTAG/NAND pins.
* **Bootloader:** Broadcom CFE v1.0.38-112.118 (Bootbase V1.06)
* **Operating System:** Linux 2.6.30 SMP PREEMPT (Broadcom CPE SDK 4.12L.06B)
* **Dual-Partition Layout:**
  * Partition 0: `0xb8020000`
  * Partition 1: `0xba920000`
  * NVRAM / PSI Partition: `0x00000000 - 0x00020000`

---

### 2. UART Pinout & Connection
The 5-pin `J1` header on the PCB exposes the serial console:
* **Pin 1:** GND
* **Pin 2:** Key notch (empty)
* **Pin 3:** TXD (Router) -> Connect to RXD on USB-TTL
* **Pin 4:** RXD (Router) -> Connect to TXD on USB-TTL
* **Pin 5:** NC / Auxiliary
* **Connection Settings:** 115200 Baud, 8 data bits, no parity, 1 stop bit (115200 8N1), no flow control.
* **Hardware Tool:** CH341A USB programmer set to TTL mode (Jumper on pins 2-3).

---

### 3. Failures, Root Cause Analysis & Technical Discoveries

#### A. Web GUI Firmware Flashing Failure (RAM Exhaustion)
* In the live Linux environment, available memory is restricted to ~1.6 - 2.0 MB (`MemFree: 1640 kB`).
* Uploading an 18 MB firmware `.bin` file via HTTP multipart causes an instant Out-of-Memory (OOM) freeze in `httpd`.
* **Resolution:** All flashing must be executed via **CFE HTTP Rescue Server** (`http://192.168.1.1/upload.cgi`) or CFE TFTP, where Linux is dormant and all 64 MB of RAM is accessible for direct NAND streaming.

#### B. Kernel Panic on `100AAPP2D0.bin` (2014) & `100AAPP6D0.bin` (2018)
* The board hardware revision (2016-2019 BCM63168D0 + Toshiba NAND) is incompatible with legacy kernel drivers (`bcm_enet / net_rx_action` panic).
* Only modern 2019 kernel trees (`100AAPP7D0` and `100AAPP12D0`) maintain stability on this hardware revision.

#### C. Dual-Partition Rescue & Anti-Brick Protection
* Using CFE CLI commands (`fwselect 0`, `fwselect 1`, `ATGO`), automated scripts can catch bootloops and switch active partitions within seconds, preventing any permanent brick scenario.

---

### 4. Scripts & Utilities in this Repository

| Script | Purpose |
| :--- | :--- |
| `auto_flash.py` | Automatically intercepts CFE on reboot and flashes firmware via HTTP socket |
| `patch_and_repack.py` | Decompresses backup `.conf` via LZW, enables `root`/Telnet, disables TR-069, recalculates JamCRC |
| `switch_and_boot_aapp6.py` | Safely forces partition switch and auto-reverts to stable partition if kernel panic occurs |
| `cli_unlock.py` | Automatically logs into ZyXEL CLI (`consoled`) and executes maintenance commands |

---

## 👤 Author
* **Emre Kayahan** ([GitHub Profile](https://github.com/emrekayahan))
