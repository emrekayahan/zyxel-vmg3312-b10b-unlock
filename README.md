# ZyXEL VMG3312-B10B: ISP (Türk Telekom) Kilidini Kırma Çabaları, Başarısız Denemeler ve Donanım Analizi
**ZyXEL VMG3312-B10B: ISP De-Branding Failures, Attempted Methods & Hardware Reverse Engineering Report**

> ⚠️ **DURUM: BAŞARISIZ / GELİŞTİRİLMEYE AÇIK (STATUS: FAILED / WORK IN PROGRESS)**  
> Bu depo, Türk Telekom tarafından dağıtılan **ZyXEL VMG3312-B10B** VDSL2 modemdeki servis sağlayıcı kısıtlamalarını (gizli menüler, zorunlu `@ttnet` kullanıcı adı dayatması, TR-069 arka kapısı ve kilitli yazılım güncelleme) kaldırmak için yapılan **tüm denemeleri, donanımsal tersine mühendislik bulgularını ve neden başarısız olduğumuzu** belgelemektedir.  
> **Amaç:** Aynı hataların tekrar denenerek zaman kaybedilmesini önlemek ve konuyu geliştirmek isteyen araştırmacılara net bir zemin sunmaktır.

---

## 🇹🇷 Türkçe Bölüm: Neleri Denedik, Neden Başaramadık?

### 🎯 Nihai Hedefimiz Neydi?
* Modemin Türk Telekom arayüzünden tamamen arındırılması (Saf Global ZyXEL yapılması).
* Gizlenen **Yazılım Güncelleme (Firmware Upgrade)** menüsünün kalıcı açılması.
* WAN ayarlarındaki zorunlu **`@ttnet`** kullanıcı adı ekinin kaldırılması (TurkNet, Vodafone, Millenicom vb. özgürce kullanılabilmesi).
* Kalıcı root / telnet erişimi elde edilmesi.

---

### ❌ Denediğimiz Yöntemler ve Başarısızlık Nedenleri (Post-Mortem)

#### 1. Deneme: Web Arayüzünden Doğrudan Firmware Yükleme (`tabFW.html`)
* **Ne Denedik:** Türk Telekom arayüzünde gizlenen yazılım yükleme sayfasına doğrudan `http://192.168.1.1/pages/tabFW/tabFW.html` adresinden eriştik ve `.bin` dosyalarını yüklemeyi denedik.
* **Neden Başarısız Oldu? (RAM Yetersizliği / OOM):**
  * Modem çalışırken Linux çekirdeğinin sadece **~1.6 - 2.0 MB** boş RAM'i kalmaktadır (`MemFree: 1640 kB`).
  * 18 MB boyutundaki firmware dosyasını tarayıcı üzerinden yüklemeye çalıştığınızda, Linux çekirdeği bellek yetersizliğinden (Out of Memory - OOM) dolayı ya işlemi sessizce sonlandırıyor ya da `httpd` servisini kilitleyerek hiçbir işlem yapmıyor. Web üzerinden büyük firmware dosyası yazmak bu cihazda imkansıza yakındır.

#### 2. Deneme: Orijinal Global Firmware (`100AAPP2D0`, 2014) CFE ile Flaşlama
* **Ne Denedik:** UART seri konsol ile CFE bootloader'ı yakaladık. CFE HTTP kurtarma sunucusu (`http://192.168.1.1/upload.cgi`) üzerinden saf global sürüm olan `100AAPP2D0.bin` kalıbını flash belleğe (`0xb8020000`) başarıyla yazdık.
* **Neden Başarısız Oldu? (Kernel Panic / Donanım Uyuşmazlığı):**
  * `100AAPP2D0` sürümü 2014 yılına aittir.
  * Bizim modemimizin anakartında ise 2016 fabrika çıkışlı **Broadcom BCM63168D0** revizyonu ve **Toshiba TC58BVG0S3HTA00 128MB NAND** bellek bulunmaktadır.
  * 2014 çekirdeği ethernet sürücüsünü (`bcm_enet / net_rx_action`) başlatırken anında çöktü (`CPU 0 Unable to handle kernel paging request at virtual address 00000000 -> Fatal exception in interrupt`).
  * Donanımsal bekçi köpeği (watchdog timer) modemi sürekli reset döngüsüne (Bootloop) soktu.

#### 3. Deneme: Ara Sürüm `100AAPP6D0.bin` (2018) Flaşlama
* **Ne Denedik:** Belki 2018 sürümü donanımı tanır ve kısıtlamasızdır düşüncesiyle `100AAPP6D0` sürümünü CFE üzerinden Partition 0'a yazdık ve `sys fwselect 0` ile başlattık.
* **Neden Başarısız Oldu?:**
  * `AAPP.6` sürümünün çekirdeği de karttaki BCM63168D0 yongasıyla uyuşmadı ve yine `Kernel Panic` vererek çöktü.
  * Modemin brick kalmaması için geliştirdiğimiz otomatik CFE kurtarma scripti anında CFE'yi yakalayıp çalışan sağlam bölüme (`AAPP.12`) geri döndürdü.

#### 4. Deneme: Güncel `100AAPP7D0.bin` (2019) Flaşlama
* **Ne Denedik:** 2019 çekirdeği BCM63168D0 donanımını tam desteklediği için `100AAPP7D0.bin` CFE üzerinden yazıldı ve modem çökmeksizin açıldı.
* **Neden Başarısız Oldu? (Yine Türk Telekom!):**
  * Yazılım teknik olarak çalıştı ancak `100AAPP7D0` sürümü de Türk Telekom'un resmi bir güncellemesi olduğu için menüler yine gizli kaldı, `@ttnet` dayatması ve Türk Telekom logoları devam etti. Türk Telekom imajından kurtulamadık.

#### 5. Deneme: CLI Üzerinden `webstyle Original` Komutu
* **Ne Denedik:** Seri konsol üzerinden ZyXEL mühendislik komutu olan `webstyle Original` çalıştırıldı ve `save` ile kalıcı hale getirildi.
* **Neden Başarısız Oldu?:**
  * Bu komut sadece giriş ekranındaki logo görselini Türk Telekom'dan `logo.gif` (ZyXEL) yaptı. Ancak ana arayüze girildiğinde menülerdeki kısıtlamaları ve servis sağlayıcı kilitlerini kaldırmadı.

#### 6. Deneme: OpenWrt Yükleme Alternatifi
* **Neden İmkansız?:**
  * Broadcom firması VDSL/ADSL modem (DSL PHY - `adsldd`, `bcmxtmrt`) ve Wi-Fi (`wl`) sürücülerini kapalı kaynak tutmaktadır.
  * OpenWrt topluluğunun bu yongaya DSL sürücüsü derlemesi imkansızdır. OpenWrt kurulsa bile DSL (internet) ve kablosuz ağ kesinlikle çalışmayacaktır.

---

### 🔍 Donanım Tersine Mühendislik Bulguları
1. **Flash Bellek Yanılgısı:** İnternette bu modem için "CH341A mandal (SOIC8 klips) ile SPI flash çipini sökmeden okuyup yazın" şeklinde anlatımlar vardır. **Bu tamamen yanlıştır.** Anakartta 8 pinli SPI flash yoktur; **128 MB Parallel NAND Flash (Toshiba TC58BVG0S3HTA00)** kullanılmıştır. SOIC8 mandallarla bu çipe müdahale edilemez.
2. **Dual Partition Mekanizması:** CFE bootloader hafızasında iki bağımsız yazılım bölümü tutar:
   * Partition 0: `0xb8020000`
   * Partition 1: `0xba920000`
   * CFE açılışta `Boot image 0=latest` parametresiyle sürüm numarası yüksek olan bölümü otomatik başlatır.
3. **UART Pin Şeması:** Anakart üzerindeki 5 pinli `J1` portu:
   * `Pin 1`: GND
   * `Pin 2`: Boş
   * `Pin 3`: TXD (Modem) -> RXD (USB-TTL)
   * `Pin 4`: RXD (Modem) -> TXD (USB-TTL)
   * `Pin 5`: NC / Boş
   * Bağlantı parametresi: `115200 Baud, 8N1`.

---

### 💡 Gelecekteki Araştırmacılar İçin Çözüm Yolları (Açık Problemler)
Bu cihazı gerçekten Türk Telekom'dan arındırmak isteyenlerin araştırması gereken noktalar:
1. **SquashFS RootFS Modifikasyonu:** Donanımla uyumlu çalışan `100AAPP7D0.bin` dosyasının rootfs bölümü (SquashFS) ayrıştırılıp, içerisindeki `httpd` sayfaları (`menu.js`, `main.html`, `@ttnet` filtreleri) doğrudan düzenlenip Broadcom formatında yeniden paketlenerek CFE ile basılabilir mi?
2. **ROMFILE / PSI Yamalama:** Modemin yedek ayar dosyasındaki (`configuration-backupsettings.conf`) LZW sıkıştırması çözülüp `TR-069` ve `@ttnet` kısıtlamaları silinip JamCRC ile geri basıldığında kalıcı çözüm sunabilir mi?

---

## 🇬🇧 English Section: What We Tried & Why We Failed

### 🎯 The Objective
* Completely remove the locked Türk Telekom ISP branding and restrictions from the ZyXEL VMG3312-B10B.
* Unhide the **Firmware Upgrade** menu permanently.
* Remove the mandatory **`@ttnet`** PPPoE username suffix to allow any ISP credentials.
* Obtain permanent root / Telnet shell access.

---

### ❌ Attempted Methods & Failure Breakdown

| Attempt | Method | Result | Root Cause of Failure |
| :--- | :--- | :--- | :--- |
| **#1** | Web GUI flash via `/pages/tabFW/tabFW.html` | **Failed / Froze** | Linux has only ~1.6 MB free RAM. 18 MB file causes immediate Out-Of-Memory (OOM). |
| **#2** | CFE flash of `100AAPP2D0.bin` (Global 2014) | **Bootloop** | 2014 kernel drivers crash (`Kernel panic in bcm_enet`) on 2016 BCM63168D0 silicon revision. |
| **#3** | CFE flash of `100AAPP6D0.bin` (2018) | **Bootloop** | Incompatible kernel revision causes instant crash on boot. |
| **#4** | CFE flash of `100AAPP7D0.bin` (2019) | **Booted, but still locked** | Stable boot, but AAPP.7 is STILL an ISP Türk Telekom release with full restrictions. |
| **#5** | CLI `webstyle Original` | **Partial / Visual Only** | Only changed the login logo reference to ZyXEL; did NOT unlock dashboard menus or `@ttnet`. |
| **#6** | OpenWrt installation | **Impossible** | Broadcom DSL PHY (`adsldd`, `bcmxtmrt`) & Wi-Fi drivers are proprietary closed-source. |

---

### 🔬 Hardware Insights
* **SoC:** Broadcom BCM63168D0 (400 MHz MIPS, DDR2)
* **Flash:** **128 MB Parallel NAND (Toshiba TC58BVG0S3HTA00 / 0x98f1)**. Not an 8-pin SPI flash — SOIC8 clips cannot be used.
* **Bootloader:** Broadcom CFE v1.0.38-112.118 (Bootbase V1.06).
* **UART Header `J1`:** Pin 1 = GND, Pin 2 = Empty, Pin 3 = TX, Pin 4 = RX, Pin 5 = NC. (115200 8N1).

---

### 🛠️ Included Tools in this Repository
* `auto_flash.py`: Catches CFE on power-on and uploads firmware via raw HTTP socket.
* `switch_and_boot_aapp6.py`: Fail-safe script that tests alternate partitions and reverts to Partition 1 if a kernel panic is detected.
* `patch_and_repack.py`: Decompresses router config via LZW, alters root/telnet credentials, and recalculates JamCRC.
* `cli_unlock.py`: Automated serial console login and command runner.

---

## 👤 Author
* **Emre Kayahan** ([GitHub Profile](https://github.com/emrekayahan))
