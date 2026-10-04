# AI Prompts Log

Word-for-word log of the prompts used during this project.

---

## Problem 1: Vibe coder prompts

### Original prompt

> Great, thanks. First we're going to create the AI_prompts file. This should be a word for word log of my prompts during this project, starting with this one. This prompt should have a section for each of our problems, which contains the problem number and title, the original prompt, and any follow-up prompts. If any follow ups are needed, add an explanation of why they were necessary and what was lacking int he first prompt. Keep these explanations to one sentence. This was the prompt for problem 1, Vibe coder prompts. If i ever forget to give a problem number and title, please ask me for them

### Follow-up prompts

None.

---

## Problem 2: Analyze the database

### Original prompt

> Thanks, we're moving to problem 2, analyze the database. Look over campus_customs.db and understand it all, including catalgue, inventory, and users. Nothing to do, just ask questions if you have any. Then create harness.md. Write down each table and its fields and one short line on why each field matters for the shop and/or chatbot. We're going to keep adding to this harness

### Follow-up prompts

> Yes, colors show the colors Yes, that's right on colors. Lets make sure this bot is feature complete, so yes we want teh ask about this button. Chats don't need to be remembered. The bot should treat the blues and the hoodies the same

*Why needed:* The first prompt didn't settle what the `colors` field means, whether the bot needs product context, whether chats are remembered, or how to handle near-duplicate colors and garment types.

> navy and navy blue should be the same. Royal blue should be separate.. Light blue should be separate. The term "blue" should be an overarching filter that returns all three of those categories

*Why needed:* The previous prompt said to treat "the blues" the same without saying which shades are one color and which stay separate.

---

## Problem 3: Build the campus customs website

### Original prompt

> Thanks, we're on to problem 3, build the campus customs website. Scaffold a front end using the tools I described earlier. We want a navigation bar at the top with Home, Products, About Us, Log In, and Create Account. For Home and About Us, use yalebulldogblue.com as reference, but make sure to change the wording so that it doesn't break copyright. On the Products page, show our products with the images linked int eh database along with a name, price, and short description. Each product should have its own page, and clicking teh product should take you tehre. This page should have a large image on the left side, full product text on the other side. This should include the full description, price, sizes, stock in each size or an out of stock message. Add a chat interface that's innt he bottom right and should be present for the entire site.  The hisstory should stay with the user while they're navigating the site, not disappear every time they go to a new page, although it doesn't have to keep the history once somebody leaves the site. A floating chat panel is fine, but make sure it starts int eh bottom right and doesn't go over anything. We'll create the agent powering the chatbot later. Since we'll need an API to read the database, create a simple FastAPI in backend/main.py that can serve products and images. We'll expand it later.

### Follow-up prompts

None.

---

## Problem 4: Create account and login

### Original prompt

> Great, now we're on Problem 4 Campus Customs shop + chatbot. We're going to create the account login flow. When you create an account, it should require first name, last name, emai, password, and confirm password. the login will just be email and password. New accounts should go int he users table of our database. Store the passwords securely to prevent hacks. You can use the test user already created: email is test@campuscustoms.yale.edu and the password is password. Confirmt he login flow works with that user. Then update the harness with an explanation of how the authentication process works. This should include how you store usernames and passwords, as well as how they're protected.

### Follow-up prompts

> Actually rename Problem 4 Create account and login

*Why needed:* The first prompt gave the problem a broad title ("Campus Customs shop + chatbot") that didn't describe this problem's account and login work.

---

## Problem 5: PydanticAI agent backend

### Original prompt

> Great, we're on problem 5 pydanticai agent backend. We're going to build the pydantic agent behind fastapi and plug it into the frontend chat widget. This agent should be main.py in the backend folder. We'll run it with uvicorn. the agent should have four files, pictured. I main.py, expose a chat route so it can repond to queries from teh website. In prompt.md, we're going to add voice and safety basics. Create any good safety rules you can think of, andgive it the voice of morgan freeman. Start or update types in models.py for chat replies and product cards. In the harness, explain how the frontend talks to fastapi and how the agent is laoded (prompt file + model). Make sure it runs from the backend folder like this: uvicorn main:app --reload --port 8000
>
> *[Attached image listing the four agent files: `backend/prompts/prompt.md` — system prompt (grow this same file later); `backend/agent.py` — agent entry / wiring; `backend/tools.py` — tools the agent can call; `backend/models.py` — Pydantic / PydanticAI structured types]*

### Follow-up prompts

> yes, you can stop the lecture 7 backend. And yes, update the product pages for those three items

*Why needed:* The first prompt didn't anticipate that port 8000 was already in use by another app or that three catalogue products had placeholder descriptions and no colors.

---

## Problem 6: Product info and stock

### Original prompt

> Perfect, thanks. Now we are on problem 6 product info and stock. The agent needs to be able to look up info from the database. That should include the product description, price, and stock. It should say if something is out of stock. It should use the database to answer queries, not make up any answers. Can you add these funstions to prompts.md so that it knows how to do this? Add or return types in models.y. then add to the harness an explanation of what model fields are used for lookup results and why

### Follow-up prompts

None.

---

## Problem 7: Chat search that updates the page

### Original prompt

> Great, now we are on problem 7 Chat search that updates the page. Whena. customer asks about a certain type of item ("what kinds of t shirts do you have") it should show the customer the matching items as product cards (image, name, price, short info), which they can click to go to the full page. Update prompt.md  to let the chatbot do this and put int he harness a description of how it's working

### Follow-up prompts

None.

---

## Problem 8: Customer memory

### Original prompt

> Great, now we're on problem 8 customer memory. I've changed my mind, a customer's chat history should be saved to their account and reloaded when they log in again. The agent should also know who is chatting (name, email) so put that in the agent deps and/or tools it can call. Guess can still use the chatbot but don't have memory or name/email. Also make sure the agent understands the context of a page. If a customer asks "do you have this in pink" then the agent should understand what "this" is. Document in the harness how you've done this, what info is stored, what the agent can see about the customer, and how the agent understands the page context.

### Follow-up prompts

None.

---

## Problem 9: Usability improvements

### Original prompt

> Thanks, now we're on problem 9: usability improvements. Implement two usability improvements to teh front end experience. For example, you can add a button to reset the chatbot as one. Then add two backend improvements. For example, give the agent tools that make things faster or cheaper. Write usability.md as you work to describe what you've done. Say what you added and why it helps the website or customer. Then make sure everything works.

### Follow-up prompts

None.

---

## Problem 10: Style the website

### Original prompt

> Great, now were on problem 10 style the website. We need to make it feel more like a real Yale website. Can you pick a new font. make the colors yale blue, make the AI chatbot Handsome Dan teh bulldog, and make everything feel more Yale? Make sure the Yale crest is on there too. In the harness, explain what changes you amde and why it should help customers shop more and have a better experience. Keep this pretty short.

### Follow-up prompts

None.

---

## Problem 11: Site testing (app check)

### Original prompt

> Okay great, now we're on Problem 11: site testing (app check). Can you run a live test of the site and document it in app_check.html? Include screenshots and captions showing that you can ask the chat for the inventory level of an item and it will answer accurately from the database, the search result cards that pop up when you ask for a product category, and show one of the usability features added in problem 9. Make this HTML easy to read - headers for each of these checks, screenshots, one or two sentences showing what each screenshot proves. Put the screenshots in app_check_images and link them to the html with relative paths. then make sure the html works when you double click it

### Follow-up prompts

None.

---

## Problem 12: Audit trail, safety, finish harness

### Original prompt

> Great, thanks. We're on problem 12 Audit trail, safety, finish harness. Keep an eppend only audit_trail.json file of agent-loop activity. Log the time, tools used, results, and stop reason. Do mot wipe this between runs, just keep appending. Put some more safety rules into prompt.md. Finally, finish the harness by making sure it has a full explanation of how the system works. It should explain the model fields in models.py and how you chose them, the tools ad abilities our agent has, the safety rules, and the specs (loop limits, result caps, models, how to run frontend and backend)

### Follow-up prompts

None.

---

## Problem 13: Push to GitHub and submit the URL

### Original prompt

> Thank you. This is problem 13 push to github and submit the url. Finally, can you push the hw4 folder to a public github repository? I'll also need the url to submit to my professor. Do not put the real .env, campus_customs.db, or product images into github. Use .gitignore. Include .env.example with placeholder values. Make sure the file structures still matches this photo.
>
> *[Attached image: the expected `hw4/` file layout (AI_prompts.md, requirements.txt, .env.example, .gitignore, README.md, frontend/, backend/ with main.py, agent.py, models.py, tools.py and prompts/prompt.md, and output/ with harness.md, design.md, usability.md, app_check.html, app_check_images/ and audit_trail.json), plus the local-only `data/` pack (campus_customs.db, products/), and the note that README.md should explain how to run the front end and back end after placing the data pack]*

### Follow-up prompts

None.
