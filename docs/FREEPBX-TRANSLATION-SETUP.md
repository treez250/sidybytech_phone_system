# FreePBX Translation Setup - Quick Guide

## Prerequisites
- FreePBX running on 192.168.1.180 ✅
- Translation service running on 192.168.1.178 ✅
- Both servers can communicate ✅

## Step 1: Add Translation Dialplan (5 minutes)

### Via Web UI (Easiest)
1. Open http://192.168.1.180 in browser
2. Login to FreePBX admin
3. Go to **Admin → Config Edit**
4. Select **extensions_custom.conf**
5. Add at the top:
   ```
   #include extensions_translation.conf
   ```
6. Click **Save**
7. Go to **Admin → Asterisk CLI**
8. Run: `dialplan reload`

### Via SSH (Alternative)
```bash
ssh rtreese@192.168.1.180
cd ~/sidybytech_phone_system
sudo docker exec -it pbx-freepbx bash
echo '#include extensions_translation.conf' >> /etc/asterisk/extensions_custom.conf
asterisk -rx "dialplan reload"
exit
```

## Step 2: Create Test Extensions (10 minutes)

1. Go to **Applications → Extensions**
2. Click **Add Extension → Add New PJSIP Extension**
3. Create Extension 100:
   - User Extension: 100
   - Display Name: Test User 1
   - Secret: (generate strong password)
   - Under **Advanced** tab:
     - Codecs: PCMU only (uncheck all others)
     - Direct Media: No
     - RTP Symmetric: Yes
4. Click **Submit**
5. Repeat for Extension 101
6. Click **Apply Config**

## Step 3: Test Translation (5 minutes)

### Test A: Echo Test
1. Register a softphone to extension 100
2. Dial **8888**
3. You should hear "hello world"
4. Speak - you'll hear your voice echoed back
5. Check translation service logs for recognition

### Test B: Call with Translation
1. Register two softphones (100 and 101)
2. From 100, dial **8101**
3. Speak in English
4. Extension 101 hears the call
5. Check logs for translation output

### Test C: Direct Call (No Translation)
1. From 100, dial **9101**
2. This calls 101 directly without translation
3. Use this to compare audio quality

## Dialplan Cheat Sheet

- **8XXX** = Call extension XXX with translation
- **9XXX** = Call extension XXX directly (no translation)
- **8888** = Translation echo test

## Troubleshooting

### "Number not in service"
- Dialplan not loaded. Run: `asterisk -rx "dialplan reload"`
- Check: `asterisk -rx "dialplan show translation-context"`

### No audio / one-way audio
- Check codec is PCMU only
- Verify Direct Media = No
- Verify RTP Symmetric = Yes

### Translation service not responding
- Check service running on 192.168.1.178
- Verify firewall allows UDP 4000-4001
- Test connectivity: `ping 192.168.1.178`

## Next Steps

Once basic translation works:
1. Add TTS for synthesized speech output
2. Configure bidirectional translation
3. Add more language pairs
4. Scale for production use

See `docs/TRANSLATION-INTEGRATION.md` for full details.
