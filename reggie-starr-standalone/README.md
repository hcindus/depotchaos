# Reggie Starr RS-79 POS - Standalone Version
**Type:** Single-file HTML Application  
**Location:** `/root/.openclaw/workspace/DepotChaos/reggie-starr-standalone/`  
**Status:** ✅ READY

---

## Features Included

### Core POS Features
- ✅ Splash screen with fade animation
- ✅ PIN login (default: 1234)
- ✅ Multi-category item grid (Grocery, Produce, Deli, Bakery, Beverages)
- ✅ Order management with quantity controls
- ✅ Real-time subtotal, tax (8.25%), and total calculation
- ✅ Hold orders system
- ✅ Order history tracking

### Checkout Features
- ✅ 6 payment methods: Cash, Card, Crypto, Gift Card, Store Credit, Check
- ✅ Tender calculator with numpad
- ✅ Change calculation
- ✅ Printable receipts

### Data Persistence
- ✅ localStorage for orders, history, and counters
- ✅ No server required
- ✅ Works offline

### Design
- ✅ Touch-optimized for tablets/phones
- ✅ Responsive layout
- ✅ Dark theme (Bob Ross palette)
- ✅ CSS animations and transitions

---

## How to Use

### Option 1: Direct Browser
1. Open `reggiestarr-pos.html` in any web browser
2. No installation required
3. Works on Windows, Mac, Linux, tablets, phones

### Option 2: Deploy to Web Server
```bash
cp reggiestarr-pos.html /var/www/html/
# Access via browser: http://your-server/reggiestarr-pos.html
```

### Default Login
- **Select any clerk** from dropdown
- **PIN:** `1234`

---

## File Structure

```
DepotChaos/reggie-starr-standalone/
├── reggiestarr-pos.html    (44KB - complete POS system)
└── README.md               (this file)
```

**Single file contains:** HTML + CSS + JavaScript + embedded data

---

## Differences from Abacus Version

| Feature | Abacus (Full) | Standalone |
|---------|---------------|------------|
| Database | PostgreSQL | localStorage |
| Server | Required (Next.js) | None |
| Multi-user | Concurrent | Single-session |
| Reporting | Advanced charts | Basic history |
| KDS | Full system | Receipt-only |
| Inventory | Full CRUD | Read-only menu |
| Themes | Bob Ross + Militant | Bob Ross only |
| Languages | 6 languages | English only |
| Loyalty | Full system | Not included |
| Layaway | Full system | Hold orders only |

**Standalone is perfect for:**
- Quick deployment
- Offline operation
- Small businesses
- Testing/demo
- Hardware integration testing

---

## Customization

### Add Items
Edit the `itemsDB` object in the JavaScript section:
```javascript
grocery: [
    { id: 'g1', name: 'Your Item', price: 9.99, icon: '📦' },
    // ...
]
```

### Change Tax Rate
Edit the `store` object:
```javascript
const store = {
    taxRate: 0.0825,  // Change to your rate
    // ...
};
```

### Change PIN
Edit the `submitLogin` function:
```javascript
if (store.pinBuffer !== '1234') {  // Change PIN here
```

---

## Browser Compatibility

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+
- ✅ Mobile browsers (iOS Safari, Chrome Android)

---

## Credits

**Built from:** Reggie Starr RS-79 Master Specification (17,040 lines)  
**Original:** Abacus AI Agent (16,000+ credits)  
**Standalone version:** Miles for DepotChaos  
**Date:** 2026-04-19

---

**Ready to use! Open in browser and start selling.** 🚀
