# 🧪 TRAXORA: PM Test Checklist (Dual-Mode Dev Verification)

## ✅ PRE-TEST CHECKS
- [ ] Confirm REPLIT_PROFILE is set to `dev`
- [ ] Run application → check for "TRAXORA running in DEVELOPMENT mode" in logs
- [ ] Database initializes without config errors
- [ ] SSL warnings are bypassed (dev only)

## 🧠 MODULE TESTS

### Driver Report Logic
- [ ] Handles large MTD files without crashing
- [ ] Skips invalid rows and logs reason
- [ ] Filters for "Pickup Truck" and "On-Road" only
- [ ] Zero-value rows excluded
- [ ] Report generates asynchronously or with clear fallback

### Runtime Mode
- [ ] Dev-specific logs show `[DEVELOPMENT]`
- [ ] Can simulate `prod` mode by toggling `.replit` flag
- [ ] No prod-only secrets or endpoints leak in `dev` mode

## 🧩 API + ASSETS
- [ ] Gauge API hits show success (or proper failover to placeholder)
- [ ] Asset/job site data pulls from expected dev source

## 📦 MISC
- [ ] Logs show which agents ran (DriverClassifier, GeoValidator, etc.)
- [ ] If errors occur, they are caught and shown clearly (not cryptic)

---

✅ If all above checks pass → proceed with stakeholder validation.
❌ If anything fails, capture logs and notify dev/Kaizen GPT.
