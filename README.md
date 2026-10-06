# SystemMaster / White Owl

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-blue.svg)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT%20%2F%20Open-lightgrey.svg)](#)

[English](#english) | [فارسی](#فارسی)

---

## English

A lightweight Python/Tkinter GUI utility for managing common Windows 10 and 11 system administrative settings, network controls, and security configurations safely and predictably.

### Features & Capabilities

- **Safe Command Execution:** Uses native Windows PowerShell commands with argument boundaries, timeouts (90s limit), and accurate error reporting.
- **Administrative Checks:** Verifies Administrator privilege elevation prior to modifying any system or security configurations.
- **Tamper Protection Awareness:** Respects Windows Defender Tamper Protection and organizational policies without attempting unsafe bypasses.
- **Two-way Protection:** Offers both safe disabling (with confirmation prompts and warnings) and comprehensive re-enabling of Windows Defender and Firewall profiles.

### Downloads & Running

#### 1. Pre-built Executable (Recommended)
Download the latest pre-compiled standalone executable from the [Releases](https://github.com/White-Owl86/SystemMaster/releases) page.
Right-click `SystemMaster.exe` and select **Run as administrator** for commands that modify system configurations.

#### 2. Running from Source
Requires Python 3.9+ with Tcl/Tk support:
```powershell
python systemmaster.py
```
> Note: Ensure `security_controls.py` is present in the same directory.

### Command Behaviors

| Feature / Action | Behavior & Details |
| --- | --- |
| **Show-Share** | Opens Network and Sharing Center; configures sharing without auto-installing legacy SMB1 |
| **Printer Error Fix** | Opens Printer settings for standard troubleshooting; does not alter RPC protection |
| **Restart Print Spooler** | Restarts the Windows Print Spooler service with live status reporting |
| **Windows Update** | Launches Windows Update settings to pause or configure updates natively |
| **Firewall Controls** | Allows toggling Domain, Private, and Public firewall profiles with user confirmation |
| **Disable RDP Port** | Disables incoming Remote Desktop connections using `fDenyTSConnections=1` |
| **Defender & Firewall Protection** | Detailed security control to toggle Defender protections and firewall profiles safely |

### Building from Source

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --onefile --windowed --name SystemMaster systemmaster.py
```
Output will be generated in `dist\SystemMaster.exe`.

### Running Unit Tests

```powershell
python -m unittest discover -s tests -v
```
All unit tests mock Windows system calls and do not alter your host machine's actual settings.

---

## فارسی

ابزار کوچک Tkinter برای دسترسی به تنظیمات و اجرای چند فرمان مدیریتی ویندوز ۱۰ و ۱۱.

**سورس نسخهٔ جدید در `systemmaster.py` است. فایل `SystemMaster.exe` خروجی اجرایی آمادهٔ برنامه است.**

### اجرا

روی ویندوز، Python 3.9 یا جدیدتر همراه با Tcl/Tk نصب کنید و در پوشهٔ پروژه اجرا کنید:

```powershell
py -3 systemmaster.py
```

بستهٔ جانبی برای اجرای سورس لازم نیست. فایل `security_controls.py` باید کنار `systemmaster.py` باشد. برای تغییر حفاظت Defender، فایروال، Remote Desktop یا راه‌اندازی مجدد Print Spooler، PowerShell را با **Run as administrator** باز کنید و دستور بالا را در آن اجرا کنید. تنظیمات معمولی با دسترسی کاربر عادی باز می‌شوند.

### تغییر فرمان‌های قدیمی

| گزینهٔ قبلی | رفتار نسخهٔ جدید |
| --- | --- |
| Show-Share | بازکردن Network and Sharing Center؛ تنظیم اشتراک‌گذاری بدون نصب خودکار SMB1 |
| Fix Printer Error 0x0000011b | بازکردن تنظیمات چاپگر؛ این گزینه ادعای رفع خودکار خطا ندارد و حفاظت RPC را غیرفعال نمی‌کند |
| Restart Print Spooler | راه‌اندازی مجدد سرویس همراه با نمایش نتیجه یا خطای واقعی |
| Disable Windows Update | بازکردن Windows Update برای بررسی یا توقف موقت از طریق گزینه‌های موجود ویندوز |
| Disable Firewall | غیرفعال‌کردن همهٔ پروفایل‌ها با تأیید کاربر؛ گزینهٔ فعال‌کردن همهٔ پروفایل‌ها نیز اضافه شده است |
| Disable RDP Port | غیرفعال‌کردن اتصال ورودی Remote Desktop با `fDenyTSConnections=1`؛ شمارهٔ پورت تغییر نمی‌کند |
| Disable Antivirus | گزینهٔ `Disable Defender protections + firewall` برای غیرفعال‌کردن حفاظت‌های مشخص‌شده در بخش بعد با هشدار قبلی؛ گزینهٔ بازکردن Windows Security نیز موجود است |

اگر نسخهٔ قبلی را اجرا کرده‌اید، تغییرات قبلی مثل پورت RDP، وضعیت سرویس Update یا تنظیم RPC چاپگر خودکار برگردانده نمی‌شوند. فعال‌کردن فایروال همهٔ پروفایل‌ها را روشن می‌کند؛ وضعیت قبلی هر پروفایل ذخیره یا بازیابی نمی‌شود. سیاست سازمانی ممکن است بعضی تنظیمات را محدود یا دوباره اعمال کند.

انتخاب اولیه معتبر نیست و دکمهٔ اجرا تا انتخاب یک گزینه غیرفعال می‌ماند. فرمان‌ها در پس‌زمینه اجرا می‌شوند؛ خطاهای PowerShell، نبود دسترسی مدیر و پایان مهلت ۹۰ ثانیه نمایش داده می‌شوند. پایان مهلت به معنی بازگرداندن تغییرات نیست.

### غیرفعال‌کردن حفاظت Defender و فایروال

گزینهٔ **Disable Defender protections + firewall** ابتدا هشدار آسیب‌پذیرشدن دستگاه در برابر بدافزار و ارتباطات شبکه را نشان می‌دهد. انتخاب پیش‌فرض **No** است؛ لغو یا بستن هشدار هیچ فرمان تغییردهنده‌ای اجرا نمی‌کند. پس از تأیید کاربر و بررسی دسترسی مدیر، این موارد درخواست می‌شوند:

- خاموش‌کردن حفاظت بلادرنگ Defender، پایش رفتار و بررسی فایل‌های دریافتی؛
- تنظیم اسکن اسکریپت Defender روی حالت خاموش؛
- خاموش‌کردن پروفایل‌های Domain، Private و Public فایروال.

برنامه از `Set-MpPreference` و `Set-NetFirewallProfile` استفاده می‌کند. پیش از تغییر، وضعیت Defender، Tamper Protection و فایروال خوانده می‌شود. اگر Tamper Protection فعال یا وضعیت آن نامعلوم باشد، برنامه با پیام خطا متوقف می‌شود و تنظیمی را تغییر نمی‌دهد. برنامه Tamper Protection یا سیاست سازمانی را دور نمی‌زند.

وضعیت واقعی سه حفاظت Defender، ترجیحات چهارگانهٔ اسکن و سیاست فعال هر سه پروفایل فایروال پس از تغییر بررسی می‌شوند. اگر خاموش‌شدن Defender تأیید نشود، مرحلهٔ خاموش‌کردن فایروال اجرا نمی‌شود. پیام موفقیت صرفاً با خروج موفق فرمان نمایش داده نمی‌شود. اگر عملیات در میانه شکست بخورد، بعضی تنظیمات ممکن است عوض شده باشند و این موضوع در پیام خطا مشخص می‌شود؛ بازگردانی خودکار انجام نمی‌شود.

**این گزینه حذف یا خاموش‌کردن کامل و دائمی موتور Defender نیست.** اسکن دستی/زمان‌بندی‌شده، SmartScreen و سایر ویژگی‌های امنیتی در این گزینه تغییر نمی‌کنند. ویندوز یا سیاست سازمانی ممکن است حفاظت را دوباره فعال کند. وضعیت اسکن اسکریپت از تنظیمات خوانده می‌شود و آزمون زندهٔ اسکن محسوب نمی‌شود.

برای روشن‌کردن دوباره از **Enable Defender protections + firewall** استفاده کنید. این گزینه همهٔ موارد بالا را روشن می‌کند و وضعیت آن‌ها را بررسی می‌کند؛ وضعیت قبلی هر تنظیم را بازیابی نمی‌کند. حتی اگر روشن‌کردن یکی از دو بخش شکست بخورد، روشن‌کردن بخش دیگر هم تلاش می‌شود. گزینه‌های مستقل فعال/غیرفعال‌کردن فایروال نیز سیاست فعال ویندوز را بررسی می‌کنند.

### ساخت فایل اجرایی جدید

روی **ویندوز** و با Python دارای Tkinter:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --onefile --windowed --name SystemMaster systemmaster.py
```

خروجی در `dist\SystemMaster.exe` ساخته می‌شود. برای فرمان‌های مدیریتی روی همین فایل راست‌کلیک کرده و **Run as administrator** را انتخاب کنید.

### آزمون

```powershell
py -3 -m unittest discover -s tests -v
```

آزمون‌ها اجرای فرمان‌های سیستم را شبیه‌سازی می‌کنند و تنظیمات دستگاه را تغییر نمی‌دهند. آزمون رابط کاربری به Tk و نمایشگر نیاز دارد. تست‌های شبیه‌سازی‌شده جای آزمایش واقعی روی ویندوز را نمی‌گیرند.

### منابع سازگاری

- [وضعیت SMB1 و جایگزین‌های آن — Microsoft](https://learn.microsoft.com/en-us/windows-server/storage/file-server/troubleshoot/smbv1-not-installed-by-default-in-windows)
- [محدودیت‌های DisableAntiSpyware — Microsoft](https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/unattend/security-malware-windows-defender-disableantispyware)
- [آدرس صفحات تنظیمات ویندوز — Microsoft](https://learn.microsoft.com/en-us/windows/apps/develop/launch/launch-settings-app)
- [عیب‌یابی چاپگر — Microsoft](https://support.microsoft.com/en-us/windows/fix-printer-connection-and-printing-problems-in-windows-fb830bff-7702-6349-33cd-9443fe987f73)
- [تنظیم fDenyTSConnections — Microsoft](https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/remote-desktop-cannot-connect-remote-computer)
- [تنظیمات پشتیبانی‌شدهٔ Defender — Microsoft](https://learn.microsoft.com/en-us/powershell/module/defender/set-mppreference)
- [خواندن وضعیت Defender — Microsoft](https://learn.microsoft.com/en-us/powershell/module/defender/get-mpcomputerstatus)
- [Tamper Protection — Microsoft](https://learn.microsoft.com/en-us/defender-endpoint/prevent-changes-to-security-settings-with-tamper-protection)
- [سیاست فعال فایروال — Microsoft](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallprofile)
