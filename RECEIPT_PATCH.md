# Receipt-on-/addpremium Patch — Install

Yeh patch aapke Angle bot me PAYMENT RECEIPT image auto-generate karta hai
jab bhi `/addpremium` chalega, aur receipt **user + owner dono** ko bhej deta hai.

## Files

| File | Where to put | Why |
|------|--------------|-----|
| `receipt_generator.py` | `plugins/receipt_generator.py` | PIL se receipt PNG banata hai |
| `premium_cdm.py`       | `plugins/premium_cdm.py` (REPLACE existing) | `/addpremium` me receipt send karta hai |

## Steps

1. **Install Pillow** (agar already nahi hai):
   ```bash
   pip install pillow
   ```
   Pillow already aata hai `qrcode` ke saath, so usually kuch karna nahi padta.

2. **Copy dono files** apne bot ke `plugins/` folder me:
   ```bash
   cp receipt_generator.py /path/to/Angle-New/plugins/
   cp premium_cdm.py       /path/to/Angle-New/plugins/   # overwrite
   ```

3. **Restart the bot.**

4. Test:
   ```
   /addpremium 123456789 1 d gold
   ```
   - User ko activation message + PNG receipt milegi
   - Owner ko bhi same PNG receipt with user details milegi

## Customize

`receipt_generator.py` ke top par config constants hain — colors, padding,
brand name, etc. tweak kar sakte ho:

```python
BG_HEADER  = (226, 59, 59)   # red header
COL_FOOTER = (255, 91, 91)   # "Powered By Angle Baby" red
```

Brand name `_send_receipt()` me hardcoded hai (`brand="Angle Baby"`) —
agar aap kuch aur dikhana chahte ho to wahaan badal lo.

## Bonus: receipt from UPI screenshot flow

Agar aap chahte ho ki `cbb.py` me jab user "I have paid" dabaaye + screenshot
bheje tab bhi auto-receipt jaye, to `forward_payment_screenshot()` me
`_send_receipt(...)` ko call kar do — same signature. Pero abhi yeh
`/addpremium` par fire hota hai (jo manually owner chalata hai), so wahaan
already cover hai (owner verify karke `/addpremium` chalata hai → receipt
issue ho jaati hai).

## Sample output

`sample_receipt.png` is included so you can see exactly what gets sent.
