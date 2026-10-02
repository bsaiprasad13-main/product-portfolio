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
- Vanilla JavaScript for the build log ticker, the nav that shrinks on scroll, the theme toggle, the mobile menu, and a kitten (`kitten.png`) that chases the cursor (or taps on phones), sits when it catches up, and naps when left alone
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

The floating chat button in the bottom-right corner opens an AI assistant that answers visitors' questions in my voice, as an AI version of me. It uses Groq (OpenAI GPT-OSS 120B, falling back to GPT-OSS 20B when the free-tier rate limit is hit) and answers only from my portfolio content and my story (`worker/story.txt`).

How it works:
- **Frontend** (`index.html`): the chat button and panel. It sends the conversation to the backend URL set in `ASSISTANT_ENDPOINT`.
- **Backend** (`worker/`): a small Cloudflare Worker that stores the Groq API key as a secret, adds my portfolio facts as context, and calls Groq. It only accepts requests from the sites in `ALLOWED_ORIGINS`, keeps up to 10 messages of history, trims each message to 500 characters, and limits each visitor to 20 messages a minute.

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

**Updating what the assistant knows:** edit `SYSTEM_PROMPT` in `worker/worker.js` whenever the site content changes, then run `npx wrangler deploy`.
