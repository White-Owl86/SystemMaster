# SystemMaster / White Owl

ابزار کوچک Tkinter برای دسترسی به تنظیمات و اجرای چند فرمان مدیریتی ویندوز ۱۰ و ۱۱.

**سورس نسخهٔ جدید در `systemmaster.py` است. فایل `SystemMaster.exe` در ریشه، نسخهٔ قبلی است و از این سورس بازسازی نشده است.**

## اجرا

روی ویندوز، Python 3.9 یا جدیدتر همراه با Tcl/Tk نصب کنید و در پوشهٔ پروژه اجرا کنید:

```powershell
py -3 systemmaster.py
```

بستهٔ جانبی برای اجرای سورس لازم نیست. برای تغییر فایروال، Remote Desktop یا راه‌اندازی مجدد Print Spooler، PowerShell را با **Run as administrator** باز کنید و دستور بالا را در آن اجرا کنید. تنظیمات معمولی با دسترسی کاربر عادی باز می‌شوند.

## تغییر فرمان‌های قدیمی

| گزینهٔ قبلی | رفتار نسخهٔ جدید |
| --- | --- |
| Show-Share | بازکردن Network and Sharing Center؛ تنظیم اشتراک‌گذاری بدون نصب خودکار SMB1 |
| Fix Printer Error 0x0000011b | بازکردن تنظیمات چاپگر؛ این گزینه ادعای رفع خودکار خطا ندارد و حفاظت RPC را غیرفعال نمی‌کند |
| Restart Print Spooler | راه‌اندازی مجدد سرویس همراه با نمایش نتیجه یا خطای واقعی |
| Disable Windows Update | بازکردن Windows Update برای بررسی یا توقف موقت از طریق گزینه‌های موجود ویندوز |
| Disable Firewall | غیرفعال‌کردن همهٔ پروفایل‌ها با تأیید کاربر؛ گزینهٔ فعال‌کردن همهٔ پروفایل‌ها نیز اضافه شده است |
| Disable RDP Port | غیرفعال‌کردن اتصال ورودی Remote Desktop با `fDenyTSConnections=1`؛ شمارهٔ پورت تغییر نمی‌کند |
| Disable Antivirus | بازکردن Windows Security برای مدیریت حفاظت از مسیر پشتیبانی‌شدهٔ ویندوز |

اگر نسخهٔ قبلی را اجرا کرده‌اید، تغییرات قبلی مثل پورت RDP، وضعیت سرویس Update یا تنظیم RPC چاپگر خودکار برگردانده نمی‌شوند. فعال‌کردن فایروال همهٔ پروفایل‌ها را روشن می‌کند؛ وضعیت قبلی هر پروفایل ذخیره یا بازیابی نمی‌شود. سیاست سازمانی ممکن است بعضی تنظیمات را محدود یا دوباره اعمال کند.

انتخاب اولیه معتبر نیست و دکمهٔ اجرا تا انتخاب یک گزینه غیرفعال می‌ماند. فرمان‌ها در پس‌زمینه اجرا می‌شوند؛ خطاهای PowerShell، نبود دسترسی مدیر و پایان مهلت ۹۰ ثانیه نمایش داده می‌شوند. پایان مهلت به معنی بازگرداندن تغییرات نیست.

## ساخت فایل اجرایی جدید

روی **ویندوز** و با Python دارای Tkinter:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --onefile --windowed --name SystemMaster systemmaster.py
```

خروجی در `dist\SystemMaster.exe` ساخته می‌شود. برای فرمان‌های مدیریتی روی همین فایل راست‌کلیک کرده و **Run as administrator** را انتخاب کنید.

## آزمون

```powershell
py -3 -m unittest discover -s tests -v
```

آزمون‌ها اجرای فرمان‌های سیستم را شبیه‌سازی می‌کنند و تنظیمات دستگاه را تغییر نمی‌دهند. آزمون رابط کاربری به Tk و نمایشگر نیاز دارد؛ در لینوکس می‌توان از `xvfb-run -a python3 -m unittest discover -s tests -v` استفاده کرد. تست‌های شبیه‌سازی‌شده جای آزمایش واقعی روی ویندوز را نمی‌گیرند.

قبل از انتشار، روی ویندوز ۱۰ و ۱۱ بازشدن صفحات تنظیمات با کاربر عادی، رد فرمان‌های مدیریتی بدون دسترسی مدیر، اجرای آن‌ها با دسترسی مدیر، و نمایش خطا در یک ماشین آزمایشی بررسی شود. خاموش‌کردن فایروال یا RDP را روی دستگاهی که تنها دسترسی شما به آن از راه دور است آزمایش نکنید.

## منابع سازگاری

- [وضعیت SMB1 و جایگزین‌های آن — Microsoft](https://learn.microsoft.com/en-us/windows-server/storage/file-server/troubleshoot/smbv1-not-installed-by-default-in-windows)
- [محدودیت‌های DisableAntiSpyware — Microsoft](https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/unattend/security-malware-windows-defender-disableantispyware)
- [آدرس صفحات تنظیمات ویندوز — Microsoft](https://learn.microsoft.com/en-us/windows/apps/develop/launch/launch-settings-app)
- [عیب‌یابی چاپگر — Microsoft](https://support.microsoft.com/en-us/windows/fix-printer-connection-and-printing-problems-in-windows-fb830bff-7702-6349-33cd-9443fe987f73)
- [تنظیم fDenyTSConnections — Microsoft](https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/remote-desktop-cannot-connect-remote-computer)
