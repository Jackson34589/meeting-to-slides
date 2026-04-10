# Meeting to Slides — Client Guide

## What does this solution do?

It automatically converts a recorded meeting into a presentation ready to share.

Instead of someone manually taking notes, transcribing the meeting, and building slides by hand, this tool does all of that in under a minute:

1. Receives the recording (or text) of your meeting
2. Analyzes it with artificial intelligence
3. Generates a Google Slides presentation with the key points
4. Uploads it to Google Drive and gives you a shareable link
5. Logs the process cost in a spreadsheet

---

## What does the generated presentation include?

Each presentation has 5 slides:

| Slide | Content |
|---|---|
| Cover | Meeting title |
| Executive Summary | 2-3 sentences with the most important takeaways |
| Objectives | The 3 main topics or goals discussed |
| Action Items | The 3 concrete tasks agreed upon, with owner |
| Next Steps | What happens after this meeting |

---

## How does it help the business?

**Before this solution:**
- Someone spent 30-60 minutes after each meeting writing the summary and building the slides
- The result depended on who did it — inconsistent in format and detail
- Agreements took time to be distributed to the team

**With this solution:**
- The summary and presentation are ready in under 1 minute
- The format is always consistent and professional
- The link can be shared immediately with everyone involved
- The cost of each process is automatically logged

### Estimated savings per meeting

| Item | Value |
|---|---|
| Time saved per meeting | ~45 minutes of manual work |
| AI cost per meeting | ~$0.05 USD |
| Meetings per month | 20 |
| Total monthly AI cost | ~$1.00 USD |

---

## How do you use it?

### What you need to have ready

- A text file with the meeting transcript (the technical team can configure automatic transcription)
- Internet access

### Steps to generate the presentation

1. Place the meeting text file in the project folder
2. Run the process with a single command (the technical team can automate this)
3. In under a minute you will receive:
   - A link to the presentation in Google Slides
   - Confirmation that the file was saved in Google Drive
   - The updated cost log in Google Sheets

### Example of what you will see when it finishes

```
Pipeline completed successfully.
Presentation: https://docs.google.com/presentation/d/.../edit?usp=sharing
Cost report: saved in Google Sheets
```

---

## What happens to my data?

- The meeting text is processed through Anthropic's AI API (the same creators of Claude)
- The final presentation is saved in your own Google Drive account — not on external servers
- No access keys or passwords are stored in the code

---

## Frequently Asked Questions

**Does it work with any meeting?**
Yes, as long as you have the text of what was discussed. The tool accepts any transcript in plain text format.

**Can I change the slide format?**
In this initial version (POC) the format is standard. The technical team can customize the design in a future version.

**What languages does it support?**
The AI understands and generates content in both Spanish and English. The output language follows the language of the transcript.

**How accurate is the summary?**
The AI identifies the main topics, objectives, and commitments from the text. For very long meetings or conversations with a lot of noise, it is recommended to review the summary before sharing it.

**Who can see the generated presentation?**
Anyone with the link can view it (read-only). The technical team can adjust the permissions if greater privacy is needed.
