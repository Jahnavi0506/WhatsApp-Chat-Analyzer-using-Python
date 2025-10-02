This project analyzes exported WhatsApp group or personal chat data to uncover insights such as:

Most active participants

Message counts by date and hour

Most used words

Emoji usage

Media/deleted message stats

Word clouds per participant

✅ Features

Parse WhatsApp chat .txt exports

Clean and filter messages (remove media, deleted, and system messages)

Extract:

Date and time

Author

Message body

Generate:

Participation stats

Word clouds per user

Hourly/daily activity plots

▶️ How to Use
1. Export WhatsApp Chat

Export without media and rename the file to:

whatsapp-chat-data.txt


Place it in the project folder or update the path in the notebook.

2. Open the Notebook

Run ChatAnalysis.ipynb step by step.

3. Parsing

The code auto-detects Android format and extracts:

Date

Time

Author

Message

4. Cleaning

It removes:

<Media omitted>
This message was deleted


plus empty/system messages.

5. Visualizations

You can generate:

Word clouds for selected authors

Top active hours

Message counts

Emoji usage

Emoji frequency

Skip media and deleted messages safely
