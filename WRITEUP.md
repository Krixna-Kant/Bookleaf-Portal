# BookLeaf Author Support — write-up

## What shipped

A separate FastAPI service and a Next.js portal, backed by Postgres. Authors sign in and see only their books and tickets. Operations sees a priority queue, can override category and priority, edit an AI draft, and keep internal notes off the author thread. Updates arrive over a role-scoped server-sent stream, with polling if that stream drops.

The sample file is loaded as-is: 10 authors, 18 books, and four opening tickets. Production titles keep null price and royalty. Pending royalty under ₹1,000 is called out instead of being treated as payable.

## What I built first

The ticket lifecycle and access checks came before the visual design. A wrong royalty number or a note leaking to an author would matter more than the layout. The author sketchbook and the operations ledger were applied after those paths worked, and they still render the database, not the mockup's invented sales or monthly payout dates.

## Auth

Login is email and password with JWT access and refresh tokens, enforced in API dependencies. Authors and admins are different roles, so a stolen author token cannot open the queue. Clerk would be a later production login (hosted sessions, password reset, SSO). It is not in this version because the assignment is scored on our own middleware and role checks. Refresh tokens cannot be used as access tokens.

## AI

Groq is the free provider (`openai/gpt-oss-120b`). Gemini is the configured backup. The first Groq model name (`llama-3.3-70b-versatile`) now 404s on a free key, so the client points at a model the account still serves.

Classify uses the query and the book snapshot only. The draft uses the tone guide plus one category slice of the knowledge base, so a print ticket does not carry the royalty policy into the prompt. Rules always run. If the key is missing or the call fails, the ticket still exists, the keyword label remains, and the draft is marked failed for a human to write. Regenerating a draft is explicit. That keeps token use to one classify and one draft per ticket unless someone asks again.

A paid model later would be a provider swap, not a workflow change. The same fallback should stay, because a support desk cannot block ticket creation on an upstream outage.

## What production would add

Rotate `JWT_SECRET` and keep keys only in the host's secret store. Put uploaded proofs in object storage. Move the AI job and the event fan-out off the web process (a queue, and Redis or a managed socket) so more than one API instance can run. Add password reset. The portal can then sit on a static host with the API and Postgres on a small container platform. None of that changes the author or operations workflows already in the API.
