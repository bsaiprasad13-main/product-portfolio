# Sai Prasad — Product Builder Portfolio

This repository holds my personal portfolio website. I'm a B.Tech student at IIT Madras (Engineering Physics), building toward product management roles.

## Overview

The site is one page (`index.html`) written in plain HTML, CSS, and JavaScript. It needs no build step and no dependencies. It covers the products I've shipped, my technical projects, my experience, my leadership roles, and the sports I play.

### Sections
- **Hero and build log:** a short intro, a profile photo, and a scrolling ticker of highlights.
- **The story behind this page:** a personal letter to the reader.
- **01 — How I got here:** how I moved from code to design to product, and why I added an extra year to my degree.
- **02 — Products Built & Launched:**
  - **CampusGuide:** a student knowledge base and community on Discord. 260 active users in 3 weeks.
  - **Free Rooms:** a PWA that shows which of 135 classrooms are free right now. 250+ users in 2 weeks.
- **03 — Technical Projects:**
  - **Mutual Fund FAQ Assistant:** a RAG chatbot with safety guardrails, built with FastAPI, ChromaDB, Groq, and Llama-3.
  - **Weekly Product Review Pulse:** an AI agent that clusters and summarizes 5000+ app reviews each week and sends reports through a custom MCP server.
- **04 — Experience:** PM Fellow at the NextLeap PM Fellowship; Product Development Intern at The Startup School.
- **05 — Also Worth Knowing:** Saarang Safety & Security, where I went from Volunteer to Super Coordinator (Head of Creatives), and Project Manager at CFI.
- **06 — Where I compete:** captain or vice-captain in 4 cricket and frisbee tournaments, with 2 championships and 2 runner-up finishes.

## Technologies Used
- HTML5
- CSS3 (custom properties, Flexbox, CSS Grid, responsive layout)
- Light and dark themes; the choice is saved in `localStorage` and follows the system setting by default
- Vanilla JavaScript for the build log ticker, the nav that shrinks on scroll, the theme toggle, and the mobile menu
- Fonts: Space Grotesk, Inter, IBM Plex Mono, Lora (from Google Fonts)

## Project Structure
```
index.html               # the whole site: markup, styles, and scripts
profile.jpg              # hero photo
saarang.jpg, cfi.jpg     # leadership card covers
*_cricket.jpg, ee_frisbee.jpg   # sports card covers
```

## How to View

Open `index.html` in any modern browser.

## Contact
- LinkedIn: [sai-prasad-bathula](https://www.linkedin.com/in/sai-prasad-bathula-702966380/)
- Email: [bsaiprasad13@gmail.com](mailto:bsaiprasad13@gmail.com)
- GitHub: [bsaiprasad13-main](https://github.com/bsaiprasad13-main)

## Portfolio Assistant (AI chatbot)

The floating chat button in the bottom-right corner opens an AI assistant that answers visitors' questions in my voice, as an AI version of me. It uses retrieval (RAG) over my portfolio content and story, with Groq models (OpenAI GPT-OSS 120B, then GPT-OSS 20B, then Qwen) answering only from what's retrieved.

How it works:
- **Frontend** (`index.html`): the chat button and panel. It sends the conversation to the backend URL set in `ASSISTANT_ENDPOINT`.
- **Backend** (`worker/`): a small Cloudflare Worker that stores the Groq API key as a secret and calls Groq. It only accepts requests from the sites in `ALLOWED_ORIGINS`, keeps up to 6 messages of history, trims each message to 500 characters, and limits each visitor to 20 messages a minute.
- **Retrieval:** `worker/knowledge.txt` is split into topic sections (one per `## ` heading). Each question is embedded with Cloudflare Workers AI (`bge-base-en-v1.5`), the 4 closest sections are picked by cosine similarity plus a small boost when a question word appears in a section's title (hybrid search, which helps broad questions like "tell me about your leadership"), and only those are sent, together with the short core profile in `worker/profile.txt`. With about 22 sections, the search runs in memory, so no vector database is needed. That cut each question from about 3,800 to about 1,500 prompt tokens, which matters because Groq's free tier allows 8,000 tokens per minute per model.
- **Capacity:** if a model is rate-limited, the Worker waits and retries when Groq says it frees up within 2.5 seconds, otherwise it moves to the next model (GPT-OSS 120B, then 20B, then Qwen). In a test of 15 questions about 5 seconds apart, all 15 were answered (it was 7 of 15 before retrieval).
- **Monitoring:** `npx wrangler tail` shows each request's token usage and which sections were retrieved, never the visitor's text.

If `ASSISTANT_ENDPOINT` is empty or the backend is down, the chat replies with my email and LinkedIn instead.

### Setup (one time)
1. Get a free API key at [console.groq.com](https://console.groq.com/keys).
2. Deploy the Worker (this needs a free Cloudflare account):
   ```bash
   cd worker
   npx wrangler login
   npx wrangler secret put GROQ_API_KEY
   npx wrangler deploy
   ```
3. Copy the `https://portfolio-assistant.<you>.workers.dev` URL it prints into `ASSISTANT_ENDPOINT` in `index.html`.
4. If the site is served from somewhere other than `https://bsaiprasad13-main.github.io`, add that origin to `ALLOWED_ORIGINS` in `worker/wrangler.toml` and deploy again.

**Updating what the assistant knows:** edit `worker/knowledge.txt` (keep one topic per `## ` section) and, for facts that should always be included, `worker/profile.txt`. Then run `npx wrangler deploy`. The rules for how it answers are in `RULES` in `worker/worker.js`.

## Oneko Cat

The little pixel cat that chases your cursor is [oneko.js](https://github.com/adryd325/oneko.js) by adryd (MIT License, see `oneko-LICENSE.txt`), a web version of the classic Neko desktop cat. It's loaded with `oneko.js` and the sprite `oneko.gif`.

Changes from the original:
- It moves smoothly every frame and reacts faster. Sprites still change at the classic 10 fps.
- A predictable idle routine: it scratches after 2 seconds still and falls asleep after 5 (the original picked an idle animation at random, about every 20 seconds, and woke up on its own).
- A soft grey circle trails the mouse cursor.
- Its z-index is 150 instead of the maximum, so it stays below the chat assistant.

Tunable constants at the top of `oneko.js`:

| Constant | Default | Original | What it does |
| :--- | :--- | :--- | :--- |
| `NEKO_SPEED` | `200` | `100` | Running speed in px per second |
| `STOP_DISTANCE` | `24` | `48` | How close (px) it sits to the cursor |
| `ALERT_FRAMES` | `3` | up to `6` | Alert pose before running, in 100 ms frames |
| `BLOB_SIZE` | `28` | none | Diameter (px) of the circle trailing the cursor |
| `BLOB_LERP` | `0.2` | none | Circle easing per frame (lower = more lag) |
| `SCRATCH_AFTER_MS` | `2000` | random, ~20 s | Sitting still this long, it scratches (the screen edge if it's at one, otherwise itself) |
| `SCRATCH_FRAMES` | `15` | `10` | Scratch animation length, in 100 ms frames |
| `SLEEP_AFTER_MS` | `5000` | random, ~20 s | Sitting still this long, it yawns and sleeps until the mouse moves |
