---
title: "Clicknow's Roadmap: 1.14 ~ 2.1"
url: "/roadmap/"
date: 2024-12-28T06:59:00Z
lastmod: 2025-02-18T01:23:43Z
description: "Enhanced AI-search, two-way translation, custom prompts, and screenshot mode"
summary: "Enhanced AI-search, two-way translation, custom prompts, and screenshot mode"
author: "laike9m"
cover:
  image: "/blog/assets/uploads/9e46e74813a26b5d4e0762cb8b2cee10.jpeg"
  relative: false
---

Here's the planned roadmap for Clicknow, from 1.4 to 2.1

## Ver 1.14 - Enhanced AI-search

Clicknow can search online, but in many cases the result is still directly returned from LLM without online data. I want to make it work more reliably, so that online data is included in the result when available.

Note: online-search requires accessing perplexity.ai. Not being able to access the website will disable this feature.

## Ver 1.15 - Two-way Translation

This feature is asked by many non-English speaking users.

The end state will be like this: you can set a **first** (your native language) and **second language** (most likely English)

- If the selected text is not in your first language, it will be translated to your **first language**;
- If the selected text is in your first language, it will be translated to the **second language**.

let's say I'm a native Chinese speaker, I can set my first language as Chinese, and second language as English. Then, I can first write something in Chinese, and let Clicknow translate it into English, which it currently can't do.

## Ver 2.0 - Custom Prompts

This is probably the most asked feature, and admittedly a significant change.

The current workflow and UX will **NOT** change. **A third button will be added so you can enter custom prompts. You will also be able to store common prompts and select from them to avoid repetitive typing**.

Details and UI is TBD. I will share more when ready.

## Ver 2.1 - Screenshot Mode

Finally, explain or translate the text in a screenshot is also what many people want to use Clicknow for. I was a bit hesitant at first, but ultimately thought it would be really useful, so I decided to put it here.

## Final Words

After 2.1, I believe Clicknow will (by and large) be feature complete. Of course, there will always be new requests and bug fixes, which I will be working on. However, Clicknow will not evolve into a full-featured LLM client, that is not the goal. **It will always be a lightweight, non-interruptive, use-and-forget tool, that is there when you're too lazy to switch to another app**. If you need to dig deep into something, a LLM client is a better choice.
