# Route Matrix — 6 Endings QA Checklist

## Overview

Steins;Gate has 6 endings activated by specific D-Mail response chains. Each ending requires the player to respond (or NOT respond) to certain D-Mails throughout the game. This matrix documents every decision point.

## Ending Requirements

### Ending 1: Mayuri Ending
- **Activation:** Do NOT respond to any D-Mail after Chapter 4
- **Key checkpoints:** Ignore all D-Mail triggers from Mayuri
- **Chapter range:** Ch 1-11

### Ending 2: Faris Ending
- **Activation:** Respond to Faris's D-Mails ONLY (ignore others)
- **Key D-Mails:** 
  - Ch 6: Reply to Faris about arcade match
  - Ch 7: Reply to Faris's rematch request
  - Do NOT reply to Luka, Moeka, or Suzuha D-Mails

### Ending 3: Luka Ending
- **Activation:** Respond to Luka's D-Mails ONLY
- **Key D-Mails:**
  - Ch 4: Reply to Luka's message about shopping
  - Ch 6: Reply to Luka about the festival
  - Do NOT reply to Faris, Moeka, or Suzuha

### Ending 4: Moeka Ending
- **Activation:** Respond to Moeka's D-Mails ONLY
- **Key D-Mails:**
  - Ch 5: Reply to Moeka's inquiry about IBN 5100
  - Ch 7: Reply to Moeka's follow-up
  - Do NOT reply to Faris, Luka, or Suzuha

### Ending 5: Suzuha Ending
- **Activation:** Respond to Suzuha's D-Mails ONLY
- **Key D-Mails:**
  - Ch 3: Reply to Suzuha about meeting
  - Ch 7: Reply to Suzuha's time machine message
  - Do NOT reply to Faris, Luka, or Moeka

### Ending 6: True Ending (Kurisu)
- **Activation:** Clear all flags for Kurisu route:
  - Respond to Kurisu's D-Mails when prompted
  - Ch 10: Send the specific D-Mail with correct keyword
  - All previous endings do NOT need to be completed first
  - **Critical D-Mail:** The final message to Kurisu must contain the exact trigger word

## QA Test Protocol

### For each ending:
1. Load save at Chapter 3 (first D-Mail decision point)
2. Follow the exact response pattern above
3. Play through to credits
4. Verify ending CG/credits sequence plays
5. Log any text overflow, missing triggers, or crashes

### Critical test:
- The True Ending's final D-Mail keyword MUST match character count expectations
- If the translated keyword has different length than expected, Phone Trigger fails → soft-lock

## Save States Needed

| Save Point | Chapter | Purpose |
|-----------|---------|---------|
| save_01 | Ch 3 start | Suzuha branch test |
| save_02 | Ch 4 start | Luka/Mayuri branch test |
| save_03 | Ch 5 start | Moeka branch test |
| save_04 | Ch 6 start | Faris branch test |
| save_05 | Ch 10 start | True End test |
| save_06 | Ch 11 start | Final convergence test |
