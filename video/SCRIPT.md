# Film script: Search in Whose Language?

Target 3:00-3:30 at 1920x1080, 60 fps. Plain teaching register. Every number is from
`results/analysis.json` (Gemini 2.5 Flash-Lite unless stated). Cues p1-p11; visuals are
phrase-anchored (see `build_film.py`).

p1. Hundreds of millions of people in India now reach the web through a chat assistant. They ask a question, the assistant searches, reads what comes back, and answers. When the question is in Hindi or Telugu instead of English, the answer is wrong more often. The question is why, because the fix depends on the cause.

p2. There are two very different causes. The first is the agent: it may write a worse query, or search in a language where the evidence is not. We call that the query-side gap. The second is the web itself. Hindi Wikipedia has about two percent of the articles of English Wikipedia. If the fact was never written in Hindi, no Hindi query will find it. We call that the evidence-side gap.

p3. To separate them, we built an instrument. The same question in two languages: human-translated Hindi and English pairs, and Telugu and English pairs. The same evidence served three ways: a frozen pool of Wikipedia text served English-only, Indic-only, or both. A search agent that may search three times and then must answer. And a log of the script of every query it writes.

p4. First, in whose language does the agent search? Left free, with a Hindi question, Gemini 2.5 Flash-Lite writes thirty percent of its queries in English. With a Telugu question, forty-four percent. And it does not change its behaviour when the pool returns no Hindi text at all.

p5. Second, the gap. With the evidence present in both languages, the Hindi question is answered sixty-six percent of the time, the same question in English seventy-six. Nine points. For the two stronger Gemini models the gap is two to three points and inside the noise.

p6. Now the lever. Force the agent to query in Hindi: no change. Force it to query in both languages: two points. Force English: four and a half, not significant. With a modern cross-lingual retriever, the query language barely matters, because a Hindi query already finds the English passage. The query-side gap is almost nothing.

p7. Swap the retriever for classic keyword search, and everything changes. The same Hindi questions, the same model, now lose nineteen points. Searching only in Hindi collapses to thirty-five percent. Searching in both languages wins nine points back. The query gap is a property of the search engine, not of the user.

p8. Third, coverage. We checked, for five hundred and thirty-nine questions per language, whether the Hindi or Telugu Wikipedia article actually states the answer. Hindi: twenty-nine percent. Telugu: twenty-four percent. Most of the evidence an Indian user needs exists only in English.

p9. Put that into the decomposition. With keyword search, a real Hindi user gets forty-five percent against seventy-one for an English user, and most of that loss is the seventy-one percent of facts that only English holds. Telling the agent to search in English lifts the Hindi user to sixty-three. With cross-lingual search, the pool language costs nothing. Then we measured the uncovered questions directly, and they are harder for everyone: the Hindi user gets 51 against 60 for the English user. The same nine-point gap.

p10. So what is the remaining nine points? Reading. Give the model the correct English passage directly: the English question is answered eighty-seven percent of the time, the Hindi question eighty-one. Six points, with nothing left to retrieve. And given a Hindi passage, the Hindi question does worse still, seventy-three. The cheap model reads English better than Hindi.

p11. Six directions were written down before any data. Three held, two failed, one split. The honest summary: with a cross-lingual search engine, the Indic user's deficit is the model's reading, not the web and not the query; with a keyword engine, it is the query, and the fix is to search in English. Search in whose language? It depends on who is doing the searching.
